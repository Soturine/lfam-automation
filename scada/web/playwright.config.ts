import { defineConfig } from "@playwright/test";

// Pré-requisitos (não iniciados aqui): backend em :8000 (LFAM_TIME_SCALE=30) e `npm run dev` em :5173. Ver docs/SCADA_RUN.md.
export default defineConfig({
  testDir: "./e2e",
  timeout: 240_000,
  workers: 1,
  use: { baseURL: process.env.PW_BASE ?? "http://127.0.0.1:5173", trace: "off" },
  reporter: [["list"]],
});
