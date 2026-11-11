from simulator.lfam_sim import Plant, Inputs, ZONES


def run(plant, u, secs, dt=0.1):
    for _ in range(int(secs / dt)):
        plant.step(dt, u)


def heated(duty=0.63):
    pl = Plant()
    u = Inputs(duty=[duty] * ZONES, k1=True)
    run(pl, u, 900)
    return pl, u


def test_zones_reach_operating_band_with_k1_closed():
    pl, _ = heated()
    assert all(330 <= t <= 375 for t in pl.t_zone), pl.t_zone


def test_no_heating_with_k1_open():
    pl = Plant()
    run(pl, Inputs(duty=[1.0] * ZONES, k1=False), 300)
    assert max(pl.t_zone) < 26


def test_stuck_k1_heats_without_command_and_is_visible_to_plc():
    pl = Plant()
    pl.faults.k1_stuck_closed = True
    u = Inputs(duty=[1.0] * ZONES, k1=False)
    run(pl, u, 300)
    assert max(pl.t_zone) > 100 and pl.sensors(u)["K1_CONF"] is True


def test_pressure_grows_with_rpm_and_cold_penalty():
    pl, u = heated()
    u.inv_run, u.rpm_ref = True, 20.0
    run(pl, u, 30); p20 = pl.pressure
    u.rpm_ref = 34.0
    run(pl, u, 30)
    assert pl.pressure > p20 > 0
    cold = Plant(); cu = Inputs(inv_run=True, rpm_ref=20.0); run(cold, cu, 30)
    assert cold.pressure > p20


def test_pressure_fault_injection_reaches_17():
    pl, u = heated()
    pl.faults.pressure_offset_mpa = 5.0
    u.inv_run, u.rpm_ref = True, 34.0
    run(pl, u, 30)
    assert pl.pressure >= 17.0


def test_open_thermocouple_flags_quality_and_hides_value():
    pl = Plant(); pl.faults.tc_open[2] = True
    s = pl.sensors(Inputs())
    assert s["TC_Z3_OK"] is False and s["TT_Z3"] is None and s["TT_Z1"] is not None


def test_active_low_hopper_and_vent_polarity():
    pl = Plant(); u = Inputs(vent_motor=True)
    s = pl.sensors(u); assert s["FUNIL_BAIXO"] is True and s["VENT_OK"] is True
    pl.faults.funil_empty = True; pl.faults.vent_fail = True
    s = pl.sensors(u); assert s["FUNIL_BAIXO"] is False and s["VENT_OK"] is False


def test_inverter_fault_stops_screw():
    pl = Plant(); u = Inputs(inv_run=True, rpm_ref=25.0); run(pl, u, 30)
    assert pl.rpm > 20
    pl.faults.inv_fault = True; run(pl, u, 30)
    assert pl.rpm < 1


def test_deterministic_with_seed():
    a, b = Plant(seed=7), Plant(seed=7)
    a.p.noise_c = b.p.noise_c = 1.0
    u = Inputs(duty=[0.5] * ZONES, k1=True)
    run(a, u, 10); run(b, u, 10)
    assert a.sensors(u)["TT_Z1"] == b.sensors(u)["TT_Z1"]
