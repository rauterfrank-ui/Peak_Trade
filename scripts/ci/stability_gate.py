from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _now_utc(override: Optional[str]) -> datetime:
    return _parse_iso8601(override) if override else datetime.now(timezone.utc)


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


def _latest_success_schedule(runs: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for r in runs:
        if (
            r.get("event") == "schedule"
            and r.get("status") == "completed"
            and r.get("conclusion") == "success"
        ):
            return r
    return None


@dataclass
class GateResult:
    name: str
    workflow: str
    run_id: Optional[int]
    created_at: Optional[str]
    age_hours: Optional[float]
    ok: bool
    reason: str


def _evaluate(
    name: str,
    workflow: str,
    branch: str,
    now: datetime,
    limit: int,
    max_age_h: float,
    runs_override: Optional[list[dict[str, Any]]],
) -> GateResult:
    runs = runs_override if runs_override is not None else _gh_run_list(workflow, branch, limit)
    hit = _latest_success_schedule(runs)
    if not hit:
        return GateResult(name, workflow, None, None, None, False, "NO_SCHEDULE_SUCCESS")
    created = hit.get("createdAt")
    age_h = (now - _parse_iso8601(created)).total_seconds() / 3600.0 if created else None
    if age_h is None:
        return GateResult(
            name, workflow, int(hit.get("databaseId")), created, None, False, "MISSING_CREATED_AT"
        )
    if age_h > max_age_h:
        return GateResult(
            name,
            workflow,
            int(hit.get("databaseId")),
            created,
            age_h,
            False,
            "STALE_SCHEDULE_SUCCESS",
        )
    return GateResult(name, workflow, int(hit.get("databaseId")), created, age_h, True, "OK")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stability gate for PR-J and PR-K schedule freshness.")
    ap.add_argument(
        "--out-dir", default="reports/status", help="Output directory for stability_gate.{json,md}"
    )
    ap.add_argument("--branch", default="main")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument(
        "--now", default=None, help="Override now (ISO8601) for deterministic runs/tests."
    )
    ap.add_argument("--max-age-hours-prk", type=float, default=36.0)
    ap.add_argument("--max-age-hours-prj", type=float, default=36.0)
    ap.add_argument("--prk-workflow", default="prk-prj-status-report.yml")
    ap.add_argument("--prj-workflow", default="prj-scheduled-shadow-paper-features-smoke.yml")
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

    prk = _evaluate(
        "PR-K",
        args.prk_workflow,
        args.branch,
        now,
        args.limit,
        float(args.max_age_hours_prk),
        prk_runs,
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

    out = {
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "branch": args.branch,
        "results": [
            {
                "name": prk.name,
                "workflow": prk.workflow,
                "run_id": prk.run_id,
                "created_at": prk.created_at,
                "age_hours": prk.age_hours,
                "ok": prk.ok,
                "reason": prk.reason,
            },
            {
                "name": prj.name,
                "workflow": prj.workflow,
                "run_id": prj.run_id,
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
        "",
        "## Results",
        fmt(prk),
        fmt(prj),
    ]
    (outdir / "stability_gate.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    return 0 if out["overall_ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
