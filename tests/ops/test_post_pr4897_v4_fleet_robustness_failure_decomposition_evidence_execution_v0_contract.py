"""Contract tests for post-PR4897 v4 fleet failure decomposition evidence execution v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_execution_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0.md"
)
SCOPE_DEFINITION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_class_scope_definition_v0.json"
)
EXECUTION_GO = "GO_POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
EVIDENCE_CLASS_ID = "POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
SCOPE_ID = (
    "POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_CLASS_SCOPE_DEFINITION_V0"
)
PROCESS_CLASSIFICATION = EXECUTION_ID = EVIDENCE_CLASS_ID
SCOPE_CLASSIFICATION = (
    "READ_ONLY_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_AFTER_FLEET_ECONOMIC_VALIDITY_FAIL_V0"
)
EXECUTION_STATUS = "FAILURE_DECOMPOSITION_EXECUTION_COMPLETE_V0"
SELECTED_CLASS = "E"
BASELINE_HEAD = "d592746dc6ae63b96731c60c0fd36c99f6f2e273"
PARENT_EVALUATION_SUFFIX = (
    "post_pr4895_versioned_fleet_offline_economic_evaluation_execution_v0_20260706T022228Z"
)
SCOPE_DEFINITION_SUFFIX = (
    "post_pr4897_next_versioned_research_scope_definition_only_v0_20260706T025026Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
DECOMPOSITION_AXES = (
    "signal_edge",
    "turnover_cost_drag",
    "regime_instability",
    "monte_carlo_negative_return_fragility",
    "parameter_fragility",
    "sparse_signal_underpowering",
    "long_short_asymmetry",
    "instrument_concentration",
    "funding_slippage_sensitivity",
    "portfolio_contribution_failure",
    "binding_delta_rescue_hypothesis",
)
NEXT_SCOPE_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
BOUNDARY_PHRASES = (
    "NO_UNCHANGED_V4_BINDING_RETRY",
    "PANEL_ZERO_TRADE_REFUTED",
    "TERMINAL_NEGATIVE",
    "MISSING_EVIDENCE",
    "REFUTED",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4897V4FleetRobustnessFailureDecompositionEvidenceExecutionV0Contract:
    def test_execution_config_core_fields(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == EXECUTION_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["execution_id"] == EXECUTION_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["selected_class"] == SELECTED_CLASS
        assert config["go_token"] == EXECUTION_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["fleet_verdict"] == "FLEET_ECONOMIC_VALIDITY_FAIL"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["panel_zero_trade_refuted"] is True
        assert config["same_binding_retry_allowed"] is False
        assert config["immutable_binding_retry_allowed"] is False
        assert config["new_candidates_ratified"] is False
        assert config["strategy_version"] == "v4"
        assert config["decomposition_axes"] == list(DECOMPOSITION_AXES)

    def test_execution_config_reuses_scope_definition(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        scope_def = json.loads(SCOPE_DEFINITION_CONFIG.read_text(encoding="utf-8"))
        assert config["failed_candidates"] == scope_def["failed_candidates"]
        assert config["scope_id"] == scope_def["scope_id"]
        assert PARENT_EVALUATION_SUFFIX in config["parent_evaluation_evidence_ref"]
        assert SCOPE_DEFINITION_SUFFIX in config["parent_scope_definition_evidence_ref"]
        assert config["parent_evaluation_manifest_verify_rc"] == 0
        assert config["parent_scope_definition_manifest_verify_rc"] == 0

    def test_execution_config_blocked_actions(self) -> None:
        config = json.loads(EXECUTION_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "NEW_CANDIDATE_RATIFICATION",
        ):
            assert action in blocked

    def test_governance_doc_exists_with_docs_token(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4897_V4_FLEET_ROBUSTNESS_FAILURE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{EXECUTION_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`EXECUTION_STATUS` | `{EXECUTION_STATUS}`" in body
        assert "`FLEET_VERDICT` | `FLEET_ECONOMIC_VALIDITY_FAIL`" in body
        assert "`PANEL_ZERO_TRADE_REFUTED` | `true`" in body
        assert "`FAILED_BINDINGS_RETRY_ALLOWED` | `false`" in body

    def test_governance_doc_boundary_phrases(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body

    def test_governance_doc_failed_candidates(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        for candidate in FAILED_CANDIDATES:
            assert f"`{candidate}`" in body
            assert "ROBUSTNESS_FAILED" in body

    def test_governance_doc_no_execution_flags(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "`economic_evaluation_executed` | `false`" in body
        assert "`backtest_executed` | `false`" in body
        assert "`walk_forward_run_executed` | `false`" in body
        assert "`monte_carlo_run_executed` | `false`" in body
        assert "`stress_run_executed` | `false`" in body
        assert "`RUNTIME_AUTHORITY` | `NONE`" in body

    def test_governance_doc_next_scope_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert NEXT_SCOPE_GO in body
        assert _field_value(body, "SAME_BINDING_RETRY_ALLOWED") == "false"

    def test_collector_script_exists(self) -> None:
        script = (
            REPO_ROOT
            / "scripts/research/post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_execution_v0.py"
        )
        assert script.is_file()
        body = script.read_text(encoding="utf-8")
        assert EXECUTION_GO in body
        assert "FAILURE_DECOMPOSITION_REPORT.md" in body
        assert "FAILURE_DECOMPOSITION_SUMMARY.json" in body
        assert "INPUT_EVIDENCE_INDEX.json" in body
        assert "GOVERNANCE_BOUNDARY_ATTESTATION.json" in body
        assert "RUN_METADATA.json" in body
        assert "CANDIDATE_RESULT_" in body
