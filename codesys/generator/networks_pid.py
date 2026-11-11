"""Rede 06/13 (PID reais Util.PID + PWM), rede 14 (R_TRIG + CTU) e escala do inversor.

Execucao: PID e PWM sao chamados SEM EN em todo ciclo da MainTask (cíclica, 100 ms): equivalente didatico ao OB30 do S7-1200.
O PID e desabilitado por RESET=TRUE (saida = offset 0, integral zerada); o PWM so chega ao SSR nas redes 06/13 (gate).
Parametros iniciais HIPOTETICOS (KP em %/degC, TN em s); a sintonia real exige ensaio.
"""
from .ld import CmpRung, FbRung, AssignRung

ZONES = range(1, 6)

# Dente de serra do PWM: contador de CICLOS da MainTask (100 ms): fase 0..19 => periodo de 2 s, deterministico.
# (O ET de um TON como dente de serra foi descartado: o importador PLCopen mapeou a saida errada.)
CYCLES = 20
SAW = [AssignRung("NETWORK 06 - fase do PWM: (fase + 1) MOD 20 ciclos de 100 ms", "PWM_FASE", "(PWM_FASE + 1) MOD 20",
                  {"PWM_FASE": "INT"})]


def _pid(z: str, pv: str, sp: str, reset: str, kp: str, tn: str, y: str, inst: str, title: str) -> FbRung:
    return FbRung(
        title, "PID", inst,
        {"ACTUAL": pv, "SET_POINT": sp, "KP": kp, "TN": tn, "TV": "0.0", "Y_MANUAL": "0.0", "Y_OFFSET": "0.0",
         "Y_MIN": "0.0", "Y_MAX": "100.0", "MANUAL": "FALSE", "RESET": reset},
        # as 3 saidas do Util.PID sao ligadas (o importador mapeia saidas por posicao); LIMITS_ACTIVE/OVERFLOW sao diagnosticos
        {"Y": (y, "REAL"), "LIMITS_ACTIVE": (f"LIM_{z}", "BOOL"), "OVERFLOW": (f"OVF_{z}", "BOOL")},
        declare={sp: "REAL"},
    )


PID_ZONES = []
PWM_ZONES = []
for z in ZONES:
    PID_ZONES.append(_pid(f"Z{z}", f"TT_Z{z}", f"SP_Z{z}", f"NOT EST_AQUEC OR NOT TC_Z{z}_OK", "8.0", "20.0", f"Y_Z{z}",
                          f"PID_Z{z}", f"NETWORK 06 - PID zona {z} (Util.PID; RESET quando sem aquecimento ou termopar ruim)"))
    PWM_ZONES.append(CmpRung(f"NETWORK 06 - PWM_Z{z}: fase < saida do PID (% x 20 ciclos)", "LT", "PWM_FASE", f"Y_Z{z} / 5.0", f"PWM_Z{z}"))

PID_IR = [
    _pid("IR", "TT_SUBSTRATO_C", "SP_IR_C", "NOT IR_HAB", "1.0", "50.0", "Y_IR", "PID_IR",
         "NETWORK 13 - PID do aquecedor IR (RESET quando IR nao habilitado)"),
    CmpRung("NETWORK 13 - PWM_IR: fase < saida do PID (% x 20 ciclos)", "LT", "PWM_FASE", "Y_IR / 5.0", "PWM_IR"),
]

# Rede 12 (escala do inversor): rpm -> palavra do inversor. HIPOTESE: motor 29..57 Hz para 17..34 rpm, base 60 Hz = 16384.
INV_SCALE = [
    AssignRung("NETWORK 12 - INV_REF (unico escritor): rpm -> escala do inversor (hipotese 16384 = 60 Hz)", "INV_REF",
               "REAL_TO_INT(REF_RPM_LIM / 34.0 * 57.0 / 60.0 * 16384.0)", {"INV_REF": "INT", "REF_RPM_LIM": "REAL"}),
]

# Rede 14: conta recargas do funil por BORDA do carregador (nao por nivel)
NET14_COUNT = [
    FbRung("NETWORK 14 - R_TRIG: borda de subida do carregador", "R_TRIG", "RT_FUNIL", {"CLK": "ALIM_FUNIL"}, {"Q": ("FUNIL_PULSO", "BOOL")}),
    FbRung("NETWORK 14 - CTU: recargas do dosador (reset pelo SCADA)", "CTU", "CTU_LOTES",
           {"CU": "FUNIL_PULSO", "RESET": "HMI_RESET_LOTES", "PV": "65535"}, {"CV": ("CONT_LOTES", "WORD")},
           declare={"HMI_RESET_LOTES": "BOOL"}),
]

CONTROL = SAW + PID_ZONES + PWM_ZONES + PID_IR
