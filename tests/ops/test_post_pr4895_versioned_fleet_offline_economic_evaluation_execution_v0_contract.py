"""Contract tests for post-PR4895 versioned fleet offline economic evaluation execution v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BINDING_COMPLETION_DIGEST,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXPECTED_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    PARENT_BINDING_BUNDLE_SUFFIX,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    CandidateEconomicVerdict,
    FleetEconomicVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    verify_execution_scope_v0,
    verify_preconditions_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    RESEARCH_CANDIDATES,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4895_versioned_fleet_offline_economic_evaluation_execution_scope_v0.json"
)
BINDING_CONFIG = (
    REPO_ROOT / "config/research/post_pr4895_versioned_fleet_binding_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT
    / "scripts/ops/run_post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0.py"
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


@pytest.fixture(name="execution_scope_config")
def fixture_execution_scope_config() -> dict:
    return json.loads(EXECUTION_SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="binding_completion")
def fixture_binding_completion() -> dict:
    return json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))


class TestPostPr4895VersionedFleetOfflineEconomicEvaluationExecutionV0Contract:
    def test_go_token_and_scope_classification(self) -> None:
        assert (
            CONFIRM_GO == "GO_POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert (
            SCOPE_CLASSIFICATION
            == "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert PROCESS_CLASSIFICATION == (
            "POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )

    def test_no_runtime_authority_order_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
        assert ORDER_EFFECT == "NONE"

    def test_expected_origin_main_sha(self) -> None:
        assert EXPECTED_ORIGIN_MAIN_SHA == "523794bae4041fbd5d78fe400ff9e1e01022a510"

    def test_execution_scope_digests(self, execution_scope_config: dict) -> None:
        assert execution_scope_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
        assert execution_scope_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
        assert execution_scope_config["binding_completion_digest"] == BINDING_COMPLETION_DIGEST
        assert execution_scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert execution_scope_config["execution_go_token"] == CONFIRM_GO
        assert (
            execution_scope_config["parent_binding_bundle_suffix"] == PARENT_BINDING_BUNDLE_SUFFIX
        )
        assert execution_scope_config["strategy_version"] == "v4"
        assert execution_scope_config["fleet_candidates"] == list(RESEARCH_CANDIDATES)

    def test_execution_scope_verification(
        self, execution_scope_config: dict, binding_completion: dict
    ) -> None:
        ok, reasons = verify_execution_scope_v0(
            execution_scope_config,
            binding_completion=binding_completion,
        )
        assert ok, reasons

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
            )
            in body
        )
        assert f"`OPERATOR_GO` | `{CONFIRM_GO}`" in body
        assert f"`BINDING_COMPLETION_DIGEST` | `{BINDING_COMPLETION_DIGEST}`" in body

    def test_runner_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
        assert CONFIRM_GO in body

    def test_classify_fleet_verdict_pass(self) -> None:
        verdicts = [CandidateEconomicVerdict.ECONOMICALLY_VIABLE_OFFLINE] * 3
        assert (
            classify_fleet_verdict_v0(verdicts) is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_PASS
        )

    def test_classify_fleet_verdict_fail(self) -> None:
        verdicts = [
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
        ]
        assert (
            classify_fleet_verdict_v0(verdicts) is FleetEconomicVerdict.FLEET_ECONOMIC_VALIDITY_FAIL
        )

    def test_classify_fleet_verdict_blocked(self) -> None:
        verdicts = [
            CandidateEconomicVerdict.BLOCKED_BINDING_OR_EVIDENCE_GAP,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
            CandidateEconomicVerdict.ROBUSTNESS_FAILED,
        ]
        assert (
            classify_fleet_verdict_v0(verdicts)
            is FleetEconomicVerdict.FLEET_EXECUTION_BLOCKED_FAIL_CLOSED
        )

    def test_classify_candidate_robustness_failed(self) -> None:
        result = CandidateExecutionResultV0(
            strategy_id="trend_following",
            strategy_version="v4",
            canonical_candidate_identifier="trend_following/v4",
            config_path="cfg.json",
            output_dir="/tmp/out",
            run_id="run-1",
            terminal_status=CandidateTerminalStatus.FAIL,
            economic_validity_result="FAIL",
            economic_validity_offline_gate_pass=False,
            evidence_status="ROBUSTNESS_FAILED",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=True,
        )
        verdict = classify_candidate_verdict_v0(
            result, evidence_payload={"status": "ROBUSTNESS_FAILED"}
        )
        assert verdict is CandidateEconomicVerdict.ROBUSTNESS_FAILED

    def test_verify_preconditions_go_token(self) -> None:
        ok, reasons = verify_preconditions_v0(
            repo_root=REPO_ROOT,
            confirm=CONFIRM_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            require_clean_worktree=False,
        )
        assert ok, reasons

    def test_binding_config_ready_for_execution(self, binding_completion: dict) -> None:
        assert binding_completion["status"] == "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED"
        assert binding_completion["economic_evaluation_executed"] is False
        assert binding_completion["completion_digest"] == BINDING_COMPLETION_DIGEST
        assert len(binding_completion["candidates"]) == len(RESEARCH_CANDIDATES)
