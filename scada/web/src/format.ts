const nf = (d: number) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d });
const cache: Record<number, Intl.NumberFormat> = {};

/** Número em formato pt-BR (vírgula decimal) com d casas. */
export function num(v: number | undefined | null, d = 1): string {
  if (v === undefined || v === null || Number.isNaN(v)) return "--";
  return (cache[d] ??= nf(d)).format(v);
}

export function duration(sec: number): string {
  const s = Math.max(0, Math.round(sec));
  const m = Math.floor(s / 60);
  return `${String(m).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

export const STATE_LABEL: Record<string, string> = {
  DESLIGADO: "Desligado",
  AQUECIMENTO: "Aquecimento",
  ENCHARQUE: "Encharque",
  PRONTO: "Pronto",
  EXTRUSAO: "Extrusão",
  FALHA_TRAVADA: "Falha travada",
};

export const CAUSE_LABEL: Record<string, string> = {
  SEG_OK: "Emergência / porta (SEG_OK = 0)",
  MOT_SOBRETEMP: "Sobretemperatura do motor",
  INV_FALHA: "Falha do inversor",
  PRESSAO_ALTA_17: "Pressão ≥ 17 MPa",
  SOBRETEMP_400: "Zona acima de 400 °C",
  TC_FAULT: "Termopar rompido",
  FALHA_RESF_2M: "Câmara de resfriamento > 100 °C por 2 min",
  FALHA_SEM_MAT: "Sem material por 60 s",
  FALHA_VENT_10S: "Rosca sem ventilação por 10 s",
  FALHA_K1_COL: "Contator K1 colado",
};

/** Tabela CSV com separador ; (Excel pt-BR) e BOM. */
export function toCsv(rows: Record<string, string | number>[]): string {
  if (!rows.length) return "﻿";
  const head = Object.keys(rows[0]);
  const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
  return "﻿" + [head.join(";"), ...rows.map((r) => head.map((h) => esc(r[h])).join(";"))].join("\r\n");
}
