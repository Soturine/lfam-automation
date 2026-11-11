import type { Snapshot } from "../types";
import { num } from "../format";

/** Sinótico vetorial. Cores e animação derivam de FLAGS reais do snapshot (nunca de timer cosmético). */
export function Synoptic({ snap, stale }: { snap: Snapshot; stale: boolean }) {
  const f = snap.flags;
  const extruding = f.EST_EXTRUSAO && !stale;
  const zones = ["Z1", "Z2", "Z3", "Z4", "Z5"] as const;
  const zx = (i: number) => 250 + i * 132;
  const heat = (z: string) => (snap.ssr_duty[z] ?? 0) > 0.02 && f.K1_AQUEC && !stale;
  const dim = stale ? 0.45 : 1;
  return (
    <svg viewBox="0 0 1000 380" role="img" aria-label="Sinótico da extrusora LFAM" className="synoptic" style={{ opacity: dim }}>
      <defs>
        <pattern id="flow" width="24" height="12" patternUnits="userSpaceOnUse">
          <circle cx="4" cy="6" r="2.2" fill="var(--amber)" />
        </pattern>
      </defs>
      {/* dosador */}
      <text x="40" y="26" className="svg-label">DOSADOR</text>
      <polygon points="40,40 130,40 108,110 62,110" className="part" />
      <rect x="76" y="110" width="18" height="58" className="part" />
      {f.ALIM_FUNIL && <text x="140" y="75" className="svg-tag on">ALIM_FUNIL ligado</text>}
      {/* camara de resfriamento */}
      <rect x="150" y="150" width="76" height="86" rx="6" className={f.RESF_ON ? "part cool-on" : "part"} />
      <text x="188" y="186" textAnchor="middle" className="svg-small">Resfr.</text>
      <text x="188" y="210" textAnchor="middle" className="svg-val">{num(snap.tt_resf, 0)} °C</text>
      {/* cilindro */}
      <rect x="236" y="150" width="680" height="86" rx="8" className="barrel" />
      <g className={extruding ? "screw run" : "screw"}>
        <path d="M250,193 q22,-30 44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0 t44,0" fill="none" strokeWidth="3" />
      </g>
      {/* resistencias e rotulos */}
      {zones.map((z, i) => (
        <g key={z}>
          <rect x={zx(i) - 4} y="238" width="116" height="12" rx="3" className={heat(z) ? "heater on" : "heater"} />
          <rect x={zx(i) - 8} y="94" width="124" height="48" rx="6" className="zonebox" />
          <text x={zx(i) + 54} y="112" textAnchor="middle" className="svg-small">{i === 4 ? "Z5 · Bico" : z}</text>
          <text x={zx(i) + 54} y="134" textAnchor="middle" className="svg-val">{num(snap.temps[z], 0)} °C</text>
        </g>
      ))}
      {/* bico + fluxo */}
      <polygon points="916,160 960,178 960,208 916,226" className="part" />
      {extruding && <rect x="960" y="190" width="30" height="12" fill="url(#flow)" className="flow" />}
      <text x="930" y="278" className="svg-label">BICO</text>
      {/* deposicao + IR */}
      <rect x="800" y="330" width="190" height="16" className="part" />
      {extruding && <rect x="820" y="318" width="150" height="10" className="bead" />}
      <text x="800" y="366" className="svg-label">DEPOSIÇÃO</text>
      {f.SSR_IR && <path d="M850,290 l15,24 l15,-24 l15,24 l15,-24" className="ir" fill="none" />}
      <text x="700" y="312" className="svg-small">IR {f.SSR_IR ? "ON" : "OFF"} · robô {f.IR_HAB ? "em mov." : "—"}</text>
      {/* motor / inversor */}
      <rect x="20" y="290" width="130" height="64" rx="8" className="part" />
      <text x="85" y="314" textAnchor="middle" className="svg-small">MOTOR · INV</text>
      <text x="85" y="338" textAnchor="middle" className="svg-val">{num(snap.rpm_real, 1)} rpm</text>
      <line x1="118" y1="290" x2="160" y2="238" className="shaft" />
      <rect x="170" y="296" width="110" height="26" rx="5" className={f.VENT_MOTOR ? "badge on" : "badge"} />
      <text x="225" y="314" textAnchor="middle" className="svg-small">VENT {f.VENT_MOTOR ? "ON" : "OFF"}</text>
      {/* pressao */}
      <text x="560" y="312" className="svg-small">Pressão do fundido</text>
      <text x="560" y="336" className="svg-val">{num(snap.pressure_mpa, 1)} MPa</text>
    </svg>
  );
}
