import type { Live } from "../useLive";
import { api } from "../api";
import { num } from "../format";
import { TrendChart } from "../components/TrendChart";
import { Kpi, Panel, Pill } from "../components/ui";

export function Deposition({ live }: { live: Live }) {
  const { snap, history, status } = live;
  if (!snap) return <div className="empty" role="status">Aguardando dados…</div>;
  const f = snap.flags;
  const demo = snap.mode === "DEMO" && status !== "SEM COMUNICAÇÃO";
  return (
    <div className="grid two">
      <div className="kpis">
        <Kpi label="Substrato (pirômetro)" value={num(snap.tt_substrato, 0)} unit="°C" tone="info" sub="faixa válida 20–480 °C" />
        <Kpi label="Saída IR" value={num((snap.ssr_duty.IR ?? 0) * 100, 0)} unit="%" tone={f.SSR_IR ? "ok" : "info"} sub={`SP ${num(snap.setpoints.IR, 0)} °C`} />
        <Kpi label="Rotação" value={num(snap.rpm_real, 1)} unit="rpm" tone="info" sub={`ref. ${num(snap.rpm_ref, 1)}`} />
        <Kpi label="Pressão" value={num(snap.pressure_mpa, 1)} unit="MPa" tone={snap.pressure_mpa >= 16.5 ? "warn" : "info"} />
      </div>
      <Panel title="Pressão do fundido"><TrendChart data={history} series="pressure" height={220} /></Panel>
      <Panel title="Habilitação do aquecedor IR">
        <ul className="pills">
          <Pill ok={f.EST_EXTRUSAO} label="Rosca girando" value={f.EST_EXTRUSAO ? "SIM" : "NÃO"} />
          <Pill ok={f.IR_HAB || f.SSR_IR ? true : "warn"} label="IR_HAB (robô em movimento + pirômetro na faixa)" value={f.IR_HAB ? "HABILITADO" : "BLOQUEADO"} />
          <Pill ok={f.SSR_IR ? true : "warn"} label="SSR_IR" value={f.SSR_IR ? "LIGADO" : "DESLIGADO"} />
        </ul>
        <p className="hint">O IR só liga com rosca e robô em movimento: parado, queimaria a peça no mesmo ponto. Deposição só é animada com a extrusão <b>confirmada</b>.</p>
        <p className="hint">Imagem térmica: não disponível (a câmera termográfica vai direto ao computador do SCADA, fora do escopo desta simulação).</p>
      </Panel>
      {demo && (
        <Panel title="Robô (somente DEMO)" right={<span className="badge-demo">DEMO / SIMULADO</span>}>
          <div className="cmds">
            <button className="btn small" onClick={() => api.robot({ moving: true })}>Robô em movimento</button>
            <button className="btn small" onClick={() => api.robot({ moving: false })}>Robô parado</button>
          </div>
        </Panel>
      )}
    </div>
  );
}
