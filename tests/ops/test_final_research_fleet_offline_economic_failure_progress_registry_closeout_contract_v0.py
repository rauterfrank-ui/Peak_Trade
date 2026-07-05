"""Contract tests for final research fleet offline economic failure progress registry closeout v0."""

from __future__ import annotations

import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/governance/FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_FAILURE_CLOSEOUT_V0.md"
)
CLOSEOUT_SECTION_PREFIX = (
    "#### FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_FAILURE_PROGRESS_REGISTRY_CLOSEOUT_V0"
)
EVALUATION_STATUS = "COMPLETE_ROBUSTNESS_FAILED"
FLEET_VERDICT = "ROBUSTNESS_FAILED"
NEXT_CANONICAL_STEP = "NO_RUNTIME_OR_PROMOTION_ACTION"
MERGE_COMMIT = "9b377727cfcb33b03fa545aaf6b48c20c31451e7"
SOURCE_EVAL_BUNDLE = (
    "bounded_new_evidence_class_offline_economic_evaluation_execution_v0_20260705T003528Z"
)
PR4846_CLOSEOUT_BUNDLE = (
    "bounded_new_evidence_class_offline_economic_evaluation_pr_squash_merge_closeout_v0_"
    "20260705T004825Z"
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
    next_heading = tail.find("\n#### ")
    return tail if next_heading == -1 else tail[:next_heading]


class TestFinalResearchFleetOfflineEconomicFailureProgressRegistryCloseoutContract:
    def test_governance_doc_has_docs_token_and_verdict(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_FAILURE_CLOSEOUT_V0"
            )
            in body
        )
        assert f"`VERDICT` | `{EVALUATION_STATUS}`" in body
        assert f"`FINAL_RESEARCH_FLEET_FLEET_VERDICT` | `{FLEET_VERDICT}`" in body
        assert MERGE_COMMIT in body
        assert SOURCE_EVAL_BUNDLE in body

    def test_registry_metadata_fields(self) -> None:
        text = read_registry()
        assert _field_value(text, "CURRENT_STATE") == (
            "FINAL_RESEARCH_FLEET_NEW_EVIDENCE_CLASS_OFFLINE_EVALUATION_COMPLETE_ROBUSTNESS_FAILED_V0"
        )
        assert _field_value(text, "FINAL_RESEARCH_FLEET_EVALUATION_STATUS") == EVALUATION_STATUS
        assert _field_value(text, "FINAL_RESEARCH_FLEET_FLEET_VERDICT") == FLEET_VERDICT
        assert _field_value(text, "FINAL_RESEARCH_FLEET_OFFLINE_EVALUATION_COMPLETE") == "true"
        assert _field_value(text, "ECONOMIC_EVALUATION_EXECUTED") == "true"
        assert _field_value(text, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(text, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(text, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(text, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(text, "PR4846_MERGE_COMMIT") == MERGE_COMMIT
        assert SOURCE_EVAL_BUNDLE in _field_value(
            text, "NEW_EVIDENCE_CLASS_OFFLINE_EVALUATION_EVIDENCE_REF"
        )
        assert PR4846_CLOSEOUT_BUNDLE in _field_value(text, "PR4846_CLOSEOUT_EVIDENCE_REF")
        assert authoritative_field_value("RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert authoritative_field_value("RUNTIME_AUTHORITY") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == (
            "consumed_for_completed_offline_scope_only"
        )

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == EVALUATION_STATUS
        assert _field_value(section, "FINAL_RESEARCH_FLEET_EVALUATION_STATUS") == EVALUATION_STATUS
        assert _field_value(section, "FINAL_RESEARCH_FLEET_FLEET_VERDICT") == FLEET_VERDICT
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_AUTHORITY") == "false"
        assert _field_value(section, "EVALUATION_AUTHORIZED") == (
            "consumed_for_completed_offline_scope_only"
        )
        assert _field_value(section, "SHADOW_AUTHORIZED") == "false"
        assert _field_value(section, "PAPER_AUTHORIZED") == "false"
        assert _field_value(section, "TESTNET_AUTHORIZED") == "false"
        assert _field_value(section, "ORDERS_ALLOWED") == "false"
        assert _field_value(section, "SCHEDULER_RUNTIME_ALLOWED") == "false"
        assert _field_value(section, "LIVE_AUTHORIZED") == "false"
        assert _field_value(section, "RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert _field_value(section, "RE_EVALUATION_SAME_BINDING_ALLOWED") == "false"
        assert _field_value(section, "ECONOMICALLY_VIABLE_CANDIDATE_COUNT") == "0"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "PROGRESS_REGISTRY_CLOSEOUT_PERFORMED") == "true"

    def test_no_economically_viable_candidate(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "trend_following_v1_verdict") == FLEET_VERDICT
        assert _field_value(section, "bollinger_bands_v1_verdict") == FLEET_VERDICT
        assert _field_value(section, "momentum_1h_v1_verdict") == FLEET_VERDICT
        assert _field_value(section, "ECONOMICALLY_VIABLE_CANDIDATE_COUNT") == "0"
