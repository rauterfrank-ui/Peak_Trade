"""Contract tests for post-v4 versioned fleet offline economic evaluation execution scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    STEP31F_CONFIG_PATHS,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    RESEARCH_CANDIDATES,
)
from src.research.post_v4_versioned_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXPECTED_ORIGIN_MAIN_SHA,
    MATERIALIZATION_DIGEST,
    MATERIALIZATION_REL,
    ORDER_EFFECT,
    PARENT_CLOSEOUT_SUFFIX,
    PROCESS_CLASSIFICATION,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    STRATEGY_VERSION,
    CandidateEconomicVerdict,
    FleetEconomicVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    compute_execution_scope_digests_v0,
    verify_execution_scope_v0,
    verify_preconditions_v0,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_v4_versioned_fleet_offline_economic_evaluation_execution_scope_v0.json"
)
MATERIALIZATION_CONFIG = REPO_ROOT / MATERIALIZATION_REL
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0.md"
)
RUNNER_SCRIPT = (
    REPO_ROOT
    / "scripts/research/post_v4_versioned_fleet_offline_economic_evaluation_execution_v0.py"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
)
SCOPE_STATUS = "FLEET_ECONOMIC_VALIDITY_FAIL"
CURRENT_STATE = "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_FAIL_V0"
NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_POST_V4_FLEET_FAILURE_DECOMPOSITION_OR_NEXT_RESEARCH_SCOPE_V0"
)
EVIDENCE_SUFFIX = (
    "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
)
CURRENT_ADMISSIBLE_SCOPE = "NONE"


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n---\n\n## PR #4629 Evidence-Drift")
    return tail if next_heading == -1 else tail[:next_heading]


@pytest.fixture(name="execution_scope_config")
def fixture_execution_scope_config() -> dict:
    return json.loads(EXECUTION_SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="materialization_config")
def fixture_materialization_config() -> dict:
    return json.loads(MATERIALIZATION_CONFIG.read_text(encoding="utf-8"))


class TestPostV4VersionedFleetOfflineEconomicEvaluationExecutionScopeV0Contract:
    def test_go_token_and_scope_classification(self) -> None:
        assert (
            CONFIRM_GO
            == "GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
        )
        assert (
            SCOPE_CLASSIFICATION
            == "BOUNDED_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        )
        assert PROCESS_CLASSIFICATION == (
            "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
        )

    def test_no_runtime_authority_order_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
        assert ORDER_EFFECT == "NONE"

    def test_expected_origin_main_sha(self) -> None:
        assert EXPECTED_ORIGIN_MAIN_SHA == "acf7dec82b070bf42d953f0b542e882fa5920603"

    def test_execution_scope_digests(self, execution_scope_config: dict) -> None:
        assert execution_scope_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
        assert execution_scope_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
        assert execution_scope_config["materialization_digest"] == MATERIALIZATION_DIGEST
        assert execution_scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert execution_scope_config["execution_go_token"] == CONFIRM_GO
        assert execution_scope_config["parent_closeout_suffix"] == PARENT_CLOSEOUT_SUFFIX
        assert execution_scope_config["strategy_version"] == STRATEGY_VERSION
        assert execution_scope_config["fleet_candidates"] == list(RESEARCH_CANDIDATES)
        assert execution_scope_config["execution_performed"] is True
        assert execution_scope_config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert execution_scope_config["economic_validity_offline_gate_pass"] is False
        assert (
            "post_v4_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T040339Z"
            in (execution_scope_config["durable_evidence_ref"])
        )

    def test_execution_scope_semantic_digest_recomputes(self, execution_scope_config: dict) -> None:
        _scope_digest, semantic_digest = compute_execution_scope_digests_v0(execution_scope_config)
        assert semantic_digest == EXECUTION_SEMANTIC_DIGEST

    def test_execution_scope_verification(
        self, execution_scope_config: dict, materialization_config: dict
    ) -> None:
        ok, reasons = verify_execution_scope_v0(
            execution_scope_config,
            materialization=materialization_config,
        )
        assert ok, reasons

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
            )
            in body
        )
        assert f"`OPERATOR_GO` | `{CONFIRM_GO}`" in body
        assert f"`MATERIALIZATION_DIGEST` | `{MATERIALIZATION_DIGEST}`" in body
        assert _field_value(body, "VERDICT") == SCOPE_STATUS
        assert _field_value(body, "EXECUTION_PERFORMED") == "true"

    def test_runner_script_exists(self) -> None:
        assert RUNNER_SCRIPT.is_file()
        body = RUNNER_SCRIPT.read_text(encoding="utf-8")
        assert CONFIRM_GO in body
        assert "run_bounded_scope_v0" in body

    def test_step31f_configs_not_sparse_signal(self) -> None:
        for strategy_id in RESEARCH_CANDIDATES:
            rel = STEP31F_CONFIG_PATHS[strategy_id]
            assert "sparse" not in rel.lower()
            assert "SPARSE_SIGNAL" not in (REPO_ROOT / rel).read_text(encoding="utf-8")

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
            strategy_version=STRATEGY_VERSION,
            canonical_candidate_identifier=f"trend_following/{STRATEGY_VERSION}",
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

    def test_materialization_config_ready_for_execution(self, materialization_config: dict) -> None:
        assert materialization_config["verdict"] == "BINDINGS_MATERIALIZED_NOT_EVALUATED"
        assert materialization_config["economic_evaluation_authorized"] is False
        assert (
            "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
            in materialization_config["blocked_research_scopes"]
        )
        by_id = {c["strategy_id"]: c for c in materialization_config["fleet_bindings"]}
        for sid in RESEARCH_CANDIDATES:
            assert by_id[sid]["strategy_version"] == STRATEGY_VERSION
            assert by_id[sid]["evaluation_status"] == "NOT_EVALUATED"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert _field_value(text, "CURRENT_STATE") == CURRENT_STATE
        assert _field_value(text, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(text, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(text, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == "NONE"
        assert _field_value(text, "LAST_VERIFIED_ORIGIN_MAIN") == EXPECTED_ORIGIN_MAIN_SHA
        assert (
            _field_value(
                text,
                "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0_GO_TOKEN",
            )
            == CONFIRM_GO
        )
        assert PARENT_CLOSEOUT_SUFFIX in _field_value(
            text,
            "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0_PARENT_CLOSEOUT_REF",
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_STATUS
        assert _field_value(section, "GO_TOKEN") == CONFIRM_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "BASELINE_HEAD") == EXPECTED_ORIGIN_MAIN_SHA
        assert _field_value(section, "EXECUTION_PERFORMED") == "true"
        assert _field_value(section, "FLEET_VERDICT") == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert EVIDENCE_SUFFIX in _field_value(section, "DURABLE_EVIDENCE_REF")
        assert _field_value(section, "STRATEGY_VERSION") == STRATEGY_VERSION
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == "NONE"
        assert _field_value(section, "offline_only") == "true"
        assert _field_value(section, "non_authorizing") == "true"
