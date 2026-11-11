"""Programa LFAM (parcial): redes implementadas, na ORDEM DE EXECUCAO do ciclo.
Ainda ausentes: PID real (FB em tarefa propria), rede 14 (CTU) e ir/vir de dados do inversor."""
from . import networks_logic as L
from . import networks_timed as T
from . import networks_rest as R
from . import networks_pid as PD
from .ld import variables_of, pou_xml

# CORE: logica de controle que consome sinais ja escalonados (TT_Zn em degC, PT em MPa)
CORE = (
    T.NET02 + T.NET03 + T.NET07_FLAGS
    + R.NET12[:2]
    + [L.NET04_M_CAUSA] + L.NET04_FIRST + [L.NET04_SET, L.NET04_RESET, L.NET05_AQUEC, L.NET05_K1, L.NET07_RESF]
    + T.NET08
    + R.NET09
    + [L.NET10_ROSCA]
    + R.NET10B
    + R.NET14A
    + T.NET11
    + R.NET12[2:]
    + PD.INV_SCALE
    + R.NET06
    + R.NET13
    + R.NET15
    + PD.NET14_COUNT
)

# Escalonamento dos sinais brutos; produz TT_Zn/PT/TT_SUBSTRATO e TC_Zn_ABERTO antes do CORE.
SCALING = R.NET01
# TC_Zn_OK = NOT TC_Zn_ABERTO (qualidade), derivado logo apos o escalonamento
from .ld import Rung, C, Coil  # noqa: E402

TC_OK = [Rung(f"NETWORK 02 - TC_Z{z}_OK = nao aberto", C(f"TC_Z{z}_ABERTO", neg=True), [Coil(f"TC_Z{z}_OK")]) for z in range(1, 6)]

# PID/PWM antes do CORE: usam o estado do ciclo anterior (EST_AQUEC, IR_HAB); SSR_x so liga nas redes 06/13 (gate)
RUNGS = SCALING + TC_OK + PD.CONTROL + CORE
# Mesmo programa sem PID/PWM: usado por testes que injetam PWM_* para isolar as redes de gate (06/13)
NOPID = SCALING + TC_OK + CORE


def variables() -> dict:
    return variables_of(RUNGS)


def xml(name: str = "PLC_PRG") -> str:
    return pou_xml(name, variables(), RUNGS)
