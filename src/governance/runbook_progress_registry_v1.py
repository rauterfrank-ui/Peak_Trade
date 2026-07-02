"""Canonical runbook progress registry resolver v1 (Slice C).

Offline, deterministic resolution for ``PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md``.
Authoritative current status is resolved only from explicitly classified current
owner sections. Historical step snapshots and legacy aliases never produce global
authority.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping, Sequence

PACKAGE_MARKER = "RUNBOOK_PROGRESS_REGISTRY_RESOLVER_V1=true"
CANONICAL_RUNBOOK_PROGRESS_REGISTRY_DOC = (
    "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
)
RUNBOOK_PROGRESS_REGISTRY_RESOLVER_OWNER = "src.governance.runbook_progress_registry_v1"

CANONICAL_ORDER_INTENT_TRANSFORMATION_OWNER = "src/governance/canonical_order_intent_v1.py"

REGISTRY_UNQUALIFIED_FIRST_MATCH_ALLOWED = False
LEGACY_REGISTRY_AUTHORITY = False

FIELD_TABLE_ROW_RE = re.compile(r"\| `([^`]+)` \| `([^`]*)` \|")
SECTION_HEADING_RE = re.compile(r"^#{2,4} .+$", re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"\s<!--.*?-->", re.DOTALL)

GLOBAL_SUMMARY_HEADING = "## Registry-Metadaten"
SLICE_D_HEADING = "#### CANONICAL_CORE_RUNTIME_INTEGRATION_REMEDIATION_SLICE_D_V0"
SLICE_C_HEADING = "#### CANONICAL_CORE_RUNTIME_INTEGRATION_REMEDIATION_SLICE_C_V0"
SLICE_B_HEADING = "#### CANONICAL_CORE_RUNTIME_INTEGRATION_REMEDIATION_SLICE_B_V0"
STATUS_VALUES_HEADING = "## Statuswerte"


class RegistryEntryClass(str, Enum):
    CANONICAL_CURRENT_OWNER_ONLY = "CANONICAL_CURRENT_OWNER_ONLY"
    HISTORICAL_STEP_SNAPSHOT = "HISTORICAL_STEP_SNAPSHOT"
    HISTORICAL_REMEDIATION_SNAPSHOT = "HISTORICAL_REMEDIATION_SNAPSHOT"
    LEGACY_NON_AUTHORITATIVE = "LEGACY_NON_AUTHORITATIVE"


class RunbookProgressRegistryError(ValueError):
    """Fail-closed registry resolution error."""


@dataclass(frozen=True)
class RegistryFieldOccurrence:
    section_heading: str
    field: str
    value: str
    entry_class: RegistryEntryClass


@dataclass(frozen=True)
class RunbookProgressRegistryV1:
    text: str
    occurrences_by_field: Mapping[str, tuple[RegistryFieldOccurrence, ...]]

    def authoritative_value(self, field: str) -> str:
        current = self.current_authoritative_occurrences(field)
        if not current:
            raise RunbookProgressRegistryError(
                f"missing authoritative current owner for field: {field}"
            )
        values = {occ.value for occ in current}
        if len(values) != 1:
            raise RunbookProgressRegistryError(
                f"ambiguous authoritative current owner for {field}: {sorted(values)}"
            )
        return next(iter(values))

    def current_authoritative_occurrences(self, field: str) -> tuple[RegistryFieldOccurrence, ...]:
        return tuple(
            occ
            for occ in self.occurrences_by_field.get(field, ())
            if occ.entry_class is RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY
        )

    def section_value(self, section_heading: str, field: str) -> str:
        for occ in self.occurrences_by_field.get(field, ()):
            if occ.section_heading == section_heading:
                return occ.value
        raise RunbookProgressRegistryError(f"missing field {field} in section {section_heading}")

    def all_occurrences(self, field: str) -> tuple[RegistryFieldOccurrence, ...]:
        return self.occurrences_by_field.get(field, ())


def default_registry_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[2]
    return root / CANONICAL_RUNBOOK_PROGRESS_REGISTRY_DOC


def _strip_comments(text: str) -> str:
    return HTML_COMMENT_RE.sub("", text)


def _section_entry_class(section_heading: str, fields: Mapping[str, str]) -> RegistryEntryClass:
    explicit = fields.get("REGISTRY_ENTRY_CLASS")
    if explicit:
        try:
            return RegistryEntryClass(explicit)
        except ValueError as exc:
            raise RunbookProgressRegistryError(
                f"unknown REGISTRY_ENTRY_CLASS={explicit!r} in section {section_heading}"
            ) from exc

    if section_heading == GLOBAL_SUMMARY_HEADING:
        return RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY
    if section_heading == SLICE_D_HEADING:
        return RegistryEntryClass.CANONICAL_CURRENT_OWNER_ONLY
    if section_heading == SLICE_C_HEADING:
        return RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT
    if section_heading == SLICE_B_HEADING:
        return RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT
    if section_heading.startswith("#### RUNBOOK_STEP_"):
        return RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT
    if section_heading == "#### CANONICAL_CORE_RUNTIME_INTEGRATION_REMEDIATION_SLICE_A_V0":
        return RegistryEntryClass.HISTORICAL_REMEDIATION_SNAPSHOT
    if "legacy heading" in section_heading.lower():
        return RegistryEntryClass.LEGACY_NON_AUTHORITATIVE
    return RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT


def _iter_sections(text: str) -> Iterable[tuple[str, str]]:
    normalized = _strip_comments(text)
    heading_matches = list(SECTION_HEADING_RE.finditer(normalized))
    for index, match in enumerate(heading_matches):
        heading = match.group(0).strip()
        start = match.end()
        end = (
            heading_matches[index + 1].start()
            if index + 1 < len(heading_matches)
            else len(normalized)
        )
        yield heading, normalized[start:end]


def _parse_section_fields(section_text: str) -> dict[str, str]:
    return {field: value for field, value in FIELD_TABLE_ROW_RE.findall(section_text)}


def load_runbook_progress_registry_v1(
    path: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> RunbookProgressRegistryV1:
    registry_path = path or default_registry_path(repo_root)
    text = registry_path.read_text(encoding="utf-8")
    occurrences: dict[str, list[RegistryFieldOccurrence]] = {}

    for heading, section_text in _iter_sections(text):
        fields = _parse_section_fields(section_text)
        if not fields:
            continue
        entry_class = _section_entry_class(heading, fields)
        for field, value in fields.items():
            occurrences.setdefault(field, []).append(
                RegistryFieldOccurrence(
                    section_heading=heading,
                    field=field,
                    value=value,
                    entry_class=entry_class,
                )
            )

    frozen = {field: tuple(values) for field, values in occurrences.items()}
    return RunbookProgressRegistryV1(text=text, occurrences_by_field=frozen)


def resolve_authoritative_field(
    registry: RunbookProgressRegistryV1 | str | Path,
    field: str,
    *,
    repo_root: Path | None = None,
) -> str:
    parsed = (
        registry
        if isinstance(registry, RunbookProgressRegistryV1)
        else load_runbook_progress_registry_v1(registry, repo_root=repo_root)
    )
    return parsed.authoritative_value(field)


def resolve_step_section_field(
    registry: RunbookProgressRegistryV1 | str | Path,
    section_heading: str,
    field: str,
    *,
    repo_root: Path | None = None,
) -> str:
    parsed = (
        registry
        if isinstance(registry, RunbookProgressRegistryV1)
        else load_runbook_progress_registry_v1(registry, repo_root=repo_root)
    )
    return parsed.section_value(section_heading, field)


def duplicate_current_owner_fields(
    registry: RunbookProgressRegistryV1,
    *,
    fields: Sequence[str] | None = None,
) -> dict[str, list[str]]:
    ambiguous: dict[str, list[str]] = {}
    keys = fields or tuple(registry.occurrences_by_field.keys())
    for field in keys:
        current = registry.current_authoritative_occurrences(field)
        values = sorted({occ.value for occ in current})
        if len(values) > 1:
            ambiguous[field] = values
    return ambiguous


def assert_unique_authoritative_owner(registry: RunbookProgressRegistryV1, field: str) -> None:
    ambiguous = duplicate_current_owner_fields(registry, fields=(field,))
    if ambiguous:
        values = ambiguous[field]
        raise RunbookProgressRegistryError(
            f"duplicate authoritative current owner for {field}: {values}"
        )


def global_summary_section(text: str) -> str:
    start = text.index(GLOBAL_SUMMARY_HEADING)
    end = text.index(f"\n{STATUS_VALUES_HEADING}", start)
    return _strip_comments(text[start:end])


def step_section(text: str, heading_prefix: str) -> str:
    pattern = re.compile(rf"^#### {re.escape(heading_prefix)}[^\n]*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        raise RunbookProgressRegistryError(f"missing step section prefix: {heading_prefix}")
    start = match.start()
    following = list(SECTION_HEADING_RE.finditer(text, match.end()))
    end = following[0].start() if following else len(text)
    return _strip_comments(text[start:end])
