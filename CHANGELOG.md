# Changelog

Todas as mudanças relevantes do projeto. Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/); versões em [SemVer](https://semver.org/lang/pt-BR/).
Para o estado atual (o que funciona e o que não foi provado), veja o [README](README.md) e o [relatório de implementação](docs/projeto/IMPLEMENTATION_REPORT.md).

## [1.0.0] — 2026-11-11
Primeira versão completa: o Ladder real executa no CODESYS Control Win e a tela de operação conversa com ele.

### Adicionado
- **Ensaio no CLP em tempo real** (`tools/cp4_scenarios.py`): 65 verificações — termopar rompido, inversor, K1 colado, emergência, disjuntor, encharque de 15 min (903–906 s), aviso e falha de pressão, ventilador (10,2 s), falta de material (60,6 s), pós-ventilação (300 s) e parada normal. Resultado: **65/65**.
- **Comparação do `Util.PID` real com o modelo** (`tools/cp4_pid_compare.py`): erro médio 0,4–1,0 %.
- **Modo apresentação** no SCADA: seletor de velocidade (Tempo real, Rápido 30×, Apresentação 90×) no DEMO; a demonstração inteira cabe em ~2 min.
- **Projeto CODESYS** com o Ladder completo e o servidor OPC UA configurados: `codesys/LFAM_Automacao_Ladder.project`.
- **Scripts para outro PC**: `tools/setup.ps1`, `start-demo.ps1`, `start-plc.ps1` (senha oculta) e `run-tests.ps1`.
- **Documentação em subpastas** (`entender`, `guias`, `academico`, `projeto`) com índice, perguntas e respostas da arguição, roteiro de 2 minutos, Ladder explicado etapa por etapa e a ligação backend↔CODESYS.
- Catálogo do Ladder em imagens (`tools/render_ladder.py`), galeria do SCADA e três GIFs (fluxo completo, tour das telas, celular).
- Acabamento visual do SCADA: profundidade, entrada escalonada, números animados, estados de comando, skeleton de carregamento, tendência na visão geral.
- Trace por ciclo e falhas de ensaio no backend (`/api/trace`, disjuntor aberto, aviso e bloqueio de pressão).

### Corrigido
- **Temporizadores com preset 0 no CLP:** o importador do CODESYS perdia o literal do pino `PT`; agora é um `inVariable` ligado ao pino, com teste de regressão no XML.
- **Falso `SOBRETEMP_400` com termopar aberto:** os comparadores de 390/400 °C só valem com termopar válido.
- **Modelo de PID:** anti-windup por retrocálculo, medido no bloco real.
- **Planta simulada em modo PLC** passa a seguir o relógio real (os TON do CLP também).
- Leituras OPC UA em lotes (o servidor recusa pedidos grandes) e timeout configurável.

### Removido
- Prompt e notas de andamento superadas da raiz e de `docs/` (cópias locais em `references/`, fora do Git).
- O `LFAM_Automacao.project` original da raiz (um `PLC_PRG` vazio); o histórico continua no Git.

## [0.4.0] — 2026-11-11
Comunicação com o CLP.
### Adicionado
- Cliente **OPC UA** no backend e **modo PLC** na interface; canal `Basic256Sha256` assinado e cifrado, certificado de cliente local, credenciais só no ambiente e nunca nos logs.
- Ensaio de ida e volta tela → API → OPC UA → Ladder → tela, com reset de partida.
- Procedimento real do OPC UA no Control Win (certificados, símbolos, erros e soluções).
### Corrigido
- O `asyncua` em `DEBUG` imprimia a senha (loggers forçados a `WARNING`, com teste).
- Botão STOP ficava preso (agora é um pulso de 1 s).
- Conclusão errada de que o runtime não tinha OPC UA; o servidor é parte do Control Win.

## [0.3.0] — 2026-11-11
Programa completo, backend DEMO e SCADA.
### Adicionado
- Gerador de Ladder em Python (DSL → PLCopen XML) e **15 redes**: escalonamento, termopares, temporizadores, segurança, aquecimento, encharque, rosca, ventilação, pressão, IR, carregador (`R_TRIG` + `CTU`) e torre luminosa.
- **6 PIDs reais** (`Util.PID`) executados todo ciclo, PWM por fase e escala do inversor.
- Latches de **primeira causa** de falha no Ladder; alinhamento com as pranchas (divergências D16–D25).
- Backend **FastAPI + WebSocket** em modo DEMO e **SCADA React/TypeScript** de 6 telas, com testes E2E (Playwright) em 4 tamanhos.
- Auditoria de testes e gerador; `tags.csv` com as 164 variáveis; relatório de implementação, conformidade com o enunciado e roteiro de 20 min.
### Alterado
- `eval()` substituído por avaliador de expressões com lista branca.

## [0.2.0] — 2026-11-11
Ladder gráfico real e execução online.
### Adicionado
- Inspeção do projeto pelo MCP do CODESYS; prova de conceito de Ladder via PLCopen XML + Scripting API.
- Execução online da prova de conceito no Control Win (login do administrador feito pelo usuário; script roda dentro do IDE).
- Reconciliação das fontes (S7-1200 × CODESYS, decisões D1–D15).
- Simulador didático da planta com injeção de falhas e testes.
- Guia completo de instalação no Windows e diagnóstico (`tools/diagnose-windows.ps1`).

## [0.1.0] — 2026-11-10
### Adicionado
- Projeto CODESYS inicial e documentação de preparo, integração MCP e plano de entrega.
