"""Dynamic market / selection evidence contract (observer-only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.dynamic_market_selection_evidence_contract_v1 import (
    CONTRACT_AUTHORITY,
    PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION,
    RELATIONAL_EVIDENCE_FAILURE,
    RELATION_FAIL,
    RELATION_PASS,
    RELATION_UNKNOWN,
    DynamicMarketSelectionObservationContextV1,
    build_dynamic_market_selection_evidence_contract_v1,
    build_observation_context_from_evidence_root_v1,
    classify_ghv_path_evidence_semantics_v1,
    native_correlation_key_from_instrument_id_v1,
    observation_context_from_mapping_v1,
    path_relational_integrity_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
    build_whole_cycle_observability_v1,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1]
SAND_FIXTURE = (
    FIXTURE_ROOT
    / "fixtures"
    / "ops"
    / "dynamic_market_selection_evidence_sand_combined_ghv_v1.json"
)
COMBINED_EVIDENCE = Path(
    "evidence/ops/combined_ghv_whole_cycle_canary_measurement_v1/20261002T074052Z"
)


def _ctx(**kwargs: object) -> DynamicMarketSelectionObservationContextV1:
    base = observation_context_from_mapping_v1(json.loads(SAND_FIXTURE.read_text()))
    return DynamicMarketSelectionObservationContextV1(
        run_id=kwargs.get("run_id", base.run_id),
        cycle_index=kwargs.get("cycle_index", base.cycle_index),
        selected_instrument=str(kwargs.get("selected_instrument", base.selected_instrument)),
        bound_instrument=kwargs.get("bound_instrument", base.bound_instrument),
        observed_instrument_id=str(
            kwargs.get("observed_instrument_id", base.observed_instrument_id)
        ),
        reference_price=str(kwargs.get("reference_price", base.reference_price)),
        sizing_state=kwargs.get("sizing_state", base.sizing_state),
        decision_outcome=str(kwargs.get("decision_outcome", base.decision_outcome)),
        selected_side=str(kwargs.get("selected_side", base.selected_side)),
        pre_external_reached=kwargs.get("pre_external_reached", base.pre_external_reached),
        policy_outcome=str(kwargs.get("policy_outcome", base.policy_outcome)),
        fresh_pretrade_captured=kwargs.get("fresh_pretrade_captured", base.fresh_pretrade_captured),
        observation_stage=base.observation_stage,
        source_provenance=base.source_provenance,
    )


def test_same_instrument_changing_price_is_dynamic_not_drift() -> None:
    ctx_a = _ctx(reference_price="0.05748")
    ctx_b = _ctx(reference_price="0.06100")
    report_a = build_dynamic_market_selection_evidence_contract_v1(ctx_a)
    report_b = build_dynamic_market_selection_evidence_contract_v1(ctx_b)
    prices_a = [
        o["observed_value"]
        for o in report_a["dynamic_value_observations"]
        if o["field_name"] == "reference_price"
    ]
    prices_b = [
        o["observed_value"]
        for o in report_b["dynamic_value_observations"]
        if o["field_name"] == "reference_price"
    ]
    assert prices_a != prices_b
    assert report_a["ghv_path_evidence_semantics"]["DYNAMIC_VALUE_CHANGE_IS_NOT_DRIFT"] is True
    assert path_relational_integrity_v1(report_a["relational_evidence"]) == "PASS"


def test_different_instrument_internally_consistent_accepted() -> None:
    bound = {
        "instrument_id": "okx_eea:linear_perpetual:PROS:USDT:USDT:pros-usdt-swap",
        "venue_native_id": "PROS-USDT-SWAP",
        "selected_future_count": 1,
        "max_positions_effective": 1,
        "ranking_snapshot_id": "x",
        "ranking_integrity_digest": "x",
        "universe_snapshot_id": "x",
        "selection_id": "x",
        "selection_integrity_digest": "x",
        "selection_state": "SELECTED",
    }
    ctx = _ctx(
        selected_instrument="PROS-USDT-SWAP",
        bound_instrument=bound,
        observed_instrument_id=bound["instrument_id"],
        reference_price="1.23",
    )
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    sel_rel = next(
        r
        for r in report["relational_evidence"]
        if r["relation_name"] == "SELECTION_TO_BINDING_IDENTITY"
    )
    assert sel_rel["relation_status"] == RELATION_PASS


def test_cross_instrument_relational_mismatch_detected() -> None:
    sizing = dict(_ctx().sizing_state or {})
    envelope = dict(sizing.get("scope_capital_envelope") or {})
    envelope["instrument_id"] = "okx_eea:linear_perpetual:PROS:USDT:USDT:pros-usdt-swap"
    sizing["scope_capital_envelope"] = envelope
    ctx = _ctx(
        selected_instrument="SAND-USDT-SWAP",
        observed_instrument_id=envelope["instrument_id"],
        sizing_state=sizing,
    )
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    market_rel = next(
        r
        for r in report["relational_evidence"]
        if r["relation_name"] == "BINDING_TO_MARKET_IDENTITY"
    )
    assert market_rel["relation_status"] == RELATION_FAIL
    assert (
        classify_ghv_path_evidence_semantics_v1(
            relations=report["relational_evidence"],
            pre_external_reached=False,
            policy_outcome="BLOCKED",
        )["GHV_PATH_EVIDENCE_CLASSIFICATION"]
        == RELATIONAL_EVIDENCE_FAILURE
    )


def test_capital_sizing_change_not_drift() -> None:
    sizing = dict(_ctx().sizing_state or {})
    sizing["final_quantity"] = "0"
    ctx = _ctx(sizing_state=sizing, policy_outcome="BLOCKED")
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    assert any(o["field_name"] == "final_quantity" for o in report["dynamic_value_observations"])


def test_legitimate_blocked_not_path_failure() -> None:
    report = build_dynamic_market_selection_evidence_contract_v1(_ctx())
    semantics = report["ghv_path_evidence_semantics"]
    assert (
        semantics["GHV_PATH_EVIDENCE_CLASSIFICATION"]
        == PATH_CORRECT_WITH_LEGITIMATE_POLICY_REJECTION
    )
    assert semantics["POLICY_OUTCOME"] == "BLOCKED"
    assert semantics["PRE_EXTERNAL_REACHED"] is False


def test_unknown_provenance_not_fabricated_pass() -> None:
    ctx = DynamicMarketSelectionObservationContextV1(
        selected_instrument="SAND-USDT-SWAP",
        sizing_state={"outcome": "BLOCKED", "reason_codes": ["BELOW_MIN_QUANTITY"]},
    )
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    explained = next(
        r for r in report["relational_evidence"] if r["relation_name"] == "SIZING_OUTCOME_EXPLAINED"
    )
    assert explained["relation_status"] == RELATION_UNKNOWN


def test_pre_external_false_when_relational_integrity_passes() -> None:
    report = build_dynamic_market_selection_evidence_contract_v1(_ctx())
    assert report["ghv_path_evidence_semantics"]["PATH_RELATIONAL_INTEGRITY"] == "PASS"
    assert report["ghv_path_evidence_semantics"]["PRE_EXTERNAL_REACHED"] is False


def test_post_safety_invariants_stable() -> None:
    report = build_dynamic_market_selection_evidence_contract_v1(_ctx())
    post_rel = next(
        r for r in report["relational_evidence"] if r["relation_name"] == "POST_AUTHORITY_INVARIANT"
    )
    assert post_rel["relation_status"] == RELATION_PASS
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False


def test_observer_authority_none() -> None:
    report = build_dynamic_market_selection_evidence_contract_v1(_ctx())
    assert report["authority"] == CONTRACT_AUTHORITY
    assert CONTRACT_AUTHORITY == "NONE"


def test_sand_fixture_regression_without_universal_expected_values() -> None:
    ctx = observation_context_from_mapping_v1(json.loads(SAND_FIXTURE.read_text()))
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    assert ctx.selected_instrument == "SAND-USDT-SWAP"
    assert "BELOW_MIN_QUANTITY" in json.dumps(report["dynamic_value_observations"])
    explained = next(
        r for r in report["relational_evidence"] if r["relation_name"] == "SIZING_OUTCOME_EXPLAINED"
    )
    assert explained["relation_status"] == RELATION_UNKNOWN
    assert report["ghv_path_evidence_semantics"]["PRE_EXTERNAL_REACHED"] is False


def test_native_correlation_key() -> None:
    key = native_correlation_key_from_instrument_id_v1(
        "okx_eea:linear_perpetual:SAND:USDT:USDT:sand-usdt-swap"
    )
    assert key == "SAND-USDT-SWAP"


@pytest.mark.skipif(
    not (Path.cwd() / COMBINED_EVIDENCE).is_dir(),
    reason="combined GHV evidence not present locally",
)
def test_build_context_from_combined_evidence_root() -> None:
    ctx = build_observation_context_from_evidence_root_v1(Path.cwd() / COMBINED_EVIDENCE)
    assert ctx is not None
    assert ctx.selected_instrument == "SAND-USDT-SWAP"
    report = build_dynamic_market_selection_evidence_contract_v1(ctx)
    assert report["ghv_path_evidence_semantics"]["PATH_RELATIONAL_INTEGRITY"] in {
        "PASS",
        "UNKNOWN_CURRENT",
    }


def test_whole_cycle_bundle_includes_dynamic_contract(tmp_path: Path) -> None:
    evidence = Path.cwd() / COMBINED_EVIDENCE
    if not evidence.is_dir():
        pytest.skip("combined GHV evidence not present locally")
    bundle = build_whole_cycle_observability_v1(evidence_root=evidence, harness_report=None)
    assert bundle.get("dynamic_market_selection_evidence") is not None
