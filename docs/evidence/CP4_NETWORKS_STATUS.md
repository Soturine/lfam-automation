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
