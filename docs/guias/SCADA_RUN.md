# Executar o SCADA

Pré-requisitos: Python 3.12 com `.venv` (`pip install -r requirements-dev.txt`) e Node LTS (`cd scada/web; npm install`).
Explicação geral do que é cada parte: [COMO_FUNCIONA.md](../entender/COMO_FUNCIONA.md).

## Modo DEMO (sem CODESYS)
```powershell
# 1) backend DEMO (LFAM_TIME_SCALE acelera o relógio simulado; 1 = tempo real, 30 = encharque de 15 min em ~30 s)
$env:LFAM_TIME_SCALE = "30"
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000

# 2) frontend (em outro terminal)
cd scada\web
npm run dev          # http://localhost:5173
```
A velocidade pode ser trocada **na própria tela** (seletor no topo, só no DEMO): **Tempo real**, **Rápido 30×** ou **Apresentação 90×** (partida até a extrusão em ~15 s; demonstração completa em ~2 min). Via API: `POST /api/demo/speed {"scale": 90}` (1 a 150).

A tela mostra o selo **DEMO / SIMULADO**: a lógica é o programa Ladder gerado executado por um avaliador em Python, **não** o Control Win.

## Modo PLC (Ladder rodando no CODESYS Control Win)
Exige o CODESYS com o servidor OPC UA configurado (certificados, símbolos): passo a passo em [MODO_PLC.md](MODO_PLC.md).
```powershell
$env:LFAM_MODE = "plc"; $env:LFAM_OPCUA_URL = "opc.tcp://localhost:4840"
$env:LFAM_OPCUA_USER = "SEU_USUARIO"; $env:LFAM_OPCUA_SECURITY = "Basic256Sha256,SignAndEncrypt"
$sec = Read-Host "senha" -AsSecureString; $env:LFAM_OPCUA_PASSWORD = [System.Net.NetworkCredential]::new('', $sec).Password
python tools/gen_opcua_client_cert.py            # uma vez: certificado de cliente local (work/pki, fora do Git)
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --port 8000
```
A senha fica **só** no ambiente da sessão; nunca em arquivo. O selo passa a `LÓGICA NO CLP · PLANTA SIMULADA` (a planta continua simulada). No modo PLC o tempo é o real.

Ensaios no CLP (com o backend em modo PLC rodando): `python tools/cp3_roundtrip.py` (ida e volta, ~1 min) e `python tools/cp4_scenarios.py` (cenários completos, ~1h30).

## Variáveis de ambiente
| Variável | Para quê | Padrão |
|---|---|---|
| `LFAM_MODE` | `demo` ou `plc` | `demo` |
| `LFAM_TIME_SCALE` | aceleração do relógio (só DEMO) | `1` |
| `LFAM_OPCUA_URL` / `_USER` / `_PASSWORD` | conexão OPC UA | — |
| `LFAM_OPCUA_SECURITY` | política de segurança do canal | vazio (sem criptografia; o servidor recusa senha) |
| `LFAM_OPCUA_CERT` / `_KEY` | certificado e chave do cliente | `work/pki/client_cert.der`, `client_key.pem` |
| `LFAM_OPCUA_TIMEOUT` | timeout (s) | `10` |
| `LFAM_API` / `LFAM_WEB_PORT` | (frontend) backend e porta do Vite | `127.0.0.1:8000` / `5173` |

## Testes
```powershell
.\.venv\Scripts\python.exe -m pytest -q tests          # simulador, Ladder gerado, backend DEMO, OPC UA (dublê), avaliador seguro
cd scada\web; npm run build                            # tsc + vite
npx playwright install chromium                        # uma vez
npx playwright test                                    # E2E; exige backend DEMO (:8000, fator 30) e `npm run dev` ativos; grava docs/evidence/scada/
```
Para rodar o E2E sem tocar num backend em uso: `LFAM_API=127.0.0.1:8100 LFAM_WEB_PORT=5180 npm run dev` e `PW_BASE=http://localhost:5180 npx playwright test`.
