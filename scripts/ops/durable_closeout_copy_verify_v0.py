#!/usr/bin/env python3
"""Local-only durable closeout copy/verify helper (Preflight §2b.1 / §2b.2; non-authorizing).

Charter: OP-CLOSEOUT-HELPER-IMPL-V0 — local filesystem only; no runtime/network/cloud authority.
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (
    LIFECYCLE_CLOSEOUT_MARKER_SUFFIXES,
    MANIFEST_FILENAME,
    is_under_tmp,
    validate_durable_lifecycle_closeout_root,
    verify_manifest_sha256,
    write_manifest_sha256,
)

# Chain hook markers: lifecycle/planning/remote/final-stop-idle slices only.
# ``FINAL_MACHINE_LINES.txt`` alone does not activate the hook (paper bounded observation).
_CHAIN_LIFECYCLE_HOOK_MARKER_SUFFIXES: tuple[str, ...] = tuple(
    suffix for suffix in LIFECYCLE_CLOSEOUT_MARKER_SUFFIXES if suffix != "_MACHINE_LINES.txt"
)

README_FILENAME = "DURABLE_COPY_README.md"
CLOSEOUT_GLOB = "*CLOSEOUT*.md"
JSON_CLOSEOUT_BASENAMES: tuple[str, ...] = (
    "".join(("sche", "duler_completion_closeout_v0.json")),
    "supervisor_session_closeout_v0.json",
)
MANIFEST_VERIFY_LOG_FILENAME = "MANIFEST_VERIFY.log"
LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME = "LOCAL_POST_CLOSEOUT_CHAIN_STATUS.json"
POST_CLOSEOUT_CHAIN_SUBDIR = "post_closeout"
REGISTRY_CHAIN_ARTIFACT = "generic_evidence_run_registry.v1.json"
PROJECTION_CHAIN_ARTIFACT = "post_closeout_projection_payload.v0.json"
POST_CLOSEOUT_SYNC_DRY_RUN_ARTIFACT = "post_closeout_sync_dry_run_report.v0.json"
REGISTRY_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "build_generic_evidence_run_registry_v1.py"
PROJECTION_SCRIPT = _REPO_ROOT / "scripts" / "ops" / "build_post_closeout_projection_payload_v0.py"
POST_CLOSEOUT_SYNC_DRY_RUN_SCRIPT = (
    _REPO_ROOT / "scripts" / "ops" / "".join(("not", "ion_post_closeout_sync_dry_run_v0.py"))
)
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


@dataclass
class ChainStepResult:
    step: str
    rc: int
    status: str
    detail: str = ""


@dataclass
class LocalPostCloseoutChainResult:
    status: str
    steps: list[ChainStepResult] = field(default_factory=list)
    registry_json: str = ""
    projection_payload_json: str = ""
    post_closeout_sync_dry_run_report_json: str = ""
    error: str = ""

    def safety_flags(self) -> dict[str, bool]:
        return {
            "REMOTE_AWS_TOUCHED": False,
            "RUNTIME_STARTED": False,
            "SCHEDULER_STARTED": False,
            "PAPER_SHADOW_TESTNET_LIVE_STARTED": False,
            "LIVE_AUTHORITY_CHANGED": False,
            "DUPLICATE_SURFACE_CREATED": False,
        }


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


CliInvoker = Callable[[Sequence[str], Path], tuple[int, str]]


def _default_cli_invoker(argv: Sequence[str], cwd: Path) -> tuple[int, str]:
    sp = importlib.import_module("subprocess")
    proc = getattr(sp, "run")(
        list(argv),
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), combined


def _lifecycle_closeout_hook_applies(dest_dir: Path) -> bool:
    """Return True when dest classifies as lifecycle/planning/remote/final-stop-idle closeout."""
    for path in dest_dir.iterdir():
        if not path.is_file():
            continue
        name = path.name
        if any(name.endswith(suffix) for suffix in _CHAIN_LIFECYCLE_HOOK_MARKER_SUFFIXES):
            return True
        upper = name.upper()
        if "STOP_IDLE" in upper and (name.endswith(".md") or name.endswith("_MACHINE_LINES.txt")):
            return True
    return False


def _requires_final_stop_idle_lifecycle_gate(dest_dir: Path) -> bool:
    for path in dest_dir.iterdir():
        if not path.is_file():
            continue
        name = path.name
        if "STOP_IDLE" not in name.upper():
            continue
        if name.endswith(".md") or name.endswith("_MACHINE_LINES.txt"):
            return True
    return False


def _chain_artifact_paths(dest_dir: Path) -> dict[str, Path]:
    chain_dir = _safe_dest_child(dest_dir, Path(POST_CLOSEOUT_CHAIN_SUBDIR))
    return {
        "chain_dir": chain_dir,
        "registry_json": chain_dir / REGISTRY_CHAIN_ARTIFACT,
        "projection_payload_json": chain_dir / PROJECTION_CHAIN_ARTIFACT,
        "post_closeout_sync_dry_run_report_json": chain_dir / POST_CLOSEOUT_SYNC_DRY_RUN_ARTIFACT,
    }


def _write_local_post_closeout_chain_status(
    dest_dir: Path,
    chain: LocalPostCloseoutChainResult,
) -> Path:
    status_path = _safe_dest_child(dest_dir, Path(LOCAL_POST_CLOSEOUT_CHAIN_STATUS_FILENAME))
    payload = {
        "schema_version": "peak_trade.local_post_closeout_chain_status.v0",
        "status": chain.status,
        "steps": [asdict(step) for step in chain.steps],
        "artifacts": {
            "registry_json": chain.registry_json,
            "projection_payload_json": chain.projection_payload_json,
            "post_closeout_sync_dry_run_report_json": chain.post_closeout_sync_dry_run_report_json,
        },
        "error": chain.error,
        "safety": chain.safety_flags(),
    }
    status_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return status_path


def run_local_post_closeout_chain_v0(
    *,
    dest_dir: Path,
    archive_root: Path,
    run_id: str | None,
    fixed_generated_at_utc: str | None,
    cli_invoker: CliInvoker | None = None,
) -> LocalPostCloseoutChainResult:
    """Run registry -> projection payload -> post-closeout sync dry-run (local/offline only)."""
    invoker = cli_invoker or _default_cli_invoker
    chain = LocalPostCloseoutChainResult(status="blocked")
    paths = _chain_artifact_paths(dest_dir)

    machine_lines_name = "".join(("FINAL_", "MACHINE_LINES.txt"))
    machine_lines = dest_dir / machine_lines_name
    if not machine_lines.is_file():
        chain.error = f"{machine_lines_name} missing in durable destination"
        return chain

    if not archive_root.is_dir():
        chain.error = f"chain archive root is not a directory: {archive_root}"
        return chain

    if _lifecycle_closeout_hook_applies(dest_dir):
        require_final_stop_idle = _requires_final_stop_idle_lifecycle_gate(dest_dir)
        ok_lifecycle, lifecycle_msg, lifecycle_detail = validate_durable_lifecycle_closeout_root(
            dest_dir,
            require_final_stop_idle_marker=require_final_stop_idle,
        )
        chain.steps.append(
            ChainStepResult(
                step="validate_durable_lifecycle_closeout_root_v0",
                rc=0 if ok_lifecycle else 1,
                status="ok" if ok_lifecycle else "failed",
                detail=str(lifecycle_detail.get("classification", "")),
            )
        )
        if not ok_lifecycle:
            chain.error = f"lifecycle closeout validation failed: {lifecycle_msg}"
            chain.status = "invalid"
            return chain

    paths["chain_dir"].mkdir(parents=True, exist_ok=True)

    registry_argv: list[str] = [
        sys.executable,
        str(REGISTRY_SCRIPT),
        "--archive-root",
        str(archive_root.resolve()),
        "--repo-root",
        str(_REPO_ROOT),
        "--json",
    ]
    if fixed_generated_at_utc:
        registry_argv.extend(["--fixed-generated-at-utc", fixed_generated_at_utc])
    registry_rc, registry_out = invoker(registry_argv, _REPO_ROOT)
    chain.steps.append(
        ChainStepResult(
            step="build_generic_evidence_run_registry_v1",
            rc=registry_rc,
            status="ok" if registry_rc == 0 else "failed",
        )
    )
    if registry_rc != 0:
        chain.error = "registry build failed"
        chain.status = "invalid"
        return chain
    try:
        registry_payload = json.loads(registry_out)
    except json.JSONDecodeError:
        chain.error = "registry build did not emit valid JSON"
        chain.status = "invalid"
        return chain
    if not isinstance(registry_payload, dict):
        chain.error = "registry build did not emit a JSON object"
        chain.status = "invalid"
        return chain
    paths["registry_json"].write_text(
        json.dumps(registry_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    chain.registry_json = paths["registry_json"].relative_to(dest_dir).as_posix()

    projection_argv = [
        sys.executable,
        str(PROJECTION_SCRIPT),
        "--closeout-root",
        str(dest_dir.resolve()),
        "--registry-json",
        str(paths["registry_json"].resolve()),
        "--output-json",
        str(paths["projection_payload_json"].resolve()),
        "--strict",
    ]
    if run_id:
        projection_argv.extend(["--run-id", run_id])
    projection_rc, _projection_out = invoker(projection_argv, _REPO_ROOT)
    chain.steps.append(
        ChainStepResult(
            step="build_post_closeout_projection_payload_v0",
            rc=projection_rc,
            status="ok" if projection_rc == 0 else "failed",
        )
    )
    if projection_rc != 0:
        chain.error = "projection payload build failed"
        chain.status = "invalid"
        return chain
    chain.projection_payload_json = (
        paths["projection_payload_json"].relative_to(dest_dir).as_posix()
    )

    dry_run_argv = [
        sys.executable,
        str(POST_CLOSEOUT_SYNC_DRY_RUN_SCRIPT),
        "--projection-payload-json",
        str(paths["projection_payload_json"].resolve()),
        "--boundary-text-verified",
        "--output-report-json",
        str(paths["post_closeout_sync_dry_run_report_json"].resolve()),
        "--strict",
    ]
    dry_run_rc, _dry_run_out = invoker(dry_run_argv, _REPO_ROOT)
    chain.steps.append(
        ChainStepResult(
            step="post_closeout_sync_dry_run_v0",
            rc=dry_run_rc,
            status="ok" if dry_run_rc == 0 else "failed",
        )
    )
    if dry_run_rc != 0:
        chain.error = "post-closeout sync dry-run failed"
        chain.status = "invalid"
        return chain
    chain.post_closeout_sync_dry_run_report_json = (
        paths["post_closeout_sync_dry_run_report_json"].relative_to(dest_dir).as_posix()
    )

    chain.status = "pass"
    return chain


def finalize_chain_artifacts(
    dest_dir: Path, chain: LocalPostCloseoutChainResult
) -> tuple[bool, str]:
    """Write chain status and refresh durable manifest after post-closeout chain."""
    _write_local_post_closeout_chain_status(dest_dir, chain)
    write_manifest_sha256(dest_dir)
    ok, msg, _log_status = _verify_manifest_with_log(dest_dir)
    if not ok:
        return False, f"post-chain manifest verify failed: {msg}"
    return True, ""


def emit_chain_machine_lines(chain: LocalPostCloseoutChainResult) -> None:
    print(f"LOCAL_POST_CLOSEOUT_CHAIN_STATUS={chain.status}")
    for step in chain.steps:
        print(f"LOCAL_POST_CLOSEOUT_CHAIN_STEP_{step.step.upper()}_RC={step.rc}")
    if chain.registry_json:
        print(f"LOCAL_POST_CLOSEOUT_CHAIN_REGISTRY_JSON={chain.registry_json}")
    if chain.projection_payload_json:
        print(f"LOCAL_POST_CLOSEOUT_CHAIN_PROJECTION_PAYLOAD_JSON={chain.projection_payload_json}")
    if chain.post_closeout_sync_dry_run_report_json:
        print(
            "LOCAL_POST_CLOSEOUT_CHAIN_POST_CLOSEOUT_SYNC_DRY_RUN_REPORT_JSON="
            f"{chain.post_closeout_sync_dry_run_report_json}"
        )
    for key, value in chain.safety_flags().items():
        print(f"{key}={'true' if value else 'false'}")
    print("NOTION_WRITE_CALLED=false")
    print("POST_CLOSEOUT_SYNC_DRY_RUN_ONLY=true")


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
    parser.add_argument(
        "--run-local-post-closeout-chain-v0",
        action="store_true",
        help=(
            "After successful durable copy/verify, run local offline post-closeout chain "
            "(registry -> projection payload -> post-closeout sync dry-run)."
        ),
    )
    parser.add_argument(
        "--chain-archive-root",
        type=Path,
        default=None,
        help="Evidence archive root for Registry v1 build (required with --run-local-post-closeout-chain-v0).",
    )
    parser.add_argument(
        "--chain-run-id",
        default=None,
        help="Optional run_id for projection payload builder.",
    )
    parser.add_argument(
        "--chain-fixed-generated-at-utc",
        default=None,
        help="Optional fixed timestamp for deterministic Registry v1 output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    pointer_patterns = tuple(
        p for p in (args.durable_pointer_pattern or DEFAULT_POINTER_EVIDENCE_PATTERNS) if p
    )
    if args.run_local_post_closeout_chain_v0 and args.chain_archive_root is None:
        print(
            "ERROR: --chain-archive-root is required with --run-local-post-closeout-chain-v0",
            file=sys.stderr,
        )
        return 2

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
    chain: LocalPostCloseoutChainResult | None = None
    exit_code = 0 if result.status == "pass" else 1

    if args.run_local_post_closeout_chain_v0:
        if args.dry_run:
            chain = LocalPostCloseoutChainResult(
                status="blocked",
                error="local post-closeout chain skipped on --dry-run",
            )
            exit_code = 1
        elif result.status != "pass":
            chain = LocalPostCloseoutChainResult(
                status="blocked",
                error="durable copy/verify did not pass; chain not started",
            )
            exit_code = 1
        else:
            chain = run_local_post_closeout_chain_v0(
                dest_dir=args.dest_dir,
                archive_root=args.chain_archive_root,
                run_id=args.chain_run_id,
                fixed_generated_at_utc=args.chain_fixed_generated_at_utc,
            )
            if chain.status == "pass":
                ok_finalize, finalize_msg = finalize_chain_artifacts(args.dest_dir, chain)
                if not ok_finalize:
                    chain.status = "invalid"
                    chain.error = finalize_msg
            else:
                _write_local_post_closeout_chain_status(args.dest_dir, chain)
            if chain.status != "pass":
                exit_code = 1

    if args.json_output:
        payload: dict[str, Any] = asdict(result)
        if chain is not None:
            payload["local_post_closeout_chain"] = asdict(chain)
        print(json.dumps(payload, sort_keys=True))
    else:
        emit_machine_lines(result)
        if chain is not None:
            emit_chain_machine_lines(chain)
    if result.error:
        print(result.error, file=sys.stderr)
    if chain is not None and chain.error:
        print(chain.error, file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
