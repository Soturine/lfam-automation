# Perguntas e respostas (arguição, banca e curiosos)

Perguntas que a professora, a banca ou alguém de fora podem fazer, com **respostas diretas, honestas e ligadas à evidência**.
Regra de ouro: **diga o estado real de cada coisa** — *executado no CLP*, *compilado*, *simulado* ou *hipótese*. Respostas curtas primeiro; o detalhe está nos links.

**Índice:** [1. Visão geral](#1-visão-geral-e-escopo) · [2. CLP e hardware](#2-clp-e-hardware) · [3. Ladder e lógica](#3-ladder-e-lógica) · [4. Controle (PID)](#4-controle-pid-e-temperatura) · [5. Segurança e falhas](#5-segurança-e-falhas) · [6. SCADA e comunicação](#6-scada-comunicação-e-integração) · [7. Testes e validação](#7-testes-e-validação) · [8. Limites e honestidade](#8-limites-honestidade-e-trabalho-em-grupo) · [9. Perguntas-armadilha](#9-perguntas-armadilha)

---

## 1. Visão geral e escopo

**1.1 O que o projeto faz, em uma frase?**
Controla (em simulação) uma extrusora de impressão 3D de grande formato: aquece 5 zonas, espera o encharque de 15 min, extruda e protege contra falhas, com um programa **Ladder** executado num **CLP virtual** e uma tela web de operação. → [COMO_FUNCIONA](../entender/COMO_FUNCIONA.md)

**1.2 Qual o problema real que ele resolve?**
Paradas não planejadas de extrusoras LFAM (motor, alimentação, controle térmico). A automação traz sequência segura, intertravamentos e falhas que **travam até serem reconhecidas**, e dá visibilidade ao operador.

**1.3 O que foi efetivamente entregue?**
Gerador do Ladder (15 redes), importação e compilação no CODESYS, execução no CODESYS Control Win, backend FastAPI com OPC UA, SCADA de 6 telas, planta simulada, testes automáticos e documentação. → [IMPLEMENTATION_REPORT](../projeto/IMPLEMENTATION_REPORT.md)

**1.4 O que é real e o que é simulado?**
**Real:** o Ladder (importado, compilado e executado no Control Win), o canal OPC UA, os PIDs `Util.PID` da biblioteca, os temporizadores. **Simulado:** a máquina inteira (temperaturas, pressão, rotação, sensores). **Hipóteses:** ganhos de PID, escala do inversor, parâmetros da planta. → [COMO_FUNCIONA §6](../entender/COMO_FUNCIONA.md#6-o-que-é-real-e-o-que-é-simulado)

**1.5 Isso funciona numa máquina real?**
**Não foi testado** e não deve ser usado para comandar máquina real sem análise de riscos, comissionamento e circuito de emergência independente. É um projeto educacional.

**1.6 O trabalho atende ao enunciado?**
Lista item a item, com o que existe e o que é do grupo (monografia manuscrita, apresentação oral). → [ACADEMIC_COMPLIANCE](ACADEMIC_COMPLIANCE.md)

---

## 2. CLP e hardware

**2.1 Por que a proposta usa Siemens S7-1200 e a demonstração usa CODESYS?**
A proposta acadêmica é S7-1200 CPU 1214C (com módulos de termopar e E/S). Para **provar que a lógica executa** sem comprar hardware, usamos o CODESYS Control Win, um CLP virtual que roda Ladder real (IEC 61131-3). A lógica é portável; endereços, `PID_Compact` e OBs são Siemens e exigem adaptação. → [SOURCE_RECONCILIATION](SOURCE_RECONCILIATION.md)

**2.2 O que muda ao migrar para o TIA Portal?**
`OB1/OB30` → `MainTask` de 100 ms; `PID_Compact` → `Util.PID`; `NORM_X/SCALE_X` → aritmética em REAL; `SM0.0` → `TRUE`; endereços `%I/%Q/%IW` → variáveis simbólicas. A tabela completa de equivalências está na reconciliação (D1–D25).

**2.3 Como as entradas e saídas foram definidas?**
Pela lista de E/S da arquitetura do grupo, reconciliada e materializada em [tags.csv](../projeto/tags.csv) (164 variáveis: tipo, unidade, sentido de escrita, origem, status).

**2.4 Como o termopar rompido é detectado?**
Pelo valor de fim de escala do módulo (32767) → `TC_Zn_ABERTO`/`TC_Zn_OK`. É uma **hipótese do módulo SM 1231**; em outro hardware usa-se o diagnóstico do módulo. A leitura inválida **não** é tratada como sobretemperatura: gera `TC_FAULT`. → [LADDER_EXPLICADO §4](../entender/LADDER_EXPLICADO.md#4-rede-por-rede)

**2.5 O que está em aberto no hardware?**
A **tensão do sistema** (220 V monofásico × trifásico sem neutro) é inconsistente entre o cálculo do K1 e o esquema elétrico: deve ser resolvida pela área elétrica antes de dimensionar. → [SOURCE_RECONCILIATION D12](SOURCE_RECONCILIATION.md)

---

## 3. Ladder e lógica

**3.1 Como funciona um CLP?**
Repete, a cada ciclo (aqui 100 ms), três passos: lê as entradas, executa o programa **de cima para baixo**, escreve as saídas. A ordem das redes importa. → [LADDER_EXPLICADO §2](../entender/LADDER_EXPLICADO.md#2-o-ciclo-de-varredura)

**3.2 Como ler uma rede Ladder?**
Contatos = condições; **série = E**, **paralelo = OU**; bobina = saída; `S`/`R` = set/reset. → [LADDER_EXPLICADO §1](../entender/LADDER_EXPLICADO.md#1-como-ler-uma-rede-ladder-3-minutos)

**3.3 Por que o PID não fica depois de contatos (como na prancha)?**
Se o bloco deixa de ser chamado, a saída **congela** no último valor e pode manter um aquecedor ligado. Aqui o PID roda **todo ciclo**; o bloqueio é feito no pino `RESET` do PID e no portão do SSR. A própria monografia descreve esse erro. → [SOURCE_RECONCILIATION D16](SOURCE_RECONCILIATION.md)

**3.4 O que é falha "travada" e por que reset condicionado?**
`FALHA_GERAL` é *set* quando qualquer das 10 causas críticas aparece e só é apagada por `BT_RESET` **E** nenhuma causa ativa. Evita religar com a causa ainda presente. Ensaiado no CLP: o reset é recusado com a causa presente e aceito depois. → [CP4 cenários](../evidence/CP4_ONLINE_SCENARIOS.txt)

**3.5 E se a causa some sozinha?**
Os latches `CAUSA_*` guardam a **primeira causa**, e a falha continua travada até o operador resetar. A tela mostra qual causa travou.

**3.6 Por que `BT_DESLIGA` é normalmente fechado?**
Fail-safe: se o fio romper, o contato abre e o programa **para**. Por isso, no Ladder, "parar" é nível 0. A tela envia um pulso de 1 s abrindo esse contato.

**3.7 Por que "um escritor por saída"?**
Duas redes escrevendo a mesma saída fazem a última sobrescrever a anterior (erro clássico em `INV_REF`). Há teste automático que verifica isso.

**3.8 Qual a política de pressão?**
≥ 16,5 MPa: alarme e referência × 0,9 (piso de 17 rpm); ≥ 17 MPa: falha travada e rosca parada. Unifica três descrições divergentes das fontes. → [SOURCE_RECONCILIATION D5](SOURCE_RECONCILIATION.md)

**3.9 Como funciona o encharque de 15 min?**
As 5 zonas ≥ 330 °C **continuamente** por 900 s (TON). Se uma cair, o temporizador zera. Medido no CLP em 4 corridas: PRONTO em 903 a 906 s. → [CP4 cenários](../evidence/CP4_ONLINE_SCENARIOS.txt)

**3.10 Como o Ladder foi criado se o CODESYS não é "desenhado por IA"?**
Um gerador em Python descreve as redes e produz **PLCopen XML**; o CODESYS importa, compila e executa. O mesmo modelo alimenta os testes e as imagens de [LADDER](../entender/LADDER.md).

**3.11 Por que tantos testes se o CLP real já roda?**
Dois níveis se completam: o avaliador Python testa a lógica rápido e em massa; o CLP real prova a execução. **O CLP real achou defeitos que o avaliador não via** (presets de TON perdidos na importação; falso alarme de sobretemperatura com termopar aberto), corrigidos e cobertos por teste de regressão.

---

## 4. Controle (PID) e temperatura

**4.1 Como é o controle de temperatura?**
Um PID por zona (5) mais um para o infravermelho. A saída (0–100 %) vira **PWM por fase** (20 ciclos de 100 ms) que liga o SSR da resistência. O portão do SSR exige aquecimento ligado, K1 confirmado, zona < 390 °C e termopar íntegro.

**4.2 Os ganhos estão sintonizados?**
**Não.** KP = 8 %/°C e TN = 20 s (zonas) são **hipotéticos**. Foi verificado que o `Util.PID` real se comporta como o modelo (KP e Ki ajustados 8,00 e 0,399 contra 8 e 0,40; erro médio 0,4–1,0 %). A sintonia real exige ensaio na máquina. → [CP4_PID_COMPARE](../evidence/CP4_PID_COMPARE.txt)

**4.3 O que é anti-windup e qual o usado?**
Evita que a integral cresça enquanto a saída está saturada. O `Util.PID` real usa **retrocálculo** (a integral é adaptada para que a saída fique no limite); isso foi **medido** no CLP e o modelo de referência foi corrigido para igualar.

**4.4 Qual o sobressinal?**
Na **planta simulada**, no máximo ≈ 2,8 °C acima do setpoint nos ensaios. Não vale para máquina real (parâmetros hipotéticos).

**4.5 Por que PWM e não saída analógica?**
O atuador é um **SSR** (liga/desliga). A modulação por largura de pulso aproxima potência contínua; o período de 2 s é pequeno frente à constante térmica das zonas (60 s na simulação).

**4.6 Por que 330 °C e 15 min de encharque?**
Valores propostos pelo grupo (material parado funde devagar; o resfriamento/ventilador perde vazão em baixa rotação). São **ajustáveis**; o que é testado é a lógica (contínuo, zera se cair).

---

## 5. Segurança e falhas

**5.1 A tela web pode parar a máquina em emergência?**
**Não.** A emergência é **circuito de hardware independente**. A tela avisa isso em todas as telas e só **solicita** ações.

**5.2 Quais falhas o programa trata?**
10 causas críticas: segurança/porta, sobretemperatura do motor, falha do inversor, pressão ≥ 17 MPa, zona > 400 °C, termopar rompido, câmara quente por 2 min, sem material por 60 s, ventilador sem retorno por 10 s, K1 colado por 1 s. → [LADDER_EXPLICADO §5](../entender/LADDER_EXPLICADO.md#5-as-10-causas-de-falha-rede-04)

**5.3 Qual a diferença entre alarme e falha?**
Alarme (390 °C, 16,5 MPa, trecho frio) **sinaliza** sem travar; falha **trava** e desliga aquecimento e rosca.

**5.4 O que acontece se a comunicação cair?**
O CLP continua executando o Ladder sozinho (a segurança não depende da tela). A tela detecta o heartbeat parado (2 s), mostra **SEM COMUNICAÇÃO**, desabilita comandos, para de pintar valores em verde e **descarta** pedidos pendentes (nunca reenviados).

**5.5 Há análise de falhas (efeito, detecção, resposta)?**
O comportamento está definido e ensaiado por causa (termopar, inversor, K1, emergência, pressão, ventilador, material). A **tabela formal de análise de falhas** do texto da monografia é tarefa do grupo; o ensaio fornece os dados. → [ACADEMIC_COMPLIANCE](ACADEMIC_COMPLIANCE.md)

**5.6 Isso é segurança funcional certificada (SIL/PL)?**
**Não.** Não há cálculo de SIL/PL nem relés/CLP de segurança certificados. É uma lógica didática; a segurança real exige hardware certificado e análise de riscos.

**5.7 Como as credenciais são protegidas?**
Somente em **variáveis de ambiente da sessão** (o script pede a senha de forma oculta); nunca em arquivo, log ou Git. Os logs da biblioteca OPC UA foram forçados a `WARNING` (em `DEBUG` ela imprimia a senha — achado, com teste).

---

## 6. SCADA, comunicação e integração

**6.1 Como a tela controla o Ladder?**
A tela **solicita** (`POST /api/command`) → o backend valida e escreve **só entradas** no CLP por OPC UA (pulso de 0,5 s) → o Ladder decide → o backend lê o estado → a tela mostra "✓ Confirmado" **somente** quando o estado volta do CLP. → [COMO_FUNCIONA §4](../entender/COMO_FUNCIONA.md#4-como-a-tela-controla-o-ladder-passo-a-passo)

**6.2 Como o backend se liga ao CODESYS?**
Cliente **OPC UA** criptografado (`Basic256Sha256`, assinado e cifrado), com certificados e Configuração de símbolos no CODESYS. → [LIGACAO_BACKEND_CODESYS](../entender/LIGACAO_BACKEND_CODESYS.md)

**6.3 Por que OPC UA e não PROFINET (que a proposta cita)?**
PROFINET é o barramento de campo da proposta (CLP–inversor–robô) e **não foi testado nem simulado**. OPC UA é o canal de **supervisão** que o CODESYS suporta e que permite autenticação e criptografia. São camadas diferentes.

**6.4 Como a tela sabe que o dado é real e atual?**
Pelo **heartbeat** (`PLC_HEARTBEAT`, +1 por ciclo). Parado por mais de 2 s → dado obsoleto. O selo no topo diz o modo: `DEMO / SIMULADO` ou `LÓGICA NO CLP · PLANTA SIMULADA`.

**6.5 O que é o modo DEMO e o modo apresentação?**
DEMO executa o mesmo Ladder num avaliador Python (sem CODESYS). O **modo apresentação** (seletor no topo, só no DEMO) acelera o relógio simulado: **90×** leva da partida à extrusão em ~15 s e a demonstração inteira cabe em ~2 min. No modo CLP o tempo é o real (os temporizadores são os do Ladder).

**6.6 Quais são as 6 telas?**
Visão geral, Temperaturas/PID, Deposição/IR, Alarmes, Receitas e Histórico. → [GALERIA](../entender/GALERIA.md)

**6.7 Os setpoints são validados?**
Sim, no backend (zonas 330–375 °C, 17–34 rpm, IR 20–480 °C) e a tela bloqueia o ajuste durante a extrusão.

---

## 7. Testes e validação

**7.1 O que foi testado e como?**
(a) **Lógica** por rede em Python (limiares, temporizadores, selo, reset com cada causa, PWM); (b) **compilação** no CODESYS (0 erros e 0 avisos); (c) **execução no CLP real**: ida e volta tela→CLP→tela e cenários de falha em tempo real; (d) **interface**: build, testes E2E em 4 tamanhos de tela; (e) **segurança**: avaliador sem `eval`, senha fora dos logs.

**7.2 Como provar que o Ladder rodou de verdade?**
[Ensaio de ida e volta](../evidence/CP3_ROUNDTRIP_OK.txt) (termina com `CP3 OK`) e [cenários completos](../evidence/CP4_ONLINE_SCENARIOS.txt), ambos lidos do CLP via OPC UA. A planta que alimenta as entradas é simulada.

**7.3 Quais cenários foram ensaiados no CLP?**
Termopar rompido, falha do inversor, K1 colado, disjuntor aberto, emergência lógica, encharque de 15 min até PRONTO, partida da extrusão, aviso e falha de pressão, ventilador, falta de material e parada normal com pós-ventilação de 5 min.

**7.4 Como reproduzir os testes?**
`tools\run-tests.ps1` (pytest + build; `-E2E` inclui a interface) e `tools\cp4_scenarios.py` para o CLP. → [INICIO_RAPIDO](../guias/INICIO_RAPIDO.md)

**7.5 O que NÃO foi testado?**
Sintonia dos PIDs em máquina real, escala do inversor, PROFINET/S7-1200, máquina física e perda de comunicação com o CLP **em execução real** (coberta por testes com servidor de teste e pela lógica de obsolescência).

---

## 8. Limites, honestidade e trabalho em grupo

**8.1 Quais são as limitações?**
Planta simulada e parâmetros hipotéticos; ganhos não sintonizados; escala do inversor (16384 = 60 Hz) a confirmar; tensão do painel em aberto; nenhuma validação em máquina; não é segurança certificada.

**8.2 O que o grupo ainda precisa produzir?**
A **monografia manuscrita**, a apresentação oral de 20 min e a tabela formal de análise de falhas. O repositório fornece código, evidências e o roteiro. → [ROTEIRO_APRESENTACAO](ROTEIRO_APRESENTACAO.md)

**8.3 Houve uso de IA? Como declarar?**
Sim: o assistente (Claude Code) ajudou a gerar o código, os testes e os documentos, sob revisão do grupo. Declare isso conforme a regra da disciplina; **todos devem dominar o projeto inteiro** e saber explicar qualquer parte (use [COMO_FUNCIONA](../entender/COMO_FUNCIONA.md) e [LADDER_EXPLICADO](../entender/LADDER_EXPLICADO.md) para estudar).

**8.4 Como saber que as fontes do grupo foram respeitadas?**
Toda divergência entre fontes (prancha × monografia × arquitetura) foi registrada com a decisão tomada e o teste que a valida: 25 itens em [SOURCE_RECONCILIATION](SOURCE_RECONCILIATION.md).

---

## 9. Perguntas-armadilha

| Pergunta | Resposta honesta |
|---|---|
| "Então o sistema está pronto para a fábrica?" | **Não.** É um protótipo educacional validado em simulação; falta sintonia, comissionamento e segurança certificada |
| "O PID está sintonizado?" | **Não**; ganhos hipotéticos. O que foi verificado é que o bloco real se comporta como o modelo |
| "A web comanda a máquina?" | A web **solicita**; quem decide é o Ladder; a emergência é hardware independente |
| "Isso rodou num S7-1200?" | **Não.** Rodou no CODESYS Control Win; o S7-1200 é a proposta |
| "Por que não escreveram em ST?" | O enunciado exige **Ladder real ligado ao processo**; o Ladder é o artefato central |
| "E se o sensor der leitura absurda?" | Termopar inválido → `TC_FAULT` (falha travada); não vira sobretemperatura falsa |
| "E se a rede cair?" | O CLP segue sozinho; a tela marca SEM COMUNICAÇÃO e bloqueia comandos |
| "Quem garante que a tela não mente?" | O "confirmado" só aparece quando o estado volta do CLP; sem heartbeat, nada é pintado como normal |
| "Qual a diferença entre o DEMO e o CLP?" | DEMO usa um avaliador Python do mesmo programa; no modo CLP o Ladder roda no Control Win. O selo no topo diz qual |
| "Quanto do código foi testado automaticamente?" | Mais de 80 testes pytest (Ladder, simulador, backend, OPC UA de teste) e E2E da interface; o CLP foi ensaiado por cenários |
