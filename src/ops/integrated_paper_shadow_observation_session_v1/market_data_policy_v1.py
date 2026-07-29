"""OKX Futures market-data policy for Paper-Shadow Observation (offline).

No network. Callers supply ticks; policy validates futures-only, BTC/Spot
exclusion, and duplicate/gap/stale/disconnect/clock consistency.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.integrated_paper_shadow_observation_session_v1.constants_v1 import (
    MARKET_TYPE_FUTURES,
    VENUE_OKX,
)

MARKET_DATA_POLICY_ID = "ops.integrated_paper_shadow_observation_market_data_policy_v1"
MARKET_DATA_POLICY_VERSION = "v1"

_BITCOIN_FRAGMENTS = frozenset({"BTC", "XBT", "BITCOIN"})
_SPOT_FRAGMENTS = frozenset({"SPOT", "/EUR", "/USD", "/USDT"})


class MarketDataPolicyError(ValueError):
    """Fail-closed market-data policy error."""


@dataclass(frozen=True)
class MarketDataPolicyParamsV1:
    venue: str = VENUE_OKX
    market_type: str = MARKET_TYPE_FUTURES
    allowed_instruments: tuple[str, ...] = (PRODUCTION_INSTRUMENT_ID,)
    btc_forbidden: bool = True
    spot_forbidden: bool = True
    max_stale_seconds: float = 5.0
    max_gap_seconds: float = 10.0
    max_clock_skew_seconds: float = 30.0
    max_clock_drift_seconds: float = 30.0
    allow_duplicates: bool = False
    network_allowed: bool = False


@dataclass(frozen=True)
class ObservationMarketTickV1:
    instrument_id: str
    venue: str
    market_type: str
    sequence: int
    event_ts_unix: float
    receive_ts_unix: float
    mono_ts: float
    mid_price: float
    source: str = "caller_supplied_offline"


@dataclass
class MarketDataPolicyResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    accepted_tick_count: int = 0
    duplicate_count: int = 0
    gap_count: int = 0
    stale_count: int = 0
    disconnect_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_bitcoin(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    return any(frag in upper for frag in _BITCOIN_FRAGMENTS)


def _is_spot(instrument_id: str) -> bool:
    upper = instrument_id.upper()
    if "XPERP" in upper or upper.endswith("-PERP") or "SWAP" in upper:
        return False
    return any(frag in upper for frag in _SPOT_FRAGMENTS)


def validate_instrument_for_observation_v1(
    *,
    instrument_id: str,
    params: MarketDataPolicyParamsV1 | None = None,
) -> tuple[str, ...]:
    cfg = params or MarketDataPolicyParamsV1()
    blockers: list[str] = []
    inst = str(instrument_id or "").strip()
    if not inst:
        return ("INSTRUMENT_REQUIRED",)
    if cfg.btc_forbidden and _is_bitcoin(inst):
        blockers.append("BTC_INSTRUMENT_FORBIDDEN")
    if cfg.spot_forbidden and _is_spot(inst):
        blockers.append("SPOT_INSTRUMENT_FORBIDDEN")
    if cfg.allowed_instruments and inst not in cfg.allowed_instruments:
        blockers.append("INSTRUMENT_NOT_IN_ALLOWLIST")
    return tuple(blockers)


def evaluate_market_data_sequence_v1(
    ticks: Sequence[ObservationMarketTickV1],
    *,
    params: MarketDataPolicyParamsV1 | None = None,
    wall_now_unix: Optional[float] = None,
) -> MarketDataPolicyResultV1:
    """Validate an offline tick sequence. Does not fetch market data."""
    cfg = params or MarketDataPolicyParamsV1()
    result = MarketDataPolicyResultV1(ok=True)
    if cfg.network_allowed:
        result.ok = False
        result.blockers.append("NETWORK_FORBIDDEN_FOR_CAPABILITY_DEFAULT")
        return result
    if cfg.venue.upper() != VENUE_OKX:
        result.ok = False
        result.blockers.append(f"VENUE_FORBIDDEN:{cfg.venue}")
        return result
    if cfg.market_type.upper() != MARKET_TYPE_FUTURES:
        result.ok = False
        result.blockers.append(f"MARKET_TYPE_FORBIDDEN:{cfg.market_type}")
        return result
    if not ticks:
        result.ok = False
        result.blockers.append("EMPTY_TICK_SEQUENCE")
        return result

    seen_seq: set[int] = set()
    prev: ObservationMarketTickV1 | None = None
    for tick in ticks:
        if tick.venue.upper() != VENUE_OKX:
            result.blockers.append(f"TICK_VENUE_FORBIDDEN:{tick.venue}")
            continue
        if tick.market_type.upper() != MARKET_TYPE_FUTURES:
            result.blockers.append(f"TICK_MARKET_TYPE_FORBIDDEN:{tick.market_type}")
            continue
        inst_blockers = validate_instrument_for_observation_v1(
            instrument_id=tick.instrument_id, params=cfg
        )
        if inst_blockers:
            result.blockers.extend(inst_blockers)
            continue
        if tick.mid_price <= 0:
            result.blockers.append("NON_POSITIVE_PRICE")
            continue
        if tick.sequence in seen_seq:
            result.duplicate_count += 1
            if not cfg.allow_duplicates:
                result.blockers.append(f"DUPLICATE_SEQUENCE:{tick.sequence}")
                continue
        seen_seq.add(tick.sequence)
        skew = abs(tick.receive_ts_unix - tick.event_ts_unix)
        if skew > cfg.max_clock_skew_seconds:
            result.blockers.append(f"CLOCK_SKEW:{skew}")
            continue
        if wall_now_unix is not None:
            stale = wall_now_unix - tick.receive_ts_unix
            if stale > cfg.max_stale_seconds:
                result.stale_count += 1
                result.blockers.append(f"STALE_DATA:{stale}")
                continue
        if prev is not None:
            gap = tick.event_ts_unix - prev.event_ts_unix
            if gap < 0:
                result.blockers.append("NON_MONOTONIC_EVENT_TS")
                continue
            if gap > cfg.max_gap_seconds:
                result.gap_count += 1
                result.blockers.append(f"DATA_GAP:{gap}")
                continue
            mono_gap = tick.mono_ts - prev.mono_ts
            if mono_gap < 0:
                result.blockers.append("NON_MONOTONIC_MONO_TS")
                continue
            if abs((tick.receive_ts_unix - prev.receive_ts_unix) - mono_gap) > (
                cfg.max_clock_drift_seconds
            ):
                result.blockers.append("CLOCK_DRIFT")
                continue
            if tick.sequence != prev.sequence + 1:
                # Treat sequence holes as disconnect-like gaps.
                result.disconnect_detected = True
                result.blockers.append(f"SEQUENCE_DISCONNECT:{prev.sequence}->{tick.sequence}")
                continue
        prev = tick
        result.accepted_tick_count += 1

    if result.blockers:
        result.ok = False
    return result


def default_market_data_policy_params_v1() -> MarketDataPolicyParamsV1:
    return MarketDataPolicyParamsV1()


def market_data_policy_identity_v1() -> Mapping[str, Any]:
    return {
        "policy_id": MARKET_DATA_POLICY_ID,
        "policy_version": MARKET_DATA_POLICY_VERSION,
        "venue": VENUE_OKX,
        "market_type": MARKET_TYPE_FUTURES,
        "network_allowed": False,
        "btc_forbidden": True,
        "spot_forbidden": True,
    }
