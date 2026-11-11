"""Cenarios de ENSAIO ONLINE (CP4): backend em modo PLC -> OPC UA -> Ladder no CODESYS Control Win, em TEMPO REAL (~1h30).

Fala so com a API HTTP do backend (nao conhece senha). As falhas sao injetadas na planta SIMULADA do backend (sensor/atuador),
nunca no programa. Cada verificacao registra PASS/FAIL com valores observados em docs/evidence/CP4_ONLINE_SCENARIOS.txt.
Uso: python tools/cp4_scenarios.py [http://127.0.0.1:8000]
"""
import json
import sys
import time
import traceback
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
OUT = Path("docs/evidence/CP4_ONLINE_SCENARIOS.txt")
if len(sys.argv) > 2:
    OUT = Path("docs/evidence/CP4_ONLINE_SCENARIOS_COMPLEMENTO.txt")
TRACE = Path("work/cp4_trace.json")
FAULTS = ["tc_open_1", "tc_open_2", "tc_open_3", "tc_open_4", "tc_open_5", "pressure_high", "pressure_warn", "pressure_stuck", "funil_empty",
          "vent_fail", "inv_fault", "k1_stuck", "estop_test", "disj_open"]
RESULTS = []
T0 = time.time()


def log(msg):
    line = f"[{time.time() - T0:7.1f}s] {msg}"
    print(line, flush=True)
    with OUT.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=8) as r:
        return json.load(r)


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.load(r)


class Fail(Exception):
    pass


def st():
    return get("/api/state")


def wait(pred, secs, what, poll=0.25, hook=None):
    t0 = time.time()
    while time.time() - t0 < secs:
        s = st()
        if hook:
            hook(s)
        if s["plc_connected"] is False:
            raise Fail(f"enlace PLC perdido enquanto aguardava: {what}")
        if pred(s):
            return s, time.time() - t0
        time.sleep(poll)
    s = st()
    raise Fail(f"TIMEOUT {secs}s: {what} (estado={s['state']}, flags ativos={[k for k, v in s['flags'].items() if v]}, causas={s['causes']})")


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    log(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")
    return bool(cond)


def cmd(n):
    post("/api/command", {"name": n})


def fault(f, on=True):
    post("/api/demo/fault", {"fault": f, "on": on})


def clear_faults():
    for f in FAULTS:
        fault(f, False)


def idle():
    """Baseline: sem falhas injetadas, aquecimento desligado, falha reconhecida."""
    clear_faults()
    s = st()
    if s["state"] == "EXTRUSAO":
        cmd("STOP")      # BT_DESLIGA desliga a EXTRUSAO (tags.csv); o aquecimento segue
        wait(lambda s: s["state"] != "EXTRUSAO", 20, "parada da extrusao")
    if st()["flags"]["EST_AQUEC"]:
        fault("disj_open")   # o aquecimento so desliga por DISJ_AQUEC (disjuntor) ou por falha
        wait(lambda s: not s["flags"]["EST_AQUEC"], 20, "aquecimento desligado pelo disjuntor")
        fault("disj_open", False)
    for _ in range(4):
        s = st()
        if s["state"] != "FALHA_TRAVADA":
            break
        time.sleep(3)  # deixa causas simuladas sumirem
        cmd("BT_RESET")
        time.sleep(2.5)
    wait(lambda s: s["state"] == "DESLIGADO", 20, "estado DESLIGADO")


def expect_fault(name, cause, secs):
    s, dt = wait(lambda s: s["state"] == "FALHA_TRAVADA", secs, f"falha travada por {name}")
    check(f"{name}: falha travada pelo Ladder (causa {cause})", cause in s["latched_causes"], f"em {dt:.1f}s; latched={s['latched_causes']}")
    check(f"{name}: K1 aberto, rosca parada, sirene",
          (not s["flags"]["K1_AQUEC"]) and (not s["flags"]["INV_RUN"]) and s["flags"]["LUZ_VERM_SIRENE"],
          f"K1={s['flags']['K1_AQUEC']} INV_RUN={s['flags']['INV_RUN']} sirene={s['flags']['LUZ_VERM_SIRENE']}")
    return s, dt


def reset_refused_then_ok(name, injected):
    cmd("BT_RESET")
    time.sleep(3.0)
    s = st()
    check(f"{name}: reset RECUSADO com a causa ainda presente", s["state"] == "FALHA_TRAVADA", f"estado={s['state']}")
    fault(injected, False)
    time.sleep(3.0)
    for _ in range(3):
        cmd("BT_RESET")
        time.sleep(2.5)
        if st()["state"] != "FALHA_TRAVADA":
            break
    check(f"{name}: reset ACEITO depois que a causa sumiu", st()["state"] == "DESLIGADO", f"estado={st()['state']}")


def stays_latched_then_reset(name, injected):
    """Causas ligadas a extrusao (ventilador, funil, pressao) somem sozinhas quando a rosca para: a FALHA deve continuar TRAVADA
    ate o reset do operador (primeira causa preservada), e so entao sair."""
    fault(injected, False)
    time.sleep(5.0)
    s = st()
    check(f"{name}: falha SEGUE travada depois que a causa sumiu (ate o reset)", s["state"] == "FALHA_TRAVADA" and not s["flags"]["M_CAUSA"],
          f"estado={s['state']} M_CAUSA={s['flags']['M_CAUSA']} latched={s['latched_causes']}")
    cmd("BT_RESET")
    time.sleep(2.5)
    check(f"{name}: reset do operador aceito (causa extinta)", st()["state"] == "DESLIGADO", f"estado={st()['state']}")


class Heat:
    """Aquece ate PRONTO medindo sobressinal e o tempo de encharque."""

    def __init__(self):
        self.over = [0.0] * 5
        self.vent_off_at = None
        self.vent_watch_t0 = None

    def hook(self, s):
        for i in range(5):
            self.over[i] = max(self.over[i], s["temps"][f"Z{i + 1}"] - s["setpoints"][f"Z{i + 1}"])
        if self.vent_watch_t0 is not None and self.vent_off_at is None and not s["flags"]["VENT_MOTOR"]:
            self.vent_off_at = time.time() - self.vent_watch_t0

    def to_ready(self, name):
        cmd("BT_AQUEC")
        s, dt = wait(lambda s: s["flags"]["K1_AQUEC"] and s["state"] == "AQUECIMENTO", 20, "K1 fechado e AQUECIMENTO", hook=self.hook)
        check(f"{name}: BT_AQUEC confirmado pelo Ladder (K1_AQUEC)", True, f"em {dt:.1f}s")
        s, dt = wait(lambda s: s["state"] in ("ENCHARQUE", "PRONTO"), 600, "todas as zonas >= 330 (ENCHARQUE)", hook=self.hook)
        check(f"{name}: zonas chegaram a 330 degC (ENCHARQUE)", True, f"em {dt:.0f}s; temps={s['temps']}")
        t_ench = time.time()
        s, dt = wait(lambda s: s["state"] == "PRONTO", 1100, "PRONTO apos 15 min", poll=1.0, hook=self.hook)
        el = time.time() - t_ench
        check(f"{name}: PRONTO somente apos ~900 s de encharque continuo", 895 <= el <= 925, f"{el:.1f}s")
        check(f"{name}: sobressinal dos PIDs (limite de aviso 15 degC)", max(self.over) <= 15.0,
              f"max sobressinal por zona={[round(x, 1) for x in self.over]}")
        return s

    def to_extrusion(self, name):
        cmd("BT_LIGA")
        s, dt = wait(lambda s: s["state"] == "EXTRUSAO", 20, "EXTRUSAO", hook=self.hook)
        check(f"{name}: BT_LIGA confirmado pelo Ladder (EXTRUSAO)", True, f"em {dt:.1f}s")
        s, _ = wait(lambda s: abs(s["rpm_real"] - s["rpm_ref"]) < 1.0 and s["rpm_ref"] > 0, 30, "rpm real segue a referencia", hook=self.hook)
        check(f"{name}: INV_RUN, ventilador, referencia 25 rpm",
              s["flags"]["INV_RUN"] and s["flags"]["VENT_MOTOR"] and abs(s["rpm_ref"] - 25) < 1,
              f"rpm_ref={s['rpm_ref']} real={s['rpm_real']} pressao={s['pressure_mpa']} MPa")
        return s


def scenario(name):
    def deco(fn):
        def run():
            log(f"===== {name} =====")
            try:
                fn()
            except Fail as e:
                check(name, False, f"{e}")
            except Exception as e:  # noqa: BLE001
                check(name, False, f"excecao {type(e).__name__}: {e}")
                log(traceback.format_exc())
            finally:
                try:
                    idle()
                except Exception as e:  # noqa: BLE001
                    log(f"AVISO: baseline nao restabelecido: {e}")
        return run
    return deco


@scenario("S1 partida e reset de partida")
def s1():
    idle()
    check("S1: DESLIGADO apos reset de partida", st()["state"] == "DESLIGADO")


@scenario("S2 termopar rompido (Z3) durante aquecimento")
def s2():
    cmd("BT_AQUEC")
    wait(lambda s: s["state"] == "AQUECIMENTO", 20, "AQUECIMENTO")
    time.sleep(10)
    fault("tc_open_3")
    expect_fault("S2", "TC_FAULT", 20)
    reset_refused_then_ok("S2", "tc_open_3")


@scenario("S3 falha do inversor")
def s3():
    fault("inv_fault")
    expect_fault("S3", "INV_FALHA", 15)
    reset_refused_then_ok("S3", "inv_fault")


@scenario("S4 contator K1 colado")
def s4():
    fault("k1_stuck")
    expect_fault("S4", "FALHA_K1_COL", 15)
    reset_refused_then_ok("S4", "k1_stuck")


@scenario("S5b disjuntor do aquecimento abre")
def s5b():
    cmd("BT_AQUEC")
    wait(lambda s: s["state"] == "AQUECIMENTO", 20, "AQUECIMENTO")
    fault("disj_open")
    s, dt = wait(lambda s: not s["flags"]["EST_AQUEC"] and not s["flags"]["K1_AQUEC"], 10, "K1 abre com DISJ_AQUEC=0")
    check("S5b: disjuntor aberto desliga o aquecimento sem falha", s["state"] == "DESLIGADO", f"em {dt:.1f}s estado={s['state']}")
    fault("disj_open", False)
    time.sleep(2)
    check("S5b: aquecimento NAO religa sozinho ao fechar o disjuntor", st()["state"] == "DESLIGADO", f"estado={st()['state']}")


@scenario("S5 emergencia logica de teste")
def s5():
    cmd("BT_AQUEC")
    wait(lambda s: s["state"] == "AQUECIMENTO", 20, "AQUECIMENTO")
    fault("estop_test")
    expect_fault("S5", "SEG_OK", 15)
    reset_refused_then_ok("S5", "estop_test")


def run_stop_scenario():
    log("===== S12 parada normal e pos-ventilacao de 5 min =====")
    h4 = Heat()
    try:
        idle()
        h4.to_ready("S12")
        h4.to_extrusion("S12")
        cmd("STOP")
        t_stop = time.time()
        s, _ = wait(lambda s: s["state"] != "EXTRUSAO", 10, "sair de EXTRUSAO")
        check("S12: STOP parou a rosca e manteve o aquecimento (PRONTO)", (not s["flags"]["INV_RUN"]) and s["state"] == "PRONTO", f"estado={s['state']}")
        check("S12: ventilador segue ligado apos parar", s["flags"]["VENT_MOTOR"])
        wait(lambda s: not s["flags"]["VENT_MOTOR"], 340, "fim da pos-ventilacao", poll=1.0)
        el = time.time() - t_stop
        check("S12: pos-ventilacao de 5 min", 290 <= el <= 320, f"{el:.1f}s")
    except Fail as e:
        check("S12 parada normal", False, str(e))
    finally:
        clear_faults()


def cycle_runs(only_pressure=False, only_rest=False):
    t_fault = time.time()
    # --- RUN 1: nominal + pressao
    h = Heat()
    log("===== S6 nominal: aquecer, encharque 15 min, PRONTO, EXTRUSAO =====")
    try:
        h.to_ready("S6")
        h.to_extrusion("S6")
        log("===== S7 aviso de pressao (16,5-17 MPa) e reducao de referencia =====")
        fault("pressure_warn")
        seen_alm, min_ref = False, 99.0
        t0 = time.time()
        while time.time() - t0 < 25:
            s = st()
            seen_alm |= s["flags"]["ALM_PRESSAO_16_5"]
            min_ref = min(min_ref, s["rpm_ref"])
            time.sleep(0.25)
        check("S7: ALM_PRESSAO_16_5 acionado", seen_alm)
        check("S7: referencia reduzida a ~90% (22,5 rpm)", min_ref <= 22.6, f"menor REF_RPM_LIM observada={min_ref}")
        s = st()
        check("S7: aviso NAO trava falha", s["state"] == "EXTRUSAO", f"estado={s['state']} pressao={s['pressure_mpa']}")
        fault("pressure_warn", False)
        time.sleep(3)
        log("===== S8 pressao >= 17 MPa: falha travada =====")
        fault("pressure_high")
        expect_fault("S8", "PRESSAO_ALTA_17", 20)
        t_fault = time.time()
        s = st()
        check("S8: pos-ventilacao do motor segue apos a falha", s["flags"]["VENT_MOTOR"], f"VENT_MOTOR={s['flags']['VENT_MOTOR']}")
        # com a rosca parada a pressao simulada cai sozinha: a falha tem de SEGUIR travada ate o reset...
        fault("pressure_high", False)
        time.sleep(5)
        s = st()
        check("S8: falha SEGUE travada depois que a pressao normalizou (ate o reset)", s["state"] == "FALHA_TRAVADA" and not s["flags"]["M_CAUSA"],
              f"estado={s['state']} M_CAUSA={s['flags']['M_CAUSA']} pressao={s['pressure_mpa']}")
        # ...e com bloqueio persistente (>= 17 MPa mesmo parada) o reset tem de ser RECUSADO
        fault("pressure_stuck")
        time.sleep(2)
        reset_refused_then_ok("S8", "pressure_stuck")
    except Fail as e:
        check("S6-S8 (nominal/pressao)", False, str(e))
    except Exception as e:  # noqa: BLE001
        check("S6-S8", False, f"excecao {e}")
        log(traceback.format_exc())
    finally:
        clear_faults()
    if only_pressure:
        if only_rest:
            run_stop_scenario()
        return
    # --- RUN 2: ventilador (mede em paralelo o fim da pos-ventilacao apos a falha de pressao)
    h2 = Heat()
    h2.vent_watch_t0 = t_fault
    log("===== S9 ventilador do motor falha por 10 s =====")
    try:
        idle()
        h2.to_ready("S9")
        check("S10: pos-ventilacao terminou ~300 s apos a rosca parar", h2.vent_off_at is not None and 285 <= h2.vent_off_at <= 330,
              f"VENT_MOTOR apagou {h2.vent_off_at and round(h2.vent_off_at, 1)}s apos a falha de pressao")
        h2.to_extrusion("S9")
        fault("vent_fail")
        expect_fault("S9", "FALHA_VENT_10S", 25)
        stays_latched_then_reset("S9", "vent_fail")
    except Fail as e:
        check("S9 ventilador", False, str(e))
    finally:
        clear_faults()
    # --- RUN 3: funil
    log("===== S11 sem material por 60 s =====")
    h3 = Heat()
    try:
        idle()
        h3.to_ready("S11")
        h3.to_extrusion("S11")
        fault("funil_empty")
        s, dt = expect_fault("S11", "FALHA_SEM_MAT", 90)
        check("S11: falha so apos ~60 s", 55 <= dt <= 70, f"{dt:.1f}s")
        stays_latched_then_reset("S11", "funil_empty")
    except Fail as e:
        check("S11 funil", False, str(e))
    finally:
        clear_faults()
    run_stop_scenario()


def save_trace():
    rows, nxt, cols = [], 0, ""
    while True:
        r = get(f"/api/trace?since={nxt}")
        cols = r["cols"]
        rows += r["rows"]
        if not r["rows"]:
            break
        nxt += len(r["rows"])
    TRACE.parent.mkdir(exist_ok=True)
    TRACE.write_text(json.dumps({"cols": cols, "rows": rows}), encoding="utf-8")
    log(f"trace salvo: {len(rows)} ciclos em {TRACE}")


if __name__ == "__main__":
    ONLY = sys.argv[2] if len(sys.argv) > 2 else ""   # "rest" = complemento: pressao (S6-S8 com latch) + parada normal (S12)
    OUT.write_text("", encoding="utf-8") if not ONLY else None
    h = get("/api/health")
    log(f"CP4 cenarios online, tempo real. health={h}")
    assert h["mode"] == "PLC" and h["plc_connected"], "backend precisa estar em modo PLC e conectado"
    log("ATENCAO: entradas vem da planta SIMULADA do backend; o Ladder e o canal OPC UA sao reais.")
    try:
        for f in (s1,) if ONLY else (s1, s2, s3, s4, s5b, s5):
            f()
        cycle_runs(only_pressure=bool(ONLY), only_rest=(ONLY == "rest"))
    finally:
        try:
            clear_faults()
            save_trace()
        except Exception as e:  # noqa: BLE001
            log(f"AVISO ao salvar trace: {e}")
        ok = sum(1 for _, c in RESULTS if c)
        log(f"RESUMO: {ok}/{len(RESULTS)} verificacoes passaram")
        for n, c in RESULTS:
            if not c:
                log(f"  FALHOU: {n}")
