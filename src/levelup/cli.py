"""
Minimal CLI for Level-Up v0 manifests (validate / format / schema export / round-trip checks).

Does not connect to exchanges or change execution posture.

validate exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed and model-validated
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode)
- 3 — JSON ok but model / schema validation failed

dump-empty exit contract (stdout is one JSON object per invocation):
- 0 — empty manifest written
- 2 — usage / path / write problem (e.g. target is a directory, mkdir/write permission)

format exit contract (stdout is one JSON object per invocation):
- 0 — manifest validated and canonically rewritten
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode) or write problem
- 3 — JSON ok but model / schema validation failed

canonical-check exit contract (stdout is one JSON object per invocation):
- 0 — manifest validated and already canonical
- 2 — usage / input problem (unreadable path, invalid JSON, UTF-8 decode)
- 3 — model / schema validation failed, or manifest is valid but not canonical

export-json-schema exit contract (stdout is one JSON object per invocation):
- 0 — schema export succeeded

describe-slice exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated, slice_id found
- 2 — usage / input problem (same as validate: unreadable path, invalid JSON, UTF-8 decode)
- 3 — JSON ok but model / schema validation failed, or manifest valid but slice_id not found

list-slices exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; stdout lists slice_id values in manifest order
- 2 — usage / input problem (same as validate)
- 3 — JSON ok but model / schema validation failed

check-evidence exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has an existing directory at repo-relative path
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest ok but at least one evidence path is missing or not a directory

check-evidence-coverage exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice has a non-empty evidence field
- 2 — usage / input problem (same as validate)
- 3 — manifest parsed, model-validated; at least one slice has no evidence field

check-evidence-readiness exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice has evidence and all evidence paths exist as directories
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest parsed, model-validated; at least one slice has missing evidence or invalid evidence path

check-evidence-bundle exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has a bundle-ready evidence directory
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest parsed, model-validated; at least one slice with evidence is not bundle-ready

check-evidence-integrity exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has SHA256-consistent files for SHA256SUMS entries
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest parsed, model-validated; at least one slice with evidence has integrity-readiness issues

check-evidence-attestation exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has at least one *_ATTESTATION.txt file
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest parsed, model-validated; at least one slice with evidence has no attestation-ready directory state

check-evidence-attestation-contract exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence has an attestation file matching the minimal contract
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest path
- 3 — manifest parsed, model-validated; at least one slice with evidence violates attestation contract readiness

check-evidence-attestation-consistency exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence is consistent across manifest slice_id, attestation fields, and canonical integrity target binding
- 2 — usage / input problem (same as validate), repository root could not be resolved, or per-slice path/readability errors occurred
- 3 — manifest parsed, model-validated; at least one slice with evidence has a domain-level consistency mismatch

check-evidence-attestation-readiness exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice with evidence is attestation-ready (presence + minimal contract + canonical target-bound consistency)
- 2 — usage / input problem (same as validate), repository root could not be resolved, or per-slice path/readability errors occurred
- 3 — manifest parsed, model-validated; at least one slice with evidence has a domain-level attestation readiness mismatch

check-evidence-attestation-uniqueness exit contract (stdout is one JSON object per invocation):
- 0 — manifest mode: manifest parsed, model-validated; every slice with evidence has exactly one *_ATTESTATION.txt file
      target mode: one evidence target has exactly one *_ATTESTATION.txt file
- 2 — usage / input problem (same as validate), or repository root could not be resolved from the manifest-or-target path
- 3 — at least one checked target has missing / multiple attestations or path-directory state mismatch

check-evidence-attestation-integrity exit contract (stdout is one JSON object per invocation):
- 0 — manifest mode: manifest parsed, model-validated; every slice with evidence has one attestation and the attested SHA256SUMS target is canonical + cryptographically valid
      target mode: one evidence target has one attestation and the attested SHA256SUMS target is canonical + cryptographically valid
- 2 — usage / input problem (same as validate), repository root could not be resolved from the manifest-or-target path, or evidence/attestation read errors occurred
- 3 — at least one checked target violates attestation-integrity requirements

check-evidence-readiness-overall exit contract (stdout is one JSON object per invocation):
- 0 — manifest parsed, model-validated; every slice is evidence-ready across coverage/path, bundle, integrity, and attestation-readiness
- 2 — usage / input problem (same as validate), repository root could not be resolved, or at least one per-slice path/readability input error occurred
- 3 — manifest parsed, model-validated; at least one slice has domain-level non-readiness without input errors
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from src.levelup.v0_io import canonical_manifest_json, read_manifest, write_manifest
from src.levelup.v0_models import LevelUpManifestV0, levelup_manifest_v0_json_schema

EXIT_VALIDATION_OK = 0
EXIT_INPUT = 2
EXIT_VALIDATION_FAILED = 3

_BUNDLE_REQUIREMENT_FILE_SHA256SUMS = "SHA256SUMS.txt"
_BUNDLE_REQUIREMENT_GLOB_BUNDLE = "*.bundle.tgz"
_BUNDLE_REQUIREMENT_GLOB_SUMMARY = "*_CRAWLER_SUMMARY_1LINE.txt"
_ATTESTATION_REQUIREMENT_GLOB = "*_ATTESTATION.txt"
_SHA256SUMS_LINE_RE = re.compile(r"^([0-9a-f]{64})\s+(.+)$")
_ATTESTATION_KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*?)\s*$")
_ATTESTATION_REQUIRED_KEYS = (
    "slice_id",
    "attested_at_utc",
    "attestor",
    "scope",
    "sha256sums_file",
)
_ATTESTED_AT_UTC_ISO8601_LIKE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:\d{2})$"
)


def _find_peak_trade_repo_root(manifest_path: Path) -> Path | None:
    """Walk parents from *manifest_path* for a checkout marker (pyproject + src/levelup)."""
    resolved = manifest_path.resolve()
    anchor = resolved.parent if resolved.is_file() else resolved
    for p in [anchor, *anchor.parents]:
        if (p / "pyproject.toml").is_file() and (p / "src" / "levelup").is_dir():
            return p
    return None


def _emit_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _resolve_hashed_file_path(raw_path: str, repo_root: Path, evidence_dir: Path) -> Path | None:
    rel = Path(raw_path)
    if rel.is_absolute():
        return None
    evidence_root = evidence_dir.resolve()
    candidates = [(evidence_dir / rel).resolve(), (repo_root / rel).resolve()]
    for candidate in candidates:
        if _is_relative_to(candidate, evidence_root):
            return candidate
    return None


def _canonical_integrity_anchor_path(evidence_dir: Path) -> Path:
    return (evidence_dir / _BUNDLE_REQUIREMENT_FILE_SHA256SUMS).resolve()


def _assess_attestation_target_binding_to_canonical_integrity_anchor(
    resolved_sha256sums_target: Path | None, evidence_dir: Path
) -> tuple[str, bool, bool | None]:
    canonical_anchor = _canonical_integrity_anchor_path(evidence_dir)
    canonical_anchor_exists = canonical_anchor.is_file()
    targets_canonical_anchor: bool | None = None
    if canonical_anchor_exists and resolved_sha256sums_target is not None:
        targets_canonical_anchor = resolved_sha256sums_target.resolve() == canonical_anchor
    return str(canonical_anchor), canonical_anchor_exists, targets_canonical_anchor


def _parse_sha256sums_records(
    sha_file: Path, repo_root: Path, evidence_dir: Path
) -> tuple[list[dict[str, object]], bool]:
    try:
        content = sha_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], True

    records: list[dict[str, object]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _SHA256SUMS_LINE_RE.fullmatch(line)
        if match is None:
            return [], True
        expected_sha256 = match.group(1)
        raw_path = match.group(2)
        target_path = _resolve_hashed_file_path(raw_path, repo_root, evidence_dir)
        if target_path is None:
            return [], True
        records.append(
            {
                "path": raw_path,
                "expected_sha256": expected_sha256,
                "target_path": target_path,
            }
        )
    return records, False


def _parse_attestation_key_values(content: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in content.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = _ATTESTATION_KEY_VALUE_RE.fullmatch(raw_line)
        if match is None:
            continue
        fields[match.group(1)] = match.group(2).strip()
    return fields


def _looks_like_sha256sums_file_reference(value: str) -> bool:
    ref_name = Path(value.strip()).name
    if ref_name == _BUNDLE_REQUIREMENT_FILE_SHA256SUMS:
        return True
    return "SHA256SUMS" in ref_name and ref_name.lower().endswith(".txt")


def _read_manifest_with_contract(path: Path) -> tuple[LevelUpManifestV0 | None, int | None]:
    try:
        m = read_manifest(path)
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_read_failed",
                "message": str(exc),
            }
        )
        return None, EXIT_INPUT
    except UnicodeDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "utf8_decode_failed",
                "message": str(exc),
            }
        )
        return None, EXIT_INPUT
    except JSONDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "json_parse_failed",
                "message": str(exc),
            }
        )
        return None, EXIT_INPUT
    except ValidationError as exc:
        issues = exc.errors()
        if issues and issues[0].get("type") == "json_invalid":
            msg = str(issues[0].get("msg") or "invalid JSON")
            _emit_json(
                {
                    "ok": False,
                    "error": "input",
                    "reason": "json_parse_failed",
                    "message": msg,
                }
            )
            return None, EXIT_INPUT
        issues = issues[:8]
        _emit_json(
            {
                "ok": False,
                "error": "validation",
                "reason": "model_validation_failed",
                "message": "manifest failed LevelUpManifestV0 validation",
                "issues": issues,
            }
        )
        return None, EXIT_VALIDATION_FAILED

    return m, None


def _cmd_validate(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    _emit_json({"ok": True, "schema": m.schema_version, "slices": len(m.slices)})
    return EXIT_VALIDATION_OK


def _cmd_dump_empty(path: Path) -> int:
    m = LevelUpManifestV0()
    try:
        write_manifest(path, m)
    except IsADirectoryError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "target_path_is_directory",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_write_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT

    _emit_json({"ok": True, "wrote": str(path)})
    return EXIT_VALIDATION_OK


def _cmd_format(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    try:
        write_manifest(path, m)
    except IsADirectoryError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "target_path_is_directory",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_write_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT

    _emit_json(
        {"ok": True, "wrote": str(path), "schema": m.schema_version, "slices": len(m.slices)}
    )
    return EXIT_VALIDATION_OK


def _cmd_canonical_check(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    try:
        current = path.read_text(encoding="utf-8")
    except OSError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "manifest_read_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT
    except UnicodeDecodeError as exc:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "utf8_decode_failed",
                "message": str(exc),
            }
        )
        return EXIT_INPUT

    expected = canonical_manifest_json(m)
    if current != expected:
        _emit_json(
            {
                "ok": False,
                "error": "validation",
                "reason": "manifest_not_canonical",
                "message": "manifest is valid but not in canonical serialized form",
                "canonical": False,
                "schema": m.schema_version,
                "slices": len(m.slices),
            }
        )
        return EXIT_VALIDATION_FAILED

    _emit_json({"ok": True, "canonical": True, "schema": m.schema_version, "slices": len(m.slices)})
    return EXIT_VALIDATION_OK


def _cmd_export_json_schema() -> int:
    schema = levelup_manifest_v0_json_schema()
    _emit_json({"ok": True, "schema": LevelUpManifestV0().schema_version, "json_schema": schema})
    return EXIT_VALIDATION_OK


def _cmd_describe_slice(path: Path, slice_id: str) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    for sl in m.slices:
        if sl.slice_id == slice_id:
            _emit_json(
                {
                    "ok": True,
                    "schema": m.schema_version,
                    "command": "describe-slice",
                    "slice_id": sl.slice_id,
                    "title": sl.title,
                    "contract_summary": sl.contract_summary,
                    "evidence": sl.evidence.model_dump(mode="json")
                    if sl.evidence is not None
                    else None,
                }
            )
            return EXIT_VALIDATION_OK

    _emit_json(
        {
            "ok": False,
            "error": "validation",
            "reason": "slice_not_found",
            "message": f"no slice with slice_id {slice_id!r} in manifest",
            "schema": m.schema_version,
            "slice_id": slice_id,
        }
    )
    return EXIT_VALIDATION_FAILED


def _cmd_list_slices(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    ids = [sl.slice_id for sl in m.slices]
    _emit_json(
        {
            "ok": True,
            "schema": m.schema_version,
            "command": "list-slices",
            "count": len(ids),
            "slices": ids,
        }
    )
    return EXIT_VALIDATION_OK


def _cmd_check_evidence(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue
        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
            }
        )

    missing_count = sum(1 for e in entries if not e["exists"])
    not_dir_count = sum(1 for e in entries if e["exists"] and not e["is_dir"])
    ok = missing_count == 0 and not_dir_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence",
            "manifest_path": str(path.resolve()),
            "checked_count": len(entries),
            "missing_count": missing_count,
            "not_dir_count": not_dir_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_coverage(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    entries: list[dict[str, object]] = []
    for sl in m.slices:
        has_evidence = sl.evidence is not None and bool(sl.evidence.relative_dir.strip())
        entries.append(
            {
                "slice_id": sl.slice_id,
                "has_evidence": has_evidence,
                "evidence": sl.evidence.relative_dir if sl.evidence is not None else None,
            }
        )

    total_slices = len(entries)
    with_evidence_count = sum(1 for e in entries if e["has_evidence"])
    without_evidence_count = total_slices - with_evidence_count
    coverage_ratio = float(with_evidence_count) / float(total_slices) if total_slices > 0 else 1.0
    ok = without_evidence_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-coverage",
            "manifest_path": str(path.resolve()),
            "total_slices": total_slices,
            "with_evidence_count": with_evidence_count,
            "without_evidence_count": without_evidence_count,
            "coverage_ratio": coverage_ratio,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_readiness(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        has_evidence = sl.evidence is not None and bool(sl.evidence.relative_dir.strip())
        if not has_evidence:
            entries.append(
                {
                    "slice_id": sl.slice_id,
                    "has_evidence": False,
                    "evidence": None,
                    "exists": None,
                    "is_dir": None,
                    "status": "missing_evidence",
                }
            )
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        if not exists:
            status = "missing_path"
        elif not is_dir:
            status = "not_a_directory"

        entries.append(
            {
                "slice_id": sl.slice_id,
                "has_evidence": True,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "status": status,
            }
        )

    total_slices = len(entries)
    with_evidence_count = sum(1 for e in entries if e["has_evidence"])
    without_evidence_count = total_slices - with_evidence_count
    checked_path_count = with_evidence_count
    missing_path_count = sum(1 for e in entries if e["status"] == "missing_path")
    not_dir_count = sum(1 for e in entries if e["status"] == "not_a_directory")
    ok = without_evidence_count == 0 and missing_path_count == 0 and not_dir_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-readiness",
            "manifest_path": str(path.resolve()),
            "total_slices": total_slices,
            "with_evidence_count": with_evidence_count,
            "without_evidence_count": without_evidence_count,
            "checked_path_count": checked_path_count,
            "missing_path_count": missing_path_count,
            "not_dir_count": not_dir_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_bundle(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        required_checks: list[dict[str, object]] = []
        missing_requirements: list[str] = []
        status = "ok"

        if not exists:
            status = "missing_path"
            required_checks = [
                {
                    "requirement": "sha256sums_txt",
                    "pattern": _BUNDLE_REQUIREMENT_FILE_SHA256SUMS,
                    "ok": False,
                },
                {
                    "requirement": "bundle_archive",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_BUNDLE,
                    "min_count": 1,
                    "match_count": 0,
                    "ok": False,
                },
                {
                    "requirement": "crawler_summary_1line",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_SUMMARY,
                    "min_count": 1,
                    "match_count": 0,
                    "ok": False,
                },
            ]
            missing_requirements = [c["requirement"] for c in required_checks]
        elif not is_dir:
            status = "not_a_directory"
            required_checks = [
                {
                    "requirement": "sha256sums_txt",
                    "pattern": _BUNDLE_REQUIREMENT_FILE_SHA256SUMS,
                    "ok": False,
                },
                {
                    "requirement": "bundle_archive",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_BUNDLE,
                    "min_count": 1,
                    "match_count": 0,
                    "ok": False,
                },
                {
                    "requirement": "crawler_summary_1line",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_SUMMARY,
                    "min_count": 1,
                    "match_count": 0,
                    "ok": False,
                },
            ]
            missing_requirements = [c["requirement"] for c in required_checks]
        else:
            sha256_ok = (target / _BUNDLE_REQUIREMENT_FILE_SHA256SUMS).is_file()
            bundle_count = sum(1 for _ in target.glob(_BUNDLE_REQUIREMENT_GLOB_BUNDLE))
            summary_count = sum(1 for _ in target.glob(_BUNDLE_REQUIREMENT_GLOB_SUMMARY))
            required_checks = [
                {
                    "requirement": "sha256sums_txt",
                    "pattern": _BUNDLE_REQUIREMENT_FILE_SHA256SUMS,
                    "ok": sha256_ok,
                },
                {
                    "requirement": "bundle_archive",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_BUNDLE,
                    "min_count": 1,
                    "match_count": bundle_count,
                    "ok": bundle_count >= 1,
                },
                {
                    "requirement": "crawler_summary_1line",
                    "pattern": _BUNDLE_REQUIREMENT_GLOB_SUMMARY,
                    "min_count": 1,
                    "match_count": summary_count,
                    "ok": summary_count >= 1,
                },
            ]
            missing_requirements = [c["requirement"] for c in required_checks if not c["ok"]]
            if missing_requirements:
                status = "missing_bundle_requirements"

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "required_checks": required_checks,
                "missing_requirements": missing_requirements,
                "status": status,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["status"] == "ok")
    not_ready_count = checked_count - ready_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-bundle",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_integrity(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        checked_files = 0
        missing_requirements: list[str] = []
        failed_files: list[dict[str, object]] = []

        if not exists:
            status = "missing_path"
            missing_requirements = ["evidence_directory"]
        elif not is_dir:
            status = "not_a_directory"
            missing_requirements = ["evidence_directory"]
        else:
            sha_file = target / _BUNDLE_REQUIREMENT_FILE_SHA256SUMS
            if not sha_file.is_file():
                status = "missing_sha256sums"
                missing_requirements = ["sha256sums_txt"]
            else:
                records, invalid_sha256sums_format = _parse_sha256sums_records(
                    sha_file, repo_root, target
                )
                if invalid_sha256sums_format:
                    status = "invalid_sha256sums_format"
                    missing_requirements = ["sha256sums_format"]
                else:
                    checked_files = len(records)
                    for rec in records:
                        expected_sha256 = str(rec["expected_sha256"])
                        target_path = rec["target_path"]
                        assert isinstance(target_path, Path)
                        file_path = str(rec["path"])

                        if not target_path.is_file():
                            failed_files.append(
                                {
                                    "path": file_path,
                                    "status": "missing_hashed_file",
                                    "expected_sha256": expected_sha256,
                                }
                            )
                            continue

                        try:
                            actual_sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
                        except OSError as exc:
                            _emit_json(
                                {
                                    "ok": False,
                                    "error": "input",
                                    "reason": "evidence_read_failed",
                                    "message": str(exc),
                                }
                            )
                            return EXIT_INPUT

                        if actual_sha256 != expected_sha256:
                            failed_files.append(
                                {
                                    "path": file_path,
                                    "status": "hash_mismatch",
                                    "expected_sha256": expected_sha256,
                                    "actual_sha256": actual_sha256,
                                }
                            )

                    has_missing_hashed_file = any(
                        f["status"] == "missing_hashed_file" for f in failed_files
                    )
                    has_hash_mismatch = any(f["status"] == "hash_mismatch" for f in failed_files)
                    if has_missing_hashed_file:
                        status = "missing_hashed_file"
                    elif has_hash_mismatch:
                        status = "hash_mismatch"

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "status": status,
                "checked_files": checked_files,
                "missing_requirements": missing_requirements,
                "failed_files": failed_files,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["status"] == "ok")
    not_ready_count = checked_count - ready_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-integrity",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_attestation(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        attestation_matches: list[str] = []
        missing_requirements: list[str] = []

        if not exists:
            status = "missing_path"
            missing_requirements = ["evidence_directory", "attestation_file"]
        elif not is_dir:
            status = "not_a_directory"
            missing_requirements = ["evidence_directory", "attestation_file"]
        else:
            try:
                attestation_matches = sorted(
                    p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
                )
            except OSError as exc:
                _emit_json(
                    {
                        "ok": False,
                        "error": "input",
                        "reason": "evidence_read_failed",
                        "message": str(exc),
                    }
                )
                return EXIT_INPUT

            if not attestation_matches:
                status = "missing_attestation"
                missing_requirements = ["attestation_file"]

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "attestation_matches": attestation_matches,
                "missing_requirements": missing_requirements,
                "status": status,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["status"] == "ok")
    not_ready_count = checked_count - ready_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-attestation",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_attestation_contract(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        attestation_matches: list[str] = []
        missing_requirements: list[str] = []
        contract_details: dict[str, object] = {
            "checked_file": None,
            "required_keys": list(_ATTESTATION_REQUIRED_KEYS),
            "missing_keys": [],
            "empty_keys": [],
            "parsed_keys": [],
            "readable_utf8": False,
            "non_empty": False,
            "attested_at_utc_iso8601_like": False,
            "sha256sums_file_valid": False,
            "slice_id_matches_manifest": False,
            "canonical_integrity_anchor": str(_canonical_integrity_anchor_path(target)),
            "canonical_integrity_anchor_exists": False,
            "sha256sums_file_reference_resolved": None,
            "sha256sums_file_target": None,
            "sha256sums_file_target_exists": None,
            "sha256sums_file_targets_canonical_integrity_anchor": None,
            "parse_mode": "key_value",
        }

        if not exists:
            status = "missing_path"
            missing_requirements = ["evidence_directory", "attestation_contract"]
        elif not is_dir:
            status = "not_a_directory"
            missing_requirements = ["evidence_directory", "attestation_contract"]
        else:
            try:
                attestation_matches = sorted(
                    p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
                )
            except OSError as exc:
                _emit_json(
                    {
                        "ok": False,
                        "error": "input",
                        "reason": "evidence_read_failed",
                        "message": str(exc),
                    }
                )
                return EXIT_INPUT

            if not attestation_matches:
                status = "missing_attestation"
                missing_requirements = ["attestation_file", "attestation_contract"]
            elif len(attestation_matches) > 1:
                status = "multiple_attestations"
                missing_requirements = ["attestation_uniqueness", "attestation_contract"]
            else:
                checked_file = attestation_matches[0]
                contract_details["checked_file"] = checked_file
                attestation_path = target / checked_file
                try:
                    text = attestation_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    status = "unreadable_attestation"
                    missing_requirements = ["attestation_utf8_readable"]
                    contract_details["readable_utf8"] = False
                else:
                    contract_details["readable_utf8"] = True
                    contract_details["non_empty"] = bool(text.strip())
                    fields = _parse_attestation_key_values(text)
                    contract_details["parsed_keys"] = sorted(fields.keys())

                    missing_keys: list[str] = []
                    empty_keys: list[str] = []
                    for key in _ATTESTATION_REQUIRED_KEYS:
                        if key not in fields:
                            missing_keys.append(key)
                        elif not fields[key].strip():
                            empty_keys.append(key)

                    attested_at_utc = fields.get("attested_at_utc", "")
                    sha256sums_file = fields.get("sha256sums_file", "")
                    iso_like = bool(_ATTESTED_AT_UTC_ISO8601_LIKE_RE.fullmatch(attested_at_utc))
                    sha_ref_ok = _looks_like_sha256sums_file_reference(sha256sums_file)

                    contract_details["missing_keys"] = missing_keys
                    contract_details["empty_keys"] = empty_keys
                    contract_details["attested_at_utc_iso8601_like"] = iso_like
                    contract_details["sha256sums_file_valid"] = sha_ref_ok
                    contract_details["slice_id_matches_manifest"] = (
                        bool(fields.get("slice_id", "")) and fields["slice_id"] == sl.slice_id
                    )

                    if (
                        not contract_details["non_empty"]
                        or missing_keys
                        or empty_keys
                        or not iso_like
                        or not sha_ref_ok
                    ):
                        status = "invalid_attestation_contract"
                        if not contract_details["non_empty"]:
                            missing_requirements.append("attestation_non_empty")
                        missing_requirements.extend(missing_keys)
                        missing_requirements.extend(f"{key}_non_empty" for key in empty_keys)
                        if not iso_like:
                            missing_requirements.append("attested_at_utc_iso8601_like")
                        if not sha_ref_ok:
                            missing_requirements.append("sha256sums_file_reference")
                    else:
                        resolved_sha256sums_target: Path | None = None
                        if sha256sums_file:
                            resolved_sha256sums_target = _resolve_hashed_file_path(
                                sha256sums_file, repo_root, target
                            )
                        contract_details["sha256sums_file_reference_resolved"] = (
                            resolved_sha256sums_target is not None
                        )
                        if resolved_sha256sums_target is not None:
                            contract_details["sha256sums_file_target"] = str(
                                resolved_sha256sums_target
                            )
                            contract_details["sha256sums_file_target_exists"] = (
                                resolved_sha256sums_target.is_file()
                            )
                        else:
                            contract_details["sha256sums_file_target_exists"] = False

                        (
                            _canonical_anchor,
                            canonical_anchor_exists,
                            targets_canonical_anchor,
                        ) = _assess_attestation_target_binding_to_canonical_integrity_anchor(
                            resolved_sha256sums_target, target
                        )
                        contract_details["canonical_integrity_anchor_exists"] = (
                            canonical_anchor_exists
                        )
                        contract_details["sha256sums_file_targets_canonical_integrity_anchor"] = (
                            targets_canonical_anchor
                        )

                        if not contract_details["sha256sums_file_reference_resolved"]:
                            status = "invalid_attestation_contract"
                            missing_requirements.append("sha256sums_file_reference_resolved")
                        elif not contract_details["sha256sums_file_target_exists"]:
                            status = "invalid_attestation_contract"
                            missing_requirements.append("sha256sums_file_target_exists")
                        elif canonical_anchor_exists and targets_canonical_anchor is False:
                            status = "invalid_attestation_contract"
                            missing_requirements.append(
                                "sha256sums_file_targets_canonical_integrity_anchor"
                            )

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "attestation_matches": attestation_matches,
                "status": status,
                "missing_requirements": sorted(set(missing_requirements)),
                "contract_details": contract_details,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["status"] == "ok")
    not_ready_count = checked_count - ready_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-attestation-contract",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _cmd_check_evidence_attestation_consistency(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        missing_requirements: list[str] = []
        attestation_matches: list[str] = []
        attestation_file: str | None = None
        attestation_readable_utf8: bool | None = None
        attestation_slice_id: str | None = None
        attestation_slice_id_matches_manifest: bool | None = None
        attestation_sha256sums_file: str | None = None
        sha256sums_file_reference_resolved: bool | None = None
        sha256sums_file_target: str | None = None
        sha256sums_file_target_exists: bool | None = None
        canonical_integrity_anchor = str(_canonical_integrity_anchor_path(target))
        canonical_integrity_anchor_exists = False
        sha256sums_file_targets_canonical_integrity_anchor: bool | None = None

        if not exists:
            status = "missing_path"
            missing_requirements = ["evidence_directory"]
        elif not is_dir:
            status = "not_a_directory"
            missing_requirements = ["evidence_directory"]
        else:
            try:
                attestation_matches = sorted(
                    p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
                )
            except OSError as exc:
                _emit_json(
                    {
                        "ok": False,
                        "error": "input",
                        "reason": "evidence_read_failed",
                        "message": str(exc),
                    }
                )
                return EXIT_INPUT

            if not attestation_matches:
                status = "missing_attestation"
                missing_requirements = ["attestation_file"]
            elif len(attestation_matches) > 1:
                status = "multiple_attestations"
                missing_requirements = ["attestation_uniqueness"]
            else:
                attestation_file = attestation_matches[0]
                attestation_path = target / attestation_file
                try:
                    text = attestation_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    status = "unreadable_attestation"
                    attestation_readable_utf8 = False
                    missing_requirements = ["attestation_utf8_readable"]
                else:
                    attestation_readable_utf8 = True
                    fields = _parse_attestation_key_values(text)
                    attestation_slice_id = fields.get("slice_id")
                    attestation_sha256sums_file = fields.get("sha256sums_file")
                    attestation_slice_id_matches_manifest = (
                        attestation_slice_id == sl.slice_id
                        if attestation_slice_id is not None
                        else False
                    )

                    resolved_sha256sums_target: Path | None = None
                    if attestation_sha256sums_file is not None:
                        resolved_sha256sums_target = _resolve_hashed_file_path(
                            attestation_sha256sums_file, repo_root, target
                        )
                    sha256sums_file_reference_resolved = resolved_sha256sums_target is not None
                    if resolved_sha256sums_target is not None:
                        sha256sums_file_target = str(resolved_sha256sums_target)
                        sha256sums_file_target_exists = resolved_sha256sums_target.is_file()
                    else:
                        sha256sums_file_target_exists = False
                    (
                        _canonical_anchor,
                        canonical_integrity_anchor_exists,
                        sha256sums_file_targets_canonical_integrity_anchor,
                    ) = _assess_attestation_target_binding_to_canonical_integrity_anchor(
                        resolved_sha256sums_target, target
                    )

                    if attestation_slice_id_matches_manifest is False:
                        missing_requirements.append("slice_id_matches_manifest")
                    if not sha256sums_file_reference_resolved:
                        missing_requirements.append("sha256sums_file_reference_resolved")
                    elif not sha256sums_file_target_exists:
                        missing_requirements.append("sha256sums_file_target_exists")
                    elif (
                        canonical_integrity_anchor_exists
                        and sha256sums_file_targets_canonical_integrity_anchor is False
                    ):
                        missing_requirements.append(
                            "sha256sums_file_targets_canonical_integrity_anchor"
                        )

                    if missing_requirements:
                        if "slice_id_matches_manifest" in missing_requirements:
                            status = "slice_id_mismatch"
                        elif "sha256sums_file_reference_resolved" in missing_requirements:
                            status = "sha256sums_file_reference_unresolvable"
                        elif (
                            "sha256sums_file_targets_canonical_integrity_anchor"
                            in missing_requirements
                        ):
                            status = "sha256sums_file_target_noncanonical"
                        else:
                            status = "sha256sums_file_target_missing"

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "attestation_matches": attestation_matches,
                "attestation_file": attestation_file,
                "attestation_readable_utf8": attestation_readable_utf8,
                "attestation_slice_id": attestation_slice_id,
                "attestation_slice_id_matches_manifest": attestation_slice_id_matches_manifest,
                "attestation_sha256sums_file": attestation_sha256sums_file,
                "sha256sums_file_reference_resolved": sha256sums_file_reference_resolved,
                "sha256sums_file_target": sha256sums_file_target,
                "sha256sums_file_target_exists": sha256sums_file_target_exists,
                "canonical_integrity_anchor": canonical_integrity_anchor,
                "canonical_integrity_anchor_exists": canonical_integrity_anchor_exists,
                "sha256sums_file_targets_canonical_integrity_anchor": (
                    sha256sums_file_targets_canonical_integrity_anchor
                ),
                "missing_requirements": sorted(set(missing_requirements)),
                "status": status,
            }
        )

    checked_count = len(entries)
    consistent_count = sum(1 for e in entries if e["status"] == "ok")
    inconsistency_count = sum(
        1
        for e in entries
        if e["status"]
        in {
            "missing_attestation",
            "multiple_attestations",
            "slice_id_mismatch",
            "sha256sums_file_reference_unresolvable",
            "sha256sums_file_target_missing",
            "sha256sums_file_target_noncanonical",
        }
    )
    input_error_count = checked_count - consistent_count - inconsistency_count
    ok = inconsistency_count == 0 and input_error_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-attestation-consistency",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "consistent_count": consistent_count,
            "inconsistency_count": inconsistency_count,
            "input_error_count": input_error_count,
            "entries": entries,
        }
    )
    if ok:
        return EXIT_VALIDATION_OK
    if input_error_count > 0:
        return EXIT_INPUT
    return EXIT_VALIDATION_FAILED


def _cmd_check_evidence_attestation_readiness(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        if sl.evidence is None:
            continue

        rel = sl.evidence.relative_dir
        target = repo_root / rel
        exists = target.exists()
        is_dir = target.is_dir()
        status = "ok"
        input_error = False
        missing_requirements: list[str] = []
        attestation_matches: list[str] = []
        attestation_file: str | None = None
        attestation_present = False
        attestation_readable_utf8: bool | None = None
        attestation_contract_valid: bool | None = None
        attestation_slice_id: str | None = None
        attestation_slice_id_matches_manifest: bool | None = None
        attestation_sha256sums_file: str | None = None
        sha256sums_file_reference_resolved: bool | None = None
        sha256sums_file_target: str | None = None
        sha256sums_file_target_exists: bool | None = None
        canonical_integrity_anchor = str(_canonical_integrity_anchor_path(target))
        canonical_integrity_anchor_exists = False
        sha256sums_file_targets_canonical_integrity_anchor: bool | None = None
        contract_details: dict[str, object] = {
            "checked_file": None,
            "required_keys": list(_ATTESTATION_REQUIRED_KEYS),
            "missing_keys": [],
            "empty_keys": [],
            "parsed_keys": [],
            "readable_utf8": False,
            "non_empty": False,
            "attested_at_utc_iso8601_like": False,
            "sha256sums_file_valid": False,
            "slice_id_matches_manifest": False,
            "canonical_integrity_anchor": canonical_integrity_anchor,
            "canonical_integrity_anchor_exists": False,
            "sha256sums_file_reference_resolved": None,
            "sha256sums_file_target": None,
            "sha256sums_file_target_exists": None,
            "sha256sums_file_targets_canonical_integrity_anchor": None,
            "parse_mode": "key_value",
        }

        if not exists:
            status = "missing_path"
            input_error = True
            missing_requirements = ["evidence_directory"]
        elif not is_dir:
            status = "not_a_directory"
            input_error = True
            missing_requirements = ["evidence_directory"]
        else:
            try:
                attestation_matches = sorted(
                    p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
                )
            except OSError as exc:
                _emit_json(
                    {
                        "ok": False,
                        "error": "input",
                        "reason": "evidence_read_failed",
                        "message": str(exc),
                    }
                )
                return EXIT_INPUT

            attestation_present = bool(attestation_matches)
            if not attestation_present:
                status = "missing_attestation"
                missing_requirements = ["attestation_file"]
            elif len(attestation_matches) > 1:
                status = "multiple_attestations"
                missing_requirements = ["attestation_uniqueness"]
            else:
                attestation_file = attestation_matches[0]
                contract_details["checked_file"] = attestation_file
                attestation_path = target / attestation_file
                try:
                    text = attestation_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    status = "unreadable_attestation"
                    input_error = True
                    attestation_readable_utf8 = False
                    missing_requirements = ["attestation_utf8_readable"]
                else:
                    attestation_readable_utf8 = True
                    contract_details["readable_utf8"] = True
                    contract_details["non_empty"] = bool(text.strip())
                    fields = _parse_attestation_key_values(text)
                    contract_details["parsed_keys"] = sorted(fields.keys())

                    missing_keys: list[str] = []
                    empty_keys: list[str] = []
                    for key in _ATTESTATION_REQUIRED_KEYS:
                        if key not in fields:
                            missing_keys.append(key)
                        elif not fields[key].strip():
                            empty_keys.append(key)

                    attested_at_utc = fields.get("attested_at_utc", "")
                    attestation_slice_id = fields.get("slice_id")
                    attestation_sha256sums_file = fields.get("sha256sums_file")
                    iso_like = bool(_ATTESTED_AT_UTC_ISO8601_LIKE_RE.fullmatch(attested_at_utc))
                    sha_ref_ok = _looks_like_sha256sums_file_reference(
                        attestation_sha256sums_file or ""
                    )

                    contract_details["missing_keys"] = missing_keys
                    contract_details["empty_keys"] = empty_keys
                    contract_details["attested_at_utc_iso8601_like"] = iso_like
                    contract_details["sha256sums_file_valid"] = sha_ref_ok

                    attestation_contract_valid = bool(contract_details["non_empty"]) and not (
                        missing_keys or empty_keys
                    )
                    attestation_contract_valid = (
                        attestation_contract_valid and iso_like and sha_ref_ok
                    )

                    if not attestation_contract_valid:
                        status = "invalid_attestation_contract"
                        if not contract_details["non_empty"]:
                            missing_requirements.append("attestation_non_empty")
                        missing_requirements.extend(missing_keys)
                        missing_requirements.extend(f"{key}_non_empty" for key in empty_keys)
                        if not iso_like:
                            missing_requirements.append("attested_at_utc_iso8601_like")
                        if not sha_ref_ok:
                            missing_requirements.append("sha256sums_file_reference")
                    else:
                        attestation_slice_id_matches_manifest = (
                            attestation_slice_id == sl.slice_id
                            if attestation_slice_id is not None
                            else False
                        )
                        contract_details["slice_id_matches_manifest"] = (
                            attestation_slice_id_matches_manifest
                        )
                        if not attestation_slice_id_matches_manifest:
                            status = "slice_id_mismatch"
                            missing_requirements.append("slice_id_matches_manifest")
                        else:
                            resolved_sha256sums_target: Path | None = None
                            if attestation_sha256sums_file is not None:
                                resolved_sha256sums_target = _resolve_hashed_file_path(
                                    attestation_sha256sums_file, repo_root, target
                                )
                            sha256sums_file_reference_resolved = (
                                resolved_sha256sums_target is not None
                            )
                            if resolved_sha256sums_target is not None:
                                sha256sums_file_target = str(resolved_sha256sums_target)
                                sha256sums_file_target_exists = resolved_sha256sums_target.is_file()
                            else:
                                sha256sums_file_target_exists = False
                            contract_details["sha256sums_file_reference_resolved"] = (
                                sha256sums_file_reference_resolved
                            )
                            contract_details["sha256sums_file_target"] = sha256sums_file_target
                            contract_details["sha256sums_file_target_exists"] = (
                                sha256sums_file_target_exists
                            )
                            (
                                _canonical_anchor,
                                canonical_integrity_anchor_exists,
                                sha256sums_file_targets_canonical_integrity_anchor,
                            ) = _assess_attestation_target_binding_to_canonical_integrity_anchor(
                                resolved_sha256sums_target, target
                            )
                            contract_details["canonical_integrity_anchor_exists"] = (
                                canonical_integrity_anchor_exists
                            )
                            contract_details[
                                "sha256sums_file_targets_canonical_integrity_anchor"
                            ] = sha256sums_file_targets_canonical_integrity_anchor

                            if not sha256sums_file_reference_resolved:
                                status = "sha256sums_file_reference_unresolvable"
                                missing_requirements.append("sha256sums_file_reference_resolved")
                            elif not sha256sums_file_target_exists:
                                status = "sha256sums_file_target_missing"
                                missing_requirements.append("sha256sums_file_target_exists")
                            elif (
                                canonical_integrity_anchor_exists
                                and sha256sums_file_targets_canonical_integrity_anchor is False
                            ):
                                status = "sha256sums_file_target_noncanonical"
                                missing_requirements.append(
                                    "sha256sums_file_targets_canonical_integrity_anchor"
                                )

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": rel,
                "exists": exists,
                "is_dir": is_dir,
                "attestation_present": attestation_present,
                "attestation_matches": attestation_matches,
                "attestation_file": attestation_file,
                "attestation_readable_utf8": attestation_readable_utf8,
                "attestation_contract_valid": attestation_contract_valid,
                "attestation_slice_id": attestation_slice_id,
                "attestation_slice_id_matches_manifest": attestation_slice_id_matches_manifest,
                "attestation_sha256sums_file": attestation_sha256sums_file,
                "sha256sums_file_reference_resolved": sha256sums_file_reference_resolved,
                "sha256sums_file_target": sha256sums_file_target,
                "sha256sums_file_target_exists": sha256sums_file_target_exists,
                "canonical_integrity_anchor": canonical_integrity_anchor,
                "canonical_integrity_anchor_exists": canonical_integrity_anchor_exists,
                "sha256sums_file_targets_canonical_integrity_anchor": (
                    sha256sums_file_targets_canonical_integrity_anchor
                ),
                "missing_requirements": sorted(set(missing_requirements)),
                "contract_details": contract_details,
                "status": status,
                "ready": status == "ok",
                "input_error": input_error,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["ready"])
    not_ready_count = checked_count - ready_count
    input_error_count = sum(1 for e in entries if e["input_error"])
    domain_not_ready_count = not_ready_count - input_error_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-attestation-readiness",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "domain_not_ready_count": domain_not_ready_count,
            "input_error_count": input_error_count,
            "entries": entries,
        }
    )
    if ok:
        return EXIT_VALIDATION_OK
    if input_error_count > 0:
        return EXIT_INPUT
    return EXIT_VALIDATION_FAILED


def _assess_attestation_uniqueness_entry(
    *,
    slice_id: str | None,
    evidence: str,
    target: Path,
    repo_root_resolved: str,
) -> tuple[dict[str, object] | None, int | None]:
    resolved_path = str(target.resolve())
    exists = target.exists()
    is_dir = target.is_dir()
    status = "ok"
    attestation_matches: list[str] = []

    if not exists:
        status = "missing_path"
    elif not is_dir:
        status = "not_a_directory"
    else:
        try:
            attestation_matches = sorted(
                p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
            )
        except OSError as exc:
            _emit_json(
                {
                    "ok": False,
                    "error": "input",
                    "reason": "evidence_read_failed",
                    "message": str(exc),
                }
            )
            return None, EXIT_INPUT

        if not attestation_matches:
            status = "missing_attestation"
        elif len(attestation_matches) > 1:
            status = "multiple_attestations"

    return (
        {
            "slice_id": slice_id,
            "evidence": evidence,
            "status": status,
            "attestation_matches": attestation_matches,
            "attestation_count": len(attestation_matches),
            "repo_root": repo_root_resolved,
            "resolved_path": resolved_path,
            "exists": exists,
            "is_dir": is_dir,
        },
        None,
    )


def _assess_manifest_or_target_mode(manifest_or_target: Path) -> str:
    if manifest_or_target.is_dir():
        return "target"
    # File paths are treated as manifest mode only for explicit JSON manifests.
    if manifest_or_target.is_file() and manifest_or_target.suffix.lower() == ".json":
        return "manifest"
    if manifest_or_target.suffix.lower() == ".json":
        return "manifest"
    return "target"


def _cmd_check_evidence_attestation_uniqueness(manifest_or_target: Path) -> int:
    mode = _assess_manifest_or_target_mode(manifest_or_target)
    repo_root = _find_peak_trade_repo_root(manifest_or_target)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest-or-target path)"
                ),
            }
        )
        return EXIT_INPUT

    repo_root_resolved = str(repo_root.resolve())
    entries: list[dict[str, object]] = []
    manifest_path: str | None = None
    target_path: str | None = None
    total_slices = 1
    if mode == "manifest":
        m, error_exit = _read_manifest_with_contract(manifest_or_target)
        if error_exit is not None:
            return error_exit

        assert m is not None
        manifest_path = str(manifest_or_target.resolve())
        total_slices = len(m.slices)
        for sl in m.slices:
            if sl.evidence is None:
                continue

            rel = sl.evidence.relative_dir
            entry, input_exit = _assess_attestation_uniqueness_entry(
                slice_id=sl.slice_id,
                evidence=rel,
                target=repo_root / rel,
                repo_root_resolved=repo_root_resolved,
            )
            if input_exit is not None:
                return input_exit
            assert entry is not None
            entries.append(entry)
    else:
        if manifest_or_target.is_absolute():
            evidence_target = manifest_or_target
        else:
            evidence_target = repo_root / manifest_or_target
        target_path = str(evidence_target.resolve())
        try:
            evidence_display = str(evidence_target.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            evidence_display = str(manifest_or_target)
        entry, input_exit = _assess_attestation_uniqueness_entry(
            slice_id=None,
            evidence=evidence_display,
            target=evidence_target,
            repo_root_resolved=repo_root_resolved,
        )
        if input_exit is not None:
            return input_exit
        assert entry is not None
        entries.append(entry)

    summary = {
        "total_slices": total_slices,
        "checked_slices": len(entries),
        "ok_slices": sum(1 for e in entries if e["status"] == "ok"),
        "missing_attestation_slices": sum(
            1 for e in entries if e["status"] == "missing_attestation"
        ),
        "multiple_attestations_slices": sum(
            1 for e in entries if e["status"] == "multiple_attestations"
        ),
        "missing_path_slices": sum(1 for e in entries if e["status"] == "missing_path"),
        "not_a_directory_slices": sum(1 for e in entries if e["status"] == "not_a_directory"),
    }
    ok = (
        summary["missing_attestation_slices"] == 0
        and summary["multiple_attestations_slices"] == 0
        and summary["missing_path_slices"] == 0
        and summary["not_a_directory_slices"] == 0
    )

    _emit_json(
        {
            "ok": ok,
            "schema": LevelUpManifestV0().schema_version,
            "command": "check-evidence-attestation-uniqueness",
            "mode": mode,
            "manifest_path": manifest_path,
            "target_path": target_path,
            "summary": summary,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _assess_attestation_integrity_entry(
    *,
    slice_id: str | None,
    evidence: str,
    target: Path,
    repo_root: Path,
    repo_root_resolved: str,
) -> tuple[dict[str, object] | None, int | None]:
    resolved_path = str(target.resolve())
    exists = target.exists()
    is_dir = target.is_dir()
    status = "ok"
    attestation_matches: list[str] = []
    sha256sums_file: str | None = None
    resolved_sha256sums_path: str | None = None

    if not exists:
        status = "missing_path"
    elif not is_dir:
        status = "not_a_directory"
    else:
        try:
            attestation_matches = sorted(
                p.name for p in target.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
            )
        except OSError as exc:
            _emit_json(
                {
                    "ok": False,
                    "error": "input",
                    "reason": "evidence_read_failed",
                    "message": str(exc),
                }
            )
            return None, EXIT_INPUT

        if not attestation_matches:
            status = "missing_attestation"
        elif len(attestation_matches) > 1:
            status = "multiple_attestations"
        else:
            attestation_path = target / attestation_matches[0]
            try:
                text = attestation_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                _emit_json(
                    {
                        "ok": False,
                        "error": "input",
                        "reason": "attestation_read_failed",
                        "message": str(exc),
                    }
                )
                return None, EXIT_INPUT

            fields = _parse_attestation_key_values(text)
            sha256sums_file = fields.get("sha256sums_file")
            resolved_sha256sums_target: Path | None = None
            if sha256sums_file:
                resolved_sha256sums_target = _resolve_hashed_file_path(
                    sha256sums_file, repo_root, target
                )
            if resolved_sha256sums_target is not None:
                resolved_sha256sums_path = str(resolved_sha256sums_target)

            canonical_anchor = _canonical_integrity_anchor_path(target)
            if resolved_sha256sums_target is None or not resolved_sha256sums_target.is_file():
                status = "missing_sha256sums_file"
            elif resolved_sha256sums_target.resolve() != canonical_anchor:
                status = "sha256sums_file_target_noncanonical"
            else:
                records, invalid_sha256sums_format = _parse_sha256sums_records(
                    resolved_sha256sums_target, repo_root, target
                )
                if invalid_sha256sums_format:
                    status = "invalid_sha256sums_format"
                else:
                    for rec in records:
                        expected_sha256 = str(rec["expected_sha256"])
                        target_path = rec["target_path"]
                        assert isinstance(target_path, Path)

                        if not target_path.is_file():
                            status = "sha256_mismatch"
                            break
                        try:
                            actual_sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
                        except OSError as exc:
                            _emit_json(
                                {
                                    "ok": False,
                                    "error": "input",
                                    "reason": "evidence_read_failed",
                                    "message": str(exc),
                                }
                            )
                            return None, EXIT_INPUT
                        if actual_sha256 != expected_sha256:
                            status = "sha256_mismatch"
                            break

    return (
        {
            "slice_id": slice_id,
            "evidence": evidence,
            "status": status,
            "attestation_matches": attestation_matches,
            "attestation_count": len(attestation_matches),
            "sha256sums_file": sha256sums_file,
            "resolved_sha256sums_path": resolved_sha256sums_path,
            "repo_root": repo_root_resolved,
            "resolved_path": resolved_path,
            "exists": exists,
            "is_dir": is_dir,
        },
        None,
    )


def _cmd_check_evidence_attestation_integrity(manifest_or_target: Path) -> int:
    mode = _assess_manifest_or_target_mode(manifest_or_target)
    repo_root = _find_peak_trade_repo_root(manifest_or_target)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest-or-target path)"
                ),
            }
        )
        return EXIT_INPUT

    repo_root_resolved = str(repo_root.resolve())
    entries: list[dict[str, object]] = []
    manifest_path: str | None = None
    target_path: str | None = None
    total_slices = 1
    if mode == "manifest":
        m, error_exit = _read_manifest_with_contract(manifest_or_target)
        if error_exit is not None:
            return error_exit

        assert m is not None
        manifest_path = str(manifest_or_target.resolve())
        total_slices = len(m.slices)
        for sl in m.slices:
            if sl.evidence is None:
                continue

            rel = sl.evidence.relative_dir
            entry, input_exit = _assess_attestation_integrity_entry(
                slice_id=sl.slice_id,
                evidence=rel,
                target=repo_root / rel,
                repo_root=repo_root,
                repo_root_resolved=repo_root_resolved,
            )
            if input_exit is not None:
                return input_exit
            assert entry is not None
            entries.append(entry)
    else:
        if manifest_or_target.is_absolute():
            evidence_target = manifest_or_target
        else:
            evidence_target = repo_root / manifest_or_target
        target_path = str(evidence_target.resolve())
        try:
            evidence_display = str(evidence_target.resolve().relative_to(repo_root.resolve()))
        except ValueError:
            evidence_display = str(manifest_or_target)
        entry, input_exit = _assess_attestation_integrity_entry(
            slice_id=None,
            evidence=evidence_display,
            target=evidence_target,
            repo_root=repo_root,
            repo_root_resolved=repo_root_resolved,
        )
        if input_exit is not None:
            return input_exit
        assert entry is not None
        entries.append(entry)

    summary = {
        "total_slices": total_slices,
        "checked_slices": len(entries),
        "ok_slices": sum(1 for e in entries if e["status"] == "ok"),
        "missing_attestation_slices": sum(
            1 for e in entries if e["status"] == "missing_attestation"
        ),
        "multiple_attestations_slices": sum(
            1 for e in entries if e["status"] == "multiple_attestations"
        ),
        "missing_path_slices": sum(1 for e in entries if e["status"] == "missing_path"),
        "not_a_directory_slices": sum(1 for e in entries if e["status"] == "not_a_directory"),
        "missing_sha256sums_file_slices": sum(
            1 for e in entries if e["status"] == "missing_sha256sums_file"
        ),
        "noncanonical_target_slices": sum(
            1 for e in entries if e["status"] == "sha256sums_file_target_noncanonical"
        ),
        "invalid_sha256sums_format_slices": sum(
            1 for e in entries if e["status"] == "invalid_sha256sums_format"
        ),
        "sha256_mismatch_slices": sum(1 for e in entries if e["status"] == "sha256_mismatch"),
    }
    ok = (
        summary["missing_attestation_slices"] == 0
        and summary["multiple_attestations_slices"] == 0
        and summary["missing_path_slices"] == 0
        and summary["not_a_directory_slices"] == 0
        and summary["missing_sha256sums_file_slices"] == 0
        and summary["noncanonical_target_slices"] == 0
        and summary["invalid_sha256sums_format_slices"] == 0
        and summary["sha256_mismatch_slices"] == 0
    )

    _emit_json(
        {
            "ok": ok,
            "schema": LevelUpManifestV0().schema_version,
            "command": "check-evidence-attestation-integrity",
            "mode": mode,
            "manifest_path": manifest_path,
            "target_path": target_path,
            "summary": summary,
            "entries": entries,
        }
    )
    return EXIT_VALIDATION_OK if ok else EXIT_VALIDATION_FAILED


def _assess_bundle_domain(
    evidence_dir: Path, *, has_evidence: bool, path_ready: bool
) -> dict[str, object]:
    base = {
        "required_checks": [],
        "missing_requirements": [],
    }
    if not has_evidence:
        return {
            **base,
            "status": "skipped_missing_evidence",
            "ready": False,
            "input_error": False,
        }
    if not path_ready:
        return {
            **base,
            "status": "skipped_path_error",
            "ready": False,
            "input_error": False,
        }

    sha256_ok = (evidence_dir / _BUNDLE_REQUIREMENT_FILE_SHA256SUMS).is_file()
    try:
        bundle_count = sum(1 for _ in evidence_dir.glob(_BUNDLE_REQUIREMENT_GLOB_BUNDLE))
        summary_count = sum(1 for _ in evidence_dir.glob(_BUNDLE_REQUIREMENT_GLOB_SUMMARY))
    except OSError:
        return {
            **base,
            "status": "evidence_read_failed",
            "ready": False,
            "input_error": True,
        }
    required_checks = [
        {
            "requirement": "sha256sums_txt",
            "pattern": _BUNDLE_REQUIREMENT_FILE_SHA256SUMS,
            "ok": sha256_ok,
        },
        {
            "requirement": "bundle_archive",
            "pattern": _BUNDLE_REQUIREMENT_GLOB_BUNDLE,
            "min_count": 1,
            "match_count": bundle_count,
            "ok": bundle_count >= 1,
        },
        {
            "requirement": "crawler_summary_1line",
            "pattern": _BUNDLE_REQUIREMENT_GLOB_SUMMARY,
            "min_count": 1,
            "match_count": summary_count,
            "ok": summary_count >= 1,
        },
    ]
    missing_requirements = [c["requirement"] for c in required_checks if not c["ok"]]
    status = "ok" if not missing_requirements else "missing_bundle_requirements"
    return {
        "required_checks": required_checks,
        "missing_requirements": missing_requirements,
        "status": status,
        "ready": status == "ok",
        "input_error": False,
    }


def _assess_integrity_domain(
    evidence_dir: Path, repo_root: Path, *, has_evidence: bool, path_ready: bool
) -> dict[str, object]:
    base = {
        "checked_files": 0,
        "missing_requirements": [],
        "failed_files": [],
    }
    if not has_evidence:
        return {
            **base,
            "status": "skipped_missing_evidence",
            "ready": False,
            "input_error": False,
        }
    if not path_ready:
        return {
            **base,
            "status": "skipped_path_error",
            "ready": False,
            "input_error": False,
        }

    sha_file = evidence_dir / _BUNDLE_REQUIREMENT_FILE_SHA256SUMS
    if not sha_file.is_file():
        return {
            **base,
            "status": "missing_sha256sums",
            "missing_requirements": ["sha256sums_txt"],
            "ready": False,
            "input_error": False,
        }

    records, invalid_sha256sums_format = _parse_sha256sums_records(
        sha_file, repo_root, evidence_dir
    )
    if invalid_sha256sums_format:
        return {
            **base,
            "status": "invalid_sha256sums_format",
            "missing_requirements": ["sha256sums_format"],
            "ready": False,
            "input_error": False,
        }

    failed_files: list[dict[str, object]] = []
    for rec in records:
        expected_sha256 = str(rec["expected_sha256"])
        target_path = rec["target_path"]
        assert isinstance(target_path, Path)
        file_path = str(rec["path"])

        if not target_path.is_file():
            failed_files.append(
                {
                    "path": file_path,
                    "status": "missing_hashed_file",
                    "expected_sha256": expected_sha256,
                }
            )
            continue

        try:
            actual_sha256 = hashlib.sha256(target_path.read_bytes()).hexdigest()
        except OSError:
            return {
                **base,
                "status": "evidence_read_failed",
                "ready": False,
                "input_error": True,
            }

        if actual_sha256 != expected_sha256:
            failed_files.append(
                {
                    "path": file_path,
                    "status": "hash_mismatch",
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256,
                }
            )

    has_missing_hashed_file = any(f["status"] == "missing_hashed_file" for f in failed_files)
    has_hash_mismatch = any(f["status"] == "hash_mismatch" for f in failed_files)
    status = "ok"
    if has_missing_hashed_file:
        status = "missing_hashed_file"
    elif has_hash_mismatch:
        status = "hash_mismatch"

    return {
        "checked_files": len(records),
        "missing_requirements": [],
        "failed_files": failed_files,
        "status": status,
        "ready": status == "ok",
        "input_error": False,
    }


def _assess_attestation_readiness_domain(
    sl_slice_id: str,
    evidence_dir: Path,
    repo_root: Path,
    *,
    has_evidence: bool,
    path_ready: bool,
) -> dict[str, object]:
    contract_details: dict[str, object] = {
        "checked_file": None,
        "required_keys": list(_ATTESTATION_REQUIRED_KEYS),
        "missing_keys": [],
        "empty_keys": [],
        "parsed_keys": [],
        "readable_utf8": False,
        "non_empty": False,
        "attested_at_utc_iso8601_like": False,
        "sha256sums_file_valid": False,
        "slice_id_matches_manifest": False,
        "parse_mode": "key_value",
    }
    base = {
        "attestation_present": False,
        "attestation_matches": [],
        "attestation_file": None,
        "attestation_readable_utf8": None,
        "attestation_contract_valid": None,
        "attestation_slice_id": None,
        "attestation_slice_id_matches_manifest": None,
        "attestation_sha256sums_file": None,
        "sha256sums_file_reference_resolved": None,
        "sha256sums_file_target": None,
        "sha256sums_file_target_exists": None,
        "canonical_integrity_anchor": str(_canonical_integrity_anchor_path(evidence_dir)),
        "canonical_integrity_anchor_exists": False,
        "sha256sums_file_targets_canonical_integrity_anchor": None,
        "missing_requirements": [],
        "contract_details": contract_details,
    }
    if not has_evidence:
        return {
            **base,
            "status": "skipped_missing_evidence",
            "ready": False,
            "input_error": False,
        }
    if not path_ready:
        return {
            **base,
            "status": "skipped_path_error",
            "ready": False,
            "input_error": False,
        }

    try:
        attestation_matches = sorted(
            p.name for p in evidence_dir.glob(_ATTESTATION_REQUIREMENT_GLOB) if p.is_file()
        )
    except OSError:
        return {
            **base,
            "status": "evidence_read_failed",
            "ready": False,
            "input_error": True,
        }
    attestation_present = bool(attestation_matches)
    if not attestation_present:
        return {
            **base,
            "attestation_matches": attestation_matches,
            "status": "missing_attestation",
            "missing_requirements": ["attestation_file"],
            "ready": False,
            "input_error": False,
        }
    if len(attestation_matches) > 1:
        return {
            **base,
            "attestation_present": True,
            "attestation_matches": attestation_matches,
            "status": "multiple_attestations",
            "missing_requirements": ["attestation_uniqueness"],
            "ready": False,
            "input_error": False,
        }

    attestation_file = attestation_matches[0]
    contract_details["checked_file"] = attestation_file
    attestation_path = evidence_dir / attestation_file
    try:
        text = attestation_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {
            **base,
            "attestation_present": True,
            "attestation_matches": attestation_matches,
            "attestation_file": attestation_file,
            "attestation_readable_utf8": False,
            "status": "unreadable_attestation",
            "missing_requirements": ["attestation_utf8_readable"],
            "ready": False,
            "input_error": True,
        }

    contract_details["readable_utf8"] = True
    contract_details["non_empty"] = bool(text.strip())
    fields = _parse_attestation_key_values(text)
    contract_details["parsed_keys"] = sorted(fields.keys())
    missing_keys: list[str] = []
    empty_keys: list[str] = []
    for key in _ATTESTATION_REQUIRED_KEYS:
        if key not in fields:
            missing_keys.append(key)
        elif not fields[key].strip():
            empty_keys.append(key)

    attested_at_utc = fields.get("attested_at_utc", "")
    attestation_slice_id = fields.get("slice_id")
    attestation_sha256sums_file = fields.get("sha256sums_file")
    iso_like = bool(_ATTESTED_AT_UTC_ISO8601_LIKE_RE.fullmatch(attested_at_utc))
    sha_ref_ok = _looks_like_sha256sums_file_reference(attestation_sha256sums_file or "")
    contract_details["missing_keys"] = missing_keys
    contract_details["empty_keys"] = empty_keys
    contract_details["attested_at_utc_iso8601_like"] = iso_like
    contract_details["sha256sums_file_valid"] = sha_ref_ok

    attestation_contract_valid = bool(contract_details["non_empty"]) and not (
        missing_keys or empty_keys
    )
    attestation_contract_valid = attestation_contract_valid and iso_like and sha_ref_ok
    missing_requirements: list[str] = []
    status = "ok"
    attestation_slice_id_matches_manifest: bool | None = None
    sha256sums_file_reference_resolved: bool | None = None
    sha256sums_file_target: str | None = None
    sha256sums_file_target_exists: bool | None = None
    canonical_integrity_anchor_exists = False
    sha256sums_file_targets_canonical_integrity_anchor: bool | None = None

    if not attestation_contract_valid:
        status = "invalid_attestation_contract"
        if not contract_details["non_empty"]:
            missing_requirements.append("attestation_non_empty")
        missing_requirements.extend(missing_keys)
        missing_requirements.extend(f"{key}_non_empty" for key in empty_keys)
        if not iso_like:
            missing_requirements.append("attested_at_utc_iso8601_like")
        if not sha_ref_ok:
            missing_requirements.append("sha256sums_file_reference")
    else:
        attestation_slice_id_matches_manifest = (
            attestation_slice_id == sl_slice_id if attestation_slice_id is not None else False
        )
        contract_details["slice_id_matches_manifest"] = attestation_slice_id_matches_manifest
        if not attestation_slice_id_matches_manifest:
            status = "slice_id_mismatch"
            missing_requirements.append("slice_id_matches_manifest")
        else:
            resolved_sha256sums_target: Path | None = None
            if attestation_sha256sums_file is not None:
                resolved_sha256sums_target = _resolve_hashed_file_path(
                    attestation_sha256sums_file, repo_root, evidence_dir
                )
            sha256sums_file_reference_resolved = resolved_sha256sums_target is not None
            if resolved_sha256sums_target is not None:
                sha256sums_file_target = str(resolved_sha256sums_target)
                sha256sums_file_target_exists = resolved_sha256sums_target.is_file()
            else:
                sha256sums_file_target_exists = False
            (
                _canonical_anchor,
                canonical_integrity_anchor_exists,
                sha256sums_file_targets_canonical_integrity_anchor,
            ) = _assess_attestation_target_binding_to_canonical_integrity_anchor(
                resolved_sha256sums_target, evidence_dir
            )

            if not sha256sums_file_reference_resolved:
                status = "sha256sums_file_reference_unresolvable"
                missing_requirements.append("sha256sums_file_reference_resolved")
            elif not sha256sums_file_target_exists:
                status = "sha256sums_file_target_missing"
                missing_requirements.append("sha256sums_file_target_exists")
            elif (
                canonical_integrity_anchor_exists
                and sha256sums_file_targets_canonical_integrity_anchor is False
            ):
                status = "sha256sums_file_target_noncanonical"
                missing_requirements.append("sha256sums_file_targets_canonical_integrity_anchor")

    return {
        **base,
        "attestation_present": attestation_present,
        "attestation_matches": attestation_matches,
        "attestation_file": attestation_file,
        "attestation_readable_utf8": True,
        "attestation_contract_valid": attestation_contract_valid,
        "attestation_slice_id": attestation_slice_id,
        "attestation_slice_id_matches_manifest": attestation_slice_id_matches_manifest,
        "attestation_sha256sums_file": attestation_sha256sums_file,
        "sha256sums_file_reference_resolved": sha256sums_file_reference_resolved,
        "sha256sums_file_target": sha256sums_file_target,
        "sha256sums_file_target_exists": sha256sums_file_target_exists,
        "canonical_integrity_anchor_exists": canonical_integrity_anchor_exists,
        "sha256sums_file_targets_canonical_integrity_anchor": (
            sha256sums_file_targets_canonical_integrity_anchor
        ),
        "missing_requirements": sorted(set(missing_requirements)),
        "status": status,
        "ready": status == "ok",
        "input_error": False,
    }


def _cmd_check_evidence_readiness_overall(path: Path) -> int:
    m, error_exit = _read_manifest_with_contract(path)
    if error_exit is not None:
        return error_exit

    assert m is not None
    repo_root = _find_peak_trade_repo_root(path)
    if repo_root is None:
        _emit_json(
            {
                "ok": False,
                "error": "input",
                "reason": "repo_root_not_found",
                "message": (
                    "could not locate repository root (expected pyproject.toml and src/levelup/ "
                    "on the parent chain of the manifest path)"
                ),
            }
        )
        return EXIT_INPUT

    entries: list[dict[str, object]] = []
    for sl in m.slices:
        has_evidence = sl.evidence is not None and bool(sl.evidence.relative_dir.strip())
        evidence_rel = sl.evidence.relative_dir if sl.evidence is not None else None
        evidence_dir = repo_root / evidence_rel if evidence_rel is not None else repo_root

        exists: bool | None = None
        is_dir: bool | None = None
        coverage_status = "missing_evidence"
        coverage_input_error = False
        if has_evidence:
            try:
                exists = evidence_dir.exists()
                is_dir = evidence_dir.is_dir()
            except OSError:
                exists = None
                is_dir = None
                coverage_status = "path_stat_failed"
                coverage_input_error = True
            else:
                if not exists:
                    coverage_status = "missing_path"
                    coverage_input_error = True
                elif not is_dir:
                    coverage_status = "not_a_directory"
                    coverage_input_error = True
                else:
                    coverage_status = "ok"

        coverage_path = {
            "has_evidence": has_evidence,
            "evidence": evidence_rel,
            "exists": exists,
            "is_dir": is_dir,
            "status": coverage_status,
            "ready": coverage_status == "ok",
            "input_error": coverage_input_error,
        }
        path_ready = coverage_status == "ok"

        bundle = _assess_bundle_domain(
            evidence_dir, has_evidence=has_evidence, path_ready=path_ready
        )
        integrity = _assess_integrity_domain(
            evidence_dir, repo_root, has_evidence=has_evidence, path_ready=path_ready
        )
        attestation_readiness = _assess_attestation_readiness_domain(
            sl.slice_id,
            evidence_dir,
            repo_root,
            has_evidence=has_evidence,
            path_ready=path_ready,
        )

        domains = (coverage_path, bundle, integrity, attestation_readiness)
        input_error = any(bool(d["input_error"]) for d in domains)
        ready = all(bool(d["ready"]) for d in domains)
        if ready:
            final_status = "ok"
        elif input_error:
            final_status = next(str(d["status"]) for d in domains if bool(d["input_error"]))
        else:
            final_status = next(str(d["status"]) for d in domains if not bool(d["ready"]))

        entries.append(
            {
                "slice_id": sl.slice_id,
                "evidence": evidence_rel,
                "coverage_path": coverage_path,
                "bundle": bundle,
                "integrity": integrity,
                "attestation_readiness": attestation_readiness,
                "status": final_status,
                "ready": ready,
                "input_error": input_error,
            }
        )

    checked_count = len(entries)
    ready_count = sum(1 for e in entries if e["ready"])
    not_ready_count = checked_count - ready_count
    input_error_count = sum(1 for e in entries if e["input_error"])
    domain_not_ready_count = not_ready_count - input_error_count
    ok = not_ready_count == 0

    _emit_json(
        {
            "ok": ok,
            "schema": m.schema_version,
            "command": "check-evidence-readiness-overall",
            "manifest_path": str(path.resolve()),
            "checked_count": checked_count,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "domain_not_ready_count": domain_not_ready_count,
            "input_error_count": input_error_count,
            "entries": entries,
        }
    )
    if ok:
        return EXIT_VALIDATION_OK
    if input_error_count > 0:
        return EXIT_INPUT
    return EXIT_VALIDATION_FAILED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.levelup.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_val = sub.add_parser("validate", help="Validate a levelup manifest JSON file.")
    p_val.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_dump = sub.add_parser(
        "dump-empty",
        help="Write an empty v0 manifest (template) to the given path.",
    )
    p_dump.add_argument("manifest", type=Path, help="Output path")

    p_format = sub.add_parser(
        "format",
        help="Validate and canonically rewrite an existing v0 manifest in place.",
    )
    p_format.add_argument("manifest", type=Path, help="Path to existing manifest.json")

    p_check = sub.add_parser(
        "canonical-check",
        help="Validate a v0 manifest and check if it is already canonical (read-only).",
    )
    p_check.add_argument("manifest", type=Path, help="Path to existing manifest.json")

    sub.add_parser(
        "export-json-schema",
        help="Export the LevelUpManifestV0 JSON schema as one JSON object on stdout.",
    )

    p_desc = sub.add_parser(
        "describe-slice",
        help="Print one slice contract from a v0 manifest as one JSON object on stdout (read-only).",
    )
    p_desc.add_argument("manifest", type=Path, help="Path to manifest.json")
    p_desc.add_argument("slice_id", help="slice_id to resolve inside the manifest")

    p_list = sub.add_parser(
        "list-slices",
        help="List slice_id values from a v0 manifest as one JSON object on stdout (read-only).",
    )
    p_list.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev = sub.add_parser(
        "check-evidence",
        help=(
            "Verify repo-relative evidence directories for slices (read-only; one JSON line on stdout)."
        ),
    )
    p_ev.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_cov = sub.add_parser(
        "check-evidence-coverage",
        help=(
            "Check manifest evidence-field coverage for all slices (read-only; one JSON line on stdout)."
        ),
    )
    p_ev_cov.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_ready = sub.add_parser(
        "check-evidence-readiness",
        help=(
            "One-shot evidence readiness check (coverage + path integrity; read-only; one JSON line)."
        ),
    )
    p_ev_ready.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_bundle = sub.add_parser(
        "check-evidence-bundle",
        help=(
            "Check bundle artifact completeness for evidence directories (read-only; one JSON line)."
        ),
    )
    p_ev_bundle.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_integrity = sub.add_parser(
        "check-evidence-integrity",
        help=(
            "Check SHA256SUMS-backed evidence integrity for evidence directories "
            "(read-only; one JSON line)."
        ),
    )
    p_ev_integrity.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_attestation = sub.add_parser(
        "check-evidence-attestation",
        help=(
            "Check operator attestation file presence in evidence directories "
            "(read-only; one JSON line)."
        ),
    )
    p_ev_attestation.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_attestation_contract = sub.add_parser(
        "check-evidence-attestation-contract",
        help=(
            "Check minimal operator attestation content contract in evidence directories "
            "(read-only; one JSON line)."
        ),
    )
    p_ev_attestation_contract.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_attestation_consistency = sub.add_parser(
        "check-evidence-attestation-consistency",
        help=(
            "Check consistency across manifest evidence slice_id, attestation fields, and "
            "sha256sums_file target existence (read-only; one JSON line)."
        ),
    )
    p_ev_attestation_consistency.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_attestation_readiness = sub.add_parser(
        "check-evidence-attestation-readiness",
        help=(
            "Check combined attestation readiness (presence + minimal contract + consistency) "
            "for evidence directories (read-only; one JSON line)."
        ),
    )
    p_ev_attestation_readiness.add_argument("manifest", type=Path, help="Path to manifest.json")

    p_ev_attestation_uniqueness = sub.add_parser(
        "check-evidence-attestation-uniqueness",
        help=(
            "Check that each evidence directory has exactly one operator attestation file "
            "(read-only; one JSON line)."
        ),
    )
    p_ev_attestation_uniqueness.add_argument(
        "manifest_or_target",
        type=Path,
        help="Path to manifest.json or evidence target path.",
    )

    p_ev_attestation_integrity = sub.add_parser(
        "check-evidence-attestation-integrity",
        help=(
            "Check that attestation sha256sums_file points to canonical SHA256SUMS.txt "
            "and that referenced hashes are valid (read-only; one JSON line)."
        ),
    )
    p_ev_attestation_integrity.add_argument(
        "manifest_or_target",
        type=Path,
        help="Path to manifest.json or evidence target path.",
    )

    p_ev_readiness_overall = sub.add_parser(
        "check-evidence-readiness-overall",
        help=(
            "Check combined overall evidence readiness (coverage/path + bundle + integrity + "
            "attestation-readiness) for manifest slices (read-only; one JSON line)."
        ),
    )
    p_ev_readiness_overall.add_argument("manifest", type=Path, help="Path to manifest.json")

    args = parser.parse_args(argv)
    if args.cmd == "validate":
        return _cmd_validate(args.manifest)
    if args.cmd == "dump-empty":
        return _cmd_dump_empty(args.manifest)
    if args.cmd == "format":
        return _cmd_format(args.manifest)
    if args.cmd == "canonical-check":
        return _cmd_canonical_check(args.manifest)
    if args.cmd == "export-json-schema":
        return _cmd_export_json_schema()
    if args.cmd == "describe-slice":
        return _cmd_describe_slice(args.manifest, args.slice_id)
    if args.cmd == "list-slices":
        return _cmd_list_slices(args.manifest)
    if args.cmd == "check-evidence":
        return _cmd_check_evidence(args.manifest)
    if args.cmd == "check-evidence-coverage":
        return _cmd_check_evidence_coverage(args.manifest)
    if args.cmd == "check-evidence-readiness":
        return _cmd_check_evidence_readiness(args.manifest)
    if args.cmd == "check-evidence-bundle":
        return _cmd_check_evidence_bundle(args.manifest)
    if args.cmd == "check-evidence-integrity":
        return _cmd_check_evidence_integrity(args.manifest)
    if args.cmd == "check-evidence-attestation":
        return _cmd_check_evidence_attestation(args.manifest)
    if args.cmd == "check-evidence-attestation-contract":
        return _cmd_check_evidence_attestation_contract(args.manifest)
    if args.cmd == "check-evidence-attestation-consistency":
        return _cmd_check_evidence_attestation_consistency(args.manifest)
    if args.cmd == "check-evidence-attestation-readiness":
        return _cmd_check_evidence_attestation_readiness(args.manifest)
    if args.cmd == "check-evidence-attestation-uniqueness":
        return _cmd_check_evidence_attestation_uniqueness(args.manifest_or_target)
    if args.cmd == "check-evidence-attestation-integrity":
        return _cmd_check_evidence_attestation_integrity(args.manifest_or_target)
    if args.cmd == "check-evidence-readiness-overall":
        return _cmd_check_evidence_readiness_overall(args.manifest)
    return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
