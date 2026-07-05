"""Contract tests for post-no-pass sparse signal inconclusive failure classification v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_inconclusive_failure_classification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
SELECTED_CLASS = "E"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_SCOPE_DEFINITION_ONLY_V0"
)
SCOPE_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_SCOPE_DEFINITION_ONLY_V0"
)
SCOPE_DEFINITION_GO = (
    "GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_SCOPE_DEFINITION_ONLY_V0"
)
EXECUTION_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
NEXT_CANONICAL_STEP = "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_EXECUTION_REQUIRES_SEPARATE_OPERATOR_GO_V0"
CURRENT_ADMISSIBLE_SCOPE = "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
CURRENT_STATE = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_V0"
)
BASELINE_HEAD = "6b48857ab9fc9e3d2637286038d2ae6ce6f3c9a3"
PARENT_EVIDENCE_SUFFIX = "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0_20260705T213529Z"
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
CLASSIFICATION_AXES = (
    "sparse_signal_vs_zero_trade_separation",
    "signal_trade_coverage_per_candidate",
    "economic_viability_metric_materialization_failure",
    "panel_adapter_runner_defect_classification",
    "schema_gate_threshold_failure_classification",
    "insufficient_trades_classification",
    "metric_materialization_path_failure",
    "walk_forward_gate_precondition_failure",
    "stress_monte_carlo_precondition_failure",
    "execution_model_assumption_exposure",
    "dataset_period_coverage_adequacy",
    "portfolio_contribution_diagnostics_research_only",
)
REQUIRED_FUTURE_ARTIFACTS = (
    "classification_manifest",
    "source_evidence_refs",
    "candidate_binding_refs",
    "immutable_failure_refs",
    "classification_schema_version",
    "failure_axis_results",
    "admissibility_summary",
    "no_promotion_claim",
)
FORBIDDEN_ACTIONS_MINIMUM = (
    "SAME_BINDING_RETRY",
    "PARAMETER_RESCUE",
    "THRESHOLD_LOWERING",
    "PROMOTION",
    "RUNTIME",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "SCHEDULER",
    "ORDERS",
    "CREDENTIALS",
    "ARMING",
    "LIVE",
    "CLASSIFICATION_EXECUTION_IN_THIS_SCOPE",
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_SCOPE",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_PARAMETER_RESCUE",
    "Scope-Definition ≠ Classification-Execution-Autorisierung",
    "TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED",
    "NOT_CONSUMED",
    "REQUIRES_SEPARATE_OPERATOR_GO",
)
AUTHORITY_TRUE_FLAGS = (
    "economic_evaluation_authorized",
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "same_binding_retry_allowed",
    "parameter_rescue_allowed",
    "threshold_lowering_allowed",
    "classification_execution_authorized",
    "shadow_authorized",
    "paper_authorized",
    "testnet_authorized",
    "canary_authorized",
    "live_authorized",
    "orders_allowed",
    "scheduler_runtime_allowed",
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
        "\n#### POST_NO_PASS_ROBUSTNESS_FAILURE_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassSparseSignalInconclusiveFailureClassificationV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["status"] == SCOPE_STATUS
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["scope_classification"] == SCOPE_CLASSIFICATION
        assert payload["offline_only"] is True
        assert payload["non_authorizing"] is True
        assert payload["economic_evaluation_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_rescue_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["failed_candidates"] == list(FAILED_CANDIDATES)
        assert payload["failed_candidate_verdict"] == "EXECUTION_FAILED_FAIL_CLOSED"
        assert payload["fleet_status"] == "INCONCLUSIVE"
        assert payload["fleet_verdict"] == "EXECUTION_FAILED_FAIL_CLOSED"
        assert payload["inconclusive_count"] == 3
        assert payload["pass_count"] == 0
        assert payload["fail_count"] == 0
        assert payload["panel_zero_trade_refuted"] is True
        assert payload["source_prs"] == [4881]
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["spot_allowed"] is False
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["next_required_go_token_for_execution"] == EXECUTION_GO
        assert payload["next_required_go_token_for_execution_consumption"] == "NOT_CONSUMED"
        assert (
            payload["next_required_go_token_for_execution_status"]
            == "REQUIRES_SEPARATE_OPERATOR_GO"
        )
        assert payload["scope_definition_go_token"] == SCOPE_DEFINITION_GO
        assert payload["scope_definition_go_token_consumed"] is True
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["baseline_pr"] == "4881"
        assert PARENT_EVIDENCE_SUFFIX in payload["source_evidence_ref"]
        assert payload["parent_execution_manifest_verify_rc"] == 0
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_scope_config_classification_axes_and_forbidden_actions(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        axes = payload["classification_axes"]
        forbidden = payload["forbidden_actions"]
        artifacts = payload["required_future_execution_artifacts"]
        for axis in CLASSIFICATION_AXES:
            assert axis in axes, f"missing classification axis: {axis}"
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"
        for artifact in REQUIRED_FUTURE_ARTIFACTS:
            assert artifact in artifacts, f"missing future artifact: {artifact}"
        assert "THRESHOLD_LOWERING" in forbidden
        assert "PARAMETER_RESCUE" in forbidden
        assert "INCONCLUSIVE_REINTERPRETATION_AS_PASS" in forbidden

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`SELECTED_CLASS` | `{SELECTED_CLASS}`" in body
        assert f"`SCOPE_DEFINITION_GO_TOKEN` | `{SCOPE_DEFINITION_GO}`" in body
        assert "`SCOPE_DEFINITION_GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{EXECUTION_GO}`" in body
        assert "`REQUIRED_NEXT_GO_FOR_EXECUTION_CONSUMPTION` | `NOT_CONSUMED`" in body
        assert "`REQUIRED_NEXT_GO_FOR_EXECUTION_STATUS` | `REQUIRES_SEPARATE_OPERATOR_GO`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`SHADOW_AUTHORIZED` | `false`" in body
        assert "`PAPER_AUTHORIZED` | `false`" in body
        assert "`TESTNET_AUTHORIZED` | `false`" in body
        assert "`ORDERS_ALLOWED` | `false`" in body
        assert "`SCHEDULER_RUNTIME_ALLOWED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "PR #4881" in body
        assert PARENT_EVIDENCE_SUFFIX in body
        for candidate in FAILED_CANDIDATES:
            assert f"`{candidate}" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        )
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == EXECUTION_GO
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_STATUS",
            )
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_CONFIG_REF",
            )
            == "config/research/post_no_pass_sparse_signal_inconclusive_failure_classification_v0.json"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_GOVERNANCE_REF",
            )
            == "docs/governance/POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0.md"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_EVIDENCE_CLASS_ID",
            )
            == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_SCOPE_DEFINITION_GO_TOKEN",
            )
            == SCOPE_DEFINITION_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_SCOPE_DEFINITION_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION",
            )
            == EXECUTION_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION_CONSUMPTION",
            )
            == "NOT_CONSUMED"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_SPARSE_SIGNAL_INCONCLUSIVE_FAILURE_CLASSIFICATION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION_STATUS",
            )
            == "REQUIRES_SEPARATE_OPERATOR_GO"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "SELECTED_CLASS") == SELECTED_CLASS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "SCOPE_CLASSIFICATION") == SCOPE_CLASSIFICATION
        assert _field_value(section, "SCOPE_DEFINITION_GO_TOKEN") == SCOPE_DEFINITION_GO
        assert _field_value(section, "SCOPE_DEFINITION_GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "CLASSIFICATION_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "SHADOW_AUTHORIZED") == "false"
        assert _field_value(section, "PAPER_AUTHORIZED") == "false"
        assert _field_value(section, "TESTNET_AUTHORIZED") == "false"
        assert _field_value(section, "ORDERS_ALLOWED") == "false"
        assert _field_value(section, "SCHEDULER_RUNTIME_ALLOWED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "THRESHOLD_LOWERING_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == EXECUTION_GO
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION_CONSUMPTION") == "NOT_CONSUMED"
        assert (
            _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION_STATUS")
            == "REQUIRES_SEPARATE_OPERATOR_GO"
        )
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == EXECUTION_GO
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert PARENT_EVIDENCE_SUFFIX in _field_value(section, "PARENT_EXECUTION_EVIDENCE_REF")
