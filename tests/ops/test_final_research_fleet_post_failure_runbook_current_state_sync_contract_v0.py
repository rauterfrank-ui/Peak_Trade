"""Contract tests for final research fleet post-failure runbook current state sync v0."""

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
RUNBOOK_V441 = (
    REPO_ROOT
    / "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.1_multi_future_target_model_clarification.md"
)
CLOSEOUT_SECTION_PREFIX = "#### FINAL_RESEARCH_FLEET_POST_FAILURE_RUNBOOK_CURRENT_STATE_SYNC_V0"
EVALUATION_STATUS = "COMPLETE_ROBUSTNESS_FAILED"
FLEET_VERDICT = "ROBUSTNESS_FAILED"
NEXT_CANONICAL_STEP = "NO_RUNTIME_OR_PROMOTION_ACTION"
SUPERSEDED_NEXT_STEP = "RATIFY_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE"
PR4847_MERGE_COMMIT = "7385dc0900f258840a4ce09008188bac6d576bd9"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    tail = text[start + len(CLOSEOUT_SECTION_PREFIX) :]
    next_heading = tail.find("\n---\n\n## Post-PR-4847 Verification Binding")
    return tail if next_heading == -1 else tail[:next_heading]


def _section_35(text: str) -> str:
    start = text.index("# 35. Aktuell autorisierter nächster Schritt")
    end = text.index("# 36. Testleiter", start)
    return text[start:end]


class TestFinalResearchFleetPostFailureRunbookCurrentStateSyncContract:
    def test_authoritative_registry_metadata(self) -> None:
        assert (
            authoritative_field_value("FINAL_RESEARCH_FLEET_EVALUATION_STATUS") == EVALUATION_STATUS
        )
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_FLEET_VERDICT") == FLEET_VERDICT
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_AUTHORIZED") == "false"
        assert authoritative_field_value("FURTHER_SAME_BINDING_RETRY_ALLOWED") == "false"
        assert (
            authoritative_field_value(
                "FURTHER_ECONOMIC_EVALUATION_REQUIRES_NEW_EVIDENCE_CLASS_SCOPE_AND_EXPLICIT_OPERATOR_GO"
            )
            == "true"
        )
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("SUPERSEDED_NEXT_CANONICAL_STEP") == SUPERSEDED_NEXT_STEP
        assert authoritative_field_value("PR4847_MERGE_COMMIT") == PR4847_MERGE_COMMIT

    def test_no_superseded_next_step_as_current(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") != SUPERSEDED_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") != SUPERSEDED_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") != SUPERSEDED_NEXT_STEP

    def test_registry_closeout_section(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "FINAL_RESEARCH_FLEET_EVALUATION_STATUS") == EVALUATION_STATUS
        assert _field_value(section, "FINAL_RESEARCH_FLEET_FLEET_VERDICT") == FLEET_VERDICT
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "FURTHER_SAME_BINDING_RETRY_ALLOWED") == "false"
        assert (
            _field_value(
                section,
                "FURTHER_ECONOMIC_EVALUATION_REQUIRES_NEW_EVIDENCE_CLASS_SCOPE_AND_EXPLICIT_OPERATOR_GO",
            )
            == "true"
        )
        assert _field_value(section, "SUPERSEDED_NEXT_CANONICAL_STEP") == SUPERSEDED_NEXT_STEP
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "PR4847_MERGE_COMMIT") == PR4847_MERGE_COMMIT

    def test_governance_closeout_doc(self) -> None:
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert f"`FINAL_RESEARCH_FLEET_EVALUATION_STATUS` | `{EVALUATION_STATUS}`" in body
        assert f"`FINAL_RESEARCH_FLEET_FLEET_VERDICT` | `{FLEET_VERDICT}`" in body
        assert f"`NEXT_CANONICAL_STEP` | `{NEXT_CANONICAL_STEP}`" in body
        assert f"`SUPERSEDED_NEXT_CANONICAL_STEP` | `{SUPERSEDED_NEXT_STEP}`" in body
        assert (
            "`further_economic_evaluation_requires_new_evidence_class_scope_and_explicit_operator_go` | `true`"
            in body
        )

    def test_runbook_v441_section_35_current_next_step(self) -> None:
        section = _section_35(RUNBOOK_V441.read_text(encoding="utf-8"))
        assert f"NEXT_STEP={NEXT_CANONICAL_STEP}" in section
        assert SUPERSEDED_NEXT_STEP in section
        assert "superseded/complete" in section
        assert "FURTHER_SAME_BINDING_RETRY_ALLOWED=false" in section
        assert (
            "FURTHER_ECONOMIC_EVALUATION_REQUIRES_NEW_EVIDENCE_CLASS_SCOPE_AND_EXPLICIT_OPERATOR_GO=true"
            in section
        )
        assert "MULTI_FUTURE_RUNTIME_AUTHORIZED=false" in section
        assert (
            re.search(
                rf"NEXT_STEP={re.escape(SUPERSEDED_NEXT_STEP)}",
                section,
            )
            is None
        )
