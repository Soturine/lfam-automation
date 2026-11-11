import { expect, test, type Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const OUT = path.resolve(process.cwd(), "../../docs/evidence/scada");
const SIZES = [
  { name: "1920x1080", width: 1920, height: 1080 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "390x844", width: 390, height: 844 },
] as const;
const TABS = ["Visão geral", "Temperaturas / PID", "Deposição / IR", "Alarmes", "Receitas", "Histórico"];

fs.mkdirSync(OUT, { recursive: true });

async function api(page: Page, url: string, body: unknown) {
  await page.request.post(url, { data: body });
}

async function noHorizontalScroll(page: Page) {
  const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(over, "scroll horizontal da página").toBeLessThanOrEqual(1);
}

test("seis telas, comando confirmado pelo controlador, falha e sem comunicação", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.setViewportSize({ width: 1920, height: 1080 });
  await page.goto("/");
  await expect(page.locator(".link")).toHaveText("DEMO", { timeout: 15_000 });
  await expect(page.getByText("DEMO / SIMULADO").first()).toBeVisible();

  // modo apresentacao: selecionavel no site (so DEMO); o relogio simulado passa a 90x
  await page.getByRole("button", { name: /Apresentação/ }).click();
  await expect(page.getByRole("button", { name: /Apresentação/ })).toHaveAttribute("aria-pressed", "true");
  expect((await (await page.request.get("/api/state")).json()).time_scale).toBe(90);

  // estado inicial: desligado, K1 aberto; botao de extrusao desabilitado (programa nao esta PRONTO)
  await expect(page.getByRole("button", { name: "Iniciar extrusão" })).toBeDisabled();

  // comando = solicitacao; sucesso somente apos o programa confirmar
  await page.getByRole("button", { name: "Ligar aquecimento" }).click();
  await expect(page.getByRole("button", { name: /Aguardando CLP|Confirmado/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "✓ Confirmado" })).toBeVisible({ timeout: 10_000 });

  // modo apresentacao: encharque de 15 min simulados em poucos segundos reais
  await expect(page.locator(".state")).toHaveText("Pronto", { timeout: 60_000 });
  await page.getByRole("button", { name: "Iniciar extrusão" }).click();
  await expect(page.locator(".state")).toHaveText("Extrusão", { timeout: 15_000 });
  await page.waitForTimeout(8_000);

  // um estado pendente (botao aguardando) para captura
  await page.waitForTimeout(750); // espera a animacao de entrada terminar
  await page.screenshot({ path: path.join(OUT, "estado_nominal_1920x1080_visao_geral.png") });

  // seis telas em quatro tamanhos
  for (const size of SIZES) {
    await page.setViewportSize({ width: size.width, height: size.height });
    for (let i = 0; i < TABS.length; i++) {
      await page.getByRole("tab", { name: new RegExp(TABS[i].replace("/", "\/")) }).click();
      await expect(page.getByRole("tabpanel")).toBeVisible();
      await noHorizontalScroll(page);
      await page.waitForTimeout(250);
      await page.waitForTimeout(750); // espera a animacao de entrada terminar
      await page.screenshot({ path: path.join(OUT, `tela${i + 1}_${size.name}.png`), fullPage: size.width < 1100 });
    }
  }

  // setpoint fora da faixa e recusado no formulario
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.getByRole("tab", { name: /Temperaturas/ }).click();
  await expect(page.getByLabel("Novo setpoint Z1")).toBeDisabled(); // bloqueado em extrusao

  // injecao de falha (DEMO) -> programa trava a falha
  await api(page, "/api/demo/fault", { fault: "pressure_high", on: true });
  await expect(page.locator(".state")).toHaveText("Falha travada", { timeout: 20_000 });
  await page.getByRole("tab", { name: "Alarmes" }).click();
  await expect(page.locator(".tag.bad", { hasText: "FALHA TRAVADA" })).toBeVisible();
  await page.waitForTimeout(750); // espera a animacao de entrada terminar
  await page.screenshot({ path: path.join(OUT, "estado_alarme_1440x900_alarmes.png") });
  await api(page, "/api/demo/fault", { fault: "pressure_high", on: false });

  // reset condicionado: botao confirma apenas quando o programa libera
  await page.getByRole("button", { name: "Reconhecer e resetar" }).click();
  await expect(page.locator(".state")).not.toHaveText("Falha travada", { timeout: 15_000 });

  // historico exporta CSV
  await page.getByRole("tab", { name: "Histórico" }).click();
  const dl = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar CSV" }).click();
  expect((await dl).suggestedFilename()).toContain("lfam-eventos");

  // navegacao por teclado
  await page.getByRole("tab", { name: "Histórico" }).focus();
  await page.keyboard.press("ArrowLeft");
  await expect(page.getByRole("tab", { name: /Receitas/ })).toHaveAttribute("aria-selected", "true");

  expect(errors, "erros de console").toEqual([]);
});

test("sem comunicacao: dados param e a interface nao mostra verde falso", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  let forwarded = 0;
  await page.routeWebSocket(/\/ws$/, (ws) => {
    const server = ws.connectToServer();
    server.onMessage((m) => { if (forwarded++ < 2) ws.send(m); }); // repassa so 2 mensagens e "congela"
  });
  await page.goto("/");
  await expect(page.locator(".link")).toHaveText("SEM COMUNICAÇÃO", { timeout: 15_000 });
  await expect(page.getByRole("alert").first()).toContainText("Sem comunicação");
  await expect(page.getByRole("button", { name: "Ligar aquecimento" })).toBeDisabled();
  await expect(page.locator(".pills.stale")).toBeVisible(); // sem verde falso
  await page.waitForTimeout(750); // espera a animacao de entrada terminar
  await page.screenshot({ path: path.join(OUT, "estado_sem_comunicacao_1440x900_visao_geral.png") });
});
