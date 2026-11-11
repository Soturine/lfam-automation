import { useState } from "react";
import type { Sample } from "../types";
import { num } from "../format";

const WINDOW = 240; // amostras visiveis (janela deslizante); o historico completo fica no hook
const COLORS = ["#42C9E8", "#4ED5A3", "#F0BA58", "#B79CFF", "#EB6A73"];

interface Props {
  data: Sample[];
  series: "temps" | "pressure";
  height?: number;
  gapAfterMs?: number;
  /** largura logica do SVG: paineis largos usam valor maior para manter a tipografia proporcional */
  width?: number;
}

/** Tendência SVG com dados reais do stream. Sem dados => estado vazio explicativo (nunca curva fabricada). */
export function TrendChart({ data: all, series, height = 320, width = 900 }: Props) {
  const data = all.slice(-WINDOW);
  const [hover, setHover] = useState<number | null>(null);
  const W = width, H = height, L = 52, R = 12, T = 12, B = 26;
  if (data.length < 2) return <div className="empty" role="status">Aguardando amostras do controlador…</div>;
  const t0 = data[0].t, t1 = data[data.length - 1].t;
  const vals = (s: Sample, i: number) => (series === "temps" ? s.z[i] : s.p);
  const n = series === "temps" ? 5 : 1;
  let lo = Infinity, hi = -Infinity;
  data.forEach((s) => { for (let i = 0; i < n; i++) { const v = vals(s, i); lo = Math.min(lo, v); hi = Math.max(hi, v); } });
  if (series === "temps") { lo = Math.max(0, Math.min(lo, 300)); hi = Math.max(hi, 410); } else { lo = 0; hi = Math.max(hi, 18); }
  const pad = (hi - lo) * 0.05; lo -= pad; hi += pad;
  const x = (t: number) => L + ((t - t0) / Math.max(1, t1 - t0)) * (W - L - R);
  const y = (v: number) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
  const path = (i: number) => data.map((s, k) => `${k ? "L" : "M"}${x(s.t).toFixed(1)},${y(vals(s, i)).toFixed(1)}`).join(" ");
  const sp = (i: number) => data.map((s, k) => `${k ? "L" : "M"}${x(s.t).toFixed(1)},${y(s.sp[i]).toFixed(1)}`).join(" ");
  const ticks = Array.from({ length: 5 }, (_, k) => lo + ((hi - lo) * k) / 4);
  const lines: { v: number; label: string; cls: string }[] =
    series === "temps"
      ? [{ v: 390, label: "pré-alarme 390", cls: "warn" }, { v: 400, label: "falha 400", cls: "bad" }]
      : [{ v: 16.5, label: "pré-alarme 16,5", cls: "warn" }, { v: 17, label: "parada 17", cls: "bad" }];
  const idx = hover ?? data.length - 1;
  const cur = data[idx];
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={series === "temps" ? "Tendência das cinco zonas" : "Tendência da pressão"}
        onMouseMove={(e) => { const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect(); const px = ((e.clientX - r.left) / r.width) * W; setHover(Math.max(0, Math.min(data.length - 1, Math.round(((px - L) / (W - L - R)) * (data.length - 1))))); }}
        onMouseLeave={() => setHover(null)}>
        {ticks.map((v) => (<g key={v}><line x1={L} x2={W - R} y1={y(v)} y2={y(v)} className="grid" /><text x={L - 6} y={y(v) + 4} textAnchor="end" className="axis">{num(v, series === "temps" ? 0 : 1)}</text></g>))}
        {lines.map((l, k) => (<g key={l.label}><line x1={L} x2={W - R} y1={y(l.v)} y2={y(l.v)} className={`limit ${l.cls}`} /><text x={k === 0 ? L + 6 : W - R - 4} y={y(l.v) - 4} textAnchor={k === 0 ? "start" : "end"} className={`axis ${l.cls}`}>{l.label}</text></g>))}
        {series === "temps"
          ? [0, 1, 2, 3, 4].map((i) => (<g key={i}><path d={sp(i)} className="sp" stroke={COLORS[i]} /><path d={path(i)} fill="none" stroke={COLORS[i]} strokeWidth="2" /></g>))
          : <path d={path(0)} fill="none" stroke={COLORS[0]} strokeWidth="2" />}
        <text x={L} y={H - 6} className="axis">{num(t0, 0)} s</text>
        <text x={W - R} y={H - 6} textAnchor="end" className="axis">{num(t1, 0)} s (tempo simulado)</text>
        <line x1={x(cur.t)} x2={x(cur.t)} y1={T} y2={H - B} className="cursor" />
      </svg>
      <div className="legend" aria-live="off">
        {series === "temps"
          ? [0, 1, 2, 3, 4].map((i) => (<span key={i}><i style={{ background: COLORS[i] }} />Z{i + 1} <b>{num(cur.z[i], 1)} °C</b> <small>SP {num(cur.sp[i], 0)}</small></span>))
          : <span><i style={{ background: COLORS[0] }} />Pressão <b>{num(cur.p, 2)} MPa</b></span>}
      </div>
    </div>
  );
}
