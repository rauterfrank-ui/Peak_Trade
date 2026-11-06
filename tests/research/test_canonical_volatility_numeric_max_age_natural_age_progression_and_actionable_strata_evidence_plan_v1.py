"""Focused tests for natural age progression + actionable strata evidence plan v1."""

from __future__ import annotations

import math
from pathlib import Path

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1 import (
    NaturalAgeProgressionLifecycleHostV1,
    assert_architecture_guards_v1,
    assign_age_bucket_v1,
    build_additional_evidence_coverage_plan_v1,
    build_natural_age_research_recompute_policy_v1,
    compute_natural_age_seconds_v1,
    evaluate_counterfactual_candidate_impact_v1,
    lifecycle_state_machine_matrix_v1,
    producer_consumer_call_graph_matrix_v1,
    project_actionable_alpha_strata_v1,
    project_safety_risk_exit_observability_v1,
    recompute_trigger_matrix_v1,
    verify_additional_evidence_coverage_plan_artifact_v1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    CAPABILITY_ID,
    NUMERIC_MAX_AGE_ENFORCING,
    NUMERIC_MAX_AGE_SELECTED,
    PACKAGE_MARKER,
    RESEARCH_AGE_GRID_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS,
    RESEARCH_WIRING_LABEL,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    LifecycleOutcomeV1,
    NaturalAgeLifecycleErrorV1,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.recompute_policy_v1 import (
    ResearchEstimateRecomputePolicyV1,
    evaluate_recompute_decision_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)

ROOT = Path(__file__).resolve().parents[2]
VENUE = "okx"
CANON = "ETH-USD_UM_XPERP-310404"
VENUE_INST = "ETH-USD_UM_XPERP-310404"
T0 = 1_700_000_000.0


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _sample(i: int) -> MarketSampleIdentityV1:
    return MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        event_time=EventTimeInstantV1(unix_seconds=T0 + float(i * 60)),
        mark_price=_price_at(i),
    )


def _host(tmp_path: Path | None = None) -> NaturalAgeProgressionLifecycleHostV1:
    path = None if tmp_path is None else tmp_path / "mark_history.json"
    return NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        persistence_path=path,
    )


def _ingest(host: NaturalAgeProgressionLifecycleHostV1, i: int):
    return host.ingest_finalized_pt1m_mark_sample_v1(
        sample=_sample(i),
        transport=ObservationTransportMetadataV1(receive_time=T0 + i * 60 + 0.5),
    )


def _warmup_to_first_produce(host: NaturalAgeProgressionLifecycleHostV1):
    for i in range(0, 60):
        obs = _ingest(host, i)
        assert obs.outcome == LifecycleOutcomeV1.WARMUP.value
    produced = _ingest(host, 60)
    assert produced.outcome == LifecycleOutcomeV1.PRODUCED.value
    assert produced.age_seconds == 0.0
    assert produced.reuse_count == 0
    assert produced.estimate_reused is False
    return produced


def test_package_guards_and_markers() -> None:
    guards = assert_architecture_guards_v1(repo_root=ROOT)
    assert guards["guards_pass"] is True
    assert PACKAGE_MARKER.endswith("=true")
    assert CAPABILITY_ID.endswith("EVIDENCE_PLAN_V1")
    assert NUMERIC_MAX_AGE_SELECTED is False
    assert NUMERIC_MAX_AGE_ENFORCING is False


def test_forensic_and_state_machine_matrices_present() -> None:
    graph = producer_consumer_call_graph_matrix_v1()
    assert "producer" in graph
    assert "consumers" in graph
    assert graph["root_cause"]["session_02_symptom"]["max_age_seconds"] == 0.0
    sm = lifecycle_state_machine_matrix_v1()
    assert any(t["to"] == "REUSED" for t in sm["transitions"])
    matrix = recompute_trigger_matrix_v1()
    assert matrix["explicitly_not_max_age_threshold"] is True
    assert matrix["policy"]["research_wiring_label"] == RESEARCH_WIRING_LABEL


def test_freshly_produced_age_zero_reuse_zero() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    assert produced.age_seconds == 0.0
    assert produced.reuse_count == 0
    assert produced.distinct_observations_since_recompute == 0


def test_distinct_observations_reuse_and_natural_age_progression() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    as_of = produced.as_of_event_time
    source = produced.source_digest
    reused = _ingest(host, 61)
    assert reused.outcome == LifecycleOutcomeV1.REUSED.value
    assert reused.estimate_reused is True
    assert reused.as_of_event_time == as_of
    assert reused.source_digest == source
    assert reused.age_seconds == 60.0
    assert reused.reuse_count == 1
    reused2 = _ingest(host, 62)
    assert reused2.age_seconds == 120.0
    assert reused2.as_of_event_time == as_of
    assert reused2.reuse_count == 2


def test_duplicate_observation_does_not_advance_counters() -> None:
    host = _host()
    _warmup_to_first_produce(host)
    first = _ingest(host, 61)
    dup = _ingest(host, 61)
    assert dup.outcome == LifecycleOutcomeV1.DUPLICATE_NOOP.value
    assert dup.age_evaluable is False
    assert dup.reuse_count == first.reuse_count
    assert dup.distinct_observations_since_recompute == first.distinct_observations_since_recompute


def test_out_of_order_not_evaluable_no_negative_age() -> None:
    host = _host()
    _warmup_to_first_produce(host)
    _ingest(host, 65)
    ooo = _ingest(host, 63)
    assert ooo.outcome == LifecycleOutcomeV1.OUT_OF_ORDER_NOT_EVALUABLE.value
    assert ooo.age_evaluable is False
    assert ooo.age_seconds is None


def test_recompute_trigger_resets_age_and_digests() -> None:
    # Use a tiny research wiring policy for deterministic unit coverage.
    tiny = ResearchEstimateRecomputePolicyV1(
        policy_id="unit_test_recompute_wiring",
        policy_version="unit/v1",
        research_wiring_label=RESEARCH_WIRING_LABEL,
        minimum_new_distinct_observations=2,
        minimum_event_time_elapsed_seconds=10_000_000,
        source_window_ordinary_slide_does_not_recompute=True,
        session_start_behavior="PRODUCE_ON_FIRST_VALID_ESTIMATE_AFTER_WARMUP",
        missing_estimate_behavior="PRODUCE_WHEN_MATERIALIZATION_AVAILABLE",
        invalid_estimate_behavior="DO_NOT_REUSE_FAIL_CLOSED_OR_NOT_EVALUABLE",
        out_of_order_sample_behavior="REJECT_NOT_EVALUABLE_NO_NEGATIVE_AGE",
        duplicate_sample_behavior="NOOP_NO_AGE_NO_REUSE_NO_DISTINCT_ADVANCE",
        process_restart_behavior="RESTART_WITHOUT_ESTIMATE_UNTIL_FRESH_PRODUCE_NO_REMATERIALIZE_AS_FRESH",
        derivation_notes=("unit-test-only",),
    )
    host = NaturalAgeProgressionLifecycleHostV1.create(
        venue=VENUE,
        canonical_instrument_id=CANON,
        venue_instrument_id=VENUE_INST,
        policy=tiny,
    )
    produced = _warmup_to_first_produce(host)
    _ingest(host, 61)  # reuse_count=1, distinct=1
    _ingest(host, 62)  # reuse_count=2, distinct=2
    recomputed = _ingest(host, 63)
    assert recomputed.outcome == LifecycleOutcomeV1.RECOMPUTED.value
    assert recomputed.age_seconds == 0.0
    assert recomputed.reuse_count == 0
    assert recomputed.source_digest != produced.source_digest
    assert recomputed.as_of_event_time != produced.as_of_event_time


def test_runtime_cycle_does_not_advance_age() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    reused = _ingest(host, 61)
    noop = host.on_runtime_cycle_without_sample_v1()
    assert noop.outcome == LifecycleOutcomeV1.RUNTIME_CYCLE_NOOP.value
    assert noop.age_seconds is None
    assert host.lifecycle_state is not None
    assert host.lifecycle_state.reuse_count == reused.reuse_count
    assert host.lifecycle_state.as_of_event_time.isoformat() == produced.as_of_event_time


def test_negative_age_fails_closed() -> None:
    try:
        compute_natural_age_seconds_v1(
            market_event_time="2026-08-01T00:00:00+00:00",
            as_of_event_time="2026-08-01T00:01:00+00:00",
        )
        raise AssertionError("expected negative age to fail closed")
    except NaturalAgeLifecycleErrorV1 as exc:
        assert "negative_age" in str(exc)


def test_counterfactual_candidate_discrimination_and_incremental_block() -> None:
    records = [
        {
            "evidence_record_id": "evr_a",
            "age_seconds": 90.0,
            "estimate_present": True,
            "decision_outcome": "entry",
            "selected_side": "long",
            "exit_path_preservation": True,
            "data_trust_state": "TRUSTED",
            "regime_label": "UP_DIRECTIONAL",
        },
        {
            "evidence_record_id": "evr_b",
            "age_seconds": 90.0,
            "estimate_present": True,
            "decision_outcome": "blocked",
            "selected_side": "none",
            "exit_path_preservation": True,
            "data_trust_state": "TRUSTED",
            "regime_label": "INSUFFICIENT_DATA",
        },
    ]
    impact = evaluate_counterfactual_candidate_impact_v1(records)
    assert impact["candidate_discrimination_observed"] is True
    by = {row["candidate_max_age_seconds"]: row for row in impact["per_candidate"]}
    assert by[60]["stale_count"] == 2
    assert by[60]["incremental_age_only_block_count"] == 1
    assert by[60]["already_blocked_for_other_reason"] == 1
    assert by[60]["long_selected_affected"] == 1
    assert by[60]["entry_opportunity_affected"] == 1
    assert by[120]["fresh_count"] == 2
    assert by[120]["incremental_age_only_block_count"] == 0
    assert impact["incremental_age_only_effect_observed"] is True


def test_safety_risk_exit_independence_under_stale() -> None:
    strata = project_actionable_alpha_strata_v1(
        productive_record={
            "age_seconds": 500.0,
            "decision_outcome": "entry",
            "selected_side": "short",
            "exit_path_preservation": True,
            "risk_action_available": True,
            "reconciliation_action_available": True,
            "data_trust_state": "TRUSTED",
            "regime_label": "DOWN_DIRECTIONAL",
        }
    )
    obs = project_safety_risk_exit_observability_v1(strata=strata, counterfactual_stale=True)
    assert obs.alpha_only_counterfactual_block is True
    assert obs.exit_counterfactual_block is False
    assert obs.actions_available_when_stale["SAFETY_EXIT"] is True
    assert obs.actions_available_when_stale["HARD_RISK_REDUCE"] is True
    assert obs.actions_available_when_stale["POSITION_RECONCILIATION"] is True


def test_age_bucket_assignment_matches_grid() -> None:
    assert assign_age_bucket_v1(0.0) == "AGE_LE_60_S"
    assert assign_age_bucket_v1(60.0) == "AGE_LE_60_S"
    assert assign_age_bucket_v1(61.0) == "AGE_LE_120_S"
    assert assign_age_bucket_v1(7200.0) == "AGE_LE_7200_S"
    assert assign_age_bucket_v1(7201.0) == "AGE_GT_7200_S"
    assert tuple(RESEARCH_AGE_GRID_SECONDS) == (60, 120, 300, 600, 900, 1800, 3600, 7200)


def test_coverage_plan_artifact_and_no_session_authorization() -> None:
    plan = build_additional_evidence_coverage_plan_v1()
    assert plan.minimum_productive_sessions >= 2
    assert plan.natural_7200_second_reachability_required is True
    assert plan.session_execution_authorized is False
    assert plan.authorization_issuance_authorized is False
    assert plan.numeric_max_age_selected is False
    verified = verify_additional_evidence_coverage_plan_artifact_v1(repo_root=ROOT)
    assert verified["plan_digest"] == plan.plan_digest
    policy = build_natural_age_research_recompute_policy_v1()
    assert policy.minimum_new_distinct_observations == (
        RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS
    )
    assert policy.is_max_age_policy is False


def test_evidence_determinism_for_strata_projection() -> None:
    payload = {
        "age_seconds": 180.0,
        "estimate_reused": True,
        "reuse_count": 3,
        "distinct_observations_since_recompute": 3,
        "decision_outcome": "hold",
        "selected_side": "long",
        "regime_label": "CHOP_OR_RANGE",
        "data_trust_state": "TRUSTED",
        "exit_path_preservation": True,
    }
    a = project_actionable_alpha_strata_v1(productive_record=payload).to_dict()
    b = project_actionable_alpha_strata_v1(productive_record=payload).to_dict()
    assert digest_excluding_keys(a, exclude=()) == digest_excluding_keys(b, exclude=())


def test_ratified_recompute_policy_does_not_fire_on_ordinary_slide() -> None:
    host = _host()
    produced = _warmup_to_first_produce(host)
    # Ordinary next sample must reuse under ratified policy (121 obs floor).
    reused = _ingest(host, 61)
    assert reused.outcome == LifecycleOutcomeV1.REUSED.value
    assert reused.source_digest == produced.source_digest
    decision = evaluate_recompute_decision_v1(
        policy=build_natural_age_research_recompute_policy_v1(),
        prior_state=host.lifecycle_state,
        current_market_event_time=reused.market_event_time,
        newly_materialized_source_digest="different-digest-from-sliding-window",
    )
    assert decision[0] is False
