"""Desenha as redes Ladder do programa gerado como SVG (uma imagem por rede) + docs/LADDER.md.

IMPORTANTE: estes desenhos sao gerados a partir do MESMO modelo (codesys/generator) que produz o PLCopen XML importado no
CODESYS. Sao uma ilustracao fiel da estrutura (contatos, serie/paralelo, blocos, bobinas), NAO uma captura do editor do IDE.
Uso (na raiz): python tools/render_ladder.py
"""
import pathlib
import re
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codesys.generator import program  # noqa: E402
from codesys.generator.ld import AssignRung, C, CmpRung, FbRung, P, Rung, S, TonRung  # noqa: E402

OUT = ROOT / "docs" / "media" / "ladder"
ROW, CW, CH = 62, 104, 24          # altura da linha, largura da celula do contato, meia-altura da barra
CH_PX = 6.7                          # largura aproximada de um caractere (monospace 11px)
BG, WIRE, TXT, MUT, CON, COIL, BOX = "#101923", "#6fa3b8", "#e8f0f6", "#9db0bf", "#42c9e8", "#4ed5a3", "#1c2b39"
_SYM = {"GT": ">", "GE": ">=", "LT": "<", "LE": "<=", "EQ": "=", "NE": "<>"}


def tw(s: str) -> float:
    return len(s) * CH_PX


def cut(s: str, n: int = 17) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------- medida / desenho de expressoes booleanas
def measure(e):
    if isinstance(e, C):
        return CW, 1
    if isinstance(e, S):
        ms = [measure(i) for i in e.items]
        return sum(m[0] for m in ms), max(m[1] for m in ms)
    if isinstance(e, P):
        ms = [measure(i) for i in e.items]
        return max(m[0] for m in ms) + 24, sum(m[1] for m in ms)
    raise TypeError(e)


def line(x1, y1, x2, y2, c=WIRE, w=2):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}" stroke-linecap="round"/>'


def text(x, y, s, size=11, fill=TXT, anchor="middle", weight="normal"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="Consolas,Menlo,monospace" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{escape(s)}</text>')


def draw(e, x, y):
    """Desenha a expressao com a primeira linha centrada em y; devolve (partes, largura)."""
    if isinstance(e, C):
        mx = x + CW / 2
        p = [line(x, y, mx - 9, y), line(mx + 9, y, x + CW, y),
             line(mx - 9, y - CH, mx - 9, y + CH, CON, 3), line(mx + 9, y - CH, mx + 9, y + CH, CON, 3)]
        if e.neg:
            p.append(line(mx - 14, y + CH - 2, mx + 14, y - CH + 2, "#eb6a73", 2))
        p.append(text(mx, y - CH - 6, cut(e.var), 11, TXT))
        return p, CW
    if isinstance(e, S):
        parts, cx = [], x
        for it in e.items:
            p, w = draw(it, cx, y)
            parts += p
            cx += w
        return parts, cx - x
    if isinstance(e, P):
        w, _ = measure(e)
        parts, cy = [], y
        ys = []
        for it in e.items:
            iw, ih = measure(it)
            p, dw = draw(it, x + 12, cy)
            parts += p
            parts.append(line(x, cy, x + 12, cy))
            parts.append(line(x + 12 + dw, cy, x + w, cy))
            ys.append(cy)
            cy += ih * ROW
        parts.append(line(x, ys[0], x, ys[-1]))
        parts.append(line(x + w, ys[0], x + w, ys[-1]))
        return parts, w
    raise TypeError(e)


def coil(x, y, o):
    sym = {"coil": "", "set": "S", "reset": "R"}[o.kind]
    p = [f'<circle cx="{x + 18}" cy="{y}" r="15" fill="none" stroke="{COIL}" stroke-width="3"/>', line(x, y, x + 3, y)]
    if sym:
        p.append(text(x + 18, y + 4, sym, 12, COIL, weight="bold"))
    p.append(text(x + 18, y - 22, cut(o.var, 20), 11, TXT))
    return p


def box(x, y_top, w, h, title, sub=""):
    p = [f'<rect x="{x}" y="{y_top}" width="{w}" height="{h}" rx="6" fill="{BOX}" stroke="{CON}" stroke-width="2"/>',
         text(x + w / 2, y_top + 16, title, 12, CON, weight="bold")]
    if sub:
        p.append(text(x + w / 2, y_top - 6, cut(sub, 26), 11, TXT))
    return p


# ---------------------------------------------------------------- uma rede (rung) completa
def rung_svg(r):
    """Devolve (partes, largura, altura) com a origem em (0,0); a primeira linha de fio fica em y = ROW/2 + 14."""
    y0 = ROW / 2 + 14
    parts, width, rows = [], 0, 1
    if isinstance(r, Rung):
        ew, er = measure(r.power)
        p, _ = draw(r.power, 20, y0)
        parts += p
        xe = 20 + ew
        rows = max(er, len(r.outs))
        cx = xe + 40
        if len(r.outs) > 1:
            parts.append(line(xe, y0, cx - 12, y0))
            parts.append(line(cx - 12, y0, cx - 12, y0 + (len(r.outs) - 1) * ROW))
        else:
            parts.append(line(xe, y0, cx, y0))
        for i, o in enumerate(r.outs):
            yy = y0 + i * ROW
            if len(r.outs) > 1:
                parts.append(line(cx - 12, yy, cx, yy))
            parts += coil(cx, yy, o)
        width = cx + 60
    elif isinstance(r, CmpRung):
        expr = f"{r.a} {_SYM[r.op]} {r.b}"
        bw = tw(expr) + 28
        parts += [line(20, y0, 40, y0), f'<rect x="40" y="{y0 - 18}" width="{bw}" height="36" rx="5" fill="{BOX}" stroke="{CON}" stroke-width="2"/>',
                  text(40 + bw / 2, y0 + 4, expr, 11)]
        x = 40 + bw
        if r.gate:
            p, w = draw(C(r.gate), x, y0)
            parts += p
            x += w
        parts += [line(x, y0, x + 40, y0)] + coil(x + 40, y0, type("O", (), {"var": r.out, "kind": "coil"}))
        width = x + 40 + 60
    elif isinstance(r, AssignRung):
        expr = f"{r.target} := {r.expr}"
        bw = tw(expr) + 28
        parts += [line(20, y0, 40, y0), f'<rect x="40" y="{y0 - 18}" width="{bw}" height="36" rx="5" fill="{BOX}" stroke="{COIL}" stroke-width="2"/>',
                  text(40 + bw / 2, y0 + 4, expr, 11)]
        width = 40 + bw + 24
    elif isinstance(r, TonRung):
        ew, er = measure(r.power)
        p, _ = draw(r.power, 20, y0)
        parts += p
        bx = 20 + ew + 30
        parts.append(line(20 + ew, y0, bx, y0))
        bw, bh = 150, 84
        parts += box(bx, y0 - 22, bw, bh, "TON", r.inst)
        parts += [text(bx + 8, y0 + 4, "IN", 11, MUT, "start"), text(bx + 8, y0 + 30, f"PT  T#{int(r.pt_s)}s", 11, MUT, "start"),
                  text(bx + bw - 8, y0 + 4, "Q", 11, MUT, "end"), line(bx + bw, y0, bx + bw + 30, y0)]
        parts += coil(bx + bw + 30, y0, type("O", (), {"var": r.out, "kind": "coil"}))
        rows, width = 2, bx + bw + 30 + 60
    elif isinstance(r, FbRung):
        ins, outs = list(r.inputs.items()), list(r.outputs.items())
        n = max(len(ins), len(outs))
        lw = max(tw(cut(e, 30)) for _, e in ins) + 14
        bw, bh = 150, 26 * n + 30
        bx = 20 + lw + 26
        parts += box(bx, y0 - 22, bw, bh, r.fb if r.fb != "PID" else "Util.PID", r.inst)
        for i, (pin, e) in enumerate(ins):
            yy = y0 + 4 + i * 26
            parts += [text(20 + lw, yy - 3, cut(e, 30), 10, TXT, "end"), line(20 + lw + 2, yy - 4, bx, yy - 4), text(bx + 8, yy, pin, 10, MUT, "start")]
        for i, (pin, (var, _t)) in enumerate(outs):
            yy = y0 + 4 + i * 26
            parts += [text(bx + bw - 8, yy, pin, 10, MUT, "end"), line(bx + bw, yy - 4, bx + bw + 26, yy - 4), text(bx + bw + 30, yy - 1, var, 10, COIL, "start")]
        rows = max(2, (bh + 22) // ROW + 1)
        width = bx + bw + 30 + max(tw(v) for _, (v, _) in outs) + 20
    else:
        raise TypeError(r)
    return parts, width, rows * ROW + 28


def title_of(r):
    return re.sub(r"^NETWORK\s+\w+\s*-\s*", "", r.title)


def network_id(r):
    m = re.match(r"NETWORK\s+(\d+)", r.title)
    return int(m.group(1)) if m else 0


def render():
    OUT.mkdir(parents=True, exist_ok=True)
    nets = {}
    for r in program.RUNGS:
        nets.setdefault(network_id(r), []).append(r)
    index = []
    for nid in sorted(nets):
        body, y, maxw = [], 12, 0
        for r in nets[nid]:
            parts, w, h = rung_svg(r)
            body.append(text(14, y + 12, cut(title_of(r), 150), 12, MUT, "start"))
            body.append(f'<g transform="translate(0,{y + 6})">' + f'<line x1="10" y1="0" x2="10" y2="{h - 16}" stroke="{CON}" stroke-width="3"/>' + "".join(parts) + "</g>")
            y += h + 14
            maxw = max(maxw, w + 30, tw(cut(title_of(r), 150)) * 1.08 + 40)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {maxw:.0f} {y + 6}" width="{maxw:.0f}" height="{y + 6}">'
               f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>' + "".join(body) + "</svg>")
        name = f"rede_{nid:02d}.svg"
        (OUT / name).write_text(svg, encoding="utf-8")
        index.append((nid, name, [title_of(r) for r in nets[nid]]))
    return index


DESC = {
    1: "Escalonamento: converte os valores brutos do módulo analógico (termopares, pressão, substrato) em °C / MPa.",
    2: "Supervisão de temperatura: pré-alarme 390 °C, falha 400 °C e termopar rompido (só com termopar válido).",
    3: "Temporizadores de intertravamento: câmara quente 2 min, sem material 60 s, ventilador 10 s, K1 colado 1 s.",
    4: "Cérebro de segurança: `M_CAUSA` (10 causas), falha **travada**, reset condicionado e latches de **primeira causa**.",
    5: "Aquecimento: selo `EST_AQUEC` e contator `K1_AQUEC` (um escritor por saída).",
    6: "PID das 5 zonas (`Util.PID`), executado **todo ciclo**; PWM por fase e porta do SSR (`SSR_Zn`).",
    7: "Resfriamento da câmara por histerese: liga acima de 80 °C, mantém até 60 °C.",
    8: "Encharque de 15 min: todas as zonas ≥ 330 °C, contínuo; o TON zera se qualquer zona cair.",
    9: "PRONTO e permissivos do robô: encharque, secador, inversor, sem falha travada.",
    10: "Rosca: partida (`BT_LIGA`/robô), parada (`BT_DESLIGA` normalmente fechado) e `INV_RUN`.",
    11: "Ventilação do motor: liga com a rosca e segue 5 min após parar.",
    12: "Referência do inversor: política de pressão (≥ 16,5 MPa → ×0,9, piso 17 rpm), escala `INV_REF`.",
    13: "PID do aquecedor infravermelho (IR) e porta do `SSR_IR` (habilitado só com robô em movimento).",
    14: "Carregador do funil: `R_TRIG` + `CTU` contam os ciclos de recarga (lotes).",
    15: "Torre luminosa e sirene (verde/amarela/vermelha), alarme do trecho frio.",
}


def write_doc(index):
    lines = [
        "# Catálogo do Ladder (15 redes)",
        "",
        "> **O que são estas imagens:** desenhos **gerados automaticamente** a partir do mesmo modelo que produz o PLCopen XML importado no "
        "CODESYS (`python tools/render_ladder.py`). Mostram a estrutura real (contatos, série/paralelo, blocos, bobinas), mas **não são capturas "
        "do editor do IDE**. O programa que roda no CLP virtual é o `.project` compilado a partir do mesmo XML.",
        "",
        "Como ler: barra azul à esquerda = trilho de energia; contato `| |` = leitura de variável (com `/` vermelho é **negado**, NF); "
        "círculo verde = bobina (saída); `S`/`R` = set/reset; caixas = blocos de função (`TON`, `Util.PID`, `CTU`, `R_TRIG`).",
        "",
        "Convenções do projeto: **um único escritor por saída**; PID **sem contatos antes** (roda todo ciclo, o bloqueio é no `RESET` e no portão do SSR); "
        "entradas de segurança são ativas em baixo (`SEG_OK = 0` é falha).",
        "",
    ]
    for nid, name, titles in index:
        lines += [f"## Rede {nid:02d}" if nid else "## Redes auxiliares", "", DESC.get(nid, ""), "",
                  f"![Rede {nid:02d}](media/ladder/{name})", ""]
    (ROOT / "docs" / "LADDER.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    idx = render()
    write_doc(idx)
    print("gerado:", len(idx), "imagens em", OUT)
