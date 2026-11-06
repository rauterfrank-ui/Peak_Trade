"""Phase 22 incremental information-set identity and B-stage boundary tests."""

from __future__ import annotations

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.incremental_information_set_v1 import (
    CONTEXT_FAMILY_SLOT_SCHEMA,
    FAMILY_DERIVATIVES_STATE,
    INCREMENTAL_INFORMATION_SET_SCHEMA,
    STAGE_B0,
    STAGE_B1,
    STAGE_B2,
    STAGE_B3,
    STAGE_B4,
    STAGE_B5,
    STAGE_CHAIN,
    IncrementalInformationSetError,
    IncrementalInformationSetRequestV1,
    TrueL2AdmissibilityStatus,
    assert_market_context_respects_stage_boundary_v1,
    build_incremental_information_set_v1,
    census_true_l2_research_substrate_v1,
    excluded_context_families_v1,
    included_context_families_v1,
    predecessor_stage_id_v1,
    project_market_context_to_stage_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.market_context_v1 import (
    CROSS_MARKET_CONTEXT_ONLY,
    GovernedMarketContextInputsV1,
    MICROSTRUCTURE_KIND_PROXY_OHLCV,
    compose_market_context_v1_from_governed_inputs,
)

_OBS = "2026-09-01T12:00:00Z"
_INST = "inst-eth-usdt-perp"


def _slot(ref: str, *, micro_kind: str | None = None) -> dict:
    body = {
        "schema_version": CONTEXT_FAMILY_SLOT_SCHEMA,
        "presence": "PRESENT",
        "state_ref": ref,
        "pit_observed_at_utc": _OBS,
        "producer_owner": "test.phase22",
        "producer_ownership": "GOVERNED_TEST",
        "feature_version": "phase22_test_v1",
    }
    if micro_kind is not None:
        body["microstructure_kind"] = micro_kind
    if ref.startswith("cross."):
        body["cross_market_authority"] = CROSS_MARKET_CONTEXT_ONLY
    return body


def _full_source_context() -> dict:
    ctx = compose_market_context_v1_from_governed_inputs(
        GovernedMarketContextInputsV1(
            observed_at=_OBS,
            instrument_ref=_INST,
            information_set_identity_body={"fixture": "phase22_full"},
            provenance_refs=["mi.provenance.phase22.test"],
            feature_versions={"market_context_v1": "market_context_v1", "fixture": "v1"},
            price_state=_slot("price.phase22"),
            flow_state=_slot("flow.phase22"),
            liquidity_microstructure_state=_slot(
                "micro.phase22", micro_kind=MICROSTRUCTURE_KIND_PROXY_OHLCV
            ),
            derivatives_state=_slot("deriv.phase22"),
            cross_market_state=_slot("cross.phase22"),
            volatility_state=_slot("vol.phase22"),
        )
    )
    return dict(ctx)


def _info_set(stage_id: str) -> dict:
    return dict(
        build_incremental_information_set_v1(
            IncrementalInformationSetRequestV1(
                stage_id=stage_id,
                horizon_identity={"n_bars": 2, "bar_spec_ref": "bar.spec.test"},
                feature_versions={"fixture": "v1"},
                provenance_refs=["mi.provenance.phase22.test"],
            )
        )
    )


def test_predecessor_chain_and_identity_changes_with_stage() -> None:
    assert predecessor_stage_id_v1(STAGE_B0) is None
    assert predecessor_stage_id_v1(STAGE_B3) == STAGE_B2
    b0 = _info_set(STAGE_B0)
    b1 = _info_set(STAGE_B1)
    assert b0["information_set_id"] != b1["information_set_id"]
    assert b0["schema_version"] == INCREMENTAL_INFORMATION_SET_SCHEMA
    assert included_context_families_v1(STAGE_B1) - included_context_families_v1(STAGE_B0) == {
        "LIQUIDITY_MICROSTRUCTURE"
    }


def test_b0_boundary_excludes_later_families() -> None:
    source = _full_source_context()
    info = _info_set(STAGE_B0)
    projected = dict(
        project_market_context_to_stage_v1(
            source, stage_id=STAGE_B0, information_set_id=str(info["information_set_id"])
        )
    )
    assert_market_context_respects_stage_boundary_v1(projected, stage_id=STAGE_B0)
    for family in excluded_context_families_v1(STAGE_B0):
        assert family not in included_context_families_v1(STAGE_B0)


def test_b1_adds_proxy_microstructure_only() -> None:
    source = _full_source_context()
    info = _info_set(STAGE_B1)
    projected = dict(
        project_market_context_to_stage_v1(
            source, stage_id=STAGE_B1, information_set_id=str(info["information_set_id"])
        )
    )
    micro = projected["liquidity_microstructure_state_ref"]
    assert micro["presence"] == "PRESENT"
    assert micro["microstructure_kind"] == MICROSTRUCTURE_KIND_PROXY_OHLCV


def test_b5_deferred_without_true_l2_substrate() -> None:
    census = census_true_l2_research_substrate_v1()
    assert census["b5_status"] == TrueL2AdmissibilityStatus.DEFERRED_NOT_CURRENTLY_ADMISSIBLE.value
    info = _info_set(STAGE_B5)
    assert info["b5_status"] == TrueL2AdmissibilityStatus.DEFERRED_NOT_CURRENTLY_ADMISSIBLE.value
    with pytest.raises(IncrementalInformationSetError):
        project_market_context_to_stage_v1(
            _full_source_context(),
            stage_id=STAGE_B5,
            information_set_id=str(info["information_set_id"]),
        )


def test_derivatives_missing_yields_insufficient_source_for_b2() -> None:
    source = compose_market_context_v1_from_governed_inputs(
        GovernedMarketContextInputsV1(
            observed_at=_OBS,
            instrument_ref=_INST,
            information_set_identity_body={"fixture": "phase22_no_deriv"},
            provenance_refs=["mi.provenance.phase22.test"],
            feature_versions={"fixture": "v1"},
            price_state=_slot("price.phase22"),
            flow_state=_slot("flow.phase22"),
            liquidity_microstructure_state=_slot(
                "micro.phase22", micro_kind=MICROSTRUCTURE_KIND_PROXY_OHLCV
            ),
            derivatives_state=None,
        )
    )
    info = _info_set(STAGE_B2)
    with pytest.raises(IncrementalInformationSetError):
        project_market_context_to_stage_v1(
            dict(source),
            stage_id=STAGE_B2,
            information_set_id=str(info["information_set_id"]),
        )


def test_deterministic_information_set_replay() -> None:
    req = IncrementalInformationSetRequestV1(
        stage_id=STAGE_B4,
        horizon_identity={"n_bars": 2},
        feature_versions={"fixture": "v1"},
        provenance_refs=["mi.provenance.phase22.test"],
    )
    first = build_incremental_information_set_v1(req)
    second = build_incremental_information_set_v1(req)
    assert first["information_set_id"] == second["information_set_id"]
    assert first["content_digest"] == second["content_digest"]


def test_stage_chain_covers_b0_through_b5() -> None:
    assert STAGE_CHAIN == (STAGE_B0, STAGE_B1, STAGE_B2, STAGE_B3, STAGE_B4, STAGE_B5)
    assert FAMILY_DERIVATIVES_STATE in included_context_families_v1(STAGE_B2)
    assert "VOLATILITY_STATE" in included_context_families_v1(STAGE_B4)
