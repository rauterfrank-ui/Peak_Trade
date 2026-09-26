"""Phase 19 orthogonal MARKET_CONTEXT_V1 materialization tests (AUTHORITY=NONE)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_existing_fact_materialization_v1 import (
    ExistingFactMaterializationError,
    ExistingFactMaterializationRequestV1,
    GovernedCanonicalFactV1,
    WP_A_PRODUCER,
    materialize_market_context_v1_from_existing_facts_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_phase_19_orthogonal_materialization_v1 import (
    Phase19OrthogonalMaterializationInputsV1,
    assert_phase_19_authority_invariants_v1,
    load_cross_market_anchor_binding_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CROSS_MARKET_CONTEXT_ONLY,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    exact_known_61_price_fixture_v1,
)

_BASE = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
_SELECTED = "inst-sui-usdt-perp"
_ANCHOR = "inst-eth-usdt-perp"


def _quality() -> dict:
    return {
        "finalized": True,
        "in_progress": False,
        "missing": False,
        "stale": False,
        "corrected": False,
        "duplicate": False,
        "out_of_order": False,
        "gap_detected": False,
    }


def _instrument(canonical_id: str) -> dict:
    return {
        "canonical_instrument_id": canonical_id,
        "venue_native_id": "TEST-SWAP",
        "venue": "okx_eea",
        "instrument_type": "SWAP",
        "settlement_asset": "USDT",
        "mapping_provenance_digest": "a" * 64,
    }


def _ts(offset_min: int) -> tuple[int, str]:
    dt = _BASE + timedelta(minutes=offset_min)
    return int(dt.timestamp() * 1000), dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fact(kind: str, payload: dict) -> GovernedCanonicalFactV1:
    body = {**payload, "fact_kind": kind}
    return GovernedCanonicalFactV1(
        fact_kind=kind,
        fact_digest=fact_digest(body),
        payload=body,
        producer_owner=WP_A_PRODUCER,
    )


def _mark(canonical_id: str, offset: int, px: float) -> GovernedCanonicalFactV1:
    ms, iso = _ts(offset)
    return _fact(
        "FinalizedPt1mMarkFactV1",
        {
            "instrument": _instrument(canonical_id),
            "mark_px": str(px),
            "interval_start_ms": ms,
            "confirm": "1",
            "timestamps": {
                "venue_event_time_ms": ms,
                "captured_at": iso,
                "effective_at": iso,
                "source_clock_class": "venue",
            },
            "provenance": {
                "transport": "rest",
                "endpoint_or_channel": "/mark",
                "raw_payload_digest": "b" * 64,
                "session_id": "s",
                "eea_endpoint_family": "public_rest",
            },
            "quality": _quality(),
        },
    )


def _index_fact(offset: int, px: float) -> GovernedCanonicalFactV1:
    ms, iso = _ts(offset)
    return _fact(
        "IndexPriceFactV1",
        {
            "instrument": _instrument(_SELECTED),
            "index_px": str(px),
            "timestamps": {
                "venue_event_time_ms": ms,
                "captured_at": iso,
                "effective_at": iso,
                "source_clock_class": "venue",
            },
            "provenance": {
                "transport": "rest",
                "endpoint_or_channel": "/index",
                "raw_payload_digest": "c" * 64,
                "session_id": "s",
                "eea_endpoint_family": "public_rest",
            },
            "quality": _quality(),
        },
    )


def _marks_from_fixture(canonical_id: str) -> tuple[GovernedCanonicalFactV1, ...]:
    frame = exact_known_61_price_fixture_v1()
    out: list[GovernedCanonicalFactV1] = []
    for i, (ts, row) in enumerate(frame.iterrows()):
        iso = ts.isoformat().replace("+00:00", "Z")
        ms = int(ts.timestamp() * 1000)
        out.append(
            _fact(
                "FinalizedPt1mMarkFactV1",
                {
                    "instrument": _instrument(canonical_id),
                    "mark_px": str(row["mark_price"]),
                    "interval_start_ms": ms,
                    "confirm": "1",
                    "timestamps": {
                        "venue_event_time_ms": ms,
                        "captured_at": iso,
                        "effective_at": iso,
                        "source_clock_class": "venue",
                    },
                    "provenance": {
                        "transport": "rest",
                        "endpoint_or_channel": "/mark",
                        "raw_payload_digest": "d" * 64,
                        "session_id": "s",
                        "eea_endpoint_family": "public_rest",
                    },
                    "quality": _quality(),
                },
            )
        )
    return tuple(out)


def test_derivatives_basis_and_funding_materialized() -> None:
    observed = "2026-06-01T01:00:00Z"
    phase_19 = Phase19OrthogonalMaterializationInputsV1(
        derivatives_mark_fact=_mark(_SELECTED, 60, 101.0),
        derivatives_index_fact=_index_fact(60, 100.0),
        funding_rate_fact=_fact(
            "FundingRateFactV1",
            {
                "instrument": _instrument(_SELECTED),
                "funding_rate": "0.0001",
                "funding_time_ms": _ts(60)[0],
                "timestamps": {
                    "captured_at": observed,
                    "effective_at": observed,
                    "venue_event_time_ms": _ts(60)[0],
                    "source_clock_class": "venue",
                },
                "provenance": {
                    "transport": "rest",
                    "endpoint_or_channel": "/funding",
                    "raw_payload_digest": "e" * 64,
                    "session_id": "s",
                    "eea_endpoint_family": "public_rest",
                },
                "quality": _quality(),
            },
        ),
    )
    record = dict(
        materialize_market_context_v1_from_existing_facts_v1(
            ExistingFactMaterializationRequestV1(
                observed_at=observed,
                instrument_ref=_SELECTED,
                provenance_refs=["prov.phase19"],
                phase_19=phase_19,
            )
        )
    )
    assert record["derivatives_state_ref"]["presence"] == "PRESENT"
    assert record["cross_market_state_ref"]["presence"] == "MISSING"


def test_cross_market_context_only_no_rerank() -> None:
    observed = "2026-06-01T01:00:00Z"
    selected = _marks_from_fixture(_SELECTED)
    anchor = _marks_from_fixture(_ANCHOR)
    phase_19 = Phase19OrthogonalMaterializationInputsV1(
        cross_market_selected_marks=selected,
        cross_market_anchor_marks_by_ref={_ANCHOR: anchor},
    )
    record = dict(
        materialize_market_context_v1_from_existing_facts_v1(
            ExistingFactMaterializationRequestV1(
                observed_at=observed,
                instrument_ref=_SELECTED,
                provenance_refs=["prov.phase19"],
                phase_19=phase_19,
            )
        )
    )
    slot = record["cross_market_state_ref"]
    assert slot["presence"] == "PRESENT"
    assert slot["cross_market_authority"] == CROSS_MARKET_CONTEXT_ONLY
    assert slot.get("rerank_authorized") is not True


def test_anchor_not_in_binding_rejected() -> None:
    observed = "2026-06-01T01:00:00Z"
    bad_anchor = "inst-btc-usdt-perp"
    phase_19 = Phase19OrthogonalMaterializationInputsV1(
        cross_market_selected_marks=_marks_from_fixture(_SELECTED),
        cross_market_anchor_marks_by_ref={bad_anchor: _marks_from_fixture(bad_anchor)},
    )
    with pytest.raises(ExistingFactMaterializationError, match="ANCHOR_NOT_IN_GOVERNED_BINDING"):
        materialize_market_context_v1_from_existing_facts_v1(
            ExistingFactMaterializationRequestV1(
                observed_at=observed,
                instrument_ref=_SELECTED,
                provenance_refs=["prov.phase19"],
                phase_19=phase_19,
            )
        )


def test_deterministic_replay_with_phase_19_changes_context_id() -> None:
    observed = "2026-06-01T01:00:00Z"
    without = dict(
        materialize_market_context_v1_from_existing_facts_v1(
            ExistingFactMaterializationRequestV1(
                observed_at=observed,
                instrument_ref=_SELECTED,
                provenance_refs=["prov.phase19"],
            )
        )
    )
    with_p19 = dict(
        materialize_market_context_v1_from_existing_facts_v1(
            ExistingFactMaterializationRequestV1(
                observed_at=observed,
                instrument_ref=_SELECTED,
                provenance_refs=["prov.phase19"],
                phase_19=Phase19OrthogonalMaterializationInputsV1(
                    derivatives_mark_fact=_mark(_SELECTED, 0, 100.0),
                ),
            )
        )
    )
    assert without["context_id"] != with_p19["context_id"]


def test_authority_negative_proofs() -> None:
    terminal = assert_phase_19_authority_invariants_v1()
    assert terminal["NO_AUTHORITY_EXPANSION"] is True
    assert terminal["CROSS_MARKET_IS_CONTEXT_ONLY"] is True
    binding = load_cross_market_anchor_binding_v1()
    assert binding["rerank_authorized"] is False
