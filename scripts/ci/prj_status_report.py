from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate PR-J status report artifacts from a GitHub Actions runs JSON array."
    )
    p.add_argument(
        "--input",
        dest="input_path",
        default=None,
        help="Path to GitHub Actions workflow runs JSON array (default: env PRJ_RUNS_JSON or out/prj_runs.json).",
    )
    p.add_argument(
        "--output-dir",
        dest="output_dir",
        default="reports/status",
        help="Output directory for prj_status_latest.{json,md}.",
    )
    p.add_argument(
        "--limit",
        dest="limit",
        type=int,
        default=None,
        help="Optional limit for number of runs to include (most recent first).",
    )
    return p.parse_args()


def _apply_cli_overrides(args: argparse.Namespace) -> None:
    if args.input_path:
        os.environ["PRJ_RUNS_JSON"] = args.input_path
    os.environ["PRJ_REPORTS_DIR"] = args.output_dir
    if args.limit is not None:
        os.environ["PRJ_RUNS_LIMIT"] = str(args.limit)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    in_path = Path(os.environ.get("PRJ_RUNS_JSON", "out/prj_runs.json"))
    out_dir = Path(os.environ.get("PRJ_REPORTS_DIR", "reports/status"))
    out_dir.mkdir(parents=True, exist_ok=True)

    runs = json.loads(in_path.read_text(encoding="utf-8"))
    limit = os.environ.get("PRJ_RUNS_LIMIT")
    if limit:
        runs = runs[: int(limit)]
    # expected: list of runs (from GitHub API)
    rows = []
    for r in runs:
        rows.append(
            {
                "id": r.get("id"),
                "run_number": r.get("run_number"),
                "event": r.get("event"),
                "status": r.get("status"),
                "conclusion": r.get("conclusion"),
                "created_at": r.get("created_at"),
                "updated_at": r.get("updated_at"),
                "html_url": r.get("html_url"),
            }
        )

    # counts
    by_conc = {}
    for x in rows:
        k = x["conclusion"] or x["status"] or "unknown"
        by_conc[k] = by_conc.get(k, 0) + 1

    latest_schedule_success = next(
        (x for x in rows if x["event"] == "schedule" and x["conclusion"] == "success"),
        None,
    )
    latest_any = rows[0] if rows else None

    payload = {
        "generated_utc": _iso_now(),
        "workflow": "PR-J / Scheduled Shadow+Paper Features Smoke",
        "runs_count": len(rows),
        "counts": by_conc,
        "latest_any": latest_any,
        "latest_schedule_success": latest_schedule_success,
        "runs": rows,
    }

    (out_dir / "prj_status_latest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    md = []
    md.append(f"# PR-J Status Report — {_iso_now()}\n")
    md.append(f"- Runs sampled: **{len(rows)}**\n")
    md.append("## Counts\n")
    for k, v in sorted(by_conc.items(), key=lambda kv: (-kv[1], kv[0])):
        md.append(f"- **{k}**: {v}")
    md.append("")
    if latest_any:
        md.append("## Latest Run (any)\n")
        md.append(f"- event: **{latest_any['event']}**")
        md.append(f"- status/conclusion: **{latest_any['status']} / {latest_any['conclusion']}**")
        md.append(f"- created: {latest_any['created_at']}")
        md.append(f"- url: {latest_any['html_url']}\n")
    if latest_schedule_success:
        md.append("## Latest Successful Schedule Run\n")
        md.append(f"- created: {latest_schedule_success['created_at']}")
        md.append(f"- url: {latest_schedule_success['html_url']}\n")

    md.append("## Last 10 Runs\n")
    md.append("| created_at (UTC) | event | conclusion | url |")
    md.append("|---|---:|---:|---|")
    for x in rows[:10]:
        md.append(f"| {x['created_at']} | {x['event']} | {x['conclusion']} | {x['html_url']} |")

    (out_dir / "prj_status_latest.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return 0


CI_TRIGGER_WORKFLOW_YAML_FIX = True  # noqa: F841
CI_TRIGGER_PR1556 = True  # noqa: F841

if __name__ == "__main__":
    args = _parse_args()
    _apply_cli_overrides(args)
    raise SystemExit(main())
