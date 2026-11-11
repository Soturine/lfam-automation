"""Simulador fisico DIDATICO da extrusora LFAM.

Calcula apenas a planta (temperaturas, pressao, rpm, sensores). NAO decide permissivos: quem
decide e o programa do CLP. Todos os parametros sao HIPOTETICOS, nao calibrados a uma maquina real.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

T_AMB = 25.0
ZONES = 5


@dataclass
class Params:
    gain_c: float = 520.0        # degC acima do ambiente com duty=1 (regime)
    tau_s: float = 60.0          # constante de tempo termica por zona
    coupling: float = 0.04       # acoplamento com zona vizinha (1/s)
    zsr_tau_s: float = 90.0      # trecho sem resistencia (segue media das zonas 2-3 menos perda)
    zsr_ratio: float = 0.62      # fracao do delta das zonas vizinhas
    resf_heat_c: float = 40.0    # aquecimento da camara de resfriamento pela zona 1
    resf_cool_tau_s: float = 40.0
    rpm_max: float = 34.0
    rpm_tau_s: float = 2.0       # rampa do inversor
    mpa_per_rpm: float = 0.47    # pressao ~ rpm a quente (34 rpm ~ 16 MPa)
    cold_penalty: float = 1.8    # multiplicador da pressao se alguma zona < 330 degC
    ir_gain_c: float = 380.0
    ir_tau_s: float = 5.0
    noise_c: float = 0.0
    noise_mpa: float = 0.0


@dataclass
class Faults:
    tc_open: list[bool] = field(default_factory=lambda: [False] * ZONES)
    pressure_offset_mpa: float = 0.0
    funil_empty: bool = False
    vent_fail: bool = False
    inv_fault: bool = False
    k1_stuck_closed: bool = False


@dataclass
class Inputs:
    duty: list[float] = field(default_factory=lambda: [0.0] * ZONES)  # SSR Z1..Z5 (0..1)
    duty_ir: float = 0.0
    k1: bool = False                 # contator dos aquecedores
    inv_run: bool = False
    rpm_ref: float = 0.0
    resf_on: bool = False
    vent_motor: bool = False
    robo_em_mov: bool = False


class Plant:
    def __init__(self, params: Params | None = None, seed: int = 1):
        self.p = params or Params()
        self.faults = Faults()
        self.rng = random.Random(seed)
        self.t_zone = [T_AMB] * ZONES
        self.t_zsr = T_AMB
        self.t_resf = T_AMB
        self.t_subs = T_AMB
        self.rpm = 0.0
        self.pressure = 0.0
        self.time_s = 0.0

    def _n(self, amp: float) -> float:
        return self.rng.uniform(-amp, amp) if amp else 0.0

    def step(self, dt: float, u: Inputs) -> None:
        p = self.p
        k1_closed = u.k1 or self.faults.k1_stuck_closed
        new = []
        for i in range(ZONES):
            duty = u.duty[i] if k1_closed else 0.0
            target = T_AMB + p.gain_c * max(0.0, min(1.0, duty))
            d = (target - self.t_zone[i]) / p.tau_s
            for j in (i - 1, i + 1):
                if 0 <= j < ZONES:
                    d += p.coupling * (self.t_zone[j] - self.t_zone[i]) * 0.1
            new.append(self.t_zone[i] + d * dt)
        self.t_zone = new
        zsr_t = T_AMB + p.zsr_ratio * ((self.t_zone[1] + self.t_zone[2]) / 2 - T_AMB)
        self.t_zsr += (zsr_t - self.t_zsr) / p.zsr_tau_s * dt
        resf_t = T_AMB + (p.resf_heat_c * max(0.0, self.t_zone[0] - T_AMB) / 300.0 * 3.0)
        if u.resf_on:
            resf_t = T_AMB + 5.0
        self.t_resf += (resf_t - self.t_resf) / p.resf_cool_tau_s * dt
        run = u.inv_run and not self.faults.inv_fault
        ref = max(0.0, min(p.rpm_max, u.rpm_ref)) if run else 0.0
        self.rpm += (ref - self.rpm) / p.rpm_tau_s * dt
        cold = min(self.t_zone) < 330.0
        base = p.mpa_per_rpm * self.rpm * (p.cold_penalty if cold else 1.0)
        self.pressure = max(0.0, base + self.faults.pressure_offset_mpa)
        ir_t = T_AMB + p.ir_gain_c * max(0.0, min(1.0, u.duty_ir)) if (u.robo_em_mov and run) else T_AMB
        self.t_subs += (ir_t - self.t_subs) / p.ir_tau_s * dt
        self.time_s += dt

    def sensors(self, u: Inputs) -> dict:
        """Sinais como o CLP os veria. Fio aberto => flag de qualidade, valor invalido."""
        p = self.p
        tc_ok = [not f for f in self.faults.tc_open]
        out = {f"TT_Z{i+1}": (self.t_zone[i] + self._n(p.noise_c) if tc_ok[i] else None) for i in range(ZONES)}
        out.update({f"TC_Z{i+1}_OK": tc_ok[i] for i in range(ZONES)})
        out.update(
            TT_ZSR=self.t_zsr, TT_RESF=self.t_resf, TT_SUBSTRATO_C=self.t_subs,
            PT_FUNDIDO_MPA=self.pressure + self._n(p.noise_mpa), INV_RPM_REAL=self.rpm,
            FUNIL_BAIXO=not self.faults.funil_empty,       # ativo-baixo: 0 = vazio
            VENT_OK=bool(u.vent_motor) and not self.faults.vent_fail,
            K1_CONF=bool(u.k1) or self.faults.k1_stuck_closed,  # colado: confirma mesmo sem comando
            INV_FALHA=self.faults.inv_fault,
            INV_PRONTO=not self.faults.inv_fault,
        )
        return out
