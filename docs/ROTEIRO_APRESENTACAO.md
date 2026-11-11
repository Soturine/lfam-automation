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

## Cenários de demonstração (funcionam offline, em DEMO)
1. **Partida normal:** "Ligar aquecimento" (botão mostra *Aguardando* → *Confirmado* só quando K1 fecha) → encharque → PRONTO → "Iniciar extrusão".
2. **Pressão:** Alarmes → injetar "pressão alta" → o programa trava a falha, para a rosca, mostra a **causa que travou**; reset só após a causa sumir.
3. **Perda de comunicação:** parar o backend → "SEM COMUNICAÇÃO", valores neutros, comandos desabilitados.
Se a rede/CODESYS falhar: use as capturas em `docs/evidence/scada/` e o log `docs/evidence/CP2_online_run2.log`.

## Perguntas prováveis na arguição
- **Por que CODESYS se o projeto propõe S7-1200?** Control Win é a plataforma disponível para executar Ladder real; a lógica (IEC 61131-3) é portável, mas endereços/PID_Compact/OBs são Siemens e exigem adaptação (`SOURCE_RECONCILIATION.md`).
- **Por que o PID não fica depois de contatos?** Se o bloco deixa de ser chamado, a saída PWM congela no último valor e pode manter um aquecedor ligado. Aqui o PID roda todo ciclo e o bloqueio está no `RESET` e no gate do SSR.
- **O que acontece com o termopar rompido?** Zona em RESET, SSR bloqueado, falha travada; reset só sem causa.
- **Diferença entre alarme e falha?** Aviso (16,5 MPa, 390 °C, trecho frio) sinaliza; falha (17 MPa, 400 °C, termopar, inversor...) trava e desliga.
- **O SCADA é seguro como parada?** Não. Emergência é circuito de hardware independente.
- **O que não foi testado?** Programa completo no runtime; ganhos de PID; escala do inversor; PROFINET; modo CLP do SCADA.
- **Por que 15 min de encharque / 5 min de pós-ventilação?** Valores propostos do grupo (ajustáveis); justificativa: material parado funde devagar; ventilador do motor perde vazão em baixa rotação.
- **Como o sinal vai do sensor ao atuador?** Termopar → módulo analógico → escalonamento (rede 01/02) → PID → PWM → gate (rede 06) → SSR; retorno: variável → SCADA.
