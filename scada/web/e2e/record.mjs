// Grava os GIFs do README: fluxo completo (desktop), tour das telas e fluxo no celular. Somente modo DEMO.
// Uso (na pasta scada/web, com backend DEMO e Vite no ar): PW_BASE=http://localhost:5180 API=http://127.0.0.1:8100 node e2e/record.mjs
import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE = process.env.PW_BASE ?? "http://localhost:5173";
const API = process.env.API ?? "http://127.0.0.1:8000";
const OUT = path.resolve("../../work/video");
fs.rmSync(OUT, { recursive: true, force: true }); fs.mkdirSync(OUT, { recursive: true });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = (p, b) => fetch(API + p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) });
const state = async (page) => (await page.locator(".state").innerText()).trim();
async function until(page, text, ms = 120000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { if ((await state(page)) === text) return; await sleep(300); } throw new Error("timeout " + text); }

const browser = await chromium.launch();

async function flow(name, size, tabs) {
  const ctx = await browser.newContext({ viewport: size, recordVideo: { dir: path.join(OUT, name), size } });
  const page = await ctx.newPage();
  await page.goto(BASE); await page.waitForSelector(".link"); await sleep(1800);
  await page.getByRole("button", { name: "Ligar aquecimento" }).click();
  await sleep(2500);
  await until(page, "Pronto");
  await sleep(1200);
  await page.getByRole("button", { name: "Iniciar extrusão" }).click();
  await until(page, "Extrusão", 20000); await sleep(3500);
  if (tabs) for (const t of [/Temperaturas/, /Deposição/, /Alarmes/]) { await page.getByRole("tab", { name: t }).click(); await sleep(2200); }
  await page.getByRole("tab", { name: "Visão geral" }).click(); await sleep(1200);
  await post("/api/demo/fault", { fault: "pressure_high", on: true });
  await until(page, "Falha travada", 20000); await sleep(1500);
  await page.getByRole("tab", { name: "Alarmes" }).click(); await sleep(3200);
  await post("/api/demo/fault", { fault: "pressure_high", on: false }); await sleep(1500);
  await page.getByRole("button", { name: "Reconhecer e resetar" }).click(); await sleep(3000);
  await page.getByRole("tab", { name: "Visão geral" }).click(); await sleep(1800);
  await ctx.close();
}

await flow("desktop", { width: 1280, height: 720 }, true);
await flow("mobile", { width: 390, height: 844 }, false);
await browser.close();
console.log("videos em", OUT);
