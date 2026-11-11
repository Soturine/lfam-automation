"""Redes 01, 06 (liberacao dos SSR), 09, 12, 13 (gate do IR) e 15.
As expressoes das atribuicoes sao escritas pelos autores do projeto (nao ha entrada externa no eval do avaliador)."""
from .ld import C, S, P, Rung, Coil, CmpRung, AssignRung

ZONES = range(1, 6)

# NETWORK 01 - escalonamento analogico (equivale a NORM_X + SCALE_X; 0..27648 -> faixa de engenharia)
NET01 = [
    AssignRung("NETWORK 01 - PT_FUNDIDO 0..27648 -> 0..35 MPa", "PT_FUNDIDO_MPA",
               "INT_TO_REAL(PT_FUNDIDO_RAW) / 27648.0 * 35.0", {"PT_FUNDIDO_MPA": "REAL", "PT_FUNDIDO_RAW": "INT"}),
    AssignRung("NETWORK 01 - TT_SUBSTRATO 0..27648 -> 0..500 degC", "TT_SUBSTRATO_C",
               "INT_TO_REAL(TT_SUBSTRATO_RAW) / 27648.0 * 500.0", {"TT_SUBSTRATO_C": "REAL", "TT_SUBSTRATO_RAW": "INT"}),
]

# NETWORK 02 (escalonamento dos termopares: 0,1 degC; 32767 = circuito aberto no modulo SM 1231, hipotese Siemens)
for z in ZONES:
    NET01.append(AssignRung(f"NETWORK 02 - TT_Z{z} (0,1 degC -> degC)", f"TT_Z{z}", f"INT_TO_REAL(TT_Z{z}_RAW) / 10.0",
                            {f"TT_Z{z}": "REAL", f"TT_Z{z}_RAW": "INT"}))
    NET01.append(CmpRung(f"NETWORK 02 - Z{z} termopar aberto (RAW = 32767)", "EQ", f"TT_Z{z}_RAW", "32767", f"TC_Z{z}_ABERTO"))

# NETWORK 06 - liberacao do PWM de cada zona para o SSR (PID roda sempre em tarefa propria; aqui so o gate)
NET06 = [
    Rung(f"NETWORK 06 - SSR_Z{z}: PWM so com aquecimento, K1 confirmado, zona < 390 degC e termopar integro",
         S(C(f"PWM_Z{z}"), C("EST_AQUEC"), C("K1_CONF"), C(f"SOBRETEMP_390_Z{z}", neg=True), C(f"TC_Z{z}_OK")),
         [Coil(f"SSR_Z{z}")])
    for z in ZONES
]

# NETWORK 09 - extrusora pronta e sinal ao robo
NET09 = [
    Rung("NETWORK 09 - EST_PRONTO: encharque ok, secador, inversor pronto, sem falha memorizada",
         S(C("ENCH_OK"), C("SECADOR_OK"), C("INV_PRONTO"), C("FALHA_GERAL", neg=True)), [Coil("EST_PRONTO")]),
    Rung("NETWORK 09 - ROBO_EXT_PRONTA segue EST_PRONTO", C("EST_PRONTO"), [Coil("ROBO_EXT_PRONTA")]),
]

# NETWORK 12 - velocidade e pressao (politica D5: em >=16,5 MPa referencia x0,9; LIMIT 17..34; unica atribuicao)
NET12 = [
    CmpRung("NETWORK 12 - ALM_PRESSAO_16_5: pressao >= 16,5 MPa", "GE", "PT_FUNDIDO_MPA", "16.5", "ALM_PRESSAO_16_5"),
    CmpRung("NETWORK 04 - PRESSAO_ALTA_17: pressao >= 17 MPa", "GE", "PT_FUNDIDO_MPA", "17.0", "PRESSAO_ALTA_17"),
    AssignRung("NETWORK 12 - REF_RPM_LIM := LIMIT(17, SP (x0,9 se alarme), 34) - unico escritor", "REF_RPM_LIM",
               "LIMIT(17.0, SEL(ALM_PRESSAO_16_5, SP_RPM_OPERADOR, SP_RPM_OPERADOR * 0.9), 34.0)",
               {"REF_RPM_LIM": "REAL", "SP_RPM_OPERADOR": "REAL", "ALM_PRESSAO_16_5": "BOOL"}),
]

# NETWORK 13 - habilitacao do aquecedor IR (PID do IR roda na tarefa de PID; aqui o gate e o SSR)
NET13 = [
    CmpRung("NETWORK 13 - IR_FAIXA_MIN: substrato >= 20 degC", "GE", "TT_SUBSTRATO_C", "20.0", "IR_ACIMA_MIN"),
    CmpRung("NETWORK 13 - IR_FAIXA_MAX: substrato <= 480 degC", "LE", "TT_SUBSTRATO_C", "480.0", "IR_ABAIXO_MAX"),
    Rung("NETWORK 13 - IR_HAB: rosca girando, robo em movimento, pirometro na faixa, sem falha",
         S(C("EST_EXTRUSAO"), C("ROBO_EM_MOV"), C("IR_ACIMA_MIN"), C("IR_ABAIXO_MAX"), C("FALHA_GERAL", neg=True)), [Coil("IR_HAB")]),
    Rung("NETWORK 13 - SSR_IR (unico escritor): PWM_IR so com IR_HAB", S(C("PWM_IR"), C("IR_HAB")), [Coil("SSR_IR")]),
]

# NETWORK 15 - alarmes e coluna luminosa (aviso x falha travada)
NET15 = [
    CmpRung("NETWORK 15 - ALM_ZSR_BAIXA: trecho sem resistencia < 220 degC", "LT", "TT_ZSR", "220.0", "ALM_ZSR_BAIXA"),
    Rung("NETWORK 15 - LUZ_VERDE: extrusao", C("EST_EXTRUSAO"), [Coil("LUZ_VERDE")]),
    Rung("NETWORK 15 - LUZ_AMARELA: aquecendo ou aguardando encharque (sem extrusao, sem falha)",
         S(C("EST_AQUEC"), C("EST_EXTRUSAO", neg=True), C("FALHA_GERAL", neg=True)), [Coil("LUZ_AMARELA")]),
    Rung("NETWORK 15 - LUZ_VERM_SIRENE: falha travada OU aviso de pressao OU trecho frio",
         P(C("FALHA_GERAL"), C("ALM_PRESSAO_16_5"), C("ALM_ZSR_BAIXA")), [Coil("LUZ_VERM_SIRENE")]),
]

# NETWORK 10 (saida) - INV_RUN segue a rosca (unico escritor)
NET10B = [Rung("NETWORK 10 - INV_RUN segue EST_EXTRUSAO (unico escritor)", C("EST_EXTRUSAO"), [Coil("INV_RUN")])]

# NETWORK 14 (parte alimentacao) - carregador liga quando o funil esvazia (FUNIL_BAIXO = 0). Contagem CTU ainda pendente.
NET14A = [Rung("NETWORK 14 - ALIM_FUNIL: carregador liga com funil vazio (FUNIL_BAIXO=0)", C("FUNIL_BAIXO", neg=True), [Coil("ALIM_FUNIL")])]
