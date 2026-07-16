"""Progress registry contract for FULL_CANONICAL_SYSTEM evidence generation v1 offline execution."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION_V0"
)
RATIFICATION_SECTION_PREFIX = (
    "#### FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFICATION_V0"
)
GO_TOKEN = "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION"
NEXT_STEP = (
    "NO_UNCHANGED_RETRY_REQUIRES_NEW_DISTINCT_FULL_CANONICAL_SYSTEM_BINDING_OR_EVIDENCE_CLASS"
)
EVIDENCE_CLASS = "BOLLINGER_BANDS_V2_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_V1"
BINDING_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
BINDING_DIGEST = "b0b51de225a7e282263c1b00091ccb457612f74df0e817d8dd03efc7af837320"
CURRENT_STATE = (
    "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_BASELINE_COMPLETE_FAIL"
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _section(text: str, prefix: str, end_marker: str) -> str:
    start = text.index(prefix)
    end = text.index(end_marker, start)
    return text[start:end]


class TestFullCanonicalSystemEconomicEvidenceGenerationV1OfflineExecutionProgressRegistry:
    def test_authoritative_executed_fail_state(self) -> None:
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert (
            authoritative_field_value("NEW_ECONOMIC_EVIDENCE_GENERATION_STATUS")
            == "OFFLINE_BASELINE_EXECUTED_TERMINAL_FAIL"
        )
        assert authoritative_field_value("SELECTED_EVIDENCE_CLASS") == EVIDENCE_CLASS
        assert authoritative_field_value("SELECTED_BINDING_ID") == BINDING_ID
        assert authoritative_field_value("SELECTED_BINDING_DIGEST") == BINDING_DIGEST
        assert authoritative_field_value("ECONOMIC_EVALUATION_EXECUTED") == "true"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_ECONOMIC_STATUS"
            )
            == "FAIL"
        )
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_PRIMARY_FAILURE_REASON"
            )
            == "ZERO_TRADE_DEGENERATION"
        )
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_TRADE_COUNT"
            )
            == "0"
        )
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_ROBUSTNESS_EXECUTED"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_UNCHANGED_RETRY_ALLOWED"
            )
            == "false"
        )

    def test_next_step_blocks_unchanged_retry(self) -> None:
        assert authoritative_field_value("NEXT_STEP") == NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_STEP

    def test_runtime_and_authority_remain_none(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_EFFECT") == "NONE"
        assert authoritative_field_value("AUTHORITY_EFFECT") == "NONE"
        assert authoritative_field_value("STEP29M_PASS_ADMISSIBLE_BINDING_PRESENT") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION_GO_TOKEN"
            )
            == GO_TOKEN
        )
        assert (
            authoritative_field_value(
                "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION_GO_TOKEN_CONSUMED"
            )
            == "true"
        )

    def test_offline_execution_section_fields(self) -> None:
        section = _section(
            read_registry(),
            CLOSEOUT_SECTION_PREFIX,
            "\n---\n\n## PR #4629 Evidence-Drift",
        )
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "SELECTED_EVIDENCE_CLASS") == EVIDENCE_CLASS
        assert _field_value(section, "SELECTED_BINDING_ID") == BINDING_ID
        assert _field_value(section, "SELECTED_BINDING_DIGEST") == BINDING_DIGEST
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "true"
        assert _field_value(section, "ECONOMIC_STATUS") == "FAIL"
        assert _field_value(section, "TRADE_COUNT") == "0"
        assert _field_value(section, "ROBUSTNESS_EXECUTED") == "false"
        assert _field_value(section, "ROBUSTNESS_NOT_EXECUTED_REASON") == (
            "NOT_EXECUTED_BASELINE_NEGATIVE"
        )
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "MANIFEST_VERIFY_RC") == "0"
        assert _field_value(section, "NEXT_STEP") == NEXT_STEP

    def test_ratification_section_remains_historical(self) -> None:
        section = _section(
            read_registry(),
            RATIFICATION_SECTION_PREFIX,
            "\n#### FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_OFFLINE_EXECUTION_V0",
        )
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "STATUS") == "BINDING_RATIFIED_NOT_EXECUTED"
