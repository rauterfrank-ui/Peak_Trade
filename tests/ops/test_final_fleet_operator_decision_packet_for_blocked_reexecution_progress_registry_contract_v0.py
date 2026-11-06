"""Contract tests for final fleet operator decision packet v0."""

from __future__ import annotations

import re
from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATOR_DECISION_PACKET = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "FINAL_FLEET_OPERATOR_DECISION_PACKET_FOR_BLOCKED_REEXECUTION_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### FINAL_FLEET_OPERATOR_DECISION_PACKET_FOR_BLOCKED_REEXECUTION_V0"
CURRENT_HEAD = "0588d0be4e859152bf9fccd6134c1f57e2838054"
NEXT_CANONICAL_STEP = "OPERATOR_RATIFICATION_REQUIRED_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_NEW_VERSIONED_EVIDENCE_CLASS_V0"
DECISION_MATRIX = {
    "A_UNMODIFIED_STEP31F_REEXECUTION": "BLOCKED",
    "B_SHA_REBIND_ONLY": "BLOCKED",
    "C_GO_TOKEN_ALIAS_ONLY": "BLOCKED",
    "D_NEW_VERSIONED_RESEARCH_SCOPE": "OPERATOR_RATIFICATION_REQUIRED",
    "E_NEW_VERSIONED_EVIDENCE_CLASS": "OPERATOR_RATIFICATION_REQUIRED",
    "F_RUNTIME_REWIRE": "BLOCKED",
}


def _docs_token_marker(token_name: str) -> str:
    return "docs_" + "token: " + token_name


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def _read_packet() -> str:
    assert OPERATOR_DECISION_PACKET.is_file(), (
        f"missing operator decision packet: {OPERATOR_DECISION_PACKET}"
    )
    return OPERATOR_DECISION_PACKET.read_text(encoding="utf-8")


class TestFinalFleetOperatorDecisionPacketDoc:
    def test_packet_exists_and_declares_non_authorizing(self) -> None:
        body = _read_packet()
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_FINAL_FLEET_OPERATOR_DECISION_PACKET_FOR_BLOCKED_REEXECUTION_V0"
            )
            in body
        )
        assert "STATUS: OPERATOR_DECISION_PACKET" in body
        assert "non-authorizing" in body.lower()

    def test_verdict_and_blocking_flags(self) -> None:
        body = _read_packet()
        assert (
            "VERDICT` | `OPERATOR_DECISION_PACKET_READY_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0"
            in body
        )
        assert re.search(
            r"\|\s*`CURRENT_HEAD_BINDING`\s*\|\s*`0588d0be4e859152bf9fccd6134c1f57e2838054`\s*\|",
            body,
        )
        assert re.search(
            r"\|\s*`UNMODIFIED_BINDING_REEXECUTION_BLOCKED`\s*\|\s*`true`\s*\|",
            body,
        )
        assert re.search(r"\|\s*`OFFLINE_EVALUATION_ALLOWED`\s*\|\s*`false`\s*\|", body)
        assert re.search(
            r"\|\s*`NEGATIVE_EVIDENCE_CAN_NOT_BE_RECLASSIFIED_BY_GOVERNANCE`\s*\|\s*`true`\s*\|",
            body,
        )
        assert re.search(
            r"\|\s*`SHA_REBIND_ALONE_IS_NOT_NEW_EVIDENCE_CLASS`\s*\|\s*`true`\s*\|",
            body,
        )
        assert re.search(
            r"\|\s*`GO_TOKEN_ALIAS_ALONE_IS_NOT_NEW_EVIDENCE_CLASS`\s*\|\s*`true`\s*\|",
            body,
        )

    def test_decision_matrix_classes(self) -> None:
        body = _read_packet()
        for decision_class, status in DECISION_MATRIX.items():
            assert decision_class in body
            assert f"| `{decision_class}` | `{status}` |" in body


class TestFinalFleetOperatorDecisionPacketRegistry:
    def test_authoritative_next_step_and_packet_ref(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("FINAL_FLEET_OPERATOR_DECISION_PACKET_STATUS") == "READY"
        assert authoritative_field_value("UNMODIFIED_BINDING_REEXECUTION_BLOCKED") == "true"
        assert authoritative_field_value("OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ALLOWED") == "false"

    def test_execution_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"

    def test_closeout_section_records_decision_matrix(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "READY"
        assert (
            _field_value(section, "VERDICT")
            == "OPERATOR_DECISION_PACKET_READY_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0"
        )
        assert _field_value(section, "CURRENT_HEAD_BINDING") == CURRENT_HEAD
        assert _field_value(section, "OFFLINE_EVALUATION_ALLOWED") == "false"
        for decision_class, status in DECISION_MATRIX.items():
            assert _field_value(section, decision_class) == status
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "GLOBAL_RUNBOOK_NEXT_STEP",
                "FINAL_FLEET_OPERATOR_DECISION_PACKET_STATUS",
                "UNMODIFIED_BINDING_REEXECUTION_BLOCKED",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_decision_packet_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(summary, "FINAL_FLEET_OPERATOR_DECISION_PACKET_STATUS") == "READY"
