"""B11 operator profile/explainability view proofs."""

from __future__ import annotations

from dataclasses import replace
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
from src.ops.future_profile_snapshot_v1.constants_v1 import AUTHORITY_PROFILE_ONLY
from src.ops.future_profile_snapshot_v1.producer_v1 import build_future_profile_snapshot_v1
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1 import (
    classify_and_rank_economic_candidates_v1,
)
from src.ops.peak_trade_operator_profile_explainability_v1.constants_v1 import (
    B11_FEATURE_RECOMPUTE_COUNT,
    B11_RERANK_COUNT,
    B11_RESELECT_COUNT,
    B11_RESCORE_COUNT,
    LIVE_EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    REASON_BOUND_IDENTITY_MISMATCH,
    REASON_MISSING_RANKING_EXPLAINABILITY,
    REASON_MISSING_RUNTIME_BINDING_EVIDENCE,
)
from src.ops.peak_trade_operator_profile_explainability_v1.operator_view_v1 import (
    build_operator_profile_explainability_view_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_policy_v1.selection_v1 import (
    produce_single_selected_future_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH as BINDING_CALL_GRAPH,
    CAPABILITY_ID as BINDING_CAPABILITY_ID,
    OWNER as BINDING_OWNER,
    PRODUCER_VERSION as BINDING_PRODUCER_VERSION,
    SCHEMA_VERSION as BINDING_SCHEMA_VERSION,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    BoundInstrumentV1,
    RuntimeBindingEvidenceV1,
    authority_block as binding_authority_block,
    compute_config_digest_v1 as compute_binding_config_digest_v1,
)


REPO_SHA = "b11_operator_profile_test_sha"
OBSERVED_UNIX = 1_700_000_100.0
STARTED_UNIX = 1_700_000_000.0
COMPLETED_UNIX = 1_700_000_060.0
SOURCE_EVENT = "1700000000000"
PRODUCED_AT = "2023-11-14T22:15:00Z"


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


def _payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {"code": "0", "msg": "", "data": rows}


def _mark_price_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "code": "0",
        "msg": "",
        "data": [{"instId": row["instId"], "markPx": "100.5"} for row in rows],
    }


def _marks(venue_native_id: str, *, start_px: float) -> tuple[RawMarkCandleV1, ...]:
    return tuple(
        RawMarkCandleV1(
            venue_native_id=venue_native_id,
            ts_ms=str(1_700_000_000_000 + idx * 60_000),
            mark_px=f"{start_px + idx * 0.1:.8f}",
            confirm="1",
            receive_or_capture_timestamp="2023-11-14T22:14:20Z",
        )
        for idx in range(61)
    )


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


def _binding_evidence(flow: dict[str, Any]) -> RuntimeBindingEvidenceV1:
    selection = flow["selection"]
    ranking = flow["ranking"]
    universe = flow["universe"]
    bound = BoundInstrumentV1(
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
        ranking_snapshot_id=selection.ranking_snapshot_id,
        ranking_integrity_digest=selection.ranking_integrity_digest,
        ranking_policy_id=selection.ranking_policy_id,
        ranking_policy_version=selection.ranking_policy_version,
        upstream_rank_order_witness=selection.upstream_rank_order_witness,
        universe_snapshot_id=ranking.universe_snapshot_id or universe.snapshot_id,
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        selection_state=selection.state,
    )
    cfg = compute_binding_config_digest_v1(repository_sha=REPO_SHA)
    return RuntimeBindingEvidenceV1(
        capability_id=BINDING_CAPABILITY_ID,
        schema_version=BINDING_SCHEMA_VERSION,
        producer_version=BINDING_PRODUCER_VERSION,
        owner=BINDING_OWNER,
        ok=True,
        alpha_enabled=False,
        new_alpha_allowed=False,
        exit_risk_safety_preserved=True,
        hard_stop=False,
        selection_state=selection.state,
        instrument_id=selection.instrument_id,
        venue_native_id=selection.venue_native_id,
        selection_id=selection.selection_id,
        selection_integrity_digest=selection.integrity_digest,
        ranking_snapshot_id=selection.ranking_snapshot_id,
        ranking_integrity_digest=selection.ranking_integrity_digest,
        universe_snapshot_id=bound.universe_snapshot_id,
        repository_sha=REPO_SHA,
        config_digest=cfg,
        reconciliation_before_alpha=True,
        reconciliation_alpha_enabled=False,
        reason_codes=(),
        failure_codes=(),
        call_graph=BINDING_CALL_GRAPH,
        authority=binding_authority_block(),
        notes=("B11_TEST_BOUND_IDENTITY_ONLY",),
        bound=bound.to_dict(),
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
        source_payload=_payload(rows),
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
    explainability = classify_and_rank_economic_candidates_v1(
        universe_snapshot=universe.to_dict(),
        feature_production_snapshot=features,
    ).explainability
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
    flow = {
        "economic_md": economic_md,
        "explainability": explainability,
        "features": features,
        "profile": profile,
        "ranking": ranking,
        "selection": selection,
        "universe": universe,
    }
    flow["binding"] = _binding_evidence(flow)
    return flow


def _view(flow: dict[str, Any]):
    return build_operator_profile_explainability_view_v1(
        selection=flow["selection"],
        runtime_binding_evidence=flow["binding"],
        ranking_snapshot=flow["ranking"],
        ranking_explainability=flow["explainability"],
        future_profile_snapshot=flow["profile"],
        repository_sha=REPO_SHA,
        produced_at_wall_time=PRODUCED_AT,
    )


def test_operator_view_projects_selected_identity_eligibility_rank_and_profile() -> None:
    flow = _build_flow()
    view = _view(flow)
    selection = flow["selection"]

    assert view.ok is True
    assert view.view_state == "AVAILABLE"
    assert view.selected_future_identity["instrument_id"] == selection.instrument_id
    assert view.selected_future_identity["bound_instrument_id"] == selection.instrument_id
    assert view.selected_future_identity["selection_state"] == STATE_SELECTED_ACTIVE
    assert view.eligibility["selection_state"] == STATE_SELECTED_ACTIVE
    assert view.eligibility["selection_reason_codes"]
    assert view.rank == selection.selected_rank == 1
    assert view.future_profile["canonical_instrument_id"] == selection.instrument_id


def test_ranking_witness_contributions_timestamps_and_provenance_are_projected() -> None:
    flow = _build_flow()
    view = _view(flow)
    explanation = view.ranking_explanation

    assert explanation["raw_features"]
    assert explanation["normalized_features"]
    assert explanation["score_contributions"]
    assert explanation["policy_identity"]["ranking_policy_id"]
    assert view.timestamps["ranking_event_time"] == flow["ranking"].event_time
    assert (
        view.timestamps["selection_selected_at_event_time"]
        == flow["selection"].selected_at_event_time
    )
    assert view.provenance["ranking_snapshot_id"] == flow["ranking"].ranking_snapshot_id
    assert (
        view.provenance["ranking_explainability_digest"] == flow["explainability"].integrity_digest
    )
    assert view.provenance["future_profile_snapshot_id"] == flow["profile"].profile_snapshot_id


def test_output_is_deterministic_for_identical_authoritative_inputs() -> None:
    flow = _build_flow()
    first = _view(flow)
    second = build_operator_profile_explainability_view_v1(
        selection=flow["selection"],
        runtime_binding_evidence=flow["binding"],
        ranking_snapshot=flow["ranking"],
        ranking_explainability=flow["explainability"],
        future_profile_snapshot=flow["profile"],
        repository_sha=REPO_SHA,
        produced_at_wall_time="2023-11-14T22:16:00Z",
    )

    assert first.view_id == second.view_id
    assert first.integrity_digest == second.integrity_digest
    assert first.selected_future_identity == second.selected_future_identity
    assert first.ranking_explanation == second.ranking_explanation


def test_missing_required_upstream_evidence_fails_closed_without_fallback() -> None:
    flow = _build_flow()
    view = build_operator_profile_explainability_view_v1(
        selection=flow["selection"],
        runtime_binding_evidence=None,
        ranking_snapshot=flow["ranking"],
        ranking_explainability=None,
        future_profile_snapshot=flow["profile"],
        repository_sha=REPO_SHA,
        produced_at_wall_time=PRODUCED_AT,
    )

    assert view.ok is False
    assert view.hard_stop is True
    assert REASON_MISSING_RUNTIME_BINDING_EVIDENCE in view.reason_codes
    assert REASON_MISSING_RANKING_EXPLAINABILITY in view.reason_codes
    assert view.authority["B11_FEATURE_RECOMPUTE_COUNT"] == 0
    assert view.ranking_explanation == {}


def test_mismatched_binding_identity_fails_closed() -> None:
    flow = _build_flow()
    bad_binding = dict(flow["binding"].to_dict())
    bad_binding["instrument_id"] = "BTC-USDT-SWAP"
    view = build_operator_profile_explainability_view_v1(
        selection=flow["selection"],
        runtime_binding_evidence=bad_binding,
        ranking_snapshot=flow["ranking"],
        ranking_explainability=flow["explainability"],
        future_profile_snapshot=flow["profile"],
        repository_sha=REPO_SHA,
        produced_at_wall_time=PRODUCED_AT,
    )

    assert view.ok is False
    assert REASON_BOUND_IDENTITY_MISMATCH in view.reason_codes


def test_profile_only_and_unclassified_fields_remain_inert() -> None:
    flow = _build_flow()
    base = _view(flow)
    profile = flow["profile"]
    selected_id = flow["selection"].instrument_id
    mutated_instruments = []
    for instrument in profile.instruments:
        if instrument.canonical_instrument_id != selected_id:
            mutated_instruments.append(instrument)
            continue
        mutated_fields = []
        for field in instrument.fields:
            if field.authority_class == AUTHORITY_PROFILE_ONLY:
                mutated_fields.append(replace(field, value="operator-only-mutated"))
            else:
                mutated_fields.append(field)
        mutated_instruments.append(replace(instrument, fields=tuple(mutated_fields)))
    mutated_profile = replace(profile, instruments=tuple(mutated_instruments), integrity_digest="")
    mutated_profile = mutated_profile.with_integrity_digest()
    changed = build_operator_profile_explainability_view_v1(
        selection=flow["selection"],
        runtime_binding_evidence=flow["binding"],
        ranking_snapshot=flow["ranking"],
        ranking_explainability=flow["explainability"],
        future_profile_snapshot=mutated_profile,
        repository_sha=REPO_SHA,
        produced_at_wall_time=PRODUCED_AT,
    )

    assert base.rank == changed.rank == flow["selection"].selected_rank
    assert base.selected_future_identity == changed.selected_future_identity
    assert changed.authority["PROFILE_ONLY_RANKING_EFFECT"] == "NONE"
    assert changed.authority["PROFILE_ONLY_SELECTION_EFFECT"] == "NONE"
    assert changed.authority["UNCLASSIFIED_RANKING_EFFECT"] == "NONE"
    assert changed.authority["UNCLASSIFIED_SELECTION_EFFECT"] == "NONE"


def test_b11_cannot_recompute_rescore_rerank_or_reselect_and_preserves_authority() -> None:
    flow = _build_flow()
    view = _view(flow)

    assert B11_FEATURE_RECOMPUTE_COUNT == 0
    assert B11_RESCORE_COUNT == 0
    assert B11_RERANK_COUNT == 0
    assert B11_RESELECT_COUNT == 0
    assert view.authority["B11_FEATURE_RECOMPUTE_COUNT"] == 0
    assert view.authority["B11_RESCORE_COUNT"] == 0
    assert view.authority["B11_RERANK_COUNT"] == 0
    assert view.authority["B11_RESELECT_COUNT"] == 0
    assert view.authority["CAP23_SOLE_SELECTION_OWNER"] is True
    assert view.authority["CROSS_UNIVERSE_AUTHORITY"] == "NONE"
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert view.authority["MULTI_FUTURE_RUNTIME_AUTHORIZED"] is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert view.authority["MAX_POSITIONS_EFFECTIVE"] == 1
    assert LIVE_EXTERNAL_EFFECT_AUTHORIZED is False
    assert view.authority["LIVE_EXTERNAL_EFFECT_AUTHORIZED"] is False
