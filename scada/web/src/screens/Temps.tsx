import { useState } from "react";
import type { Live } from "../useLive";
import { api } from "../api";
import { num } from "../format";
import { TrendChart } from "../components/TrendChart";
import { Panel } from "../components/ui";

const LIMITS: Record<string, [number, number]> = { Z1: [330, 375], Z2: [330, 375], Z3: [330, 375], Z4: [330, 375], Z5: [345, 375] };

export function Temps({ live }: { live: Live }) {
  const { snap, history, paused, setPaused, status } = live;
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [err, setErr] = useState<Record<string, string>>({});
  if (!snap) return <div className="empty" role="status">Aguardando dados…</div>;
  const locked = snap.flags.EST_EXTRUSAO || status === "SEM COMUNICAÇÃO";

  const apply = async (z: string) => {
    const v = Number((draft[z] ?? "").replace(",", "."));
    const [lo, hi] = LIMITS[z];
    if (Number.isNaN(v) || v < lo || v > hi) { setErr((e) => ({ ...e, [z]: `Faixa permitida: ${lo}–${hi} °C` })); return; }
    const r = await api.setpoint(z, v);
    setErr((e) => ({ ...e, [z]: r.accepted ? "" : r.message }));
    if (r.accepted) setDraft((d) => ({ ...d, [z]: "" }));
  };

  return (
    <div className="grid two">
      <Panel title="Tendência das cinco zonas" right={<button className="btn small" onClick={() => setPaused(!paused)}>{paused ? "Retomar" : "Pausar"}</button>}>
        <TrendChart data={history} series="temps" />
      </Panel>
      <Panel title="Malhas PID Z1–Z5">
        <table className="tbl">
          <thead><tr><th>Zona</th><th>PV (°C)</th><th>SP (°C)</th><th>SSR (%)</th><th>Novo SP</th></tr></thead>
          <tbody>
            {(["Z1", "Z2", "Z3", "Z4", "Z5"] as const).map((z) => (
              <tr key={z}>
                <th scope="row">{z === "Z5" ? "Z5 · Bico" : z}</th>
                <td className="n">{num(snap.temps[z], 1)}</td>
                <td className="n">{num(snap.setpoints[z], 0)}</td>
                <td className="n">{num((snap.ssr_duty[z] ?? 0) * 100, 0)}</td>
                <td>
                  <div className="sp-edit">
                    <input aria-label={`Novo setpoint ${z}`} inputMode="decimal" disabled={locked} value={draft[z] ?? ""} placeholder={`${LIMITS[z][0]}–${LIMITS[z][1]}`}
                      onChange={(e) => setDraft((d) => ({ ...d, [z]: e.target.value }))} onKeyDown={(e) => e.key === "Enter" && apply(z)} />
                    <button className="btn small" disabled={locked || !(draft[z] ?? "")} onClick={() => apply(z)}>Aplicar</button>
                  </div>
                  {err[z] && <small className="cmd-msg" role="alert">{err[z]}</small>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {locked && <p className="hint">Ajuste de setpoint bloqueado durante extrusão ou sem comunicação.</p>}
        <p className="hint">Encharque: {snap.flags.ENCH_OK ? "concluído" : snap.flags.EST_ENCHARQUE ? "em andamento (todas as zonas ≥ 330 °C)" : "aguardando zonas ≥ 330 °C"} · trecho sem resistência {num(snap.tt_zsr, 0)} °C · câmara {num(snap.tt_resf, 0)} °C</p>
      </Panel>
    </div>
  );
}
