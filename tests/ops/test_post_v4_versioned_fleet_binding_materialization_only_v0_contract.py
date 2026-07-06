"""Contract tests for post-v4 versioned fleet binding materialization only v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/post_v4_versioned_fleet_binding_materialization_only_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0.md"
)
PARENT_SCOPE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_V4_NEW_HYPOTHESIS_AND_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md"
)
COLLECTOR = (
    REPO_ROOT / "scripts/research/post_v4_versioned_fleet_binding_materialization_only_v0.py"
)
CLOSEOUT_SECTION_PREFIX = "#### POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0"

SCOPE_GO = "GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0"
SCOPE_ID = "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0"
PROCESS_CLASSIFICATION = SCOPE_ID
SCOPE_CLASSIFICATION = (
    "VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_NO_EVALUATION_NO_RUNTIME_AUTHORITY"
)
VERDICT = "BINDINGS_MATERIALIZED_NOT_EVALUATED"
BASE_HEAD = "c534b0eafc53b38c046bc99e823eb8318a43da7f"
PARENT_CLOSEOUT_SUFFIX = "post_v4_new_hypothesis_and_versioned_fleet_binding_ratification_scope_merge_closeout_20260706T034102Z"
FLEET_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
NEXT_GO = (
    "GO_OPERATOR_RATIFY_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
)
CURRENT_STATE = (
    "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_BINDINGS_MATERIALIZED_NOT_EVALUATED_V0"
)
NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"
)
CURRENT_ADMISSIBLE_SCOPE = "POST_V4_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_SCOPE_V0"


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing governance field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n---\n\n## PR #4629 Evidence-Drift")
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostV4VersionedFleetBindingMaterializationOnlyV0Contract:
    def test_scope_config_core_fields(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["verdict"] == VERDICT
        assert config["process_classification"] == PROCESS_CLASSIFICATION
        assert config["scope_classification"] == SCOPE_CLASSIFICATION
        assert config["go_token"] == SCOPE_GO
        assert config["base_head"] == BASE_HEAD
        assert config["next_step"] == NEXT_GO
        assert config["parent_pr"] == 4902
        assert PARENT_CLOSEOUT_SUFFIX in config["parent_closeout_dir"]
        assert config["hypothesis_status"] == "RATIFIED_FOR_BINDING_DEFINITION_ONLY"
        assert config["materialization_status"] == "BINDING_MATERIALIZATION_ONLY"
        assert config["economic_evaluation_authorized"] is False
        assert config["runtime_authority_created"] is False
        assert config["live_authorized"] is False

    def test_scope_config_fleet_bindings_materialized(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        by_id = {c["strategy_id"]: c for c in config["fleet_bindings"]}
        for sid in FLEET_CANDIDATES:
            binding = by_id[sid]
            assert binding["strategy_version"] == "post_v4_hypothesis_v0"
            assert binding["evaluation_status"] == "NOT_EVALUATED"
            assert binding["runtime_status"] == "NO_RUNTIME_AUTHORITY"
            assert binding["candidate_binding_id"].endswith("_binding_materialized")

    def test_scope_config_blocked_scopes_and_execution_classes(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert "v4" in config["blocked_research_scopes"]
        assert "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0" in config["blocked_research_scopes"]
        blocked = set(config["blocked_execution_classes"])
        for action in (
            "OFFLINE_BACKTEST",
            "WALK_FORWARD",
            "MONTE_CARLO",
            "STRESS",
            "ECONOMIC_VIABILITY_EVIDENCE_EXECUTION",
            "LIVE",
        ):
            assert action in blocked
        policy = config["global_binding_policy"]
        assert policy["futures_only"] is True
        assert policy["failed_binding_retry_unchanged_allowed"] is False
        assert policy["policy_threshold_lowering_allowed"] is False

    def test_governance_doc_verdict_and_boundaries(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker("DOCS_TOKEN_POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0")
            in text
        )
        assert _field_value(text, "VERDICT") == VERDICT
        assert _field_value(text, "GO_TOKEN") == SCOPE_GO
        assert _field_value(text, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(text, "RUNTIME_AUTHORITY") == "NONE"
        assert _field_value(text, "BLOCKED_BINDING_CLASS") == "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
        assert NEXT_GO in text
        assert "Binding-Materialisierung ≠ Evaluation-Autorisierung" in text

    def test_parent_scope_file_exists(self) -> None:
        assert PARENT_SCOPE_DOC.is_file()
        text = PARENT_SCOPE_DOC.read_text(encoding="utf-8")
        assert SCOPE_GO in text
        assert "RATIFIED_FOR_BINDING_DEFINITION_ONLY" in text

    def test_collector_script_declares_non_evaluating_scope(self) -> None:
        text = COLLECTOR.read_text(encoding="utf-8")
        assert SCOPE_GO in text
        assert VERDICT in text
        assert "BINDING_MATERIALIZATION_ONLY" in text
        assert "write_manifest_sha256" in text
        assert NEXT_GO in text

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert _field_value(text, "CURRENT_STATE") == CURRENT_STATE
        assert _field_value(text, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(text, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(text, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_GO
        assert _field_value(text, "LAST_VERIFIED_ORIGIN_MAIN") == BASE_HEAD
        assert (
            _field_value(text, "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0_STATUS")
            == VERDICT
        )
        assert (
            _field_value(text, "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0_GO_TOKEN")
            == SCOPE_GO
        )
        assert (
            _field_value(
                text,
                "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0_REQUIRED_NEXT_GO_FOR_EVALUATION",
            )
            == NEXT_GO
        )
        assert PARENT_CLOSEOUT_SUFFIX in _field_value(
            text, "POST_V4_VERSIONED_FLEET_BINDING_MATERIALIZATION_ONLY_V0_PARENT_CLOSEOUT_REF"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == VERDICT
        assert _field_value(section, "VERDICT") == VERDICT
        assert _field_value(section, "GO_TOKEN") == SCOPE_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "false"
        assert _field_value(section, "BASELINE_HEAD") == BASE_HEAD
        assert _field_value(section, "EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "NONE"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_OFFLINE_EVALUATION") == NEXT_GO
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == NEXT_GO
        assert _field_value(section, "offline_only") == "true"
        assert _field_value(section, "non_authorizing") == "true"
