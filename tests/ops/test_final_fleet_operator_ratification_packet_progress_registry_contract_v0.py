"""Contract tests for final fleet operator ratification packet v0."""

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
OPERATOR_RATIFICATION_PACKET = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_V0.md"
)
CLOSEOUT_SECTION_PREFIX = "#### FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_V0"
FINAL_RESEARCH_FLEET = ("trend_following", "bollinger_bands", "momentum_1h")
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
ADMISSIBLE_CLASSES_DOC = {
    "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS": "OPERATOR_RATIFICATION_REQUIRED",
    "E_NEW_VERSIONED_EVIDENCE_CLASS_WITH_FULL_CONTRACT": "OPERATOR_RATIFICATION_REQUIRED",
}
ADMISSIBLE_CLASSES_REGISTRY = {
    "D_NEW_VERSIONED_RESEARCH_SCOPE_WITH_FULL_BINDINGS": "RATIFIED",
    "E_NEW_VERSIONED_EVIDENCE_CLASS_WITH_FULL_CONTRACT": "OPERATOR_RATIFICATION_REQUIRED",
}
BLOCKED_CLASSES = {
    "A_UNMODIFIED_STEP31F_REEXECUTION": "BLOCKED",
    "B_SAME_BINDINGS_NEW_SHA_ONLY": "BLOCKED",
    "C_GOVERNANCE_REWORDING_ONLY": "BLOCKED",
    "F_EVALUATION_WITHOUT_RATIFICATION": "BLOCKED",
    "G_RUNTIME_REWIRE": "BLOCKED",
}
SAFETY_TERMS = (
    "no offline economic evaluation",
    "no runtime",
    "no scheduler",
    "no shadow",
    "no paper",
    "no testnet",
    "no adapter submission",
    "no orders",
    "no credentials",
    "no arming",
    "no canary",
    "no live action",
)


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
    assert OPERATOR_RATIFICATION_PACKET.is_file(), (
        f"missing operator ratification packet: {OPERATOR_RATIFICATION_PACKET}"
    )
    return OPERATOR_RATIFICATION_PACKET.read_text(encoding="utf-8")


class TestFinalFleetOperatorRatificationPacketDoc:
    def test_packet_exists_and_declares_non_authorizing(self) -> None:
        body = _read_packet()
        assert (
            _docs_token_marker(
                "DOCS_TOKEN_FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_FOR_NEW_VERSIONED_RESEARCH_SCOPE_OR_EVIDENCE_CLASS_V0"
            )
            in body
        )
        assert "STATUS: OPERATOR_RATIFICATION_PACKET" in body
        assert "non-authorizing" in body.lower()

    def test_verdict_and_not_ratified(self) -> None:
        body = _read_packet()
        assert "VERDICT` | `OPERATOR_RATIFICATION_REQUIRED`" in body
        assert re.search(r"\|\s*`RATIFICATION_STATUS`\s*\|\s*`NOT_RATIFIED`\s*\|", body)
        assert re.search(
            r"\|\s*`ECONOMIC_EVALUATION_AUTHORIZED`\s*\|\s*`false`\s*\|",
            body,
        )
        assert "ECONOMIC_EVALUATION_AUTHORIZED` | `true`" not in body

    def test_final_research_fleet_candidates_present(self) -> None:
        body = _read_packet()
        for candidate in FINAL_RESEARCH_FLEET:
            assert candidate in body
        assert "FINAL_RESEARCH_FLEET=trend_following,bollinger_bands,momentum_1h" in body

    def test_admissible_and_blocked_classes(self) -> None:
        body = _read_packet()
        assert "`D` | `NEW_VERSIONED_RESEARCH_SCOPE` | `OPERATOR_RATIFICATION_REQUIRED`" in body
        assert "`E` | `NEW_VERSIONED_EVIDENCE_CLASS` | `OPERATOR_RATIFICATION_REQUIRED`" in body
        for decision_class, status in ADMISSIBLE_CLASSES_DOC.items():
            assert f"| `{decision_class}` | `{status}` |" in body
        for decision_class, status in BLOCKED_CLASSES.items():
            assert f"| `{decision_class}` | `{status}` |" in body

    def test_safety_non_authorization_statement(self) -> None:
        body = _read_packet().lower()
        for term in SAFETY_TERMS:
            assert term in body, term


class TestFinalFleetOperatorRatificationPacketRegistry:
    def test_registry_points_to_prepared_packet(self) -> None:
        assert (
            authoritative_field_value("FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_STATUS")
            == "RATIFIED_CLASS_D"
        )
        assert authoritative_field_value("CURRENT_STATE") == (
            "FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_MATERIALIZED_V0"
        )
        assert (
            authoritative_field_value("FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_GO_TOKEN_CONSUMED")
            == "true"
        )

    def test_economic_evaluation_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("OFFLINE_ECONOMIC_EVALUATION_EXECUTION_ALLOWED") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"

    def test_closeout_section_records_packet_state(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "RATIFIED_CLASS_D"
        assert _field_value(section, "VERDICT") == "OPERATOR_RATIFICATION_RECORDED_CLASS_D"
        assert _field_value(section, "RATIFICATION_STATUS") == "RATIFIED_BY_OPERATOR"
        assert _field_value(section, "RATIFICATION_CLASS") == "D"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "FINAL_RESEARCH_FLEET") == (
            "trend_following,bollinger_bands,momentum_1h"
        )
        for decision_class, status in ADMISSIBLE_CLASSES_REGISTRY.items():
            assert _field_value(section, decision_class) == status
        for decision_class, status in BLOCKED_CLASSES.items():
            assert _field_value(section, decision_class) == status
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "CURRENT_STATE",
                "NEXT_CANONICAL_STEP",
                "FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_STATUS",
                "ECONOMIC_EVALUATION_AUTHORIZED",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_packet_prepared_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "CURRENT_STATE") == (
            "FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_MATERIALIZED_V0"
        )
        assert (
            _field_value(summary, "FINAL_FLEET_OPERATOR_RATIFICATION_PACKET_STATUS")
            == "RATIFIED_CLASS_D"
        )
        assert _field_value(summary, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
