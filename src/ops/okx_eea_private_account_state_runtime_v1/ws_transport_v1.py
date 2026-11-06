"""Injectable observation-only Private WebSocket transport."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Protocol

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    DEFAULT_BACKOFF_INITIAL_SECONDS,
    DEFAULT_BACKOFF_MAX_SECONDS,
    DEFAULT_HEARTBEAT_SECONDS,
    DEFAULT_MAX_RECONNECT_ATTEMPTS,
    DEDICATED_FILLS_WS_OPTIONAL,
    FORBIDDEN_WS_MUTATION_OPS,
)
from src.ops.okx_eea_private_account_state_runtime_v1.ws_binding_v1 import (
    OkxEeaPrivateWsBindingV1,
    load_ratified_eea_private_ws_binding_v1,
)


class PrivateWsTransportError(RuntimeError):
    pass


def assert_ws_outbound_op_allowed_v1(op: str) -> None:
    normalized = op.strip().lower()
    if normalized in FORBIDDEN_WS_MUTATION_OPS:
        raise ValueError(f"WS_MUTATION_OP_FORBIDDEN:{op}")
    allowed = {"login", "subscribe", "unsubscribe", "ping", "pong"}
    if normalized not in allowed:
        raise ValueError(f"WS_OUTBOUND_OP_NOT_ALLOWLISTED:{op}")


WsMessageSource = Callable[[], Iterable[Mapping[str, Any]]]


class PrivateWsConnectorV1(Protocol):
    def connect(self, ws_base_url: str) -> None: ...
    def login(self, login_payload: Mapping[str, Any]) -> None: ...
    def subscribe(self, args: list[dict[str, Any]]) -> None: ...
    def send_op(self, op: str, payload: Mapping[str, Any] | None = None) -> None: ...
    def disconnect(self) -> None: ...


@dataclass
class PrivateWsSessionStateV1:
    connected: bool = False
    logged_in: bool = False
    subscribed: bool = False
    reconnect_count: int = 0
    last_heartbeat_at: float = 0.0
    fills_channel_active: bool = False
    fills_channel_rejected: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class PrivateWsTransportV1:
    binding: OkxEeaPrivateWsBindingV1
    connector: PrivateWsConnectorV1
    message_source: WsMessageSource
    login_payload: Mapping[str, Any]
    sleep: Callable[[float], None] = time.sleep
    max_reconnect: int = DEFAULT_MAX_RECONNECT_ATTEMPTS
    heartbeat_seconds: float = DEFAULT_HEARTBEAT_SECONDS
    state: PrivateWsSessionStateV1 = field(default_factory=PrivateWsSessionStateV1)

    @classmethod
    def from_ratified_binding(
        cls,
        *,
        connector: PrivateWsConnectorV1,
        message_source: WsMessageSource,
        login_payload: Mapping[str, Any],
    ) -> "PrivateWsTransportV1":
        return cls(
            binding=load_ratified_eea_private_ws_binding_v1(),
            connector=connector,
            message_source=message_source,
            login_payload=login_payload,
        )

    def connect_login_subscribe(self, *, include_optional_fills: bool = True) -> None:
        self.connector.connect(self.binding.ws_base_url)
        self.state.connected = True
        assert_ws_outbound_op_allowed_v1("login")
        self.connector.login(self.login_payload)
        self.state.logged_in = True
        args = self.binding.subscribe_args_v1(
            include_optional_fills=include_optional_fills and DEDICATED_FILLS_WS_OPTIONAL
        )
        assert_ws_outbound_op_allowed_v1("subscribe")
        try:
            self.connector.subscribe(args)
            self.state.subscribed = True
            if include_optional_fills:
                self.state.fills_channel_active = any(
                    a.get("channel") == self.binding.optional_fills_channel for a in args
                )
        except Exception as exc:
            if include_optional_fills and DEDICATED_FILLS_WS_OPTIONAL:
                self.state.fills_channel_rejected = True
                args = self.binding.subscribe_args_v1(include_optional_fills=False)
                self.connector.subscribe(args)
                self.state.subscribed = True
            else:
                raise PrivateWsTransportError("WS_SUBSCRIBE_FAILED") from exc
        self.state.last_heartbeat_at = time.monotonic()
        self.state.events.append({"event": "private_ws_subscribed", "channels": len(args)})

    def reconnect_resubscribe(self) -> None:
        if self.state.reconnect_count >= self.max_reconnect:
            raise PrivateWsTransportError("RECONNECT_BUDGET_EXCEEDED")
        backoff = min(
            DEFAULT_BACKOFF_MAX_SECONDS,
            DEFAULT_BACKOFF_INITIAL_SECONDS * (2**self.state.reconnect_count),
        )
        self.sleep(backoff)
        self.connector.disconnect()
        self.state.reconnect_count += 1
        self.connect_login_subscribe(include_optional_fills=not self.state.fills_channel_rejected)
        self.state.events.append(
            {"event": "private_ws_reconnected", "attempt": self.state.reconnect_count}
        )

    def poll_messages(self) -> list[Mapping[str, Any]]:
        if not self.state.connected or not self.state.logged_in:
            raise PrivateWsTransportError("WS_NOT_AUTHENTICATED")
        out: list[Mapping[str, Any]] = []
        for raw in self.message_source():
            msg_id = str(
                raw.get("event_id")
                or raw.get("ordId")
                or raw.get("tradeId")
                or json.dumps(raw, sort_keys=True)
            )
            tagged = dict(raw)
            out.append(tagged)
        now = time.monotonic()
        if now - self.state.last_heartbeat_at > self.heartbeat_seconds:
            assert_ws_outbound_op_allowed_v1("ping")
            self.connector.send_op("ping", {})
            self.state.last_heartbeat_at = now
            self.state.events.append({"event": "heartbeat", "op": self.binding.heartbeat_op})
        return out

    def close(self) -> None:
        self.connector.disconnect()
        self.state.connected = False
        self.state.subscribed = False
        self.state.logged_in = False
