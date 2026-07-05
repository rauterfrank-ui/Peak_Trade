"""Contract tests for post-PR4865–4872 progress registry closeout v0."""

from __future__ import annotations

import re

from src.governance.runbook_progress_registry_v1 import (
    RegistryEntryClass,
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = "#### POST_PR_4865_4872_PROGRESS_REGISTRY_CLOSEOUT_V0"
GLOBAL_NEXT_STEP = (
    "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_EXECUTION_V0"
)
HISTORICAL_CLOSEOUT_NEXT_STEP = "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
HISTORICAL_CLOSEOUT_CURRENT_STATE = "POST_PR_4865_4872_PROGRESS_REGISTRY_CLOSEOUT_COMPLETE_V0"
CURRENT_ADMISSIBLE_SCOPE = (
    "POST_NO_PASS_INCONCLUSIVE_METRIC_MATERIALIZATION_PATH_DIAGNOSTICS_EVIDENCE_CLASS_V0"
)
CURRENT_STATE = "POST_PR4883_NEXT_VERSIONED_RESEARCH_SCOPE_SELECTION_COMPLETE_V0"
ORIGIN_MAIN = "b0d584db9057369f5d6a930c97f8ea8ed3734aac"
MERGED_PRS = (
    ("4865", "31053b8364e444474687fa1df66cf1fc0de45662"),
    ("4866", "7224fa126dde8baabe8d74848fcc150e4b15aef9"),
    ("4867", "2f1672bee8761f8d50def3f6ef31cc803824b2e9"),
    ("4868", "f6c3f8301a98e8a9bb2ac13c63c76165a998ecaa"),
    ("4869", "e8cbb06beeb6bdd240a523ef31990672b812cdb8"),
    ("4870", "8c452cb4237325eb81ec7b5bd5c1f0fbe21bd80c"),
    ("4871", "a8f899a0814b6b51a6c266f45031876969d5cd16"),
    ("4872", "fe2c334d943da30e097645e178abb970b253fae5"),
)
VALID_ENTRY_CLASSES = frozenset(item.value for item in RegistryEntryClass)
ROW_RE = re.compile(r"^\| `([^`]+)` \| `([^`]*)` \|$")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## Post-PR-4847 Verification Binding", start)
    return text[start:end]


class TestPostPr4865To4872AuthoritativeGlobalState:
    def test_last_verified_origin_main_matches_current_main(self) -> None:
        assert authoritative_field_value("LAST_VERIFIED_ORIGIN_MAIN") == ORIGIN_MAIN
        assert authoritative_field_value("LAST_VERIFIED_PR") == "4883"
        assert authoritative_field_value("CURRENT_STATE") == CURRENT_STATE

    def test_strategic_blockers_remain_active(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == GLOBAL_NEXT_STEP
        assert (
            authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == CURRENT_ADMISSIBLE_SCOPE
        )
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("LIVE_AUTHORIZED") == "false"

    def test_fleet_terminal_fail_state_unchanged(self) -> None:
        assert (
            authoritative_field_value("FINAL_RESEARCH_FLEET_FLEET_STATUS")
            == "FINAL_RESEARCH_FLEET_ECONOMIC_EVIDENCE_COMPLETE_NO_PASS"
        )
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_NO_CANDIDATE_ECONOMIC_PASS") == (
            "true"
        )
        assert authoritative_field_value("PASS_COUNT") == "0"
        assert authoritative_field_value("FAIL_COUNT") == "3"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert authoritative_field_value("UNCHANGED_RETRY_ALLOWED") == "false"


class TestPostPr4865To4872CloseoutSection:
    def test_closeout_references_all_merged_prs(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "VERDICT") == HISTORICAL_CLOSEOUT_CURRENT_STATE
        for pr_number, merge_commit in MERGED_PRS:
            assert _field_value(section, f"PR{pr_number}_MERGE_COMMIT") == merge_commit
            assert _field_value(section, f"PR{pr_number}_TITLE")

    def test_closeout_records_no_runtime_or_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NO_ECONOMIC_EVALUATION") == "true"
        assert _field_value(section, "NO_NEW_CANDIDATE_RATIFICATION") == "true"
        assert _field_value(section, "NO_NEW_RESEARCH_SCOPE_RATIFICATION") == "true"
        assert _field_value(section, "NEW_EVALUATION_RUN") == "false"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == HISTORICAL_CLOSEOUT_NEXT_STEP
        assert _field_value(section, "STRATEGIC_BLOCKER") == HISTORICAL_CLOSEOUT_NEXT_STEP
        assert _field_value(section, "PR4872_CLOSEOUT_ROLE") == (
            "RESOLVER_REGISTRY_HYGIENE_PREREQUISITE"
        )
        assert _field_value(section, "PR4865_CLOSEOUT_ROLE") == (
            "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVIDENCE_CONVERGENCE_SUMMARY"
        )

    def test_closeout_entry_class_is_historical_snapshot(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "REGISTRY_ENTRY_CLASS") == (
            RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT.value
        )


class TestPostPr4865To4872RegistryResolverIntegrity:
    def test_global_summary_metadata_unique(self) -> None:
        summary = global_summary_section()
        rows = [ROW_RE.match(line.strip()) for line in summary.splitlines()]
        parsed = [(m.group(1), m.group(2)) for m in rows if m]
        keys = [key for key, _ in parsed]
        dupes = sorted({key for key in keys if keys.count(key) > 1})
        assert dupes == []

    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "CURRENT_STATE",
                "LAST_VERIFIED_ORIGIN_MAIN",
                "LAST_VERIFIED_PR",
                "CURRENT_ADMISSIBLE_NEXT_SCOPE",
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
                "RUNTIME_REWIRE_ADMISSIBLE",
            ),
        )
        assert ambiguous == {}

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
        assert unknown == []
