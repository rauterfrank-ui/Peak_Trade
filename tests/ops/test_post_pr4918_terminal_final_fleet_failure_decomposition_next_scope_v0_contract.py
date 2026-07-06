"""Contract tests for post-PR4918 terminal final fleet failure decomposition next scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4918_terminal_final_fleet_failure_decomposition_next_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4918_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_AND_NEXT_SCOPE_DECISION_V0.md"
)
SCOPE_GO = "GO_POST_PR4918_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_AND_NEXT_SCOPE_DEFINITION_V0"
EVIDENCE_CLASS_ID = (
    "POST_PR4918_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_AND_NEXT_SCOPE_DECISION_V0"
)
SCOPE_ID = EVIDENCE_CLASS_ID
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = (
    "POST_PR4918_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_AND_NEXT_SCOPE_DEFINITION_V0"
)
SCOPE_CLASSIFICATION = (
    "NEW_VERSIONED_RESEARCH_SCOPE_OR_FAILURE_DECOMPOSITION_DEFINITION_ONLY_AFTER_"
    "TERMINAL_FINAL_FLEET_FAIL_V0"
)
NEXT_STEP = (
    "OPERATOR_RATIFIED_NEW_VERSIONED_RESEARCH_SCOPE_OR_FAILURE_DECOMPOSITION_FOLLOWUP_REQUIRED"
)
PARENT_HEAD = "e5eafea28a96dcfdbb46593bea03b8769d5c3a4e"
PARENT_REVIEW_SUFFIX = (
    "pr4918_offline_economic_validity_evidence_and_promotion_admissibility_review_20260706T072735Z"
)
PARENT_CLOSEOUT_SUFFIX = (
    "pr4918_ratified_final_fleet_offline_economic_evaluation_execution_merge_closeout_"
    "20260706T072446Z"
)
PARENT_EXECUTION_SUFFIX = (
    "ratified_final_fleet_offline_economic_evaluation_execution_20260706T070422Z"
)
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
ALLOWED_NEXT_SCOPE_TYPES = (
    "FAILURE_DECOMPOSITION_ONLY",
    "NEW_VERSIONED_RESEARCH_SCOPE_DEFINITION_ONLY",
    "OPERATOR_RATIFIED_RESEARCH_DECISION_ONLY",
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
    "Scope-Definition ≠ Evidence-Execution",
    "Keine Economic Evaluation",
    "FLEET_ECONOMIC_VALIDITY_FAIL",
    "retry_unchanged_binding_allowed",
    "operator_override_allowed",
    "governance_wording_override_allowed",
    "FAILED_EVIDENCE_IS_TERMINAL=true",
    "PROMOTION_ADMISSIBLE",
    "RUNTIME_REWIRE_ADMISSIBLE",
    "POLICY_CHANGE_TO_RECLASSIFY_NEGATIVE_EVIDENCE",
    "NEW_CANDIDATE_RATIFIED",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4918TerminalFinalFleetFailureDecompositionNextScopeV0Contract:
    def test_scope_config_exists_and_parses(self) -> None:
        assert SCOPE_CONFIG.is_file()
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert isinstance(config, dict)
        assert config["schema_version"] == (
            "post_pr4918_terminal_final_fleet_failure_decomposition_next_scope.v0"
        )

    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == SCOPE_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == SCOPE_GO
        assert config["parent_head"] == PARENT_HEAD
        assert config["parent_pr"] == 4918
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["promotion_admissible"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["next_step"] == NEXT_STEP

    def test_failed_bindings_no_unchanged_retry(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["retry_unchanged_binding_allowed"] is False
        assert config["same_binding_retry_allowed"] is False
        assert config["unchanged_retry_allowed"] is False
        assert config["failed_bindings_retry_allowed"] is False
        for binding in config["failed_bindings"]:
            assert binding["retry_unchanged_binding_allowed"] is False
            assert binding["promotion_admissible"] is False

    def test_no_new_candidate_ratified(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["new_candidate_ratified"] is False
        assert config["new_candidates_ratified"] is False

    def test_no_evaluation_or_runtime_authority(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["economic_evaluation_authorized"] is False
        assert config["runtime_authority_created"] is False
        assert config["runtime_authority"] == "NONE"
        assert config["no_evaluation_authority"] is True
        assert config["no_runtime_authority"] is True

    def test_prohibited_actions_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        prohibited = set(config["prohibited_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "NEW_CANDIDATE_RATIFICATION",
            "SAME_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "THRESHOLD_LOWERING",
            "POLICY_THRESHOLD_RESCUE",
            "RUNTIME_REWIRE",
            *FORBIDDEN_RUNTIME_ACTIONS,
        ):
            assert action in prohibited

    def test_blocked_actions_include_runtime_and_orders(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in blocked

    def test_allowed_next_scope_types(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["allowed_next_scope_types"] == list(ALLOWED_NEXT_SCOPE_TYPES)

    def test_failed_bindings_candidate_summaries(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        by_id = {b["canonical_candidate_identifier"]: b for b in config["failed_bindings"]}
        assert by_id["trend_following/v1"]["net_return"] == -0.002398
        assert by_id["trend_following/v1"]["profit_factor"] == 0.951
        assert by_id["trend_following/v1"]["max_drawdown"] == -0.009945
        assert by_id["trend_following/v1"]["classified_verdict"] == "ROBUSTNESS_FAILED"
        assert by_id["bollinger_bands/v1"]["raw_evidence_status"] == "RESEARCH_ONLY"
        assert by_id["bollinger_bands/v1"]["classified_verdict"] == "ROBUSTNESS_FAILED"
        assert by_id["momentum_1h/v1"]["net_return"] == -0.001889
        assert by_id["momentum_1h/v1"]["profit_factor"] == 0.285
        assert by_id["momentum_1h/v1"]["max_drawdown"] == -0.002638

    def test_parent_refs_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_REVIEW_SUFFIX in config["parent_review_bundle"]
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_execution_closeout"]
        assert PARENT_EXECUTION_SUFFIX in config["parent_evidence_execution_bundle"]
        assert config["parent_review_bundle_manifest_verify_rc"] == 0
        assert config["parent_execution_closeout_manifest_verify_rc"] == 0
        assert config["parent_evidence_execution_manifest_verify_rc"] == 0

    def test_final_research_fleet(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["final_research_fleet"] == list(FLEET_CANDIDATES)
        assert config["strategy_version"] == "v1"

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4918_TERMINAL_FINAL_FLEET_FAILURE_DECOMPOSITION_AND_NEXT_SCOPE_DECISION_V0"
            )
            in body
        )
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_AUTHORITY_CREATED` | `false`" in body
        assert "`NEW_CANDIDATE_RATIFIED` | `false`" in body
        assert "`PROMOTION_ADMISSIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_forbidden_runtime_actions(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in body

    def test_governance_doc_next_step(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "NEXT_STEP") == NEXT_STEP

    def test_governance_doc_parent_pr4918(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert _field_value(body, "PARENT_PR") == "4918"
        assert PARENT_REVIEW_SUFFIX in body
        assert PARENT_CLOSEOUT_SUFFIX in body

    def test_scope_is_definition_only_not_execution(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["non_authorizing"] is True
        assert config["offline_only"] is True
        assert config["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert config["required_future_operator_go"] is True
        assert config["evidence_execution_executed"] is False

    def test_terminality_flags(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["failed_evidence_is_terminal"] is True
        assert config["operator_override_allowed"] is False
        assert config["governance_wording_override_allowed"] is False
        assert config["policy_threshold_rescue_allowed"] is False

    def test_authority_flags_explicitly_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["shadow_authorized"] is False
        assert config["paper_authorized"] is False
        assert config["testnet_authorized"] is False
        assert config["live_authorized"] is False
        assert config["promotion_authority"] is False
        assert config["orders_allowed"] is False

    def test_mutation_flags_all_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["core_system_mutation_allowed"] is False
        assert config["double_play_mutation_allowed"] is False
        assert config["risk_sizing_mutation_allowed"] is False
        assert config["safety_runtime_mutation_allowed"] is False
