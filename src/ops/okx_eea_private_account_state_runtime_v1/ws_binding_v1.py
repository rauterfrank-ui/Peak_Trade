"""Mechanical OKX EEA Private WebSocket binding (observation-only; fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    DEMO_ONLY_PRIVATE_WS_HOST,
    EEA_PRIVATE_WS_BASE,
    FORBIDDEN_PRODUCTION_PRIVATE_WS_HOSTS,
    OBSERVATION_WS_CHANNELS_V1,
    OPTIONAL_FILLS_WS_CHANNEL,
)


class PrivateWsBindingError(ValueError):
    """Private WS host/channel binding rejected."""


@dataclass(frozen=True)
class OkxEeaPrivateWsBindingV1:
    ws_base_url: str
    approved_channels: frozenset[str]
    optional_fills_channel: str
    heartbeat_op: str
    login_required: bool

    def subscribe_args_v1(self, *, include_optional_fills: bool = False) -> list[dict[str, Any]]:
        channels = sorted(OBSERVATION_WS_CHANNELS_V1)
        if include_optional_fills:
            channels = sorted(set(channels) | {OPTIONAL_FILLS_WS_CHANNEL})
        return [{"channel": ch} for ch in channels]


def mechanical_verify_eea_private_ws_base_v1(ws_base_url: str) -> None:
    parsed = urlparse(ws_base_url)
    host = (parsed.hostname or "").lower()
    if host in FORBIDDEN_PRODUCTION_PRIVATE_WS_HOSTS:
        raise PrivateWsBindingError(f"FORBIDDEN_DEMO_ONLY_WS_HOST_FOR_PRODUCTION:{host}")
    if parsed.scheme != "wss":
        raise PrivateWsBindingError(f"SCHEME_FORBIDDEN:{parsed.scheme}")
    if not host.endswith("okx.com"):
        raise PrivateWsBindingError(f"HOST_NOT_OKX:{host}")
    if "/ws/v5/private" not in (parsed.path or ""):
        raise PrivateWsBindingError("PATH_NOT_V5_PRIVATE")


def forbid_wseeapap_as_production_authority_v1(host: str) -> None:
    normalized = host.strip().lower()
    if (
        normalized == DEMO_ONLY_PRIVATE_WS_HOST
        or normalized in FORBIDDEN_PRODUCTION_PRIVATE_WS_HOSTS
    ):
        raise PrivateWsBindingError("WSEEAPAP_DEMO_ONLY_NOT_PRODUCTION_AUTHORITY")


def load_ratified_eea_private_ws_binding_v1() -> OkxEeaPrivateWsBindingV1:
    mechanical_verify_eea_private_ws_base_v1(EEA_PRIVATE_WS_BASE)
    return OkxEeaPrivateWsBindingV1(
        ws_base_url=EEA_PRIVATE_WS_BASE,
        approved_channels=OBSERVATION_WS_CHANNELS_V1,
        optional_fills_channel=OPTIONAL_FILLS_WS_CHANNEL,
        heartbeat_op="ping",
        login_required=True,
    )
