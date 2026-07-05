"""Contract tests for post-no-pass inconclusive metric materialization path diagnostics execution v0."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_class_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
EVIDENCE_CLASS_ID = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
SELECTED_CLASS = "E"
EXECUTION_GO = (
    "GO_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
CURRENT_STATE = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_COMPLETE_V0"
)
NEXT_CANONICAL_STEP = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_REQUIRES_OPERATOR_RATIFICATION_V0"
)
CURRENT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)
RATIFICATION_GO = (
    "GO_OPERATOR_RATIFY_NEXT_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
)
EXECUTION_STATUS = "DIAGNOSTICS_EXECUTION_COMPLETE_V0"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
MATERIALIZATION_PATH_STATUS = "PATH_PRESENT_RUNNER_FAILED_METRICS_NOT_MATERIALIZED"
PARENT_EXECUTION_SUFFIX = (
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0_20260705T213529Z"
)
CLASSIFICATION_SUFFIX = (
    "post_no_pass_sparse_signal_inconclusive_failure_classification_execution_v0_20260705T222507Z"
)
NEW_EVIDENCE_SUFFIX = (
    "post_no_pass_inconclusive_metric_materialization_path_diagnostics_evidence_execution_v0_20260705T230238Z"
)
FAILED_CANDIDATES = ("trend_following", "bollinger_bands", "momentum_1h")
FORBIDDEN_NEXT_SCOPE_MARKERS = (
    "ECONOMIC_EVALUATION_EXECUTION",
    "BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
)


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n#### POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_V0")
    return tail if next_heading == -1 else tail[:next_heading]


class TestPostNoPassInconclusiveMetricMaterializationPathDiagnosticsEvidenceExecutionV0Contract:
    def test_execution_governance_doc_exists_and_gates(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{CURRENT_STATE}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`SELECTED_CLASS` | `{SELECTED_CLASS}`" in body
        assert f"`GO_TOKEN` | `{EXECUTION_GO}`" in body
        assert "`GO_TOKEN_CONSUMED` | `true`" in body
        assert f"`EXECUTION_STATUS` | `{EXECUTION_STATUS}`" in body
        assert f"`PRIMARY_CAUSE` | `{PRIMARY_CAUSE}`" in body
        assert f"`MATERIALIZATION_PATH_STATUS` | `{MATERIALIZATION_PATH_STATUS}`" in body
        assert "`MANIFEST_VERIFY_RC` | `0`" in body
        assert PARENT_EXECUTION_SUFFIX in body
        assert CLASSIFICATION_SUFFIX in body
        assert NEW_EVIDENCE_SUFFIX in body
        assert "`economic_evaluation_executed` | `false`" in body
        assert "`PROMOTION_ELIGIBLE` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert f"NEXT_CANONICAL_STEP={NEXT_CANONICAL_STEP}" in body
        for candidate in FAILED_CANDIDATES:
            assert f"`{candidate}` | `EXECUTION_FAILED_FAIL_CLOSED`" in body

    def test_scope_config_reflects_diagnostics_execution_complete(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert payload["selected_class"] == SELECTED_CLASS
        assert payload["status"] == EXECUTION_STATUS
        assert payload["diagnostics_executed"] is True
        assert payload["non_authorizing"] is True
        assert payload["economic_evaluation_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["same_binding_retry_allowed"] is False

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert (
            _field_value(
                text,
                "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0_STATUS",
            )
            == EXECUTION_STATUS
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0_GO_TOKEN",
            )
            == EXECUTION_GO
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0_GO_TOKEN_CONSUMED",
            )
            == "true"
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0_MANIFEST_VERIFY_RC",
            )
            == "0"
        )
        assert NEW_EVIDENCE_SUFFIX in _field_value(
            text,
            "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0_EVIDENCE_REF",
        )
        assert (
            _field_value(
                text,
                "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0_DIAGNOSTICS_EXECUTED",
            )
            == "true"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == RATIFICATION_GO

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == EXECUTION_STATUS
        assert _field_value(section, "VERDICT") == CURRENT_STATE
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "SELECTED_CLASS") == SELECTED_CLASS
        assert _field_value(section, "GO_TOKEN") == EXECUTION_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "PRIMARY_CAUSE") == PRIMARY_CAUSE
        assert _field_value(section, "MATERIALIZATION_PATH_STATUS") == MATERIALIZATION_PATH_STATUS
        assert _field_value(section, "economic_evaluation_executed") == "false"
        assert _field_value(section, "SAME_BINDING_RETRY_ALLOWED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == RATIFICATION_GO
        assert NEW_EVIDENCE_SUFFIX in _field_value(section, "NEW_EVIDENCE_DIR")
        for marker in FORBIDDEN_NEXT_SCOPE_MARKERS:
            assert marker not in _field_value(section, "NEXT_CANONICAL_STEP")
