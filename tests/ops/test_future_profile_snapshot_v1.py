"""B07 Future Profile Snapshot V1 observability proofs."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    InjectedEconomicMdPublicSourceV1,
    InstrumentPublicMdBundleV1,
    RawMarkCandleV1,
    RawTickerQuoteV1,
)
from src.ops.future_profile_snapshot_v1.constants_v1 import (
    AUTHORITY_ELIGIBILITY_SAFETY,
    AUTHORITY_PROFILE_ONLY,
    AUTHORITY_RANKING_INPUT,
    AUTHORITY_UNCLASSIFIED,
    CAPABILITY_ID,
    CALL_GRAPH,
    FORBIDDEN_CALL_GRAPH_TARGETS,
    SCHEMA_VERSION,
)
from src.ops.future_profile_snapshot_v1.models_v1 import (
    profile_summary_counts_v1,
    round_trip_future_profile_snapshot_v1,
)
from src.ops.future_profile_snapshot_v1.producer_v1 import (
    build_future_profile_snapshot_v1,
    get_selected_future_profile_v1,
    missing_optional_profile_field_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import (
    RankingFailureCodeV1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)


REPO = Path(__file__).resolve().parents[2]
REPO_SHA = "b07_future_profile_snapshot_test_sha"
OBSERVED_UNIX = 1_700_000_100.0
STARTED_UNIX = 1_700_000_000.0
COMPLETED_UNIX = 1_700_000_060.0
SOURCE_EVENT = "1700000000000"


def _perp(inst_id: str, *, base: str) -> dict[str, Any]:
    return {
        "baseCcy": "",
        "ctType": "linear",
        "ctVal": "0.01",
        "ctValCcy": base,
        "expTime": "",
        "instFamily": f"{base}-USDT",
        "instId": inst_id,
        "instType": "SWAP",
        "lotSz": "1",
        "minSz": "1",
        "quoteCcy": "USDT",
        "settleCcy": "USDT",
        "state": "live",
        "tickSz": "0.01",
        "uly": f"{base}-USDT",
    }


def _source_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": "0", "msg": "", "data": rows}


def _mark_price_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": row["instId"], "markPx": "100.5"} for row in rows],
    }


def _marks(venue_native_id: str, *, start_px: float) -> tuple[RawMarkCandleV1, ...]:
    rows: list[RawMarkCandleV1] = []
    for idx in range(61):
        rows.append(
            RawMarkCandleV1(
                venue_native_id=venue_native_id,
                ts_ms=str(1_700_000_000_000 + idx * 60_000),
                mark_px=f"{start_px + idx * 0.1:.8f}",
                confirm="1",
                receive_or_capture_timestamp="2023-11-14T22:14:20Z",
            )
        )
    return tuple(rows)


def _bundle(
    venue_native_id: str,
    *,
    start_px: float,
    bid: str | None = "100.00",
    ask: str | None = "100.10",
) -> InstrumentPublicMdBundleV1:
    ticker = None
    if bid is not None or ask is not None:
        ticker = RawTickerQuoteV1(
            venue_native_id=venue_native_id,
            bid_px=bid,
            ask_px=ask,
            ticker_event_timestamp="1700000060000",
            capture_or_receive_timestamp="2023-11-14T22:14:20Z",
        )
    return InstrumentPublicMdBundleV1(
        venue_native_id=venue_native_id,
        marks=_marks(venue_native_id, start_px=start_px),
        ticker=ticker,
    )


def _build_flow(
    *,
    eth_bid: str | None = "100.00",
    eth_ask: str | None = "100.10",
) -> dict[str, Any]:
    rows = [
        _perp("ETH-USDT-SWAP", base="ETH"),
        _perp("SOL-USDT-SWAP", base="SOL"),
    ]
    universe = produce_governed_futures_universe_v1(
        source_payload=_source_payload(rows),
        mark_price_payload=_mark_price_payload(rows),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
        source_event_time=SOURCE_EVENT,
    ).snapshot
    source = InjectedEconomicMdPublicSourceV1(
        {
            "ETH-USDT-SWAP": _bundle(
                "ETH-USDT-SWAP",
                start_px=100.0,
                bid=eth_bid,
                ask=eth_ask,
            ),
            "SOL-USDT-SWAP": _bundle("SOL-USDT-SWAP", start_px=90.0),
        }
    )
    economic_md = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe.to_dict(),
        public_md_source=source,
        collection_started_at_unix=STARTED_UNIX,
        collection_completed_at_unix=COMPLETED_UNIX,
    ).snapshot
    features = produce_ranking_feature_production_snapshot_v1(economic_md)
    ranking = produce_productive_futures_ranking_v1(
        universe_snapshot=universe.to_dict(),
        feature_production_snapshot=features,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).snapshot
    selection = produce_single_selected_future_v1(
        ranking_snapshot=ranking.to_dict(),
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    ).selection
    profile = build_future_profile_snapshot_v1(
        universe_snapshot=universe,
        economic_md_snapshot=economic_md,
        feature_production_snapshot=features,
        ranking_snapshot=ranking,
        selection=selection,
        repository_sha=REPO_SHA,
        profile_observed_at_unix=OBSERVED_UNIX,
    )
    return {
        "economic_md": economic_md,
        "features": features,
        "profile": profile,
        "ranking": ranking,
        "selection": selection,
        "universe": universe,
    }


def _field_values(profile: Any, canonical_id: str) -> dict[str, Any]:
    instrument = next(
        row for row in profile.instruments if row.canonical_instrument_id == canonical_id
    )
    return {field.field_id: field.value for field in instrument.fields}


def test_complete_available_profile_contains_current_canonical_groups() -> None:
    flow = _build_flow()
    profile = flow["profile"]
    counts = profile_summary_counts_v1(profile)
    assert profile.schema_version == SCHEMA_VERSION
    assert profile.capability_id == CAPABILITY_ID
    assert counts["profile_field_count"] > 0
    assert counts["profile_only_field_count"] > 0
    assert counts["ranking_input_field_count"] > 0
    assert counts["eligibility_safety_field_count"] > 0
    assert counts["unclassified_field_count"] > 0
    selected = get_selected_future_profile_v1(profile)
    assert selected is not None
    field_ids = {field.field_id for field in selected.fields}
    assert "canonical_instrument_id" in field_ids
    assert "latest_finalized_mark_price" in field_ids
    assert "b05_raw_feature.CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1" in field_ids
    assert "balanced_movement_score" in field_ids
    assert "economic_md_raw_input_digest" in field_ids
    assert "unresolved_validity_stale_seconds" in field_ids


def test_canonical_b05_b06_values_are_reused_not_recomputed() -> None:
    flow = _build_flow()
    profile = flow["profile"]
    features = flow["features"]
    ranking = flow["ranking"]
    candidate = ranking.ranked_candidates[0]
    values = _field_values(profile, candidate.canonical_instrument_id)
    feature_row = next(
        row
        for row in features.instruments
        if row.canonical_instrument_id == candidate.canonical_instrument_id
    )
    raw_by_id = {row.feature_policy_id: row.raw_value for row in feature_row.raw_features}
    assert (
        values["b05_raw_feature.CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1"]
        == raw_by_id["CAP22_PT1M_MARK_LOG_RETURN_POPULATION_SIGMA_V1"]
    )
    assert (
        values["b05_raw_feature.CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1"]
        == raw_by_id["CAP22_PT1M_MARK_MID_RELATIVE_RANGE_V1"]
    )
    assert values["balanced_movement_score"] == candidate.total_score
    assert profile.authority["CANONICAL_FEATURE_RECOMPUTATION_INTRODUCED"] is False


def test_profile_only_ticker_change_does_not_change_rank_order_or_selection() -> None:
    base = _build_flow(eth_bid="100.00", eth_ask="100.10")
    changed = _build_flow(eth_bid="1.00", eth_ask="1000.00")
    assert [c.canonical_instrument_id for c in base["ranking"].ranked_candidates] == [
        c.canonical_instrument_id for c in changed["ranking"].ranked_candidates
    ]
    assert [c.total_score for c in base["ranking"].ranked_candidates] == [
        c.total_score for c in changed["ranking"].ranked_candidates
    ]
    assert base["selection"].instrument_id == changed["selection"].instrument_id
    assert base["selection"].state == changed["selection"].state == STATE_SELECTED_ACTIVE
    assert base["profile"].integrity_digest != changed["profile"].integrity_digest


def test_profile_construction_cannot_rerank_select_or_bind() -> None:
    profile = _build_flow()["profile"]
    assert profile.authority["PROFILE_CAN_RERANK"] is False
    assert profile.authority["PROFILE_CAN_SELECT"] is False
    assert profile.authority["PROFILE_CAN_BIND"] is False
    assert profile.authority["SELECTION_AUTHORITY_CREATED"] is False
    assert profile.authority["BINDING_EFFECT"] is False
    assert FORBIDDEN_CALL_GRAPH_TARGETS.isdisjoint(set(CALL_GRAPH))
    producer_path = REPO / "src/ops/future_profile_snapshot_v1/producer_v1.py"
    tree = ast.parse(producer_path.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.append(node.module)
    assert not any(module.endswith(".selection_v1") for module in imported_modules)
    assert not any("runtime_binding" in module for module in imported_modules)


def test_optional_missing_data_is_explicit_and_required_missing_still_fails_closed() -> None:
    flow = _build_flow(eth_bid=None, eth_ask=None)
    profile = flow["profile"]
    optional_missing = [
        field
        for instrument in profile.instruments
        for field in instrument.fields
        if missing_optional_profile_field_v1(field)
    ]
    assert optional_missing
    assert all(field.missing_reason for field in optional_missing)
    missing_required = produce_productive_futures_ranking_v1(
        universe_snapshot=flow["universe"].to_dict(),
        feature_production_snapshot=None,
        repository_sha=REPO_SHA,
        producer_observed_at_unix=OBSERVED_UNIX,
    )
    assert missing_required.ok is False
    assert RankingFailureCodeV1.ECONOMIC_FEATURE_PRODUCTION_SNAPSHOT_MISSING.value in (
        missing_required.failure_codes
    )


def test_provenance_determinism_and_serialization_round_trip() -> None:
    a = _build_flow()["profile"]
    b = build_future_profile_snapshot_v1(
        universe_snapshot=_build_flow()["universe"],
        economic_md_snapshot=_build_flow()["economic_md"],
        feature_production_snapshot=_build_flow()["features"],
        ranking_snapshot=_build_flow()["ranking"],
        selection=_build_flow()["selection"],
        repository_sha=REPO_SHA,
        profile_observed_at_unix=OBSERVED_UNIX + 999.0,
    )
    assert a.compute_integrity_digest() == b.compute_integrity_digest()
    assert a.profile_snapshot_id == b.profile_snapshot_id
    round_trip_future_profile_snapshot_v1(a)
    assert a.source_references["universe_payload_digest"]
    assert a.source_references["feature_production_digest"]
    assert a.source_references["ranking_integrity_digest"]


def test_downstream_safety_pins_unchanged() -> None:
    profile = _build_flow()["profile"]
    assert profile.authority["CAP23_SOLE_SELECTION_OWNER"] is True
    assert profile.authority["CROSS_UNIVERSE_AUTHORITY"] == "NONE"
    assert profile.authority["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert profile.authority["MAX_POSITIONS_EFFECTIVE"] == 1
    assert profile.authority["LIVE_EXTERNAL_EFFECT_AUTHORIZED"] is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    all_authorities = {
        field.authority_class for instrument in profile.instruments for field in instrument.fields
    }
    assert {
        AUTHORITY_ELIGIBILITY_SAFETY,
        AUTHORITY_PROFILE_ONLY,
        AUTHORITY_RANKING_INPUT,
        AUTHORITY_UNCLASSIFIED,
    }.issubset(all_authorities)
