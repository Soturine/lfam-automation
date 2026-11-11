# Roteiro de apresentação (20 min) e perguntas de arguição

Baseado na distribuição do `Seminario_Automacao_Extrusora.pptx` (≈ 5 min por pessoa). Ajuste os nomes ao seu grupo.
**Regra de ouro:** diga o estado real de cada coisa (executado / compilado / simulado).

| Min | Quem (área) | Conteúdo | Demonstração |
|---|---|---|---|
| 0–2 | Todos | Problema: paradas não planejadas (motor, alimentação, controle térmico) | — |
| 2–7 | Mecânica | Processo, fuso Ø60×960, sensores e atuadores, falhas reais do TG | Sinótico do SCADA |
| 7–12 | Elétrica | Painel, K1, SSRs, inversor, relé de segurança; **tensão 220 V mono × trifásico em aberto** | Esquema (rotulado ilustrativo) |
| 12–17 | Computação (Ladder/PID) | Fluxograma → redes; rede 04 (`M_CAUSA`, falha travada, reset condicionado); PIDs rodando todo ciclo | **CODESYS**: rede LD real e variável mudando online (POC) |
| 17–20 | Computação (SCADA/comunicação) | HMI só solicita; estado confirmado; DEMO × CLP; limites | SCADA DEMO: aquecer → pronto → extrusão → falha de pressão → reset |

## Demonstração de 2 minutos (modo apresentação)
No SCADA em **DEMO**, clique em **Apresentação 90×** (canto superior direito): o relógio simulado anda 90× mais rápido e o encharque de 15 min passa em poucos segundos. **Fale o que cada passo prova**; o selo `DEMO / SIMULADO` deve estar visível.

| Tempo | Ação na tela | O que dizer |
|---|---|---|
| 0:00 | Selecione **Apresentação 90×** | "Relógio acelerado só na demonstração; no CLP o tempo é real" |
| 0:10 | **Ligar aquecimento** (botão: *Aguardando CLP…* → *✓ Confirmado*) | "A tela só **solicita**; o botão confirma quando o programa responde" |
| 0:20 | Observe zonas subindo e a tendência | "5 PIDs rodando todo ciclo; SSR por PWM" |
| 0:35 | Estado **Encharque** → **Pronto** | "15 min contínuos com as 5 zonas ≥ 330 °C (aqui acelerado)" |
| 0:50 | **Iniciar extrusão** | "A rosca só parte com o programa em PRONTO e sem falha" |
| 1:10 | Aba **Alarmes** → injetar **pressão alta** | "17 MPa: o Ladder **trava a falha**, desliga rosca e aquecimento" |
| 1:30 | Mostre a **causa que travou** | "A primeira causa fica registrada mesmo que a pressão volte" |
| 1:40 | Remova a falha e **Reset** | "Reset só é aceito depois que a causa some" |
| 1:55 | Volte à **Visão geral** | "Isto é DEMO; o mesmo Ladder roda no CODESYS — mostrar a rede 04" |

**Plano B** (sem rede/CODESYS): use os GIFs de [GALERIA](../entender/GALERIA.md) e o log [CP4_ONLINE_SCENARIOS](../evidence/CP4_ONLINE_SCENARIOS.txt).
Para mostrar o **Ladder de verdade**, abra o CODESYS com o programa em execução (modo PLC): [MODO_PLC](../guias/MODO_PLC.md). No modo CLP o seletor de velocidade não existe: os temporizadores são os do Ladder, em tempo real.

## Cenários de demonstração (funcionam offline, em DEMO)
1. **Partida normal:** "Ligar aquecimento" (botão mostra *Aguardando* → *Confirmado* só quando K1 fecha) → encharque → PRONTO → "Iniciar extrusão".
2. **Pressão:** Alarmes → injetar "pressão alta" → o programa trava a falha, para a rosca, mostra a **causa que travou**; reset só após a causa sumir.
3. **Perda de comunicação:** parar o backend → "SEM COMUNICAÇÃO", valores neutros, comandos desabilitados.
Se a rede/CODESYS falhar: use as capturas em `docs/evidence/scada/` e o log `docs/evidence/CP2_online_run2.log`.

## Perguntas prováveis na arguição
> Lista completa, por tema: [PERGUNTAS_E_RESPOSTAS](PERGUNTAS_E_RESPOSTAS.md).

- **Por que CODESYS se o projeto propõe S7-1200?** Control Win é a plataforma disponível para executar Ladder real; a lógica (IEC 61131-3) é portável, mas endereços/PID_Compact/OBs são Siemens e exigem adaptação (`SOURCE_RECONCILIATION.md`).
- **Por que o PID não fica depois de contatos?** Se o bloco deixa de ser chamado, a saída PWM congela no último valor e pode manter um aquecedor ligado. Aqui o PID roda todo ciclo e o bloqueio está no `RESET` e no gate do SSR.
- **O que acontece com o termopar rompido?** Zona em RESET, SSR bloqueado, falha travada; reset só sem causa.
- **Diferença entre alarme e falha?** Aviso (16,5 MPa, 390 °C, trecho frio) sinaliza; falha (17 MPa, 400 °C, termopar, inversor...) trava e desliga.
- **O SCADA é seguro como parada?** Não. Emergência é circuito de hardware independente.
- **O que não foi testado?** Programa completo no runtime; ganhos de PID; escala do inversor; PROFINET; modo CLP do SCADA.
- **Por que 15 min de encharque / 5 min de pós-ventilação?** Valores propostos do grupo (ajustáveis); justificativa: material parado funde devagar; ventilador do motor perde vazão em baixa rotação.
- **Como o sinal vai do sensor ao atuador?** Termopar → módulo analógico → escalonamento (rede 01/02) → PID → PWM → gate (rede 06) → SSR; retorno: variável → SCADA.
