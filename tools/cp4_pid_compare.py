"""Compara a saida do Util.PID REAL (lida do Control Win) com o modelo de referencia `_PidModel`, sobre o trace do ensaio online.

Entrada: work/cp4_trace.json (gerado por tools/cp4_scenarios.py; colunas em 'cols').
O modelo recebe as MESMAS entradas (temperatura medida, setpoint, RESET = nao aquecendo ou termopar ruim) nos mesmos instantes.
Diferencas esperadas: o trace amostra ~7 Hz enquanto o PID do CLP roda a 10 Hz (defasagem de amostragem), entao o criterio
e estatistico (erro medio/maximo e concordancia da saturacao), nao ponto a ponto.
Saida: docs/evidence/CP4_PID_COMPARE.txt
"""
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codesys.generator.ld import _PidModel  # noqa: E402

TRACE = Path("work/cp4_trace.json")
OUT = Path("docs/evidence/CP4_PID_COMPARE.txt")
KP, TN = 8.0, 20.0
# indices das colunas: 0 t, 1 dt, 2-6 TT_Z1-5, 7-11 SP_Z1-5, 12-16 Y_Z1-5, 17 TT_SUBS, 18 SP_IR, 19 Y_IR, 20 IR_HAB, 21 EST_AQUEC, 22 TC_OK[5]


def main():
    rows = json.loads(TRACE.read_text(encoding="utf-8"))["rows"]
    lines = [f"Comparacao Util.PID (runtime) x _PidModel (referencia) - {len(rows)} ciclos, KP={KP} %/degC, TN={TN} s", ""]
    ok_all = True
    for z in range(5):
        m = _PidModel()
        diffs, sat_agree, sat_n, lin_diffs = [], 0, 0, []
        for r in rows:
            dt, tt, sp, y_run, aquec, tc_ok = r[1], r[2 + z], r[7 + z], r[12 + z], r[21], r[22][z]
            y_mod, _ = m.step(dt, {"RESET": (not aquec) or (not tc_ok), "MANUAL": False, "Y_MANUAL": 0.0, "Y_OFFSET": 0.0,
                                   "Y_MIN": 0.0, "Y_MAX": 100.0, "TV": 0.0, "ACTUAL": tt, "SET_POINT": sp, "KP": KP, "TN": TN})
            diffs.append(abs(y_mod - y_run))
            if y_run >= 99.9 or y_run <= 0.1 or y_mod >= 99.9 or y_mod <= 0.1:
                sat_n += 1
                sat_agree += (y_run >= 99.9) == (y_mod >= 99.9) and (y_run <= 0.1) == (y_mod <= 0.1)
            else:
                lin_diffs.append(abs(y_mod - y_run))
        lin = statistics.mean(lin_diffs) if lin_diffs else float("nan")
        lines.append(f"Z{z + 1}: erro medio={statistics.mean(diffs):.2f} %  max={max(diffs):.1f} %  | regiao linear: erro medio={lin:.2f} % "
                     f"({len(lin_diffs)} ciclos) | saturacao: concordancia {sat_agree}/{sat_n}")
        ok_all &= (not lin_diffs) or lin < 5.0
    lines += ["", "Criterio: erro medio na regiao linear < 5 % da saida (defasagem de amostragem aceita). Resultado: "
              + ("DENTRO do criterio" if ok_all else "FORA do criterio - investigar (anti-windup/integral do Util.PID)")]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
