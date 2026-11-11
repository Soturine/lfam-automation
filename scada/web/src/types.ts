export type ProcState = "DESLIGADO" | "AQUECIMENTO" | "ENCHARQUE" | "PRONTO" | "EXTRUSAO" | "FALHA_TRAVADA";

export interface Snapshot {
  mode: "DEMO" | "PLC";
  source: string;
  plc_connected: boolean;
  link_error?: string;
  t_sim_s: number;
  timestamp: number;
  state: ProcState;
  temps: Record<"Z1" | "Z2" | "Z3" | "Z4" | "Z5", number>;
  setpoints: Record<string, number>;
  ssr_duty: Record<string, number>;
  tt_zsr: number;
  tt_resf: number;
  tt_substrato: number;
  pressure_mpa: number;
  rpm_ref: number;
  rpm_real: number;
  flags: Record<string, boolean>;
  causes: string[];
  latched_causes: string[];
  log: { t_sim_s: number; msg: string }[];
}

export type LinkStatus = "CONECTANDO" | "DEMO" | "CLP CONECTADO" | "SEM COMUNICAÇÃO";

export interface Sample {
  t: number;
  z: number[];
  sp: number[];
  p: number;
  rpm: number;
}

export interface EventRow {
  id: number;
  time: string;
  tSim: number;
  kind: "ESTADO" | "FALHA" | "ALARME" | "COMANDO";
  text: string;
}
