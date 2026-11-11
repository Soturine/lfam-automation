import { useState } from "react";
import type { Live } from "../useLive";
import { api } from "../api";
import { num } from "../format";
import { Panel } from "../components/ui";

export const RECIPE = {
  name: "PEI + 20% fibra de carbono",
  note: "Valores iniciais propostos no TG (centro das faixas do datasheet). Referência acadêmica; não validada em máquina.",
  sp: { Z1: 340, Z2: 350, Z3: 350, Z4: 360, Z5: 360 } as Record<string, number>,
  limits: { Z1: [330, 375], Z2: [330, 375], Z3: [330, 375], Z4: [330, 375], Z5: [345, 375] } as Record<string, [number, number]>,
  rpm: 25,
};

export function Recipes({ live }: { live: Live }) {
  const { snap, status, addEvent } = live;
  const [result, setResult] = useState<string>("");
  if (!snap) return <div className="empty" role="status">Aguardando dados…</div>;
  const blocked = snap.flags.EST_EXTRUSAO || status === "SEM COMUNICAÇÃO";
  const apply = async () => {
    const msgs: string[] = [];
    for (const [k, v] of Object.entries(RECIPE.sp)) { const r = await api.setpoint(k, v); if (!r.accepted) msgs.push(`${k}: ${r.message}`); }
    const r = await api.setpoint("RPM", RECIPE.rpm); if (!r.accepted) msgs.push(`RPM: ${r.message}`);
    setResult(msgs.length ? `Recusado: ${msgs.join("; ")}` : "Receita aplicada. Confira os setpoints lidos de volta abaixo.");
    addEvent("COMANDO", msgs.length ? "Receita recusada" : `Receita "${RECIPE.name}" aplicada`);
  };
  return (
    <div className="grid two">
      <Panel title={`Receita: ${RECIPE.name}`}>
        <p className="hint">{RECIPE.note}</p>
        <table className="tbl">
          <thead><tr><th>Parâmetro</th><th>Receita</th><th>Limites</th><th>Atual (lido)</th></tr></thead>
          <tbody>
            {Object.entries(RECIPE.sp).map(([z, v]) => (
              <tr key={z}><th scope="row">{z === "Z5" ? "Z5 · Bico" : z}</th><td className="n">{num(v, 0)} °C</td><td className="n">{RECIPE.limits[z][0]}–{RECIPE.limits[z][1]}</td>
                <td className={`n ${snap.setpoints[z] === v ? "ok" : "warn"}`}>{num(snap.setpoints[z], 0)} °C</td></tr>
            ))}
            <tr><th scope="row">Rotação</th><td className="n">{RECIPE.rpm} rpm</td><td className="n">17–34</td><td className={`n ${snap.setpoints.RPM === RECIPE.rpm ? "ok" : "warn"}`}>{num(snap.setpoints.RPM, 0)} rpm</td></tr>
          </tbody>
        </table>
        <button className="btn" disabled={blocked} onClick={apply}>Aplicar receita</button>
        {blocked && <p className="hint">Bloqueado durante extrusão ou sem comunicação.</p>}
        {result && <p className="hint" role="status">{result}</p>}
      </Panel>
      <Panel title="Regras">
        <ul className="rules">
          <li>Setpoints fora das faixas são recusados pela API e pelo formulário.</li>
          <li>Alterações são confirmadas pela leitura de volta (coluna “Atual”).</li>
          <li>Histórico de alterações: registrado em Alarmes → Eventos da sessão.</li>
          <li>A edição de limites por senha (proposta do grupo) <b>não</b> foi implementada.</li>
        </ul>
      </Panel>
    </div>
  );
}
