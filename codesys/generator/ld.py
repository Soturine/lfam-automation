"""Gerador de redes Ladder (LD) em PLCopen XML para o CODESYS + avaliador de referencia.

Modelo: cada rede = (expressao booleana de potencia) -> lista de saidas (bobinas).
  C(var, neg=False)   contato NA (ou NF se neg)
  S(*itens)           serie (E)
  P(*itens)           paralelo (OU): varias conexoes na entrada seguinte (OR cabeado do PLCopen)
Saidas: Coil(var), Set(var), Reset(var).
O mesmo objeto alimenta (1) o XML e (2) evaluate()/scan(), para provar equivalencia booleana por testes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
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
    et: str = ""   # variavel TIME opcional que recebe ET (em ms no avaliador)


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


_IEC2PY = [(re.compile(r"\bNOT\b"), "not"), (re.compile(r"\bAND\b"), "and"), (re.compile(r"\bOR\b"), "or"),
           (re.compile(r"\bTRUE\b"), "True"), (re.compile(r"\bFALSE\b"), "False"), (re.compile("<>"), "!="), (re.compile(r"\bMOD\b"), "%")]
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*$")


@lru_cache(maxsize=None)
def _compiled(expr: str):
    py = expr
    for rx, rep in _IEC2PY:
        py = rx.sub(rep, py)
    return compile(py, "<ld-expr>", "eval")


def _ev(expr: str, env: dict):
    """Avalia expressao de AUTORIA PROPRIA do projeto (nunca entrada externa) sem builtins; nomes desconhecidos valem 0."""
    ns = _Zero(_FUNCS)
    ns.update({k: v for k, v in env.items() if not k.startswith("__")})
    return eval(_compiled(expr), {"__builtins__": {}}, ns)  # noqa: S307 - expressoes fixas do gerador


def _sel(g, a, b):
    return b if g else a


def _limit(lo, x, hi):
    return max(lo, min(hi, x))


def _real(x):
    return float(x)


_FUNCS = {"SEL": _sel, "LIMIT": _limit, "INT_TO_REAL": _real, "MAX": max, "MIN": min,
          "REAL_TO_INT": lambda x: int(round(x)), "TIME_TO_REAL": _real, "NOT": lambda x: not x}


@dataclass
class FbRung:
    """Chamada de bloco de funcao (PID, CTU, R_TRIG) SEM EN: executa TODO ciclo (PID nunca fica 'congelado').
    inputs: {pino: expressao}; outputs: {pino: (variavel, tipo)}; inst: nome da instancia (declarada com o tipo do FB)."""
    title: str
    fb: str
    inst: str
    inputs: dict
    outputs: dict
    declare: dict = field(default_factory=dict)   # variaveis so lidas nas expressoes de entrada: {nome: tipo}


class _PidModel:
    """Modelo de referencia do Util.PID (Y = KP*(e + 1/TN*int(e) + TV*de/dt) + Y_OFFSET, limitado a Y_MIN..Y_MAX,
    com a integral ADAPTADA quando limitado). Equivalencia com o runtime CODESYS so e confirmada online."""

    def __init__(self):
        self.i = 0.0
        self.e_old = None

    def step(self, dt, a):
        if a["RESET"]:
            self.i, self.e_old = 0.0, None
            return a["Y_OFFSET"], False
        if a["MANUAL"]:
            return a["Y_MANUAL"], False
        e = a["SET_POINT"] - a["ACTUAL"]
        d = 0.0 if self.e_old is None or dt <= 0 else (e - self.e_old) / dt
        self.e_old = e
        ti = self.i + (e * dt / a["TN"] if a["TN"] > 0 else 0.0)
        y = a["KP"] * (e + ti + a["TV"] * d) + a["Y_OFFSET"]
        lim = y > a["Y_MAX"] or y < a["Y_MIN"]
        if lim and a["Y_MAX"] > a["Y_MIN"]:
            y = max(a["Y_MIN"], min(a["Y_MAX"], y))   # anti-windup: integral nao acumula enquanto limitado
        else:
            self.i = ti
        return y, lim


def _eval_fb(r, env, dt):
    key = "__fb_" + r.inst
    a = {}
    for pin, ex in r.inputs.items():
        a[pin] = _ev(ex, env)
    if r.fb == "PID":
        m = env.setdefault(key, _PidModel())
        y, lim = m.step(dt, {"RESET": False, "MANUAL": False, "Y_MANUAL": 0.0, "Y_OFFSET": 0.0, "Y_MIN": 0.0, "Y_MAX": 100.0, "TV": 0.0, **a})
        out = {"Y": y, "LIMITS_ACTIVE": lim, "OVERFLOW": False}
    elif r.fb == "R_TRIG":
        old = env.get(key, False)
        out = {"Q": bool(a["CLK"]) and not old}
        env[key] = bool(a["CLK"])
    elif r.fb == "CTU":
        st = env.setdefault(key, {"cv": 0, "old": False})
        if a.get("RESET"):
            st["cv"] = 0
        elif a["CU"] and not st["old"] and st["cv"] < int(a["PV"]):
            st["cv"] += 1
        st["old"] = bool(a["CU"])
        out = {"Q": st["cv"] >= int(a["PV"]), "CV": st["cv"]}
    else:
        raise ValueError(r.fb)
    for pin, (var, _t) in r.outputs.items():
        env[var] = out[pin]


FB_TYPES = {"TON", "PID", "CTU", "R_TRIG"}
FB_QUALIFIED = {"PID": "Util.PID"}   # tipos de biblioteca que exigem namespace no PLCopen XML


_OPS = {"GT": lambda x, y: x > y, "GE": lambda x, y: x >= y, "LT": lambda x, y: x < y,
        "LE": lambda x, y: x <= y, "EQ": lambda x, y: x == y, "NE": lambda x, y: x != y}


def _num(env, tok):
    try:
        return float(tok)
    except ValueError:
        return float(_ev(tok, env))


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
        if isinstance(r, FbRung):
            _eval_fb(r, env, dt)
            continue
        if isinstance(r, AssignRung):
            env[r.target] = _ev(r.expr, env)
            continue
        if isinstance(r, TonRung):
            key = "__ton_" + r.inst
            if evaluate(r.power, env):
                env[key] = env.get(key, 0.0) + dt
            else:
                env[key] = 0.0
            env[r.out] = env[key] >= r.pt_s
            if r.et:
                env[r.et] = min(env[key], r.pt_s) * 1000.0
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
                if _IDENT.match(t):
                    names.setdefault(t, "REAL")
            names[r.out] = "BOOL"
        elif isinstance(r, FbRung):
            names[r.inst] = r.fb
            for n, t in r.declare.items():
                names.setdefault(n, t)
            for _pin, (var, t) in r.outputs.items():
                names[var] = t
        elif isinstance(r, AssignRung):
            for n, t in r.types.items():
                names.setdefault(n, t)
        elif isinstance(r, TonRung):
            walk(r.power)
            names[r.inst] = "TON"
            names[r.out] = "BOOL"
            if r.et:
                names[r.et] = "TIME"
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


def fb_xml(r: FbRung, ids, left_rail: int) -> str:
    """Bloco de funcao no estilo validado no importador do CODESYS 3.5.22.40:
    entradas = elementos inVariable ligados aos pinos (a forma 'expression dentro do pino' gera BOOL->REAL fantasma);
    saidas = destino em connectionPointOut/expression (a forma outVariable mapeia saidas fora de ordem)."""
    parts = []
    pins = []
    for pin, ex in r.inputs.items():
        i = next(ids)
        parts.append('<inVariable localId="%d">%s<connectionPointOut /><expression>%s</expression></inVariable>' % (i, _pos(), escape(ex)))
        pins.append('<variable formalParameter="%s"><connectionPointIn><connection refLocalId="%d" /></connectionPointIn></variable>' % (pin, i))
    b = next(ids)
    outs = "".join(
        '<variable formalParameter="%s"><connectionPointOut><expression>%s</expression></connectionPointOut></variable>' % (pin, escape(var))
        for pin, (var, _t) in r.outputs.items()
    )
    parts.append(
        '<block localId="%d" typeName="%s" instanceName="%s">%s<inputVariables>%s</inputVariables><inOutVariables />'
        "<outputVariables>%s</outputVariables></block>" % (b, FB_QUALIFIED.get(r.fb, r.fb), escape(r.inst), _pos(), "".join(pins), outs)
    )
    return "\n".join(parts)


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
        '</inputVariables><inOutVariables /><outputVariables><variable formalParameter="Q"><connectionPointOut /></variable>%s</outputVariables></block>'
        % (b, escape(r.inst), _pos(), conns, int(round(r.pt_s * 1000)),
           '<variable formalParameter="ET"><connectionPointOut /></variable>' if r.et else "")
    )
    if r.et:
        e_id = next(ids)
        parts.append(
            '<outVariable localId="%d">%s<connectionPointIn><connection refLocalId="%d" formalParameter="ET" /></connectionPointIn>'
            "<expression>%s</expression></outVariable>" % (e_id, _pos(), b, escape(r.et))
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
        elif isinstance(r, FbRung):
            body.append(fb_xml(r, ids, left))
        elif isinstance(r, AssignRung):
            body.append(assign_xml(r, ids, left))
        elif isinstance(r, TonRung):
            body.append(ton_xml(r, ids, left))
        else:
            body.append(rung_xml(r, ids, left))
    decl = "".join(
        '<variable name="%s"><type>%s</type></variable>'
        % (n, '<derived name="%s" />' % FB_QUALIFIED.get(t, t) if t in FB_TYPES else "<%s />" % t)
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
