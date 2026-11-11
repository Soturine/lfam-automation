import type { Live } from "../useLive";
import { num, STATE_LABEL } from "../format";
import { Synoptic } from "../components/Synoptic";
import { CmdButton, Kpi, Panel, Pill, Skeleton } from "../components/ui";
import { TrendChart } from "../components/TrendChart";
import type { CmdPhase } from "../api";

interface Props { live: Live; phase: Record<string, CmdPhase>; msg: Record<string, string>; send: (n: string) => void }

export function Overview({ live, phase, msg, send }: Props) {
  const { snap, status } = live;
  if (!snap) return <div className="grid overview"><div className="kpis">{Array.from({ length: 5 }, (_, i) => <div className="kpi" key={i}><Skeleton rows={2} /></div>)}</div><Panel title="Aguardando o primeiro dado da API…" className="syn"><Skeleton rows={5} /></Panel></div>;
  const stale = status === "SEM COMUNICAÇÃO";
  const f = snap.flags;
  const down = stale;
  const tone = snap.state === "FALHA_TRAVADA" ? "bad" : snap.state === "EXTRUSAO" ? "ok" : "info";
  return (
    <div className="grid overview">
      <div className="kpis">
        <Kpi label="Estado do processo" value={STATE_LABEL[snap.state]} tone={stale ? undefined : tone} sub={stale ? "dado desatualizado" : "confirmado pelo programa"} />
        <Kpi label="Pressão do fundido" n={snap.pressure_mpa} digits={1} unit="MPa" tone={snap.pressure_mpa >= 16.5 ? "warn" : "info"} sub="pré-alarme 16,5 · parada 17" />
        <Kpi label="Rotação da rosca" n={snap.rpm_real} digits={1} unit="rpm" tone="info" sub={`referência ${num(snap.rpm_ref, 1)} · faixa 17–34`} />
        <Kpi label="Temperatura do bico" n={snap.temps.Z5} digits={0} unit="°C" tone="info" sub={`SP ${num(snap.setpoints.Z5, 0)} °C`} />
        <Kpi label="Segurança" value={snap.causes.includes("SEG_OK") ? "FALHA" : "OK"} tone={stale ? undefined : snap.causes.includes("SEG_OK") ? "bad" : "ok"} sub={stale ? "dado desatualizado" : "relé independente do CLP"} />
      </div>
      <Panel title="Sinótico do processo" className="syn" right={<span className="hint">Alimentação → fusão → deposição</span>}>
        <div className="syn-wrap"><Synoptic snap={snap} stale={stale} /></div>
      </Panel>
      <Panel title="Comandos (solicitações)">
        <p className="hint">Os botões só <b>solicitam</b>. O sucesso aparece quando o controlador confirma.</p>
        <div className="cmds">
          <CmdButton name="BT_AQUEC" label="Ligar aquecimento" phase={phase.BT_AQUEC} msg={msg.BT_AQUEC} disabled={down || f.EST_AQUEC} onSend={send} />
          <CmdButton name="BT_LIGA" label="Iniciar extrusão" phase={phase.BT_LIGA} msg={msg.BT_LIGA} disabled={down || !f.EST_PRONTO || f.EST_EXTRUSAO} onSend={send} />
          <CmdButton name="STOP" label="Parar extrusão" phase={phase.STOP} msg={msg.STOP} disabled={down || !f.EST_EXTRUSAO} danger onSend={send} />
          <CmdButton name="BT_RESET" label="Reset de falha" phase={phase.BT_RESET} msg={msg.BT_RESET} disabled={down || !f.FALHA_GERAL} onSend={send} />
        </div>
        <p className="hint warn-text">Esta interface <b>não é</b> parada de emergência. A emergência é hardware independente.</p>
      </Panel>
      <Panel title="Tendência das cinco zonas" className="trend-wide" right={<span className="hint">últimos instantes · dados reais do stream</span>}>
        <TrendChart data={live.history} series="temps" width={1900} height={200} />
      </Panel>
      <Panel title="Estado dos equipamentos">
        <ul className={`pills ${stale ? "stale" : ""}`}>
          <Pill ok={!snap.causes.includes("SEG_OK")} label="SEG_OK / porta" value={snap.causes.includes("SEG_OK") ? "FALHA" : "NORMAL"} />
          <Pill ok label="SECADOR_OK" value="NORMAL" />
          <Pill ok={!snap.causes.includes("INV_FALHA")} label="INV_PRONTO" value={snap.causes.includes("INV_FALHA") ? "FALHA" : "PRONTO"} />
          <Pill ok={f.K1_AQUEC} label="K1_AQUEC / K1_CONF" value={f.K1_AQUEC ? "FECHADO" : "ABERTO"} />
          <Pill ok={f.ENCH_OK ? true : "warn"} label="Encharque 15 min" value={f.ENCH_OK ? "CONCLUÍDO" : f.EST_ENCHARQUE ? "EM ANDAMENTO" : "AGUARDANDO"} />
          <Pill ok={f.RESF_ON ? "warn" : true} label="RESF_ON" value={f.RESF_ON ? "LIGADO" : "DESLIGADO"} />
          <Pill ok={f.VENT_MOTOR} label="VENT_MOTOR" value={f.VENT_MOTOR ? "LIGADO" : "DESLIGADO"} />
          <Pill ok={f.ROBO_EXT_PRONTA ? true : "warn"} label="ROBO_EXT_PRONTA" value={f.ROBO_EXT_PRONTA ? "SIM" : "NÃO"} />
        </ul>
      </Panel>
    </div>
  );
}
