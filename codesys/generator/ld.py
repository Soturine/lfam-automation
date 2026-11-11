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


def scan(rungs, env: dict) -> dict:
    """Um ciclo de varredura (rede por rede, de cima para baixo), como o CLP executa."""
    env = dict(env)
    for r in rungs:
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
    names: dict = {}

    def walk(e):
        if isinstance(e, C):
            names[e.var] = "BOOL"
        else:
            for i in e.items:
                walk(i)

    for r in rungs:
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
        body.append(rung_xml(r, ids, left))
    decl = "".join('<variable name="%s"><type><%s /></type></variable>' % (n, t) for n, t in variables.items())
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
