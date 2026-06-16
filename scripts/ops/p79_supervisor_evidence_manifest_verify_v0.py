#!/usr/bin/env python3
"""Offline P79 archive manifest verification for supervisor evidence packs (non-authorizing)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.pack_online_readiness_supervisor_evidence_v0 import CLOSEOUT_FILENAME
from scripts.ops.primary_evidence_retention_v0 import MANIFEST_FILENAME, verify_manifest_sha256

GATE_EVIDENCE_FILENAME = "p79_health_gate_v1.json"
ARCHIVE_GATE_MODE = "archive_evidence_pack"


@dataclass
class ArchiveGateResult:
    archive_root: str
    closeout_path: str
    evidence_path: str
    gate_mode: str
    closeout_parse_ok: bool
    manifest_verified: bool
    evidence_non_authorizing: bool
    exit_code: int
    error: str = ""


def verify_supervisor_evidence_archive(archive_root: Path) -> ArchiveGateResult:
    """Validate packed supervisor evidence: closeout JSON + MANIFEST.sha256 via shared helper."""
    result = ArchiveGateResult(
        archive_root=str(archive_root),
        closeout_path=str(archive_root / CLOSEOUT_FILENAME),
        evidence_path=str(archive_root / GATE_EVIDENCE_FILENAME),
        gate_mode=ARCHIVE_GATE_MODE,
        closeout_parse_ok=False,
        manifest_verified=False,
        evidence_non_authorizing=True,
        exit_code=0,
    )

    if not archive_root.is_dir():
        result.exit_code = 1
        result.error = f"archive_root missing or not a directory: {archive_root}"
        return result

    closeout_path = archive_root / CLOSEOUT_FILENAME
    if not closeout_path.is_file():
        result.exit_code = 1
        result.error = f"{CLOSEOUT_FILENAME} missing"
        return result

    try:
        closeout = json.loads(closeout_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.exit_code = 1
        result.error = f"{CLOSEOUT_FILENAME} not parseable: {exc}"
        return result

    result.closeout_parse_ok = True

    if closeout.get("version") != "supervisor_session_closeout_v0":
        result.exit_code = 1
        result.error = "closeout version mismatch (expected supervisor_session_closeout_v0)"
        return result

    if closeout.get("exit_code", 0) != 0:
        result.exit_code = 1
        result.error = f"closeout records pack failure: {closeout.get('error') or 'unknown'}"
        return result

    if closeout.get("error"):
        result.exit_code = 1
        result.error = f"closeout records error: {closeout['error']}"
        return result

    manifest_path = archive_root / MANIFEST_FILENAME
    if not manifest_path.is_file():
        result.exit_code = 1
        result.error = f"{MANIFEST_FILENAME} missing"
        return result

    ok, msg = verify_manifest_sha256(archive_root)
    result.manifest_verified = ok
    if not ok:
        result.exit_code = 1
        result.error = f"manifest verify failed: {msg}"
        return result

    return result


def write_archive_gate_evidence(archive_root: Path, result: ArchiveGateResult) -> None:
    payload = {
        "version": "p79_health_gate_v1",
        "gate_mode": result.gate_mode,
        "ts_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "archive_root": result.archive_root,
        "closeout_path": result.closeout_path,
        "closeout_parse_ok": result.closeout_parse_ok,
        "manifest_verified": result.manifest_verified,
        "evidence_non_authorizing": result.evidence_non_authorizing,
        "overall_ok": result.exit_code == 0,
        "exit_code": result.exit_code,
        "error": result.error or None,
    }
    evidence_path = archive_root / GATE_EVIDENCE_FILENAME
    evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.evidence_path = str(evidence_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Offline P79 verification of supervisor evidence pack archive "
            "(closeout JSON + MANIFEST.sha256; non-authorizing)."
        ),
    )
    parser.add_argument(
        "--archive-root",
        required=True,
        type=Path,
        help="Packed supervisor evidence archive root from pack_online_readiness_supervisor_evidence_v0.py",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    result = verify_supervisor_evidence_archive(args.archive_root)
    write_archive_gate_evidence(args.archive_root, result)
    if result.error:
        print(f"P79_GATE_FAIL: {result.error}", file=sys.stderr)
        print(f"P79_ARCHIVE_GATE_RC=3")
        return 3

    print(f"P79_GATE_OK archive_root={result.archive_root} manifest_verified=true")
    print("P79_ARCHIVE_GATE_RC=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
