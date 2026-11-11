"""Transportes entre o motor do SCADA e o programa Ladder.

- DemoTransport : executa o programa gerado em um AVALIADOR Python (modo DEMO, simulado).
- OpcUaTransport: le e escreve variaveis do programa em execucao no CODESYS Control Win via OPC UA (modo PLC).

Regras do modo PLC: so valores efetivamente lidos do runtime sao usados; sem heartbeat novo o dado e marcado obsoleto;
perda de conexao descarta pulsos de comando pendentes (nunca reenvia comando automaticamente); credenciais vem do
ambiente e NUNCA sao registradas em log.
"""
from __future__ import annotations

import logging
import time
from typing import Protocol

from codesys.generator import program as PRG
from codesys.generator.ld import scan

log = logging.getLogger("lfam.transport")
READ_BATCH = 50

# asyncua em DEBUG imprime a ativacao de sessao COM a senha em claro: nunca permitir abaixo de WARNING.
for _name in ("asyncua", "asyncua.client", "asyncua.uaprotocol", "asyncua.common", "asyncua.server", "asyncua.client.ua_client"):
    logging.getLogger(_name).setLevel(logging.WARNING)

# Variaveis que o backend/simulador ESCREVEM no programa (sensores virtuais, botoes, setpoints). O resto e so leitura.
WRITABLE = (
    {f"TT_Z{z}_RAW" for z in range(1, 6)}
    | {"PT_FUNDIDO_RAW", "TT_SUBSTRATO_RAW", "TT_ZSR", "TT_RESF", "SEG_OK", "MOT_SOBRETEMP", "DISJ_AQUEC", "BT_DESLIGA", "BT_AQUEC",
       "BT_LIGA", "BT_RESET", "SEL_AUTO", "ROBO_CMD_EXTR", "ROBO_EM_MOV", "SECADOR_OK", "INV_PRONTO", "INV_FALHA", "FUNIL_BAIXO",
       "VENT_OK", "K1_CONF", "SP_RPM_OPERADOR", "SP_IR_C", "HMI_RESET_LOTES"}
    | {f"SP_Z{z}" for z in range(1, 6)}
)
HEARTBEAT = "PLC_HEARTBEAT"
STALE_S = 2.0
_SKIP_TYPES = {"TON", "Util.PID", "PID", "CTU", "R_TRIG", "TIME"}


class Transport(Protocol):
    mode: str

    def cycle(self, env_in: dict, dt: float) -> dict: ...
    @property
    def healthy(self) -> bool: ...


class DemoTransport:
    mode = "DEMO"
    healthy = True

    def cycle(self, env_in: dict, dt: float) -> dict:
        return scan(PRG.RUNGS, env_in, dt)

    def close(self) -> None:
        pass


class PlcLinkError(RuntimeError):
    pass


class OpcUaTransport:
    """Cliente OPC UA sincrono. `url` ex.: opc.tcp://localhost:4840. Mecanismo de DESENVOLVIMENTO ate haver servidor validado."""

    mode = "PLC"

    def __init__(self, url: str, username: str | None = None, password: str | None = None, root_hint: str | None = None,
                 timeout: float = 2.0, clock=time.monotonic, security: str | None = None,
                 cert_path: str | None = None, key_path: str | None = None):
        from asyncua.sync import Client  # import tardio: o modo DEMO nao precisa da biblioteca

        self._Client = Client
        self.url, self.username, self.password, self.timeout = url, username, password, timeout
        self.root_hint = root_hint
        # security ex.: "Basic256Sha256,SignAndEncrypt" (exige cert/chave do cliente; senha so segue por canal criptografado)
        self.security, self.cert_path, self.key_path = security, cert_path, key_path
        self._client = None
        self._nodes: dict = {}
        self._types = {k: t for k, t in PRG.variables().items() if t not in _SKIP_TYPES}
        self._hb_last = None
        self._hb_changed_at = 0.0
        self._clock = clock
        self.last_error = ""
        self.connected = False

    # ---------------------------------------------------------------- conexao
    def connect(self) -> None:
        self.close()
        c = self._Client(self.url, timeout=self.timeout)
        if self.security:
            c.set_security_string(f"{self.security},{self.cert_path},{self.key_path}")
            c.application_uri = "urn:lfam:backend"
        if self.username:
            c.set_user(self.username)
            c.set_password(self.password or "")
        try:
            c.connect()
            self._client = c
            self._resolve()
            self.connected = True
            self._hb_last, self._hb_changed_at = None, self._clock()
            self.last_error = ""
            log.info("OPC UA conectado a %s (%d variaveis mapeadas)", self.url, len(self._nodes))
        except Exception as e:  # noqa: BLE001
            self.connected = False
            self.last_error = f"{type(e).__name__}: {e}"
            try:
                c.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self._client = None
            raise PlcLinkError(self.last_error) from e

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.disconnect()
            except Exception:  # noqa: BLE001
                pass
        self._client, self.connected = None, False

    def _resolve(self) -> None:
        c = self._client
        root = None
        if self.root_hint:
            root = c.get_node(self.root_hint)
        else:
            root = self._find_program(c.nodes.objects, depth=0)
        if root is None:
            raise PlcLinkError("programa PLC_PRG nao encontrado no servidor OPC UA (confira a Symbol Configuration)")
        found = {}
        for ch in root.get_children():
            name = ch.read_browse_name().Name
            if name in self._types:
                found[name] = ch
        missing = sorted(k for k in WRITABLE | {HEARTBEAT} if k in self._types and k not in found)
        if missing:
            raise PlcLinkError("variaveis nao publicadas na Symbol Configuration: " + ", ".join(missing[:8]))
        self._nodes = found

    def _find_program(self, node, depth):
        if depth > 7:
            return None
        for ch in node.get_children():
            if ch.read_browse_name().Name == "PLC_PRG":
                return ch
            r = self._find_program(ch, depth + 1)
            if r is not None:
                return r
        return None

    # ---------------------------------------------------------------- ciclo
    @property
    def healthy(self) -> bool:
        return self.connected and (self._clock() - self._hb_changed_at) <= STALE_S

    def cycle(self, env_in: dict, dt: float) -> dict:
        if not self.connected:
            raise PlcLinkError(self.last_error or "sem conexao")
        from asyncua import ua

        try:
            writes, vals = [], []
            for k in WRITABLE:
                if k in env_in and k in self._nodes:
                    writes.append(self._nodes[k])
                    vals.append(ua.DataValue(self._variant(k, env_in[k])))
            if writes:
                self._write(writes, vals)
            names = list(self._nodes)
            values = []
            for i in range(0, len(names), READ_BATCH):  # o servidor limita operacoes por pedido (BadTooManyOperations)
                values += self._client.read_values([self._nodes[n] for n in names[i:i + READ_BATCH]])
        except Exception as e:  # noqa: BLE001
            self.last_error = f"{type(e).__name__}: {e}"
            self.close()     # libera ja o cliente e a thread do asyncua (nao espera a proxima reconexao)
            raise PlcLinkError(self.last_error) from e
        env = dict(zip(names, values))
        hb = env.get(HEARTBEAT)
        if hb != self._hb_last:
            self._hb_last, self._hb_changed_at = hb, self._clock()
        return env

    def _write(self, nodes, dvs) -> None:
        for n, dv in zip(nodes, dvs):
            n.write_value(dv)

    def _variant(self, name: str, value):
        from asyncua import ua

        t = self._types[name]
        if t == "BOOL":
            return ua.Variant(bool(value), ua.VariantType.Boolean)
        if t == "INT":
            return ua.Variant(int(value), ua.VariantType.Int16)
        if t == "WORD":
            return ua.Variant(int(value), ua.VariantType.UInt16)
        return ua.Variant(float(value), ua.VariantType.Float)
