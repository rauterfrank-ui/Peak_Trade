from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


def _utc_ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dataclass
class CheckResult:
    check_id: str
    command: list[str]
    returncode: int
    status: str
    stdout_path: str | None = None
    stderr_path: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass
class WorkflowOfficerReport:
    officer_version: str
    mode: str
    profile: str
    started_at: str
    finished_at: str
    output_dir: str
    repo_root: str
    success: bool
    checks: list[dict[str, Any]]
    summary: dict[str, Any]


PROFILES: dict[str, list[dict[str, Any]]] = {
    "docs_only_pr": [
        {
            "check_id": "docs_token_policy",
            "command": [sys.executable, "scripts/ops/validate_docs_token_policy.py"],
            "optional": False,
        },
        {
            "check_id": "docs_graph_triage",
            "command": [sys.executable, "scripts/ops/docs_graph_triage.py"],
            "optional": True,
        },
        {
            "check_id": "error_taxonomy_adoption",
            "command": [sys.executable, "scripts/audit/check_error_taxonomy_adoption.py"],
            "optional": True,
        },
    ],
    "ops_local_env": [
        {
            "check_id": "ops_doctor_shell",
            "command": ["bash", "scripts/ops/ops_doctor.sh"],
            "optional": True,
        },
        {
            "check_id": "docker_desktop_preflight_readonly",
            "command": ["bash", "scripts/ops/docker_desktop_preflight_readonly.sh"],
            "optional": True,
        },
        {
            "check_id": "mcp_smoke_preflight",
            "command": ["bash", "scripts/ops/mcp_smoke_preflight.sh"],
            "optional": True,
        },
        {
            "check_id": "failure_analysis",
            "command": ["bash", "scripts/ops/analyze_failures.sh"],
            "optional": True,
        },
    ],
    "live_pilot_preflight": [
        {
            "check_id": "docker_desktop_preflight_readonly",
            "command": ["bash", "scripts/ops/docker_desktop_preflight_readonly.sh"],
            "optional": False,
        },
        {
            "check_id": "mcp_smoke_preflight",
            "command": ["bash", "scripts/ops/mcp_smoke_preflight.sh"],
            "optional": True,
        },
    ],
}


MODES = {"audit", "preflight", "advise"}


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _run_check(
    repo_root: Path,
    output_dir: Path,
    check_id: str,
    command: list[str],
    optional: bool,
) -> CheckResult:
    started_at = datetime.now(UTC).isoformat()
    stdout_path = output_dir / f"{check_id}.stdout.log"
    stderr_path = output_dir / f"{check_id}.stderr.log"

    if (
        not Path(repo_root / command[-1]).exists()
        and len(command) >= 2
        and command[0] in {sys.executable, "bash"}
    ):
        status = "SKIPPED_OPTIONAL_MISSING" if optional else "FAILED_MISSING"
        _write_text(stdout_path, "")
        _write_text(stderr_path, f"Missing target: {command[-1]}\n")
        return CheckResult(
            check_id=check_id,
            command=command,
            returncode=0 if optional else 2,
            status=status,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            started_at=started_at,
            finished_at=datetime.now(UTC).isoformat(),
            notes=[f"Missing wrapped target: {command[-1]}"],
        )

    env = os.environ.copy()
    env["PEAKTRADE_SANDBOX"] = "1"
    env["WORKFLOW_OFFICER_MODE"] = "1"

    proc = subprocess.run(
        command,
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    _write_text(stdout_path, proc.stdout)
    _write_text(stderr_path, proc.stderr)

    status = "OK"
    if proc.returncode != 0:
        status = "WARN_OPTIONAL_FAIL" if optional else "FAILED"

    return CheckResult(
        check_id=check_id,
        command=command,
        returncode=proc.returncode,
        status=status,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        notes=[],
    )


def _emit_events(events_path: Path, results: list[CheckResult]) -> None:
    with events_path.open("w", encoding="utf-8") as fh:
        for result in results:
            fh.write(
                json.dumps(
                    {
                        "type": "workflow_officer_check",
                        "check_id": result.check_id,
                        "status": result.status,
                        "returncode": result.returncode,
                        "started_at": result.started_at,
                        "finished_at": result.finished_at,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def _emit_manifest(manifest_path: Path, output_dir: Path) -> None:
    files = []
    for p in sorted(output_dir.iterdir()):
        if p.is_file():
            files.append({"path": str(p), "size_bytes": p.stat().st_size})
    manifest_path.write_text(
        json.dumps({"files": files}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Peak_Trade Workflow Officer v0")
    parser.add_argument("--mode", choices=sorted(MODES), default="audit")
    parser.add_argument("--profile", choices=sorted(PROFILES.keys()), default="docs_only_pr")
    parser.add_argument("--output-root", default="out/ops/workflow_officer")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    started_at = datetime.now(UTC).isoformat()
    run_dir = repo_root / args.output_root / _utc_ts()
    _safe_mkdir(run_dir)

    results: list[CheckResult] = []
    for spec in PROFILES[args.profile]:
        result = _run_check(
            repo_root=repo_root,
            output_dir=run_dir,
            check_id=spec["check_id"],
            command=spec["command"],
            optional=bool(spec.get("optional", False)),
        )
        results.append(result)

    _emit_events(run_dir / "events.jsonl", results)
    _emit_manifest(run_dir / "manifest.json", run_dir)

    hard_failures = [r for r in results if r.status in {"FAILED", "FAILED_MISSING"}]
    optional_warnings = [
        r for r in results if r.status in {"WARN_OPTIONAL_FAIL", "SKIPPED_OPTIONAL_MISSING"}
    ]

    report = WorkflowOfficerReport(
        officer_version="v0-min",
        mode=args.mode,
        profile=args.profile,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        output_dir=str(run_dir),
        repo_root=str(repo_root),
        success=len(hard_failures) == 0,
        checks=[asdict(r) for r in results],
        summary={
            "total_checks": len(results),
            "hard_failures": len(hard_failures),
            "optional_warnings": len(optional_warnings),
            "strict": bool(args.strict),
        },
    )
    (run_dir / "report.json").write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if args.strict and optional_warnings:
        return 1
    return 0 if not hard_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
