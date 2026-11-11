"""Testes do motor e da API em modo DEMO (nada aqui fala com CLP)."""
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.engine import DemoEngine


def run(eng, secs, dt=0.1):
    for _ in range(int(secs / dt)):
        eng.step(dt)


def start_heating(eng):
    eng.request("BT_AQUEC")
    run(eng, 1.0)


def test_cold_start_is_safe_state_k1_open():
    eng = DemoEngine()
    run(eng, 2)
    s = eng.snapshot()
    assert s["state"] == "DESLIGADO" and not s["flags"]["K1_AQUEC"] and s["mode"] == "DEMO" and s["plc_connected"] is False


def test_button_is_only_a_request_state_changes_only_via_program():
    eng = DemoEngine()
    ok, _ = eng.request("BT_AQUEC")
    assert ok and not eng.snapshot()["flags"]["K1_AQUEC"], "ainda nao confirmado"
    run(eng, 1.0)
    assert eng.snapshot()["flags"]["K1_AQUEC"] and eng.snapshot()["state"] == "AQUECIMENTO"


def test_heating_reaches_setpoint_with_pid_and_ssr_gated_by_program():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 900, dt=0.5)
    t = eng.snapshot()["temps"]
    for z, sp in zip(("Z1", "Z2", "Z3", "Z4", "Z5"), eng.sp_z):
        assert abs(t[z] - sp) < 6, (z, t[z], sp)
    assert not eng.snapshot()["flags"]["FALHA_GERAL"]


def test_estop_logic_test_trips_latched_failure_and_reset_blocked_until_cleared():
    eng = DemoEngine()
    start_heating(eng)
    eng.inject("estop_test", True)
    run(eng, 1.0)
    s = eng.snapshot()
    assert s["state"] == "FALHA_TRAVADA" and not s["flags"]["K1_AQUEC"] and "SEG_OK" in s["causes"]
    eng.request("BT_RESET"); run(eng, 1.0)
    assert eng.snapshot()["state"] == "FALHA_TRAVADA", "reset nao pode limpar com causa ativa"
    eng.inject("estop_test", False); run(eng, 0.5)
    eng.request("BT_RESET"); run(eng, 1.0)
    assert eng.snapshot()["state"] != "FALHA_TRAVADA"


def test_thermocouple_open_fault_stops_and_latches():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 30)
    eng.inject("tc_open_3", True)
    run(eng, 1.0)
    s = eng.snapshot()
    assert "TC_FAULT" in s["causes"] and s["state"] == "FALHA_TRAVADA"


def test_setpoint_validation_rejects_out_of_range():
    eng = DemoEngine()
    assert eng.set_setpoint("Z1", 300)[0] is False
    assert eng.set_setpoint("Z5", 344)[0] is False
    assert eng.set_setpoint("RPM", 40)[0] is False
    assert eng.set_setpoint("Z1", 335)[0] is True and eng.sp_z[0] == 335


def test_pid_is_reset_when_disabled_no_windup_and_ssr_zero():
    eng = DemoEngine()
    run(eng, 5)
    assert eng.integral == [0.0] * 5 and all(d == 0.0 for d in eng.duty)


def test_full_extrusion_after_soak_with_accelerated_clock():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 1400, dt=0.5)        # aquece + encharque de 15 min (tempo simulado, o TON do programa conta dt)
    s = eng.snapshot()
    assert s["state"] == "PRONTO" and s["flags"]["ROBO_EXT_PRONTA"], s["state"]
    eng.request("BT_LIGA"); run(eng, 30, dt=0.5)
    s = eng.snapshot()
    assert s["state"] == "EXTRUSAO" and s["rpm_real"] > 20 and s["flags"]["VENT_MOTOR"] and s["flags"]["LUZ_VERDE"]
    assert s["pressure_mpa"] < 17


def test_pressure_fault_injection_trips_17_mpa_and_stops_screw():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 1400, dt=0.5)
    eng.request("BT_LIGA"); run(eng, 20, dt=0.5)
    eng.inject("pressure_high", True)
    run(eng, 20, dt=0.5)
    s = eng.snapshot()
    # a causa (pressao) some ao parar a rosca; a falha permanece travada ate o reset condicionado
    assert s["state"] == "FALHA_TRAVADA" and s["rpm_real"] < 1 and not s["flags"]["EST_EXTRUSAO"]


def test_api_contract_and_demo_labeling():
    client = TestClient(create_app(DemoEngine(), autostart=False))
    h = client.get("/api/health").json()
    assert h["mode"] == "DEMO" and h["plc_connected"] is False
    r = client.post("/api/command", json={"name": "BT_AQUEC"}).json()
    assert r["accepted"] and r["confirmed"] is False
    assert client.post("/api/command", json={"name": "ACIONA_MOTOR"}).json()["accepted"] is False
    assert client.post("/api/setpoint", json={"key": "Z1", "value": 999}).json()["accepted"] is False
    assert client.post("/api/demo/fault", json={"fault": "pressure_high"}).json()["mode"] == "DEMO"
    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_json()
    assert msg["mode"] == "DEMO" and "timestamp" in msg
