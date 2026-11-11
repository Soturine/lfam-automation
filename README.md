# LFAM Automation

**Supervisão e controle de uma extrusora de impressão 3D de grande formato (LFAM)**: programa **Ladder real** executado num CLP virtual (CODESYS Control Win), tela de operação web (SCADA) e uma planta simulada para testar tudo sem máquina física.
Projeto acadêmico de Automação Industrial — **não é segurança certificada nem controla máquina real**.

<p align="center">
  <img src="docs/media/scada-fluxo-completo.gif" alt="SCADA em modo DEMO: aquecer, encharque, extrusão, falha de pressão e reset" width="760"><br>
  <sub>SCADA em modo <b>DEMO / SIMULADO</b>: aquecer → encharque → pronto → extrusão → falha de pressão travada → reset (relógio acelerado).</sub>
</p>

## O que é, em 30 segundos
- Um **programa Ladder** (15 redes, 6 PIDs `Util.PID`, temporizadores, falhas travadas) decide tudo: aquece 5 zonas, espera 15 min de encharque, libera a extrusão e protege contra falhas.
- Ele roda no **CODESYS Control Win** (CLP virtual). Veja as redes em [docs/entender/LADDER.md](docs/entender/LADDER.md).
- Uma **tela web** (React) mostra o processo e **só envia pedidos**; o sucesso aparece **depois** que o CLP confirma.
- Entre os dois há um **backend FastAPI** que fala com o CLP por **OPC UA criptografado**.
- Como não existe a máquina, uma **planta simulada** devolve temperaturas, pressão e falhas.

```mermaid
flowchart LR
    OP([Operador]) --> WEB["SCADA web<br/>só mostra e SOLICITA"]
    WEB <-->|"HTTP / WebSocket"| API["Backend FastAPI"]
    API <-->|"OPC UA criptografado"| PLC["CODESYS Control Win<br/>Ladder (decide tudo)"]
    PLC -->|"K1, SSR, inversor"| SIM["Planta SIMULADA"]
    SIM -->|"termopares, pressão"| API
```

**Leia primeiro:** [docs/entender/COMO_FUNCIONA.md](docs/entender/COMO_FUNCIONA.md) — explica passo a passo como o clique na tela vira uma variável no Ladder e volta, o que é real × simulado, glossário e perguntas de quem chega de fora.

## Telas
<table>
<tr>
<td align="center"><img src="docs/media/scada-tour-telas.gif" alt="Tour das 6 telas" width="560"><br><sub><b>Tour das 6 telas</b></sub></td>
<td align="center"><img src="docs/media/scada-celular.gif" alt="SCADA no celular" width="200"><br><sub><b>No celular</b> (responsivo)</sub></td>
</tr>
</table>

Para apresentar: o seletor **Apresentação 90×** (no topo da tela, só no DEMO) faz a demonstração inteira caber em ~2 minutos.

Capturas de cada tela e dos estados (normal, falha, sem comunicação): **[galeria](docs/entender/GALERIA.md)**. Ladder em imagens: **[catálogo](docs/entender/LADDER.md)**.

## O que funciona hoje
| Parte | Estado | Onde ver |
|---|---|---|
| Ladder gráfico (15 redes, 110 elementos), importado e compilado no CODESYS | Funciona (0 erros, 0 avisos) | [catálogo do Ladder](docs/entender/LADDER.md) |
| Ladder executando no CODESYS Control Win | Funciona | [ensaio de ida e volta](docs/evidence/CP3_ROUNDTRIP_OK.txt) |
| Tela → API → OPC UA → Ladder → tela | Funciona (comandos confirmados pelo CLP) | [como o backend se liga ao CODESYS](docs/entender/LIGACAO_BACKEND_CODESYS.md) |
| Cenários de falha, reset, encharque de 15 min e pressão no CLP | Verificados em tempo real | [resultados dos cenários](docs/evidence/CP4_ONLINE_SCENARIOS.txt) |
| SCADA de 6 telas, responsivo, com testes automáticos | Funciona (modo DEMO e modo CLP) | [galeria](docs/entender/GALERIA.md) |
| Sintonia dos PIDs, escala do inversor, parâmetros da planta | **Hipóteses** (não calibradas) | [relatório técnico](docs/projeto/IMPLEMENTATION_REPORT.md) |
| Máquina física, PROFINET, Siemens S7-1200 | **Não testado** (proposta acadêmica) | [fontes e decisões](docs/academico/SOURCE_RECONCILIATION.md) |

## Como abrir (três níveis)
Guia completo: **[docs/guias/INICIO_RAPIDO.md](docs/guias/INICIO_RAPIDO.md)**.

**1. Ver a tela funcionando (qualquer PC com Python e Node, ~10 min, sem CODESYS):**
```powershell
git clone <URL> lfam-automation ; cd lfam-automation
powershell -ExecutionPolicy Bypass -File .\tools\setup.ps1          # instala tudo
powershell -ExecutionPolicy Bypass -File .\tools\start-demo.ps1     # sobe backend + tela e abre o navegador
```
**2. Testes:** `powershell -ExecutionPolicy Bypass -File .\tools\run-tests.ps1` (`-E2E` inclui a interface).
**3. Ladder de verdade no CODESYS:** [instalação](docs/guias/INSTALLATION_COMPLETE.md) → [modo PLC](docs/guias/MODO_PLC.md) → `tools\start-plc.ps1 -User SEU_USUARIO -Web` (a senha é pedida de forma oculta).
**Projeto CODESYS:** `codesys/LFAM_Automacao_Ladder.project` (o `LFAM_Automacao.project` da raiz é o original do grupo e não é alterado).

## Documentação
| Para quê | Documento |
|---|---|
| **Índice de toda a documentação** | [docs/README.md](docs/README.md) |
| Entender o projeto do zero | [COMO_FUNCIONA](docs/entender/COMO_FUNCIONA.md) |
| Ver as telas e animações | [GALERIA](docs/entender/GALERIA.md) |
| Usar em outro PC (passo a passo) | [INICIO_RAPIDO](docs/guias/INICIO_RAPIDO.md) |
| Entender o Ladder (etapa por etapa) | [LADDER_EXPLICADO](docs/entender/LADDER_EXPLICADO.md) · [imagens das 15 redes](docs/entender/LADDER.md) |
| Como o backend fala com o CODESYS | [LIGACAO_BACKEND_CODESYS](docs/entender/LIGACAO_BACKEND_CODESYS.md) |
| Arquitetura técnica | [ARCHITECTURE](docs/entender/ARCHITECTURE.md) |
| Instalar e rodar | [INSTALLATION_COMPLETE](docs/guias/INSTALLATION_COMPLETE.md) · [SCADA_RUN](docs/guias/SCADA_RUN.md) · [modo PLC](docs/guias/MODO_PLC.md) · [SETUP_WINDOWS](docs/guias/SETUP_WINDOWS.md) · [MCP_TROUBLESHOOTING](docs/guias/MCP_TROUBLESHOOTING.md) |
| O que foi feito e provado | [IMPLEMENTATION_REPORT](docs/projeto/IMPLEMENTATION_REPORT.md) · [evidence](docs/evidence) · [AUDIT](docs/projeto/AUDIT_TESTS_AND_GENERATOR.md) |
| Fontes, divergências e decisões | [SOURCE_RECONCILIATION](docs/academico/SOURCE_RECONCILIATION.md) · [tags.csv](docs/projeto/tags.csv) |
| Trabalho acadêmico | [ACADEMIC_COMPLIANCE](docs/academico/ACADEMIC_COMPLIANCE.md) · [ROTEIRO_APRESENTACAO](docs/academico/ROTEIRO_APRESENTACAO.md) |

## Estrutura
`codesys/` gerador e XML do Ladder · `backend/` FastAPI e transportes (DEMO/OPC UA) · `scada/web/` interface React · `simulator/` planta · `tools/` scripts (gerar, compilar, ensaiar, gravar mídia) · `tests/` pytest · `docs/` guias e evidências.

Testes: `pytest -q tests` (90) e, em `scada/web`, `npx playwright test` (exige o backend DEMO).
Diagnóstico do ambiente Windows: `.\tools\diagnose-windows.ps1`.

## Segurança e escopo
Projeto **educacional / simulador**. HMI e software de controle comum **não substituem** parada de emergência (circuito de hardware independente), dispositivos de segurança certificados, análise de riscos nem comissionamento. Nunca escrever comandos em máquina física sem avaliação e autorização. Credenciais ficam **somente** em variáveis de ambiente da sessão; nada de segredos, licenças ou tickets no repositório.

## Contexto acadêmico
Trabalho multidisciplinar de Automação Industrial: monografia escrita à mão, apresentação oral de 20 minutos e arguição. A proposta usa Siemens S7-1200; a demonstração executável usa CODESYS Control Win — as diferenças estão em [SOURCE_RECONCILIATION](docs/academico/SOURCE_RECONCILIATION.md). Materiais de terceiros e do grupo (`references/`) não são versionados; revise licenças antes de tornar o repositório público.
