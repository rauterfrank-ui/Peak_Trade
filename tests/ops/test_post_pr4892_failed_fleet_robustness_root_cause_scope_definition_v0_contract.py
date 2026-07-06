"""Contract tests for post-PR4892 failed fleet robustness root-cause scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4892_failed_fleet_robustness_root_cause_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_SCOPE_DEFINITION_V0.md"
)
OPERATOR_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_"
    "DEFINITION_ONLY_AFTER_PR4892_FAIL_V0"
)
EVIDENCE_CLASS_ID = "POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_SCOPE_DEFINITION_V0"
SCOPE_ID = "POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_SCOPE_DEFINITION_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = (
    "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_AFTER_"
    "POST_NO_PASS_STEP31F_OWNER_FIX_OFFLINE_ECONOMIC_EVALUATION_FAIL_V0"
)
SELECTED_CLASS = "E"
NEXT_EXECUTION_GO = (
    "GO_POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
)
BASELINE_HEAD = "72d5dfb7641776feb6969feae5f2eb2cfa08b9d8"
PARENT_EXECUTION_SUFFIX = (
    "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0_20260706T010502Z"
)
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
    "Scope-Definition ≠ Decomposition-Execution",
    "Keine Diagnostics-Execution",
    "ROBUSTNESS_FAILED",
    "NO_NEW_CANDIDATE_HOLD",
    "PANEL_ZERO_TRADE_REFUTED",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4892FailedFleetRobustnessRootCauseScopeDefinitionV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["selected_class"] == SELECTED_CLASS
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["go_token"] == OPERATOR_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert config["fleet_verdict"] == "ROBUSTNESS_FAILED"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["panel_zero_trade_refuted"] is True
        assert config["same_binding_retry_allowed"] is False
        assert config["threshold_lowering_allowed"] is False
        assert config["parameter_rescue_allowed"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["new_candidates_ratified"] is False

    def test_scope_config_blocked_actions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "NEW_STRATEGY_IMPLEMENTATION",
        ):
            assert action in blocked

    def test_scope_config_blocked_scope_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_scope_classes"])
        assert "A_UNMODIFIED_V3_BINDING_REEXECUTION" in blocked
        assert "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS" in blocked
        assert "G_RUNTIME_REWIRE" in blocked

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `ROBUSTNESS_FAILED`" in body
        assert "`PANEL_ZERO_TRADE_REFUTED` | `true`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_governance_doc_next_execution_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_EXECUTION_GO

    def test_parent_execution_evidence_ref_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_EXECUTION_SUFFIX in config["parent_execution_evidence_ref"]
        assert config["parent_execution_manifest_verify_rc"] == 0

    def test_confirmed_failure_classes_include_robustness_failed(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "ROBUSTNESS_FAILED" in config["confirmed_failure_classes"]
        assert "NEGATIVE_NET_EDGE" in config["confirmed_failure_classes"]

    def test_insufficient_axes_declared(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "turnover_cost_drag_decomposition" in config["insufficient_source_evidence_axes"]
        assert "long_short_contribution_imbalance" in config["insufficient_source_evidence_axes"]
