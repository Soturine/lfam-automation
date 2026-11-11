# Plano de entrega — automação industrial LFAM

## Requisitos da disciplina

Monografia escrita à mão, apresentação oral de 20 minutos com arguição, participação multidisciplinar e pelo menos uma função real implementada em Ladder. Entrega indicada no enunciado: **27/11/2026, 00:00**, confirmar horário do AVEA antes de entregar.

## Redes Ladder a implementar / revisar

| Rede | Função planejada | Critério mínimo |
| --- | --- | --- |
| 01 | Escalonamento analógico (pressão e substrato) | Conversão validada por tipo/faixa |
| 02 | Termopares Z1–Z5 | Limiares e diagnóstico de falha claros |
| 03 | TON dos intertravamentos | Temporizações e reset testados |
| 04 | Falha geral set/reset | Parada segura e reset só com condições normalizadas |
| 05 | Comando do contator K1 | Selo e permissivos |
| 06 | Controle das 5 zonas PID | Bibliotecas de PID compatíveis com CODESYS |
| 07 | Resfriamento com histerese | Liga/desliga sem oscilação indevida |
| 08 | Encharque 15 min | Reset se sair da faixa |
| 09 | Extrusora pronta / interface robô | Prontidão somente com permissivos |
| 10 | Rosca manual/automática | Stop com prioridade e modo definido |
| 11 | Ventilação após parada | TOF de 5 minutos |
| 12 | Velocidade / pressão | Arbitragem de referência e pré-alarme |
| 13 | Aquecedor IR | Malha e limites de operação |
| 14 | Funil / CTU | Alimentação e contagem de pulsos |
| 15 | Alarmes / sinalização | Prioridades e estados da torre |

**Situação:** especificações textuais disponíveis; as redes acima **não estão aqui marcadas como implementadas**. A validação será por importação, compilação, execução e testes.

## Seis telas HMI propostas

1. Visão geral: estados, caminho do material, permissivos, rosca e pressão.
2. Temperaturas e PID: Z1–Z5, PV/SP, tendências e alarmes.
3. Deposição / IR: robô, substrato, SSR e condição de movimento.
4. Alarmes: lista ativa/histórica, reconhecimento e origem de falha.
5. Receitas: limites, parâmetros autorizados e confirmação.
6. Histórico de paradas: eventos, duração, código de causa e exportação.

## Etapas de validação

- **CP0 — Base:** checkout versionado, CODESYS abre arquivo existente; configuração local não é versionada.
- **CP1 — MCP:** conexão Claude → CODESYS realmente estabelecida, leitura da árvore e build sem modificação.
- **CP2 — POC Ladder:** UMA rede gráfica no CODESYS, build e execução com status observado.
- **CP3 — Comunicação:** UMA tag lida + um comando escrito/confirmado, com timeout e permissão.
- **CP4 — Controle:** redes 01–15 revisadas e testadas por tabelas de verdade, bordas e temporizações.
- **CP5 — Planta simulada:** modelo térmico/mecânico com cenário nominal e falhas, sem afirmar fidelidade de máquina real.
- **CP6 — HMI:** seis telas conectadas, separação Demo/PLC, testes de perda de conexão.
- **CP7 — Entrega:** fluxograma, esquema funcional, documentação de E/S, monografia e apresentação, registro de evidências.

## Cenários mínimos

- Aquecimento normal e espera de encharque.
- Queda de temperatura antes dos 15 min.
- Perda de termopar / sobretemperatura.
- Sobrepressão, referência de RPM no limite e falha de inversor.
- Funil vazio, ventilação parada e contator colado.
- Falha geral travada e reset apenas após normalização.
- Perda de conexão HMI: não exibir dados antigos como atuais; sem comando duplicado.
- Reinício do runtime e reconexão com estados conservadores.

## Evidências

Para cada marco: ferramenta/versão, data, comandos efetivos, build com erros/avisos, screenshots de Ladder energizado, tags observadas, logs dos testes, limitações e próxima decisão. Não substituir evidência por renders ou saídas inventadas.
