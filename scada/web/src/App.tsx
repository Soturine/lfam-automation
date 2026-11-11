import { useCallback, useEffect, useState } from "react";
import { useLive } from "./useLive";
import { useCommand } from "./api";
import { Overview } from "./screens/Overview";
import { Temps } from "./screens/Temps";
import { Deposition } from "./screens/Deposition";
import { Alarms } from "./screens/Alarms";
import { Recipes } from "./screens/Recipes";
import { History } from "./screens/History";
import { STATE_LABEL } from "./format";

const TABS = [
  { id: "overview", label: "Visão geral" },
  { id: "temps", label: "Temperaturas / PID" },
  { id: "dep", label: "Deposição / IR" },
  { id: "alarms", label: "Alarmes" },
  { id: "recipes", label: "Receitas" },
  { id: "history", label: "Histórico" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function App() {
  const live = useLive();
  const [tab, setTab] = useState<TabId>(() => (TABS.find((t) => t.id === location.hash.slice(1))?.id ?? "overview"));
  const log = useCallback((k: "COMANDO", t: string) => live.addEvent(k, t), [live.addEvent]); // eslint-disable-line react-hooks/exhaustive-deps
  const { phase, msg, send } = useCommand(live.snap, log);

  useEffect(() => { history.replaceState(null, "", `#${tab}`); }, [tab]);
  const idx = TABS.findIndex((t) => t.id === tab);
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") setTab(TABS[(idx + 1) % TABS.length].id);
    if (e.key === "ArrowLeft") setTab(TABS[(idx + TABS.length - 1) % TABS.length].id);
  };

  const { status, snap, ageMs } = live;
  const tone = status === "SEM COMUNICAÇÃO" ? "bad" : status === "CONECTANDO" ? "warn" : status === "DEMO" ? "demo" : "ok";
  const age = Number.isFinite(ageMs) ? `${(Math.max(0, ageMs) / 1000).toFixed(1).replace(".", ",")} s` : "—";
  const stale = status === "SEM COMUNICAÇÃO";

  return (
    <div className="app">
      <header className="top">
        <div className="brand"><b>LFAM</b><span>/ Supervisão da extrusora</span></div>
        <div className="status" aria-live="polite">
          <span className={`link ${tone}`}>{status}</span>
          {snap && <span className="meta">último dado há {age}{stale ? "" : ` · t sim. ${snap.t_sim_s.toFixed(0)} s`}</span>}
          {snap?.mode === "DEMO" && <span className="badge-demo">DEMO / SIMULADO</span>}
          {snap?.mode === "PLC" && <span className="badge-demo">LÓGICA NO CLP · PLANTA SIMULADA</span>}
          {snap && <span className={`state ${snap.state === "FALHA_TRAVADA" ? "bad" : ""}`}>{stale ? "estado desatualizado" : STATE_LABEL[snap.state]}</span>}
        </div>
      </header>
      {stale && <div className="banner bad" role="alert">Sem comunicação com a API ou com o controlador (heartbeat parado). Comandos desabilitados; valores abaixo estão desatualizados e podem não refletir a máquina.</div>}
      <nav className="tabs" role="tablist" aria-label="Telas" onKeyDown={onKey}>
        {TABS.map((t, i) => (
          <button key={t.id} role="tab" aria-selected={tab === t.id} tabIndex={tab === t.id ? 0 : -1} className={tab === t.id ? "active" : ""} onClick={() => setTab(t.id)}>
            <small>{String(i + 1).padStart(2, "0")}</small> {t.label}
          </button>
        ))}
      </nav>
      <main key={tab} className="enter" role="tabpanel" aria-label={TABS[idx].label}>
        {tab === "overview" && <Overview live={live} phase={phase} msg={msg} send={send} />}
        {tab === "temps" && <Temps live={live} />}
        {tab === "dep" && <Deposition live={live} />}
        {tab === "alarms" && <Alarms live={live} phase={phase} msg={msg} send={send} />}
        {tab === "recipes" && <Recipes live={live} />}
        {tab === "history" && <History live={live} />}
      </main>
      <footer>Projeto educacional / simulação · não substitui parada de emergência nem segurança certificada · tela {String(idx + 1).padStart(2, "0")}/06</footer>
    </div>
  );
}
