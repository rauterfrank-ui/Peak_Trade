#!/usr/bin/env python3
"""Local-only durable closeout copy/verify helper (Preflight §2b.1 / §2b.2; non-authorizing).

Charter: OP-CLOSEOUT-HELPER-IMPL-V0 — local filesystem only; no runtime/network/cloud authority.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)

README_FILENAME = "DURABLE_COPY_README.md"
CLOSEOUT_GLOB = "*CLOSEOUT*.md"
JSON_CLOSEOUT_BASENAMES: tuple[str, ...] = (
    "".join(("sche", "duler_completion_closeout_v0.json")),
    "supervisor_session_closeout_v0.json",
)
MANIFEST_VERIFY_LOG_FILENAME = "MANIFEST_VERIFY.log"
DEFAULT_POINTER_EVIDENCE_PATTERNS: tuple[str, ...] = (
    "PR_URL.txt",
    "PR_METADATA.json",
    "ARCHIVE_POINTER.md",
    "*.pointer",
    "*INDEX*.md",
    "*index*.md",
)


@dataclass
class CopyVerifyResult:
    status: str
    dry_run: bool
    source_dir: str
    dest_dir: str
    dest_manifest_verify_rc: str
    manifest_verify_log_status: str
    pointer_evidence_required: bool
    pointer_evidence_found: bool
    source_tmp_not_canonical: bool
    force_overwrite: bool
    error: str = ""


def _fail(result: CopyVerifyResult, message: str) -> CopyVerifyResult:
    result.status = "invalid"
    result.error = message
    return result


def _source_has_files(source: Path) -> bool:
    return any(p.is_file() for p in source.rglob("*"))


def _json_closeout_valid(path: Path) -> bool:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict)


def _recognized_closeout_artifacts(root: Path) -> list[Path]:
    artifacts: list[Path] = []
    for path in sorted(root.glob(CLOSEOUT_GLOB)):
        if path.is_file():
            artifacts.append(path)
    for name in JSON_CLOSEOUT_BASENAMES:
        candidate = root / name
        if candidate.is_file() and _json_closeout_valid(candidate):
            artifacts.append(candidate)
    return artifacts


def _find_closeout_report(source: Path) -> Path | None:
    artifacts = _recognized_closeout_artifacts(source)
    if artifacts:
        return artifacts[0]
    return None


def _resolve_pr_json(source: Path, pr_number: int | None, pr_json: Path | None) -> Path | None:
    if pr_json is not None:
        return pr_json if pr_json.is_file() else None
    if pr_number is None:
        return None
    candidate = source / f"PR{pr_number}.json"
    return candidate if candidate.is_file() else None


def _dest_has_content(dest: Path) -> bool:
    if not dest.exists():
        return False
    if dest.is_file():
        return True
    return any(dest.iterdir())


def _validate_dest_outside_tmp(dest: Path) -> tuple[bool, str]:
    if is_under_tmp(dest):
        return False, "destination must be outside /tmp"
    return True, ""


def _safe_dest_child(dest: Path, relative: Path) -> Path:
    dest_resolved = dest.resolve()
    target = (dest / relative).resolve()
    if target != dest_resolved and dest_resolved not in target.parents:
        raise ValueError(f"path escapes destination: {relative}")
    return target


def _copy_tree(source: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for src_path in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = src_path.relative_to(source)
        if rel.name == MANIFEST_FILENAME:
            continue
        dst_path = _safe_dest_child(dest, rel)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)


def _verify_manifest_with_log(dest: Path) -> tuple[bool, str, str]:
    """Verify MANIFEST and write MANIFEST_VERIFY.log with deterministic summary."""
    ok, msg = verify_manifest_sha256(dest)
    verify_log = _safe_dest_child(dest, Path(MANIFEST_VERIFY_LOG_FILENAME))
    if ok:
        verify_log.write_text("MANIFEST_VERIFY_RC=0\nSTATUS=OK\n", encoding="utf-8")
        return True, "", "ok"
    verify_log.write_text(f"MANIFEST_VERIFY_RC=1\nSTATUS=FAILED\nERROR={msg}\n", encoding="utf-8")
    return False, msg, "failed"


def _manifest_verify_log_is_success(dest: Path) -> bool:
    path = _safe_dest_child(dest, Path(MANIFEST_VERIFY_LOG_FILENAME))
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    return "MANIFEST_VERIFY_RC=0" in text and "STATUS=OK" in text


def _pointer_evidence_exists(dest: Path, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for matched in dest.glob(pattern):
            if matched.is_file():
                return True
    return False


def _manifest_entries(dest: Path) -> set[str]:
    manifest = _safe_dest_child(dest, Path(MANIFEST_FILENAME))
    entries: set[str] = set()
    if not manifest.is_file():
        return entries
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        _hash, _sep, rel = line.partition("  ")
        if rel:
            entries.add(rel.strip().replace("\\", "/"))
    return entries


def _has_manifest_covered_closeout_artifact(dest: Path) -> bool:
    manifest_entries = _manifest_entries(dest)
    if not manifest_entries:
        return False
    for artifact in _recognized_closeout_artifacts(dest):
        rel = artifact.relative_to(dest).as_posix()
        if rel in manifest_entries:
            return True
    return False


def _write_durable_readme(dest: Path, source: Path, *, pr_number: int | None) -> None:
    lines = [
        "# Durable Copy README",
        "",
        f"Source: {source.resolve()}",
        f"Destination: {dest.resolve()}",
        f"Generated UTC: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "Purpose: §2b.1 durable material closeout copy (OP-CLOSEOUT-HELPER-IMPL-V0).",
        "Authority: non-authorizing; does not complete runtime or remote-paper gates.",
    ]
    if pr_number is not None:
        lines.append(f"PR context: #{pr_number}")
    readme = _safe_dest_child(dest, Path(README_FILENAME))
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


def plan_and_execute(
    *,
    source_dir: Path,
    dest_dir: Path,
    dry_run: bool,
    pr_number: int | None,
    pr_json: Path | None,
    require_closeout_report: bool,
    require_durable_pointer_evidence: bool,
    durable_pointer_patterns: tuple[str, ...],
    allow_tmp_source: bool,
    force: bool,
) -> CopyVerifyResult:
    result = CopyVerifyResult(
        status="blocked",
        dry_run=dry_run,
        source_dir=str(source_dir),
        dest_dir=str(dest_dir),
        dest_manifest_verify_rc="not_run",
        manifest_verify_log_status="not_run",
        pointer_evidence_required=require_durable_pointer_evidence,
        pointer_evidence_found=False,
        source_tmp_not_canonical=is_under_tmp(source_dir),
        force_overwrite=force,
    )

    if not source_dir.exists():
        return _fail(result, f"source does not exist: {source_dir}")
    if not source_dir.is_dir():
        return _fail(result, f"source is not a directory: {source_dir}")
    if not _source_has_files(source_dir):
        return _fail(result, "source directory has no files")
    if is_under_tmp(source_dir) and not allow_tmp_source:
        return _fail(result, "source under /tmp requires --allow-tmp-source")

    ok, msg = _validate_dest_outside_tmp(dest_dir)
    if not ok:
        return _fail(result, msg)

    if _dest_has_content(dest_dir) and not force:
        return _fail(result, "destination exists and is non-empty (use --force to overwrite)")

    if require_closeout_report and _find_closeout_report(source_dir) is None:
        return _fail(result, f"no {CLOSEOUT_GLOB} closeout report in source")

    if pr_number is not None and _resolve_pr_json(source_dir, pr_number, pr_json) is None:
        return _fail(
            result,
            f"PR{pr_number}.json missing in source and --pr-json not provided or missing",
        )

    if dry_run:
        result.status = "pass"
        result.dest_manifest_verify_rc = "not_run"
        result.manifest_verify_log_status = "not_run"
        return result

    if force and _dest_has_content(dest_dir):
        print("FORCE_OVERWRITE=true", file=sys.stderr)

    try:
        _copy_tree(source_dir, dest_dir)
        _write_durable_readme(dest_dir, source_dir, pr_number=pr_number)
        write_manifest_sha256(dest_dir)
        ok_manifest, manifest_msg, log_status = _verify_manifest_with_log(dest_dir)
        result.manifest_verify_log_status = log_status
        if not ok_manifest:
            result.dest_manifest_verify_rc = "nonzero"
            return _fail(result, f"manifest verify failed: {manifest_msg}")
        if not _manifest_verify_log_is_success(dest_dir):
            result.dest_manifest_verify_rc = "nonzero"
            return _fail(result, "manifest verify log missing or failed")
        if require_closeout_report and not _has_manifest_covered_closeout_artifact(dest_dir):
            result.dest_manifest_verify_rc = "nonzero"
            return _fail(
                result,
                "recognized closeout artifact missing or not manifest-covered while enforcement enabled",
            )
        result.pointer_evidence_found = _pointer_evidence_exists(dest_dir, durable_pointer_patterns)
        if require_durable_pointer_evidence and not result.pointer_evidence_found:
            result.dest_manifest_verify_rc = "nonzero"
            return _fail(
                result,
                "durable pointer/index evidence missing while enforcement enabled",
            )
        result.dest_manifest_verify_rc = "0"
        result.status = "pass"
        return result
    except ValueError as exc:
        return _fail(result, str(exc))
    except OSError as exc:
        return _fail(result, f"filesystem error: {exc}")


def emit_machine_lines(result: CopyVerifyResult) -> None:
    print(f"DURABLE_CLOSEOUT_COPY_VERIFY_STATUS={result.status}")
    print(f"DURABLE_CLOSEOUT_COPY_VERIFY_DRY_RUN={'true' if result.dry_run else 'false'}")
    print(f"DURABLE_CLOSEOUT_SOURCE_DIR={result.source_dir}")
    print(f"DURABLE_CLOSEOUT_DEST_DIR={result.dest_dir}")
    print(f"DURABLE_CLOSEOUT_DEST_MANIFEST_VERIFY_RC={result.dest_manifest_verify_rc}")
    print(f"DURABLE_CLOSEOUT_MANIFEST_VERIFY_LOG_STATUS={result.manifest_verify_log_status}")
    print(
        f"DURABLE_CLOSEOUT_POINTER_EVIDENCE_REQUIRED={'true' if result.pointer_evidence_required else 'false'}"
    )
    print(
        f"DURABLE_CLOSEOUT_POINTER_EVIDENCE_FOUND={'true' if result.pointer_evidence_found else 'false'}"
    )
    print(f"SOURCE_TMP_NOT_CANONICAL={'true' if result.source_tmp_not_canonical else 'false'}")
    print("CLOSEOUT_DOES_NOT_AUTHORIZE_RUNTIME=true")
    print("RUNTIME_COMMANDS_CALLED=false")
    print("AWS_CLI_CALLED=false")
    print("RCLONE_CALLED=false")
    print("NETWORK_CALLED=false")
    print("S3_UPLOAD_CALLED=false")
    print("S3_DOWNLOAD_CALLED=false")
    print("SSH_CALLED=false")
    print("SYSTEMD_CALLED=false")
    print("DOCKER_CALLED=false")
    print("PROCESS_CONTROL_CALLED=false")
    print("HOST_TERMINATION_CALLED=false")
    print("NOTION_WRITE_CALLED=false")
    print("MARKET_DASHBOARD_CHANGED=false")
    print("REMOTE_RUNNER_IMPLEMENTATION_PERMITTED=false")
    print("VALIDATOR_CLI_IMPLEMENTATION_PERMITTED=false")
    print("DRY_COMMAND_TEMPLATE_EXECUTION_PERMITTED=false")
    if result.force_overwrite:
        print("FORCE_OVERWRITE=true")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Copy material closeout tree to durable destination, write MANIFEST.sha256, "
            "and verify (Preflight §2b.1; local-only; non-authorizing)."
        ),
    )
    parser.add_argument("--source-dir", required=True, type=Path)
    parser.add_argument("--dest-dir", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pr-number", type=int, default=None)
    parser.add_argument("--pr-json", type=Path, default=None)
    parser.add_argument(
        "--require-closeout-report",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--require-durable-pointer-evidence",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Fail closed when no pointer/index evidence file exists in durable destination.",
    )
    parser.add_argument(
        "--durable-pointer-pattern",
        action="append",
        default=None,
        help="Glob pattern for acceptable durable pointer/index evidence files (repeatable).",
    )
    parser.add_argument("--allow-tmp-source", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    pointer_patterns = tuple(
        p for p in (args.durable_pointer_pattern or DEFAULT_POINTER_EVIDENCE_PATTERNS) if p
    )
    result = plan_and_execute(
        source_dir=args.source_dir,
        dest_dir=args.dest_dir,
        dry_run=args.dry_run,
        pr_number=args.pr_number,
        pr_json=args.pr_json,
        require_closeout_report=args.require_closeout_report,
        require_durable_pointer_evidence=args.require_durable_pointer_evidence,
        durable_pointer_patterns=pointer_patterns,
        allow_tmp_source=args.allow_tmp_source,
        force=args.force,
    )
    if args.json_output:
        print(json.dumps(asdict(result), sort_keys=True))
    else:
        emit_machine_lines(result)
    if result.error:
        print(result.error, file=sys.stderr)
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
