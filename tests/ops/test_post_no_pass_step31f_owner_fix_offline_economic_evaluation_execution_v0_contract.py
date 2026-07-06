"""Contract tests for post-no-pass STEP31F owner-fix offline economic evaluation execution v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXPECTED_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    OWNER_FIX_MODULE_REF,
    PATH_ACTIVATION_BINDING_COMPLETION_DIGEST,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    EconomicExecutionVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    verify_execution_scope_v0,
    verify_execution_start_state_v0,
    verify_preconditions_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_scope_v0.json"
)
SCOPE_DEFINITION_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_step31f_owner_fix_offline_economic_evaluation_scope_definition_v0.json"
)
PATH_ACTIVATION_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_metric_materialization_path_activation_binding_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_STEP31F_OWNER_FIX_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT
    / "scripts/ops/run_post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0.py"
)
DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


@pytest.fixture(name="execution_scope_config")
def fixture_execution_scope_config() -> dict:
    return json.loads(EXECUTION_SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="path_activation_binding")
def fixture_path_activation_binding() -> dict:
    return json.loads(PATH_ACTIVATION_CONFIG.read_text(encoding="utf-8"))


class TestPostNoPassStep31fOwnerFixOfflineEconomicEvaluationExecutionV0Contract:
    def test_go_token_and_scope_classification(self) -> None:
        assert CONFIRM_GO == (
            "GO_OPERATOR_AUTHORIZE_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_"
            "ECONOMIC_EVALUATION_EXECUTION_V0_WITH_STEP31F_OWNER_FIX"
        )
        assert SCOPE_CLASSIFICATION == PROCESS_CLASSIFICATION
        assert (
            SCOPE_CLASSIFICATION
            == "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_"
            "WITH_STEP31F_OWNER_FIX"
        )

    def test_no_runtime_authority_order_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
        assert ORDER_EFFECT == "NONE"

    def test_expected_origin_main_sha(self) -> None:
        assert EXPECTED_ORIGIN_MAIN_SHA == "b86a9813795e35cea1e2ca0a985d19c8f7c8ec11"

    def test_execution_scope_digests(self, execution_scope_config: dict) -> None:
        assert execution_scope_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
        assert execution_scope_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
        assert (
            execution_scope_config["binding_completion_digest"]
            == PATH_ACTIVATION_BINDING_COMPLETION_DIGEST
        )
        assert execution_scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert execution_scope_config["execution_go_token"] == CONFIRM_GO
        assert execution_scope_config["step31f_owner_fix_applied"] is True
        assert execution_scope_config["owner_fix_module_ref"] == OWNER_FIX_MODULE_REF

    def test_verify_execution_scope_accepted(
        self, execution_scope_config: dict, path_activation_binding: dict
    ) -> None:
        ok, reasons = verify_execution_scope_v0(
            execution_scope_config,
            path_activation_binding=path_activation_binding,
        )
        assert ok is True
        assert not reasons

    def test_verify_preconditions_rejects_invalid_go_token(self) -> None:
        ok, reasons = verify_preconditions_v0(
            repo_root=REPO_ROOT,
            confirm="INVALID",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            require_clean_worktree=False,
        )
        assert ok is False
        assert any("GO_TOKEN_INVALID" in reason for reason in reasons)

    def test_verify_execution_start_state_rejects_after_execution(self) -> None:
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            durable_evidence_root=DURABLE_ARCHIVE_ROOT,
            require_clean_worktree=False,
        )
        assert result.valid is False
        assert any(
            "ECONOMIC_EVALUATION_ALREADY_EXECUTED" in reason for reason in result.fail_reasons
        )

    def test_classify_fleet_verdict_metrics_not_materialized(self) -> None:
        verdict = classify_fleet_verdict_v0(
            [
                EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED,
                EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED,
                EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED,
            ]
        )
        assert verdict is EconomicExecutionVerdict.METRICS_NOT_MATERIALIZED

    def test_classify_candidate_verdict_runner_failed(self) -> None:
        result = CandidateExecutionResultV0(
            strategy_id="trend_following",
            strategy_version="v3",
            canonical_candidate_identifier="trend_following/v3",
            config_path="config/ops/example.json",
            output_dir="/tmp/out",
            run_id="run-1",
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=0,
            reason_codes=("CANDIDATE_RUN_FAILED",),
            stage_return_codes={},
            runner_execution_success=False,
        )
        verdict = classify_candidate_verdict_v0(result, evidence_payload={})
        assert verdict is EconomicExecutionVerdict.EXECUTION_FAILED_FAIL_CLOSED

    def test_runner_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()

    def test_scope_definition_requires_matching_go_token(self) -> None:
        scope_definition = json.loads(SCOPE_DEFINITION_CONFIG.read_text(encoding="utf-8"))
        assert scope_definition["status"] == "EXECUTION_COMPLETE_FAIL"
        assert scope_definition["required_next_go_for_execution"] == CONFIRM_GO
        assert scope_definition["economic_evaluation_executed"] is True

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_STEP31F_OWNER_FIX_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{CONFIRM_GO}`" in body
        assert "LIVE_AUTHORIZED: false" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert "`FLEET_VERDICT` | `ROBUSTNESS_FAILED`" in body
