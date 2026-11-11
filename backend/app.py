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


def create_app(engine: DemoEngine | None = None, autostart: bool = True) -> FastAPI:
    eng = engine or DemoEngine()
    speed = float(os.environ.get("LFAM_TIME_SCALE", "1"))

    async def loop():
        while True:
            for _ in range(max(1, int(round(speed)))):
                eng.step(TICK_S)
            await asyncio.sleep(TICK_S)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI):
        task = asyncio.create_task(loop()) if autostart else None
        yield
        if task:
            task.cancel()

    app = FastAPI(title="LFAM SCADA API (DEMO)", lifespan=lifespan)
    app.state.engine = eng

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "DEMO", "plc_connected": False}

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
        return {"accepted": ok, "message": msg, "mode": "DEMO"}

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
