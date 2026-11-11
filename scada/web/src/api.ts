import { useCallback, useEffect, useRef, useState } from "react";
import type { Snapshot } from "./types";

export type CmdPhase = "idle" | "pendente" | "confirmado" | "negado";

async function post<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export const api = {
  command: (name: string) => post<{ accepted: boolean; message: string }>("/api/command", { name }),
  setpoint: (key: string, value: number) => post<{ accepted: boolean; message: string }>("/api/setpoint", { key, value }),
  fault: (fault: string, on: boolean) => post<{ accepted: boolean; message: string }>("/api/demo/fault", { fault, on }),
  robot: (r: { moving?: boolean; cmd?: boolean; auto?: boolean }) => post<{ accepted: boolean }>("/api/demo/robot", r),
};

/** Confirmação: o sucesso só é mostrado quando o ESTADO devolvido pelo programa muda; senão expira como "negado". */
export const CONFIRM: Record<string, (s: Snapshot) => boolean> = {
  BT_AQUEC: (s) => s.flags.EST_AQUEC,
  BT_LIGA: (s) => s.flags.EST_EXTRUSAO,
  STOP: (s) => !s.flags.EST_EXTRUSAO,
  BT_RESET: (s) => !s.flags.FALHA_GERAL,
};

const TIMEOUT_MS = 6000;

export function useCommand(snap: Snapshot | null, log: (k: "COMANDO", t: string) => void) {
  const [phase, setPhase] = useState<Record<string, CmdPhase>>({});
  const [msg, setMsg] = useState<Record<string, string>>({});
  const waiting = useRef<Record<string, number>>({});

  const check = useCallback(() => {
    if (!snap) return;
    for (const [name, since] of Object.entries(waiting.current)) {
      if (CONFIRM[name]?.(snap)) {
        delete waiting.current[name];
        setPhase((p) => ({ ...p, [name]: "confirmado" }));
        window.setTimeout(() => setPhase((p) => (p[name] === "confirmado" ? { ...p, [name]: "idle" } : p)), 3000);
        log("COMANDO", `${name}: confirmado pelo controlador`);
      } else if (Date.now() - since > TIMEOUT_MS) {
        delete waiting.current[name];
        setPhase((p) => ({ ...p, [name]: "negado" }));
        window.setTimeout(() => setPhase((p) => (p[name] === "negado" ? { ...p, [name]: "idle" } : p)), 8000);
        setMsg((m) => ({ ...m, [name]: "Sem confirmação do controlador (permissivos não atendidos?)" }));
        log("COMANDO", `${name}: NÃO confirmado pelo controlador`);
      }
    }
  }, [snap, log]);
  useEffect(() => {
    check();
  }, [check]);

  const send = useCallback(
    async (name: string) => {
      if (phase[name] === "pendente") return; // proteção contra duplo clique
      setPhase((p) => ({ ...p, [name]: "pendente" }));
      setMsg((m) => ({ ...m, [name]: "" }));
      try {
        const r = await api.command(name);
        if (!r.accepted) throw new Error(r.message);
        waiting.current[name] = Date.now();
        log("COMANDO", `${name}: solicitado`);
      } catch (e) {
        setPhase((p) => ({ ...p, [name]: "negado" }));
        setMsg((m) => ({ ...m, [name]: `Falha ao enviar: ${(e as Error).message}` }));
      }
    },
    [phase, log],
  );
  return { phase, msg, send };
}
