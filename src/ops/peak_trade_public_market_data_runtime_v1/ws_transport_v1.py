"""Injectable OKX EEA Public WebSocket transport (no credentials)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional, Protocol

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    DEFAULT_BACKOFF_INITIAL_SECONDS,
    DEFAULT_BACKOFF_MAX_SECONDS,
    DEFAULT_HEARTBEAT_SECONDS,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_binding_v1 import (
    OkxEeaPublicWsBindingV1,
    PublicWsBindingError,
    load_ratified_eea_public_ws_binding_v1,
)


class PublicWsTransportError(RuntimeError):
    pass


WsMessageSource = Callable[[], Iterable[Mapping[str, Any]]]


class WsConnectorV1(Protocol):
    def connect(self, ws_base_url: str) -> None: ...
    def subscribe(self, args: list[dict[str, Any]]) -> None: ...
    def disconnect(self) -> None: ...


@dataclass
class PublicWsSessionStateV1:
    connected: bool = False
    subscribed: bool = False
    reconnect_count: int = 0
    last_heartbeat_at: float = 0.0
    seen_message_ids: set[str] = field(default_factory=set)
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PublicWsTransportV1:
    binding: OkxEeaPublicWsBindingV1
    connector: WsConnectorV1
    message_source: WsMessageSource
    venue_native_id: str
    sleep: Callable[[float], None] = time.sleep
    max_reconnect: int = DEFAULT_MAX_RECONNECT_ATTEMPTS
    heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS
    state: PublicWsSessionStateV1 = field(default_factory=PublicWsSessionStateV1)

    @classmethod
    def from_ratified_binding(
        cls,
        *,
        connector: WsConnectorV1,
        message_source: WsMessageSource,
        venue_native_id: str,
    ) -> "PublicWsTransportV1":
        return cls(
            binding=load_ratified_eea_public_ws_binding_v1(),
            connector=connector,
            message_source=message_source,
            venue_native_id=venue_native_id,
        )

    def connect_and_subscribe(self) -> None:
        self.connector.connect(self.binding.ws_base_url)
        self.state.connected = True
        args = self.binding.subscribe_args_for_instrument(self.venue_native_id)
        self.connector.subscribe(args)
        self.state.subscribed = True
        self.state.last_heartbeat_at = time.monotonic()
        self.state.events.append({"event": "ws_subscribed", "channels": len(args)})

    def reconnect_resubscribe(self) -> None:
        if self.state.reconnect_count >= self.max_reconnect:
            raise PublicWsTransportError("RECONNECT_BUDGET_EXCEEDED")
        backoff = min(
            DEFAULT_BACKOFF_MAX_SECONDS,
            DEFAULT_BACKOFF_INITIAL_SECONDS * (2**self.state.reconnect_count),
        )
        self.sleep(backoff)
        self.connector.disconnect()
        self.state.reconnect_count += 1
        self.connect_and_subscribe()
        self.state.events.append({"event": "ws_reconnected", "attempt": self.state.reconnect_count})

    def poll_messages(self) -> list[Mapping[str, Any]]:
        if not self.state.connected:
            raise PublicWsTransportError("WS_NOT_CONNECTED")
        out: list[Mapping[str, Any]] = []
        for raw in self.message_source():
            msg_id = str(raw.get("msg_id") or raw.get("tradeId") or json.dumps(raw, sort_keys=True))
            if msg_id in self.state.seen_message_ids:
                tagged = dict(raw)
                tagged["_duplicate"] = True
                out.append(tagged)
                continue
            self.state.seen_message_ids.add(msg_id)
            out.append(raw)
        now = time.monotonic()
        if now - self.state.last_heartbeat_at > self.heartbeat_seconds:
            self.state.last_heartbeat_at = now
            self.state.events.append({"event": "heartbeat", "op": self.binding.heartbeat_op})
        return out

    def close(self) -> None:
        self.connector.disconnect()
        self.state.connected = False
        self.state.subscribed = False


def assert_ws_session_reconnect_owned_v1(exc: BaseException) -> bool:
    return bool(getattr(exc, "session_reconnect_owned", False))
