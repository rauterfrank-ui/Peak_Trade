"""Production OKX EEA public WebSocket network connector (observation-only, no auth)."""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    DEFAULT_HEARTBEAT_SECONDS,
    EEA_PUBLIC_WS_BASE,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    mechanical_verify_eea_public_ws_base_v1,
    load_ratified_eea_public_ws_binding_v1,
)

DEFAULT_CONNECT_TIMEOUT_SECONDS = 10.0
DEFAULT_INBOX_MAXSIZE = 2048


@dataclass
class PublicWsNetworkConnectorStateV1:
    connected: bool = False
    subscribed: bool = False
    last_error: Optional[str] = None
    last_connect_at_monotonic: float = 0.0
    last_message_at_monotonic: float = 0.0
    messages_received: int = 0
    disconnect_requested: bool = False


@dataclass
class OkxEeaPublicWsNetworkConnectorV1:
    """Thread-backed websocket-client connector implementing WsConnectorV1."""

    connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS
    inbox_maxsize: int = DEFAULT_INBOX_MAXSIZE
    sleep: Callable[[float], None] = time.sleep
    state: PublicWsNetworkConnectorStateV1 = field(default_factory=PublicWsNetworkConnectorStateV1)
    _inbox: queue.Queue[dict[str, Any]] = field(default_factory=lambda: queue.Queue(maxsize=2048))
    _ws_app: Any = field(default=None, repr=False)
    _thread: Optional[threading.Thread] = field(default=None, repr=False)
    _ws_url: str = field(default="", repr=False)
    _pending_subscribe_args: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _send_lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def connect(self, ws_base_url: str) -> None:
        mechanical_verify_eea_public_ws_base_v1(ws_base_url)
        if ws_base_url != EEA_PUBLIC_WS_BASE:
            # Fail closed on drift from ratified constant unless caller passed verified URL.
            binding = load_ratified_eea_public_ws_binding_v1()
            if ws_base_url != binding.ws_base_url:
                raise ValueError("WS_BASE_URL_DRIFT_FROM_RATIFIED_EEA_PUBLIC")
        self.state.disconnect_requested = False
        self.state.last_error = None
        self._ws_url = ws_base_url
        self._start_thread()
        deadline = time.monotonic() + self.connect_timeout_seconds
        while time.monotonic() < deadline:
            if self.state.connected:
                self.state.last_connect_at_monotonic = time.monotonic()
                return
            if self.state.last_error:
                raise ConnectionError(self.state.last_error)
            self.sleep(0.05)
        self.disconnect()
        raise TimeoutError("PUBLIC_WS_CONNECT_TIMEOUT")

    def subscribe(self, args: list[dict[str, Any]]) -> None:
        self._pending_subscribe_args = list(args)
        payload = {"op": "subscribe", "args": args}
        self._send_json(payload)
        self.state.subscribed = True

    def disconnect(self) -> None:
        self.state.disconnect_requested = True
        self.state.connected = False
        self.state.subscribed = False
        app = self._ws_app
        if app is not None:
            try:
                app.close()
            except Exception:
                pass
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=5.0)
        self._thread = None
        self._ws_app = None

    def message_source(self) -> Iterable[Mapping[str, Any]]:
        """Drain pending decoded OKX public events for PublicWsTransportV1."""
        while True:
            try:
                item = self._inbox.get_nowait()
            except queue.Empty:
                break
            yield item

    def connection_observable_v1(self) -> dict[str, Any]:
        return {
            "schema_name": "okx_eea_public_ws_network_connector_state.v1",
            "connected": self.state.connected,
            "subscribed": self.state.subscribed,
            "last_error": self.state.last_error,
            "messages_received": self.state.messages_received,
            "ws_url_host": EEA_PUBLIC_WS_BASE.split("/")[2],
        }

    def _start_thread(self) -> None:
        import websocket  # websocket-client (sync)

        ready = threading.Event()
        err_holder: list[str] = []

        def on_open(wsapp: Any) -> None:
            self.state.connected = True
            ready.set()
            if self._pending_subscribe_args:
                wsapp.send(json.dumps({"op": "subscribe", "args": self._pending_subscribe_args}))

        def on_message(_wsapp: Any, message: str) -> None:
            self.state.last_message_at_monotonic = time.monotonic()
            self.state.messages_received += 1
            try:
                parsed = json.loads(message)
            except json.JSONDecodeError:
                return
            if isinstance(parsed, dict):
                self._enqueue(parsed)

        def on_error(_wsapp: Any, error: Any) -> None:
            err_holder.append(str(error))
            self.state.last_error = str(error)

        def on_close(_wsapp: Any, _status: Any, _msg: Any) -> None:
            self.state.connected = False

        def run() -> None:
            wsapp = websocket.WebSocketApp(
                self._ws_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            self._ws_app = wsapp
            wsapp.run_forever(
                ping_interval=DEFAULT_HEARTBEAT_SECONDS,
                ping_timeout=max(1.0, DEFAULT_HEARTBEAT_SECONDS - 1.0),
            )

        self._thread = threading.Thread(target=run, name="okx-eea-public-ws", daemon=True)
        self._thread.start()
        if not ready.wait(timeout=self.connect_timeout_seconds):
            if err_holder:
                self.state.last_error = err_holder[0]
            return

    def _send_json(self, payload: Mapping[str, Any]) -> None:
        raw = json.dumps(payload)
        with self._send_lock:
            app = self._ws_app
            if app is None or not self.state.connected:
                return
            app.send(raw)

    def _enqueue(self, item: dict[str, Any]) -> None:
        try:
            self._inbox.put_nowait(item)
        except queue.Full:
            try:
                _ = self._inbox.get_nowait()
            except queue.Empty:
                pass
            try:
                self._inbox.put_nowait(item)
            except queue.Full:
                self.state.last_error = "INBOX_OVERFLOW"


def create_ratified_eea_public_ws_network_connector_v1() -> OkxEeaPublicWsNetworkConnectorV1:
    """Factory bound to CURRENT ratified EEA public WS base (no credential surfaces)."""
    load_ratified_eea_public_ws_binding_v1()
    return OkxEeaPublicWsNetworkConnectorV1()
