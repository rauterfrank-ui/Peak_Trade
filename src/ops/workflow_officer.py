from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ensure repo root in path when run as script
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.workflow_officer_schema import validate_report_payload

from src.ops.workflow_officer_markdown import render_workflow_officer_summary


UTC = timezone.utc
MODES = {"audit", "preflight", "advise"}
SEVERITIES = {"hard_fail", "warn", "info"}
OUTCOMES = {"pass", "fail", "missing"}
EFFECTIVE_LEVELS = {"ok", "warning", "error", "info"}


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
    severity: str
    outcome: str
    effective_level: str
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


PROFILE_CHECKS: dict[str, list[dict[str, Any]]] = {
    "docs_only_pr": [
        {
            "check_id": "docs_token_policy",
            "command": [sys.executable, "scripts/ops/validate_docs_token_policy.py"],
        },
        {
            "check_id": "docs_graph_triage",
            "command": [sys.executable, "scripts/ops/docs_graph_triage.py"],
        },
        {
            "check_id": "error_taxonomy_adoption",
            "command": [sys.executable, "scripts/audit/check_error_taxonomy_adoption.py"],
        },
    ],
    "ops_local_env": [
        {
            "check_id": "ops_doctor_shell",
            "command": ["bash", "scripts/ops/ops_doctor.sh"],
        },
        {
            "check_id": "docker_desktop_preflight_readonly",
            "command": ["bash", "scripts/ops/docker_desktop_preflight_readonly.sh"],
        },
        {
            "check_id": "mcp_smoke_preflight",
            "command": ["bash", "scripts/ops/mcp_smoke_preflight.sh"],
        },
        {
            "check_id": "failure_analysis",
            "command": ["bash", "scripts/ops/analyze_failures.sh"],
        },
    ],
    "live_pilot_preflight": [
        {
            "check_id": "docker_desktop_preflight_readonly",
            "command": ["bash", "scripts/ops/docker_desktop_preflight_readonly.sh"],
        },
        {
            "check_id": "mcp_smoke_preflight",
            "command": ["bash", "scripts/ops/mcp_smoke_preflight.sh"],
        },
    ],
}


PROFILE_POLICY: dict[str, dict[str, str]] = {
    "docs_only_pr": {
        "docs_token_policy": "hard_fail",
        "docs_graph_triage": "warn",
        "error_taxonomy_adoption": "warn",
    },
    "ops_local_env": {
        "ops_doctor_shell": "warn",
        "docker_desktop_preflight_readonly": "warn",
        "mcp_smoke_preflight": "warn",
        "failure_analysis": "info",
    },
    "live_pilot_preflight": {
        "docker_desktop_preflight_readonly": "hard_fail",
        "mcp_smoke_preflight": "warn",
    },
}


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _resolve_severity(profile: str, check_id: str) -> str:
    severity = PROFILE_POLICY.get(profile, {}).get(check_id, "warn")
    if severity not in SEVERITIES:
        raise ValueError(f"Unsupported severity {severity!r} for {profile}.{check_id}")
    return severity


def _resolve_status(returncode: int, severity: str, missing: bool = False) -> str:
    if returncode == 0 and not missing:
        return "OK"
    if missing and severity == "hard_fail":
        return "FAILED_MISSING"
    if missing and severity == "warn":
        return "WARN_MISSING"
    if missing and severity == "info":
        return "INFO_MISSING"
    if severity == "hard_fail":
        return "FAILED"
    if severity == "warn":
        return "WARN"
    return "INFO"


def _resolve_outcome(returncode: int, missing: bool = False) -> str:
    if missing:
        return "missing"
    if returncode == 0:
        return "pass"
    return "fail"


def _resolve_effective_level(outcome: str, severity: str) -> str:
    if outcome == "pass":
        return "ok"
    if outcome == "missing":
        if severity == "hard_fail":
            return "error"
        if severity == "warn":
            return "warning"
        return "info"
    if severity == "hard_fail":
        return "error"
    if severity == "warn":
        return "warning"
    return "info"


def _run_check(
    repo_root: Path,
    output_dir: Path,
    profile: str,
    check_id: str,
    command: list[str],
) -> CheckResult:
    started_at = datetime.now(UTC).isoformat()
    stdout_path = output_dir / f"{check_id}.stdout.log"
    stderr_path = output_dir / f"{check_id}.stderr.log"
    severity = _resolve_severity(profile, check_id)

    wrapped_target = command[-1]
    expects_local_target = len(command) >= 2 and command[0] in {sys.executable, "bash"}

    if expects_local_target and not (repo_root / wrapped_target).exists():
        _write_text(stdout_path, "")
        _write_text(stderr_path, f"Missing target: {wrapped_target}\n")
        outcome = _resolve_outcome(returncode=2, missing=True)
        return CheckResult(
            check_id=check_id,
            command=command,
            returncode=2,
            status=_resolve_status(returncode=2, severity=severity, missing=True),
            severity=severity,
            outcome=outcome,
            effective_level=_resolve_effective_level(outcome=outcome, severity=severity),
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            started_at=started_at,
            finished_at=datetime.now(UTC).isoformat(),
            notes=[f"Missing wrapped target: {wrapped_target}"],
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

    outcome = _resolve_outcome(returncode=proc.returncode, missing=False)

    return CheckResult(
        check_id=check_id,
        command=command,
        returncode=proc.returncode,
        status=_resolve_status(returncode=proc.returncode, severity=severity),
        severity=severity,
        outcome=outcome,
        effective_level=_resolve_effective_level(outcome=outcome, severity=severity),
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
                        "severity": result.severity,
                        "outcome": result.outcome,
                        "effective_level": result.effective_level,
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
        json.dumps({"files": files}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _build_summary(results: list[CheckResult], strict: bool) -> dict[str, Any]:
    severity_counts = {"hard_fail": 0, "warn": 0, "info": 0}
    status_counts: dict[str, int] = {}
    outcome_counts = {"pass": 0, "fail": 0, "missing": 0}
    effective_level_counts = {"ok": 0, "warning": 0, "error": 0, "info": 0}

    for result in results:
        severity_counts[result.severity] += 1
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
        outcome_counts[result.outcome] += 1
        effective_level_counts[result.effective_level] += 1

    hard_failures = sum(1 for r in results if r.effective_level == "error")
    warnings = sum(1 for r in results if r.effective_level == "warning")
    infos = sum(1 for r in results if r.effective_level == "info")

    return {
        "total_checks": len(results),
        "hard_failures": hard_failures,
        "warnings": warnings,
        "infos": infos,
        "severity_counts": severity_counts,
        "status_counts": status_counts,
        "outcome_counts": outcome_counts,
        "effective_level_counts": effective_level_counts,
        "strict": strict,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Peak_Trade Workflow Officer v0")
    parser.add_argument("--mode", choices=sorted(MODES), default="audit")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_CHECKS.keys()),
        default="docs_only_pr",
    )
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
    for spec in PROFILE_CHECKS[args.profile]:
        results.append(
            _run_check(
                repo_root=repo_root,
                output_dir=run_dir,
                profile=args.profile,
                check_id=spec["check_id"],
                command=spec["command"],
            )
        )

    _emit_events(run_dir / "events.jsonl", results)
    _emit_manifest(run_dir / "manifest.json", run_dir)

    summary = _build_summary(results, strict=bool(args.strict))
    success = summary["hard_failures"] == 0

    report = WorkflowOfficerReport(
        officer_version="v0-min",
        mode=args.mode,
        profile=args.profile,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        output_dir=str(run_dir),
        repo_root=str(repo_root),
        success=success,
        checks=[asdict(r) for r in results],
        summary=summary,
    )
    report_payload = asdict(report)
    validate_report_payload(report_payload)
    (run_dir / "report.json").write_text(
        json.dumps(report_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text(
        render_workflow_officer_summary(report_payload),
        encoding="utf-8",
    )

    if summary["hard_failures"] > 0:
        return 1
    if args.strict and (summary["warnings"] > 0 or summary["infos"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
