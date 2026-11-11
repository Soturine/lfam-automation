# Relatório de implementação — LFAM (2026-11-11)

Legenda: **COMPROVADO** (executado e observado) · **IMPLEMENTADO MAS NÃO TESTADO** · **SOMENTE PROTÓTIPO / DEMO** · **BLOQUEADO** · **PENDENTE**.
Regra: compilar **não** é executar; DEMO **não** é CLP.

| Requisito | Fonte | Implementação | Teste executado | Evidência | Status |
|---|---|---|---|---|---|
| MCP lê o projeto CODESYS | Prompt §7 CP1 | Chamadas reais ao `codesys-ide` | árvore, PLC_PRG, bibliotecas, `check_for_errors` | `evidence/CP1_MCP_INSPECTION.md` | **COMPROVADO** |
| Criar Ladder gráfico (o MCP não cria) | enunciado, prompt §2 | PLCopen XML + Scripting API headless | import + build em cópia, round-trip | `evidence/CP2_LD_POC.md` | **COMPROVADO** |
| Rede LD executa no Control Win | CP2 | POC de 1 rede (`BT_TESTE`/`FALHA_TESTE`/`EST_TESTE`) | login do admin, 3 combinações online | `evidence/CP2_online_run2.log` (F,T,F) | **COMPROVADO** |
| Programa completo (15 redes, 110 elementos) compila | CP4 | `codesys/generator` → `LFAM_PROGRAM.xml`, Util 3.5.22.0, MainTask 100 ms | build headless | stderr do compilador: 0 erros, 0 avisos | **COMPROVADO (compilação)** |
| Programa completo **executa** no Control Win | CP4 | idem (110 elementos, 6 `Util.PID`) | heartbeat vivo, K1/falha/reset observados via OPC UA | `evidence/CP3_ROUNDTRIP_OK.txt` | **COMPROVADO (execução e lógica de partida/falha)**; PID/ganhos e escala do inversor seguem **não validados** |
| Lógica das redes (limiares, TONs, falha travada, reset condicionado, primeira causa, histerese, selo, PWM) | prompt §3/§4 | avaliador de referência da MESMA estrutura | 83 pytest | `tests/` | **COMPROVADO no avaliador** |
| PID por zona (5) e IR | prompt §4 rede 06/13 | `Util.PID` sem EN, RESET no bloqueio, PWM por fase de 20 ciclos | modelo de referência (saturação, anti-windup, PWM, RESET) | `test_ladder_pid.py` | **IMPLEMENTADO**; ganhos **hipotéticos**, equivalência com runtime **NÃO TESTADA** |
| Rede 14 (R_TRIG + CTU) | prompt §4 | blocos `R_TRIG`/`CTU` | contagem por borda e reset | `test_ladder_pid.py` | **COMPROVADO no avaliador** |
| Escalonamento do inversor | prompt P3 | `INV_REF` com escala **hipotética** (16384 = 60 Hz) | limites 17–34 rpm | testes | **IMPLEMENTADO** (escala a confirmar com o inversor) |
| Simulador físico | prompt §6 | `simulator/lfam_sim.py` (1ª ordem, acoplamento, pressão, falhas) | 9 pytest | `tests/test_simulator.py` | **SOMENTE PROTÓTIPO** (parâmetros hipotéticos, não calibrado) |
| Backend FastAPI + WebSocket | prompt §6 | `backend/` (comandos = solicitações, setpoints validados) | 12 pytest + E2E | `tests/`, `docs/SCADA_RUN.md` | **COMPROVADO em DEMO** |
| SCADA React/TS, 6 telas, DEMO | prompt §5/§11 | `scada/web` | build + 2 E2E Playwright, 4 tamanhos, sem scroll horizontal | `evidence/scada/*.png` | **COMPROVADO em DEMO** |
| Modo PLC no backend (cliente OPC UA) | prompt §6, addendum P1 | `backend/transport.py` | 7 testes contra servidor de **teste** (dublê) | `tests/test_opcua_transport.py` | **COMPROVADO contra o Control Win** (canal Basic256Sha256 SignAndEncrypt; leituras em lotes de 50) |
| Servidor OPC UA do Control Win | docs oficiais | Communication Manager + OPC UA Server + Symbol Configuration (UI do IDE) e certificados na Tela de segurança | conexão real, símbolos publicados | `evidence/CP3_ROUNDTRIP_OK.txt` | **COMPROVADO** |
| **CP3: HMI → FastAPI → OPC UA → Ladder → HMI** | prompt §7 CP3 | `tools/cp3_roundtrip.py` | partida com reset do operador, BT_AQUEC confirmado pelo Ladder (K1_AQUEC), falha travada, reset condicionado | `evidence/CP3_ROUNDTRIP_OK.txt` | **COMPROVADO** (entradas vêm da planta SIMULADA; o Ladder e o canal são reais) |
| Credenciais não vazam | prompt §2 | loggers `asyncua` em WARNING; senha só no ambiente | teste de log | `test_opcua_transport.py` | **COMPROVADO** |
| Reconciliação de fontes e contrato de tags | prompt §1A | `SOURCE_RECONCILIATION.md` (D1–D25), `tags.csv` (97) | revisão | docs | **COMPROVADO (documental)**; `tags.csv` atualizado com as variáveis do programa gerado (status "implementado; online pendente") |
| Guia de instalação do CODESYS | addendum anterior | `INSTALLATION_COMPLETE.md`, `diagnose-windows.ps1` | diagnóstico executado nesta máquina | docs | **COMPROVADO (diagnóstico)**; sem capturas de tela |
| Fluxograma, esquema elétrico, pranchas redesenhadas | prompt §12 | não geradas | — | — | **PENDENTE** (existem as referências do grupo) |
| Apresentação revisada (PPTX) | prompt §12 | não gerada | — | — | **PENDENTE** |

## Diferença entre o conceitual e o executável
As pranchas do grupo são desenhos **didáticos para S7-1200**; o projeto executável é CODESYS. Divergências documentadas em `SOURCE_RECONCILIATION.md` (inclui o erro de colocar contatos antes do PID_Compact).

## Reproduzir
`docs/INSTALLATION_COMPLETE.md` (ambiente) · `docs/SCADA_RUN.md` (DEMO) · `docs/MODO_PLC.md` (modo PLC). Gate local: `pytest -q tests` + build headless (`tools/codesys_scripts/build_program.py`).

## Limitações honestas
Nenhum resultado aqui autoriza comandar máquina real. Emergência é hardware independente. Pressão/ganhos/escala do inversor/tensão do sistema (monofásico × trifásico) são **hipóteses** a validar.
