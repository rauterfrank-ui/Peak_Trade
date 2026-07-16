"""Contract tests for STEP29M binding admissibility inventory + v4.4.12 progress sync."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_DOC = (
    REPO_ROOT / "docs/governance/STEP29M_SYSTEM_ECONOMIC_BINDING_ADMISSIBILITY_INVENTORY_V0.md"
)
INVENTORY_CFG = None  # docs-inventory-only; no config owner created
MAP = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
RUNBOOK = REPO_ROOT / "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"
SECTION = (
    "#### STEP29M_VERSIONED_SYSTEM_ECONOMIC_BINDING_ADMISSIBILITY_INVENTORY_"
    "AND_PROGRESS_REGISTRY_V4_4_12_SUPERSESSION_SYNC_V0"
)
HEAD = "84a584e7d8ee23834ed6bde09ef06dbe0414db8a"
NEXT = "SEPARATE_OPERATOR_GO_FOR_FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_EXECUTION"
CURRENT_STATE = (
    "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFIED_NOT_EXECUTED"
)


def _field(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing field {field}"
    return match.group(1)


def _section(text: str) -> str:
    start = text.index(SECTION)
    end = text.index("## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestStep29mBindingAdmissibilityInventoryAndProgressSyncV0:
    def test_inventory_artifacts_exist_and_deny_pass_admissible_binding(self) -> None:
        assert INVENTORY_DOC.is_file()
        doc = INVENTORY_DOC.read_text(encoding="utf-8")
        assert "`STEP29M_PASS_ADMISSIBLE_BINDING_PRESENT` | `false`" in doc
        assert "`ECONOMIC_EVALUATION_EXECUTED` | `false`" in doc
        assert "`STRATEGY_SELECTED` | `false`" in doc
        assert "`RUNTIME_EFFECT` | `NONE`" in doc
        assert "`AUTHORITY_EFFECT` | `NONE`" in doc
        assert "NOT_OBTAINED" in doc
        assert "```json" in doc
        payload = json.loads(doc.split("```json", 1)[1].split("```", 1)[0])
        assert payload["step29m_pass_admissible_binding_present"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["strategy_selected"] is False
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert payload["canonical_runbook_version"] == "v4.4.12"
        assert payload["map_points_to_v4_4_12"] is True
        assert payload["stale_v4_4_11_canonical_pointer_count"] == 0

    def test_map_and_runbook_point_to_v4_4_12(self) -> None:
        assert MAP.is_file()
        assert RUNBOOK.is_file()
        map_text = MAP.read_text(encoding="utf-8")
        assert "CANONICAL_VOLLAUTONOMIE_RUNBOOK_VERSION=v4.4.12" in map_text
        assert (
            "CANONICAL_VOLLAUTONOMIE_RUNBOOK_PATH="
            "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md" in map_text
        )
        assert "CANONICAL_VOLLAUTONOMIE_RUNBOOK_VERSION=v4.4.11" not in map_text

    def test_progress_registry_authoritative_sync(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == HEAD
        assert authoritative_field_value("LAST_VERIFIED_PR") == "5240"
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
        assert authoritative_field_value("MAP_POINTS_TO_V4_4_12") == "true"
        assert authoritative_field_value("CANONICAL_RUNBOOK_VERSION") == "v4.4.12"
        assert authoritative_field_value("STALE_V4_4_11_CANONICAL_POINTER_COUNT") == "0"
        assert authoritative_field_value("FULL_CANONICAL_CHAIN_WIRED") == "true"
        assert authoritative_field_value("BACKTEST_RUNTIME_DECISION_PARITY_PASS") == "true"
        assert authoritative_field_value("STEP_29L_2_STATUS") == "COMPLETE_MANIFEST_VERIFIED"
        assert (
            authoritative_field_value("STEP_29M_STATUS")
            == "BINDING_RATIFIED_NOT_EXECUTED_AWAITING_ECONOMIC_BASELINE_GO"
        )
        assert authoritative_field_value("STEP29M_PASS_ADMISSIBLE_BINDING_PRESENT") == "false"
        assert (
            authoritative_field_value("STEP_29N_STATUS")
            == "COMPLETE_AND_PRODUCTIVELY_BOUND_FAIL_CLOSED_BLOCKED"
        )
        assert authoritative_field_value("STEP_29R_STATUS") == "BLOCKED_BY_PRIOR_GATE"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert authoritative_field_value("STRATEGY_SELECTED") == "false"
        assert authoritative_field_value("RUNTIME_EFFECT") == "NONE"
        assert authoritative_field_value("AUTHORITY_EFFECT") == "NONE"
        assert authoritative_field_value("READ_ONLY_ASSESSMENT_COMPLETED") == "true"
        assert (
            authoritative_field_value("READ_ONLY_ASSESSMENT_EXTERNAL_EVIDENCE_PERSISTED") == "false"
        )
        assert (
            authoritative_field_value(
                "READ_ONLY_ASSESSMENT_EXTERNAL_EVIDENCE_BLOCKED_BY_CURSOR_POLICY"
            )
            == "true"
        )
        assert (
            authoritative_field_value("READ_ONLY_ASSESSMENT_MANIFEST_VERIFY_STATUS")
            == "NOT_OBTAINED"
        )
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"

    def test_closeout_section_present(self) -> None:
        section = _section(read_registry())
        assert _field(section, "GO_TOKEN").startswith("GO_STEP29M_VERSIONED_SYSTEM_ECONOMIC")
        assert _field(section, "STEP29M_PASS_ADMISSIBLE_BINDING_PRESENT") == "false"
        assert _field(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field(section, "STRATEGY_SELECTED") == "false"
        assert _field(section, "RUNTIME_EFFECT") == "NONE"
        assert _field(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field(section, "READ_ONLY_ASSESSMENT_MANIFEST_VERIFY_STATUS") == "NOT_OBTAINED"
