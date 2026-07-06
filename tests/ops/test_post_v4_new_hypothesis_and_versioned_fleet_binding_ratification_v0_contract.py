"""Contract tests for post-v4 new hypothesis and versioned fleet binding ratification v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md"
)
PARENT_SCOPE_DOC = (
    REPO_ROOT / "docs/governance/POST_PR4900_VERSIONED_BINDING_OR_EVALUATION_EXECUTION_SCOPE_V0.md"
)
COLLECTOR = (
    REPO_ROOT
    / "scripts/research/post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_v0.py"
)

SCOPE_GO = "GO_OPERATOR_RATIFY_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
SCOPE_ID = "POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
PROCESS_CLASSIFICATION = SCOPE_ID
SCOPE_CLASSIFICATION = (
    "NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_ONLY_AFTER_"
    "PR4901_FAIL_CLOSED_BINDING_PRECONDITION_INCOMPLETE_V0"
)
VERDICT = "SCOPE_DEFINED_NOT_EVALUATED"
BASE_HEAD = "27826eca324e88560f93d1b5993bab4b0acd0b62"
PARENT_CLOSEOUT_SUFFIX = "pr4901_squash_merge_closeout_20260706T032655Z"
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
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
NEXT_GO = "GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0"
HARD_BOUNDARIES = (
    "NO_RUNTIME_REWIRE",
    "NO_SHADOW",
    "NO_PAPER",
    "NO_TESTNET",
    "NO_ORDERS",
    "NO_LIVE",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


class TestPostV4NewHypothesisAndVersionedFleetBindingRatificationV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["verdict"] == VERDICT
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == SCOPE_GO
        assert config["base_head"] == BASE_HEAD
        assert config["next_admissible_step"] == NEXT_GO
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_dir"]
        hypothesis = config["research_hypothesis_binding"]
        assert hypothesis["ratification_status"] == "RATIFIED_FOR_BINDING_DEFINITION_ONLY"
        assert config["required_binding_fields_before_evaluation"] == list(REQUIRED_BINDING_FIELDS)

    def test_scope_config_fleet_binding_definitions(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        by_id = {c["strategy_id"]: c for c in config["final_research_fleet"]}
        for sid in FLEET_CANDIDATES:
            candidate = by_id[sid]
            assert candidate["strategy_version"] == "post_v4_hypothesis_v0"
            assert candidate["binding_status"] == "RATIFIED_BINDING_DEFINITION_ONLY"
            assert candidate["evaluation_authorized"] is False
            assert "v4" in candidate["blocked_versions"]
            assert "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0" in candidate["blocked_binding_classes"]

    def test_scope_config_authority_and_boundaries(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        authority = config["authority"]
        assert authority["economic_evaluation_authorized"] is False
        assert authority["backtest_authorized"] is False
        assert authority["runtime_authority"] == "NONE"
        assert authority["live_authorized"] is False
        boundaries = set(config["hard_boundaries"])
        for boundary in HARD_BOUNDARIES:
            assert boundary in boundaries

    def test_governance_doc_verdict_and_boundaries(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
            )
            in text
        )
        assert _field_value(text, "VERDICT") == VERDICT
        assert _field_value(text, "GO_TOKEN") == SCOPE_GO
        assert _field_value(text, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY") == "NONE"
        assert _field_value(text, "BLOCKED_BINDING_CLASS") == "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
        assert NEXT_GO in text
        assert "Binding-Definition-Ratifikation ≠ Binding-Materialisierung" in text

    def test_parent_scope_file_exists(self) -> None:
        assert PARENT_SCOPE_DOC.is_file()
        text = PARENT_SCOPE_DOC.read_text(encoding="utf-8")
        assert "BINDING_PRECONDITION_INCOMPLETE" in text
        assert SCOPE_GO in text

    def test_collector_script_declares_non_evaluating_scope(self) -> None:
        text = COLLECTOR.read_text(encoding="utf-8")
        assert SCOPE_GO in text
        assert VERDICT in text
        assert "RATIFIED_FOR_BINDING_DEFINITION_ONLY" in text
        assert "write_manifest_sha256" in text
        assert NEXT_GO in text
