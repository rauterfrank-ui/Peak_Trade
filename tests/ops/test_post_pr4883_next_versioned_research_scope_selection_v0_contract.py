"""Contract tests for post-PR4883 next versioned research scope selection v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SELECTION_CONFIG = (
    REPO_ROOT / "config/research/post_pr4883_next_versioned_research_scope_selection_v0.json"
)
RATIFIED_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_class_v0.json"
)
SELECTION_GOVERNANCE = (
    REPO_ROOT / "docs/governance/POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0.md"
)
RATIFIED_GOVERNANCE = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
OPERATOR_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
EVIDENCE_CLASS_ID = (
    "POST_PR4883_SPARSE_SIGNAL_INCONCLUSIVE_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
)
SCOPE_ID = "POST_PR4883_SPARSE_SIGNAL_INCONCLUSIVE_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
RATIFIED_SCOPE_ID = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
SCOPE_STATUS = "SCOPE_SELECTION_COMPLETE_NOT_EXECUTED"
RATIFIED_SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_SCOPE_DEFINITION_ONLY_V0"
SELECTED_CLASS = "E"
NEXT_EXECUTION_GO = (
    "GO_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
CURRENT_STATE = "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
CURRENT_ADMISSIBLE_SCOPE = RATIFIED_SCOPE_ID
BASELINE_HEAD = "b0d584db9057369f5d6a930c97f8ea8ed3734aac"
CLASSIFICATION_EVIDENCE_SUFFIX = (
    "post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0_20260705T222507Z"
)
RESEARCH_HYPOTHESIS = "INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_REQUIRES_READ_ONLY_DIAGNOSTICS_NOT_UNCHANGED_V2_BINDING_RETRY"
FORBIDDEN_RUNTIME_ACTIONS = (
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
)
BOUNDARY_PHRASES = (
    "Scope-Selection ≠ Diagnostics-Execution",
    "Keine Diagnostics-Execution in diesem Scope",
    "panel_zero_trade_refuted=true",
    "METRIC_MATERIALIZATION",
    "NO_NEW_CANDIDATE_HOLD",
)
DIAGNOSTIC_AXES = (
    "economic_viability_runner_failure_decomposition",
    "panel_adapter_stage_return_code_classification",
    "evidence_artifact_completeness_audit",
    "metric_schema_gate_failure_classification",
    "runner_log_excerpt_materialization_read_only",
    "candidate_binding_digest_consistency_check",
    "sparse_signal_density_vs_metric_gate_mismatch",
    "walk_forward_precondition_blocker_trace",
    "stress_monte_carlo_precondition_blocker_trace",
    "execution_model_assumption_exposure",
    "dataset_period_coverage_adequacy",
    "portfolio_contribution_diagnostics_research_only",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find(
        "\n#### POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostPr4883NextVersionedResearchScopeSelectionV0Contract:
    def test_selection_config_exists_and_governance_gates(self) -> None:
        assert SELECTION_CONFIG.is_file()
        payload = json.loads(SELECTION_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["scope_id"] == SCOPE_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["ratified_scope_id"] == RATIFIED_SCOPE_ID
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_rescue_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["required_future_operator_go"] is True
        assert payload["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["baseline_pr"] == "4883"
        assert payload["operator_go"] == OPERATOR_GO
        assert payload["go_token_consumed"] is True
        assert payload["classification_mapped_ratio"] == 1.0
        assert payload["classification_manifest_verify_rc"] == 0
        assert payload["panel_zero_trade_refuted"] is True
        assert CLASSIFICATION_EVIDENCE_SUFFIX in payload["classification_evidence_ref"]

    def test_selection_config_forbids_runtime_and_evaluation_execution(self) -> None:
        payload = json.loads(SELECTION_CONFIG.read_text(encoding="utf-8"))
        forbidden = payload["blocked_actions"]
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "SAME_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "EVALUATION_EXECUTION_IN_THIS_SCOPE",
            "DIAGNOSTICS_EXECUTION_IN_THIS_SCOPE",
        ):
            assert action in forbidden, f"missing forbidden action: {action}"
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in forbidden, f"missing forbidden runtime action: {action}"

    def test_ratified_scope_config_and_diagnostic_axes(self) -> None:
        assert RATIFIED_CONFIG.is_file()
        payload = json.loads(RATIFIED_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == RATIFIED_SCOPE_STATUS
        assert payload["scope_id"] == RATIFIED_SCOPE_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["research_hypothesis"] == RESEARCH_HYPOTHESIS
        assert payload["diagnostics_execution_authorized"] is False
        assert payload["diagnostics_executed"] is False
        assert payload["required_future_operator_go"] is True
        assert payload["next_required_go_token_for_execution"] == NEXT_EXECUTION_GO
        axes = payload["diagnostic_axes"]
        for axis in DIAGNOSTIC_AXES:
            assert axis in axes, f"missing diagnostic axis: {axis}"

    def test_governance_docs_have_docs_tokens_and_boundary_phrases(self) -> None:
        assert SELECTION_GOVERNANCE.is_file()
        selection_body = SELECTION_GOVERNANCE.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0")
            in selection_body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in selection_body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in selection_body
        assert f"`RATIFIED_SCOPE_ID` | `{RATIFIED_SCOPE_ID}`" in selection_body
        assert f"`SELECTED_CLASS` | `{SELECTED_CLASS}`" in selection_body
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in selection_body
        assert "`GO_TOKEN_CONSUMED` | `true`" in selection_body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{NEXT_EXECUTION_GO}`" in selection_body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in selection_body, f"missing boundary phrase: {phrase}"

        assert RATIFIED_GOVERNANCE.is_file()
        ratified_body = RATIFIED_GOVERNANCE.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
            )
            in ratified_body
        )
        assert f"`SCOPE_ID` | `{RATIFIED_SCOPE_ID}`" in ratified_body
        assert "Explicit Non-Authority Statement" in ratified_body
        assert "Fail-Closed Semantics" in ratified_body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        )
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
        )
        assert (
            _field_value(text, "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_STATUS")
            == SCOPE_STATUS
        )
        assert _field_value(
            text,
            "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_CONFIG_REF",
        ) == ("config/research/post_pr4883_next_versioned_research_scope_selection_v0.json")
        assert (
            _field_value(text, "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_GO_TOKEN")
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text,
                "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_RATIFIED_SCOPE_ID",
            )
            == RATIFIED_SCOPE_ID
        )
        assert (
            _field_value(
                text,
                "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION",
            )
            == NEXT_EXECUTION_GO
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "VERDICT") == SCOPE_STATUS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "SELECTED_CLASS") == SELECTED_CLASS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "RATIFIED_SCOPE_ID") == RATIFIED_SCOPE_ID
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "DIAGNOSTICS_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "THRESHOLD_LOWERING_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_EXECUTION_GO
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
