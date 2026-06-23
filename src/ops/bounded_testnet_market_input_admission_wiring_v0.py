"""Bounded testnet market input admission wiring v0.

Static producer binding typed futures market observations into
``TestnetCompletionPathMarketInputV0`` for the canonical bounded testnet
completion path. Non-authorizing: no network, credentials, or runtime execution.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    TestnetCompletionPathMarketInputV0,
    validate_testnet_completion_path_market_input,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesMarketType,
)
from trading.master_v2.double_play_state import ScopeEvent
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
    OfflineDoublePlayScenarioTickV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
)

BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_LAYER_VERSION = "v0"
BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER = (
    "ops.bounded_testnet_market_input_admission_wiring_v0"
)
PACKAGE_MARKER = "BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_V0=true"

CANONICAL_MARKET_OBSERVATION_OWNER = (
    "ops.bounded_testnet_market_input_admission_wiring_v0.BoundedTestnetFuturesMarketObservationV0"
)
CANONICAL_MARKET_INPUT_PRODUCER = (
    "ops.bounded_testnet_market_input_admission_wiring_v0."
    "build_testnet_completion_path_market_input_from_observation"
)

REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID = SYNTHETIC_FUTURES_INSTRUMENT
REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL = "PF_ETHUSD"
CANONICAL_TESTNET_OBSERVATION_LANE = "testnet_bounded_observation"

_PERMITTED_FUTURES_MARKET_TYPES = frozenset(
    {
        FuturesMarketType.FUTURES,
        FuturesMarketType.PERPETUAL,
        FuturesMarketType.SWAP,
    }
)
_BTC_SPOT_RE = re.compile(r"(?i)(btc|xbt|bitcoin|/usd|/eur|spot)")


@dataclass(frozen=True)
class BoundedTestnetFuturesMarketPriceTickObservationV0:
    """Single typed futures mark-price observation from a bounded testnet lane."""

    tick_index: int
    timestamp_ms: int
    mark_price: float
    sequence: int


@dataclass(frozen=True)
class BoundedTestnetFuturesMarketObservationV0:
    """Typed bounded-testnet futures market observation envelope with provenance."""

    selected_future_id: str
    venue_symbol: str
    exchange: str
    market_type: FuturesMarketType
    source_run_id: str
    dataset_id: str
    price_source: str
    freshness_state: FuturesFreshnessState
    observed_at_utc: str
    price_timestamp_utc: str
    mark_price_available: bool
    last_price_available: bool
    index_price_available: bool
    price_ticks: tuple[BoundedTestnetFuturesMarketPriceTickObservationV0, ...]
    source_lane: str = CANONICAL_TESTNET_OBSERVATION_LANE
    synthetic_offline_fixture: bool = False


@dataclass(frozen=True)
class TestnetMarketInputAdmissionResultV0:
    market_input: TestnetCompletionPathMarketInputV0 | None
    fail_reasons: tuple[str, ...]
    producer_pass: bool


def validate_bounded_testnet_futures_market_observation(
    observation: BoundedTestnetFuturesMarketObservationV0,
) -> list[str]:
    """Fail-closed validation for bounded testnet futures market observations."""
    reasons: list[str] = []
    if observation.synthetic_offline_fixture:
        reasons.append("synthetic_offline_fixture must be false for testnet market observation")
    if observation.source_lane != CANONICAL_TESTNET_OBSERVATION_LANE:
        reasons.append(f"source_lane must be {CANONICAL_TESTNET_OBSERVATION_LANE}")
    if not observation.source_run_id.strip():
        reasons.append("source_run_id required")
    if not observation.dataset_id.strip():
        reasons.append("dataset_id required")
    if not observation.price_source.strip():
        reasons.append("price_source required")
    if not observation.exchange.strip():
        reasons.append("exchange required")
    if not observation.observed_at_utc.strip():
        reasons.append("observed_at_utc required")
    if not observation.price_timestamp_utc.strip():
        reasons.append("price_timestamp_utc required")
    if observation.freshness_state is not FuturesFreshnessState.FRESH:
        reasons.append("freshness_state must be fresh")
    if observation.market_type not in _PERMITTED_FUTURES_MARKET_TYPES:
        reasons.append("market_type must be futures/perpetual/swap")
    if not observation.selected_future_id.strip():
        reasons.append("selected_future_id required")
    if observation.selected_future_id != REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID:
        reasons.append(
            "selected_future_id must match repo-grounded ETH-PERP Master-V2 replay instrument"
        )
    if not observation.venue_symbol.strip():
        reasons.append("venue_symbol required")
    if observation.venue_symbol != REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL:
        reasons.append("venue_symbol must match repo-grounded PF_ETHUSD futures venue symbol")
    if _BTC_SPOT_RE.search(observation.selected_future_id):
        reasons.append("selected_future_id must be futures-only (no BTC/XBT/spot)")
    if _BTC_SPOT_RE.search(observation.venue_symbol):
        reasons.append("venue_symbol must be futures-only (no BTC/XBT/spot)")
    if not observation.mark_price_available:
        reasons.append("mark_price_available required for futures/perpetual admission")
    if not observation.last_price_available:
        reasons.append("last_price_available required for futures/perpetual admission")
    if not observation.index_price_available:
        reasons.append("index_price_available required for futures/perpetual admission")
    if not observation.price_ticks:
        reasons.append("price_ticks required")
    prev_ts: int | None = None
    prev_seq: int | None = None
    for tick in observation.price_ticks:
        if tick.tick_index < 0:
            reasons.append(f"tick_index={tick.tick_index}: tick_index must be >= 0")
        if tick.timestamp_ms <= 0:
            reasons.append(f"tick_index={tick.tick_index}: timestamp_ms must be positive")
        if prev_ts is not None and tick.timestamp_ms < prev_ts:
            reasons.append(f"tick_index={tick.tick_index}: timestamps must be non-decreasing")
        prev_ts = tick.timestamp_ms
        if tick.sequence < 0:
            reasons.append(f"tick_index={tick.tick_index}: sequence must be >= 0")
        if prev_seq is not None and tick.sequence <= prev_seq:
            reasons.append(f"tick_index={tick.tick_index}: sequence must be strictly increasing")
        prev_seq = tick.sequence
        if not math.isfinite(tick.mark_price) or tick.mark_price <= 0.0:
            reasons.append(f"tick_index={tick.tick_index}: mark_price must be finite and positive")
    return reasons


def _map_observation_ticks_to_replay_ticks(
    observation: BoundedTestnetFuturesMarketObservationV0,
) -> tuple[OfflineDoublePlayScenarioTickV0, ...]:
    return tuple(
        OfflineDoublePlayScenarioTickV0(
            tick_index=tick.tick_index,
            timestamp_ms=tick.timestamp_ms,
            price=tick.mark_price,
            scope_event=ScopeEvent.NOOP,
        )
        for tick in observation.price_ticks
    )


def build_testnet_completion_path_market_input_from_observation(
    observation: BoundedTestnetFuturesMarketObservationV0,
) -> TestnetMarketInputAdmissionResultV0:
    """Map a validated bounded testnet market observation into completion-path market input."""
    reasons = validate_bounded_testnet_futures_market_observation(observation)
    if reasons:
        return TestnetMarketInputAdmissionResultV0(
            market_input=None,
            fail_reasons=tuple(reasons),
            producer_pass=False,
        )

    market_input = TestnetCompletionPathMarketInputV0(
        selected_future_id=observation.selected_future_id,
        ticks=_map_observation_ticks_to_replay_ticks(observation),
        source_run_id=observation.source_run_id,
        source_lane=observation.source_lane,
        synthetic_offline_fixture=observation.synthetic_offline_fixture,
    )
    contract_reasons = validate_testnet_completion_path_market_input(market_input)
    if contract_reasons:
        return TestnetMarketInputAdmissionResultV0(
            market_input=None,
            fail_reasons=tuple(contract_reasons),
            producer_pass=False,
        )
    return TestnetMarketInputAdmissionResultV0(
        market_input=market_input,
        fail_reasons=(),
        producer_pass=True,
    )


def resolve_testnet_completion_path_market_input(
    observation: BoundedTestnetFuturesMarketObservationV0 | None,
) -> TestnetMarketInputAdmissionResultV0 | None:
    """Resolve optional market observation into admission result; None stays fail-closed."""
    if observation is None:
        return None
    return build_testnet_completion_path_market_input_from_observation(observation)


def static_producer_owner_flags() -> dict[str, str | bool]:
    return {
        "bounded_testnet_market_input_admission_wiring_owner": (
            BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER
        ),
        "canonical_market_observation_owner": CANONICAL_MARKET_OBSERVATION_OWNER,
        "canonical_market_input_producer": CANONICAL_MARKET_INPUT_PRODUCER,
        "canonical_master_v2_replay_owner": OFFLINE_DOUBLE_PLAY_SCENARIO_REPLAY_OWNER,
        "repo_grounded_eth_perp_selected_future_id": REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
        "repo_grounded_eth_perp_venue_symbol": REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
    }
