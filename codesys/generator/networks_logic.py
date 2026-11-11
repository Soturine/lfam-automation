"""Redes puramente booleanas do LFAM: 04, 05, 07 e 10.
Reset de falha: so com M_CAUSA = FALSE (decisao D3 em docs/SOURCE_RECONCILIATION.md)."""
from .ld import C, S, P, Rung, Coil, Set, Reset, variables_of

# Causas criticas, com polaridade corrigida (SEG_OK e MOT_SOBRETEMP sao ativos-baixos).
CAUSAS = [
    C("SEG_OK", neg=True), C("MOT_SOBRETEMP", neg=True), C("INV_FALHA"), C("PRESSAO_ALTA_17"),
    C("SOBRETEMP_400"), C("TC_FAULT"), C("FALHA_RESF_2M"), C("FALHA_SEM_MAT"), C("FALHA_VENT_10S"), C("FALHA_K1_COL"),
]

NET04_M_CAUSA = Rung("NETWORK 04a - M_CAUSA: OR de todas as causas criticas", P(*CAUSAS), [Coil("M_CAUSA")])
NET04_SET = Rung("NETWORK 04b - FALHA_GERAL travada (SET por M_CAUSA)", C("M_CAUSA"), [Set("FALHA_GERAL")])
NET04_RESET = Rung(
    "NETWORK 04c - RESET condicionado (BT_RESET e nenhuma causa ativa)",
    S(C("BT_RESET"), C("M_CAUSA", neg=True)), [Reset("FALHA_GERAL")],
)

# 05: aquecimento com selo; permissivos em serie (qualquer perda desliga: prioridade de desligamento).
NET05_AQUEC = Rung(
    "NETWORK 05 - EST_AQUEC (selo; desligamento tem prioridade)",
    S(P(C("BT_AQUEC"), C("EST_AQUEC")), C("SEG_OK"), C("DISJ_AQUEC"), C("FALHA_GERAL", neg=True),
      C("SOBRETEMP_400", neg=True), C("FALHA_K1_COL", neg=True)),
    [Coil("EST_AQUEC")],
)
NET05_K1 = Rung("NETWORK 05b - K1_AQUEC segue EST_AQUEC (unico escritor)", C("EST_AQUEC"), [Coil("K1_AQUEC")])

# 07: histerese do resfriamento; RESF_HI = TT_RESF > 80, RESF_LO = TT_RESF < 60 (flags calculados nas redes analogicas)
NET07_RESF = Rung(
    "NETWORK 07 - Resfriamento por histerese (liga >80, mantem ate <60)",
    S(P(C("RESF_HI"), C("RESF_ON")), C("RESF_LO", neg=True)), [Coil("RESF_ON")],
)

# 10: rosca manual/automatica; BT_DESLIGA e NF (0 = parar) e fica em serie: parada tem prioridade.
NET10_ROSCA = Rung(
    "NETWORK 10 - Rosca (manual com selo / automatico pelo robo)",
    S(C("EST_PRONTO"), C("BT_DESLIGA"), C("FALHA_GERAL", neg=True),
      P(S(C("SEL_AUTO", neg=True), P(C("BT_LIGA"), C("EST_EXTRUSAO"))), S(C("SEL_AUTO"), C("ROBO_CMD_EXTR")))),
    [Coil("EST_EXTRUSAO")],
)

ALL = [NET04_M_CAUSA, NET04_SET, NET04_RESET, NET05_AQUEC, NET05_K1, NET07_RESF, NET10_ROSCA]


def variables() -> dict:
    return variables_of(ALL)


# Preservacao da PRIMEIRA causa: cada causa tem um latch CAUSA_<nome>, setado na varredura em que ela esta ativa e a falha
# ainda NAO estava travada (antes de 04b), e resetado junto com a falha. Assim a causa nao se perde quando some sozinha.
CAUSA_NAMES = ["SEG_OK", "MOT_SOBRETEMP", "INV_FALHA", "PRESSAO_ALTA_17", "SOBRETEMP_400", "TC_FAULT",
               "FALHA_RESF_2M", "FALHA_SEM_MAT", "FALHA_VENT_10S", "FALHA_K1_COL"]
NET04_FIRST = [
    Rung(f"NETWORK 04d - primeira causa: CAUSA_{n} (set na varredura em que a falha ainda nao estava travada)",
         S(CAUSAS[i], C("FALHA_GERAL", neg=True)), [Set(f"CAUSA_{n}")])
    for i, n in enumerate(CAUSA_NAMES)
] + [
    Rung(f"NETWORK 04e - CAUSA_{n} reseta junto com a falha (BT_RESET e nenhuma causa ativa)",
         S(C("BT_RESET"), C("M_CAUSA", neg=True)), [Reset(f"CAUSA_{n}")])
    for n in CAUSA_NAMES
]
