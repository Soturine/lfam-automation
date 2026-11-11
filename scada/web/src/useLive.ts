import { useCallback, useEffect, useRef, useState } from "react";
import type { EventRow, LinkStatus, Sample, Snapshot } from "./types";
import { CAUSE_LABEL, STATE_LABEL } from "./format";

const STALE_MS = 2500;
const HISTORY = 900;

export interface Live {
  snap: Snapshot | null;
  status: LinkStatus;
  ageMs: number;
  history: Sample[];
  events: EventRow[];
  paused: boolean;
  setPaused: (p: boolean) => void;
  addEvent: (kind: EventRow["kind"], text: string) => void;
}

/** Dados ao vivo via WebSocket com reconexão automática. Sem dados válidos => SEM COMUNICAÇÃO (nunca "verde falso"). */
export function useLive(): Live {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [now, setNow] = useState(Date.now());
  const [history, setHistory] = useState<Sample[]>([]);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [paused, setPaused] = useState(false);
  const lastRx = useRef(0);
  const prev = useRef<Snapshot | null>(null);
  const idSeq = useRef(1);
  const pausedRef = useRef(false);
  pausedRef.current = paused;

  const addEvent = useCallback((kind: EventRow["kind"], text: string) => {
    setEvents((e) => [...e, { id: idSeq.current++, time: new Date().toLocaleTimeString("pt-BR"), tSim: prev.current?.t_sim_s ?? 0, kind, text }].slice(-500));
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let timer: number | undefined;
    let closed = false;
    const open = () => {
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/ws`);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        if (!closed) timer = window.setTimeout(open, 1500);
      };
      ws.onerror = () => ws?.close();
      ws.onmessage = (m) => {
        const s: Snapshot = JSON.parse(m.data);
        lastRx.current = Date.now();
        const p = prev.current;
        if (p && p.state !== s.state) {
          addEvent(s.state === "FALHA_TRAVADA" ? "FALHA" : "ESTADO", `${STATE_LABEL[p.state]} → ${STATE_LABEL[s.state]}`);
        }
        if (s.state === "FALHA_TRAVADA" && s.latched_causes.length) {
          const novas = s.latched_causes.filter((c) => !p?.latched_causes.includes(c));
          novas.forEach((c) => addEvent("FALHA", CAUSE_LABEL[c] ?? c));
        }
        if (p && !p.flags.ALM_PRESSAO_16_5 && s.flags.ALM_PRESSAO_16_5) addEvent("ALARME", "Pré-alarme de pressão (≥ 16,5 MPa)");
        if (p && !p.flags.ALM_ZSR_BAIXA && s.flags.ALM_ZSR_BAIXA) addEvent("ALARME", "Trecho sem resistência abaixo de 220 °C");
        prev.current = s;
        setSnap(s);
        if (!pausedRef.current) {
          const zs = [s.temps.Z1, s.temps.Z2, s.temps.Z3, s.temps.Z4, s.temps.Z5];
          const sps = [1, 2, 3, 4, 5].map((i) => s.setpoints[`Z${i}`]);
          setHistory((h) => [...h, { t: s.t_sim_s, z: zs, sp: sps, p: s.pressure_mpa, rpm: s.rpm_real }].slice(-HISTORY));
        }
      };
    };
    open();
    const tick = window.setInterval(() => setNow(Date.now()), 500);
    return () => {
      closed = true;
      window.clearTimeout(timer);
      window.clearInterval(tick);
      ws?.close();
    };
  }, [addEvent]);

  const ageMs = lastRx.current ? now - lastRx.current : Infinity;
  let status: LinkStatus = "CONECTANDO";
  if (snap) {
    if (!connected || ageMs > STALE_MS) status = "SEM COMUNICAÇÃO";
    else status = snap.mode === "DEMO" ? "DEMO" : "CLP CONECTADO";
  } else if (!connected && lastRx.current) {
    status = "SEM COMUNICAÇÃO";
  }
  return { snap, status, ageMs, history, events, paused, setPaused, addEvent };
}
