#!/usr/bin/env python3
"""Shared primary evidence manifest helpers (Preflight §2a/§2a.1; non-authorizing).

Machine markers (stable literals for contract tests):

```
PRIMARY_EVIDENCE_SHARED_HELPER_V0=true
FUTURE_RUNS_REQUIRE_DURABLE_ARCHIVE_ROOT=true
TMP_ONLY_EVIDENCE_INVALID=true
MANIFEST_VERIFY_REQUIRED=true
CLOSEOUT_REFERENCE_REQUIRED=true
RUN_INCOMPLETE_WITHOUT_PRIMARY_EVIDENCE=true
EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
VALIDATE_DURABLE_PRIMARY_EVIDENCE_ROOT_V0=true
PRIMARY_EVIDENCE_RETENTION_HARD_GATE_EXTENSION_V0=true
VALIDATE_DURABLE_LIFECYCLE_CLOSEOUT_ROOT_V0=true
VALIDATE_ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_ROOT_V0=true
GAP2A1_PRIMARY_EVIDENCE_RETENTION_OPERATIVE_ENFORCEMENT_V0=true
COMPLETION_BLOCKED_UNTIL_RETENTION_VERIFIED=true
```
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    evaluate_wallclock_evidence_fields,
)

MANIFEST_FILENAME = "MANIFEST.sha256"

# Bounded observation durable run roots (Shadow/Testnet adapter parity; Preflight §2a.1).
BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS = (
    "RUN_METADATA.json",
    "review/REVIEW_RESULT.json",
    "wrapper_evidence/steps.jsonl",
    "wrapper_evidence/manifest.json",
    "logs/wrapper_stdout.log",
    "logs/wrapper_stderr.log",
    MANIFEST_FILENAME,
)

# Post-#4489 bounded Shadow closeout extends the shared bounded durable contract.
BOUNDED_SHADOW_DURABLE_RUN_REQUIRED_REL_PATHS: tuple[str, ...] = (
    *BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    WALLCLOCK_EVIDENCE_FILENAME,
)

# Post-#4493 bounded Testnet closeout extends the shared bounded durable contract.
BOUNDED_TESTNET_DURABLE_RUN_REQUIRED_REL_PATHS: tuple[str, ...] = (
    *BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
    WALLCLOCK_EVIDENCE_FILENAME,
)

# Paper bounded observation durable run roots (scheduler composition; Preflight §2a.1).
PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS = (
    "RUN_METADATA.json",
    "review/REVIEW_RESULT.json",
    "runtime_out/evidence_manifest.json",
    "logs/scheduler_stdout.log",
    "logs/scheduler_stderr.log",
    MANIFEST_FILENAME,
)

# Order-Capability offline dry-validation durable run roots (no network; non-authorizing).
ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_REQUIRED_REL_PATHS = (
    "RUN_METADATA.json",
    "ORDER_CAPABILITY_DRY_VALIDATION_RESULT.json",
    "CLOSEOUT.md",
    MANIFEST_FILENAME,
)

# Closeout filenames referenced by §2a.1 hard gate (index only; owners remain canonical).
KNOWN_CLOSEOUT_FILENAMES = (
    "scheduler_completion_closeout_v0.json",
    "supervisor_session_closeout_v0.json",
)

# Lifecycle / planning / remote closeout slices (Preflight §2a.1 extension v0).
MANIFEST_VERIFY_LOG_FILENAMES: tuple[str, ...] = (
    "MANIFEST_VERIFY.log",
    "LOCAL_MANIFEST_VERIFY.log",
)

MACHINE_SUMMARY_FILENAME = "MACHINE_SUMMARY.env"
RECOMMENDED_NEXT_STEP_FILENAME = "RECOMMENDED_NEXT_STEP.md"

# GAP2A1 operative retention bundle (durable archive outside /tmp; non-authorizing).
PRIMARY_EVIDENCE_RETENTION_BUNDLE_REQUIRED_REL_PATHS: tuple[str, ...] = (
    MACHINE_SUMMARY_FILENAME,
    RECOMMENDED_NEXT_STEP_FILENAME,
    MANIFEST_FILENAME,
)

_COMPLETION_SUCCESS_STATUSES = frozenset(
    {"SUCCESS", "success", "PASS", "pass", "COMPLETE", "complete"}
)

LIFECYCLE_CLOSEOUT_MARKER_SUFFIXES: tuple[str, ...] = (
    "_REPORT.md",
    "_READONLY.md",
    "_RECORD.md",
    "_MACHINE_LINES.txt",
    "CLOSEOUT.md",
)

LIFECYCLE_CLOSEOUT_CLASSIFICATION = "lifecycle_closeout_slice_v0"
FINAL_STOP_IDLE_CLOSEOUT_CLASSIFICATION = "final_stop_idle_lifecycle_closeout_v0"


def is_under_tmp(path: Path) -> bool:
    """Return True when path resolves under /tmp (including /private/tmp on macOS)."""
    try:
        resolved = path.resolve()
        for tmp_root in (Path("/tmp").resolve(), Path("/private/tmp").resolve()):
            if resolved == tmp_root or tmp_root in resolved.parents:
                return True
        return False
    except OSError:
        text = str(path)
        return text.startswith("/tmp") or text.startswith("/private/tmp")


def require_durable_archive_root(path: Path) -> tuple[bool, str]:
    """Fail closed when primary evidence root is missing or under /tmp."""
    if is_under_tmp(path):
        return False, "archive root must be outside /tmp"
    if not path.exists():
        return False, f"archive root missing: {path}"
    return True, ""


def write_manifest_sha256(root: Path) -> None:
    """Write MANIFEST.sha256 over all files under root (excluding the manifest itself)."""
    lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    manifest = root / MANIFEST_FILENAME
    manifest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def verify_manifest_sha256(root: Path) -> tuple[bool, str]:
    """Verify MANIFEST.sha256 against files under root. Fail closed on any mismatch."""
    manifest = root / MANIFEST_FILENAME
    if not manifest.is_file():
        return False, "MANIFEST.sha256 missing"
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            return False, f"invalid manifest line: {line!r}"
        digest, rel = parts
        path = root / rel
        if not path.is_file():
            return False, f"missing manifest entry: {rel}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            return False, f"checksum mismatch: {rel}"
    return True, ""


def finalize_primary_evidence_root(root: Path) -> tuple[bool, str]:
    """Write MANIFEST.sha256 then verify. Fail closed on verify failure."""
    write_manifest_sha256(root)
    return verify_manifest_sha256(root)


def write_manifest_verify_log(root: Path, *, verify_ok: bool, verify_msg: str = "") -> int:
    """Write MANIFEST_VERIFY.log with explicit MANIFEST_VERIFY_RC (U2b + template §6)."""
    rc = 0 if verify_ok else 1
    status = "OK" if verify_ok else "FAILED"
    body = (
        f"verify_ok={str(verify_ok).lower()}\n"
        f"message={verify_msg}\n"
        f"MANIFEST_VERIFY_RC={rc}\n"
        f"STATUS={status}\n"
    )
    (root / MANIFEST_VERIFY_LOG_FILENAMES[0]).write_text(body, encoding="utf-8")
    return rc


def finalize_durable_bundle_manifest(root: Path) -> tuple[int, str]:
    """Write MANIFEST.sha256, verify, persist MANIFEST_VERIFY.log with RC, re-hash."""
    write_manifest_sha256(root)
    verify_ok, verify_msg = verify_manifest_sha256(root)
    rc = write_manifest_verify_log(root, verify_ok=verify_ok, verify_msg=verify_msg)
    write_manifest_sha256(root)
    final_ok, final_msg = verify_manifest_sha256(root)
    if not final_ok:
        return 1, final_msg
    return rc, verify_msg


def validate_durable_primary_evidence_root(
    root: Path,
    *,
    required_rel_paths: tuple[str, ...] = BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS,
) -> tuple[bool, str, dict[str, Any]]:
    """Validate durable bounded-observation primary evidence root (Preflight §2a.1).

    Machine marker: ``VALIDATE_DURABLE_PRIMARY_EVIDENCE_ROOT_V0=true``
    """
    checks: dict[str, bool] = {}
    issues: list[str] = []

    ok, msg = require_durable_archive_root(root)
    checks["durable_root_outside_tmp"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    for rel in required_rel_paths:
        path = root / rel
        present = path.is_file()
        key = "required_" + rel.replace("/", "_").replace(".", "_")
        checks[key] = present
        if not present:
            issues.append(f"missing durable required file: {rel}")

    if WALLCLOCK_EVIDENCE_FILENAME in required_rel_paths:
        wallclock_path = root / WALLCLOCK_EVIDENCE_FILENAME
        if wallclock_path.is_file():
            try:
                wallclock_payload = json.loads(wallclock_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                msg = f"WALLCLOCK_EVIDENCE.json invalid: {exc}"
                checks["durable_wallclock_evidence_valid"] = False
                issues.append(msg)
            else:
                evaluation = evaluate_wallclock_evidence_fields(wallclock_payload)
                wallclock_valid = bool(evaluation.get("duration_evidence_valid"))
                checks["durable_wallclock_evidence_valid"] = wallclock_valid
                if not wallclock_valid:
                    reasons = evaluation.get("fail_reasons", [])
                    issues.append(f"WALLCLOCK_EVIDENCE.json failed validation: {reasons}")

    if issues:
        return False, issues[0], {"checks": checks, "issues": issues}

    ok, msg = verify_manifest_sha256(root)
    checks["manifest_sha256_verify"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    review_path = root / "review" / "REVIEW_RESULT.json"
    try:
        review_payload = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"review/REVIEW_RESULT.json invalid: {exc}"
        checks["durable_review_verdict_pass"] = False
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    review_pass = review_payload.get("verdict") == "PASS"
    checks["durable_review_verdict_pass"] = review_pass
    if not review_pass:
        msg = "review/REVIEW_RESULT.json verdict must be PASS"
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    return True, "", {"checks": checks, "issues": []}


def validate_order_capability_offline_durable_run_root(
    run_root: Path | str,
) -> tuple[bool, list[str]]:
    """Validate order-cap offline dry-validation durable run root.

    Machine marker: ``VALIDATE_ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_ROOT_V0=true``

    Does not require review/REVIEW_RESULT.json (offline contract lane).
    """
    root = Path(run_root)
    issues: list[str] = []

    ok, msg = require_durable_archive_root(root)
    if not ok:
        issues.append(msg)
        return False, issues

    for rel in ORDER_CAPABILITY_OFFLINE_DURABLE_RUN_REQUIRED_REL_PATHS:
        if not (root / rel).is_file():
            issues.append(f"missing durable required file: {rel}")

    if issues:
        return False, issues

    ok, msg = verify_manifest_sha256(root)
    if not ok:
        issues.append(msg)
        return False, issues

    return True, []


def parse_manifest_verify_log_rc(root: Path) -> tuple[int | None, str, str]:
    """Parse MANIFEST_VERIFY_RC from standard or LOCAL manifest verify logs."""
    for name in MANIFEST_VERIFY_LOG_FILENAMES:
        log_path = root / name
        if not log_path.is_file():
            continue
        text = log_path.read_text(encoding="utf-8")
        for raw in text.splitlines():
            line = raw.strip()
            if not line.startswith("MANIFEST_VERIFY_RC="):
                continue
            value = line.split("=", 1)[1].strip()
            try:
                return int(value), "", name
            except ValueError:
                return None, f"invalid MANIFEST_VERIFY_RC in {name}", name
        return None, f"MANIFEST_VERIFY_RC missing in {name}", name
    return None, "manifest verify log missing", ""


def _has_lifecycle_closeout_marker(root: Path) -> bool:
    for path in root.iterdir():
        if not path.is_file():
            continue
        if any(path.name.endswith(suffix) for suffix in LIFECYCLE_CLOSEOUT_MARKER_SUFFIXES):
            return True
    return False


def _has_final_stop_idle_marker(root: Path) -> bool:
    for path in root.iterdir():
        if not path.is_file():
            continue
        name = path.name
        upper = name.upper()
        if "STOP_IDLE" not in upper:
            continue
        if name.endswith(".md") or name.endswith("_MACHINE_LINES.txt"):
            return True
    return False


def validate_durable_lifecycle_closeout_root(
    root: Path,
    *,
    require_closeout_marker: bool = True,
    require_final_stop_idle_marker: bool = False,
) -> tuple[bool, str, dict[str, Any]]:
    """Validate durable lifecycle/planning/remote closeout slice root (§2a.1 extension v0).

    Machine marker: ``VALIDATE_DURABLE_LIFECYCLE_CLOSEOUT_ROOT_V0=true``

    Accepts ``MANIFEST_VERIFY.log`` or ``LOCAL_MANIFEST_VERIFY.log`` when RC=0.
    Nested subdirectory manifests are orthogonal; parent ``MANIFEST.sha256`` is canonical.
    """
    checks: dict[str, bool] = {}
    issues: list[str] = []
    classification = (
        FINAL_STOP_IDLE_CLOSEOUT_CLASSIFICATION
        if require_final_stop_idle_marker
        else LIFECYCLE_CLOSEOUT_CLASSIFICATION
    )

    ok, msg = require_durable_archive_root(root)
    checks["durable_root_outside_tmp"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues, "classification": classification}

    ok, msg = verify_manifest_sha256(root)
    checks["manifest_sha256_verify"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues, "classification": classification}

    rc, rc_msg, log_name = parse_manifest_verify_log_rc(root)
    checks["manifest_verify_log_present"] = bool(log_name)
    checks["manifest_verify_rc_zero"] = rc == 0
    if rc is None:
        issues.append(rc_msg)
        return False, rc_msg, {"checks": checks, "issues": issues, "classification": classification}
    if rc != 0:
        msg = f"manifest verify RC must be 0 (got {rc} in {log_name})"
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues, "classification": classification}

    if require_closeout_marker:
        has_marker = _has_lifecycle_closeout_marker(root)
        checks["closeout_marker_present"] = has_marker
        if not has_marker:
            msg = "lifecycle closeout marker artifact missing"
            issues.append(msg)
            return (
                False,
                msg,
                {"checks": checks, "issues": issues, "classification": classification},
            )

    if require_final_stop_idle_marker:
        has_stop_idle = _has_final_stop_idle_marker(root)
        checks["final_stop_idle_marker_present"] = has_stop_idle
        if not has_stop_idle:
            msg = "final stop-idle marker missing"
            issues.append(msg)
            return (
                False,
                msg,
                {"checks": checks, "issues": issues, "classification": classification},
            )

    return (
        True,
        "",
        {
            "checks": checks,
            "issues": [],
            "classification": classification,
            "manifest_verify_log": log_name,
        },
    )


def _parse_env_kv(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None


def validate_durable_primary_evidence_retention_bundle(
    root: Path,
    *,
    required_rel_paths: tuple[str, ...] = PRIMARY_EVIDENCE_RETENTION_BUNDLE_REQUIRED_REL_PATHS,
) -> tuple[bool, str, dict[str, Any]]:
    """Validate durable primary evidence retention bundle (GAP2A1 operative enforcement v0).

    Machine marker: ``GAP2A1_PRIMARY_EVIDENCE_RETENTION_OPERATIVE_ENFORCEMENT_V0=true``

    Fail-closed when root is /tmp-only, required artifacts are missing or empty,
    ``DURABLE_SAVE_CONFIRMED`` is not true, ``MANIFEST_VERIFY_RC`` is not 0, or
    ``MANIFEST.sha256`` verification fails.
    """
    checks: dict[str, bool] = {}
    issues: list[str] = []

    ok, msg = require_durable_archive_root(root)
    checks["durable_root_outside_tmp"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    for rel in required_rel_paths:
        path = root / rel
        present = path.is_file()
        key = "required_" + rel.replace("/", "_").replace(".", "_")
        checks[key] = present
        if not present:
            msg = f"missing primary evidence artifact: {rel}"
            issues.append(msg)
            return False, msg, {"checks": checks, "issues": issues}
        if path.stat().st_size == 0:
            msg = f"empty primary evidence artifact: {rel}"
            issues.append(msg)
            return False, msg, {"checks": checks, "issues": issues}

    machine_summary = root / MACHINE_SUMMARY_FILENAME
    if not machine_summary.read_text(encoding="utf-8").strip():
        msg = f"{MACHINE_SUMMARY_FILENAME} must not be empty"
        issues.append(msg)
        checks["machine_summary_nonempty"] = False
        return False, msg, {"checks": checks, "issues": issues}
    checks["machine_summary_nonempty"] = True

    recommended = root / RECOMMENDED_NEXT_STEP_FILENAME
    if not recommended.read_text(encoding="utf-8").strip():
        msg = f"{RECOMMENDED_NEXT_STEP_FILENAME} must not be empty"
        issues.append(msg)
        checks["recommended_next_step_nonempty"] = False
        return False, msg, {"checks": checks, "issues": issues}
    checks["recommended_next_step_nonempty"] = True

    durable_save = _parse_env_kv(machine_summary, "DURABLE_SAVE_CONFIRMED")
    checks["durable_save_confirmed_true"] = durable_save == "true"
    if durable_save != "true":
        msg = "DURABLE_SAVE_CONFIRMED must be true in MACHINE_SUMMARY.env"
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    rc_val = _parse_env_kv(machine_summary, "MANIFEST_VERIFY_RC")
    rc_int: int | None
    try:
        rc_int = int(rc_val) if rc_val is not None else None
    except ValueError:
        rc_int = None
    checks["manifest_verify_rc_zero"] = rc_int == 0
    if rc_int != 0:
        msg = f"MANIFEST_VERIFY_RC must be 0 in MACHINE_SUMMARY.env (got {rc_val!r})"
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    ok, msg = verify_manifest_sha256(root)
    checks["manifest_sha256_verify"] = ok
    if not ok:
        issues.append(msg)
        return False, msg, {"checks": checks, "issues": issues}

    return True, "", {"checks": checks, "issues": []}


def evaluate_completion_retention_gate(
    root: Path | None,
    *,
    completion_status: str,
    required_rel_paths: tuple[str, ...] = PRIMARY_EVIDENCE_RETENTION_BUNDLE_REQUIRED_REL_PATHS,
) -> tuple[str, str, dict[str, Any]]:
    """Fail-closed completion gate: SUCCESS blocked until retention bundle validates.

    Machine marker: ``COMPLETION_BLOCKED_UNTIL_RETENTION_VERIFIED=true``
    """
    if completion_status not in _COMPLETION_SUCCESS_STATUSES:
        return completion_status, "", {"retention_gate_applied": False}

    if root is None:
        return (
            "INCOMPLETE",
            "primary evidence root required before SUCCESS completion",
            {"retention_gate_applied": True},
        )

    ok, msg, detail = validate_durable_primary_evidence_retention_bundle(
        root,
        required_rel_paths=required_rel_paths,
    )
    detail = dict(detail)
    detail["retention_gate_applied"] = True
    if not ok:
        return "INCOMPLETE", msg, detail
    return completion_status, "", detail
