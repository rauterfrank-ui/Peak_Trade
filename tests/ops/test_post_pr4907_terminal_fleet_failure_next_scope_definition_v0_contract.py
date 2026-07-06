"""Contract tests for post-PR4907 terminal fleet failure next scope definition v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_pr4907_terminal_fleet_failure_next_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0.md"
)
OPERATOR_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_"
    "AFTER_POST_PR4906_OFFLINE_EVIDENCE_EXECUTION_V0"
)
EVIDENCE_CLASS_ID = "POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0"
SCOPE_ID = EVIDENCE_CLASS_ID
SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0"
SCOPE_CLASSIFICATION = (
    "NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_DEFINITION_ONLY_AFTER_TERMINAL_"
    "PR4907_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
)
SELECTED_CLASS = "I"
SELECTED_NEXT_SCOPE_CLASS = "OFFLINE_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_EXECUTION_REQUIRED"
NEXT_EXECUTION_GO = (
    "GO_OPERATOR_RATIFY_NEXT_OFFLINE_ONLY_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_"
    "EXECUTION_SCOPE_AFTER_POST_PR4907_TERMINAL_FAILURE_SCOPE_DEFINITION_V0"
)
BASELINE_HEAD = "320398092a22544471a0a0861198b676b29308d3"
PARENT_PR4905_OUTPUT_SUFFIX = (
    "post_pr4904_v4_fleet_robustness_failure_decomposition_v0_20260706T042551Z"
)
PARENT_PR4905_CLOSEOUT_SUFFIX = "pr4905_squash_merge_closeout_20260706T043541Z"
PARENT_PR4906_CLOSEOUT_SUFFIX = (
    "post_pr4905_terminal_fleet_failure_next_scope_definition_merge_closeout_20260706T044625Z"
)
PARENT_PR4907_EVIDENCE_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_v0_20260706T045000Z"
)
PARENT_PR4907_CLOSEOUT_SUFFIX = (
    "post_pr4906_offline_only_terminal_fleet_failure_evidence_execution_merge_closeout_"
    "20260706T045620Z"
)
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
ADMISSIBLE_EVIDENCE_CLASSES = (
    "TRADE_LEDGER_LONG_SHORT_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
    "TURNOVER_COST_DRAG_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
    "INSTRUMENT_CONCENTRATION_DECOMPOSITION_OFFLINE_ARTIFACT_V0",
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
    "NO_NEW_CANDIDATE_HOLD",
    "FAILED_BINDINGS_RETRY_ALLOWED=false",
    "UNCHANGED_RETRY_ALLOWED=false",
    "POLICY_THRESHOLD_RESCUE_ALLOWED=false",
    "FAILED_EVIDENCE_IS_TERMINAL=true",
    "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY_ALLOWED=false",
    "POLICY_CHANGE_TO_RECLASSIFY_NEGATIVE_EVIDENCE",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4907TerminalFleetFailureNextScopeDefinitionV0Contract:
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
        assert config["parent_pr4907_aggregate_result"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["failed_evidence_is_terminal"] is True
        assert config["same_binding_retry_allowed"] is False
        assert config["unchanged_retry_allowed"] is False
        assert config["failed_bindings_retry_allowed"] is False
        assert config["policy_threshold_rescue_allowed"] is False
        assert config["threshold_lowering_allowed"] is False
        assert config["parameter_rescue_allowed"] is False
        assert config["runtime_rewire_admissible"] is False
        assert config["new_candidates_ratified"] is False
        assert config["economic_evaluation_executed"] is False
        assert config["offline_evaluation_executed"] is False
        assert config["backtest_executed"] is False
        assert config["evidence_execution_completed"] is True
        assert config["runtime_authority"] == "NONE"
        assert config["runtime_authority_created"] is False
        assert config["strategy_version"] == "post_v4_hypothesis_v0"
        assert config["no_evaluation_authority"] is True

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
            "POLICY_THRESHOLD_RESCUE",
            "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY",
            "EVIDENCE_EXECUTION_IN_THIS_SCOPE",
            "EVIDENCE_EXECUTION_REEXECUTION",
            "POLICY_CHANGE_TO_RECLASSIFY_NEGATIVE_EVIDENCE",
        ):
            assert action in blocked

    def test_scope_config_blocked_scope_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_scope_classes"])
        assert "A_UNMODIFIED_POST_V4_BINDING_REEXECUTION" in blocked
        assert "F_ECONOMIC_EVALUATION_RESCUE" in blocked
        assert "F_OFFLINE_ONLY_RESEARCH_OR_EVIDENCE_EXECUTION_REEXECUTION" in blocked
        assert "G_RUNTIME_REWIRE" in blocked
        assert "H_NEAR_DUPLICATE_ARCHETYPE_RETRY" in blocked

    def test_scope_config_admissible_evidence_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["admissible_next_evidence_classes"] == list(ADMISSIBLE_EVIDENCE_CLASSES)

    def test_scope_config_final_research_fleet(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["final_research_fleet"] == list(FLEET_CANDIDATES)
        assert (
            config["final_research_fleet_status"]
            == "TERMINAL_NEGATIVE_EVIDENCE_ARTIFACT_MATERIALIZATION_REQUIRED"
        )

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4907_TERMINAL_FLEET_FAILURE_NEXT_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "LIVE_AUTHORIZED: false" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert (
            "`SELECTED_NEXT_SCOPE_CLASS` | "
            "`OFFLINE_ARTIFACT_MATERIALIZATION_OR_EVIDENCE_CLASS_EXECUTION_REQUIRED`" in body
        )
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in body
        assert "`OFFLINE_EVALUATION_EXECUTED` | `false`" in body
        assert "`BACKTEST_EXECUTED` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body
        assert "`RUNTIME_AUTHORITY_CREATED` | `false`" in body
        assert "`FAILED_EVIDENCE_IS_TERMINAL` | `true`" in body

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

    def test_parent_pr4907_evidence_refs_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert PARENT_PR4905_OUTPUT_SUFFIX in config["parent_pr4905_output_bundle"]
        assert PARENT_PR4905_CLOSEOUT_SUFFIX in config["parent_pr4905_closeout_dir"]
        assert PARENT_PR4906_CLOSEOUT_SUFFIX in config["parent_pr4906_closeout_dir"]
        assert PARENT_PR4907_EVIDENCE_SUFFIX in config["parent_pr4907_evidence_bundle"]
        assert PARENT_PR4907_CLOSEOUT_SUFFIX in config["parent_pr4907_closeout_dir"]
        assert config["parent_evidence_manifest_verify_rc"] == 0
        assert config["parent_closeout_manifest_verify_rc"] == 0
        assert config["parent_pr4907_evidence_manifest_verify_rc"] == 0
        assert config["parent_pr4907_closeout_manifest_verify_rc"] == 0
        assert config["parent_pr"] == 4907

    def test_confirmed_failure_classes_include_fleet_fail(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "ROBUSTNESS_FAILED" in config["confirmed_failure_classes"]
        assert "FLEET_ECONOMIC_VALIDITY_FAIL" in config["confirmed_failure_classes"]
        assert "MISSING_SOURCE_ARTIFACT" in config["confirmed_failure_classes"]
        assert "REFUTED_AS_PRIMARY_RESCUE_PATH" in config["confirmed_failure_classes"]

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
        assert config["orders_allowed"] is False

    def test_scope_is_definition_only_not_execution(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["non_authorizing"] is True
        assert config["offline_only"] is True
        assert config["repo_mutation_scope"] == "GOVERNANCE_ONLY"
        assert config["required_future_operator_go"] is True
        assert config["evidence_execution_executed"] is False

    def test_excluded_candidate_families_present(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        excluded = config["excluded_candidate_families"]
        assert "trend_following/post_v4_hypothesis_v0" in excluded
        assert "unchanged_post_v4_hypothesis_v0_binding" in excluded

    def test_mutation_flags_all_false(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["core_system_mutation_allowed"] is False
        assert config["double_play_mutation_allowed"] is False
        assert config["risk_sizing_mutation_allowed"] is False
        assert config["safety_runtime_mutation_allowed"] is False
