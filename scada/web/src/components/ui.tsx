import type { ReactNode } from "react";
import type { CmdPhase } from "../api";
import { useTween } from "../useTween";
import { num } from "../format";

export function Panel({ title, children, right, className = "" }: { title: string; children: ReactNode; right?: ReactNode; className?: string }) {
  return (
    <section className={`panel ${className}`}>
      <header><h2>{title}</h2>{right}</header>
      {children}
    </section>
  );
}

export function Kpi({ label, value, n, digits = 1, unit, sub, tone }: { label: string; value?: string; n?: number; digits?: number; unit?: string; sub?: string; tone?: "ok" | "warn" | "bad" | "info" }) {
  const t = useTween(n ?? 0);
  const shown = n !== undefined ? num(t, digits) : value;
  return (
    <div className={`kpi ${tone ?? ""}`}>
      <span className="kpi-label">{label}</span>
      <span className="kpi-value" key={n === undefined ? value : undefined}>{shown}{unit && <small>{unit}</small>}</span>
      {sub && <span className="kpi-sub">{sub}</span>}
    </div>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="skeleton" role="status" aria-label="Carregando">
      {Array.from({ length: rows }, (_, i) => <span key={i} style={{ width: `${88 - i * 14}%` }} />)}
    </div>
  );
}

export function Pill({ ok, label, value }: { ok: boolean | "warn"; label: string; value: string }) {
  const tone = ok === "warn" ? "warn" : ok ? "ok" : "bad";
  return (
    <li className="pill-row">
      <span className={`dot ${tone}`} aria-hidden="true" />
      <span>{label}</span>
      <b className={tone}>{value}</b>
    </li>
  );
}

export function CmdButton({ name, label, phase, msg, disabled, danger, onSend }: {
  name: string; label: string; phase?: CmdPhase; msg?: string; disabled?: boolean; danger?: boolean; onSend: (n: string) => void;
}) {
  const p = phase ?? "idle";
  const text = p === "pendente" ? "Aguardando CLP…" : p === "confirmado" ? "✓ Confirmado" : p === "negado" ? "✕ Negado" : label;
  const icon = p === "pendente" ? <i className="spin" aria-hidden="true" /> : null;
  return (
    <div className="cmd">
      <button className={`btn ${danger ? "danger" : ""} ${p}`} disabled={disabled || p === "pendente"} onClick={() => onSend(name)} aria-live="polite">
        {icon}{text}
      </button>
      {msg ? <small className="cmd-msg" role="alert">{msg}</small> : null}
    </div>
  );
}
