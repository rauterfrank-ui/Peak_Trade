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
```
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

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

# Paper bounded observation durable run roots (scheduler composition; Preflight §2a.1).
PAPER_BOUNDED_DURABLE_RUN_REQUIRED_REL_PATHS = (
    "RUN_METADATA.json",
    "review/REVIEW_RESULT.json",
    "runtime_out/evidence_manifest.json",
    "logs/scheduler_stdout.log",
    "logs/scheduler_stderr.log",
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
