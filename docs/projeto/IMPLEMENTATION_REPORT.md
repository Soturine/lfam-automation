# Relatório de implementação — LFAM

Legenda: **COMPROVADO** = executado e observado · **COMPILADO** = só compilação · **SIMULADO** = planta/DEMO · **HIPÓTESE** = parâmetro não calibrado · **PENDENTE**.
Regras: compilar **não** é executar; DEMO **não** é CLP. Resumo para leigos: [COMO_FUNCIONA](../entender/COMO_FUNCIONA.md).

## 1. Estado por requisito

| Requisito | Implementação | Teste executado | Evidência | Estado |
|---|---|---|---|---|
| Ladder **gráfico real** (o assistente de IA não "desenha" Ladder) | Gerador Python → PLCopen XML → importado no CODESYS pela Scripting API | importação + compilação + exportação de volta (ida e volta) | [prova de conceito](../evidence/CP2_LD_POC.md) | **COMPROVADO** |
| Programa completo: 15 redes, 110 elementos, 6 `Util.PID`, `TON`, `CTU`, `R_TRIG`, `MainTask` 100 ms | `codesys/generator` → `LFAM_PROGRAM.xml` → [`LFAM_Automacao_Ladder.project`](../../codesys/LFAM_Automacao_Ladder.project) | compilação no CODESYS | 0 erros, 0 avisos | **COMPROVADO (compilação)** |
| Programa **executa** no CODESYS Control Win | idem, baixado no CLP virtual | 65 verificações em tempo real (ver §2) | [cenários no CLP](../evidence/CP4_ONLINE_SCENARIOS.txt) | **COMPROVADO** (65/65) |
| Tela → API → **OPC UA** → Ladder → tela | `backend/transport.py` (canal `Basic256Sha256`, assinado e cifrado) | comando confirmado pelo Ladder, falha travada e reset condicionado | [ida e volta](../evidence/CP3_ROUNDTRIP_OK.txt) | **COMPROVADO** |
| Lógica das redes (limiares, TON, selo, falha travada, reset, primeira causa, histerese, PWM) | avaliador Python da MESMA estrutura | 90 testes pytest | `tests/` | **COMPROVADO** |
| PID real (5 zonas + IR) | `Util.PID` sem contatos antes (roda todo ciclo); RESET no bloqueio; PWM por fase de 20 ciclos | `Util.PID` real comparado com o modelo sobre ~43 mil ciclos | [PID real × modelo](../evidence/CP4_PID_COMPARE.txt) | **COMPROVADO** (erro médio 0,4–1,0 %); **ganhos HIPÓTESE** (KP 8 %/°C, TN 20 s) |
| Rede 14 (`R_TRIG` + `CTU`) | blocos da biblioteca padrão | contagem por borda e reset | `tests/test_ladder_pid.py` | **COMPROVADO no avaliador**; compilado no CLP |
| Escalonamento do inversor | `INV_REF` com escala 16384 = 60 Hz | limites 17–34 rpm | testes | **HIPÓTESE** (confirmar com o inversor) |
| Simulador físico | `simulator/lfam_sim.py` (1ª ordem, acoplamento, pressão, falhas) | 9 testes | `tests/test_simulator.py` | **SIMULADO** (parâmetros hipotéticos) |
| Backend FastAPI + WebSocket | comandos = solicitações; setpoints validados; heartbeat; modo apresentação (velocidade do DEMO) | testes pytest + E2E | `tests/` | **COMPROVADO** |
| SCADA React/TS, 6 telas | `scada/web` | build + 2 E2E Playwright em 4 tamanhos | [galeria](../entender/GALERIA.md) | **COMPROVADO** (DEMO e modo CLP) |
| Credenciais não vazam | senha só no ambiente; logs do `asyncua` em WARNING | teste de log | `tests/test_opcua_transport.py` | **COMPROVADO** |
| Reconciliação das fontes e contrato de variáveis | [25 divergências](../academico/SOURCE_RECONCILIATION.md) e [`tags.csv`](tags.csv) (164 variáveis) | revisão | docs | **COMPROVADO (documental)** |
| Guia de instalação do CODESYS e scripts para outro PC | [INSTALLATION_COMPLETE](../guias/INSTALLATION_COMPLETE.md), [INICIO_RAPIDO](../guias/INICIO_RAPIDO.md), `tools/*.ps1` | diagnóstico executado | docs | **COMPROVADO** |
| Fluxograma, esquema elétrico e pranchas redesenhados; apresentação revisada | não geradas (existem as do grupo) | — | — | **PENDENTE** (trabalho do grupo) |

## 2. O que o ensaio no CLP mediu (em tempo real, Control Win)
Roteiro: `tools/cp4_scenarios.py`. As entradas vêm da planta **simulada** do backend; o Ladder e o canal OPC UA são reais. Resultado: **65 de 65 verificações em PASS**.

| Cenário | Resultado medido |
|---|---|
| Termopar rompido, falha do inversor, K1 colado, emergência lógica | O Ladder travou a falha em < 1 s, abriu K1 e parou a rosca; **reset recusado** com a causa presente e aceito depois |
| Disjuntor do aquecimento aberto | Desliga o aquecimento sem falha e **não religa sozinho** |
| Encharque de 15 min (4 corridas) | PRONTO em **905,9 / 905,1 / 906,3 / 903,3 s** (alvo 900 s) |
| Sobressinal dos PIDs na planta simulada | ≤ **2,8 °C** acima do setpoint |
| Aviso de pressão (≥ 16,5 MPa) | Alarme e referência reduzida a **22,5 rpm** sem travar falha |
| Pressão ≥ 17 MPa | Falha travada em 0,3 s; **segue travada** após a pressão normalizar; reset recusado com bloqueio persistente |
| Ventilador sem retorno | Falha em **10,2 s** (alvo 10 s) |
| Falta de material | Falha em **60,6 s** (alvo 60 s) |
| Pós-ventilação | **300,1 s** após a falha de pressão e **300,9 s** após parada normal (alvo 300 s) |
| Parada normal (`BT_DESLIGA`) | Para a rosca e **mantém o aquecimento** (PRONTO) |

PID real × modelo: o `Util.PID` do Control Win tem **KP = 8,00 e Ki = 0,399** (nominal 8 e 0,40) e usa anti-windup por **retrocálculo**; o modelo de referência foi corrigido para igualar.

## 3. Defeitos que o ensaio no CLP revelou
O avaliador Python sozinho **não** os detectava; por isso existem os dois níveis de teste.

| Defeito | Causa | Correção e proteção |
|---|---|---|
| Todos os temporizadores com preset 0 (encharque terminava na hora) | O importador do CODESYS **perde** o literal `T#...` escrito dentro do pino `PT` | Preset como elemento `inVariable` ligado ao pino; **teste de regressão no XML** de todos os `TON` |
| Falso `SOBRETEMP_400` com termopar aberto | Leitura inválida (32767 → 3276,7 °C) passava pelo comparador | Comparadores de 390/400 °C só valem com `TC_Zn_OK`; teste por zona |
| Modelo de PID divergente do bloco real (5–8 %) | Anti-windup diferente | Modelo com retrocálculo, medido no CLP; erro cai para < 1,6 % |
| Planta mais lenta que o CLP em modo PLC | Passo fixo de 0,1 s com ciclo OPC UA mais longo | Planta passa a seguir o relógio real |
| Teste de reset "recusado" falhava em causas ligadas à extrusão | Premissa errada: essas causas somem sozinhas quando a rosca para | A propriedade correta (a falha **segue travada** até o reset) passou a ser verificada |

Outros achados e correções do desenvolvimento: `eval()` substituído por avaliador com lista branca; o `asyncua` em `DEBUG` imprimia a senha (loggers forçados a `WARNING`); botão STOP ficava preso (agora é pulso de 1 s). → [auditoria](AUDIT_TESTS_AND_GENERATOR.md)

## 4. Diferença entre o conceitual e o executável
As pranchas do grupo são desenhos **didáticos para S7-1200**; o projeto executável é CODESYS. Divergências (incluindo o erro de colocar contatos antes do `PID_Compact`) em [SOURCE_RECONCILIATION](../academico/SOURCE_RECONCILIATION.md).

## 5. Reproduzir
[INICIO_RAPIDO](../guias/INICIO_RAPIDO.md) (DEMO, testes e CLP) · [MODO_PLC](../guias/MODO_PLC.md) · gate local: `tools\run-tests.ps1` e, para o CLP, `tools\cp4_scenarios.py`.

## 6. Limitações honestas
Nenhum resultado aqui autoriza comandar máquina real. A emergência é hardware independente. **Hipóteses a validar:** ganhos dos PIDs, escala do inversor, parâmetros da planta e a tensão do painel (monofásico × trifásico). Não testados: PROFINET, Siemens S7-1200 e máquina física.
