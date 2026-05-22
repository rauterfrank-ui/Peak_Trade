#!/usr/bin/env python3
"""Offline pack closeout for Online Readiness Supervisor/Daemon evidence (Preflight §2a; non-authorizing).

Operator-invoked after STOP. Does not start/stop supervisor, daemon, or launchctl.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import finalize_primary_evidence_root, is_under_tmp

CLOSEOUT_FILENAME = "supervisor_session_closeout_v0.json"
SUPERVISOR_SESSION_DIR = "supervisor_session"
SUPPORTING_DIR = "supporting"


@dataclass
class OptionalArtifactResult:
    source: str
    dest: str
    status: str
    reason: str = ""


@dataclass
class PackResult:
    out_dir: str
    archive_root: str
    closeout_path: str
    supervisor_session_dest: str
    optional_artifacts: list[OptionalArtifactResult] = field(default_factory=list)
    primary_evidence_enforce: bool = False
    manifest_verified: bool = False
    exit_code: int = 0
    error: str = ""


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _copy_file_or_tree(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
    else:
        shutil.copy2(source, dest)


def _copy_optional_artifact(source: Path, supporting_root: Path) -> OptionalArtifactResult:
    dest = supporting_root / source.name
    rel_dest = f"{SUPPORTING_DIR}/{source.name}"
    if not source.exists():
        return OptionalArtifactResult(
            source=str(source),
            dest=rel_dest,
            status="missing",
            reason="source path does not exist",
        )
    _copy_file_or_tree(source, dest)
    return OptionalArtifactResult(
        source=str(source),
        dest=rel_dest,
        status="copied",
    )


def pack_supervisor_evidence(
    *,
    out_dir: Path,
    archive_root: Path,
    optional_artifacts: Sequence[Path] = (),
    primary_evidence_enforce: bool = False,
    require_optional_artifacts: bool = False,
) -> PackResult:
    """Copy supervisor OUT_DIR and optional artifacts into archive_root; optional MANIFEST finalize."""
    result = PackResult(
        out_dir=str(out_dir),
        archive_root=str(archive_root),
        closeout_path=str(archive_root / CLOSEOUT_FILENAME),
        supervisor_session_dest=str(archive_root / SUPERVISOR_SESSION_DIR),
        primary_evidence_enforce=primary_evidence_enforce,
    )

    if not out_dir.is_dir():
        result.exit_code = 1
        result.error = f"out_dir missing or not a directory: {out_dir}"
        return result

    if primary_evidence_enforce and is_under_tmp(archive_root):
        result.exit_code = 1
        result.error = "archive_root must be outside /tmp when --primary-evidence-enforce is set"
        return result

    archive_root.mkdir(parents=True, exist_ok=True)
    session_dest = archive_root / SUPERVISOR_SESSION_DIR
    if session_dest.exists():
        shutil.rmtree(session_dest)
    shutil.copytree(out_dir, session_dest)

    supporting_root = archive_root / SUPPORTING_DIR
    supporting_root.mkdir(parents=True, exist_ok=True)
    for src in optional_artifacts:
        artifact = _copy_optional_artifact(src, supporting_root)
        result.optional_artifacts.append(artifact)
        if require_optional_artifacts and artifact.status == "missing":
            result.exit_code = 1
            result.error = f"required optional artifact missing: {src}"
            _write_closeout(archive_root, result)
            return result

    _write_closeout(archive_root, result)

    if primary_evidence_enforce:
        ok, msg = finalize_primary_evidence_root(archive_root)
        result.manifest_verified = ok
        if not ok:
            result.exit_code = 1
            result.error = f"primary evidence finalize failed: {msg}"
            _write_closeout(archive_root, result)
            return result

    return result


def _write_closeout(archive_root: Path, result: PackResult) -> None:
    payload = {
        "version": "supervisor_session_closeout_v0",
        "evidence_non_authorizing": True,
        "ts_utc": _utc_ts(),
        "out_dir": result.out_dir,
        "archive_root": result.archive_root,
        "supervisor_session_dest": result.supervisor_session_dest,
        "primary_evidence_enforce": result.primary_evidence_enforce,
        "manifest_verified": result.manifest_verified,
        "optional_artifacts": [
            {
                "source": a.source,
                "dest": a.dest,
                "status": a.status,
                "reason": a.reason,
            }
            for a in result.optional_artifacts
        ],
        "exit_code": result.exit_code,
        "error": result.error or None,
    }
    closeout = archive_root / CLOSEOUT_FILENAME
    closeout.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result.closeout_path = str(closeout)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Pack Online Readiness Supervisor/Daemon evidence into a durable archive "
            "(non-authorizing; operator-invoked after STOP)."
        ),
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Existing supervisor OUT_DIR under out/ops/ containing tick artifacts",
    )
    parser.add_argument(
        "--archive-root",
        required=True,
        type=Path,
        help="Durable destination root for packed evidence",
    )
    parser.add_argument(
        "--optional-artifact",
        action="append",
        default=[],
        type=Path,
        help="Optional pid/log/lock/stdout/stderr source path (repeatable)",
    )
    parser.add_argument(
        "--primary-evidence-enforce",
        action="store_true",
        help="Write and verify MANIFEST.sha256 via shared helper (archive-root outside /tmp)",
    )
    parser.add_argument(
        "--require-optional-artifacts",
        action="store_true",
        help="Fail closed when any --optional-artifact path is missing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(list(argv) if argv is not None else None)
    result = pack_supervisor_evidence(
        out_dir=args.out_dir,
        archive_root=args.archive_root,
        optional_artifacts=tuple(args.optional_artifact or []),
        primary_evidence_enforce=bool(args.primary_evidence_enforce),
        require_optional_artifacts=bool(args.require_optional_artifacts),
    )
    if result.error:
        print(f"ERR: {result.error}", file=sys.stderr)
    print(f"SUPERVISOR_EVIDENCE_PACK_RC={result.exit_code}")
    print(f"CLOSEOUT_PATH={result.closeout_path}")
    print(f"MANIFEST_VERIFIED={str(result.manifest_verified).lower()}")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
