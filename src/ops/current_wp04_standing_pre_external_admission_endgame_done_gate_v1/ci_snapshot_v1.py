"""Admission-time CI context snapshot (structural; GREEN verified on GitHub)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CiAdmissionSnapshotV1:
    schema_version: str
    required_contexts: tuple[str, ...]
    ignored_contexts: tuple[str, ...]
    effective_required_contexts: tuple[str, ...]
    recorded: bool
    all_required_ci_green_at_admission: bool
    verification_note: str


def load_ci_admission_snapshot_v1(
    *,
    repo_root: Path,
    config_relative: str,
    all_required_ci_green_at_admission: bool = False,
) -> CiAdmissionSnapshotV1:
    path = repo_root / config_relative
    raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    required = tuple(str(x) for x in raw.get("required_contexts", ()))
    ignored = tuple(str(x) for x in raw.get("ignored_contexts", ()))
    ignored_set = set(ignored)
    effective = tuple(c for c in required if c not in ignored_set)
    return CiAdmissionSnapshotV1(
        schema_version=str(raw.get("schema_version", "")),
        required_contexts=required,
        ignored_contexts=ignored,
        effective_required_contexts=effective,
        recorded=len(effective) > 0,
        all_required_ci_green_at_admission=all_required_ci_green_at_admission,
        verification_note=(
            "Structural snapshot from config/ci/required_status_checks.json; "
            "terminal GREEN verified via GitHub required checks on PR."
        ),
    )
