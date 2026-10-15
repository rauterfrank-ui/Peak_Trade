"""Source validation guards (reuse canonical validators; no validator mutation)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_CENSUS_VALIDATOR = (
    Path(__file__).resolve().parents[1] / "validate_current_system_census_graph_v1.py"
)
_LANDSCAPE_VALIDATOR = (
    Path(__file__).resolve().parents[1] / "validate_current_universe_landscape_snapshot_v1.py"
)


@dataclass
class SourceValidationResultV1:
    ok: bool
    census_errors: list[str] = field(default_factory=list)
    landscape_errors: list[str] = field(default_factory=list)
    snapshot_errors: list[str] = field(default_factory=list)
    census_validator_connected: bool = False
    landscape_validator_connected: bool = False

    def all_errors(self) -> list[str]:
        return [*self.census_errors, *self.landscape_errors, *self.snapshot_errors]


def _load_census_validator_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "validate_current_system_census_graph_v1", _CENSUS_VALIDATOR
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validate_census_document(
    doc: dict[str, Any],
    *,
    strict_repo_invariants: bool,
) -> tuple[list[str], bool]:
    mod = _load_census_validator_module()
    errors: list[str] = []
    errors.extend(mod.validate_structure(doc))
    if strict_repo_invariants:
        errors.extend(mod.validate_objects(doc))
        errors.extend(mod.validate_edges(doc))
        errors.extend(mod.validate_topology(doc))
        errors.extend(mod.validate_discrepancies(doc))
    else:
        objects = doc.get("census_objects", [])
        ids = [o.get("object_id") for o in objects]
        if len(ids) != len(set(ids)):
            errors.append("duplicate object_id")
        edges = doc.get("semantic_edges", [])
        eids = [e.get("edge_id") for e in edges]
        if len(eids) != len(set(eids)):
            errors.append("duplicate edge_id")
    return errors, True


def validate_landscape_document_minimal(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("authority_effect") != "NONE":
        errors.append("authority_effect must be NONE")
    if doc.get("runtime_authorization_effect") != "NONE":
        errors.append("runtime_authorization_effect must be NONE")
    if doc.get("not_operational_ssot") is not True:
        errors.append("not_operational_ssot must be true")
    surfaces = doc.get("surfaces") or []
    if not surfaces:
        errors.append("surfaces empty")
    return errors


def run_landscape_validator_subprocess(
    *, repo_root: Path, pt_launcher: Path
) -> tuple[list[str], bool]:
    if not _LANDSCAPE_VALIDATOR.is_file():
        return ["landscape_validator_missing"], False
    proc = subprocess.run(
        [str(pt_launcher), str(_LANDSCAPE_VALIDATOR)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "landscape_validation_failed").strip()
        return [msg.splitlines()[-1] if msg else "landscape_validation_failed"], True
    return [], True


def run_census_validator_subprocess(
    *, repo_root: Path, pt_launcher: Path
) -> tuple[list[str], bool]:
    proc = subprocess.run(
        [str(pt_launcher), str(_CENSUS_VALIDATOR)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "census_validation_failed").strip()
        return [msg.splitlines()[-1] if msg else "census_validation_failed"], True
    return [], True


def validate_snapshot_compatibility(
    *,
    git_head: str,
    census_doc: dict[str, Any],
    landscape_doc: dict[str, Any],
    strict: bool,
) -> list[str]:
    if not strict:
        return []
    errors: list[str] = []
    baseline = str(census_doc.get("source_baseline_head") or "")
    if baseline and git_head != baseline:
        errors.append(f"census_source_baseline_head_mismatch: head={git_head} baseline={baseline}")
    land_sha = str(
        landscape_doc.get("evidence_baseline_sha")
        or landscape_doc.get("universe_map_consolidation_v1", {}).get(
            "consolidation_baseline_sha", ""
        )
        or ""
    )
    if land_sha and git_head != land_sha:
        errors.append(
            f"landscape_evidence_baseline_sha_mismatch: head={git_head} baseline={land_sha}"
        )
    if not baseline:
        errors.append("missing_census_source_revision")
    return errors


def validate_sources_v1(
    *,
    repo_root: Path,
    census_doc: dict[str, Any],
    landscape_doc: dict[str, Any],
    git_head: str,
    strict_repo_invariants: bool,
    pt_launcher: Path | None = None,
) -> SourceValidationResultV1:
    result = SourceValidationResultV1(ok=True)
    census_errors, census_connected = validate_census_document(
        census_doc, strict_repo_invariants=strict_repo_invariants
    )
    result.census_errors = census_errors
    result.census_validator_connected = census_connected

    if strict_repo_invariants and pt_launcher and pt_launcher.is_file():
        sub_err, _ = run_census_validator_subprocess(repo_root=repo_root, pt_launcher=pt_launcher)
        if sub_err:
            result.census_errors.extend(sub_err)
        land_err, land_connected = run_landscape_validator_subprocess(
            repo_root=repo_root, pt_launcher=pt_launcher
        )
        result.landscape_errors = land_err
        result.landscape_validator_connected = land_connected
    else:
        result.landscape_errors = validate_landscape_document_minimal(landscape_doc)
        result.landscape_validator_connected = False

    result.snapshot_errors = validate_snapshot_compatibility(
        git_head=git_head,
        census_doc=census_doc,
        landscape_doc=landscape_doc,
        strict=strict_repo_invariants,
    )
    if result.all_errors():
        result.ok = False
    return result
