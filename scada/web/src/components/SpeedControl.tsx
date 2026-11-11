import { useState } from "react";
import { api } from "../api";

const PRESETS = [
  { scale: 1, label: "Tempo real", hint: "1×: o relógio simulado anda como o relógio da parede" },
  { scale: 30, label: "Rápido", hint: "30×: encharque de 15 min em ~30 s" },
  { scale: 90, label: "Apresentação", hint: "90×: da partida à extrusão em ~15 s — a demonstração inteira cabe em ~2 min" },
] as const;

/** Velocidade do relógio SIMULADO. Só existe no DEMO: no modo CLP os temporizadores são os do Ladder, em tempo real. */
export function SpeedControl({ mode, scale, onLog }: { mode: "DEMO" | "PLC"; scale: number; onLog: (k: "COMANDO", t: string) => void }) {
  const [busy, setBusy] = useState(false);
  if (mode === "PLC") return <span className="speed real" title="Os temporizadores são os do Ladder no CLP: não dá para acelerar">tempo real (CLP)</span>;
  const pick = async (s: number) => {
    if (busy || s === scale) return;
    setBusy(true);
    try { const r = await api.speed(s); onLog("COMANDO", r.accepted ? `velocidade da simulação: ${s}×` : `velocidade recusada: ${r.message}`); } finally { setBusy(false); }
  };
  return (
    <div className={`speed ${scale >= 90 ? "present" : ""}`} role="group" aria-label="Velocidade da simulação">
      {PRESETS.map((p) => (
        <button key={p.scale} type="button" aria-pressed={scale === p.scale} title={p.hint} onClick={() => pick(p.scale)} disabled={busy}>
          {p.label}{p.scale > 1 && <small>{p.scale}×</small>}
        </button>
      ))}
    </div>
  );
}
