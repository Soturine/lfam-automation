"""Motor do MODO DEMO.

Executa o MESMO programa Ladder gerado (avaliador de referencia em codesys/generator) sobre o simulador fisico
didatico, mais PIDs em Python. Isto NAO e o CLP: e uma simulacao rotulada como DEMO. No modo CLP a logica vem
do CODESYS Control Win (ainda nao integrado - ver docs/evidence).
"""
from __future__ import annotations

import threading
import time

from codesys.generator import program as PRG
from codesys.generator.ld import scan
from simulator.lfam_sim import Plant, Inputs, ZONES

SP_LIMITS = {"Z1": (330, 375), "Z2": (330, 375), "Z3": (330, 375), "Z4": (330, 375), "Z5": (345, 375)}
RPM_LIMITS = (17.0, 34.0)
BUTTONS = {"BT_AQUEC", "BT_LIGA", "BT_RESET"}  # pulsos; BT_DESLIGA e tratado como 'parar' (NF)
PERIOD_S = 2.0
KP, KI = 0.08, 0.004


class DemoEngine:
    def __init__(self, seed: int = 1):
        self.plant = Plant(seed=seed)
        self.env: dict = {}
        self.t = 0.0
        self.sp_z = [340.0, 350.0, 350.0, 360.0, 360.0]
        self.sp_rpm = 25.0
        self.sp_ir = 200.0
        self.integral = [0.0] * ZONES
        self.integral_ir = 0.0
        self.duty = [0.0] * ZONES
        self.duty_ir = 0.0
        self.pulses: dict = {}
        self.stop_pressed = False
        self.estop_test = False       # emergencia LOGICA de teste (nao substitui a fisica)
        self.robo_mov = False
        self.sel_auto = False
        self.robo_cmd = False
        self.lock = threading.RLock()
        self.log: list = []

    # ---------------------------------------------------------------- comandos (apenas SOLICITACOES)
    def request(self, name: str) -> tuple[bool, str]:
        with self.lock:
            if name in BUTTONS:
                self.pulses[name] = 0.5
                self._log(f"solicitado {name}")
                return True, "solicitacao enviada; aguarde confirmacao do estado"
            if name == "STOP":
                self.stop_pressed = True
                self._log("solicitado STOP")
                return True, "parada solicitada"
            if name == "STOP_RELEASE":
                self.stop_pressed = False
                return True, "parada liberada"
        return False, f"comando desconhecido: {name}"

    def set_setpoint(self, key: str, value: float) -> tuple[bool, str]:
        with self.lock:
            if key in SP_LIMITS:
                lo, hi = SP_LIMITS[key]
                if not lo <= value <= hi:
                    return False, f"{key} fora da faixa {lo}-{hi} degC"
                self.sp_z[int(key[1]) - 1] = float(value)
            elif key == "RPM":
                if not RPM_LIMITS[0] <= value <= RPM_LIMITS[1]:
                    return False, "rotacao fora da faixa 17-34 rpm"
                self.sp_rpm = float(value)
            elif key == "IR":
                if not 20 <= value <= 480:
                    return False, "IR fora da faixa 20-480 degC"
                self.sp_ir = float(value)
            else:
                return False, f"setpoint desconhecido: {key}"
            self._log(f"setpoint {key}={value}")
            return True, "ok"

    def inject(self, fault: str, on: bool = True) -> tuple[bool, str]:
        """Somente DEMO: injeta falha na PLANTA (sensor/atuador), nunca no programa."""
        f = self.plant.faults
        with self.lock:
            if fault.startswith("tc_open_") and fault[-1] in "12345":
                f.tc_open[int(fault[-1]) - 1] = on
            elif fault == "pressure_high":
                f.pressure_offset_mpa = 7.0 if on else 0.0  # bico entupido (hipotese didatica)
            elif fault == "funil_empty":
                f.funil_empty = on
            elif fault == "vent_fail":
                f.vent_fail = on
            elif fault == "inv_fault":
                f.inv_fault = on
            elif fault == "k1_stuck":
                f.k1_stuck_closed = on
            elif fault == "estop_test":
                self.estop_test = on
            else:
                return False, f"falha desconhecida: {fault}"
            self._log(f"DEMO falha {fault}={on}")
            return True, "ok"

    def set_robot(self, moving: bool | None = None, cmd: bool | None = None, auto: bool | None = None) -> None:
        with self.lock:
            if moving is not None:
                self.robo_mov = moving
            if cmd is not None:
                self.robo_cmd = cmd
            if auto is not None:
                self.sel_auto = auto

    # ---------------------------------------------------------------- um passo de simulacao
    def step(self, dt: float = 0.1) -> None:
        with self.lock:
            u_prev = self._plant_inputs()
            s = self.plant.sensors(u_prev)
            raw = {f"TT_Z{z}_RAW": 32767 if s[f"TT_Z{z}"] is None else int(round(s[f"TT_Z{z}"] * 10)) for z in range(1, 6)}
            env_in = {
                **self.env, **raw,
                "PT_FUNDIDO_RAW": int(max(0.0, min(35.0, s["PT_FUNDIDO_MPA"])) / 35.0 * 27648),
                "TT_SUBSTRATO_RAW": int(max(0.0, min(500.0, s["TT_SUBSTRATO_C"])) / 500.0 * 27648),
                "TT_ZSR": s["TT_ZSR"], "TT_RESF": s["TT_RESF"],
                "SEG_OK": not self.estop_test, "MOT_SOBRETEMP": True, "DISJ_AQUEC": True,
                "BT_DESLIGA": not self.stop_pressed, "SEL_AUTO": self.sel_auto, "ROBO_CMD_EXTR": self.robo_cmd,
                "ROBO_EM_MOV": self.robo_mov, "SECADOR_OK": True,
                "INV_PRONTO": s["INV_PRONTO"], "INV_FALHA": s["INV_FALHA"], "FUNIL_BAIXO": s["FUNIL_BAIXO"],
                "VENT_OK": s["VENT_OK"], "K1_CONF": s["K1_CONF"], "SP_RPM_OPERADOR": self.sp_rpm,
                "BT_AQUEC": "BT_AQUEC" in self.pulses, "BT_LIGA": "BT_LIGA" in self.pulses, "BT_RESET": "BT_RESET" in self.pulses,
            }
            # PIDs rodam SEMPRE (cada passo); o programa decide se o PWM chega ao SSR (rede 06/13)
            pv = [self.env.get(f"TT_Z{z}") for z in range(1, 6)]
            en = bool(self.env.get("EST_AQUEC"))
            for i in range(ZONES):
                self.duty[i], self.integral[i] = self._pid(self.sp_z[i], pv[i], self.integral[i], en, dt)
                env_in[f"PWM_Z{i + 1}"] = (self.t % PERIOD_S) < PERIOD_S * self.duty[i]
            self.duty_ir, self.integral_ir = self._pid(self.sp_ir, self.env.get("TT_SUBSTRATO_C"), self.integral_ir,
                                                       bool(self.env.get("IR_HAB")), dt, kp=0.01, ki=0.002)
            env_in["PWM_IR"] = (self.t % PERIOD_S) < PERIOD_S * self.duty_ir

            self.env = scan(PRG.RUNGS, env_in, dt)
            for k in list(self.pulses):
                self.pulses[k] -= dt
                if self.pulses[k] <= 0:
                    del self.pulses[k]
            self.plant.step(dt, self._plant_inputs())
            self.t += dt

    @staticmethod
    def _pid(sp, pv, integral, enabled, dt, kp=KP, ki=KI):
        if not enabled or pv is None:
            return 0.0, 0.0                      # desabilitado/sensor invalido: saida 0 e integral zerada (anti-windup)
        e = sp - pv
        u = kp * e + ki * integral
        if 0.0 < u < 1.0:
            integral += e * dt                   # integra so se nao saturado
        return max(0.0, min(1.0, u)), integral

    def _plant_inputs(self) -> Inputs:
        e = self.env
        return Inputs(
            duty=[1.0 if e.get(f"SSR_Z{z}") else 0.0 for z in range(1, 6)], duty_ir=1.0 if e.get("SSR_IR") else 0.0,
            k1=bool(e.get("K1_AQUEC")), inv_run=bool(e.get("INV_RUN")), rpm_ref=float(e.get("REF_RPM_LIM", 0.0)),
            resf_on=bool(e.get("RESF_ON")), vent_motor=bool(e.get("VENT_MOTOR")), robo_em_mov=self.robo_mov,
        )

    # ---------------------------------------------------------------- leitura para a HMI
    def snapshot(self) -> dict:
        with self.lock:
            e = self.env
            state = ("FALHA_TRAVADA" if e.get("FALHA_GERAL") else "EXTRUSAO" if e.get("EST_EXTRUSAO")
                     else "PRONTO" if e.get("EST_PRONTO") else "ENCHARQUE" if e.get("EST_ENCHARQUE")
                     else "AQUECIMENTO" if e.get("EST_AQUEC") else "DESLIGADO")
            return {
                "mode": "DEMO", "source": "simulacao (programa Ladder gerado em avaliador Python; NAO e o CLP)",
                "plc_connected": False, "t_sim_s": round(self.t, 2), "timestamp": time.time(), "state": state,
                "temps": {f"Z{z}": round(e.get(f"TT_Z{z}", 0.0), 1) for z in range(1, 6)},
                "setpoints": {f"Z{z}": self.sp_z[z - 1] for z in range(1, 6)} | {"RPM": self.sp_rpm, "IR": self.sp_ir},
                "ssr_duty": {f"Z{z}": round(self.duty[z - 1], 3) for z in range(1, 6)} | {"IR": round(self.duty_ir, 3)},
                "tt_zsr": round(self.plant.t_zsr, 1), "tt_resf": round(self.plant.t_resf, 1),
                "tt_substrato": round(self.plant.t_subs, 1), "pressure_mpa": round(e.get("PT_FUNDIDO_MPA", 0.0), 2),
                "rpm_ref": e.get("REF_RPM_LIM", 0.0), "rpm_real": round(self.plant.rpm, 2),
                "flags": {k: bool(e.get(k)) for k in (
                    "EST_AQUEC", "EST_ENCHARQUE", "ENCH_OK", "EST_PRONTO", "EST_EXTRUSAO", "FALHA_GERAL", "M_CAUSA", "K1_AQUEC",
                    "RESF_ON", "VENT_MOTOR", "INV_RUN", "SSR_IR", "IR_HAB", "ALIM_FUNIL", "ALM_PRESSAO_16_5", "ALM_ZSR_BAIXA",
                    "TC_FAULT", "LUZ_VERDE", "LUZ_AMARELA", "LUZ_VERM_SIRENE", "ROBO_EXT_PRONTA")},
                "causes": [k for k in ("SEG_OK", "MOT_SOBRETEMP", "INV_FALHA", "PRESSAO_ALTA_17", "SOBRETEMP_400", "TC_FAULT",
                                       "FALHA_RESF_2M", "FALHA_SEM_MAT", "FALHA_VENT_10S", "FALHA_K1_COL")
                           if (not e.get(k, True) if k in ("SEG_OK", "MOT_SOBRETEMP") else e.get(k))],
                "log": self.log[-20:],
            }

    def _log(self, msg: str) -> None:
        self.log.append({"t_sim_s": round(self.t, 1), "msg": msg})
