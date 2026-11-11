"""Testes do cliente OPC UA contra um servidor de TESTE (duble local, apenas nestes testes).

Este servidor NAO e o CLP e nunca e usado pelos modos DEMO/PLC da aplicacao: ele so exercita o codigo do cliente
(mapeamento de variaveis, heartbeat, perda e reconexao). A integracao real exige o Control Win (docs/evidence/CP3_*)."""
import time

import pytest
from asyncua import ua
from asyncua.sync import Server

from backend.engine import DemoEngine
from backend.transport import HEARTBEAT, OpcUaTransport, PlcLinkError, STALE_S, _SKIP_TYPES
from codesys.generator import program as PRG

PORT = 48410
URL = f"opc.tcp://127.0.0.1:{PORT}"
VT = {"BOOL": ua.VariantType.Boolean, "INT": ua.VariantType.Int16, "WORD": ua.VariantType.UInt16, "REAL": ua.VariantType.Float}
INIT = {"BOOL": False, "INT": 0, "WORD": 0, "REAL": 0.0}


def start_server():
    srv = Server()
    srv.set_endpoint(URL)
    idx = srv.register_namespace("urn:lfam:test-double")
    node = srv.nodes.objects
    for name in ("DeviceSet", "TestDevice", "Resources", "Application"):
        node = node.add_object(idx, name)
    prg = node.add_object(idx, "PLC_PRG")
    nodes = {}
    for name, t in PRG.variables().items():
        if t in _SKIP_TYPES:
            continue
        v = prg.add_variable(idx, name, INIT[t], varianttype=VT[t])
        v.set_writable()
        nodes[name] = v
    srv.start()
    return srv, nodes


@pytest.fixture()
def server():
    srv, nodes = start_server()
    yield srv, nodes
    try:
        srv.stop()
    except Exception:  # noqa: BLE001
        pass


def test_resolves_program_and_roundtrips_typed_values(server):
    _srv, nodes = server
    t = OpcUaTransport(URL)
    t.connect()
    env = t.cycle({"BT_AQUEC": True, "SP_Z1": 345.5, "TT_Z1_RAW": 3400, "SEG_OK": True}, 0.1)
    assert env["BT_AQUEC"] is True and abs(env["SP_Z1"] - 345.5) < 1e-3 and env["TT_Z1_RAW"] == 3400
    assert nodes["BT_AQUEC"].get_value() is True           # o servidor recebeu de fato
    t.close()


def test_never_writes_outputs_computed_by_the_program(server):
    _srv, nodes = server
    t = OpcUaTransport(URL)
    t.connect()
    t.cycle({"K1_AQUEC": True, "SSR_Z1": True, "EST_EXTRUSAO": True, "INV_REF": 999}, 0.1)   # nao esta na lista de escrita
    assert nodes["K1_AQUEC"].get_value() is False and nodes["SSR_Z1"].get_value() is False and nodes["INV_REF"].get_value() == 0
    t.close()


def test_heartbeat_staleness_marks_link_unhealthy(server):
    _srv, nodes = server
    now = [0.0]
    t = OpcUaTransport(URL, clock=lambda: now[0])
    t.connect()
    nodes[HEARTBEAT].set_value(ua.Variant(1, ua.VariantType.Int16))
    t.cycle({}, 0.1)
    assert t.healthy
    now[0] += STALE_S + 0.5                                  # CLP parado: heartbeat nao muda
    t.cycle({}, 0.1)
    assert not t.healthy
    nodes[HEARTBEAT].set_value(ua.Variant(2, ua.VariantType.Int16))
    t.cycle({}, 0.1)
    assert t.healthy
    t.close()


def test_missing_variables_are_reported_clearly():
    srv = Server()
    srv.set_endpoint(URL)
    idx = srv.register_namespace("urn:lfam:test-double")
    prg = srv.nodes.objects.add_object(idx, "PLC_PRG")
    prg.add_variable(idx, "BT_AQUEC", False).set_writable()
    srv.start()
    try:
        t = OpcUaTransport(URL)
        with pytest.raises(PlcLinkError, match="nao publicadas"):
            t.connect()
    finally:
        srv.stop()


def test_connection_loss_raises_and_engine_drops_pulses_and_refuses_commands():
    srv, _ = start_server()
    t = OpcUaTransport(URL, timeout=1.0)
    t.connect()
    eng = DemoEngine(transport=t)
    eng.step(0.1)
    ok, _ = eng.request("BT_AQUEC")
    assert ok and eng.pulses
    srv.stop()                                                # enlace cai com o pulso pendente
    time.sleep(0.3)
    eng.step(0.1)
    assert eng.link_error and not eng.pulses, "pulso pendente deve ser descartado, nunca reenviado"
    assert eng.snapshot()["plc_connected"] is False
    ok, msg = eng.request("BT_LIGA")
    assert not ok and "sem comunicacao" in msg


def test_reconnect_after_server_restart():
    srv, _ = start_server()
    t = OpcUaTransport(URL, timeout=1.0)
    t.connect()
    srv.stop()
    with pytest.raises(PlcLinkError):
        t.cycle({}, 0.1)
    assert not t.connected
    srv2, _ = start_server()
    try:
        t.connect()
        assert t.connected and t.cycle({"SEG_OK": True}, 0.1)["SEG_OK"] is True
    finally:
        t.close()
        srv2.stop()


def test_credentials_are_not_logged(server, caplog):
    import logging

    caplog.set_level(logging.DEBUG)
    t = OpcUaTransport(URL, username="admin", password="segredo-que-nao-pode-vazar")
    try:
        t.connect()
    except PlcLinkError:
        pass                                                  # servidor de teste e anonimo; so importa o que foi logado
    assert "segredo-que-nao-pode-vazar" not in caplog.text
    t.close()
