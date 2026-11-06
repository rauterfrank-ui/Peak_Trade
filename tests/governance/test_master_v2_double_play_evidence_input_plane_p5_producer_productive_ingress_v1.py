"""Contract, bypass, census, and A-termination tests for P5 producer ingress."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    ADMIT_DISPOSITION,
    REJECT_DISPOSITION,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1 import (
    DIRECT_PRODUCER_TO_B_BYPASS,
    DIRECT_PRODUCER_TO_DP_BYPASS,
    IMPLEMENTS_P5_PRODUCER_PRODUCTIVE_INGRESS,
    PRODUCER_TRADING_AUTHORITY,
    build_authority_negative_proofs_v1,
    build_p5_producer_closure_matrix_v1,
    prove_p5_producer_productive_ingress_v1,
    run_meta_learning_contract_crosswalk_v1,
    run_meta_learning_lineage_census_v1,
    run_optimization_contract_crosswalk_v1,
    run_optimization_lineage_census_v1,
    run_p5_producer_census_v1,
    run_p5_upstream_invocation_proofs_v1,
    scan_producer_class_bypass_v1,
    terminate_learning_conditioned_evaluative_at_a_v1,
    terminate_market_intelligence_market_context_at_a_v1,
    terminate_meta_learning_routed_at_a_v1,
    terminate_optimization_envelope_at_a_v1,
    validate_p5_producer_ingress_authority_contract_v1,
    write_p5_proof_artifacts_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.adapters_v1 import (
    default_termination_context_from_market_context_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.loop_a_conditioned_learning_evidence_v1 import (
    ConditionedLearningComposeInputsV1,
    compose_conditioned_mi_learning_evidence_v1,
    run_loop_a_conditioned_learning_cycle_v1,
)
from tests.learning.test_loop_a_conditioned_learning_evidence_v1 import (
    _mint_forecast,
    _observation_for_n,
    _realized_behavior,
)
from tests.learning.test_market_context_realized_behavior_join_v1 import _context_for_observation

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_p5_authority_constants() -> None:
    assert IMPLEMENTS_P5_PRODUCER_PRODUCTIVE_INGRESS is True
    assert PRODUCER_TRADING_AUTHORITY == "NONE"
    assert DIRECT_PRODUCER_TO_B_BYPASS is False
    assert DIRECT_PRODUCER_TO_DP_BYPASS is False
    assert validate_p5_producer_ingress_authority_contract_v1().ok


def test_producer_bypass_scan_clean() -> None:
    ok, hits = scan_producer_class_bypass_v1(REPO_ROOT)
    assert ok, hits


def test_mi_and_learning_terminate_at_a_admit() -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    record = compose_conditioned_mi_learning_evidence_v1(
        ConditionedLearningComposeInputsV1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            market_context=ctx,
            realized_behavior=rb,
            realized_direction="UP",
        )
    )
    termination = default_termination_context_from_market_context_v1(
        ctx, market_observation_epoch=0
    )
    mi = terminate_market_intelligence_market_context_at_a_v1(
        ctx, termination=termination, repo_root=REPO_ROOT
    )
    learn = terminate_learning_conditioned_evaluative_at_a_v1(
        record, termination=termination, repo_root=REPO_ROOT
    )
    assert mi.adjudication.disposition == ADMIT_DISPOSITION
    assert learn.adjudication.disposition == ADMIT_DISPOSITION
    assert mi.adjudication.envelope is not None
    assert mi.adjudication.envelope.trading_authority == "NONE"


def test_deterministic_mi_adjudication_digest() -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    termination = default_termination_context_from_market_context_v1(
        ctx, market_observation_epoch=0
    )
    first = terminate_market_intelligence_market_context_at_a_v1(
        ctx, termination=termination, repo_root=REPO_ROOT
    )
    second = terminate_market_intelligence_market_context_at_a_v1(
        ctx, termination=termination, repo_root=REPO_ROOT
    )
    assert first.adjudication.adjudication_digest == second.adjudication.adjudication_digest


def test_optimization_and_meta_wrong_schema_blocked_at_promotion() -> None:
    opt = terminate_optimization_envelope_at_a_v1(
        {"schema_version": "canonical_optimization_experiment_evidence_v1"},
        source_artifact_schema="canonical_optimization_experiment_evidence_v1",
        source_content_digest="a" * 64,
        termination=default_termination_context_from_market_context_v1(
            _context_for_observation(_observation_for_n(n_bars=2)),
            market_observation_epoch=0,
        ),
        repo_root=REPO_ROOT,
    )
    meta = terminate_meta_learning_routed_at_a_v1(
        {"schema_version": "meta_evidence_v1"},
        source_artifact_schema="meta_evidence_v1",
        source_content_digest="b" * 64,
        termination=default_termination_context_from_market_context_v1(
            _context_for_observation(_observation_for_n(n_bars=2)),
            market_observation_epoch=0,
        ),
        repo_root=REPO_ROOT,
    )
    assert opt.blocked_at_promotion is True
    assert meta.blocked_at_promotion is True
    assert (
        ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
        in opt.adjudication.reason_codes
    )


def test_loop_a_cycle_includes_a_termination(tmp_path: Path) -> None:
    obs = _observation_for_n(n_bars=2)
    ctx = _context_for_observation(obs)
    rb = _realized_behavior(obs=obs, ctx=ctx)
    forecast = _mint_forecast(n_bars=2, bar_spec_ref=str(obs["bar_spec_ref"]))
    cycle = run_loop_a_conditioned_learning_cycle_v1(
        store_root=tmp_path / "p5_loop_a",
        inputs=ConditionedLearningComposeInputsV1(
            forecast_evidence=forecast,
            evaluation_observation=obs,
            market_context=ctx,
            realized_behavior=rb,
            realized_direction="UP",
        ),
    )
    term = cycle.get("master_v2_evidence_plane_a_termination")
    assert term is not None
    assert term["market_intelligence"]["disposition"] == ADMIT_DISPOSITION
    assert term["learning"]["disposition"] == ADMIT_DISPOSITION


def test_optimization_lineage_classification_a_after_closure() -> None:
    lineage = run_optimization_lineage_census_v1(REPO_ROOT)
    assert lineage["classification"] == "A"
    assert lineage["productive_lineage_proven"] is True
    assert lineage["promotion_to_a_mechanically_allowed"] is True


def test_meta_learning_lineage_classification_b_after_closure() -> None:
    lineage = run_meta_learning_lineage_census_v1(REPO_ROOT)
    assert lineage["classification"] == "B"
    assert lineage["productive_lineage_proven"] is True
    assert lineage["meta_evidence_v1_vs_p2_kind_relation"]["equated"] is False


def test_closure_matrix_all_producers_terminate_at_a() -> None:
    matrix = build_p5_producer_closure_matrix_v1(REPO_ROOT)
    assert matrix["market_intelligence"]["TERMINATES_AT_A"] is True
    assert matrix["learning"]["TERMINATES_AT_A"] is True
    assert matrix["optimization"]["TERMINATES_AT_A"] is True
    assert matrix["meta_learning"]["TERMINATES_AT_A"] is True


def test_optimization_contract_crosswalk_allows_producer_bridge() -> None:
    crosswalk = run_optimization_contract_crosswalk_v1()
    assert crosswalk["producer_bridge_allowed"] is True
    assert crosswalk["verdict"] == "MECHANICALLY_ALLOWED"


def test_meta_learning_contract_crosswalk_allows_without_equating_meta_evidence_v1() -> None:
    crosswalk = run_meta_learning_contract_crosswalk_v1()
    assert crosswalk["producer_bridge_allowed"] is True
    assert crosswalk["meta_evidence_v1_equated_to_target"] is False
    assert crosswalk["verdict"] == "MECHANICALLY_ALLOWED"


def test_upstream_invocation_productive_reachable_at_a() -> None:
    proofs = run_p5_upstream_invocation_proofs_v1()
    assert proofs["optimization"]["productive_reachable_proven"] is True
    assert proofs["meta_learning"]["productive_reachable_proven"] is True


def test_authority_negative_proofs_none() -> None:
    neg = build_authority_negative_proofs_v1()
    assert neg["PRODUCER_TRADING_AUTHORITY"] == "NONE"
    assert neg["EXECUTION_EFFECT"] == "NONE"
    assert neg["PRODUCTIVE_ACTIVATION_AUTHORIZED"] == "false"


def test_census_and_proof_bundle() -> None:
    census = run_p5_producer_census_v1(REPO_ROOT)
    assert len(census["entries"]) == 4
    out = write_p5_proof_artifacts_v1(REPO_ROOT)
    assert (out / "p5_proof_bundle_v1.json").is_file()
    proof = prove_p5_producer_productive_ingress_v1(REPO_ROOT)
    assert proof["verdict"] in {"PROVEN_COMPLETE", "FAIL_CLOSED"}
    assert proof["proof_obligations"]["proof_12_mi_and_learning_integrated"] is True
    assert proof["proof_obligations"]["proof_16_crosswalks_mechanically_allowed"] is True
    assert proof["verdict"] == "PROVEN_COMPLETE"
    assert (out / "p5_optimization_contract_crosswalk_v1.json").is_file()
    assert (out / "p5_meta_learning_contract_crosswalk_v1.json").is_file()
