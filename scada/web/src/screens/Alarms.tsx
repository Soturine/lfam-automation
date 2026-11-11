import { useState } from "react";
import type { Live } from "../useLive";
import type { CmdPhase } from "../api";
import { api } from "../api";
import { CAUSE_LABEL } from "../format";
import { CmdButton, Panel } from "../components/ui";

const FAULTS: [string, string][] = [
  ["estop_test", "Emergência lógica de teste (SEG_OK = 0)"], ["tc_open_3", "Termopar Z3 aberto"], ["pressure_high", "Pressão alta (bico entupido)"],
  ["funil_empty", "Funil vazio"], ["vent_fail", "Ventilação do motor ausente"], ["inv_fault", "Falha do inversor"], ["k1_stuck", "K1 colado"],
];

interface Props { live: Live; phase: Record<string, CmdPhase>; msg: Record<string, string>; send: (n: string) => void }

export function Alarms({ live, phase, msg, send }: Props) {
  const { snap, events, status } = live;
  const [filter, setFilter] = useState<"TODOS" | "FALHA" | "ALARME">("TODOS");
  const [active, setActive] = useState<Record<string, boolean>>({});
  if (!snap) return <div className="empty" role="status">Aguardando dados…</div>;
  const rows = events.filter((e) => filter === "TODOS" || e.kind === filter).slice().reverse();
  const warnings = [snap.flags.ALM_PRESSAO_16_5 && "Pré-alarme de pressão (≥ 16,5 MPa) — referência reduzida em 10%", snap.flags.ALM_ZSR_BAIXA && "Trecho sem resistência abaixo de 220 °C"].filter(Boolean) as string[];
  const down = status === "SEM COMUNICAÇÃO";
  const demo = !down; // injeção afeta só a PLANTA simulada (também no modo PLC)
  return (
    <div className="grid two">
      <Panel title="Alarmes ativos" right={snap.state === "FALHA_TRAVADA" ? <span className="tag bad">FALHA TRAVADA</span> : <span className="tag ok">SEM FALHA TRAVADA</span>}>
        {down && <p className="banner bad" role="alert">Sem comunicação: alarmes exibidos podem estar desatualizados.</p>}
        {snap.state === "FALHA_TRAVADA" && snap.latched_causes.length > 0 && (
          <p className="hint">Causa(s) que travaram a falha: <b>{snap.latched_causes.map((c) => CAUSE_LABEL[c] ?? c).join("; ")}</b>.{" "}
            {snap.causes.length ? "Ainda ativa(s): reset bloqueado." : "Já normalizada(s): o reset está liberado."}</p>)}
        <ul className="alarm-list">
          {snap.causes.map((c) => <li key={c} className="al bad"><b>FALHA</b><span>{CAUSE_LABEL[c] ?? c}</span><small>ativa agora</small></li>)}
          {warnings.map((w) => <li key={w} className="al warn"><b>AVISO</b><span>{w}</span><small>não trava</small></li>)}
          {!snap.causes.length && !warnings.length && <li className="al ok"><b>OK</b><span>Nenhum alarme ativo</span></li>}
        </ul>
        <CmdButton name="BT_RESET" label="Reconhecer e resetar" phase={phase.BT_RESET} msg={msg.BT_RESET} disabled={down || !snap.flags.FALHA_GERAL} onSend={send} />
        <p className="hint">O reset só é aceito pelo programa quando <b>nenhuma</b> causa crítica está ativa (M_CAUSA = 0).</p>
      </Panel>
      <Panel title="Eventos da sessão" right={
        <select aria-label="Filtro" value={filter} onChange={(e) => setFilter(e.target.value as typeof filter)}>
          <option value="TODOS">Todos</option><option value="FALHA">Falhas</option><option value="ALARME">Alarmes</option>
        </select>}>
        {rows.length === 0 ? <div className="empty small">Nenhum evento registrado nesta sessão.</div> : (
          <table className="tbl"><thead><tr><th>Hora</th><th>Tipo</th><th>Descrição</th></tr></thead>
            <tbody>{rows.slice(0, 30).map((e) => <tr key={e.id}><td className="n">{e.time}</td><td><span className={`tag ${e.kind === "FALHA" ? "bad" : e.kind === "ALARME" ? "warn" : "info"}`}>{e.kind}</span></td><td>{e.text}</td></tr>)}</tbody></table>
        )}
      </Panel>
      {demo && (
        <Panel title="Injeção de falhas na planta" right={<span className="badge-demo">{snap.mode === "DEMO" ? "DEMO / SIMULADO" : "PLANTA SIMULADA"}</span>}>
          <p className="hint">Afeta apenas a planta simulada (sensores/atuadores). O programa decide a reação.</p>
          <div className="faults">
            {FAULTS.map(([id, label]) => (
              <label key={id} className="chk"><input type="checkbox" checked={!!active[id]} onChange={async (e) => { setActive((a) => ({ ...a, [id]: e.target.checked })); await api.fault(id, e.target.checked); }} />{label}</label>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}
