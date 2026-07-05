"""Contract tests for bounded post no-pass futures research scope definition v0."""

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
    REPO_ROOT / "config/research/bounded_post_no_pass_futures_research_scope_definition_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0"
OPERATOR_GO = "GO_NEW_RATIFIED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
EVIDENCE_CLASS_ID = "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0"
SCOPE_ID = "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0"
SCOPE_STATUS = "SCOPE_EXECUTED_COMPLETE_ROBUSTNESS_FAILED"
HISTORICAL_CLOSEOUT_SCOPE_STATUS = "SCOPE_DEFINED_NOT_EXECUTED"
PROCESS_CLASSIFICATION = "NEW_RATIFIED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_SCOPE_DEFINITION_ONLY_V0"
NEXT_REQUIRED_GO = "GO_BOUNDED_POST_NO_PASS_FUTURES_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_BOUNDED_POST_NO_PASS_FUTURES_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
BASELINE_HEAD = "ae799675366a2266b4b2b6dacc1bd4292b9c405c"
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
    "Scope definition ≠ Evaluation authorization",
    "Keine Evaluation in diesem Scope",
    "NO_NEW_CANDIDATE_HOLD",
    "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_COMPLETE_NO_PASS",
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
    next_heading = tail.find("\n---\n\n## ")
    return tail if next_heading == -1 else tail[:next_heading]


class TestBoundedPostNoPassFuturesResearchScopeDefinitionV0Contract:
    def test_scope_config_exists_and_governance_gates(self) -> None:
        assert SCOPE_CONFIG.is_file()
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["status"] == SCOPE_STATUS
        assert payload["scope_id"] == SCOPE_ID
        assert payload["process_classification"] == PROCESS_CLASSIFICATION
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["economic_evaluation_effect"] == "NONE"
        assert payload["trading_effect"] == "NONE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["evaluation_execution_authorized"] is False
        assert payload["candidate_promotion_authorized"] is False
        assert payload["promotion_authorized"] is False
        assert payload["promotion_eligible"] is False
        assert payload["runtime_rewire_admissible"] is False
        assert payload["runtime_rewire_authorized"] is False
        assert payload["runtime_authority"] is False
        assert payload["no_evaluation_authority"] is True
        assert payload["no_runtime_authority"] is True
        assert payload["no_promotion_authority"] is True
        assert payload["required_future_operator_go"] is True
        assert payload["required_next_go_for_execution"] == NEXT_REQUIRED_GO
        assert payload["futures_only"] is True
        assert payload["spot_allowed"] is False
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["baseline_head"] == BASELINE_HEAD
        assert payload["baseline_pr"] == "4873"
        assert payload["operator_go"] == OPERATOR_GO

    def test_scope_config_forbids_runtime_and_evaluation_execution(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        forbidden = payload["forbidden_actions"]
        for action in (
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "CANDIDATE_PROMOTION",
            "RUNTIME_REWIRE",
        ):
            assert action in forbidden, f"missing forbidden action: {action}"
        for action in FORBIDDEN_RUNTIME_ACTIONS:
            assert action in forbidden, f"missing forbidden runtime action: {action}"

    def test_governance_doc_has_docs_token_and_boundary_phrases(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{HISTORICAL_CLOSEOUT_SCOPE_STATUS}`" in body
        assert f"`EVIDENCE_CLASS_ID` | `{EVIDENCE_CLASS_ID}`" in body
        assert f"`OPERATOR_GO` | `{OPERATOR_GO}`" in body
        assert "`ECONOMIC_EVALUATION_AUTHORIZED` | `false`" in body
        assert "`RUNTIME_REWIRE_ADMISSIBLE` | `false`" in body
        assert "`authority_effect` | `NONE`" in body
        assert f"`REQUIRED_NEXT_GO_FOR_EXECUTION` | `{NEXT_REQUIRED_GO}`" in body
        for phrase in BOUNDARY_PHRASES:
            assert phrase in body, f"missing boundary phrase: {phrase}"

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert (
            _field_value(text, "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0_STATUS")
            == SCOPE_STATUS
        )
        assert (
            _field_value(
                text, "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0_CONFIG_REF"
            )
            == "config/research/bounded_post_no_pass_futures_research_scope_definition_v0.json"
        )
        assert (
            _field_value(
                text,
                "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0_EVIDENCE_CLASS_ID",
            )
            == EVIDENCE_CLASS_ID
        )
        assert (
            _field_value(text, "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0_GO_TOKEN")
            == OPERATOR_GO
        )
        assert (
            _field_value(
                text,
                "BOUNDED_POST_NO_PASS_FUTURES_RESEARCH_SCOPE_DEFINITION_V0_REQUIRED_NEXT_GO_FOR_EXECUTION",
            )
            == NEXT_REQUIRED_GO
        )
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == (
            "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
        )
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == (
            "GO_POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
        )
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == (
            "POST_NO_PASS_ROBUSTNESS_FAILURE_DIAGNOSTICS_EVIDENCE_EXECUTION_REQUIRES_SEPARATE_OPERATOR_GO_V0"
        )
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == HISTORICAL_CLOSEOUT_SCOPE_STATUS
        assert _field_value(section, "VERDICT") == HISTORICAL_CLOSEOUT_SCOPE_STATUS
        assert _field_value(section, "PROCESS_CLASSIFICATION") == PROCESS_CLASSIFICATION
        assert _field_value(section, "EVIDENCE_CLASS_ID") == EVIDENCE_CLASS_ID
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "EVALUATION_EXECUTION_AUTHORIZED") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "REQUIRED_FUTURE_OPERATOR_GO") == "true"
        assert _field_value(section, "REQUIRED_NEXT_GO_FOR_EXECUTION") == NEXT_REQUIRED_GO
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
