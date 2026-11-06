"""Contract tests for post-no-pass robustness failure diagnostics evidence class v0."""

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
    REPO_ROOT / "config/research/post_no_pass_robustness_failure_diagnostics_evidence_class_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0"
EVIDENCE_CLASS_ID = "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0"
SELECTED_CLASS = "E"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
CLASS_REGISTRY_STATUS = "DIAGNOSTICS_EXECUTION_COMPLETE_V0"
HISTORICAL_CLOSEOUT_NEXT_STEP = "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_REQUIRES_SEPARATE_OPERATOR_GO_V0"
HISTORICAL_CLOSEOUT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
CURRENT_STATE = "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_COMPLETE_V0"
NEXT_CANONICAL_STEP = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_REQUIRES_OPERATOR_RATIFICATION_V0"
CURRENT_ADMISSIBLE_SCOPE = "NEW_VERSIONED_RESEARCH_SCOPE_SELECTION_V0"
EXECUTION_GO = "GO_POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
OPERATOR_RATIFICATION_GO = "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
SOURCE_EVIDENCE_SUFFIX = (
    "bounded_post_no_pass_futures_offline_economic_evaluation_execution_v0_20260705T192520Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
SOURCE_PRS = (4873, 4875, 4876)
DIAGNOSTIC_AXES = (
    "trade_count_sufficiency_sparse_signal_failure",
    "fee_slippage_funding_drag_decomposition",
    "walk_forward_window_instability",
    "monte_carlo_sequence_fragility",
    "stress_cost_sensitivity",
    "regime_concentration_single_regime_dependence",
    "long_short_contribution_imbalance",
    "turnover_versus_gross_edge",
    "parameter_sensitivity_without_optimization",
    "dataset_period_coverage_adequacy",
    "execution_model_assumption_exposure",
    "portfolio_contribution_diagnostics_research_only",
)
REQUIRED_FUTURE_ARTIFACTS = (
    "diagnostic_manifest",
    "source_evidence_refs",
    "candidate_binding_refs",
    "immutable_failure_refs",
    "diagnostics_schema_version",
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
)
BOUNDARY_PHRASES = (
    "NO_EVALUATION_IN_THIS_SCOPE",
    "NO_SAME_BINDING_RETRY",
    "NO_PROMOTION",
    "NO_RUNTIME",
    "NO_PARAMETER_RESCUE",
    "Scope-Definition ≠ Diagnostics-Execution-Autorisierung",
    "TERMINAL_NEGATIVE_EVIDENCE_UNCHANGED",
)
AUTHORITY_TRUE_FLAGS = (
    "economic_evaluation_authorized",
    "promotion_eligible",
    "runtime_rewire_admissible",
    "runtime_authority",
    "same_binding_retry_allowed",
    "parameter_rescue_allowed",
    "threshold_lowering_allowed",
    "diagnostics_execution_authorized",
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
        "\n#### POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0"
    )
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassRobustnessFailureDiagnosticsEvidenceClassV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["status"] == SCOPE_STATUS
        assert payload["offline_only"] is True
        assert payload["non_authorizing"] is True
        assert payload["economic_evaluation_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False
        assert payload["parameter_rescue_allowed"] is False
        assert payload["threshold_lowering_allowed"] is False
        assert payload["failed_candidates"] == list(FAILED_CANDIDATES)
        assert payload["failed_candidate_verdict"] == "ROBUSTNESS_FAILED"
        assert payload["source_prs"] == list(SOURCE_PRS)
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["spot_allowed"] is False
        assert payload["synthetic_spot_allowed"] is False
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["terminal_negative_evidence_for_unchanged_binding"] is True
        assert payload["historical_negative_evidence_mutated"] is False
        assert payload["next_required_go_token_for_execution"] == EXECUTION_GO
        assert payload["operator_ratification_go_token"] == OPERATOR_RATIFICATION_GO
        assert SOURCE_EVIDENCE_SUFFIX in payload["source_evidence_ref"]
        for flag in AUTHORITY_TRUE_FLAGS:
            assert payload.get(flag) is not True, f"authority flag must not be true: {flag}"

    def test_scope_config_diagnostic_axes_and_forbidden_actions(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        axes = payload["diagnostic_axes"]
        forbidden = payload["forbidden_actions"]
        artifacts = payload["required_future_execution_artifacts"]
        for axis in DIAGNOSTIC_AXES:
            assert axis in axes, f"missing diagnostic axis: {axis}"
        for action in FORBIDDEN_ACTIONS_MINIMUM:
            assert action in forbidden, f"missing forbidden action: {action}"
        for artifact in REQUIRED_FUTURE_ARTIFACTS:
            assert artifact in artifacts, f"missing future artifact: {artifact}"
        assert "THRESHOLD_LOWERING" in forbidden
        assert "PARAMETER_RESCUE" in forbidden

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`SELECTED_CLASS` | `{SELECTED_CLASS}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`SAME_BINDING_RETRY_ALLOWED` | `false`" in body
        assert "`PARAMETER_RESCUE_ALLOWED` | `false`" in body
        assert "`THRESHOLD_LOWERING_ALLOWED` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert "PR #4873" in body
        assert "PR #4875" in body
        assert "PR #4876" in body
        assert SOURCE_EVIDENCE_SUFFIX in body
        for candidate in FAILED_CANDIDATES:
            assert f"`{candidate}` | `ROBUSTNESS_FAILED`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text, "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0_STATUS"
            )
            == CLASS_REGISTRY_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_ID",
            )
            == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0_SELECTED_CLASS",
            )
            == SELECTED_CLASS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0_DIAGNOSTICS_EXECUTED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0_ECONOMIC_EVALUATION_AUTHORIZED",
            )
            == "false"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_CLASS_V0_REQUIRED_NEXT_GO_FOR_EXECUTION",
            )
            == EXECUTION_GO
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == SCOPE_STATUS
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "SELECTED_CLASS") == SELECTED_CLASS
        assert _field_value(section, "DIAGNOSTICS_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "PARAMETER_RESCUE_ALLOWED") == "false"
        assert _field_value(section, "THRESHOLD_LOWERING_ALLOWED") == "false"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == EXECUTION_GO
        assert _field_value(section, "NEXT_CANONICAL_STEP") == HISTORICAL_CLOSEOUT_NEXT_STEP
        assert (
            _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE")
            == HISTORICAL_CLOSEOUT_ADMISSIBLE_SCOPE
        )
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == EXECUTION_GO
        assert _field_value(section, "FUTURES_ONLY") == "true"
        assert _field_value(section, "BITCOIN_DIRECTION_ALLOWED") == "false"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "TRADING_EFFECT") == "NONE"
        assert SOURCE_EVIDENCE_SUFFIX in _field_value(section, "SOURCE_EVIDENCE_REF")
