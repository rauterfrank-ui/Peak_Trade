from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

OUTPUT_VERSION = 1


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
    p.add_argument(
        "--validate-schema",
        dest="validate_schema",
        action="store_true",
        default=True,
        help="Validate output JSON against schema (default).",
    )
    p.add_argument(
        "--no-validate-schema",
        dest="validate_schema",
        action="store_false",
        help="Disable schema validation.",
    )
    p.add_argument(
        "--stale-hours",
        dest="stale_hours",
        type=float,
        default=36.0,
        help="Mark report stale if last successful schedule run older than this many hours.",
    )
    p.add_argument(
        "--now",
        dest="now",
        default=None,
        help="Override current time (ISO8601) for deterministic tests.",
    )
    return p.parse_args()


def _load_schema() -> dict:
    schema_path = Path(__file__).resolve().parent / "prj_status_report_schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def _validate_schema(obj: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        return
    schema = _load_schema()
    jsonschema.validate(instance=obj, schema=schema)


def _apply_cli_overrides(args: argparse.Namespace) -> None:
    if args.input_path:
        os.environ["PRJ_RUNS_JSON"] = args.input_path
    os.environ["PRJ_REPORTS_DIR"] = args.output_dir
    if args.limit is not None:
        os.environ["PRJ_RUNS_LIMIT"] = str(args.limit)


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso8601(s: str):
    from datetime import datetime, timezone

    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _apply_staleness_policy(payload: dict, rows: list, args: argparse.Namespace | None) -> None:
    from datetime import datetime, timezone

    now = (
        _parse_iso8601(args.now)
        if args and getattr(args, "now", None)
        else datetime.now(timezone.utc)
    )
    stale_hours = float(getattr(args, "stale_hours", 36.0)) if args else 36.0

    last_ok = None
    for r in rows:
        if r.get("event") == "schedule" and r.get("conclusion") == "success":
            last_ok = r.get("created_at")
            break

    if not last_ok:
        payload["policy"] = {
            "action": "NO_TRADE",
            "reason_codes": ["PRJ_STATUS_NO_SUCCESS"],
        }
        return

    age_h = (now - _parse_iso8601(last_ok)).total_seconds() / 3600.0
    payload["last_successful_schedule_created_at"] = last_ok
    payload["last_successful_schedule_age_hours"] = round(age_h, 2)

    if age_h > stale_hours:
        payload["policy"] = {
            "action": "NO_TRADE",
            "reason_codes": ["PRJ_STATUS_STALE"],
        }


def main(args: argparse.Namespace | None = None) -> int:
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
        "output_version": OUTPUT_VERSION,
        "generated_utc": _iso_now(),
        "workflow": "PR-J / Scheduled Shadow+Paper Features Smoke",
        "runs_count": len(rows),
        "counts": by_conc,
        "latest_any": latest_any,
        "latest_schedule_success": latest_schedule_success,
        "runs": rows,
    }

    _apply_staleness_policy(payload, rows, args)

    if args and getattr(args, "validate_schema", True):
        _validate_schema(payload)

    (out_dir / "prj_status_latest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    md = []
    md.append(f"# PR-J Status Report — {_iso_now()}\n")
    policy = payload.get("policy")
    if policy and policy.get("action") == "NO_TRADE":
        reason = ", ".join(policy.get("reason_codes", []))
        md.append(f"**⚠️ STALE — NO_TRADE** (`{reason}`)\n")
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
    raise SystemExit(main(args))
