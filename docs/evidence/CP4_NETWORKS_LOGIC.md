# CP4 (parcial) - redes booleanas 04, 05, 07, 10 geradas e compiladas - 2026-11-11

Gerador: `codesys/generator/ld.py` (DSL contatos/serie/paralelo/bobinas set-reset -> PLCopen XML + avaliador de referencia).
Redes: `codesys/generator/networks_logic.py` (M_CAUSA/FALHA_GERAL/reset condicionado, EST_AQUEC+K1, histerese RESF, rosca manual/auto).
XML gerado: `codesys/exports/NETWORKS_LOGIC.xml` (`python tools/gen_ld_xml.py`).

## Verificado (executado)
- `pytest`: 20 testes passam (11 de logica: 10 causas travam FALHA_GERAL e impedem reset; reset so com M_CAUSA=0; SET com prioridade;
  partida a frio com entradas ativas-baixas em 0 = falha; K1 cai com perda de qualquer permissivo; histerese sem chatter;
  rosca com selo, parada NF com prioridade, modo auto; escritor unico por bobina).
- Importacao no CODESYS (copia `work/LFAM_NET.project`, projeto original intacto) + `app.build()`:
  **"Compilacao completa -- 0 erros, 0 avisos"** (saida do compilador, stderr do script headless).
- Round-trip: exportando de volta do projeto compilado: 32 contatos (= esperado), 7 bobinas (1 SET, 1 RESET),
  OR cabeado preservado (M_CAUSA com 10 conexoes, EST_EXTRUSAO com 3).

## Nao verificado ainda
- Execucao online destas redes no Control Win (so a POC de 1 rede esta em teste online).
- Posicoes/layout graficos: o CODESYS organiza na importacao; a legibilidade no editor nao foi revisada.
- Redes com blocos (TON/TOF/CTU, comparadores, NORM_X/SCALE_X, PID) e redes 01-03, 06, 08, 09, 11-15 ainda nao existem.
- Variaveis estao como locais do PLC_PRG (nao GVL) e sem mapeamento de E/S.
