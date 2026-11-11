"""Redes 02, 03, 07, 08, 11 e integracao com 04/05/10 contra o avaliador de referencia (com tempo)."""
import xml.etree.ElementTree as ET

from codesys.generator import program as PRG
from codesys.generator.ld import scan

NORMAL = dict(SECADOR_OK=True, INV_PRONTO=True, SEG_OK=True, MOT_SOBRETEMP=True, DISJ_AQUEC=True, BT_DESLIGA=True, FUNIL_BAIXO=True, VENT_OK=True,
              **{f"TC_Z{z}_OK": True for z in range(1, 6)}, **{f"TT_Z{z}": 350.0 for z in range(1, 6)}, TT_RESF=40.0)


def run(env, secs=0.0, dt=0.5):
    env = scan(PRG.CORE, env, 0.0)
    t = 0.0
    while t < secs:
        env = scan(PRG.CORE, env, dt)
        t += dt
    return env


def test_over_temperature_thresholds_390_and_400():
    env = run({**NORMAL, "TT_Z3": 391.0})
    assert env["SOBRETEMP_390_Z3"] and not env["SOBRETEMP_400"] and not env.get("FALHA_GERAL")
    env = run({**NORMAL, "TT_Z3": 401.0})
    assert env["SOBRETEMP_400"] and env["FALHA_GERAL"] and not env["K1_AQUEC"]


def test_open_thermocouple_is_fault_per_zone():
    for z in range(1, 6):
        env = run({**NORMAL, f"TC_Z{z}_OK": False})
        assert env["TC_FAULT"] and env["FALHA_GERAL"], z


def test_cooling_chamber_fault_only_after_two_minutes():
    env = run({**NORMAL, "TT_RESF": 101.0}, 119.0)
    assert not env["FALHA_RESF_2M"] and not env.get("FALHA_GERAL")
    env = run({**env}, 2.0)
    assert env["FALHA_RESF_2M"] and env["FALHA_GERAL"]
    # voltou a baixo antes de 2 min: zera o temporizador
    env = run({**NORMAL, "TT_RESF": 101.0}, 100.0)
    env = run({**env, "TT_RESF": 90.0}, 1.0)
    env = run({**env, "TT_RESF": 101.0}, 100.0)
    assert not env["FALHA_RESF_2M"]


def test_hysteresis_flags_and_latch_via_networks():
    env = run({**NORMAL, "TT_RESF": 85.0})
    assert env["RESF_ON"]
    env = run({**env, "TT_RESF": 70.0})
    assert env["RESF_ON"]
    env = run({**env, "TT_RESF": 55.0})
    assert not env["RESF_ON"]


def test_no_material_fault_after_60s_only_when_extruding_and_loader_on():
    base = {**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True, "FUNIL_BAIXO": False, "ALIM_FUNIL": True}
    env = run(base, 59.0)
    assert not env["FALHA_SEM_MAT"]
    env = run(env, 2.0)
    # a causa some sozinha quando a falha trava a rosca: por isso FALHA_GERAL e travada
    assert env["FALHA_GERAL"] and not env["EST_EXTRUSAO"]


def test_vent_fault_after_10s_and_k1_stuck_after_1s():
    env = run({**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True, "VENT_OK": False}, 9.0)
    assert not env["FALHA_VENT_10S"]
    env = run(env, 2.0)   # a causa some quando a falha trava a rosca: o que fica e a falha travada
    assert env["FALHA_GERAL"] and not env["EST_EXTRUSAO"]
    env = run({**NORMAL, "K1_CONF": True, "K1_AQUEC": False}, 0.5)
    assert not env["FALHA_K1_COL"]
    assert run(env, 1.0)["FALHA_K1_COL"]


def test_soak_15_minutes_continuous_and_restarts_if_a_zone_drops():
    env = run(NORMAL, 899.0)
    assert env["EST_ENCHARQUE"] and not env["ENCH_OK"]
    env = run(env, 2.0)
    assert env["ENCH_OK"]
    env = run({**NORMAL}, 800.0)
    env = run({**env, "TT_Z2": 329.0}, 1.0)          # uma zona cai: reinicia
    assert not env["EST_ENCHARQUE"] and not env["ENCH_OK"]
    env = run({**env, "TT_Z2": 350.0}, 899.0)
    assert not env["ENCH_OK"], "contagem deve recomecar do zero"


def test_ventilation_runs_with_screw_and_five_minutes_after_stop():
    base = {**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True}
    env = run(base, 1.0)
    assert env["EST_EXTRUSAO"] and env["VENT_MOTOR"]
    env = run({**env, "BT_LIGA": False, "BT_DESLIGA": False}, 1.0)   # STOP (NF aberto)
    assert not env["EST_EXTRUSAO"] and env["VENT_MOTOR"], "pos-ventilacao ativa"
    env = run({**env, "BT_DESLIGA": True}, 298.0)
    assert env["VENT_MOTOR"]
    env = run(env, 3.0)
    assert not env["VENT_MOTOR"], "apos 5 min desliga"


def test_restart_during_post_ventilation_keeps_fan_on():
    env = run({**NORMAL, "__ton_T_ENCHARQUE": 900.0, "BT_LIGA": True}, 1.0)
    env = run({**env, "BT_LIGA": False, "BT_DESLIGA": False}, 100.0)
    env = run({**env, "BT_DESLIGA": True, "BT_LIGA": True}, 400.0)
    assert env["EST_EXTRUSAO"] and env["VENT_MOTOR"]


def test_single_writer_per_output_across_full_program():
    root = ET.fromstring(PRG.xml())
    ns = {"p": "http://www.plcopen.org/xml/tc6_0200"}
    plain = [c.find("p:variable", ns).text for c in root.findall(".//p:coil", ns) if c.get("storage") == "none"]
    dups = {v for v in plain if plain.count(v) > 1}
    assert not dups, dups


def test_xml_has_blocks_and_derived_ton_instances():
    root = ET.fromstring(PRG.xml())
    ns = {"p": "http://www.plcopen.org/xml/tc6_0200"}
    types = {b.get("typeName") for b in root.findall(".//p:block", ns)}
    assert types == {"TON", "Util.PID", "CTU", "R_TRIG"}  # comparacoes sao contatos com expressao
    assert len(root.findall(".//p:derived[@name='TON']", ns)) == 6
    assert len(root.findall(".//p:derived[@name='Util.PID']", ns)) == 6
