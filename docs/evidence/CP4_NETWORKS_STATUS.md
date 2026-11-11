# CP4 - inventario rede a rede (2026-11-11)

Programa gerado: `codesys/exports/LFAM_PROGRAM.xml` (70 elementos de rede; ordem em `codesys/generator/program.py`).
Build headless em copia do projeto: **"Compilacao completa -- 0 erros, 0 avisos"**. 40 testes pytest (avaliador de referencia com tempo simulado).
Legenda: IMPLEMENTADA = gerada, importada e compilada no CODESYS; TESTADA = coberta por pytest contra o avaliador de referencia
(equivalencia booleana/temporal da MESMA estrutura que gera o XML). **Nenhuma rede alem da POC foi executada online no Control Win ainda.**

| Rede | Funcao | Status | Observacao |
|---|---|---|---|
| 01 | Escalonamento analogico | IMPLEMENTADA, TESTADA | atribuicao grafica `INT_TO_REAL(raw)/27648*faixa` (equivale a NORM_X+SCALE_X) |
| 02 | Termopares, 390/400 degC, fio aberto 32767 | IMPLEMENTADA, TESTADA | 32767 e hipotese do modulo Siemens |
| 03 | TONs 2 min / 60 s / 10 s / 1 s | IMPLEMENTADA, TESTADA | |
| 04 | M_CAUSA (10 causas) + falha travada + reset condicionado | IMPLEMENTADA, TESTADA | corrige reset da Prancha 1 (D3) |
| 05 | EST_AQUEC com selo + K1 | IMPLEMENTADA, TESTADA | |
| 06 | Liberacao do SSR por zona | IMPLEMENTADA (so o gate), TESTADA | **PID em si ainda nao existe** (FB em tarefa propria) |
| 07 | Histerese 80/60 | IMPLEMENTADA, TESTADA | |
| 08 | Encharque 15 min | IMPLEMENTADA, TESTADA | |
| 09 | Pronto + sinal ao robo | IMPLEMENTADA, TESTADA | |
| 10 | Rosca manual/auto, STOP prioritario | IMPLEMENTADA, TESTADA | |
| 11 | Ventilacao +5 min | IMPLEMENTADA, TESTADA | TON em vez de TOF |
| 12 | Velocidade/pressao (politica D5) | IMPLEMENTADA, TESTADA | escritor unico de REF_RPM_LIM; falta escala para INV_REF |
| 13 | Gate do IR + SSR_IR | IMPLEMENTADA (gate), TESTADA | PID do IR pendente |
| 14 | Funil + CTU | **PENDENTE** | requer CTU/R_TRIG |
| 15 | Alarmes e torre luminosa | IMPLEMENTADA, TESTADA | |

Limites conhecidos: variaveis locais do PLC_PRG (sem GVL/E-S); comparadores como contato com expressao; layout grafico nao revisado;
PID, CTU e tarefa ciclica de 100 ms ainda nao criados; logica nao validada no runtime (so POC).

## Atualização (rede 14, PIDs reais e escala) - 2026-11-11
Programa: 88 elementos (`codesys/exports/LFAM_PROGRAM.xml`), biblioteca **Util 3.5.22.0** adicionada, MainTask cíclica de **100 ms** (equivalente ao OB30).
Build headless em cópia: **"Compilação completa -- 0 erros, 0 avisos"**. 59 testes pytest.
- **PIDs reais:** 5 zonas + IR com `Util.PID` (KP, TN, Y 0..100 %, RESET quando sem aquecimento/termopar ruim/IR não habilitado); chamados SEM EN todo ciclo.
  PWM por fase de 20 ciclos (2 s) -> `PWM_Zn`; só chega ao SSR nos gates das redes 06/13. Parâmetros KP/TN **hipotéticos**.
- **Rede 14:** `R_TRIG` + `CTU` (`CONT_LOTES`, reset `HMI_RESET_LOTES`), carregador `ALIM_FUNIL` (FUNIL_BAIXO=0).
- **Rede 12:** `INV_REF` (INT) com escala hipotética 16384 = 60 Hz (motor 29..57 Hz).
- **Descobertas do importador PLCopen (3.5.22.40):** (1) `PID` precisa do nome qualificado `Util.PID`; (2) entradas de FB por *expressão dentro do pino* geram erro
  fantasma BOOL->REAL, o estilo `inVariable` compila limpo; (3) saídas por `outVariable` são mapeadas fora de ordem, o destino em `connectionPointOut/expression` funciona;
  (4) `ET` de TON via `outVariable` quebra -> PWM por contador de ciclos.
- **Pendente:** execução ONLINE do programa completo (só a POC rodou no Control Win); sintonia real dos PIDs; layout gráfico não revisado.
