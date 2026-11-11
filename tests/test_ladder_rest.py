"""Redes 01, 02 (escala), 06, 09, 12, 13 e 15 + XML completo."""
import xml.etree.ElementTree as ET

from codesys.generator import program as PRG
from codesys.generator.ld import scan

NORMAL = dict(EST_AQUEC=True, SEG_OK=True, MOT_SOBRETEMP=True, DISJ_AQUEC=True, BT_DESLIGA=True, FUNIL_BAIXO=True, VENT_OK=True,
              SECADOR_OK=True, INV_PRONTO=True, K1_CONF=True,
              **{f"TT_Z{z}_RAW": 3500 for z in range(1, 6)}, TT_ZSR_RAW=0, TT_ZSR=300.0, TT_RESF=40.0,
              PT_FUNDIDO_RAW=0, TT_SUBSTRATO_RAW=0, SP_RPM_OPERADOR=25.0)


def cycle(env, n=1, dt=0.1):
    for _ in range(n):
        env = scan(PRG.NOPID, env, dt)
    return env


def test_analog_scaling_pressure_and_substrate_and_tc():
    env = cycle({**NORMAL, "PT_FUNDIDO_RAW": 27648, "TT_SUBSTRATO_RAW": 13824})
    assert abs(env["PT_FUNDIDO_MPA"] - 35.0) < 1e-9 and abs(env["TT_SUBSTRATO_C"] - 250.0) < 1e-9
    env = cycle({**NORMAL, "TT_Z2_RAW": 3567})
    assert abs(env["TT_Z2"] - 356.7) < 1e-9
    assert not env["TC_FAULT"]


def test_open_tc_32767_is_detected_and_blocks_ssr():
    env = cycle({**NORMAL, "TT_Z4_RAW": 32767, "PWM_Z4": True, "EST_AQUEC": True})
    assert env["TC_Z4_ABERTO"] and env["TC_FAULT"] and env["FALHA_GERAL"] and not env["SSR_Z4"]


def test_ssr_gating_requires_all_conditions_and_pid_output_not_frozen():
    env = cycle({**NORMAL, "BT_AQUEC": True, "PWM_Z1": True}, 3)
    assert env["K1_AQUEC"] and env["SSR_Z1"]
    assert not cycle({**env, "PWM_Z1": False})["SSR_Z1"]
    assert not cycle({**env, "K1_CONF": False}, 3)["SSR_Z1"]
    hot = cycle({**env, "TT_Z1_RAW": 3910})
    assert hot["SOBRETEMP_390_Z1"] and not hot["SSR_Z1"]
    assert hot["SSR_Z1"] is False and not cycle({**env, "SEG_OK": False}, 2)["SSR_Z1"]


def test_ready_needs_soak_dryer_inverter_and_no_latched_fault():
    base = {**NORMAL, "__ton_T_ENCHARQUE": 900.0, **{f"TT_Z{z}_RAW": 3500 for z in range(1, 6)}}
    env = cycle(base)
    assert env["EST_PRONTO"] and env["ROBO_EXT_PRONTA"]
    for off in ("SECADOR_OK", "INV_PRONTO"):
        assert not cycle({**base, off: False})["EST_PRONTO"], off
    assert not cycle({**base, "INV_FALHA": True}, 2)["EST_PRONTO"]


def test_pressure_policy_d5_and_inverter_reference_single_writer():
    env = cycle({**NORMAL, "PT_FUNDIDO_RAW": int(16.0 / 35 * 27648)})
    assert not env["ALM_PRESSAO_16_5"] and env["REF_RPM_LIM"] == 25.0
    env = cycle({**NORMAL, "PT_FUNDIDO_RAW": int(16.6 / 35 * 27648) + 1, "SP_RPM_OPERADOR": 30.0})
    assert env["ALM_PRESSAO_16_5"] and abs(env["REF_RPM_LIM"] - 27.0) < 1e-9 and not env["PRESSAO_ALTA_17"]
    env = cycle({**NORMAL, "PT_FUNDIDO_RAW": int(16.6 / 35 * 27648) + 1, "SP_RPM_OPERADOR": 18.0})
    assert env["REF_RPM_LIM"] == 17.0, "piso 17 rpm (limitacao documentada)"
    assert cycle({**NORMAL, "SP_RPM_OPERADOR": 99.0})["REF_RPM_LIM"] == 34.0
    assert cycle({**NORMAL, "SP_RPM_OPERADOR": 3.0})["REF_RPM_LIM"] == 17.0


def test_pressure_17_trips_latched_failure():
    env = cycle({**NORMAL, "PT_FUNDIDO_RAW": int(17.1 / 35 * 27648)}, 2)
    assert env["PRESSAO_ALTA_17"] and env["FALHA_GERAL"] and env["LUZ_VERM_SIRENE"]


def test_ir_enable_requires_screw_robot_range_and_no_fault():
    base = {**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True, "ROBO_EM_MOV": True, "TT_SUBSTRATO_RAW": 5530, "PWM_IR": True}
    env = cycle(base, 3)
    assert env["EST_EXTRUSAO"] and env["IR_HAB"] and env["SSR_IR"]
    assert not cycle({**env, "ROBO_EM_MOV": False})["SSR_IR"], "robo parado desliga IR"
    assert not cycle({**env, "TT_SUBSTRATO_RAW": 27648})["SSR_IR"], "pirometro fora da faixa"
    assert not cycle({**env, "BT_DESLIGA": False}, 2)["SSR_IR"]


def test_tower_light_semantics_warning_vs_latched_fault():
    heating = cycle({**NORMAL, "BT_AQUEC": True}, 2)
    assert heating["LUZ_AMARELA"] and not heating["LUZ_VERDE"] and not heating["LUZ_VERM_SIRENE"]
    cold = cycle({**NORMAL, "TT_ZSR": 200.0})
    assert cold["ALM_ZSR_BAIXA"] and cold["LUZ_VERM_SIRENE"] and not cold.get("FALHA_GERAL")
    fault = cycle({**NORMAL, "INV_FALHA": True})
    assert fault["LUZ_VERM_SIRENE"] and fault["FALHA_GERAL"]


def test_full_xml_wellformed_and_assignments_present():
    root = ET.fromstring(PRG.xml())
    ns = {"p": "http://www.plcopen.org/xml/tc6_0200"}
    outs = [o.find("p:expression", ns).text for o in root.findall(".//p:outVariable", ns)]
    assert "REF_RPM_LIM" in outs and "PT_FUNDIDO_MPA" in outs
    assert len(outs) == len(set(outs)), "escritor unico tambem para atribuicoes"


def test_tower_alignment_with_reference_plates():
    ready = cycle({**NORMAL, "__ton_T_ENCHARQUE": 900.0}, 2)
    assert ready["EST_PRONTO"] and not ready["LUZ_AMARELA"], "amarela apaga quando pronto (Prancha 4)"
    run_ = cycle({**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True}, 3)
    assert run_["LUZ_VERDE"] and not run_["LUZ_AMARELA"]
    hot = cycle({**NORMAL, **{"TT_Z2_RAW": 3910}}, 2)
    assert hot["SOBRETEMP_390_Z2"] and hot["LUZ_VERM_SIRENE"], "pre-alarme de 390 aciona a sirene (aviso, sem travar falha)"
    assert not hot.get("FALHA_GERAL")
    cold_zsr = {**NORMAL, "TT_ZSR": 200.0}
    assert cycle({**cold_zsr, "EST_AQUEC": False}, 2)["ALM_ZSR_BAIXA"] is False, "alarme do trecho frio so durante o encharque"
    assert cycle(cold_zsr, 2)["ALM_ZSR_BAIXA"] is True


def test_soak_requires_heating_on():
    env = cycle({**NORMAL, "EST_AQUEC": False, "SEG_OK": True}, 3)
    assert not env["EST_ENCHARQUE"] and not env.get("ENCH_OK"), "sem aquecimento nao ha encharque nem PRONTO"
