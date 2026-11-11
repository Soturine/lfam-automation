import { useMemo, useState } from "react";
import type { Live } from "../useLive";
import { toCsv } from "../format";
import { Panel } from "../components/ui";

export function History({ live }: { live: Live }) {
  const { events, snap } = live;
  const [kind, setKind] = useState("TODOS");
  const rows = useMemo(() => events.filter((e) => kind === "TODOS" || e.kind === kind), [events, kind]);
  const pareto = useMemo(() => {
    const c: Record<string, number> = {};
    events.filter((e) => e.kind === "FALHA" && !e.text.includes("→")).forEach((e) => { c[e.text] = (c[e.text] ?? 0) + 1; });
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  }, [events]);
  const max = pareto[0]?.[1] ?? 1;
  const exportCsv = () => {
    const blob = new Blob([toCsv(rows.map((e) => ({ hora: e.time, t_sim_s: e.tSim, tipo: e.kind, descricao: e.text })))], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `lfam-eventos-${snap?.mode ?? "x"}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  };
  return (
    <div className="grid two">
      <Panel title="Pareto de causas de falha (sessão)">
        {pareto.length === 0 ? <div className="empty small">Nenhuma falha registrada nesta sessão. Os dados são reais do stream; nada é preenchido artificialmente.</div> : (
          <ul className="pareto">{pareto.map(([k, v]) => <li key={k}><span>{k}</span><div className="bar"><i style={{ width: `${(v / max) * 100}%` }} /></div><b>{v}</b></li>)}</ul>
        )}
      </Panel>
      <Panel title="Histórico de eventos" right={
        <div className="row">
          <select aria-label="Tipo" value={kind} onChange={(e) => setKind(e.target.value)}><option>TODOS</option><option>ESTADO</option><option>FALHA</option><option>ALARME</option><option>COMANDO</option></select>
          <button className="btn small" onClick={exportCsv} disabled={!rows.length}>Exportar CSV</button>
        </div>}>
        {rows.length === 0 ? <div className="empty small">Sem eventos. Eles aparecem conforme o processo muda de estado.</div> : (
          <table className="tbl"><thead><tr><th>Hora</th><th>t sim. (s)</th><th>Tipo</th><th>Descrição</th></tr></thead>
            <tbody>{rows.slice().reverse().slice(0, 60).map((e) => <tr key={e.id}><td className="n">{e.time}</td><td className="n">{e.tSim.toFixed(0)}</td><td>{e.kind}</td><td>{e.text}</td></tr>)}</tbody></table>
        )}
        <p className="hint">Persistência: apenas nesta sessão do navegador. Duração por parada e banco de eventos persistente ainda não implementados.</p>
      </Panel>
    </div>
  );
}
