from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Optional

MAX_EVIDENCE_AGE_HOURS = 36.0
ALLOWED_EVENTS = {"schedule", "workflow_dispatch"}
PRJ_WORKFLOW = "prj-scheduled-shadow-paper-features-smoke.yml"
PRK_WORKFLOW = "prk-prj-status-report.yml"
PRK_REPORT_FILES = ("prj_status_latest.json", "prj_health_summary.json")


def _parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    value = datetime.fromisoformat(s)
    if value.tzinfo is None:
        raise ValueError("Evidence timestamp requires a time zone")
    return value.astimezone(timezone.utc)


def _now_utc(override: Optional[str]) -> datetime:
    return _parse_iso8601(override) if override else datetime.now(timezone.utc)


def read_stability_gate_ages(
    receipt: dict[str, Any], *, now: datetime | None = None
) -> tuple[str | None, dict[str, float]]:
    """Recheck the original source windows at the point of scorecard use."""
    if isinstance(receipt, dict) and receipt.get("overall_ok") is False:
        return "STABILITY_GATE_FAIL", {}
    if not isinstance(receipt, dict) or receipt.get("overall_ok") is not True:
        return "INVALID_STABILITY_GATE", {}

    now = now if now is not None else _now_utc(None)
    ages: dict[str, float] = {}
    events: dict[str, str] = {}
    new_receipt = "evidence_scope" in receipt
    try:
        generated = _parse_iso8601(receipt["generated_at"])
        if generated > now:
            return "INVALID_STABILITY_GATE", {}
        for row in receipt["results"]:
            name = row["name"]
            created = _parse_iso8601(row["created_at"])
            if name not in ("PR-J", "PR-K") or name in ages or created > generated:
                return "INVALID_STABILITY_GATE", {}
            if new_receipt:
                if row["ok"] is not True or row["event"] not in ALLOWED_EVENTS:
                    return "INVALID_STABILITY_GATE", {}
                if name == "PR-J" and row["run_id"] != receipt["prk_report_prj_run_id"]:
                    return "INVALID_STABILITY_GATE", {}
                events[name] = row["event"]
            ages[name] = (now - created).total_seconds() / 3600
    except (AttributeError, KeyError, TypeError, ValueError):
        return "INVALID_STABILITY_GATE", {}
    if ages.keys() != {"PR-J", "PR-K"}:
        return "INVALID_STABILITY_GATE", {}
    if new_receipt:
        scope = "ON_DEMAND" if "workflow_dispatch" in events.values() else "SCHEDULED"
        if scope != receipt["evidence_scope"] or not _valid_report_digests(
            receipt.get("prk_report_sha256", {})
        ):
            return "INVALID_STABILITY_GATE", {}
    if any(age > MAX_EVIDENCE_AGE_HOURS for age in ages.values()):
        return "STABILITY_GATE_STALE", {}
    return None, ages


def _gh_run_list(workflow: str, branch: str, limit: int) -> list[dict[str, Any]]:
    cmd = [
        "gh",
        "run",
        "list",
        "--workflow",
        workflow,
        "--branch",
        branch,
        "--limit",
        str(limit),
        "--json",
        "databaseId,status,conclusion,createdAt,event",
    ]
    out = subprocess.check_output(cmd, text=True)
    return json.loads(out)


def _read_workflow_evidence(name: str, run_id: int) -> dict[str, Any]:
    base = f"repos/{{owner}}/{{repo}}/actions/runs/{run_id}"
    jobs = json.loads(
        subprocess.check_output(["gh", "api", base + "/jobs?filter=latest"], text=True)
    )["jobs"]
    artifacts = json.loads(subprocess.check_output(["gh", "api", base + "/artifacts"], text=True))[
        "artifacts"
    ]
    job_name, artifact_name = (
        ("prj-features-smoke", "prj-features-smoke")
        if name == "PR-J"
        else ("prj-status-report", "prj-status-report")
    )
    completed = next(
        (job for job in jobs if job["name"] == job_name and job["conclusion"] == "success"),
        None,
    )
    if (
        completed is None
        or sum(item["name"] == artifact_name and item["expired"] is False for item in artifacts)
        != 1
    ):
        return {}
    witness = {"steps": {step["name"]: step["conclusion"] for step in completed["steps"]}}
    if name == "PR-K" and _verified_steps(name, witness["steps"]):
        with tempfile.TemporaryDirectory(prefix="stability-prk-") as directory:
            subprocess.run(
                [
                    "gh",
                    "run",
                    "download",
                    str(run_id),
                    "--name",
                    artifact_name,
                    "--dir",
                    directory,
                ],
                check=True,
            )
            files = {name: Path(directory) / name for name in PRK_REPORT_FILES}
            if all(path.is_file() for path in files.values()):
                contents = {name: path.read_bytes() for name, path in files.items()}
                witness["report"] = json.loads(contents["prj_status_latest.json"])
                witness["report_sha256"] = {
                    name: sha256(content).hexdigest() for name, content in contents.items()
                }
    return witness


def _verified_steps(name: str, steps: dict[str, str]) -> bool:
    if name == "PR-J":
        return (
            steps.get("Run PR-J smoke + evidence") == "success"
            and steps.get("Upload PR-J smoke artifacts") == "success"
        )
    return (
        steps.get("Build mock runs JSON") == "skipped"
        and steps.get("Fetch last 50 PR-J runs (GitHub API)") == "success"
        and steps.get("Upload report artifact") == "success"
    )


def _matching_prj_record(report: dict[str, Any], prj: GateResult, prk_created: datetime) -> bool:
    if prj.created_at is None or _parse_iso8601(prj.created_at) > prk_created:
        return False
    return any(
        item.get("id") == prj.run_id
        and item.get("event") == prj.event
        and item.get("status") == "completed"
        and item.get("conclusion") == "success"
        and item.get("created_at") == prj.created_at
        for item in report.get("runs", [])
    )


def _valid_report_digests(digests: object) -> bool:
    return (
        isinstance(digests, dict)
        and digests.keys() == set(PRK_REPORT_FILES)
        and all(
            isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value)
            for value in digests.values()
        )
    )


@dataclass
class GateResult:
    name: str
    workflow: str
    run_id: Optional[int]
    created_at: Optional[str]
    age_hours: Optional[float]
    ok: bool
    reason: str
    event: str | None = None
    report_sha256: dict[str, str] | None = None


def _evaluate(
    name: str,
    workflow: str,
    branch: str,
    now: datetime,
    limit: int,
    max_age_h: float,
    runs_override: Optional[list[dict[str, Any]]],
    *,
    prj: GateResult | None = None,
) -> GateResult:
    runs = runs_override if runs_override is not None else _gh_run_list(workflow, branch, limit)
    failure = GateResult(name, workflow, None, None, None, False, "NO_SUCCESSFUL_RUN")
    for run in runs:
        event = run.get("event")
        if (
            event not in ALLOWED_EVENTS
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
        ):
            continue
        run_id, created = run["databaseId"], run.get("createdAt")
        if not created:
            return GateResult(
                name, workflow, run_id, None, None, False, "MISSING_CREATED_AT", event
            )
        created_at = _parse_iso8601(created)
        age_h = (now - created_at).total_seconds() / 3600.0
        if age_h < 0:
            return GateResult(
                name, workflow, run_id, created, age_h, False, "FUTURE_CREATED_AT", event
            )
        if age_h > max_age_h:
            if failure.run_id is None:
                return GateResult(
                    name, workflow, run_id, created, age_h, False, "STALE_SUCCESS", event
                )
            return failure
        witness = (
            _read_workflow_evidence(name, run_id)
            if runs_override is None
            else run.get("evidence", {})
        )
        if not _verified_steps(name, witness.get("steps", {})):
            reason = "MISSING_VERIFIED_WORKFLOW_EVIDENCE"
        elif name == "PR-K":
            report_digests = witness.get("report_sha256", {})
            if (
                prj is not None
                and prj.ok
                and _valid_report_digests(report_digests)
                and _matching_prj_record(witness.get("report", {}), prj, created_at)
            ):
                return GateResult(
                    name, workflow, run_id, created, age_h, True, "OK", event, report_digests
                )
            reason = "PRJ_REPORT_SOURCE_MISMATCH"
        else:
            return GateResult(name, workflow, run_id, created, age_h, True, "OK", event)
        if failure.run_id is None:
            failure = GateResult(name, workflow, run_id, created, age_h, False, reason, event)
    return failure


def main() -> int:
    ap = argparse.ArgumentParser(description="Stability gate for matched PR-J and PR-K evidence.")
    ap.add_argument(
        "--out-dir", default="reports/status", help="Output directory for stability_gate.{json,md}"
    )
    ap.add_argument("--branch", default="main")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument(
        "--now", default=None, help="Override now (ISO8601) for deterministic runs/tests."
    )
    ap.add_argument("--max-age-hours-prk", type=float, default=MAX_EVIDENCE_AGE_HOURS)
    ap.add_argument("--max-age-hours-prj", type=float, default=MAX_EVIDENCE_AGE_HOURS)
    ap.add_argument("--prk-workflow", default=PRK_WORKFLOW)
    ap.add_argument("--prj-workflow", default=PRJ_WORKFLOW)
    ap.add_argument(
        "--prk-runs-json", default=None, help="Optional path to runs JSON array (offline)."
    )
    ap.add_argument(
        "--prj-runs-json", default=None, help="Optional path to runs JSON array (offline)."
    )
    args = ap.parse_args()

    now = _now_utc(args.now)

    prk_runs = (
        json.loads(Path(args.prk_runs_json).read_text(encoding="utf-8"))
        if args.prk_runs_json
        else None
    )
    prj_runs = (
        json.loads(Path(args.prj_runs_json).read_text(encoding="utf-8"))
        if args.prj_runs_json
        else None
    )

    prj = _evaluate(
        "PR-J",
        args.prj_workflow,
        args.branch,
        now,
        args.limit,
        float(args.max_age_hours_prj),
        prj_runs,
    )
    prk = _evaluate(
        "PR-K",
        args.prk_workflow,
        args.branch,
        now,
        args.limit,
        float(args.max_age_hours_prk),
        prk_runs,
        prj=prj,
    )

    out = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "branch": args.branch,
        "evidence_scope": (
            ("SCHEDULED" if prj.event == prk.event == "schedule" else "ON_DEMAND")
            if prj.ok and prk.ok
            else None
        ),
        "prk_report_prj_run_id": prj.run_id if prk.ok else None,
        "prk_report_sha256": prk.report_sha256,
        "results": [
            {
                "name": prk.name,
                "workflow": prk.workflow,
                "run_id": prk.run_id,
                "event": prk.event,
                "created_at": prk.created_at,
                "age_hours": prk.age_hours,
                "ok": prk.ok,
                "reason": prk.reason,
            },
            {
                "name": prj.name,
                "workflow": prj.workflow,
                "run_id": prj.run_id,
                "event": prj.event,
                "created_at": prj.created_at,
                "age_hours": prj.age_hours,
                "ok": prj.ok,
                "reason": prj.reason,
            },
        ],
        "overall_ok": bool(prk.ok and prj.ok),
    }

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "stability_gate.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def fmt(r: GateResult) -> str:
        age = "(n/a)" if r.age_hours is None else f"{r.age_hours:.2f}"
        return f"- {r.name}: ok={r.ok} reason={r.reason} age_h={age} run_id={r.run_id}"

    md = [
        f"# Stability Gate — {out['generated_at']}",
        f"- branch: **{args.branch}**",
        f"- overall_ok: **{out['overall_ok']}**",
        f"- evidence_scope: **{out['evidence_scope']}**",
        "",
        "## Results",
        fmt(prk),
        fmt(prj),
    ]
    (outdir / "stability_gate.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return 0 if out["overall_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
