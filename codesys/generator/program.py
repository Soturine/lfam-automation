"""Programa LFAM completo (parcial): todas as redes ja implementadas, na ORDEM DE EXECUCAO do ciclo."""
from . import networks_logic as L
from . import networks_timed as T
from .ld import variables_of, pou_xml

# 02/03/07-flags/08 produzem flags que 04/05/10/11 consomem: ficam antes.
RUNGS = (
    T.NET02 + T.NET03 + T.NET07_FLAGS
    + [L.NET04_M_CAUSA, L.NET04_SET, L.NET04_RESET, L.NET05_AQUEC, L.NET05_K1, L.NET07_RESF]
    + T.NET08
    + [L.NET10_ROSCA]
    + T.NET11
)


def variables() -> dict:
    return variables_of(RUNGS)


def xml(name: str = "PLC_PRG") -> str:
    return pou_xml(name, variables(), RUNGS)
