"""PID Util.PID (modelo de referencia), PWM, CTU/R_TRIG e escala do inversor, no programa completo."""
from codesys.generator import program as PRG
from codesys.generator.ld import scan

BASE = dict(EST_AQUEC=True, SEG_OK=True, MOT_SOBRETEMP=True, DISJ_AQUEC=True, BT_DESLIGA=True, FUNIL_BAIXO=True, VENT_OK=True,
            SECADOR_OK=True, INV_PRONTO=True, K1_CONF=True, TT_ZSR=300.0, TT_RESF=40.0, PT_FUNDIDO_RAW=0, TT_SUBSTRATO_RAW=0,
            SP_RPM_OPERADOR=25.0, SP_IR_C=200.0, **{f"SP_Z{z}": 350.0 for z in range(1, 6)})


def temps(raw):
    return {f"TT_Z{z}_RAW": raw for z in range(1, 6)}


def run(env, secs, dt=0.1):
    for _ in range(round(secs / dt)):
        env = scan(PRG.RUNGS, env, dt)
    return env


def test_pid_is_reset_zero_output_when_heating_off_not_frozen():
    env = run({**BASE, **temps(3000), "BT_AQUEC": True}, 5)
    assert env["EST_AQUEC"] and env["Y_Z1"] > 0
    env = run({**env, "BT_AQUEC": False, "SEG_OK": False}, 0.5)      # perde permissivo: EST_AQUEC cai
    assert not env["EST_AQUEC"] and env["Y_Z1"] == 0.0 and not env["SSR_Z1"], "PID nao pode congelar a saida"


def test_pid_saturates_at_100_and_has_anti_windup():
    env = run({**BASE, **temps(500), "BT_AQUEC": True}, 120)             # 50 degC contra SP 350: saturado
    assert env["Y_Z1"] == 100.0
    env = run({**env, **temps(3600)}, 0.5)                               # 360 degC: erro negativo
    assert env["Y_Z1"] < 100.0, "sem windup: sai da saturacao logo apos o erro inverter"
    env = run({**env, **temps(3600)}, 5)
    assert env["Y_Z1"] == 0.0


def test_pwm_duty_matches_pid_output_over_one_period():
    env = run({**BASE, **temps(3495), "BT_AQUEC": True}, 30)           # a 0,5 degC do SP -> saida intermediaria (nao saturada)
    y = env["Y_Z2"]
    assert 0.0 < y < 100.0
    on = n = 0
    for _ in range(int(20.0 / 0.1)):                                    # 10 periodos de ~2 s
        env = scan(PRG.RUNGS, env, 0.1)
        on += bool(env["PWM_Z2"]); n += 1
    assert abs(on / n * 100.0 - env["Y_Z2"]) < 8.0, (on / n * 100.0, env["Y_Z2"])


def test_open_thermocouple_resets_that_zone_pid_and_blocks_ssr():
    env = run({**BASE, **temps(3000), "BT_AQUEC": True}, 3)
    env = run({**env, "TT_Z3_RAW": 32767}, 1)
    assert env["Y_Z3"] == 0.0 and not env["SSR_Z3"] and env["TC_FAULT"]


def test_ir_pid_only_runs_when_ir_enabled():
    env = run({**BASE, **temps(3500)}, 2)
    assert env["Y_IR"] == 0.0 and not env["SSR_IR"]


def test_funnel_counter_counts_edges_not_levels_and_resets():
    env = run({**BASE, **temps(3500)}, 1)
    for _ in range(3):
        env = run({**env, "FUNIL_BAIXO": False}, 2)      # funil esvazia -> carregador liga (borda)
        env = run({**env, "FUNIL_BAIXO": True}, 2)
    assert env["CONT_LOTES"] == 3
    env = run({**env, "FUNIL_BAIXO": False}, 10)         # nivel mantido nao conta de novo
    assert env["CONT_LOTES"] == 4
    env = run({**env, "HMI_RESET_LOTES": True}, 0.3)
    assert env["CONT_LOTES"] == 0


def test_inverter_reference_scale_limits():
    env = run({**BASE, "SP_RPM_OPERADOR": 34.0}, 0.2)
    assert env["INV_REF"] == round(34.0 / 34.0 * 57.0 / 60.0 * 16384.0)
    env = run({**BASE, "SP_RPM_OPERADOR": 5.0}, 0.2)    # abaixo da faixa -> LIMIT 17 rpm
    assert env["INV_REF"] == round(17.0 / 34.0 * 57.0 / 60.0 * 16384.0)


def test_every_identifier_used_in_expressions_is_declared():
    """Evita o erro C46 do compilador (identificador nao definido) que o avaliador Python tolera (nome desconhecido = 0)."""
    import re
    from codesys.generator.ld import AssignRung, CmpRung, FbRung, _FUNCS
    declared = PRG.variables()
    keywords = {"NOT", "AND", "OR", "MOD", "TRUE", "FALSE"} | set(_FUNCS)
    missing = set()
    for r in PRG.RUNGS:
        exprs = []
        if isinstance(r, FbRung):
            exprs = list(r.inputs.values())
        elif isinstance(r, AssignRung):
            exprs = [r.expr]
        elif isinstance(r, CmpRung):
            exprs = [r.a, r.b]
        for ex in exprs:
            for tok in re.findall(r"\b[A-Za-z_][A-Za-z_0-9]*\b", ex):
                if tok not in keywords and tok not in declared and not re.fullmatch(r"\d+(\.\d+)?", tok):
                    missing.add(tok)
    assert not missing, sorted(missing)
