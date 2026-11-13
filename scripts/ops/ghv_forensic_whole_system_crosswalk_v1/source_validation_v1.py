"""Source validation guards (reuse canonical validators; no validator mutation)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    ATLAS_BOUNDARIES,
    ATLAS_MODEL,
    CENSUS_PATH,
    LANDSCAPE_PATH,
)

_CENSUS_VALIDATOR = (
    Path(__file__).resolve().parents[1] / "validate_current_system_census_graph_v1.py"
)
_LANDSCAPE_VALIDATOR = (
    Path(__file__).resolve().parents[1] / "validate_current_universe_landscape_snapshot_v1.py"
)
_ATLAS_VALIDATOR = Path(__file__).resolve().parents[1] / "validate_system_atlas_v1.py"


def _validator_script_repo_root() -> Path:
    return _CENSUS_VALIDATOR.resolve().parents[2]


def _subprocess_validators_required(
    *, strict_repo_invariants: bool, pt_launcher: Path | None
) -> bool:
    return bool(strict_repo_invariants and pt_launcher and pt_launcher.is_file())


@dataclass
class SourceValidationResultV1:
    ok: bool
    census_errors: list[str] = field(default_factory=list)
    landscape_errors: list[str] = field(default_factory=list)
    atlas_errors: list[str] = field(default_factory=list)
    snapshot_errors: list[str] = field(default_factory=list)
    census_validator_connected: bool = False
    landscape_validator_connected: bool = False
    atlas_subprocess_executed: bool = False
    landscape_subprocess_executed: bool = False
    every_required_validator_executed_and_passed: bool = False

    def all_errors(self) -> list[str]:
        return [
            *self.census_errors,
            *self.landscape_errors,
            *self.atlas_errors,
            *self.snapshot_errors,
        ]


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
    if repo_root.resolve() != _validator_script_repo_root().resolve():
        return (
            ["landscape_subprocess_validator_skipped:repo_root_mismatch_with_validator_checkout"],
            False,
        )
    if not _LANDSCAPE_VALIDATOR.is_file():
        return ["landscape_validator_missing"], False
    try:
        proc = subprocess.run(
            [str(pt_launcher), str(_LANDSCAPE_VALIDATOR)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [f"landscape_subprocess_validator_start_failed:{exc}"], False
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "landscape_validation_failed").strip()
        return [msg.splitlines()[-1] if msg else "landscape_validation_failed"], True
    return [], True


def run_atlas_validator_subprocess(*, repo_root: Path, pt_launcher: Path) -> tuple[list[str], bool]:
    if repo_root.resolve() != _validator_script_repo_root().resolve():
        return (
            ["atlas_subprocess_validator_skipped:repo_root_mismatch_with_validator_checkout"],
            False,
        )
    if not _ATLAS_VALIDATOR.is_file():
        return ["atlas_validator_missing"], False
    try:
        proc = subprocess.run(
            [str(pt_launcher), str(_ATLAS_VALIDATOR)],
            cwd=str(repo_root),
            env={**os.environ, "GIT_WORK_TREE": str(repo_root.resolve())},
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [f"atlas_subprocess_validator_start_failed:{exc}"], False
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "atlas_validation_failed").strip()
        return [msg.splitlines()[-1] if msg else "atlas_validation_failed"], True
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
    if not land_sha:
        errors.append("missing_landscape_source_revision")
    return errors


def inspect_source_binding_v1(
    *,
    repo_root: Path,
    code_snapshot,
    sources,
) -> dict[str, Any]:
    """Separate recorded source bytes from the scope of each revision claim."""
    head = code_snapshot.git_head
    records = {}
    for path, revision, role, scope_count in (
        (CENSUS_PATH, code_snapshot.census_revision, "CENSUS_SEMANTIC_INPUT", None),
        (LANDSCAPE_PATH, code_snapshot.landscape_revision, "LANDSCAPE_SEMANTIC_INPUT", None),
        (
            ATLAS_MODEL,
            code_snapshot.atlas_model_revision,
            "FROZEN_NAVIGATION_MODEL",
            sources.atlas_meta.get("model_reference_paths"),
        ),
        (
            ATLAS_BOUNDARIES,
            code_snapshot.atlas_revision,
            "REVIEWED_NAVIGATION_REGISTER",
            sources.atlas_meta.get("boundary_reference_paths"),
        ),
    ):
        actual = sources.source_sha256.get(path)
        if actual is None:
            continue
        blob = subprocess.run(
            ["git", "-C", str(repo_root), "cat-file", "blob", f"{head}:{path}"],
            capture_output=True,
            check=False,
        )
        bytes_match_head = blob.returncode == 0 and sha256(blob.stdout).hexdigest() == actual
        if not bytes_match_head:
            status = "SOURCE_BYTES_NOT_BOUND_TO_CHECKOUT_HEAD"
        elif scope_count is not None:
            # The loader already restricts the projection to references whose
            # Git bytes match the declared anchor and the checked-out files.
            status = "BOUND_FOR_FILTERED_NAVIGATION"
        elif revision == head:
            status = "DECLARED_CURRENT_REVISION"
        else:
            status = "SEMANTIC_REVIEW_REQUIRED"
        records[path] = {
            "role": role,
            "declared_revision": revision,
            "sha256": actual,
            "bytes_match_head": bytes_match_head,
            "status": status,
            "unchanged_reference_paths": scope_count,
        }
    return {"authority": "NONE", "reviewed_checkout": head, "sources": records}


def _finalize_validation_result(
    result: SourceValidationResultV1,
    *,
    subprocess_required: bool,
) -> None:
    if subprocess_required:
        executed = result.atlas_subprocess_executed and result.landscape_subprocess_executed
        passed = executed and not (
            result.census_errors or result.landscape_errors or result.atlas_errors
        )
        result.every_required_validator_executed_and_passed = passed
        if not result.atlas_subprocess_executed and not result.atlas_errors:
            result.atlas_errors.append("required_atlas_subprocess_validator_not_executed")
        if not result.landscape_subprocess_executed and not result.landscape_errors:
            result.landscape_errors.append("required_landscape_subprocess_validator_not_executed")
    else:
        result.every_required_validator_executed_and_passed = (
            not result.census_errors and not result.landscape_errors
        )
    result.ok = not result.all_errors() and result.every_required_validator_executed_and_passed


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
    result.census_errors = list(census_errors)
    result.census_validator_connected = census_connected

    result.landscape_errors = validate_landscape_document_minimal(landscape_doc)

    subprocess_required = _subprocess_validators_required(
        strict_repo_invariants=strict_repo_invariants, pt_launcher=pt_launcher
    )
    if subprocess_required:
        assert pt_launcher is not None
        atlas_errors, atlas_executed = run_atlas_validator_subprocess(
            repo_root=repo_root, pt_launcher=pt_launcher
        )
        result.atlas_subprocess_executed = atlas_executed
        result.atlas_errors.extend(atlas_errors)

        land_sub_err, land_executed = run_landscape_validator_subprocess(
            repo_root=repo_root, pt_launcher=pt_launcher
        )
        result.landscape_subprocess_executed = land_executed
        result.landscape_validator_connected = land_executed
        if land_sub_err:
            result.landscape_errors.extend(land_sub_err)
    else:
        result.landscape_validator_connected = False

    result.snapshot_errors = validate_snapshot_compatibility(
        git_head=git_head,
        census_doc=census_doc,
        landscape_doc=landscape_doc,
        strict=strict_repo_invariants,
    )
    _finalize_validation_result(result, subprocess_required=subprocess_required)
    return result
