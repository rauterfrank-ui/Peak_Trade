"""U2a — offline fixture loader for FuturesProducerPacket bundles (read-only, no I/O beyond path read)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading.master_v2.double_play_futures_input import FuturesFreshnessState, FuturesMarketType
from trading.master_v2.double_play_futures_input_producer import (
    FuturesProducerCandidate,
    FuturesProducerDerivatives,
    FuturesProducerInstrumentMetadata,
    FuturesProducerLiquidity,
    FuturesProducerMarketDataProvenance,
    FuturesProducerOpportunity,
    FuturesProducerPacket,
    FuturesProducerRanking,
    FuturesProducerVolatility,
    producer_packet_has_runtime_handles,
)

from .futures_universe_upstream_adapter_v1 import (
    FORBIDDEN_UPSTREAM_SOURCE_MARKERS,
    FuturesUniverseUpstreamInputV1,
    is_forbidden_upstream_source,
)

FIXTURE_SCHEMA_NAME = "futures_producer_packet_fixture.v1"
FIXTURE_SCHEMA_VERSION = 1
FIXTURE_SOURCE_KIND = "fixture"
FIXTURE_PRODUCER_ID = "futures_producer_packet_fixture_source_v1"
FIXTURE_SOURCE_CONTRACT = "futures_producer_packet_fixture_source.v1"

REASON_FIXTURE_NOT_MARKED = "FIXTURE_NOT_MARKED"
REASON_OBSERVABILITY_TRUTH_CLAIMED = "OBSERVABILITY_TRUTH_CLAIMED"
REASON_NON_AUTHORIZING_REQUIRED = "NON_AUTHORIZING_REQUIRED"
REASON_FORBIDDEN_UPSTREAM_SOURCE = "FORBIDDEN_UPSTREAM_SOURCE"
REASON_FIXTURE_SCHEMA_INVALID = "FIXTURE_SCHEMA_INVALID"
REASON_FIXTURE_PACKET_RUNTIME_HANDLE = "FIXTURE_PACKET_RUNTIME_HANDLE"
REASON_FIXTURE_MISSING_REQUIRED_FIELD = "FIXTURE_MISSING_REQUIRED_FIELD"


class FuturesProducerPacketFixtureSourceError(ValueError):
    """Raised when a fixture bundle violates U2a safety or schema rules."""


@dataclass(frozen=True)
class FuturesProducerPacketFixtureBundleV1:
    """Loaded fixture bundle — never observability truth; tests and explicit callers only."""

    source_kind: str
    producer_id: str
    generated_at: str
    source_run_id: str
    source_stage: str
    fixture_only: bool
    observability_truth_allowed: bool
    non_authorizing: bool
    universe: dict[str, Any]
    ranking: dict[str, Any]
    selected_future: dict[str, Any]
    packets: tuple[FuturesProducerPacket, ...]
    selected_candidate_id: str | None = None
    fixture_path: str | None = None


def fixture_root_under(project_root: Path) -> Path:
    return (
        project_root
        / "tests"
        / "fixtures"
        / "workflow_dashboard_readmodel_v1"
        / "futures_producer_packet_v1"
    )


def assert_fixture_not_observability_truth(bundle: FuturesProducerPacketFixtureBundleV1) -> None:
    """Fail closed when a bundle claims production observability truth."""
    if bundle.observability_truth_allowed:
        msg = f"{REASON_OBSERVABILITY_TRUTH_CLAIMED}: fixture must not claim observability truth"
        raise FuturesProducerPacketFixtureSourceError(msg)
    if not bundle.fixture_only:
        msg = f"{REASON_FIXTURE_NOT_MARKED}: fixture_only must be true"
        raise FuturesProducerPacketFixtureSourceError(msg)
    if not bundle.non_authorizing:
        msg = f"{REASON_NON_AUTHORIZING_REQUIRED}: non_authorizing must be true"
        raise FuturesProducerPacketFixtureSourceError(msg)


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        msg = f"{REASON_FIXTURE_MISSING_REQUIRED_FIELD}: missing or invalid '{key}' object"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return value


def _require_bool(data: dict[str, Any], key: str) -> bool:
    if key not in data:
        msg = f"{REASON_FIXTURE_MISSING_REQUIRED_FIELD}: missing '{key}'"
        raise FuturesProducerPacketFixtureSourceError(msg)
    value = data[key]
    if not isinstance(value, bool):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: '{key}' must be boolean"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return value


def _require_str(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"{REASON_FIXTURE_MISSING_REQUIRED_FIELD}: missing or empty '{key}'"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return value.strip()


def _parse_market_type(raw: str) -> FuturesMarketType:
    try:
        return FuturesMarketType(raw.strip().lower())
    except ValueError as exc:
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: invalid market_type '{raw}'"
        raise FuturesProducerPacketFixtureSourceError(msg) from exc


def _parse_freshness_state(raw: str) -> FuturesFreshnessState:
    try:
        return FuturesFreshnessState(raw.strip().lower())
    except ValueError as exc:
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: invalid freshness_state '{raw}'"
        raise FuturesProducerPacketFixtureSourceError(msg) from exc


def _parse_tuple_str(value: Any, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: '{field}' must be a string array"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return tuple(value)


def _parse_candidate(raw: dict[str, Any]) -> FuturesProducerCandidate:
    return FuturesProducerCandidate(
        candidate_id=_require_str(raw, "candidate_id"),
        instrument_id=_require_str(raw, "instrument_id"),
        symbol=_require_str(raw, "symbol"),
        market_type=_parse_market_type(_require_str(raw, "market_type")),
        exchange=_require_str(raw, "exchange"),
        base_currency=_require_str(raw, "base_currency"),
        quote_currency=_require_str(raw, "quote_currency"),
        live_authorization=bool(raw.get("live_authorization", False)),
    )


def _parse_ranking(raw: dict[str, Any]) -> FuturesProducerRanking:
    return FuturesProducerRanking(
        source_universe_size=raw.get("source_universe_size"),
        selected_top_n=raw.get("selected_top_n"),
        rank=raw.get("rank"),
        score=raw.get("score"),
        score_components_complete=bool(raw.get("score_components_complete", False)),
        is_top_n_member=bool(raw.get("is_top_n_member", False)),
    )


def _parse_instrument(raw: dict[str, Any]) -> FuturesProducerInstrumentMetadata:
    return FuturesProducerInstrumentMetadata(
        complete=bool(raw.get("complete", False)),
        contract_size_known=bool(raw.get("contract_size_known", False)),
        tick_size_known=bool(raw.get("tick_size_known", False)),
        step_size_known=bool(raw.get("step_size_known", False)),
        min_qty_known=bool(raw.get("min_qty_known", False)),
        min_notional_known=bool(raw.get("min_notional_known", False)),
        margin_asset_known=bool(raw.get("margin_asset_known", False)),
        settlement_asset_known=bool(raw.get("settlement_asset_known", False)),
        leverage_bounds_known=bool(raw.get("leverage_bounds_known", False)),
        missing_fields=_parse_tuple_str(raw.get("missing_fields"), field="missing_fields"),
    )


def _parse_provenance(raw: dict[str, Any]) -> FuturesProducerMarketDataProvenance:
    return FuturesProducerMarketDataProvenance(
        complete=bool(raw.get("complete", False)),
        freshness_state=_parse_freshness_state(_require_str(raw, "freshness_state")),
        dataset_id=raw.get("dataset_id"),
        source=raw.get("source"),
        mark_available=bool(raw.get("mark_available", False)),
        index_available=bool(raw.get("index_available", False)),
        last_available=bool(raw.get("last_available", False)),
        ohlcv_available=bool(raw.get("ohlcv_available", False)),
        funding_available=bool(raw.get("funding_available", False)),
        open_interest_available=bool(raw.get("open_interest_available", False)),
        missing_fields=_parse_tuple_str(raw.get("missing_fields"), field="missing_fields"),
    )


def _parse_volatility(raw: dict[str, Any]) -> FuturesProducerVolatility:
    return FuturesProducerVolatility(
        realized_volatility=raw.get("realized_volatility"),
        atr_or_rolling_range=raw.get("atr_or_rolling_range"),
        volatility_regime=raw.get("volatility_regime"),
        dynamic_scope_usable=bool(raw.get("dynamic_scope_usable", False)),
    )


def _parse_liquidity(raw: dict[str, Any]) -> FuturesProducerLiquidity:
    return FuturesProducerLiquidity(
        spread_bps=raw.get("spread_bps"),
        average_spread_bps=raw.get("average_spread_bps"),
        volume=raw.get("volume"),
        quote_volume=raw.get("quote_volume"),
        liquidity_regime=raw.get("liquidity_regime"),
        spread_quality=raw.get("spread_quality"),
    )


def _parse_derivatives(raw: dict[str, Any]) -> FuturesProducerDerivatives:
    return FuturesProducerDerivatives(
        funding_available=bool(raw.get("funding_available", False)),
        funding_rate=raw.get("funding_rate"),
        funding_regime=raw.get("funding_regime"),
        open_interest_available=bool(raw.get("open_interest_available", False)),
        open_interest=raw.get("open_interest"),
        open_interest_regime=raw.get("open_interest_regime"),
    )


def _parse_opportunity(raw: dict[str, Any]) -> FuturesProducerOpportunity:
    return FuturesProducerOpportunity(
        opportunity_score=raw.get("opportunity_score"),
        inactivity_score=raw.get("inactivity_score"),
        movement_above_fee_slippage_breakeven=raw.get("movement_above_fee_slippage_breakeven"),
        chop_risk=raw.get("chop_risk"),
        candidate_is_inactive=bool(raw.get("candidate_is_inactive", False)),
    )


def _parse_packet(raw: dict[str, Any]) -> FuturesProducerPacket:
    packet = FuturesProducerPacket(
        candidate=_parse_candidate(_require_mapping(raw, "candidate")),
        ranking=_parse_ranking(_require_mapping(raw, "ranking")),
        instrument=_parse_instrument(_require_mapping(raw, "instrument")),
        provenance=_parse_provenance(_require_mapping(raw, "provenance")),
        volatility=_parse_volatility(_require_mapping(raw, "volatility")),
        liquidity=_parse_liquidity(_require_mapping(raw, "liquidity")),
        derivatives=_parse_derivatives(_require_mapping(raw, "derivatives")),
        opportunity=_parse_opportunity(_require_mapping(raw, "opportunity")),
        dashboard_label=raw.get("dashboard_label"),
        ai_summary=raw.get("ai_summary"),
    )
    if producer_packet_has_runtime_handles(packet):
        msg = f"{REASON_FIXTURE_PACKET_RUNTIME_HANDLE}: packet contains runtime handles"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return packet


def _validate_fixture_governance(data: dict[str, Any]) -> tuple[str, str]:
    schema_name = _require_str(data, "schema_name")
    if schema_name != FIXTURE_SCHEMA_NAME:
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: schema_name must be {FIXTURE_SCHEMA_NAME}"
        raise FuturesProducerPacketFixtureSourceError(msg)
    if data.get("schema_version") != FIXTURE_SCHEMA_VERSION:
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: schema_version must be {FIXTURE_SCHEMA_VERSION}"
        raise FuturesProducerPacketFixtureSourceError(msg)

    fixture_only = _require_bool(data, "fixture_only")
    observability_truth_allowed = _require_bool(data, "observability_truth_allowed")
    non_authorizing = _require_bool(data, "non_authorizing")
    if not fixture_only or observability_truth_allowed or not non_authorizing:
        msg = (
            f"{REASON_FIXTURE_NOT_MARKED}: requires fixture_only=true, "
            "observability_truth_allowed=false, non_authorizing=true"
        )
        raise FuturesProducerPacketFixtureSourceError(msg)

    source_kind = _require_str(data, "source_kind")
    producer_id = _require_str(data, "producer_id")
    if is_forbidden_upstream_source(
        upstream_source_kind=source_kind,
        upstream_producer_id=producer_id,
    ):
        msg = f"{REASON_FORBIDDEN_UPSTREAM_SOURCE}: source_kind/producer_id forbidden"
        raise FuturesProducerPacketFixtureSourceError(msg)
    if (
        source_kind in FORBIDDEN_UPSTREAM_SOURCE_MARKERS
        or producer_id in FORBIDDEN_UPSTREAM_SOURCE_MARKERS
    ):
        msg = f"{REASON_FORBIDDEN_UPSTREAM_SOURCE}: source markers forbidden"
        raise FuturesProducerPacketFixtureSourceError(msg)
    return source_kind, producer_id


def load_futures_producer_packet_fixture(path: Path) -> FuturesProducerPacketFixtureBundleV1:
    """Load and validate a fixture JSON file from an explicit path (read-only)."""
    raw_text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: invalid JSON"
        raise FuturesProducerPacketFixtureSourceError(msg) from exc
    if not isinstance(data, dict):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: root must be object"
        raise FuturesProducerPacketFixtureSourceError(msg)

    source_kind, producer_id = _validate_fixture_governance(data)
    universe = _require_mapping(data, "universe")
    ranking = _require_mapping(data, "ranking")
    selected_future = _require_mapping(data, "selected_future")

    packets_raw = data.get("packets")
    if packets_raw is None:
        msg = f"{REASON_FIXTURE_MISSING_REQUIRED_FIELD}: missing 'packets'"
        raise FuturesProducerPacketFixtureSourceError(msg)
    if not isinstance(packets_raw, list):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: 'packets' must be array"
        raise FuturesProducerPacketFixtureSourceError(msg)

    packets = tuple(_parse_packet(item) for item in packets_raw if isinstance(item, dict))
    if len(packets) != len(packets_raw):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: each packet must be an object"
        raise FuturesProducerPacketFixtureSourceError(msg)

    selected_candidate_id = data.get("selected_candidate_id")
    if selected_candidate_id is not None and (
        not isinstance(selected_candidate_id, str) or not selected_candidate_id.strip()
    ):
        msg = f"{REASON_FIXTURE_SCHEMA_INVALID}: selected_candidate_id must be non-empty string"
        raise FuturesProducerPacketFixtureSourceError(msg)

    bundle = FuturesProducerPacketFixtureBundleV1(
        source_kind=source_kind,
        producer_id=producer_id,
        generated_at=_require_str(data, "generated_at"),
        source_run_id=_require_str(data, "source_run_id"),
        source_stage=_require_str(data, "source_stage"),
        fixture_only=True,
        observability_truth_allowed=False,
        non_authorizing=True,
        universe=universe,
        ranking=ranking,
        selected_future=selected_future,
        packets=packets,
        selected_candidate_id=selected_candidate_id.strip()
        if isinstance(selected_candidate_id, str)
        else None,
        fixture_path=str(path),
    )
    assert_fixture_not_observability_truth(bundle)
    return bundle


def bundle_to_upstream_input(
    bundle: FuturesProducerPacketFixtureBundleV1,
) -> FuturesUniverseUpstreamInputV1:
    """Map a validated fixture bundle to U1 upstream input — always fixture_marked."""
    assert_fixture_not_observability_truth(bundle)
    return FuturesUniverseUpstreamInputV1(
        source_run_id=bundle.source_run_id,
        source_stage=bundle.source_stage,
        generated_at=bundle.generated_at,
        packets=bundle.packets,
        upstream_source_kind=bundle.source_kind,
        upstream_producer_id=bundle.producer_id,
        selected_candidate_id=bundle.selected_candidate_id,
        evidence_links=(),
        fixture_marked=True,
    )
