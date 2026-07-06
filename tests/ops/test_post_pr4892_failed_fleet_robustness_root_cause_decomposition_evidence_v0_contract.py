"""Contract tests for post-PR4892 failed fleet robustness root-cause decomposition evidence v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_V0.md"
)
SCOPE_DEFINITION_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4892_failed_fleet_robustness_root_cause_scope_definition_v0.json"
)
EXECUTION_GO = (
    "GO_POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
)
EVIDENCE_CLASS_ID = "POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_V0"
PROCESS_CLASSIFICATION = (
    "POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_EXECUTION_V0"
)
SCOPE_CLASSIFICATION = (
    "POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_CLASS_V0"
)
EXECUTION_STATUS = "ROOT_CAUSE_DECOMPOSITION_EXECUTION_COMPLETE_V0"
SELECTED_CLASS = "E"
BASELINE_HEAD = "223fdb519a4bba0875314c22ed9bc62180f01cad"
PARENT_EXECUTION_SUFFIX = (
    "post_no_pass_step31f_owner_fix_offline_economic_evaluation_execution_v0_20260706T010502Z"
)
SCOPE_DEFINITION_SUFFIX = (
    "post_pr4892_failed_fleet_robustness_root_cause_scope_definition_v0_20260706T014350Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
DECOMPOSITION_AXES = (
    "signal_edge",
    "turnover_cost_drag",
    "regime_instability",
    "parameter_fragility",
    "sparse_signal_underpowering",
    "long_short_asymmetry",
    "instrument_concentration",
    "funding_slippage_sensitivity",
    "portfolio_contribution_failure",
)
NEXT_RATIFICATION_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_DEFINITION_ONLY_V0"
)
BOUNDARY_PHRASES = (
    "NO_UNCHANGED_V3_BINDING_RETRY",
    "PANEL_ZERO_TRADE_REFUTED",
    "TERMINAL_NEGATIVE",
    "MISSING_EVIDENCE",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4892FailedFleetRobustnessRootCauseDecompositionEvidenceV0Contract:
    def test_decomposition_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == EXECUTION_STATUS
        assert config["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["selected_class"] == SELECTED_CLASS
        assert config["go_token"] == EXECUTION_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["fleet_verdict"] == "ROBUSTNESS_FAILED"
        assert config["economic_validity_offline_gate_pass"] is False
        assert config["panel_zero_trade_refuted"] is True
        assert config["same_binding_retry_allowed"] is False
        assert config["immutable_binding_retry_allowed"] is False
        assert config["new_candidates_ratified"] is False
        assert config["decomposition_axes"] == list(DECOMPOSITION_AXES)

    def test_decomposition_config_reuses_scope_definition(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        scope_def = json.loads(SCOPE_DEFINITION_CONFIG.read_text(encoding="utf-8"))
        assert config["failed_candidates"] == scope_def["failed_candidates"]
        assert config["fleet_verdict"] == scope_def["fleet_verdict"]
        assert PARENT_EXECUTION_SUFFIX in config["parent_execution_evidence_ref"]
        assert SCOPE_DEFINITION_SUFFIX in config["parent_scope_definition_evidence_ref"]
        assert config["parent_execution_manifest_verify_rc"] == 0
        assert config["parent_scope_definition_manifest_verify_rc"] == 0

    def test_decomposition_config_blocked_actions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "SAME_BINDING_RETRY",
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
                "DOCS_TOKEN_POST_PR4892_FAILED_FLEET_ROBUSTNESS_ROOT_CAUSE_DECOMPOSITION_EVIDENCE_V0"
            )
            in body
        )
        assert f"`GO_TOKEN` | `{EXECUTION_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`EXECUTION_STATUS` | `{EXECUTION_STATUS}`" in body
        assert "`FLEET_VERDICT` | `ROBUSTNESS_FAILED`" in body
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

    def test_governance_doc_next_ratification_go(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert NEXT_RATIFICATION_GO in body
        assert _field_value(body, "SAME_BINDING_RETRY_ALLOWED") == "false"

    def test_collector_script_exists(self) -> None:
        script = (
            REPO_ROOT
            / "scripts/research/post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0.py"
        )
        assert script.is_file()
        body = script.read_text(encoding="utf-8")
        assert EXECUTION_GO in body
        assert "ROOT_CAUSE_DECOMPOSITION_REPORT.md" in body
        assert "ROOT_CAUSE_DECOMPOSITION_SUMMARY.json" in body
        assert "INPUT_EVIDENCE_INDEX.json" in body
        assert "GOVERNANCE_BOUNDARY_ATTESTATION.json" in body
        assert "RUN_METADATA.json" in body
