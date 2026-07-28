"""OKX Futures/SWAP read-only telemetry surface for Pre-Economic evidence session v1.

Reuses ``OkxPublicMarketDataClientV1`` (public REST, no credentials, no orders).
Never exposes trading methods. BTC and Spot are rejected.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol

from src.ops.okx_public_market_data_client_v1 import (
    OkxPublicMarketDataClientError,
    OkxPublicMarketDataClientV1,
)
from src.ops.pre_economic_zero_order_evidence_session_authorization_v1 import (
    MARKET_TYPE_SWAP,
    VENUE_OKX,
    assert_instrument_allowed,
    AuthorizationContractError,
)

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_OKX_READONLY_TELEMETRY_V1=true"
CAPABILITY_ID = "PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_SESSION_AUTHORIZATION_AND_EXECUTION"

# Order-shaped method names that must never be present on the client surface.
FORBIDDEN_CLIENT_METHODS = frozenset(
    {
        "place_order",
        "order",
        "cancel_order",
        "amend_order",
        "close_position",
        "set_leverage",
        "transfer",
        "submit_algo",
        "place_algo_order",
        "batch_orders",
        "private_post",
        "trade",
        "execute",
    }
)


class TelemetryError(RuntimeError):
    """Read-only telemetry failure."""


class MarketDataFetcher(Protocol):
    def get_json(self, path: str, params: Mapping[str, str]) -> Any: ...


@dataclass
class TelemetrySnapshotV1:
    connection_status: str
    venue: str
    market_type: str
    instrument_id: str
    exchange_time: Optional[str]
    local_receive_time: float
    sequence: int
    freshness_seconds: float
    stale: bool
    disconnect_count: int
    reconnect_count: int
    rate_limit_events: int
    transport_errors: int
    latency_ms: float
    session_uptime_seconds: float
    data_gap_events: int
    clock_drift_seconds: float
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TelemetrySummaryV1:
    venue: str
    market_type: str
    instrument_id: str
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    disconnect_count: int = 0
    reconnect_count: int = 0
    rate_limit_events: int = 0
    transport_errors: int = 0
    data_gap_events: int = 0
    stale_events: int = 0
    max_clock_drift_seconds: float = 0.0
    last_connection_status: str = "DISCONNECTED"
    unresolved_integrity_violation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assert_client_read_only(client: Any) -> None:
    """Fail-closed if client exposes order-capable methods."""

    for name in FORBIDDEN_CLIENT_METHODS:
        if hasattr(client, name) and callable(getattr(client, name)):
            raise TelemetryError(f"ORDER_CAPABLE_METHOD_PRESENT:{name}")
    # Public client must not carry credentials.
    for attr in ("api_key", "secret", "passphrase", "apiKey", "secret_key"):
        if hasattr(client, attr) and getattr(client, attr):
            raise TelemetryError(f"CREDENTIAL_ATTRIBUTE_PRESENT:{attr}")


def build_default_okx_public_client(
    *,
    fetcher: Optional[Callable[[str, float], tuple[int, bytes]]] = None,
) -> OkxPublicMarketDataClientV1:
    client = OkxPublicMarketDataClientV1(fetcher=fetcher)
    assert_client_read_only(client)
    return client


@dataclass
class OkxFuturesReadOnlyTelemetryV1:
    """Bounded observation loop over public mark-price / tickers."""

    instrument_id: str
    market_type: str = MARKET_TYPE_SWAP
    venue: str = VENUE_OKX
    allowlist: tuple[str, ...] = ("ETH-USDT-SWAP",)
    stale_threshold_seconds: float = 5.0
    client: Optional[MarketDataFetcher] = None
    clock: Callable[[], float] = time.time
    monotonic: Callable[[], float] = time.monotonic

    disconnect_count: int = 0
    reconnect_count: int = 0
    rate_limit_events: int = 0
    transport_errors: int = 0
    data_gap_events: int = 0
    stale_events: int = 0
    sequence: int = 0
    _session_start_mono: float = 0.0
    _last_ok_mono: Optional[float] = None
    _connected: bool = False
    _max_clock_drift: float = 0.0
    _snapshots: list[TelemetrySnapshotV1] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.venue != VENUE_OKX:
            raise TelemetryError(f"VENUE_FORBIDDEN:{self.venue}")
        try:
            assert_instrument_allowed(
                instrument_id=self.instrument_id,
                allowlist=self.allowlist,
                btc_forbidden=True,
                spot_forbidden=True,
                market_type=self.market_type,
            )
        except AuthorizationContractError as exc:
            raise TelemetryError(str(exc)) from exc
        if self.client is None:
            self.client = build_default_okx_public_client()
        assert_client_read_only(self.client)
        self._session_start_mono = float(self.monotonic())

    def poll_once(self) -> TelemetrySnapshotV1:
        assert self.client is not None
        local_start = float(self.clock())
        mono_start = float(self.monotonic())
        exchange_time: Optional[str] = None
        status = "CONNECTED"
        detail = "ok"
        latency_ms = 0.0
        freshness = 0.0
        drift = 0.0
        try:
            envelope = self.client.get_json(
                "/api/v5/public/mark-price",
                {"instId": self.instrument_id, "instType": self.market_type},
            )
            if not self._connected:
                if self.disconnect_count > 0:
                    self.reconnect_count += 1
                self._connected = True
            latency_ms = max(0.0, (float(self.monotonic()) - mono_start) * 1000.0)
            exchange_time = getattr(envelope, "provider_timestamp", None)
            if exchange_time is None and isinstance(envelope, dict):
                exchange_time = envelope.get("provider_timestamp")
            # Clock drift indicator: local receive vs capture start if available.
            captured = getattr(envelope, "captured_at", None)
            if captured is None and isinstance(envelope, dict):
                captured = envelope.get("captured_at")
            # Without parsed provider epoch, drift stays 0 unless mock injects it.
            self._last_ok_mono = float(self.monotonic())
        except OkxPublicMarketDataClientError as exc:
            msg = str(exc)
            self.transport_errors += 1
            if "RATE_LIMIT" in msg:
                self.rate_limit_events += 1
            if self._connected:
                self.disconnect_count += 1
                self._connected = False
                self.data_gap_events += 1
            status = "DISCONNECTED"
            detail = msg
        except Exception as exc:  # noqa: BLE001
            self.transport_errors += 1
            if self._connected:
                self.disconnect_count += 1
                self._connected = False
                self.data_gap_events += 1
            status = "ERROR"
            detail = f"TRANSPORT:{exc}"

        now_mono = float(self.monotonic())
        if self._last_ok_mono is not None:
            freshness = max(0.0, now_mono - self._last_ok_mono)
        else:
            freshness = max(0.0, now_mono - self._session_start_mono)
        stale = freshness > float(self.stale_threshold_seconds)
        if stale:
            self.stale_events += 1
        self.sequence += 1
        self._max_clock_drift = max(self._max_clock_drift, abs(drift))
        snap = TelemetrySnapshotV1(
            connection_status=status,
            venue=self.venue,
            market_type=self.market_type,
            instrument_id=self.instrument_id,
            exchange_time=exchange_time,
            local_receive_time=local_start,
            sequence=self.sequence,
            freshness_seconds=freshness,
            stale=stale,
            disconnect_count=self.disconnect_count,
            reconnect_count=self.reconnect_count,
            rate_limit_events=self.rate_limit_events,
            transport_errors=self.transport_errors,
            latency_ms=latency_ms,
            session_uptime_seconds=max(0.0, now_mono - self._session_start_mono),
            data_gap_events=self.data_gap_events,
            clock_drift_seconds=drift,
            detail=detail,
        )
        self._snapshots.append(snap)
        return snap

    def summary(self) -> TelemetrySummaryV1:
        unresolved = (
            self.stale_events > 0 and (not self._connected or self.data_gap_events > 0)
        ) or (self.transport_errors > 0 and self.disconnect_count > self.reconnect_count)
        return TelemetrySummaryV1(
            venue=self.venue,
            market_type=self.market_type,
            instrument_id=self.instrument_id,
            snapshots=[s.to_dict() for s in self._snapshots],
            disconnect_count=self.disconnect_count,
            reconnect_count=self.reconnect_count,
            rate_limit_events=self.rate_limit_events,
            transport_errors=self.transport_errors,
            data_gap_events=self.data_gap_events,
            stale_events=self.stale_events,
            max_clock_drift_seconds=self._max_clock_drift,
            last_connection_status="CONNECTED" if self._connected else "DISCONNECTED",
            unresolved_integrity_violation=bool(unresolved),
        )


@dataclass
class SimulatedOkxTelemetryClientV1:
    """Test-only client: no network, no order methods."""

    responses: list[Any] = field(default_factory=list)
    fail_with: Optional[Exception] = None
    _idx: int = 0

    def get_json(self, path: str, params: Mapping[str, str]) -> Any:
        if self.fail_with is not None:
            raise self.fail_with
        if self._idx >= len(self.responses):
            # Default healthy envelope-like object.
            return _SimEnvelope(
                provider_timestamp="1970-01-01T00:00:00Z", captured_at="1970-01-01T00:00:00Z"
            )
        item = self.responses[self._idx]
        self._idx += 1
        return item


@dataclass
class _SimEnvelope:
    provider_timestamp: Optional[str] = None
    captured_at: Optional[str] = None
