"""Contract tests for post-PR4894 next versioned research scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_pr4894_next_versioned_research_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md"
)
OPERATOR_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
EVIDENCE_CLASS_ID = "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
SCOPE_ID = "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
SCOPE_CLASSIFICATION = (
    "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_"
    "ROOT_CAUSE_DECOMPOSITION_V0"
)
SELECTED_CLASS = "D"
NEXT_BINDING_RATIFICATION_GO = "GO_POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
BASELINE_HEAD = "04d176f291f3824857dd2636f5059bc8c1d67136"
PARENT_DECOMPOSITION_SUFFIX = (
    "post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0_20260706T015337Z"
)
REQUIRED_BINDING_FIELDS = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
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
    "Scope-Definition ≠ Binding-Ratifikation",
    "Keine Economic Evaluation",
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


class TestPostPr4894NextVersionedResearchScopeDefinitionV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["selected_class"] == SELECTED_CLASS
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == OPERATOR_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["required_next_go_for_binding_ratification"] == NEXT_BINDING_RATIFICATION_GO
        assert config["fleet_verdict"] == "ROBUSTNESS_FAILED"
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
            "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY",
            "BINDING_RATIFICATION_IN_THIS_SCOPE",
        ):
            assert action in blocked

    def test_scope_config_blocked_scope_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_scope_classes"])
        assert "A_UNMODIFIED_V3_BINDING_REEXECUTION" in blocked
        assert "G_RUNTIME_REWIRE" in blocked
        assert "H_NEAR_DUPLICATE_ARCHETYPE_RETRY" in blocked

    def test_scope_config_required_binding_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        for field in REQUIRED_BINDING_FIELDS:
            assert field in config["required_binding_fields"]

    def test_scope_config_final_research_fleet(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["final_research_fleet"] == list(FLEET_CANDIDATES)
        assert config["final_research_fleet_status"] == "BINDINGS_REQUIRED_BEFORE_EVALUATION"

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0")
            in body
        )
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `ROBUSTNESS_FAILED`" in body
        assert "`PANEL_ZERO_TRADE_REFUTED` | `true`" in body
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

    def test_governance_doc_next_binding_ratification_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _field_value(body, "REQUIRED_NEXT_GO_FOR_BINDING_RATIFICATION")
            == NEXT_BINDING_RATIFICATION_GO
        )

    def test_parent_decomposition_evidence_ref_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_DECOMPOSITION_SUFFIX in config["parent_decomposition_evidence_ref"]
        assert config["parent_decomposition_manifest_verify_rc"] == 0

    def test_confirmed_failure_classes_include_robustness_failed(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "ROBUSTNESS_FAILED" in config["confirmed_failure_classes"]
        assert "NEGATIVE_NET_EDGE" in config["confirmed_failure_classes"]
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
        assert config["new_candidate_ratified"] is False
