"""Motor do MODO DEMO.

Executa o MESMO programa Ladder gerado (avaliador de referencia em codesys/generator) sobre o simulador fisico
didatico, mais PIDs em Python. Isto NAO e o CLP: e uma simulacao rotulada como DEMO. No modo CLP a logica vem
do CODESYS Control Win (ainda nao integrado - ver docs/evidence).
"""
from __future__ import annotations

import threading
import time

from .transport import DemoTransport, PlcLinkError
from simulator.lfam_sim import Plant, Inputs, ZONES

SP_LIMITS = {"Z1": (330, 375), "Z2": (330, 375), "Z3": (330, 375), "Z4": (330, 375), "Z5": (345, 375)}
RPM_LIMITS = (17.0, 34.0)
BUTTONS = {"BT_AQUEC", "BT_LIGA", "BT_RESET"}  # pulsos; BT_DESLIGA e tratado como 'parar' (NF)


class DemoEngine:
    def __init__(self, seed: int = 1, transport=None):
        self.transport = transport or DemoTransport()
        self.link_error = ""
        self.plant = Plant(seed=seed)
        self.env: dict = {}
        self.t = 0.0
        self.sp_z = [340.0, 350.0, 350.0, 360.0, 360.0]
        self.sp_rpm = 25.0
        self.sp_ir = 200.0
        self.duty = [0.0] * ZONES
        self.duty_ir = 0.0
        self.pulses: dict = {}
        self.time_scale = 1.0         # velocidade do relogio simulado (so DEMO; modo apresentacao)
        self.estop_test = False       # emergencia LOGICA de teste (nao substitui a fisica)
        self.disj_open = False        # disjuntor do aquecimento aberto (DEMO/ensaio)
        self.robo_mov = False
        self.sel_auto = False
        self.robo_cmd = False
        self.lock = threading.RLock()
        self.log: list = []
        self._trace: list = []
        self._trace_base = 0

    # ---------------------------------------------------------------- comandos (apenas SOLICITACOES)
    def request(self, name: str) -> tuple[bool, str]:
        with self.lock:
            if self.transport.mode == "PLC" and not self.transport.healthy:
                return False, "sem comunicacao com o controlador: comando recusado"
            if name in BUTTONS:
                self.pulses[name] = 0.5
                self._log(f"solicitado {name}")
                return True, "solicitacao enviada; aguarde confirmacao do estado"
            if name == "STOP":
                self.pulses["STOP"] = 1.0      # BT_DESLIGA e NF: pulso de 1 s com contato aberto (nao fica preso)
                self._log("solicitado STOP")
                return True, "parada solicitada"
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
            elif fault == "pressure_warn":
                f.pressure_offset_mpa = 5.0 if on else 0.0  # faixa 16,5-17 MPa a 25 rpm: aviso sem falha (hipotese didatica)
            elif fault == "pressure_stuck":
                f.pressure_offset_mpa = 18.0 if on else 0.0  # linha bloqueada: pressao >= 17 MPa mesmo com a rosca parada
            elif fault == "funil_empty":
                f.funil_empty = on
            elif fault == "vent_fail":
                f.vent_fail = on
            elif fault == "inv_fault":
                f.inv_fault = on
            elif fault == "k1_stuck":
                f.k1_stuck_closed = on
            elif fault == "disj_open":
                self.disj_open = on
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
                "SEG_OK": not self.estop_test, "MOT_SOBRETEMP": True, "DISJ_AQUEC": not self.disj_open,
                "BT_DESLIGA": "STOP" not in self.pulses, "SEL_AUTO": self.sel_auto, "ROBO_CMD_EXTR": self.robo_cmd,
                "ROBO_EM_MOV": self.robo_mov, "SECADOR_OK": True,
                "INV_PRONTO": s["INV_PRONTO"], "INV_FALHA": s["INV_FALHA"], "FUNIL_BAIXO": s["FUNIL_BAIXO"],
                "VENT_OK": s["VENT_OK"], "K1_CONF": s["K1_CONF"], "SP_RPM_OPERADOR": self.sp_rpm,
                "BT_AQUEC": "BT_AQUEC" in self.pulses, "BT_LIGA": "BT_LIGA" in self.pulses, "BT_RESET": "BT_RESET" in self.pulses,
            }
            # PID e PWM executam DENTRO do programa (Util.PID no Ladder, todo ciclo); aqui so os setpoints
            for i in range(ZONES):
                env_in[f"SP_Z{i + 1}"] = self.sp_z[i]
            env_in["SP_IR_C"] = self.sp_ir

            try:
                self.env = self.transport.cycle(env_in, dt)
                self.link_error = ""
            except PlcLinkError as e:
                self.link_error = str(e)
                self.pulses.clear()            # nunca reenviar comandos pendentes apos perda de enlace
                return
            self.duty = [self.env.get(f"Y_Z{z}", 0.0) / 100.0 for z in range(1, 6)]
            self.duty_ir = self.env.get("Y_IR", 0.0) / 100.0
            for k in list(self.pulses):
                self.pulses[k] -= dt
                if self.pulses[k] <= 0:
                    del self.pulses[k]
            self._trace.append([time.time(), dt] + [self.env.get(f"TT_Z{z}", 0.0) for z in range(1, 6)] + list(self.sp_z)
                               + [self.env.get(f"Y_Z{z}", 0.0) for z in range(1, 6)]
                               + [self.env.get("TT_SUBSTRATO_C", 0.0), self.sp_ir, self.env.get("Y_IR", 0.0), bool(self.env.get("IR_HAB")),
                                  bool(self.env.get("EST_AQUEC")), [bool(self.env.get(f"TC_Z{z}_OK", True)) for z in range(1, 6)]])
            if len(self._trace) > 100000:
                del self._trace[:20000]
                self._trace_base += 20000
            self.plant.step(dt, self._plant_inputs())
            self.t += dt

    def trace_since(self, since: int) -> dict:
        with self.lock:
            i = max(0, since - self._trace_base)
            return {"next": self._trace_base + len(self._trace), "cols": "t,dt,TT_Z1-5,SP_Z1-5,Y_Z1-5,TT_SUBS,SP_IR,Y_IR,IR_HAB,EST_AQUEC,TC_OK[5]",
                    "rows": self._trace[i:i + 20000]}

    CAUSE_KEYS = ("SEG_OK", "MOT_SOBRETEMP", "INV_FALHA", "PRESSAO_ALTA_17", "SOBRETEMP_400", "TC_FAULT",
                  "FALHA_RESF_2M", "FALHA_SEM_MAT", "FALHA_VENT_10S", "FALHA_K1_COL")

    def _active_causes(self) -> list:
        e = self.env
        return [k for k in self.CAUSE_KEYS if (not e.get(k, True) if k in ("SEG_OK", "MOT_SOBRETEMP") else e.get(k))]

    def latched_causes(self) -> list:
        """Primeira(s) causa(s) que travaram a falha: latches CAUSA_* do PROPRIO programa (nao dependem do polling do backend)."""
        return [k for k in self.CAUSE_KEYS if self.env.get("CAUSA_" + k)]

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
                "mode": self.transport.mode, "link_error": self.link_error,
                "source": ("simulacao (programa Ladder gerado em avaliador Python; NAO e o CLP)" if self.transport.mode == "DEMO"
                           else "valores lidos do CODESYS Control Win via OPC UA (ponte de desenvolvimento)"),
                "time_scale": self.time_scale, "plc_connected": self.transport.mode == "PLC" and self.transport.healthy, "t_sim_s": round(self.t, 2), "timestamp": time.time(), "state": state,
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
                "causes": self._active_causes(),
                "latched_causes": self.latched_causes(),
                "log": self.log[-20:],
            }

    def _log(self, msg: str) -> None:
        self.log.append({"t_sim_s": round(self.t, 1), "msg": msg})
