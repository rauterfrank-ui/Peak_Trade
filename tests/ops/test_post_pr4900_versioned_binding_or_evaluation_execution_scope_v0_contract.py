"""Contract tests for post-PR4900 versioned binding or evaluation execution scope v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_pr4900_versioned_binding_or_evaluation_execution_scope_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0.md"
)
PARENT_SCOPE_FILE = (
    REPO_ROOT
    / "docs/ops/research/POST_PR4899_TERMINAL_FLEET_FAILURE_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0.md"
)
V4_BINDING_CONFIG = (
    REPO_ROOT / "config/research/post_pr4895_versioned_fleet_binding_ratification_v0.json"
)
COLLECTOR = (
    REPO_ROOT / "scripts/research/post_pr4900_versioned_binding_or_evaluation_execution_scope_v0.py"
)

SCOPE_GO = "GO_POST_PR4899_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0"
SCOPE_ID = "POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0"
PROCESS_CLASSIFICATION = SCOPE_ID
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_BINDING_FIRST_AND_FAIL_CLOSED_OFFLINE_ECONOMIC_EVALUATION_SCOPE_"
    "AFTER_TERMINAL_V4_FLEET_FAILURE_V0"
)
EXECUTION_STATUS = "BINDING_PRECONDITION_INCOMPLETE_NOT_EVALUATED_V0"
BASELINE_HEAD = "8a04f3885a31ec5d0752d5e1fb4bd2eb10b0bc0d"
PARENT_BUNDLE_SUFFIX = (
    "post_pr4897_v4_fleet_robustness_failure_decomposition_evidence_execution_v0_20260706T030033Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
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
    "research_hypothesis_binding",
    "binding_class_binding",
)
NEXT_GO = "GO_OPERATOR_RATIFY_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostPr4900VersionedBindingOrEvaluationExecutionScopeV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["status"] == EXECUTION_STATUS
        assert config["evidence_class_id"] == SCOPE_ID
        assert config["scope_id"] == SCOPE_ID
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == SCOPE_GO
        assert config["baseline_head"] == BASELINE_HEAD
        assert config["binding_precondition_status"] == "BINDING_PRECONDITION_INCOMPLETE"
        assert config["result_classification"] == "BINDING_PRECONDITION_INCOMPLETE"
        assert config["economic_evaluation_executed"] is False
        assert config["backtest_executed"] is False
        assert config["walk_forward_executed"] is False
        assert config["monte_carlo_executed"] is False
        assert config["stress_executed"] is False
        assert config["parent_manifest_verify_rc"] == 0
        assert config["required_binding_fields"] == list(REQUIRED_BINDING_FIELDS)
        assert PARENT_BUNDLE_SUFFIX in config["parent_evidence_bundle"]

    def test_scope_config_blocked_actions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        blocked = set(config["blocked_actions"])
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "V4_TERMINAL_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "PARAMETER_RESCUE",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
        ):
            assert action in blocked

    def test_governance_doc_verdict_and_boundaries(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0"
            )
            in text
        )
        assert _field_value(text, "VERDICT") == EXECUTION_STATUS
        assert (
            _field_value(text, "BINDING_PRECONDITION_STATUS") == "BINDING_PRECONDITION_INCOMPLETE"
        )
        assert _field_value(text, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(text, "BACKTEST_EXECUTED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY") == "NONE"
        assert _field_value(text, "GO_TOKEN") == SCOPE_GO
        assert NEXT_GO in text

    def test_parent_scope_file_exists(self) -> None:
        assert PARENT_SCOPE_FILE.is_file()
        text = PARENT_SCOPE_FILE.read_text(encoding="utf-8")
        assert "research_hypothesis_binding" in text
        assert "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0" in text

    def test_v4_binding_inventory_is_terminal_not_admissible(self) -> None:
        v4 = json.loads(V4_BINDING_CONFIG.read_text(encoding="utf-8"))
        assert v4["strategy_version"] == "v4"
        assert v4["fleet_bindings_ratified"] is True
        candidates = {c["strategy_id"]: c for c in v4["candidates"]}
        for sid in FAILED_CANDIDATES:
            candidate = candidates[sid]
            assert candidate["strategy_version"] == "v4"
            adapter = candidate["dataset_binding"]["evaluation_price_data_adapter"]
            assert adapter["binding_class"] == "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
            assert "research_hypothesis_binding" not in candidate

    def test_collector_script_declares_fail_closed_scope(self) -> None:
        text = COLLECTOR.read_text(encoding="utf-8")
        assert SCOPE_GO in text
        assert "BINDING_PRECONDITION_INCOMPLETE" in text
        assert "evaluation_admissible" in text
        assert "write_manifest_sha256" in text
