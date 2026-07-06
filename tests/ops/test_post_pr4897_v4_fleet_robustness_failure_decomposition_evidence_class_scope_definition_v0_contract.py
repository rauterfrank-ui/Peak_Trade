"""Contract tests for post-PR4897 v4 fleet failure decomposition scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_class_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_DEFINITION_V0.md"
)
OPERATOR_GO = (
    "GO_NEXT_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_AFTER_PR4897_V0"
)
EVIDENCE_CLASS_ID = (
    "POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_DEFINITION_V0"
)
SCOPE_ID = EVIDENCE_CLASS_ID
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = (
    "POST_PR4897_NEXT_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
)
SCOPE_CLASSIFICATION = "GOVERNANCE_ONLY_SCOPE_DEFINITION_AFTER_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
SELECTED_CLASS = "E"
SELECTED_NEXT_SCOPE_CLASS = "NEW_EVIDENCE_CLASS_REQUIRED"
NEXT_EXECUTION_GO = "GO_POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
BASELINE_HEAD = "175bb91bb46163f787e73c5f0024c3723536f9e2"
PARENT_EVALUATION_SUFFIX = (
    "post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T022228Z"
)
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
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
    "Keine Economic Evaluation",
    "FLEET_ECONOMIC_VALIDITY_FAIL",
    "ROBUSTNESS_FAILED",
    "NO_NEW_CANDIDATE_HOLD",
    "PANEL_ZERO_TRADE_REFUTED",
    "FAILED_BINDINGS_RETRY_ALLOWED=false",
    "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY_ALLOWED=false",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4897V4FleetRobustnessFailureDecompositionScopeDefinitionV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["selected_class"] == SELECTED_CLASS
        assert config["selected_next_scope_class"] == SELECTED_NEXT_SCOPE_CLASS
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == OPERATOR_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["required_next_go_for_execution"] == NEXT_EXECUTION_GO
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["panel_zero_trade_refuted"] is True
        assert config["same_binding_retry_allowed"] is False
        assert config["failed_bindings_retry_allowed"] is False
        assert config["threshold_lowering_allowed"] is False
        assert config["parameter_rescue_allowed"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["new_candidates_ratified"] is False
        assert config["economic_evaluation_executed"] is False
        assert config["backtest_executed"] is False
        assert config["runtime_authority"] == "NONE"
        assert config["strategy_version"] == "v4"

    def test_scope_config_blocked_actions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY",
            "DECOMPOSITION_EXECUTION_IN_THIS_SCOPE",
        ):
            assert action in blocked

    def test_scope_config_blocked_scope_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_scope_classes"])
        assert "A_UNMODIFIED_V4_BINDING_REEXECUTION" in blocked
        assert "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS" in blocked
        assert "G_RUNTIME_REWIRE" in blocked
        assert "H_NEAR_DUPLICATE_ARCHETYPE_RETRY" in blocked

    def test_scope_config_final_research_fleet(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["final_research_fleet"] == list(FLEET_CANDIDATES)

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`SELECTED_NEXT_SCOPE_CLASS` | `NEW_EVIDENCE_CLASS_REQUIRED`" in body
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in body
        assert "`BACKTEST_EXECUTED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body

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

    def test_parent_evaluation_evidence_ref_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_EVALUATION_SUFFIX in config["parent_evaluation_evidence_ref"]
        assert config["parent_evaluation_manifest_verify_rc"] == 0

    def test_confirmed_failure_classes_include_robustness_failed(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "ROBUSTNESS_FAILED" in config["confirmed_failure_classes"]
        assert "FLEET_ECONOMIC_VALIDITY_FAIL" in config["confirmed_failure_classes"]
        assert "PORTFOLIO_CONTRIBUTION_FAILURE" in config["confirmed_failure_classes"]

    def test_near_duplicate_retry_blocked(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["near_duplicate_breakout_mean_reversion_retry_allowed"] is False

    def test_authority_flags_explicitly_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["shadow_authorized"] is False
        assert config["paper_authorized"] is False
        assert config["testnet_authorized"] is False
        assert config["live_authorized"] is False
        assert config["promotion_authority"] is False

    def test_excluded_candidate_families_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        excluded = config["excluded_candidate_families"]
        assert "trend_following/v4/SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0" in excluded
        assert "unchanged_v4_panel_sequential_signal_density_binding" in excluded
