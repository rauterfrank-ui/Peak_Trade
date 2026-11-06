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

from src.ops.truth_officer_integration import build_unified_truth_status
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
# Within same priority + effective_level: failed/missing checks surface before pass; hard_fail before warn/info.
_FOLLOWUP_OUTCOME_URGENCY = {"fail": 0, "missing": 1, "pass": 2}
_FOLLOWUP_SEVERITY_URGENCY = {"hard_fail": 0, "warn": 1, "info": 2}
_FOLLOWUP_RANK_HEURISTIC_VERSION = "workflow_officer.followup_rank_heuristic/v0"

# Handoff context: bounded excerpt for operators (read-only, no extra I/O).
_HANDOFF_CONTEXT_TOP_FOLLOWUPS = 5
_HANDOFF_CONTEXT_SCHEMA_VERSION = "workflow_officer.handoff_context/v1"

_PROVENANCE_SCHEMA_VERSION = "workflow_officer.provenance/v0"
_NEXT_CHAT_PREVIEW_SCHEMA_VERSION = "workflow_officer.next_chat_preview/v1"
_NEXT_CHAT_PREVIEW_QUEUE_LEN = 3
_OPERATOR_REPORT_SCHEMA_VERSION = "workflow_officer.operator_report/v0"
_EXECUTIVE_SUMMARY_SCHEMA_VERSION = "workflow_officer.executive_summary/v0"
_DASHBOARD_VIEW_SCHEMA_VERSION = "workflow_officer.dashboard_view/v0"
_EXECUTIVE_PANEL_VIEW_SCHEMA_VERSION = "workflow_officer.executive_panel_view/v0"
_HANDOFF_OBSERVATION_VIEW_SCHEMA_VERSION = "workflow_officer.handoff_observation_view/v0"
_NEXT_CHAT_PREVIEW_OBSERVATION_VIEW_SCHEMA_VERSION = (
    "workflow_officer.next_chat_preview_observation_view/v0"
)
_MAX_HANDOFF_PREVIEW_OBS_STR = 128

_SEQUENCING_SCHEMA_VERSION = "workflow_officer.sequencing/v0"

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
                [
                    "category",
                    "check_id",
                    "effective_level",
                    "outcome",
                    "recommended_action",
                    "recommended_priority",
                    "sequencing",
                    "severity",
                    "surface",
                ]
            ),
            "ordering_inputs": sorted(
                ["check_id", "effective_level", "outcome", "recommended_priority", "severity"]
            ),
            "rank_heuristic_schema_version": _FOLLOWUP_RANK_HEURISTIC_VERSION,
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
                    "primary_sequencing",
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
        "next_chat_preview": {
            "builder": "build_next_chat_preview",
            "queued_followup_max": _NEXT_CHAT_PREVIEW_QUEUE_LEN,
            "summary_inputs": sorted(["handoff_context", "workflow_officer_provenance"]),
        },
        "operator_report": {
            "builder": "build_operator_report_view",
            "markdown_builder": "render_operator_report_markdown",
            "summary_inputs": sorted(
                [
                    "followup_topic_ranking",
                    "handoff_context",
                    "hard_failures",
                    "infos",
                    "next_chat_preview",
                    "strict",
                    "total_checks",
                    "warnings",
                    "workflow_officer_provenance",
                ]
            ),
        },
        "executive_summary": {
            "builder": "build_executive_summary_view",
            "markdown_builder": "render_executive_summary_markdown",
            "summary_inputs": sorted(
                [
                    "hard_failures",
                    "infos",
                    "operator_report",
                    "strict",
                    "total_checks",
                    "warnings",
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


def _followup_row_sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, str]:
    prio = row.get("recommended_priority")
    eff = row.get("effective_level")
    out = row.get("outcome")
    sev = row.get("severity")
    cid = row.get("check_id", "")
    pr = _FOLLOWUP_PRIORITY_RANK[prio] if prio in _FOLLOWUP_PRIORITY_RANK else 99
    er = _FOLLOWUP_EFFECTIVE_RANK[eff] if eff in _FOLLOWUP_EFFECTIVE_RANK else 99
    or_ = _FOLLOWUP_OUTCOME_URGENCY[out] if out in _FOLLOWUP_OUTCOME_URGENCY else 99
    sr = _FOLLOWUP_SEVERITY_URGENCY[sev] if sev in _FOLLOWUP_SEVERITY_URGENCY else 99
    return (pr, er, or_, sr, str(cid))


def _followup_rank_heuristic_payload(row: dict[str, Any]) -> dict[str, Any]:
    pr, er, or_, sr, _ = _followup_row_sort_key(row)
    return {
        "heuristic_schema_version": _FOLLOWUP_RANK_HEURISTIC_VERSION,
        "components": {
            "priority_rank": pr,
            "effective_level_rank": er,
            "outcome_rank": or_,
            "severity_rank": sr,
        },
        "tie_break": "check_id_ascii",
    }


def _gates_incomplete_from_check_dicts(check_dicts: list[dict[str, Any]]) -> bool:
    for r in check_dicts:
        el = r.get("effective_level")
        if el in ("error", "warning"):
            return True
    return False


def _gates_incomplete_from_summary(summary: dict[str, Any]) -> bool:
    try:
        hf = int(summary.get("hard_failures", 0))
        wn = int(summary.get("warnings", 0))
    except (TypeError, ValueError):
        return True
    return hf > 0 or wn > 0


def _sequencing_topic_blob(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("check_id", "")),
        str(row.get("recommended_action", "")),
        str(row.get("category", "")),
        str(row.get("surface", "")),
    ]
    return " ".join(parts).lower()


def classify_workflow_officer_sequencing(
    row: dict[str, Any],
    *,
    gates_incomplete: bool,
) -> dict[str, Any]:
    """Classify a follow-up topic into a single sequencing bucket (read-only heuristics).

    ``gates_incomplete`` should reflect whether bounded-pilot / truth / ops rollups still
    show unresolved error- or warning-level checks (same signal as summary rollups).
    """
    text = _sequencing_topic_blob(row)
    ai_markers = (
        "ai layer",
        "provider",
        "model",
        "critic",
        "proposer",
        "live ai",
        "llm",
        "enablement",
        "full live",
    )
    build_markers = (
        "execution",
        "ledger",
        "reconciliation",
        "pilot",
        "kill switch",
        "kill-switch",
        "incident",
        "broker",
        "operator",
        "truth",
        "evidence",
        "verify",
        "bounded pilot",
        "gating",
        "reconcile",
    )
    stabilize_markers = (
        "workflow officer",
        "dashboard",
        "wording",
        "regression",
        "docs-only",
        "polish",
        "markdown",
    )

    ai_hit = any(m in text for m in ai_markers)
    build_hit = any(m in text for m in build_markers)
    stab_hit = any(m in text for m in stabilize_markers)

    if ai_hit and gates_incomplete:
        return {
            "sequencing_bucket": "defer_until_prerequisites",
            "sequencing_rationale": (
                "topic expands AI-layer breadth before bounded-pilot, truth, and operator "
                "gating prerequisites are fully satisfied"
            ),
            "prerequisite_signals": [
                "bounded_pilot_clear",
                "truth_and_ops_gates_green",
                "operator_gating_clear",
            ],
            "blocked_by": ["ai_layer_breadth_before_gates"],
            "suggested_next_theme_class": "ai_breadth_after_gates",
            "sequencing_schema_version": _SEQUENCING_SCHEMA_VERSION,
        }
    if build_hit:
        return {
            "sequencing_bucket": "build_now",
            "sequencing_rationale": (
                "execution-adjacent bounded-pilot / truth / ops work is a nearer prerequisite "
                "than broader AI-layer expansion"
            ),
            "prerequisite_signals": ["active_path_hardening"],
            "blocked_by": [],
            "suggested_next_theme_class": "bounded_pilot_truth_ops",
            "sequencing_schema_version": _SEQUENCING_SCHEMA_VERSION,
        }
    if stab_hit:
        return {
            "sequencing_bucket": "stabilize_only",
            "sequencing_rationale": (
                "topic appears to refine an already-built surface rather than unblock the active pilot path"
            ),
            "prerequisite_signals": ["existing_surface_operational"],
            "blocked_by": [],
            "suggested_next_theme_class": "surface_hardening",
            "sequencing_schema_version": _SEQUENCING_SCHEMA_VERSION,
        }
    return {
        "sequencing_bucket": "build_now",
        "sequencing_rationale": (
            "execution-adjacent bounded-pilot / truth / ops work is a nearer prerequisite "
            "than broader AI-layer expansion"
        ),
        "prerequisite_signals": ["default_active_path"],
        "blocked_by": [],
        "suggested_next_theme_class": "bounded_pilot_truth_ops",
        "sequencing_schema_version": _SEQUENCING_SCHEMA_VERSION,
    }


def build_followup_topic_ranking(check_dicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank checks as read-only follow-up topics (no I/O, no mutation).

    Uses only fields already present on each check row. Ordering (ascending tuple,
    more urgent first):

    1. ``recommended_priority`` (p0 … p3)
    2. ``effective_level`` (error, warning, info, ok)
    3. ``outcome`` (fail, missing, pass)
    4. ``severity`` (hard_fail, warn, info)
    5. ``check_id`` (ASCII lexicographic)

    Unknown ``outcome``/``severity``/priority fields sort last within their axis (rank
    99) for stable behavior on partial rows.
    """
    if not check_dicts:
        return []
    ordered = sorted(check_dicts, key=_followup_row_sort_key)
    gates_incomplete = _gates_incomplete_from_check_dicts(check_dicts)
    return [
        {
            "rank": idx,
            "check_id": row["check_id"],
            "recommended_action": str(row.get("recommended_action", "")),
            "recommended_priority": row["recommended_priority"],
            "effective_level": row["effective_level"],
            "surface": row["surface"],
            "category": row["category"],
            "followup_rank_heuristic": _followup_rank_heuristic_payload(row),
            "sequencing": classify_workflow_officer_sequencing(
                row, gates_incomplete=gates_incomplete
            ),
        }
        for idx, row in enumerate(ordered, start=1)
    ]


def build_next_chat_preview(summary: dict[str, Any]) -> dict[str, Any]:
    """Compact read-only cues for the next operator chat (summary dict only, no I/O)."""
    handoff = summary.get("handoff_context")
    if not isinstance(handoff, dict):
        handoff = {}
    prov = summary.get("workflow_officer_provenance")
    if not isinstance(prov, dict):
        prov = {}
    pv = prov.get("provenance_schema_version")
    provenance_schema_version: str | None
    if isinstance(pv, str) and pv.strip():
        provenance_schema_version = pv.strip()
    else:
        provenance_schema_version = None

    rollup = handoff.get("rollup")
    total_checks = hard_failures = warnings = 0
    if isinstance(rollup, dict):
        try:
            total_checks = int(rollup.get("total_checks", 0))
        except (TypeError, ValueError):
            total_checks = 0
        try:
            hard_failures = int(rollup.get("hard_failures", 0))
        except (TypeError, ValueError):
            hard_failures = 0
        try:
            warnings = int(rollup.get("warnings", 0))
        except (TypeError, ValueError):
            warnings = 0

    primary_raw = handoff.get("primary_followup_check_id")
    if primary_raw is not None and isinstance(primary_raw, str) and primary_raw.strip():
        primary_followup_check_id: str | None = primary_raw.strip()
    else:
        primary_followup_check_id = None

    top = handoff.get("top_followups")
    if not isinstance(top, list):
        top = []
    queued_followup_check_ids: list[str] = []
    for row in top[:_NEXT_CHAT_PREVIEW_QUEUE_LEN]:
        if not isinstance(row, dict):
            continue
        cid = row.get("check_id")
        if isinstance(cid, str) and cid.strip():
            queued_followup_check_ids.append(cid.strip())

    reg = handoff.get("registry_inputs_rollup")
    registry_pointer_count: int | None = None
    if isinstance(reg, dict):
        try:
            registry_pointer_count = int(reg.get("pointer_count", 0))
        except (TypeError, ValueError):
            registry_pointer_count = None

    ml = handoff.get("merge_log_inputs_rollup")
    latest_pr_number: int | None = None
    if isinstance(ml, dict):
        raw_pr = ml.get("latest_pr_number")
        if raw_pr is not None:
            try:
                latest_pr_number = int(raw_pr)
            except (TypeError, ValueError):
                latest_pr_number = None

    primary_seq = handoff.get("primary_sequencing")
    if not isinstance(primary_seq, dict):
        primary_seq = None

    return {
        "hard_failures": hard_failures,
        "latest_pr_number": latest_pr_number,
        "preview_schema_version": _NEXT_CHAT_PREVIEW_SCHEMA_VERSION,
        "primary_followup_check_id": primary_followup_check_id,
        "primary_sequencing": primary_seq,
        "provenance_schema_version": provenance_schema_version,
        "queued_followup_check_ids": queued_followup_check_ids,
        "registry_pointer_count": registry_pointer_count,
        "total_checks": total_checks,
        "warnings": warnings,
    }


def render_next_chat_preview_markdown(preview: dict[str, Any]) -> str:
    """Deterministic markdown excerpt for ``summary[\"next_chat_preview\"]`` (read-only, no I/O)."""
    if not isinstance(preview, dict):
        return ""
    schema = preview.get("preview_schema_version")
    if not isinstance(schema, str) or not schema.strip():
        return ""

    def _int_field(key: str) -> str:
        raw = preview.get(key)
        try:
            return str(int(raw))
        except (TypeError, ValueError):
            return "n/a"

    prov = preview.get("provenance_schema_version")
    prov_s = prov.strip() if isinstance(prov, str) and prov.strip() else "n/a"

    primary = preview.get("primary_followup_check_id")
    primary_s = primary.strip() if isinstance(primary, str) and primary.strip() else "n/a"

    queued_raw = preview.get("queued_followup_check_ids")
    if isinstance(queued_raw, list):
        queued = [x.strip() for x in queued_raw if isinstance(x, str) and x.strip()]
    else:
        queued = []

    reg_s = _int_field("registry_pointer_count")
    raw_pr = preview.get("latest_pr_number")
    try:
        pr_s = str(int(raw_pr)) if raw_pr is not None else "n/a"
    except (TypeError, ValueError):
        pr_s = "n/a"

    lines = [
        "## Next chat preview",
        "",
        f"- preview_schema_version: `{schema.strip()}`",
        f"- provenance_schema_version: `{prov_s}`",
        f"- total_checks: `{_int_field('total_checks')}`",
        f"- hard_failures: `{_int_field('hard_failures')}`",
        f"- warnings: `{_int_field('warnings')}`",
        f"- primary_followup_check_id: `{primary_s}`",
    ]
    if queued:
        joined = ", ".join(f"`{cid}`" for cid in queued)
        lines.append(f"- queued_followup_check_ids (order preserved): {joined}")
    else:
        lines.append("- queued_followup_check_ids (order preserved): _(none)_")
    lines.append(f"- registry_pointer_count: `{reg_s}`")
    lines.append(f"- latest_pr_number: `{pr_s}`")
    pseq = preview.get("primary_sequencing")
    if isinstance(pseq, dict):
        bucket = pseq.get("sequencing_bucket")
        rat = pseq.get("sequencing_rationale")
        bucket_s = bucket.strip() if isinstance(bucket, str) and bucket.strip() else "n/a"
        rat_s = rat.strip() if isinstance(rat, str) and rat.strip() else "n/a"
        lines.append(f"- sequencing_bucket: `{bucket_s}`")
        lines.append(f"- sequencing_rationale: {rat_s}")
    return "\n".join(lines) + "\n"


def build_operator_report_view(summary: dict[str, Any]) -> dict[str, Any]:
    """Single read-only operator snapshot built only from an existing summary dict (no I/O)."""
    ranking = summary.get("followup_topic_ranking")
    if not isinstance(ranking, list):
        ranking = []
    handoff = summary.get("handoff_context")
    if not isinstance(handoff, dict):
        handoff = {}
    preview = summary.get("next_chat_preview")
    if not isinstance(preview, dict):
        preview = {}
    prov = summary.get("workflow_officer_provenance")
    if not isinstance(prov, dict):
        prov = {}

    def _safe_int(key: str) -> int:
        raw = summary.get(key)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    primary_followup: dict[str, Any] | None = None
    if ranking and isinstance(ranking[0], dict):
        row = ranking[0]
        h = row.get("followup_rank_heuristic")
        ra_raw = row.get("recommended_action")
        ra_s = str(ra_raw).strip() if isinstance(ra_raw, str) and str(ra_raw).strip() else None
        seq = row.get("sequencing")
        primary_followup = {
            "check_id": str(row.get("check_id", "")),
            "recommended_action": ra_s,
            "recommended_priority": str(row.get("recommended_priority", "")),
            "effective_level": str(row.get("effective_level", "")),
            "followup_rank_heuristic": h if isinstance(h, dict) else None,
            "sequencing": seq if isinstance(seq, dict) else None,
        }

    top_followups: list[dict[str, Any]] = []
    for row in ranking[:5]:
        if not isinstance(row, dict):
            continue
        cid = row.get("check_id")
        if not isinstance(cid, str) or not cid:
            continue
        rk = row.get("rank")
        try:
            rkn = int(rk)
        except (TypeError, ValueError):
            rkn = 0
        seq_r = row.get("sequencing")
        top_followups.append(
            {
                "check_id": cid,
                "effective_level": str(row.get("effective_level", "")),
                "rank": rkn,
                "recommended_priority": str(row.get("recommended_priority", "")),
                "sequencing": seq_r if isinstance(seq_r, dict) else None,
            }
        )

    ft_prov = prov.get("followup_topic_ranking")
    ordering_inputs: list[str] = []
    rank_heuristic_schema_version: str | None = None
    if isinstance(ft_prov, dict):
        oi = ft_prov.get("ordering_inputs")
        if isinstance(oi, list):
            ordering_inputs = [str(x) for x in oi]
        rhs = ft_prov.get("rank_heuristic_schema_version")
        if isinstance(rhs, str) and rhs.strip():
            rank_heuristic_schema_version = rhs.strip()

    prov_schema = prov.get("provenance_schema_version")
    prov_schema_s = (
        prov_schema.strip() if isinstance(prov_schema, str) and prov_schema.strip() else None
    )

    reg = handoff.get("registry_inputs_rollup")
    reg_out: dict[str, Any] = {
        "pointer_count": 0,
        "primary_run_id": None,
        "registry_dir_present": False,
    }
    if isinstance(reg, dict):
        reg_out["registry_dir_present"] = bool(reg.get("registry_dir_present", False))
        try:
            reg_out["pointer_count"] = int(reg.get("pointer_count", 0))
        except (TypeError, ValueError):
            reg_out["pointer_count"] = 0
        prid = reg.get("primary_run_id")
        reg_out["primary_run_id"] = (
            str(prid).strip() if isinstance(prid, str) and str(prid).strip() else None
        )

    ml = handoff.get("merge_log_inputs_rollup")
    ml_out: dict[str, Any] = {
        "canonical_merge_log_count": 0,
        "latest_merge_commit_sha": None,
        "latest_pr_number": None,
        "merge_logs_dir_present": False,
    }
    if isinstance(ml, dict):
        ml_out["merge_logs_dir_present"] = bool(ml.get("merge_logs_dir_present", False))
        try:
            ml_out["canonical_merge_log_count"] = int(ml.get("canonical_merge_log_count", 0))
        except (TypeError, ValueError):
            ml_out["canonical_merge_log_count"] = 0
        lpr = ml.get("latest_pr_number")
        if lpr is not None:
            try:
                ml_out["latest_pr_number"] = int(lpr)
            except (TypeError, ValueError):
                ml_out["latest_pr_number"] = None
        sha = ml.get("latest_merge_commit_sha")
        if isinstance(sha, str) and sha.strip():
            ml_out["latest_merge_commit_sha"] = sha.strip().lower()

    qc = preview.get("queued_followup_check_ids")
    queued: list[str] = []
    if isinstance(qc, list):
        queued = [str(x).strip() for x in qc if isinstance(x, str) and str(x).strip()]

    prim_prev = preview.get("primary_followup_check_id")
    prim_prev_s = (
        str(prim_prev).strip() if prim_prev is not None and str(prim_prev).strip() else None
    )

    lpr_p = preview.get("latest_pr_number")
    try:
        latest_pr_prev = int(lpr_p) if lpr_p is not None else None
    except (TypeError, ValueError):
        latest_pr_prev = None

    rpc = preview.get("registry_pointer_count")
    try:
        reg_ptr_prev = int(rpc) if rpc is not None else None
    except (TypeError, ValueError):
        reg_ptr_prev = None

    return {
        "merge_log_signals": ml_out,
        "next_chat_essentials": {
            "latest_pr_number": latest_pr_prev,
            "primary_followup_check_id": prim_prev_s,
            "queued_followup_check_ids": queued,
            "registry_pointer_count": reg_ptr_prev,
        },
        "operator_report_schema_version": _OPERATOR_REPORT_SCHEMA_VERSION,
        "primary_followup": primary_followup,
        "provenance_schema_version": prov_schema_s,
        "ranking_basis": {
            "ordering_inputs": ordering_inputs,
            "rank_heuristic_schema_version": rank_heuristic_schema_version,
        },
        "registry_signals": reg_out,
        "rollup": {
            "hard_failures": _safe_int("hard_failures"),
            "infos": _safe_int("infos"),
            "total_checks": _safe_int("total_checks"),
            "warnings": _safe_int("warnings"),
        },
        "strict": bool(summary.get("strict", False)),
        "top_followups": top_followups,
    }


def render_operator_report_markdown(operator_report: dict[str, Any]) -> str:
    """Deterministic markdown excerpt for ``summary[\"operator_report\"]`` (read-only, no I/O)."""
    if not isinstance(operator_report, dict):
        return ""
    schema = operator_report.get("operator_report_schema_version")
    if not isinstance(schema, str) or not schema.strip():
        return ""

    def _yn(val: bool) -> str:
        return "yes" if val else "no"

    lines = [
        "## Operator consolidated view",
        "",
        f"- operator_report_schema_version: `{schema.strip()}`",
        f"- strict: `{_yn(bool(operator_report.get('strict', False)))}`",
    ]
    rollup = operator_report.get("rollup")
    if isinstance(rollup, dict):
        lines.append(
            f"- rollup: total `{rollup.get('total_checks', 0)}`, "
            f"errors `{rollup.get('hard_failures', 0)}`, warnings `{rollup.get('warnings', 0)}`, "
            f"infos `{rollup.get('infos', 0)}`"
        )
    pf = operator_report.get("primary_followup")
    if isinstance(pf, dict) and pf.get("check_id"):
        lines.append(
            f"- primary follow-up: `{pf['check_id']}` "
            f"(priority `{pf.get('recommended_priority', '')}`, level `{pf.get('effective_level', '')}`)"
        )
        hr = pf.get("followup_rank_heuristic")
        if isinstance(hr, dict):
            comp = hr.get("components")
            if isinstance(comp, dict):
                lines.append(
                    "- ranking heuristic (primary): "
                    f"`priority_rank={comp.get('priority_rank')}` "
                    f"`effective_level_rank={comp.get('effective_level_rank')}` "
                    f"`outcome_rank={comp.get('outcome_rank')}` "
                    f"`severity_rank={comp.get('severity_rank')}`"
                )
        seqp = pf.get("sequencing")
        if isinstance(seqp, dict):
            sb = seqp.get("sequencing_bucket")
            sr = seqp.get("sequencing_rationale")
            if isinstance(sb, str) and sb.strip():
                lines.append(f"- primary sequencing_bucket: `{sb.strip()}`")
            if isinstance(sr, str) and sr.strip():
                lines.append(f"- primary sequencing_rationale: {sr.strip()}")
    basis = operator_report.get("ranking_basis")
    if isinstance(basis, dict):
        oi = basis.get("ordering_inputs")
        if isinstance(oi, list) and oi:
            lines.append("- ranking tie order: " + ", ".join(oi))
        rhs = basis.get("rank_heuristic_schema_version")
        if isinstance(rhs, str) and rhs.strip():
            lines.append(f"- rank heuristic schema: `{rhs.strip()}`")

    tops = operator_report.get("top_followups")
    if isinstance(tops, list) and tops:
        parts: list[str] = []
        for t in tops[:5]:
            if isinstance(t, dict) and t.get("check_id"):
                parts.append(f"`{t['check_id']}` rank {t.get('rank', '')}")
        if parts:
            lines.append("- top follow-ups: " + ", ".join(parts))

    nce = operator_report.get("next_chat_essentials")
    if isinstance(nce, dict):
        lpr = nce.get("latest_pr_number")
        lpr_s = str(lpr) if lpr is not None else "n/a"
        lines.append(
            f"- next-chat essentials: primary `{nce.get('primary_followup_check_id') or 'n/a'}`, "
            f"latest_pr `{lpr_s}`"
        )
        q = nce.get("queued_followup_check_ids")
        if isinstance(q, list) and q:
            lines.append("- next-chat queue: " + ", ".join(f"`{x}`" for x in q))

    reg = operator_report.get("registry_signals")
    if isinstance(reg, dict):
        lines.append(
            f"- registry: present=`{_yn(bool(reg.get('registry_dir_present')))}`, "
            f"pointers=`{reg.get('pointer_count', 0)}`, "
            f"primary_run_id=`{reg.get('primary_run_id') or 'n/a'}`"
        )

    ml = operator_report.get("merge_log_signals")
    if isinstance(ml, dict):
        mlpr = ml.get("latest_pr_number")
        mlpr_s = str(mlpr) if mlpr is not None else "n/a"
        lines.append(
            f"- merge logs: present=`{_yn(bool(ml.get('merge_logs_dir_present')))}`, "
            f"count=`{ml.get('canonical_merge_log_count', 0)}`, "
            f"latest_pr=`{mlpr_s}`"
        )

    provs = operator_report.get("provenance_schema_version")
    if isinstance(provs, str) and provs.strip():
        lines.append(f"- provenance schema: `{provs.strip()}`")

    lines.append("")
    return "\n".join(lines)


def build_executive_summary_view(summary: dict[str, Any]) -> dict[str, Any]:
    """Embedded decision-package slice from ``operator_report`` plus top-level rollups (read-only, no I/O)."""
    op = summary.get("operator_report")
    if not isinstance(op, dict):
        op = {}

    def _safe_int(key: str) -> int:
        raw = summary.get(key)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    hard_failures = _safe_int("hard_failures")
    warnings = _safe_int("warnings")
    infos = _safe_int("infos")
    total_checks = _safe_int("total_checks")
    strict = bool(summary.get("strict", False))

    pf = op.get("primary_followup")
    primary: dict[str, Any] | None = pf if isinstance(pf, dict) else None

    def _urgency_label() -> str:
        if total_checks == 0:
            return "none"
        if hard_failures > 0:
            return "critical"
        if primary is None:
            return "clear"
        prio = primary.get("recommended_priority")
        if prio == "p0":
            return "critical"
        if prio == "p1":
            return "elevated"
        if prio == "p2":
            return "moderate"
        return "clear"

    def _attention_rationale() -> str:
        if total_checks == 0:
            return "No checks recorded; nothing to action."
        if hard_failures > 0:
            return (
                "One or more hard-fail checks failed or are missing required targets; "
                "remediate before relying on this path."
            )
        if warnings > 0:
            return "Warning-level findings need review before treating this run as clean."
        if strict and (warnings > 0 or infos > 0):
            return "Strict mode flags non-zero warning or info counts."
        if infos > 0:
            return "Informational-only signals; verify manually if relevant to your change."
        return "No blocking errors; routine documentation or hygiene follow-ups only."

    primary_out: dict[str, Any] = {
        "check_id": None,
        "effective_level": None,
        "recommended_action_excerpt": None,
        "recommended_priority": None,
        "sequencing": None,
    }
    if primary is not None:
        cid = primary.get("check_id")
        primary_out["check_id"] = (
            str(cid).strip() if isinstance(cid, str) and str(cid).strip() else None
        )
        el = primary.get("effective_level")
        primary_out["effective_level"] = (
            str(el).strip() if isinstance(el, str) and str(el).strip() else None
        )
        rp = primary.get("recommended_priority")
        primary_out["recommended_priority"] = (
            str(rp).strip() if isinstance(rp, str) and str(rp).strip() else None
        )
        ra = primary.get("recommended_action")
        if isinstance(ra, str) and ra.strip():
            excerpt = ra.strip()
            if len(excerpt) > 160:
                excerpt = excerpt[:157] + "..."
            primary_out["recommended_action_excerpt"] = excerpt
        else:
            primary_out["recommended_action_excerpt"] = None
        ps = primary.get("sequencing")
        primary_out["sequencing"] = ps if isinstance(ps, dict) else None

    top_slice: list[dict[str, Any]] = []
    tops = op.get("top_followups")
    if isinstance(tops, list):
        for row in tops[:3]:
            if not isinstance(row, dict):
                continue
            cid = row.get("check_id")
            if not isinstance(cid, str) or not cid.strip():
                continue
            rk = row.get("rank")
            try:
                rkn = int(rk)
            except (TypeError, ValueError):
                rkn = 0
            seq_t = row.get("sequencing")
            top_slice.append(
                {
                    "rank": rkn,
                    "check_id": cid.strip(),
                    "effective_level": str(row.get("effective_level", "")),
                    "recommended_priority": str(row.get("recommended_priority", "")),
                    "sequencing": seq_t if isinstance(seq_t, dict) else None,
                }
            )

    supporting_signals: list[str] = []
    rollup = op.get("rollup")
    if isinstance(rollup, dict):
        try:
            tc = int(rollup.get("total_checks", 0))
        except (TypeError, ValueError):
            tc = 0
        try:
            hf = int(rollup.get("hard_failures", 0))
        except (TypeError, ValueError):
            hf = 0
        try:
            wn = int(rollup.get("warnings", 0))
        except (TypeError, ValueError):
            wn = 0
        try:
            inf = int(rollup.get("infos", 0))
        except (TypeError, ValueError):
            inf = 0
        supporting_signals.append(f"rollup_total={tc} errors={hf} warnings={wn} infos={inf}")
    supporting_signals.append(f"strict={'yes' if strict else 'no'}")

    basis = op.get("ranking_basis")
    if isinstance(basis, dict):
        rhs = basis.get("rank_heuristic_schema_version")
        if isinstance(rhs, str) and rhs.strip():
            supporting_signals.append(f"rank_heuristic_schema={rhs.strip()}")

    if primary is not None:
        hr = primary.get("followup_rank_heuristic")
        if isinstance(hr, dict):
            comp = hr.get("components")
            if isinstance(comp, dict):
                supporting_signals.append(
                    "primary_heuristic_ranks: "
                    f"priority={comp.get('priority_rank')} "
                    f"effective_level={comp.get('effective_level_rank')} "
                    f"outcome={comp.get('outcome_rank')} "
                    f"severity={comp.get('severity_rank')}"
                )

    reg = op.get("registry_signals")
    if isinstance(reg, dict):
        prid = reg.get("primary_run_id")
        prid_s = str(prid).strip() if isinstance(prid, str) and str(prid).strip() else "n/a"
        try:
            pc = int(reg.get("pointer_count", 0))
        except (TypeError, ValueError):
            pc = 0
        supporting_signals.append(f"registry_pointers={pc} primary_run_id={prid_s}")

    ml = op.get("merge_log_signals")
    if isinstance(ml, dict):
        try:
            mcc = int(ml.get("canonical_merge_log_count", 0))
        except (TypeError, ValueError):
            mcc = 0
        lpr = ml.get("latest_pr_number")
        try:
            lpr_s = str(int(lpr)) if lpr is not None else "n/a"
        except (TypeError, ValueError):
            lpr_s = "n/a"
        supporting_signals.append(f"merge_logs_count={mcc} latest_pr={lpr_s}")

    nce = op.get("next_chat_essentials")
    handoff_out: dict[str, Any] = {
        "latest_pr_number": None,
        "primary_followup_check_id": None,
        "queued_followup_check_ids": [],
        "registry_pointer_count": None,
    }
    if isinstance(nce, dict):
        lpr = nce.get("latest_pr_number")
        try:
            handoff_out["latest_pr_number"] = int(lpr) if lpr is not None else None
        except (TypeError, ValueError):
            handoff_out["latest_pr_number"] = None
        pfc = nce.get("primary_followup_check_id")
        handoff_out["primary_followup_check_id"] = (
            str(pfc).strip() if isinstance(pfc, str) and str(pfc).strip() else None
        )
        rpc = nce.get("registry_pointer_count")
        try:
            handoff_out["registry_pointer_count"] = int(rpc) if rpc is not None else None
        except (TypeError, ValueError):
            handoff_out["registry_pointer_count"] = None
        qc = nce.get("queued_followup_check_ids")
        if isinstance(qc, list):
            handoff_out["queued_followup_check_ids"] = [
                str(x).strip() for x in qc if isinstance(x, str) and str(x).strip()
            ][:3]

    prov = op.get("provenance_schema_version")
    prov_s = prov.strip() if isinstance(prov, str) and prov.strip() else None

    return {
        "attention_rationale": _attention_rationale(),
        "executive_summary_schema_version": _EXECUTIVE_SUMMARY_SCHEMA_VERSION,
        "next_chat_handoff": handoff_out,
        "primary_recommendation": primary_out,
        "provenance_schema_version": prov_s,
        "rollup_snapshot": {
            "hard_failures": hard_failures,
            "infos": infos,
            "strict": strict,
            "total_checks": total_checks,
            "warnings": warnings,
        },
        "supporting_signals": supporting_signals,
        "top_followups": top_slice,
        "urgency_label": _urgency_label(),
    }


def render_executive_summary_markdown(executive: dict[str, Any]) -> str:
    """Deterministic markdown for ``summary[\"executive_summary\"]`` (read-only, no I/O)."""
    if not isinstance(executive, dict):
        return ""
    schema = executive.get("executive_summary_schema_version")
    if not isinstance(schema, str) or not schema.strip():
        return ""

    lines = [
        "## Executive decision package",
        "",
        f"- executive_summary_schema_version: `{schema.strip()}`",
    ]
    prov = executive.get("provenance_schema_version")
    prov_s = prov.strip() if isinstance(prov, str) and prov.strip() else "n/a"
    lines.append(f"- provenance_schema_version: `{prov_s}`")
    lines.append(f"- urgency_label: `{executive.get('urgency_label', '')}`")

    pr = executive.get("primary_recommendation")
    if isinstance(pr, dict) and pr.get("check_id"):
        lines.append(
            f"- primary: `{pr['check_id']}` priority `{pr.get('recommended_priority') or 'n/a'}` "
            f"level `{pr.get('effective_level') or 'n/a'}`"
        )
        ex = pr.get("recommended_action_excerpt")
        if isinstance(ex, str) and ex.strip():
            lines.append(f"- primary action (excerpt): {ex.strip()}")
        sq = pr.get("sequencing")
        if isinstance(sq, dict):
            sb = sq.get("sequencing_bucket")
            sr = sq.get("sequencing_rationale")
            if isinstance(sb, str) and sb.strip():
                lines.append(f"- primary sequencing_bucket: `{sb.strip()}`")
            if isinstance(sr, str) and sr.strip():
                lines.append(f"- primary sequencing_rationale: {sr.strip()}")
    else:
        lines.append("- primary: _(none)_")

    ar = executive.get("attention_rationale")
    if isinstance(ar, str) and ar.strip():
        lines.append(f"- why now: {ar.strip()}")

    tops = executive.get("top_followups")
    if isinstance(tops, list) and tops:
        parts: list[str] = []
        for t in tops[:3]:
            if isinstance(t, dict) and t.get("check_id"):
                parts.append(
                    f"`{t['check_id']}` rank {t.get('rank', '')} "
                    f"({t.get('recommended_priority', '')}/{t.get('effective_level', '')})"
                )
        if parts:
            lines.append("- top follow-ups: " + "; ".join(parts))
    else:
        lines.append("- top follow-ups: _(none)_")

    sigs = executive.get("supporting_signals")
    if isinstance(sigs, list) and sigs:
        lines.append("- supporting signals:")
        for s in sigs:
            if isinstance(s, str) and s.strip():
                lines.append(f"  - {s.strip()}")
    else:
        lines.append("- supporting signals: _(none)_")

    nch = executive.get("next_chat_handoff")
    if isinstance(nch, dict):
        lpr = nch.get("latest_pr_number")
        try:
            lpr_s = str(int(lpr)) if lpr is not None else "n/a"
        except (TypeError, ValueError):
            lpr_s = "n/a"
        q = nch.get("queued_followup_check_ids")
        if isinstance(q, list) and q:
            qjoin = ", ".join(f"`{x}`" for x in q if isinstance(x, str))
            qline = qjoin if qjoin else "_(none)_"
        else:
            qline = "_(none)_"
        pfc = nch.get("primary_followup_check_id") or "n/a"
        rpc = nch.get("registry_pointer_count")
        try:
            rpc_s = str(int(rpc)) if rpc is not None else "n/a"
        except (TypeError, ValueError):
            rpc_s = "n/a"
        lines.append(
            f"- next-chat handoff: primary `{pfc}` queue {qline} "
            f"latest_pr `{lpr_s}` registry_pointers `{rpc_s}`"
        )

    rs = executive.get("rollup_snapshot")
    if isinstance(rs, dict):
        lines.append(
            f"- rollup snapshot: total `{rs.get('total_checks', 0)}` errors `{rs.get('hard_failures', 0)}` "
            f"warnings `{rs.get('warnings', 0)}` infos `{rs.get('infos', 0)}` "
            f"strict `{'yes' if rs.get('strict') else 'no'}`"
        )

    lines.append("")
    return "\n".join(lines)


def _build_executive_panel_view_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Read-only WebUI executive slice: canonical ``build_executive_summary_view`` + markdown preview (no I/O)."""
    ex = build_executive_summary_view(summary)
    md = render_executive_summary_markdown(ex)
    preview_lines = [ln for ln in md.splitlines() if ln.strip()][:32]
    pr = ex.get("primary_recommendation")
    primary_out: dict[str, Any] | None = None
    if isinstance(pr, dict) and pr.get("check_id"):
        primary_out = {
            "check_id": pr.get("check_id"),
            "recommended_priority": pr.get("recommended_priority"),
            "effective_level": pr.get("effective_level"),
            "recommended_action_excerpt": pr.get("recommended_action_excerpt"),
            "sequencing": pr.get("sequencing"),
        }
    tops: list[dict[str, Any]] = []
    for row in (ex.get("top_followups") or [])[:3]:
        if isinstance(row, dict) and row.get("check_id"):
            tops.append(
                {
                    "rank": row.get("rank"),
                    "check_id": str(row.get("check_id", "")).strip(),
                    "recommended_priority": str(row.get("recommended_priority", "")),
                    "effective_level": str(row.get("effective_level", "")),
                }
            )
    sigs: list[str] = []
    for s in (ex.get("supporting_signals") or [])[:8]:
        if isinstance(s, str) and s.strip():
            sigs.append(s.strip())
    nch = ex.get("next_chat_handoff")
    handoff = nch if isinstance(nch, dict) else None
    rs = ex.get("rollup_snapshot")
    rollup_snapshot = rs if isinstance(rs, dict) else None
    return {
        "present": True,
        "executive_panel_schema_version": _EXECUTIVE_PANEL_VIEW_SCHEMA_VERSION,
        "executive_summary_schema_version": ex.get("executive_summary_schema_version"),
        "urgency_label": ex.get("urgency_label"),
        "attention_rationale": ex.get("attention_rationale"),
        "primary_recommendation": primary_out,
        "top_followups": tops,
        "supporting_signals": sigs,
        "rollup_snapshot": rollup_snapshot,
        "next_chat_handoff": handoff,
        "provenance_schema_version": ex.get("provenance_schema_version"),
        "decision_package_preview_lines": preview_lines,
    }


def _dashboard_empty(reason: str) -> dict[str, Any]:
    return {
        "present": False,
        "dashboard_schema_version": _DASHBOARD_VIEW_SCHEMA_VERSION,
        "empty_reason": reason,
        "executive_panel": {
            "present": False,
            "executive_panel_schema_version": _EXECUTIVE_PANEL_VIEW_SCHEMA_VERSION,
            "empty_reason": reason,
        },
    }


def _truncate_handoff_preview_obs_str(val: object | None) -> str | None:
    if val is None:
        return None
    if not isinstance(val, str):
        s = str(val).strip()
    else:
        s = val.strip()
    if not s:
        return None
    if len(s) <= _MAX_HANDOFF_PREVIEW_OBS_STR:
        return s
    return s[: _MAX_HANDOFF_PREVIEW_OBS_STR - 3] + "..."


def build_handoff_observation_view(summary: dict[str, Any]) -> dict[str, Any]:
    """Bounded read-only digest of ``summary[\"handoff_context\"]`` for Ops Cockpit (no I/O)."""
    hc = summary.get("handoff_context")
    if not isinstance(hc, dict) or not hc:
        return {
            "absent_reason": "no_handoff_context_in_report",
            "handoff_observation_schema_version": _HANDOFF_OBSERVATION_VIEW_SCHEMA_VERSION,
            "present": False,
        }
    top = hc.get("top_followups")
    tcount = len(top) if isinstance(top, list) else 0
    primary_s = _truncate_handoff_preview_obs_str(hc.get("primary_followup_check_id"))
    hs_s = _truncate_handoff_preview_obs_str(hc.get("handoff_schema_version"))

    reg = hc.get("registry_inputs_rollup")
    rpc: int | None = None
    if isinstance(reg, dict):
        try:
            rpc = int(reg.get("pointer_count", 0))
        except (TypeError, ValueError):
            rpc = None

    ml = hc.get("merge_log_inputs_rollup")
    lpr: int | None = None
    if isinstance(ml, dict):
        raw_pr = ml.get("latest_pr_number")
        if raw_pr is not None:
            try:
                lpr = int(raw_pr)
            except (TypeError, ValueError):
                lpr = None

    return {
        "handoff_observation_schema_version": _HANDOFF_OBSERVATION_VIEW_SCHEMA_VERSION,
        "handoff_schema_version": hs_s,
        "merge_log_latest_pr_number": lpr,
        "present": True,
        "primary_followup_check_id": primary_s,
        "registry_pointer_count": rpc,
        "top_followups_count": min(int(tcount), 9999),
    }


def build_next_chat_preview_observation_view(summary: dict[str, Any]) -> dict[str, Any]:
    """Bounded read-only digest of ``summary[\"next_chat_preview\"]`` for Ops Cockpit (no I/O)."""
    ncp = summary.get("next_chat_preview")
    if not isinstance(ncp, dict) or not ncp:
        return {
            "absent_reason": "no_next_chat_preview_in_report",
            "next_chat_preview_observation_schema_version": _NEXT_CHAT_PREVIEW_OBSERVATION_VIEW_SCHEMA_VERSION,
            "present": False,
        }

    pv_s = _truncate_handoff_preview_obs_str(ncp.get("preview_schema_version"))
    prov_s = _truncate_handoff_preview_obs_str(ncp.get("provenance_schema_version"))
    prim_s = _truncate_handoff_preview_obs_str(ncp.get("primary_followup_check_id"))

    q_raw = ncp.get("queued_followup_check_ids")
    queued: list[str] = []
    if isinstance(q_raw, list):
        for x in q_raw[:_NEXT_CHAT_PREVIEW_QUEUE_LEN]:
            ts = _truncate_handoff_preview_obs_str(x)
            if ts:
                queued.append(ts)

    lpr: int | None = None
    raw_pr = ncp.get("latest_pr_number")
    if raw_pr is not None:
        try:
            lpr = int(raw_pr)
        except (TypeError, ValueError):
            lpr = None

    rpc: int | None = None
    raw_rpc = ncp.get("registry_pointer_count")
    if raw_rpc is not None:
        try:
            rpc = int(raw_rpc)
        except (TypeError, ValueError):
            rpc = None

    def _ri(key: str) -> int:
        try:
            return int(ncp.get(key, 0))
        except (TypeError, ValueError):
            return 0

    return {
        "latest_pr_number": lpr,
        "next_chat_preview_observation_schema_version": _NEXT_CHAT_PREVIEW_OBSERVATION_VIEW_SCHEMA_VERSION,
        "present": True,
        "preview_schema_version": pv_s,
        "primary_followup_check_id": prim_s,
        "provenance_schema_version": prov_s,
        "queued_followup_check_ids": queued,
        "registry_pointer_count": rpc,
        "rollup_echo": {
            "hard_failures": _ri("hard_failures"),
            "total_checks": _ri("total_checks"),
            "warnings": _ri("warnings"),
        },
    }


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
    gi = _gates_incomplete_from_summary(summary)

    def _row_sequencing(row: dict[str, Any]) -> dict[str, Any]:
        raw = row.get("sequencing")
        if isinstance(raw, dict) and raw.get("sequencing_schema_version"):
            return raw
        return classify_workflow_officer_sequencing(row, gates_incomplete=gi)

    primary_sequencing: dict[str, Any] | None = None
    if ranking and isinstance(ranking[0], dict):
        primary_sequencing = _row_sequencing(ranking[0])

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
        "primary_sequencing": primary_sequencing,
        "top_followups": [
            {
                "rank": int(row["rank"]),
                "check_id": str(row["check_id"]),
                "recommended_priority": str(row["recommended_priority"]),
                "effective_level": str(row["effective_level"]),
                "sequencing": _row_sequencing(row),
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
    hc = summary["handoff_context"]
    summary["primary_sequencing"] = hc.get("primary_sequencing") if isinstance(hc, dict) else None
    summary["next_chat_preview"] = build_next_chat_preview(summary)
    summary["operator_report"] = build_operator_report_view(summary)
    summary["executive_summary"] = build_executive_summary_view(summary)
    summary["unified_truth_status"] = build_unified_truth_status(repo_root)
    return summary


def build_workflow_officer_dashboard_view(repo_root: Path) -> dict[str, Any]:
    """Read-only WebUI slice: latest ``report.json`` under ``out/ops/workflow_officer`` (no writes)."""
    out_root = repo_root / "out" / "ops" / "workflow_officer"
    if not out_root.is_dir():
        return _dashboard_empty("no_officer_output_dir")
    run_dirs = sorted([p for p in out_root.iterdir() if p.is_dir()], key=lambda p: p.name)
    if not run_dirs:
        return _dashboard_empty("no_officer_runs")
    latest = run_dirs[-1]
    report_path = latest / "report.json"
    if not report_path.is_file():
        return _dashboard_empty("no_report_json")
    try:
        raw = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return _dashboard_empty("report_unreadable")
    if not isinstance(raw, dict):
        return _dashboard_empty("invalid_report")
    summary = raw.get("summary")
    if not isinstance(summary, dict):
        return _dashboard_empty("invalid_report")

    ex = summary.get("executive_summary")
    op = summary.get("operator_report")
    ranking = summary.get("followup_topic_ranking")

    top_followups: list[dict[str, Any]] = []
    if isinstance(op, dict) and isinstance(op.get("top_followups"), list):
        for row in op["top_followups"][:3]:
            if not isinstance(row, dict):
                continue
            cid = row.get("check_id")
            if not isinstance(cid, str) or not cid.strip():
                continue
            top_followups.append(
                {
                    "rank": row.get("rank"),
                    "check_id": cid.strip(),
                    "recommended_priority": str(row.get("recommended_priority", "")),
                    "effective_level": str(row.get("effective_level", "")),
                }
            )
    elif isinstance(ranking, list):
        for row in ranking[:3]:
            if not isinstance(row, dict):
                continue
            cid = row.get("check_id")
            if not isinstance(cid, str) or not cid.strip():
                continue
            top_followups.append(
                {
                    "rank": row.get("rank"),
                    "check_id": cid.strip(),
                    "recommended_priority": str(row.get("recommended_priority", "")),
                    "effective_level": str(row.get("effective_level", "")),
                }
            )

    primary_followup: dict[str, Any] | None = None
    if isinstance(op, dict):
        pf = op.get("primary_followup")
        if isinstance(pf, dict) and pf.get("check_id"):
            primary_followup = {
                "check_id": str(pf.get("check_id", "")),
                "recommended_priority": str(pf.get("recommended_priority", "")),
                "effective_level": str(pf.get("effective_level", "")),
            }
            ra = pf.get("recommended_action")
            if isinstance(ra, str) and ra.strip():
                excerpt = ra.strip()
                if len(excerpt) > 120:
                    excerpt = excerpt[:117] + "..."
                primary_followup["recommended_action_excerpt"] = excerpt
            else:
                primary_followup["recommended_action_excerpt"] = None

    urgency: str | None = None
    attention: str | None = None
    exec_schema: str | None = None
    if isinstance(ex, dict):
        u = ex.get("urgency_label")
        urgency = str(u).strip() if isinstance(u, str) and u.strip() else None
        a = ex.get("attention_rationale")
        attention = str(a).strip() if isinstance(a, str) and a.strip() else None
        evs = ex.get("executive_summary_schema_version")
        exec_schema = str(evs).strip() if isinstance(evs, str) and evs.strip() else None

    operator_line = ""
    if isinstance(op, dict):
        r = op.get("rollup")
        if isinstance(r, dict):
            operator_line = (
                f"total={r.get('total_checks')} errors={r.get('hard_failures')} "
                f"warnings={r.get('warnings')} infos={r.get('infos')}"
            )

    rel = str(report_path.relative_to(repo_root).as_posix())
    return {
        "present": True,
        "dashboard_schema_version": _DASHBOARD_VIEW_SCHEMA_VERSION,
        "empty_reason": None,
        "run_dir_name": latest.name,
        "report_rel_path": rel,
        "officer_version": raw.get("officer_version"),
        "profile": raw.get("profile"),
        "mode": raw.get("mode"),
        "success": raw.get("success"),
        "finished_at": raw.get("finished_at"),
        "rollup": {
            "total_checks": summary.get("total_checks"),
            "hard_failures": summary.get("hard_failures"),
            "warnings": summary.get("warnings"),
            "infos": summary.get("infos"),
            "strict": summary.get("strict"),
        },
        "executive": {
            "urgency_label": urgency,
            "attention_rationale": attention,
            "schema_version": exec_schema,
        },
        "primary_followup": primary_followup,
        "top_followups": top_followups,
        "operator_snapshot_line": operator_line,
        "executive_panel": _build_executive_panel_view_from_summary(summary),
        "handoff_observation": build_handoff_observation_view(summary),
        "next_chat_preview_observation": build_next_chat_preview_observation_view(summary),
    }


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
