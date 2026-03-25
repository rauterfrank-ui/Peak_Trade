from __future__ import annotations

import argparse
import json
import os
import re
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

from src.ops.workflow_officer_markdown import render_workflow_officer_summary
from src.ops.workflow_officer_profiles import PROFILE_POLICY, PROFILES
from src.ops.workflow_officer_schema import validate_report_payload

UTC = timezone.utc
MODES = {"audit", "preflight", "advise"}
SEVERITIES = {"hard_fail", "warn", "info"}
OUTCOMES = {"pass", "fail", "missing"}
EFFECTIVE_LEVELS = {"ok", "warning", "error", "info"}

# Re-export for tests and callers that imported from workflow_officer.
PROFILE_CHECKS = PROFILES

# Follow-up topic queue: lower tuple sorts first (more urgent).
_FOLLOWUP_PRIORITY_RANK = {"p0": 0, "p1": 1, "p2": 2, "p3": 3}
_FOLLOWUP_EFFECTIVE_RANK = {"error": 0, "warning": 1, "info": 2, "ok": 3}

# Handoff context: bounded excerpt for operators (read-only, no extra I/O).
_HANDOFF_CONTEXT_TOP_FOLLOWUPS = 5
_HANDOFF_CONTEXT_SCHEMA_VERSION = "workflow_officer.handoff_context/v0"

_PROVENANCE_SCHEMA_VERSION = "workflow_officer.provenance/v0"

# Ops registry pointers under docs/ops/registry (read-only; same line format as
# scripts/ops/verify_registry_pointer_artifacts.parse_pointer).
_OPS_REGISTRY_REL = Path("docs/ops/registry")

# Canonical merge logs (read-only); matches docs/ops/merge_logs/PR_*_MERGE_LOG.md convention.
_MERGE_LOGS_SUBDIR = Path("docs/ops/merge_logs")
_MERGE_LOG_GLOB = "PR_*_MERGE_LOG.md"
_MERGE_LOG_FILENAME_RE = re.compile(r"^PR_(\d+)_MERGE_LOG\.md$")
_MAX_RECENT_MERGE_LOGS = 5
_MERGE_COMMIT_PATTERNS = (
    re.compile(r"mergeCommit:\s*`([0-9a-fA-F]{7,40})`"),
    re.compile(r"Merge commit:\s*([0-9a-fA-F]{7,40})\b"),
    re.compile(r"Merge commit `([0-9a-fA-F]{7,40})`"),
)
_MERGED_AT_PATTERNS = (
    re.compile(r"mergedAt:\s*`([^`]+)`"),
    re.compile(r"Merged at \(UTC\):\s*(\S+)"),
)


def build_workflow_officer_provenance() -> dict[str, Any]:
    """Declare read-only lineage for derived summary fields (no I/O, deterministic)."""
    return {
        "provenance_schema_version": _PROVENANCE_SCHEMA_VERSION,
        "recommended_priority_and_action": {
            "builder": "_recommend_priority_action",
            "check_row_inputs": sorted(["effective_level", "outcome", "severity"]),
            "profile_plan_fields_appended": sorted(["category", "description", "surface"]),
        },
        "followup_topic_ranking": {
            "builder": "build_followup_topic_ranking",
            "check_row_inputs": sorted(
                ["category", "check_id", "effective_level", "recommended_priority", "surface"]
            ),
            "ordering_inputs": sorted(["check_id", "effective_level", "recommended_priority"]),
        },
        "registry_inputs": {
            "builder": "load_ops_registry_inputs",
            "repo_relative_glob": "docs/ops/registry/*.pointer",
        },
        "merge_log_inputs": {
            "builder": "load_ops_merge_log_inputs",
            "body_signal_parser": "parse_merge_log_signals",
            "parsed_fields": sorted(["merged_at", "merge_commit_sha"]),
            "repo_relative_glob": "docs/ops/merge_logs/PR_*_MERGE_LOG.md",
        },
        "handoff_context": {
            "builder": "build_handoff_context",
            "handoff_output_keys": sorted(
                [
                    "handoff_schema_version",
                    "merge_log_inputs_rollup",
                    "primary_followup_check_id",
                    "registry_inputs_rollup",
                    "rollup",
                    "strict",
                    "top_followups",
                ]
            ),
            "rollup_keys": sorted(["hard_failures", "infos", "total_checks", "warnings"]),
            "summary_inputs": sorted(
                [
                    "followup_topic_ranking",
                    "merge_log_inputs",
                    "registry_inputs",
                    "strict",
                ]
            ),
        },
    }


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


_RECOMMEND_PREFIX = "[workflow_officer.recommend"


def _format_recommendation(rationale_key: str, body: str) -> str:
    return f"{_RECOMMEND_PREFIX}.{rationale_key}] {body}"


def _recommend_priority_action(
    effective_level: str,
    outcome: str,
    severity: str,
) -> tuple[str, str]:
    """Deterministic operator-facing recommendation; never implies auto-fix.

    Precedence: ``error`` > ``warning`` > ``ok``; remaining ``info`` effective
    level branches on ``outcome`` (pass → p3, else → p2).
    """
    if effective_level not in EFFECTIVE_LEVELS:
        raise ValueError(f"Unsupported effective_level {effective_level!r}")
    if outcome not in OUTCOMES:
        raise ValueError(f"Unsupported outcome {outcome!r}")
    if severity not in SEVERITIES:
        raise ValueError(f"Unsupported severity {severity!r}")

    if effective_level == "error":
        return (
            "p0",
            _format_recommendation(
                "remediate_error",
                "Stop and remediate: hard_fail check failed or a required target is "
                "missing under hard_fail severity.",
            ),
        )
    if effective_level == "warning":
        return (
            "p1",
            _format_recommendation(
                "review_warning",
                "Review stdout/stderr logs; resolve warnings before relying on this path.",
            ),
        )
    if effective_level == "ok":
        return (
            "p3",
            _format_recommendation(
                "no_action_ok",
                "No operator action required.",
            ),
        )
    if effective_level == "info":
        if outcome == "pass":
            return (
                "p3",
                _format_recommendation(
                    "no_action_info_pass",
                    "No operator action required.",
                ),
            )
        return (
            "p2",
            _format_recommendation(
                "verify_manual_info",
                "Informational: verify manually if this check matters for your change.",
            ),
        )
    raise AssertionError(f"Unhandled effective_level {effective_level!r}")


def _check_to_report_dict(result: CheckResult, plan: dict[str, Any]) -> dict[str, Any]:
    rec = asdict(result)
    prio, action = _recommend_priority_action(
        result.effective_level,
        result.outcome,
        result.severity,
    )
    rec["surface"] = plan["surface"]
    rec["category"] = plan["category"]
    rec["description"] = plan["description"]
    rec["recommended_action"] = action
    rec["recommended_priority"] = prio
    return rec


def _run_check(
    repo_root: Path,
    output_dir: Path,
    profile: str,
    check_id: str,
    command: list[str],
    severity: str,
) -> CheckResult:
    started_at = datetime.now(UTC).isoformat()
    stdout_path = output_dir / f"{check_id}.stdout.log"
    stderr_path = output_dir / f"{check_id}.stderr.log"
    if severity not in SEVERITIES:
        raise ValueError(f"Unsupported severity {severity!r} for {profile}.{check_id}")

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


def _emit_events(events_path: Path, check_dicts: list[dict[str, Any]]) -> None:
    with events_path.open("w", encoding="utf-8") as fh:
        for row in check_dicts:
            fh.write(
                json.dumps(
                    {
                        "type": "workflow_officer_check",
                        "check_id": row["check_id"],
                        "status": row["status"],
                        "severity": row["severity"],
                        "outcome": row["outcome"],
                        "effective_level": row["effective_level"],
                        "recommended_priority": row["recommended_priority"],
                        "returncode": row["returncode"],
                        "started_at": row.get("started_at"),
                        "finished_at": row.get("finished_at"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def parse_ops_pointer_text(text: str) -> dict[str, str]:
    """Parse ``docs/ops/registry/*.pointer`` body (key=value lines; ``#`` comments ignored)."""
    d: dict[str, str] = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if "=" in ln:
            k, v = ln.split("=", 1)
            key = k.strip()
            if key:
                d[key] = v.strip()
    return d


def parse_ops_pointer_file(path: Path) -> dict[str, str]:
    return parse_ops_pointer_text(path.read_text(encoding="utf-8"))


def load_ops_registry_inputs(repo_root: Path) -> dict[str, Any]:
    """Read-only scan of tracked-style pointer files (no writes, no network)."""
    reg_dir = repo_root / _OPS_REGISTRY_REL
    if not reg_dir.is_dir():
        return {
            "registry_dir_present": False,
            "pointer_count": 0,
            "pointers": [],
        }
    files = sorted(reg_dir.glob("*.pointer"), key=lambda p: p.name)
    pointers: list[dict[str, Any]] = []
    for p in files:
        if not p.is_file():
            continue
        try:
            raw = parse_ops_pointer_file(p)
        except OSError:
            raw = {}
        fields = dict(sorted(raw.items()))
        rel = str(p.relative_to(repo_root).as_posix())
        pointers.append({"name": p.name, "rel_path": rel, "fields": fields})
    return {
        "registry_dir_present": True,
        "pointer_count": len(pointers),
        "pointers": pointers,
    }


def _registry_inputs_rollup(summary: dict[str, Any]) -> dict[str, Any]:
    """Handoff-sized digest of ``registry_inputs`` (first ``run_id`` in sorted pointer order)."""
    reg = summary.get("registry_inputs")
    if not isinstance(reg, dict):
        return {
            "registry_dir_present": False,
            "pointer_count": 0,
            "primary_run_id": None,
        }
    present = bool(reg.get("registry_dir_present", False))
    try:
        count = int(reg.get("pointer_count", 0))
    except (TypeError, ValueError):
        count = 0
    primary: str | None = None
    pointers = reg.get("pointers")
    if isinstance(pointers, list):
        for entry in pointers:
            if not isinstance(entry, dict):
                continue
            fields = entry.get("fields")
            if not isinstance(fields, dict):
                continue
            rid = fields.get("run_id")
            if isinstance(rid, str) and rid.strip():
                primary = rid.strip()
                break
    return {
        "registry_dir_present": present,
        "pointer_count": count,
        "primary_run_id": primary,
    }


def parse_merge_log_signals(text: str) -> dict[str, str | None]:
    """Extract common merge metadata from a merge-log markdown body (best-effort)."""
    merge_sha: str | None = None
    merged_at: str | None = None
    for rx in _MERGE_COMMIT_PATTERNS:
        m = rx.search(text)
        if m:
            merge_sha = m.group(1).lower()
            break
    for rx in _MERGED_AT_PATTERNS:
        m = rx.search(text)
        if m:
            merged_at = m.group(1).strip()
            break
    return {"merge_commit_sha": merge_sha, "merged_at": merged_at}


def load_ops_merge_log_inputs(repo_root: Path) -> dict[str, Any]:
    """Read-only scan of canonical PR merge logs under docs/ops/merge_logs."""
    ml_dir = repo_root / _MERGE_LOGS_SUBDIR
    if not ml_dir.is_dir():
        return {
            "merge_logs_dir_present": False,
            "canonical_merge_log_count": 0,
            "recent_merge_logs": [],
        }
    entries: list[tuple[int, Path]] = []
    for p in ml_dir.glob(_MERGE_LOG_GLOB):
        if not p.is_file():
            continue
        m = _MERGE_LOG_FILENAME_RE.match(p.name)
        if not m:
            continue
        entries.append((int(m.group(1)), p))
    entries.sort(key=lambda t: t[0], reverse=True)
    recent: list[dict[str, Any]] = []
    for pr_num, p in entries[:_MAX_RECENT_MERGE_LOGS]:
        rel = str(p.relative_to(repo_root).as_posix())
        try:
            body = p.read_text(encoding="utf-8")
        except OSError:
            body = ""
        sig = parse_merge_log_signals(body)
        recent.append(
            {
                "pr_number": pr_num,
                "rel_path": rel,
                "merge_commit_sha": sig["merge_commit_sha"],
                "merged_at": sig["merged_at"],
            }
        )
    return {
        "merge_logs_dir_present": True,
        "canonical_merge_log_count": len(entries),
        "recent_merge_logs": recent,
    }


def _merge_log_inputs_rollup(summary: dict[str, Any]) -> dict[str, Any]:
    """Handoff-sized digest of ``merge_log_inputs``."""
    block = summary.get("merge_log_inputs")
    if not isinstance(block, dict):
        return {
            "merge_logs_dir_present": False,
            "canonical_merge_log_count": 0,
            "latest_pr_number": None,
            "latest_merge_commit_sha": None,
        }
    present = bool(block.get("merge_logs_dir_present", False))
    try:
        count = int(block.get("canonical_merge_log_count", 0))
    except (TypeError, ValueError):
        count = 0
    latest_pr: int | None = None
    latest_sha: str | None = None
    recent = block.get("recent_merge_logs")
    if isinstance(recent, list) and recent:
        first = recent[0]
        if isinstance(first, dict):
            try:
                latest_pr = int(first["pr_number"])
            except (KeyError, TypeError, ValueError):
                latest_pr = None
            sha = first.get("merge_commit_sha")
            if isinstance(sha, str) and sha.strip():
                latest_sha = sha.strip().lower()
    return {
        "merge_logs_dir_present": present,
        "canonical_merge_log_count": count,
        "latest_pr_number": latest_pr,
        "latest_merge_commit_sha": latest_sha,
    }


def build_followup_topic_ranking(check_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank checks as read-only follow-up topics (no I/O, no mutation).

    Uses only fields already present on each check row. Ordering:
    1. ``recommended_priority`` (p0 most urgent, then p1, p2, p3)
    2. ``effective_level`` (error, warning, info, ok)
    3. ``check_id`` (lexicographic, ASCII)
    """
    if not check_dicts:
        return []
    ordered = sorted(
        check_dicts,
        key=lambda row: (
            _FOLLOWUP_PRIORITY_RANK[row["recommended_priority"]],
            _FOLLOWUP_EFFECTIVE_RANK[row["effective_level"]],
            row["check_id"],
        ),
    )
    return [
        {
            "rank": idx,
            "check_id": row["check_id"],
            "recommended_priority": row["recommended_priority"],
            "effective_level": row["effective_level"],
            "surface": row["surface"],
            "category": row["category"],
        }
        for idx, row in enumerate(ordered, start=1)
    ]


def build_handoff_context(summary: dict[str, Any]) -> dict[str, Any]:
    """Derive a small read-only handoff snapshot from an existing summary dict.

    Uses ``followup_topic_ranking``, check rollups, ``registry_inputs``, and
    ``merge_log_inputs``. If ``followup_topic_ranking`` is missing or not a list,
    it is treated as empty.
    """
    ranking = summary.get("followup_topic_ranking")
    if not isinstance(ranking, list):
        ranking = []
    top = ranking[:_HANDOFF_CONTEXT_TOP_FOLLOWUPS]
    primary: str | None = ranking[0]["check_id"] if ranking else None
    return {
        "handoff_schema_version": _HANDOFF_CONTEXT_SCHEMA_VERSION,
        "strict": bool(summary["strict"]),
        "rollup": {
            "total_checks": int(summary["total_checks"]),
            "hard_failures": int(summary["hard_failures"]),
            "warnings": int(summary["warnings"]),
            "infos": int(summary["infos"]),
        },
        "primary_followup_check_id": primary,
        "top_followups": [
            {
                "rank": int(row["rank"]),
                "check_id": str(row["check_id"]),
                "recommended_priority": str(row["recommended_priority"]),
                "effective_level": str(row["effective_level"]),
            }
            for row in top
        ],
        "registry_inputs_rollup": _registry_inputs_rollup(summary),
        "merge_log_inputs_rollup": _merge_log_inputs_rollup(summary),
    }


def _emit_manifest(manifest_path: Path, output_dir: Path) -> None:
    files = []
    for p in sorted(output_dir.iterdir()):
        if p.is_file():
            files.append({"path": str(p), "size_bytes": p.stat().st_size})
    manifest_path.write_text(
        json.dumps({"files": files}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _build_summary(
    check_dicts: list[dict[str, Any]], strict: bool, repo_root: Path
) -> dict[str, Any]:
    severity_counts = {"hard_fail": 0, "warn": 0, "info": 0}
    status_counts: dict[str, int] = {}
    outcome_counts = {"pass": 0, "fail": 0, "missing": 0}
    effective_level_counts = {"ok": 0, "warning": 0, "error": 0, "info": 0}
    recommended_priority_counts = {"p0": 0, "p1": 0, "p2": 0, "p3": 0}

    for row in check_dicts:
        severity_counts[row["severity"]] += 1
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1
        outcome_counts[row["outcome"]] += 1
        effective_level_counts[row["effective_level"]] += 1
        recommended_priority_counts[row["recommended_priority"]] += 1

    hard_failures = sum(1 for r in check_dicts if r["effective_level"] == "error")
    warnings = sum(1 for r in check_dicts if r["effective_level"] == "warning")
    infos = sum(1 for r in check_dicts if r["effective_level"] == "info")

    summary: dict[str, Any] = {
        "total_checks": len(check_dicts),
        "hard_failures": hard_failures,
        "warnings": warnings,
        "infos": infos,
        "severity_counts": severity_counts,
        "status_counts": status_counts,
        "outcome_counts": outcome_counts,
        "effective_level_counts": effective_level_counts,
        "recommended_priority_counts": recommended_priority_counts,
        "strict": strict,
        "registry_inputs": load_ops_registry_inputs(repo_root),
        "merge_log_inputs": load_ops_merge_log_inputs(repo_root),
        "followup_topic_ranking": build_followup_topic_ranking(check_dicts),
    }
    summary["workflow_officer_provenance"] = build_workflow_officer_provenance()
    summary["handoff_context"] = build_handoff_context(summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Peak_Trade Workflow Officer")
    parser.add_argument("--mode", choices=sorted(MODES), default="audit")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
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
    plans = PROFILES[args.profile]
    for plan in plans:
        results.append(
            _run_check(
                repo_root=repo_root,
                output_dir=run_dir,
                profile=args.profile,
                check_id=plan["check_id"],
                command=plan["command"],
                severity=plan["severity"],
            )
        )

    check_dicts = [_check_to_report_dict(r, p) for r, p in zip(results, plans)]

    _emit_events(run_dir / "events.jsonl", check_dicts)
    _emit_manifest(run_dir / "manifest.json", run_dir)

    summary = _build_summary(check_dicts, strict=bool(args.strict), repo_root=repo_root)
    success = summary["hard_failures"] == 0

    report = WorkflowOfficerReport(
        officer_version="v1-min",
        mode=args.mode,
        profile=args.profile,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        output_dir=str(run_dir),
        repo_root=str(repo_root),
        success=success,
        checks=check_dicts,
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
