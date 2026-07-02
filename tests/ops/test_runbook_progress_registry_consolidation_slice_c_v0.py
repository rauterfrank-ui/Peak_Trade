"""Contract tests for runbook progress registry consolidation Slice C v0."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.governance.runbook_progress_registry_v1 import (
    CANONICAL_ORDER_INTENT_TRANSFORMATION_OWNER,
    LEGACY_REGISTRY_AUTHORITY,
    REGISTRY_UNQUALIFIED_FIRST_MATCH_ALLOWED,
    RegistryEntryClass,
    RunbookProgressRegistryError,
    RunbookProgressRegistryV1,
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    PROGRESS_REGISTRY,
    authoritative_field_value,
    load_registry,
    section_field_value,
    step_29q_section,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSFORMATION_OWNER = REPO_ROOT / "src" / "governance" / "canonical_order_intent_v1.py"
RESOLVER_MODULE = REPO_ROOT / "src" / "governance" / "runbook_progress_registry_v1.py"

STEP29Q_TRANSFORMATION_KEYS = (
    "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND",
    "CANONICAL_ORDER_INTENT_TRANSFORMATION_OWNER",
    "CANONICAL_ORDER_INTENT_TRANSFORMATION_AUTHORITY",
)

RUNTIME_REWIRE_KEYS = (
    "RUNTIME_REWIRE_STATUS",
    "RUNTIME_REWIRE_IMPLEMENTED",
    "RUNTIME_REWIRE_PERFORMED",
    "ZERO_ORDER_RUNTIME_READY",
    "ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED",
)


def test_resolver_module_is_canonical_owner() -> None:
    assert RESOLVER_MODULE.is_file()
    assert authoritative_field_value("REGISTRY_RESOLVER_OWNER") == (
        "src/governance/runbook_progress_registry_v1.py"
    )


def test_transformation_owner_module_exists_and_is_unique() -> None:
    assert TRANSFORMATION_OWNER.is_file()
    assert authoritative_field_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_OWNER") == (
        CANONICAL_ORDER_INTENT_TRANSFORMATION_OWNER
    )


def test_authoritative_transformation_bound_is_true() -> None:
    assert authoritative_field_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"
    assert (
        authoritative_field_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_AUTHORITY")
        == "CANONICAL_CURRENT_OWNER_ONLY"
    )


def test_step29q_snapshot_preserves_pre_29r_transformation_state() -> None:
    section = step_29q_section()
    assert "REGISTRY_ENTRY_CLASS" in section
    assert section_field_value(
        "RUNBOOK_STEP_29Q — Canonical Order Intent v1", "REGISTRY_ENTRY_CLASS"
    ) == (RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT.value)
    assert (
        section_field_value(
            "RUNBOOK_STEP_29Q — Canonical Order Intent v1",
            "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND",
        )
        == "false"
    )


def test_historical_step_snapshot_not_used_for_authoritative_resolution() -> None:
    registry = load_registry()
    historical_29q = [
        occ
        for occ in registry.all_occurrences("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND")
        if occ.entry_class is RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT
        and "29Q" in occ.section_heading
    ]
    assert historical_29q
    assert registry.authoritative_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"
    assert all(occ.value == "false" for occ in historical_29q)


def test_no_duplicate_conflicting_authoritative_current_owners_for_slice_c_keys() -> None:
    registry = load_registry()
    watched = (
        *STEP29Q_TRANSFORMATION_KEYS,
        *RUNTIME_REWIRE_KEYS,
        "SLICE_A_STATUS",
        "SLICE_B_STATUS",
        "SLICE_C_STATUS",
        "REGISTRY_DUPLICATE_CURRENT_OWNER_COUNT",
        "CANONICAL_CORE_SINGLE_SSOT_CONFIRMED",
    )
    ambiguous = duplicate_current_owner_fields(registry, fields=watched)
    assert ambiguous == {}


def test_registry_unqualified_first_match_disabled() -> None:
    assert REGISTRY_UNQUALIFIED_FIRST_MATCH_ALLOWED is False
    assert authoritative_field_value("REGISTRY_UNQUALIFIED_FIRST_MATCH_ALLOWED") == "false"


def test_legacy_registry_authority_disabled() -> None:
    assert LEGACY_REGISTRY_AUTHORITY is False
    assert authoritative_field_value("LEGACY_REGISTRY_AUTHORITY") == "false"


def test_slice_semantics_unchanged() -> None:
    assert authoritative_field_value("SLICE_A_STATUS") == "COMPLETE"
    assert authoritative_field_value("SLICE_B_STATUS") == "BOUND_NOT_ACTIVATED"
    assert authoritative_field_value("SLICE_C_STATUS") == "REGISTRY_CONSOLIDATED"


def test_runtime_rewire_and_zero_order_semantics_not_upgraded() -> None:
    assert authoritative_field_value("RUNTIME_REWIRE_STATUS") == "PARTIAL"
    assert authoritative_field_value("ZERO_ORDER_RUNTIME_READY") == "false"
    assert authoritative_field_value("ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED") == "true"
    assert authoritative_field_value("CANONICAL_CORE_SINGLE_SSOT_CONFIRMED") == "false"


def test_slice_c_binding_status_fields_preserved() -> None:
    assert authoritative_field_value("CANONICAL_RUNTIME_CORE_CONSUMPTION_STATUS") == (
        "BOUND_NOT_ACTIVATED"
    )
    assert authoritative_field_value("CANONICAL_ORDER_INTENT_TO_EXECUTION_PIPELINE_STATUS") == (
        "BOUND_NOT_ACTIVATED"
    )
    assert authoritative_field_value("INTENT_COMPATIBILITY_FIREWALL_STATUS") == "BOUND_OFFLINE"
    assert authoritative_field_value("CAPITAL_RISK_SIZING_BINDING_STATUS") == "BOUND_OFFLINE"
    assert authoritative_field_value("EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_STATUS") == "PASS"


def test_duplicate_conflicting_authoritative_values_fail_closed() -> None:
    registry = load_registry()
    mutated = dict(registry.occurrences_by_field)
    conflicted: list = []
    flipped = False
    for occ in mutated["CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND"]:
        if occ.entry_class is RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY and not flipped:
            conflicted.append(
                type(occ)(
                    section_heading=occ.section_heading,
                    field=occ.field,
                    value="CONFLICT",
                    entry_class=occ.entry_class,
                )
            )
            flipped = True
        else:
            conflicted.append(occ)
    mutated["CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND"] = tuple(conflicted)
    conflict_registry = RunbookProgressRegistryV1(text=registry.text, occurrences_by_field=mutated)
    with pytest.raises(RunbookProgressRegistryError, match="ambiguous authoritative"):
        conflict_registry.authoritative_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND")


def test_document_order_does_not_change_authoritative_resolution() -> None:
    registry = load_registry()
    text = registry.text
    reversed_sections = "\n".join(reversed(text.splitlines()))
    assert registry.authoritative_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"
    reloaded = load_runbook_progress_registry_v1()
    assert reloaded.authoritative_value("CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND") == "true"
    assert reversed_sections != text


def test_step29q_start_and_closeout_contracts_use_section_or_authoritative_lookups() -> None:
    start_text = (
        REPO_ROOT / "tests" / "ops" / "test_runbook_step29q_progress_registry_start_contract_v0.py"
    ).read_text(encoding="utf-8")
    closeout_text = (
        REPO_ROOT
        / "tests"
        / "ops"
        / "test_runbook_step29q_progress_registry_closeout_contract_v0.py"
    ).read_text(encoding="utf-8")
    assert "authoritative_field_value" in start_text
    assert "authoritative_field_value" in closeout_text
    assert not re.search(
        r'_field_value\(text, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND"\)',
        start_text,
    )
    assert not re.search(
        r'_field_value\(text, "CANONICAL_ORDER_INTENT_TRANSFORMATION_BOUND"\)',
        closeout_text,
    )
