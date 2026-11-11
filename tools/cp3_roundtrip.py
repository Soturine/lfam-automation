"""Prova do CP3: HMI -> FastAPI -> OPC UA -> Ladder no Control Win -> leitura confirmada -> HMI.

Pre-requisitos: backend em modo PLC rodando (LFAM_MODE=plc) e o programa em execucao no Control Win com OPC UA publicado.
Credenciais OPC UA ficam em variaveis de ambiente do backend; este script so fala com a API HTTP e NAO conhece senha.
Uso: python tools/cp3_roundtrip.py [http://127.0.0.1:8000]
"""
import json
import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.load(r)


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)


def wait(pred, secs, what):
    t0 = time.time()
    while time.time() - t0 < secs:
        s = get("/api/state")
        if pred(s):
            return s
        time.sleep(0.3)
    raise SystemExit(f"FALHOU: {what} (estado={get('/api/state')['state']}, erro={get('/api/state').get('link_error')})")


h = get("/api/health")
print("health:", h)
assert h["mode"] == "PLC", "backend nao esta em modo PLC"
s = wait(lambda s: s["plc_connected"], 30, "plc_connected (heartbeat do CLP mudando)")
print("1) conectado; heartbeat vivo; estado:", s["state"], "t(s)=", s["t_sim_s"])
hb1 = s["timestamp"]

r = post("/api/command", {"name": "BT_AQUEC"})
print("2) comando solicitado:", r)
s = wait(lambda s: s["flags"]["K1_AQUEC"] and s["state"] != "DESLIGADO", 15, "K1_AQUEC confirmado pelo Ladder")
print("3) CONFIRMADO pelo Ladder no Control Win -> K1_AQUEC=", s["flags"]["K1_AQUEC"], "estado=", s["state"])

# O Ladder decide: injeta emergencia logica de teste na planta simulada -> programa deve travar falha e abrir K1
post("/api/demo/fault", {"fault": "estop_test", "on": True})
s = wait(lambda s: s["state"] == "FALHA_TRAVADA" and not s["flags"]["K1_AQUEC"], 15, "FALHA_TRAVADA e K1 aberto")
print("4) Ladder travou a falha e abriu K1; causas latched:", s["latched_causes"])
post("/api/demo/fault", {"fault": "estop_test", "on": False})
time.sleep(1.5)
post("/api/command", {"name": "BT_RESET"})
s = wait(lambda s: s["state"] != "FALHA_TRAVADA", 15, "reset condicionado")
print("5) reset aceito pelo programa somente apos a causa sumir; estado:", s["state"])
print("CP3 OK: ida e volta real HMI -> FastAPI -> OPC UA -> Ladder -> HMI")
