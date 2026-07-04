"""Contract tests for final_research_fleet_offline_economic_evaluation_execution_v0."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backtest.economic_validity_policy_v1 import EconomicValidityEvaluationStatus
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    ACCEPTED_GO_TOKENS,
    AUTHORITY_EFFECT,
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    EXPECTED_ORIGIN_MAIN_SHA,
    FleetTerminalStatus,
    GO_TOKEN,
    GO_TOKEN_OPERATOR_ALIAS,
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
    ORDER_EFFECT,
    PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS,
    REASON_NEW_EVIDENCE_CLASS_REQUIRED,
    REASON_UNMODIFIED_BINDING_RETRY_BLOCKED,
    RUNTIME_EFFECT,
    is_accepted_go_token,
    map_candidate_terminal_status_v0,
    materialize_fleet_evaluation_summary_v0,
    resolve_fleet_terminal_status_v0,
    verify_execution_start_state_v0,
    verify_unmodified_retry_admissibility_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
BINDING_COMPLETION_PATH = (
    ARCHIVE_ROOT
    / "planning"
    / "bounded_final_research_fleet_offline_economic_evaluation_scope_ratification_v0_20260703T050130Z"
    / "final_research_fleet_versioned_binding_completion_v0.json"
)


@pytest.fixture(name="ratified_binding_completion")
def fixture_ratified_binding_completion() -> dict:
    if not BINDING_COMPLETION_PATH.is_file():
        pytest.skip(f"missing archived binding completion: {BINDING_COMPLETION_PATH}")
    import json

    return json.loads(BINDING_COMPLETION_PATH.read_text(encoding="utf-8"))


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(ratified_binding_completion: dict) -> dict:
    return materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=ratified_binding_completion,
    )


def test_go_token_constant() -> None:
    assert GO_TOKEN == "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"


def test_go_token_operator_alias_is_accepted_without_second_authority() -> None:
    assert GO_TOKEN_OPERATOR_ALIAS in ACCEPTED_GO_TOKENS
    assert is_accepted_go_token(GO_TOKEN_OPERATOR_ALIAS)
    assert is_accepted_go_token(GO_TOKEN)
    assert not is_accepted_go_token("GO_UNKNOWN_TOKEN")


def test_expected_origin_main_sha_rebound_to_pr4826_merge() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "208ab96562f7750fb4dff43936b345a040d1cea4"


def test_pr4826_scope_does_not_create_new_execution_evidence_class() -> None:
    assert PR4826_CREATES_NEW_EXECUTION_EVIDENCE_CLASS is False


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_map_candidate_terminal_status_pass_only_when_fully_viable() -> None:
    assert (
        map_candidate_terminal_status_v0(
            runner_execution_success=True,
            economic_validity_result=EconomicValidityEvaluationStatus.PASS.value,
            economic_validity_offline_gate_pass=True,
            evidence_status="ECONOMICALLY_VIABLE_OFFLINE",
        )
        is CandidateTerminalStatus.PASS
    )


def test_map_candidate_terminal_status_fail_on_policy_fail() -> None:
    assert (
        map_candidate_terminal_status_v0(
            runner_execution_success=True,
            economic_validity_result=EconomicValidityEvaluationStatus.FAIL.value,
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
        )
        is CandidateTerminalStatus.FAIL
    )


def test_map_candidate_terminal_status_inconclusive_on_runner_failure() -> None:
    assert (
        map_candidate_terminal_status_v0(
            runner_execution_success=False,
            economic_validity_result="BLOCKED",
            economic_validity_offline_gate_pass=False,
            evidence_status="",
        )
        is CandidateTerminalStatus.INCONCLUSIVE
    )


def test_fleet_status_fail_closed_no_partial_pass() -> None:
    results = [
        CandidateExecutionResultV0(
            strategy_id="trend_following",
            strategy_version="v1",
            canonical_candidate_identifier="trend_following/v1",
            config_path="cfg.json",
            output_dir="/tmp/a",
            run_id="r1",
            terminal_status=CandidateTerminalStatus.PASS,
            economic_validity_result="PASS",
            economic_validity_offline_gate_pass=True,
            evidence_status="ECONOMICALLY_VIABLE_OFFLINE",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
        CandidateExecutionResultV0(
            strategy_id="bollinger_bands",
            strategy_version="v1",
            canonical_candidate_identifier="bollinger_bands/v1",
            config_path="cfg.json",
            output_dir="/tmp/b",
            run_id="r2",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
        CandidateExecutionResultV0(
            strategy_id="momentum_1h",
            strategy_version="v1",
            canonical_candidate_identifier="momentum_1h/v1",
            config_path="cfg.json",
            output_dir="/tmp/c",
            run_id="r3",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="RESEARCH_ONLY",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
    ]
    assert resolve_fleet_terminal_status_v0(results) is FleetTerminalStatus.FAIL


def test_fleet_summary_preserves_individual_failures(
    scope_ratification: dict,
) -> None:
    results = [
        CandidateExecutionResultV0(
            strategy_id="trend_following",
            strategy_version="v1",
            canonical_candidate_identifier="trend_following/v1",
            config_path="cfg.json",
            output_dir="/tmp/a",
            run_id="r1",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
        CandidateExecutionResultV0(
            strategy_id="bollinger_bands",
            strategy_version="v1",
            canonical_candidate_identifier="bollinger_bands/v1",
            config_path="cfg.json",
            output_dir="/tmp/b",
            run_id="r2",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="RESEARCH_ONLY",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
        CandidateExecutionResultV0(
            strategy_id="momentum_1h",
            strategy_version="v1",
            canonical_candidate_identifier="momentum_1h/v1",
            config_path="cfg.json",
            output_dir="/tmp/c",
            run_id="r3",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        ),
    ]
    summary = materialize_fleet_evaluation_summary_v0(
        ratification=scope_ratification,
        candidate_results=results,
        execution_bundle_dir="/tmp/fleet",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert summary["individual_failure_preservation"] is True
    assert summary["fail_count"] == 3
    assert summary["pass_count"] == 0
    assert summary["economic_validity_offline_gate_pass"] is False
    assert summary["fleet_status"] == "FAIL"
    assert summary["runtime_rewire_admissible"] is False


def test_start_state_verification_blocks_unmodified_step31f_retry() -> None:
    import json

    repo_binding_path = (
        REPO_ROOT
        / "config"
        / "research"
        / "final_research_fleet_versioned_binding_completion_v0.json"
    )
    fleet_binding_completion = json.loads(repo_binding_path.read_text(encoding="utf-8"))
    scope_ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=fleet_binding_completion,
        )
    )
    assert (
        fleet_binding_completion.get("completion_digest")
        == HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
    )
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        fleet_binding_completion=fleet_binding_completion,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
    )
    assert result.valid is False
    assert REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in result.fail_reasons
    assert REASON_NEW_EVIDENCE_CLASS_REQUIRED in result.fail_reasons


def test_unmodified_retry_admissibility_fail_closed_for_historical_digest() -> None:
    ok, reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion={
            "completion_digest": HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
        },
    )
    assert ok is False
    assert REASON_UNMODIFIED_BINDING_RETRY_BLOCKED in reasons


def test_unmodified_retry_admissibility_passes_for_different_binding_digest() -> None:
    ok, reasons = verify_unmodified_retry_admissibility_v0(
        fleet_binding_completion={"completion_digest": "different_digest_value"},
    )
    assert ok is True
    assert reasons == ()


def test_fleet_candidate_set_exactness(scope_ratification: dict) -> None:
    refs = scope_ratification["candidate_refs"]
    assert sorted(refs) == sorted(["bollinger_bands/v1", "momentum_1h/v1", "trend_following/v1"])
    assert len(refs) == len(set(refs))
