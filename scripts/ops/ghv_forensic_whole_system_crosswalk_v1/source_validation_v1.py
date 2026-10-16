"""Source validation guards (reuse canonical validators; no validator mutation)."""

from __future__ import annotations

import copy
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
    snapshot_errors: list[str] = field(default_factory=list)
    census_validator_connected: bool = False
    landscape_validator_connected: bool = False
    census_subprocess_executed: bool = False
    landscape_subprocess_executed: bool = False
    every_required_validator_executed_and_passed: bool = False

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


def run_census_validator_subprocess(
    *, repo_root: Path, pt_launcher: Path
) -> tuple[list[str], bool]:
    if repo_root.resolve() != _validator_script_repo_root().resolve():
        return (
            ["census_subprocess_validator_skipped:repo_root_mismatch_with_validator_checkout"],
            False,
        )
    if not _CENSUS_VALIDATOR.is_file():
        return ["census_validator_missing"], False
    try:
        proc = subprocess.run(
            [str(pt_launcher), str(_CENSUS_VALIDATOR)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return [f"census_subprocess_validator_start_failed:{exc}"], False
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout or "census_validation_failed").strip()
        return [msg.splitlines()[-1] if msg else "census_validation_failed"], True
    return [], True


def _git_is_ancestor(repo_root: Path, ancestor: str, head: str) -> bool:
    if not ancestor or not head:
        return False
    if ancestor == head:
        return True
    try:
        subprocess.check_call(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", ancestor, head],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _load_json_at_git_ref(repo_root: Path, git_ref: str, rel_path: str) -> dict[str, Any] | None:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repo_root), "show", f"{git_ref}:{rel_path}"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return None
    return json.loads(raw)


def _strip_census_pin_fields(doc: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(doc)
    stripped.pop("source_baseline_head", None)
    return stripped


def _strip_landscape_pin_fields(doc: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(doc)
    stripped.pop("evidence_baseline_sha", None)
    stripped.pop("evidence_baseline_tree_sha", None)
    return stripped


def _materialized_governance_snapshot_matches_baseline(
    *,
    repo_root: Path,
    git_head: str,
    baseline_sha: str,
    current_doc: dict[str, Any],
    rel_path: str,
    strip_fn,
) -> bool:
    if not baseline_sha or git_head == baseline_sha:
        return True
    if not _git_is_ancestor(repo_root, baseline_sha, git_head):
        return False
    baseline_doc = _load_json_at_git_ref(repo_root, baseline_sha, rel_path)
    if baseline_doc is None:
        return False
    return strip_fn(baseline_doc) == strip_fn(current_doc)


def validate_snapshot_compatibility(
    *,
    repo_root: Path,
    git_head: str,
    census_doc: dict[str, Any],
    landscape_doc: dict[str, Any],
    strict: bool,
) -> list[str]:
    if not strict:
        return []
    errors: list[str] = []
    baseline = str(census_doc.get("source_baseline_head") or "")
    census_rel = "config/governance/current_system_census_graph_v1/source_v1.json"
    landscape_rel = "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
    if baseline and git_head != baseline:
        if not _materialized_governance_snapshot_matches_baseline(
            repo_root=repo_root,
            git_head=git_head,
            baseline_sha=baseline,
            current_doc=census_doc,
            rel_path=census_rel,
            strip_fn=_strip_census_pin_fields,
        ):
            errors.append(
                f"census_source_baseline_head_mismatch: head={git_head} baseline={baseline}"
            )
    land_sha = str(
        landscape_doc.get("evidence_baseline_sha")
        or landscape_doc.get("universe_map_consolidation_v1", {}).get(
            "consolidation_baseline_sha", ""
        )
        or ""
    )
    if land_sha and git_head != land_sha:
        if not _materialized_governance_snapshot_matches_baseline(
            repo_root=repo_root,
            git_head=git_head,
            baseline_sha=land_sha,
            current_doc=landscape_doc,
            rel_path=landscape_rel,
            strip_fn=_strip_landscape_pin_fields,
        ):
            errors.append(
                f"landscape_evidence_baseline_sha_mismatch: head={git_head} baseline={land_sha}"
            )
    if not baseline:
        errors.append("missing_census_source_revision")
    return errors


def _finalize_validation_result(
    result: SourceValidationResultV1,
    *,
    subprocess_required: bool,
) -> None:
    if subprocess_required:
        executed = result.census_subprocess_executed and result.landscape_subprocess_executed
        passed = executed and not result.census_errors and not result.landscape_errors
        result.every_required_validator_executed_and_passed = passed
        if not executed and not result.census_errors and not result.landscape_errors:
            result.census_errors.append("required_census_subprocess_validator_not_executed")
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
        census_sub_err, census_executed = run_census_validator_subprocess(
            repo_root=repo_root, pt_launcher=pt_launcher
        )
        result.census_subprocess_executed = census_executed
        result.census_validator_connected = census_connected and census_executed
        if census_sub_err:
            result.census_errors.extend(census_sub_err)

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
        repo_root=repo_root,
        git_head=git_head,
        census_doc=census_doc,
        landscape_doc=landscape_doc,
        strict=strict_repo_invariants,
    )
    _finalize_validation_result(result, subprocess_required=subprocess_required)
    return result
