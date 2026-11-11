"""Gerador de redes Ladder (LD) em PLCopen XML para o CODESYS + avaliador de referencia.

Modelo: cada rede = (expressao booleana de potencia) -> lista de saidas (bobinas).
  C(var, neg=False)   contato NA (ou NF se neg)
  S(*itens)           serie (E)
  P(*itens)           paralelo (OU): varias conexoes na entrada seguinte (OR cabeado do PLCopen)
Saidas: Coil(var), Set(var), Reset(var).
O mesmo objeto alimenta (1) o XML e (2) evaluate()/scan(), para provar equivalencia booleana por testes.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from xml.sax.saxutils import escape


@dataclass(frozen=True)
class C:
    var: str
    neg: bool = False


class S:
    def __init__(self, *items):
        self.items = tuple(items)


class P:
    def __init__(self, *items):
        self.items = tuple(items)


@dataclass(frozen=True)
class Out:
    var: str
    kind: str = "coil"  # coil | set | reset


@dataclass
class Rung:
    title: str
    power: object  # expressao C/S/P
    outs: list     # lista de Out


@dataclass
class CmpRung:
    """Comparador alimentando uma bobina: out := (a <op> b). a e b sao variaveis ou literais REAL."""
    title: str
    op: str   # GT GE LT LE EQ NE
    a: str
    b: str
    out: str


@dataclass
class TonRung:
    """TON alimentado pela potencia 'power'; Q -> bobina out. pt em segundos (T#...s no XML)."""
    title: str
    power: object
    inst: str
    pt_s: float
    out: str


@dataclass
class AssignRung:
    """Atribuicao grafica do LD: target := expr (incondicional). reals/ints declaram tipos dos nomes usados."""
    title: str
    target: str
    expr: str
    types: dict  # {nome: 'REAL'|'INT'|'BOOL'} de todos os nomes envolvidos (alvo e operandos)


class _Zero(dict):
    """Namespace do avaliador: variavel nao inicializada vale 0 (como no CLP apos a carga)."""

    def __missing__(self, key):
        return 0.0


def _sel(g, a, b):
    return b if g else a


def _limit(lo, x, hi):
    return max(lo, min(hi, x))


def _real(x):
    return float(x)


_FUNCS = {"SEL": _sel, "LIMIT": _limit, "INT_TO_REAL": _real, "MAX": max, "MIN": min}


_OPS = {"GT": lambda x, y: x > y, "GE": lambda x, y: x >= y, "LT": lambda x, y: x < y,
        "LE": lambda x, y: x <= y, "EQ": lambda x, y: x == y, "NE": lambda x, y: x != y}


def _num(env, tok):
    try:
        return float(tok)
    except ValueError:
        return float(env.get(tok, 0.0))


def Coil(v): return Out(v, "coil")
def Set(v): return Out(v, "set")
def Reset(v): return Out(v, "reset")


def evaluate(expr, env: dict) -> bool:
    if isinstance(expr, C):
        v = bool(env.get(expr.var, False))
        return (not v) if expr.neg else v
    if isinstance(expr, S):
        return all(evaluate(i, env) for i in expr.items)
    if isinstance(expr, P):
        return any(evaluate(i, env) for i in expr.items)
    raise TypeError(expr)


def scan(rungs, env: dict, dt: float = 0.0) -> dict:
    """Um ciclo de varredura (rede por rede, de cima para baixo), como o CLP executa.
    dt (s) avanca os temporizadores TON; estado do TON fica em env['__ton_<inst>']."""
    env = dict(env)
    for r in rungs:
        if isinstance(r, CmpRung):
            env[r.out] = _OPS[r.op](_num(env, r.a), _num(env, r.b))
            continue
        if isinstance(r, AssignRung):
            env[r.target] = eval(r.expr, {"__builtins__": {}}, _Zero({**_FUNCS, **{k: v for k, v in env.items() if not k.startswith("__")}}))
            continue
        if isinstance(r, TonRung):
            key = "__ton_" + r.inst
            if evaluate(r.power, env):
                env[key] = env.get(key, 0.0) + dt
            else:
                env[key] = 0.0
            env[r.out] = env[key] >= r.pt_s
            continue
        p = evaluate(r.power, env)
        for o in r.outs:
            if o.kind == "coil":
                env[o.var] = p
            elif o.kind == "set" and p:
                env[o.var] = True
            elif o.kind == "reset" and p:
                env[o.var] = False
    return env


def variables_of(rungs) -> dict:
    """{nome: tipo}. Tipos: BOOL, REAL (operandos nao literais de comparadores) ou TON (instancias)."""
    names: dict = {}

    def walk(e):
        if isinstance(e, C):
            names.setdefault(e.var, "BOOL")
        else:
            for i in e.items:
                walk(i)

    for r in rungs:
        if isinstance(r, CmpRung):
            for t in (r.a, r.b):
                try:
                    float(t)
                except ValueError:
                    names.setdefault(t, "REAL")
            names[r.out] = "BOOL"
        elif isinstance(r, AssignRung):
            for n, t in r.types.items():
                names.setdefault(n, t)
        elif isinstance(r, TonRung):
            walk(r.power)
            names[r.inst] = "TON"
            names[r.out] = "BOOL"
        else:
            walk(r.power)
            for o in r.outs:
                names[o.var] = "BOOL"
    return names


# ---------------------------------------------------------------- emissor PLCopen XML
def _pos() -> str:
    return '<position x="0" y="0" />'


def _emit_expr(expr, srcs, ids, out):
    """Emite contatos; devolve os localIds cuja saida leva a potencia adiante."""
    if isinstance(expr, C):
        i = next(ids)
        conns = "".join('<connection refLocalId="%d" />' % s for s in srcs)
        out.append(
            '<contact localId="%d" negated="%s" storage="none">%s<connectionPointIn>%s</connectionPointIn>'
            "<connectionPointOut /><variable>%s</variable></contact>"
            % (i, str(expr.neg).lower(), _pos(), conns, escape(expr.var))
        )
        return [i]
    if isinstance(expr, S):
        cur = srcs
        for it in expr.items:
            cur = _emit_expr(it, cur, ids, out)
        return cur
    if isinstance(expr, P):
        ends: list = []
        for it in expr.items:
            ends += _emit_expr(it, srcs, ids, out)
        return ends
    raise TypeError(expr)


_STORAGE = {"coil": "none", "set": "set", "reset": "reset"}


def rung_xml(rung: Rung, ids, left_rail: int) -> str:
    parts: list = []
    ends = _emit_expr(rung.power, [left_rail], ids, parts)
    for o in rung.outs:
        i = next(ids)
        conns = "".join('<connection refLocalId="%d" />' % s for s in ends)
        parts.append(
            '<coil localId="%d" negated="false" storage="%s">%s<connectionPointIn>%s</connectionPointIn>'
            "<connectionPointOut /><variable>%s</variable></coil>" % (i, _STORAGE[o.kind], _pos(), conns, escape(o.var))
        )
    return "\n".join(parts)


def _lit(tok: str) -> str:
    return escape(tok)


_SYM = {"GT": ">", "GE": ">=", "LT": "<", "LE": "<=", "EQ": "=", "NE": "<>"}


def cmp_xml(r: CmpRung, ids, left_rail: int) -> str:
    """Comparacao como CONTATO com expressao booleana (ex.: TT_Z1 > 390.0) -> bobina.
    (As caixas GT/GE/LT do CODESYS exigem nomes de pino que o PLCopen XML nao documenta; ver docs/evidence.)"""
    c = next(ids)
    o = next(ids)
    expr = "%s %s %s" % (r.a, _SYM[r.op], r.b)
    return (
        '<contact localId="%d" negated="false" storage="none">%s<connectionPointIn><connection refLocalId="%d" /></connectionPointIn>'
        "<connectionPointOut /><variable>%s</variable></contact>"
        '<coil localId="%d" negated="false" storage="none">%s<connectionPointIn><connection refLocalId="%d" /></connectionPointIn>'
        "<connectionPointOut /><variable>%s</variable></coil>" % (c, _pos(), left_rail, escape(expr), o, _pos(), c, escape(r.out))
    )


def assign_xml(r: AssignRung, ids, left_rail: int) -> str:
    a = next(ids)
    b = next(ids)
    return (
        '<inVariable localId="%d">%s<connectionPointOut /><expression>%s</expression></inVariable>'
        '<outVariable localId="%d">%s<connectionPointIn><connection refLocalId="%d" /></connectionPointIn><expression>%s</expression></outVariable>'
        % (a, _pos(), escape(r.expr), b, _pos(), a, escape(r.target))
    )


def ton_xml(r: TonRung, ids, left_rail: int) -> str:
    parts: list = []
    ends = _emit_expr(r.power, [left_rail], ids, parts)
    b = next(ids)
    o = next(ids)
    conns = "".join('<connection refLocalId="%d" />' % s for s in ends)
    parts.append(
        '<block localId="%d" typeName="TON" instanceName="%s">%s<inputVariables>'
        '<variable formalParameter="IN"><connectionPointIn>%s</connectionPointIn></variable>'
        '<variable formalParameter="PT"><connectionPointIn><expression>T#%dms</expression></connectionPointIn></variable>'
        '</inputVariables><inOutVariables /><outputVariables><variable formalParameter="Q"><connectionPointOut /></variable></outputVariables></block>'
        % (b, escape(r.inst), _pos(), conns, int(round(r.pt_s * 1000)))
    )
    parts.append(
        '<coil localId="%d" negated="false" storage="none">%s<connectionPointIn><connection refLocalId="%d" formalParameter="Q" />'
        "</connectionPointIn><connectionPointOut /><variable>%s</variable></coil>" % (o, _pos(), b, escape(r.out))
    )
    return "\n".join(parts)


def pou_xml(name: str, variables: dict, rungs: list) -> str:
    """Programa PLCopen com uma barra de potencia esquerda por rede."""
    ids = count(1)
    body = []
    for r in rungs:
        left = next(ids)
        body.append(
            '<comment localId="%d" height="0" width="0">%s<content><xhtml xmlns="http://www.w3.org/1999/xhtml">%s</xhtml></content></comment>'
            % (next(ids), _pos(), escape(r.title))
        )
        body.append('<leftPowerRail localId="%d">%s<connectionPointOut formalParameter="none" /></leftPowerRail>' % (left, _pos()))
        if isinstance(r, CmpRung):
            body.append(cmp_xml(r, ids, left))
        elif isinstance(r, AssignRung):
            body.append(assign_xml(r, ids, left))
        elif isinstance(r, TonRung):
            body.append(ton_xml(r, ids, left))
        else:
            body.append(rung_xml(r, ids, left))
    decl = "".join(
        '<variable name="%s"><type>%s</type></variable>'
        % (n, '<derived name="TON" />' if t == "TON" else "<%s />" % t)
        for n, t in variables.items()
    )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<project xmlns="http://www.plcopen.org/xml/tc6_0200">'
        '<fileHeader companyName="" productName="CODESYS" productVersion="CODESYS V3.5 SP22 Patch 4" creationDateTime="2026-11-11T00:00:00" />'
        '<contentHeader name="LFAM" modificationDateTime="2026-11-11T00:00:00"><coordinateInfo>'
        '<fbd><scaling x="1" y="1" /></fbd><ld><scaling x="1" y="1" /></ld><sfc><scaling x="1" y="1" /></sfc>'
        "</coordinateInfo></contentHeader><types><dataTypes /><pous>"
        '<pou name="%s" pouType="program"><interface><localVars>%s</localVars></interface>'
        "<body><LD>%s</LD></body></pou></pous></types><instances><configurations /></instances></project>"
        % (name, decl, "\n".join(body))
    )
