"""Testes das redes booleanas contra o avaliador de referencia (mesma estrutura que gera o XML)."""
import xml.etree.ElementTree as ET

from codesys.generator import networks_logic as N
from codesys.generator.ld import scan, pou_xml

SAFE = dict(SEG_OK=True, MOT_SOBRETEMP=True, DISJ_AQUEC=True, BT_DESLIGA=True)  # ativos-baixos em estado normal


def run(env, n=1):
    for _ in range(n):
        env = scan(N.ALL, env)
    return env


def test_each_critical_cause_latches_failure_and_reset_is_blocked_while_active():
    causes = {
        "SEG_OK": False, "MOT_SOBRETEMP": False, "INV_FALHA": True, "PRESSAO_ALTA_17": True, "SOBRETEMP_400": True,
        "TC_FAULT": True, "FALHA_RESF_2M": True, "FALHA_SEM_MAT": True, "FALHA_VENT_10S": True, "FALHA_K1_COL": True,
    }
    assert len(causes) == 10
    for name, bad in causes.items():
        env = run({**SAFE, name: bad})
        assert env["M_CAUSA"] and env["FALHA_GERAL"], name
        env2 = run({**env, "BT_RESET": True})
        assert env2["FALHA_GERAL"], f"reset indevido com causa ativa: {name}"


def test_reset_works_only_after_all_causes_clear():
    env = run({**SAFE, "INV_FALHA": True})
    assert env["FALHA_GERAL"]
    env = run({**env, "INV_FALHA": False, "BT_RESET": True})
    assert not env["M_CAUSA"] and not env["FALHA_GERAL"]


def test_set_priority_over_reset_in_same_scan_with_active_cause():
    env = run({**SAFE, "PRESSAO_ALTA_17": True, "BT_RESET": True})
    assert env["FALHA_GERAL"]


def test_cold_start_with_active_low_inputs_at_zero_is_fault():
    env = run({})  # tudo 0: SEG_OK=0 e MOT_SOBRETEMP=0 => falha (estado seguro na inicializacao)
    assert env["FALHA_GERAL"] and not env["K1_AQUEC"]


def test_k1_needs_permissives_and_drops_on_loss_of_any():
    env = run({**SAFE, "BT_AQUEC": True})
    assert env["EST_AQUEC"] and env["K1_AQUEC"]
    env = run({**env, "BT_AQUEC": False})
    assert env["K1_AQUEC"], "selo deve manter"
    for loss in ("SEG_OK", "DISJ_AQUEC"):
        assert not run({**env, loss: False})["K1_AQUEC"], loss
    for loss in ("FALHA_GERAL", "SOBRETEMP_400", "FALHA_K1_COL"):
        assert not run({**env, loss: True})["K1_AQUEC"], loss


def test_k1_not_started_when_failure_latched():
    env = run({**SAFE, "INV_FALHA": True})
    assert not run({**env, "INV_FALHA": False, "BT_AQUEC": True})["K1_AQUEC"]


def test_cooling_hysteresis_no_chatter():
    env = run({**SAFE})
    assert not env.get("RESF_ON")
    env = run({**env, "RESF_HI": True})
    assert env["RESF_ON"]
    env = run({**env, "RESF_HI": False})          # entre 60 e 80: mantem
    assert env["RESF_ON"]
    env = run({**env, "RESF_LO": True})            # abaixo de 60: desliga
    assert not env["RESF_ON"]
    env = run({**env, "RESF_LO": False})           # entre bandas de novo: continua desligado
    assert not env["RESF_ON"]


def test_screw_manual_latch_and_stop_priority():
    base = {**SAFE, "EST_PRONTO": True}
    env = run({**base, "BT_LIGA": True})
    assert env["EST_EXTRUSAO"]
    env = run({**env, "BT_LIGA": False})
    assert env["EST_EXTRUSAO"], "selo manual"
    env = run({**env, "BT_DESLIGA": False})        # NF aberto = parar, mesmo com BT_LIGA pressionado
    assert not env["EST_EXTRUSAO"]
    assert not run({**env, "BT_DESLIGA": False, "BT_LIGA": True})["EST_EXTRUSAO"]


def test_screw_auto_follows_robot_and_ignores_manual_button():
    base = {**SAFE, "EST_PRONTO": True, "SEL_AUTO": True}
    assert run({**base, "ROBO_CMD_EXTR": True})["EST_EXTRUSAO"]
    assert not run({**base, "BT_LIGA": True})["EST_EXTRUSAO"]
    assert not run({**base, "ROBO_CMD_EXTR": True, "BT_DESLIGA": False})["EST_EXTRUSAO"]


def test_screw_blocked_when_not_ready_or_failed():
    assert not run({**SAFE, "BT_LIGA": True})["EST_EXTRUSAO"]
    env = run({**SAFE, "EST_PRONTO": True, "BT_LIGA": True, "INV_FALHA": True})
    assert not env["EST_EXTRUSAO"]


def test_xml_is_wellformed_with_ld_body_and_single_writer_per_output():
    xml = pou_xml("PLC_PRG", N.variables(), N.ALL)
    root = ET.fromstring(xml)
    ns = {"p": "http://www.plcopen.org/xml/tc6_0200"}
    assert root.find(".//p:LD", ns) is not None
    assert len(root.findall(".//p:leftPowerRail", ns)) == len(N.ALL)
    # escritor unico: cada bobina 'coil' (nao set/reset) aparece uma vez por variavel
    plain = [c.find("p:variable", ns).text for c in root.findall(".//p:coil", ns) if c.get("storage") == "none"]
    assert len(plain) == len(set(plain))
    # EST_EXTRUSAO e EST_AQUEC/K1/RESF/M_CAUSA: uma unica bobina normal cada
    for v in ("EST_AQUEC", "K1_AQUEC", "RESF_ON", "M_CAUSA", "EST_EXTRUSAO"):
        assert plain.count(v) == 1, v
