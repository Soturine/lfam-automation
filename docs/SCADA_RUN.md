# Executar o SCADA (modo DEMO)

Pré-requisitos: Python 3.12 com `.venv` (`pip install -r requirements-dev.txt`) e Node LTS (`cd scada/web; npm install`).

```powershell
# 1) backend DEMO (LFAM_TIME_SCALE acelera o relógio simulado; 1 = tempo real, 30 = encharque de 15 min em ~30 s)
$env:LFAM_TIME_SCALE = "30"
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000

# 2) frontend (em outro terminal)
cd scada\web
npm run dev          # http://127.0.0.1:5173
```

Testes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests          # simulador, Ladder gerado, backend DEMO
cd scada\web; npm run build                            # tsc + vite
npx playwright install chromium                        # uma vez
npx playwright test                                    # E2E; exige backend (:8000, fator 30) e `npm run dev` ativos; grava docs/evidence/scada/
```

**Modo CLP:** ainda **não existe**. A API só expõe `mode: "DEMO"` e `plc_connected: false`; a interface mostra o selo
`DEMO / SIMULADO`. A lógica do modo DEMO é o programa Ladder gerado (`codesys/generator`) executado por um avaliador em Python,
**não** o Control Win. Ver `docs/evidence/` para o que está comprovado.
