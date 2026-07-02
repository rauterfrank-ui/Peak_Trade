"""Shared helpers for runbook progress registry contract tests (Slice C)."""

from __future__ import annotations

from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    GLOBAL_SUMMARY_HEADING,
    RunbookProgressRegistryError,
    RunbookProgressRegistryV1,
    load_runbook_progress_registry_v1,
    step_section,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"

STEP_29Q_HEADING_PREFIX = "RUNBOOK_STEP_29Q — Canonical Order Intent v1"
STEP_29R_HEADING_PREFIX = "RUNBOOK_STEP_29R — Runtime Rewire"
SLICE_C_HEADING = "#### CANONICAL_CORE_RUNTIME_INTEGRATION_REMEDIATION_SLICE_C_V0"


def read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file(), f"missing canonical registry: {PROGRESS_REGISTRY}"
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def load_registry() -> RunbookProgressRegistryV1:
    return load_runbook_progress_registry_v1(PROGRESS_REGISTRY)


def authoritative_field_value(field: str) -> str:
    return load_registry().authoritative_value(field)


def section_field_value(section_heading_prefix: str, field: str) -> str:
    registry = load_registry()
    for occ in registry.all_occurrences(field):
        if section_heading_prefix in occ.section_heading:
            return occ.value
    raise RunbookProgressRegistryError(
        f"missing field {field} in section prefix {section_heading_prefix}"
    )


def step_29q_section(text: str | None = None) -> str:
    return step_section(text or read_registry(), STEP_29Q_HEADING_PREFIX)


def step_29r_section(text: str | None = None) -> str:
    return step_section(text or read_registry(), STEP_29R_HEADING_PREFIX)


def global_summary_section(text: str | None = None) -> str:
    from src.governance.runbook_progress_registry_v1 import global_summary_section as _global

    return _global(text or read_registry())
