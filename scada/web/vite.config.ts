import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// LFAM_API / LFAM_WEB_PORT permitem rodar o SCADA contra outro backend/porta (padrao: backend :8000, web :5173).
const api = process.env.LFAM_API ?? "127.0.0.1:8000";
export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.LFAM_WEB_PORT ?? 5173),
    proxy: { "/api": `http://${api}`, "/ws": { target: `ws://${api}`, ws: true } },
  },
});
