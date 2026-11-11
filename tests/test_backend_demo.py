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
    assert all(d == 0.0 for d in eng.duty) and eng.duty_ir == 0.0  # PID agora vive no programa (Util.PID, RESET sem aquecimento)


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


def test_latched_cause_is_remembered_after_it_clears_until_reset():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 1400, dt=0.5)
    eng.request("BT_LIGA"); run(eng, 20, dt=0.5)
    eng.inject("pressure_high", True)
    run(eng, 20, dt=0.5)
    s = eng.snapshot()
    assert s["state"] == "FALHA_TRAVADA" and "PRESSAO_ALTA_17" in s["latched_causes"]
    assert "PRESSAO_ALTA_17" not in s["causes"], "a causa ativa ja normalizou"
    eng.inject("pressure_high", False)
    eng.request("BT_RESET"); run(eng, 3, dt=0.5)
    s = eng.snapshot()
    assert s["state"] != "FALHA_TRAVADA" and s["latched_causes"] == []


def test_stop_is_a_one_second_pulse_and_does_not_latch_the_stop_button():
    eng = DemoEngine()
    start_heating(eng)
    run(eng, 1400, dt=0.5)
    eng.request("BT_LIGA"); run(eng, 5, dt=0.5)
    assert eng.snapshot()["state"] == "EXTRUSAO"
    eng.request("STOP"); run(eng, 3, dt=0.5)
    assert eng.snapshot()["state"] == "PRONTO", "parou"
    eng.request("BT_LIGA"); run(eng, 3, dt=0.5)
    assert eng.snapshot()["state"] == "EXTRUSAO", "STOP nao pode ficar preso e bloquear nova partida"


# ---------------------------------------------------------------- modo apresentacao (velocidade do relogio simulado)
def test_step_size_keeps_original_up_to_30x_and_grows_above():
    from backend.app import step_dt
    assert step_dt(1) == 0.1 and abs(step_dt(30) - 0.1) < 1e-9
    assert abs(step_dt(90) - 0.3) < 1e-9 and abs(step_dt(150) - 0.5) < 1e-9


def test_clock_accumulator_advances_exactly_scale_times_wall_time_without_drift():
    from backend.app import advance
    for scale in (1, 5, 30, 90, 150):
        debt, sim = 0.0, 0.0
        for _ in range(500):                      # 500 iteracoes de 20 ms reais = 10 s reais
            n, dt, debt = advance(debt, 0.02, scale)
            sim += n * dt
        assert abs((sim + debt) - scale * 10.0) < 1e-6, scale     # nada se perde
        assert abs(sim - scale * 10.0) <= step_dt_of(scale), scale  # sobra no maximo um passo


def step_dt_of(scale):
    from backend.app import step_dt
    return step_dt(scale) + 1e-9


def test_clock_accumulator_drops_backlog_when_machine_is_too_slow():
    from backend.app import advance, MAX_STEPS_PER_TICK
    n, dt, debt = advance(0.0, 0.5, 150)       # 75 s simulados devidos de uma vez: >> 30 passos de 0,5 s
    assert n == MAX_STEPS_PER_TICK and debt <= dt


def test_speed_endpoint_demo_accepts_in_range_and_rejects_outside():
    with TestClient(create_app(DemoEngine(), autostart=False)) as c:
        assert c.get("/api/state").json()["time_scale"] == 1.0
        r = c.post("/api/demo/speed", json={"scale": 90}).json()
        assert r["accepted"] and r["time_scale"] == 90.0 and c.get("/api/state").json()["time_scale"] == 90.0
        assert not c.post("/api/demo/speed", json={"scale": 0.5}).json()["accepted"]
        assert not c.post("/api/demo/speed", json={"scale": 1000}).json()["accepted"]
        assert c.get("/api/state").json()["time_scale"] == 90.0, "valor recusado nao altera a velocidade"


def test_presentation_speed_does_not_change_the_process_outcome():
    """Mesma partida em 1x (passos de 0,1 s) e com passos de 0,3 s: PRONTO e extrusao chegam ao mesmo estado fisico aproximado."""
    def go(dt):
        eng = DemoEngine()
        eng.request("BT_AQUEC")
        t = 0.0
        while t < 1200 and eng.snapshot()["state"] != "PRONTO":
            eng.step(dt)
            t += dt
        return eng, t
    e1, t1 = go(0.1)
    e3, t3 = go(0.3)
    assert e1.snapshot()["state"] == "PRONTO" == e3.snapshot()["state"]
    assert abs(t1 - t3) < 15, (t1, t3)      # encharque de 900 s: diferenca de poucos segundos
    assert all(abs(e1.snapshot()["temps"][z] - e3.snapshot()["temps"][z]) < 5 for z in ("Z1", "Z2", "Z3", "Z4", "Z5"))
