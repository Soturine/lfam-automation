"""Redes com comparadores e temporizadores: 02, 03, 07 (flags), 08 e 11.
Temperaturas TT_Zn, TT_RESF em degC (REAL) ja escalonadas; a rede 01 (NORM_X/SCALE_X) ainda nao existe."""
from .ld import C, S, P, CmpRung, TonRung, Rung, Coil

ZONES = range(1, 6)

# NETWORK 02 - supervisao dos termopares / sobretemperatura
NET02 = []
for z in ZONES:
    NET02.append(CmpRung(f"NETWORK 02 - Z{z} acima de 390 degC (pre-alarme)", "GT", f"TT_Z{z}", "390.0", f"SOBRETEMP_390_Z{z}"))
for z in ZONES:
    NET02.append(CmpRung(f"NETWORK 02 - Z{z} acima de 400 degC (falha)", "GT", f"TT_Z{z}", "400.0", f"SOBRETEMP_400_Z{z}"))
NET02.append(Rung("NETWORK 02 - SOBRETEMP_400: OR das cinco zonas",
                  P(*[C(f"SOBRETEMP_400_Z{z}") for z in ZONES]), [Coil("SOBRETEMP_400")]))
NET02.append(Rung("NETWORK 02 - TC_FAULT: OR de termopar com qualidade ruim",
                  P(*[C(f"TC_Z{z}_OK", neg=True) for z in ZONES]), [Coil("TC_FAULT")]))

# NETWORK 03 - temporizadores de intertravamento
NET03 = [
    CmpRung("NETWORK 03 - TT_RESF acima de 100 degC", "GT", "TT_RESF", "100.0", "RESF_ACIMA_100"),
    TonRung("NETWORK 03 - camara quente por 2 min", C("RESF_ACIMA_100"), "T_RESF_100C", 120.0, "FALHA_RESF_2M"),
    TonRung("NETWORK 03 - sem material por 60 s (FUNIL_BAIXO=0 e vazio)",
            S(C("EST_EXTRUSAO"), C("FUNIL_BAIXO", neg=True), C("ALIM_FUNIL")), "T_FUNIL_VAZIO", 60.0, "FALHA_SEM_MAT"),
    TonRung("NETWORK 03 - rosca sem ventilacao por 10 s", S(C("INV_RUN"), C("VENT_OK", neg=True)), "T_FALHA_VENT", 10.0, "FALHA_VENT_10S"),
    TonRung("NETWORK 03 - K1 colado por 1 s (confirma sem comando)", S(C("K1_AQUEC", neg=True), C("K1_CONF")), "T_K1_COLADO", 1.0, "FALHA_K1_COL"),
]

# NETWORK 07 (flags da histerese)
NET07_FLAGS = [
    CmpRung("NETWORK 07 - RESF_HI: TT_RESF acima de 80 degC", "GT", "TT_RESF", "80.0", "RESF_HI"),
    CmpRung("NETWORK 07 - RESF_LO: TT_RESF abaixo de 60 degC", "LT", "TT_RESF", "60.0", "RESF_LO"),
]

# NETWORK 08 - encharque de 15 min (zonas >= 330 em AND; TON zera se qualquer zona cair)
NET08 = [CmpRung(f"NETWORK 08 - Z{z} >= 330 degC", "GE", f"TT_Z{z}", "330.0", f"Z{z}_ATEMP") for z in ZONES]
NET08.append(Rung("NETWORK 08 - EST_ENCHARQUE: aquecimento ligado e todas as zonas >= 330 (Prancha 2: gate por EST_AQUEC)", S(C("EST_AQUEC"), *[C(f"Z{z}_ATEMP") for z in ZONES]), [Coil("EST_ENCHARQUE")]))
NET08.append(TonRung("NETWORK 08 - encharque continuo de 15 min", C("EST_ENCHARQUE"), "T_ENCHARQUE", 900.0, "ENCH_OK"))

# NETWORK 11 - ventilacao do motor: liga com a rosca e segue 5 min apos parar
NET11 = [
    TonRung("NETWORK 11 - 5 min de pos-ventilacao (rosca parada e ventilador ligado)",
            S(C("EST_EXTRUSAO", neg=True), C("VENT_MOTOR")), "T_POS_VENT", 300.0, "VENT_FIM"),
    Rung("NETWORK 11 - VENT_MOTOR (unico escritor): rosca OU em pos-ventilacao ate o fim do tempo",
         S(P(C("EST_EXTRUSAO"), C("VENT_MOTOR")), C("VENT_FIM", neg=True)), [Coil("VENT_MOTOR")]),
]
