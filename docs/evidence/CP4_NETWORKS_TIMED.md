# CP4 (parcial) - redes 02, 03, 04, 05, 07, 08, 10, 11 em um unico programa - 2026-11-11

`python tools/gen_ld_xml.py` -> `codesys/exports/LFAM_PROGRAM.xml` (35 redes, ordem de execucao em `codesys/generator/program.py`).

## Verificado (executado)
- `pytest`: 31 testes (logica + tempo simulado): limiares 390/400 por zona, termopar aberto por zona, camara quente so falha apos 2 min
  (e zera se voltar), histerese 80/60, falta de material 60 s, ventilacao 10 s, K1 colado 1 s, encharque 15 min continuo que reinicia
  se uma zona cair, ventilacao 5 min apos parar e mantida se religar, **um unico escritor por saida** no XML completo.
- Importacao em copia do projeto (headless) + build: **"Compilacao completa -- 0 erros, 0 avisos"** (35 redes).

## Descobertas de formato (CODESYS 3.5.22.40, PLCopen XML)
- Caixas de comparacao `GT/GE/LT` com pinos `IN1/IN2/OUT` ou `In1/In2/Out1` -> **erro C22 "requer exatamente 2 operandos"**; sem `formalParameter`
  a importacao falha. Nomes de pino nao documentados; **solucao adotada**: comparacao como contato com expressao booleana
  (`TT_Z1 > 390.0`) alimentando bobina (LD gráfico valido).
- `TON` aceita so a saida usada (`Q`); declarar tambem `ET` gera "O bloco tem saidas demais".

## Nao verificado
- Execucao online do programa completo no Control Win (teste online ainda so da POC de 1 rede).
- Redes 01, 06, 09, 12, 13, 14, 15; escalonamento analogico e PID.
- Legibilidade do layout no editor.
