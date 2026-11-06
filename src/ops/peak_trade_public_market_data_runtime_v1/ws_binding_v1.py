"""Mechanical OKX EEA Public WebSocket binding (fail-closed on drift)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    EEA_PUBLIC_WS_BASE,
    FORBIDDEN_WS_AUTHORITY_HOSTS,
)


class PublicWsBindingError(ValueError):
    """WS host/channel binding rejected."""


@dataclass(frozen=True)
class OkxEeaPublicWsBindingV1:
    ws_base_url: str
    public_channel_inst_tickers: str
    public_channel_trades: str
    public_channel_books5: str
    heartbeat_op: str

    def subscribe_args_for_instrument(self, venue_native_id: str) -> list[dict[str, Any]]:
        return [
            {"channel": self.public_channel_inst_tickers, "instId": venue_native_id},
            {"channel": self.public_channel_trades, "instId": venue_native_id},
            {"channel": self.public_channel_books5, "instId": venue_native_id},
        ]


def mechanical_verify_eea_public_ws_base_v1(ws_base_url: str) -> None:
    parsed = urlparse(ws_base_url)
    host = (parsed.hostname or "").lower()
    if host in FORBIDDEN_WS_AUTHORITY_HOSTS:
        raise PublicWsBindingError(f"FORBIDDEN_HISTORICAL_WS_HOST:{host}")
    if parsed.scheme != "wss":
        raise PublicWsBindingError(f"SCHEME_FORBIDDEN:{parsed.scheme}")
    if not host.endswith("okx.com"):
        raise PublicWsBindingError(f"HOST_NOT_OKX:{host}")
    if "/ws/v5/public" not in (parsed.path or ""):
        raise PublicWsBindingError("PATH_NOT_V5_PUBLIC")


def forbid_wseeapap_as_authority_v1(host: str) -> None:
    if host.strip().lower() == "wseeapap.okx.com":
        raise PublicWsBindingError("WSEEAPAP_NOT_AUTHORITY")


def load_ratified_eea_public_ws_binding_v1() -> OkxEeaPublicWsBindingV1:
    mechanical_verify_eea_public_ws_base_v1(EEA_PUBLIC_WS_BASE)
    return OkxEeaPublicWsBindingV1(
        ws_base_url=EEA_PUBLIC_WS_BASE,
        public_channel_inst_tickers="tickers",
        public_channel_trades="trades",
        public_channel_books5="books5",
        heartbeat_op="ping",
    )
