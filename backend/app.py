"""API do SCADA (modo DEMO). Uso: uvicorn backend.app:app --port 8000

A HMI envia SOLICITACOES; o estado exibido vem do programa (aqui: Ladder gerado em avaliador, rotulado DEMO).
Nao ha rota que acione motor/SSR diretamente."""
from __future__ import annotations

import asyncio
import contextlib
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .engine import DemoEngine
from .transport import DemoTransport, OpcUaTransport, PlcLinkError

TICK_S = 0.1


class Command(BaseModel):
    name: str


class Setpoint(BaseModel):
    key: str
    value: float


class Fault(BaseModel):
    fault: str
    on: bool = True


class RobotState(BaseModel):
    moving: bool | None = None
    cmd: bool | None = None
    auto: bool | None = None


def build_engine() -> DemoEngine:
    """LFAM_MODE=demo (padrao) ou plc. No modo plc as credenciais OPC UA vem SOMENTE do ambiente e nunca sao registradas."""
    if os.environ.get("LFAM_MODE", "demo").lower() == "plc":
        t = OpcUaTransport(os.environ.get("LFAM_OPCUA_URL", "opc.tcp://localhost:4840"), os.environ.get("LFAM_OPCUA_USER"),
                           os.environ.get("LFAM_OPCUA_PASSWORD"), os.environ.get("LFAM_OPCUA_ROOT"))
        return DemoEngine(transport=t)
    return DemoEngine(transport=DemoTransport())


def create_app(engine: DemoEngine | None = None, autostart: bool = True) -> FastAPI:
    eng = engine or build_engine()
    plc = eng.transport.mode == "PLC"
    speed = 1.0 if plc else float(os.environ.get("LFAM_TIME_SCALE", "1"))   # PLC roda em tempo real (o CLP tem o proprio ciclo)

    async def loop():
        while True:
            if plc and not eng.transport.connected:
                try:
                    await asyncio.to_thread(eng.transport.connect)
                    eng.link_error = ""
                except PlcLinkError as e:
                    eng.link_error = str(e)
                    eng.pulses.clear()
                    await asyncio.sleep(3.0)             # recuo entre tentativas; nenhum comando e reenviado
                continue
            for _ in range(max(1, int(round(speed)))):
                if plc:
                    await asyncio.to_thread(eng.step, TICK_S)
                else:
                    eng.step(TICK_S)
            await asyncio.sleep(TICK_S)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI):
        task = asyncio.create_task(loop()) if autostart else None
        yield
        if task:
            task.cancel()
        if hasattr(eng.transport, "close"):
            eng.transport.close()

    app = FastAPI(title="LFAM SCADA API (DEMO)", lifespan=lifespan)
    app.state.engine = eng

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": eng.transport.mode, "plc_connected": plc and eng.transport.healthy, "link_error": eng.link_error}

    @app.get("/api/state")
    def state():
        return eng.snapshot()

    @app.post("/api/command")
    def command(c: Command):
        ok, msg = eng.request(c.name)
        return {"accepted": ok, "message": msg, "confirmed": False}

    @app.post("/api/setpoint")
    def setpoint(s: Setpoint):
        ok, msg = eng.set_setpoint(s.key, s.value)
        return {"accepted": ok, "message": msg}

    @app.post("/api/demo/fault")
    def fault(f: Fault):
        ok, msg = eng.inject(f.fault, f.on)
        return {"accepted": ok, "message": msg, "mode": eng.transport.mode, "target": "planta simulada"}

    @app.post("/api/demo/robot")
    def robot(r: RobotState):
        eng.set_robot(r.moving, r.cmd, r.auto)
        return {"accepted": True, "mode": "DEMO"}

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        await sock.accept()
        try:
            while True:
                await sock.send_json(eng.snapshot())
                await asyncio.sleep(0.5)
        except WebSocketDisconnect:
            return

    return app


app = create_app()
