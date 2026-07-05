"""Contract tests for runbook progress registry resolver hygiene v0.

Guarantees the canonical registry document remains machine-readable and that
authoritative Registry-Metadaten fields are unique and fail-closed safe.
"""

from __future__ import annotations

import re

from src.governance.runbook_progress_registry_v1 import (
    RegistryEntryClass,
    duplicate_current_owner_fields,
    global_summary_section,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]*)` \|$")
VALID_ENTRY_CLASSES = frozenset(item.value for item in RegistryEntryClass)
AUTHORITATIVE_NEXT_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
CURRENT_ADMISSIBLE_SCOPE = "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
CURRENT_STATE = "POST_NO_PASS_ROBUSTNESS_FAILURE_NEXT_RESEARCH_SCOPE_DEFINITION_COMPLETE_V0"
ORIGIN_MAIN = "77de907bbf7808ed4cbf8604c7994f7078932b85"


def _metadata_field_rows(text: str) -> list[tuple[str, str]]:
    summary = global_summary_section(text)
    rows: list[tuple[str, str]] = []
    for line in summary.splitlines():
        match = ROW_RE.match(line.strip())
        if match:
            rows.append((match.group(1), match.group(2)))
    return rows


class TestRunbookProgressRegistryResolverHygieneV0:
    def test_registry_entry_classes_are_resolver_known(self) -> None:
        text = read_registry()
        unknown: list[str] = []
        for line in text.splitlines():
            if "| `REGISTRY_ENTRY_CLASS` |" not in line:
                continue
            match = ROW_RE.match(line.strip())
            assert match, f"malformed REGISTRY_ENTRY_CLASS row: {line}"
            value = match.group(2)
            if value not in VALID_ENTRY_CLASSES:
                unknown.append(value)
        assert unknown == [], f"unknown REGISTRY_ENTRY_CLASS values: {sorted(set(unknown))}"

    def test_authoritative_metadata_has_no_duplicate_keys(self) -> None:
        rows = _metadata_field_rows(read_registry())
        keys = [key for key, _ in rows]
        dupes = sorted({key for key in keys if keys.count(key) > 1})
        assert dupes == [], f"duplicate authoritative metadata keys: {dupes}"

    def test_new_candidates_ratified_is_unique_and_false(self) -> None:
        rows = _metadata_field_rows(read_registry())
        values = [value for key, value in rows if key == "NEW_CANDIDATES_RATIFIED"]
        assert values == ["false"]
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"

    def test_next_canonical_step_is_unique_and_post_fleet_hold(self) -> None:
        rows = _metadata_field_rows(read_registry())
        values = [value for key, value in rows if key == "NEXT_CANONICAL_STEP"]
        assert values == [AUTHORITATIVE_NEXT_STEP]
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == AUTHORITATIVE_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == AUTHORITATIVE_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == AUTHORITATIVE_NEXT_STEP

    def test_safety_blockers_remain_active(self) -> None:
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        )
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"

    def test_post_pr4865_4872_closeout_metadata(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == ORIGIN_MAIN
        assert authoritative_field_value("LAST_VERIFIED_PR") == "4878"
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE
        assert (
            authoritative_field_value("POST_PR_4865_4872_PROGRESS_REGISTRY_CLOSEOUT_STATUS")
            == "COMPLETE"
        )
        assert (
            authoritative_field_value(
                "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_AND_REGISTRY_UPDATE_V0_STATUS"
            )
            == "POST_NO_PASS_ECONOMIC_EVIDENCE_CLOSEOUT_COMPLETE"
        )

    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "NEXT_CANONICAL_ACTION",
                "GLOBAL_RUNBOOK_NEXT_STEP",
                "NEW_CANDIDATES_RATIFIED",
                "NO_NEW_CANDIDATE_HOLD",
                "FINAL_RESEARCH_FLEET_BINDING_READY",
                "ECONOMIC_EVALUATION_AUTHORIZED",
            ),
        )
        assert ambiguous == {}

    def test_registry_resolver_loads_without_error(self) -> None:
        registry = load_runbook_progress_registry_v1()
        assert registry.authoritative_value("FINAL_RESEARCH_FLEET") == (
            "trend_following,bollinger_bands,momentum_1h"
        )
