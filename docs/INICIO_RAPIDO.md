# Início rápido: rodar o projeto em outro PC

Três níveis, do mais fácil ao mais completo. **Comece pelo Nível 1** — ele não precisa de CODESYS.

| Nível | O que você vê | Precisa de | Tempo |
|---|---|---|---|
| **1. DEMO** | A tela (SCADA) funcionando com a planta simulada | Python + Node | ~10 min |
| **2. Testes** | Os testes automáticos passando | Nível 1 | ~5 min |
| **3. CLP real (virtual)** | O **Ladder rodando de verdade** no CODESYS e a tela conversando com ele | CODESYS (Windows) | ~1 h na 1ª vez |

> Sistema: Windows 10/11. O Nível 1 e 2 também funcionam em Linux/macOS com os comandos manuais da seção "Sem os scripts".

## Nível 1 — ver a tela funcionando (DEMO)

**O que instalar (uma vez):**
1. **Python 3.10+** — https://www.python.org/downloads/ (marque **“Add Python to PATH”**).
2. **Node.js LTS** — https://nodejs.org/
3. **Git** — https://git-scm.com/ (ou baixe o ZIP do repositório).

**Passo a passo** (PowerShell):
```powershell
git clone <URL-do-repositorio> lfam-automation
cd lfam-automation
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1          # instala tudo (≈ 5 min)
powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1     # sobe backend + tela e abre o navegador
```
O navegador abre em **http://localhost:5173**. Você deve ver o selo **DEMO / SIMULADO**.

**Roteiro de demonstração (2 min):**
1. Clique **Ligar aquecimento** → o botão mostra *Aguardando CLP…* e só vira *✓ Confirmado* quando o programa confirma.
2. Espere o estado **Pronto** (o relógio é acelerado 30×; o encharque de 15 min leva ~30 s).
3. **Iniciar extrusão** → a rosca gira, pressão e rpm aparecem.
4. Aba **Alarmes** → injete **pressão alta** → o programa **trava a falha** e mostra a causa.
5. Remova a falha e clique **Reconhecer e resetar** → só funciona depois que a causa some.

**Encerrar:** `powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1 -Stop`

Opções úteis: `-Scale 1` (tempo real), `-ApiPort 8100 -WebPort 5180` (outras portas), `-NoBrowser`.

## Nível 2 — rodar os testes
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1            # pytest + build do SCADA
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1 -Tests         # (uma vez) baixa o navegador dos testes E2E
powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1 -E2E       # + testes de interface (sobe e derruba o que precisa)
```
Esperado: *“Todos os testes passaram.”* O pytest cobre Ladder (por rede), simulador, backend e o cliente OPC UA (contra um servidor de **teste**).

## Nível 3 — o Ladder de verdade no CODESYS
Isto liga o **CLP virtual**. Você precisa do **CODESYS V3.5 SP22 (Patch 4)** com o **Control Win** — guia completo e conferido nas fontes oficiais em [INSTALLATION_COMPLETE.md](INSTALLATION_COMPLETE.md). Depois:

1. Abra `codesys/LFAM_Automacao_Ladder.project`, compile, faça **Logon → Download → Iniciar** (Control Win iniciado). Detalhes: [MODO_PLC.md](MODO_PLC.md) (certificados do OPC UA, símbolos).
2. Suba o backend em modo PLC — o script pede a senha de forma **oculta**:
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\start-plc.ps1 -User SEU_USUARIO_DO_DISPOSITIVO -Web
```
3. Abra http://localhost:5173. O selo passa a **LÓGICA NO CLP · PLANTA SIMULADA**. Em `http://127.0.0.1:8000/api/health` você vê `plc_connected: true`.
4. Prove a ida e volta: `.\.venv\Scripts\python.exe tools\cp3_roundtrip.py` (termina com `CP3 OK`). Ensaio completo (~1h30): `tools\cp4_scenarios.py`.

Se algo falhar, a tabela de erros de [LIGACAO_BACKEND_CODESYS.md](LIGACAO_BACKEND_CODESYS.md) cobre os casos reais.

## Problemas comuns
| Mensagem / sintoma | O que fazer |
|---|---|
| “A execução de scripts foi desabilitada” | Use o prefixo `powershell -ExecutionPolicy Bypass -File ...` como nos exemplos |
| `Python 3.10+ não encontrado` | Reinstale o Python marcando *Add to PATH*; abra um PowerShell novo |
| Porta 8000/5173 em uso | `tools\start-demo.ps1 -Stop` ou use `-ApiPort`/`-WebPort` |
| Tela em branco / “Aguardando o primeiro dado” | O backend não subiu: veja a janela minimizada dele; confira `http://127.0.0.1:8000/api/health` |
| `npm` falha | Confira o Node LTS (`node --version`) e a internet; apague `scada/web/node_modules` e rode `setup.ps1` de novo |
| Tela diz **SEM COMUNICAÇÃO** | Backend parado ou (modo PLC) aplicação parada no CODESYS |

## Sem os scripts (manual, qualquer sistema)
```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
LFAM_TIME_SCALE=30 python -m uvicorn backend.app:app --port 8000 &
cd scada/web && npm install && npm run dev            # http://localhost:5173
```

## O que você **não** deve esperar
Isto é um projeto educacional: a **máquina é simulada**, os ganhos de PID e a escala do inversor são hipóteses, e a interface **não é** parada de emergência. Veja [COMO_FUNCIONA.md](COMO_FUNCIONA.md).
