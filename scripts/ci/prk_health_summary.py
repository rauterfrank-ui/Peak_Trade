"""Generate compact PR-K health summary from prj_status_latest.json."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate compact PR-K health summary from prj_status_latest.json"
    )
    p.add_argument(
        "--input",
        dest="input_path",
        default="reports/status/prj_status_latest.json",
    )
    p.add_argument(
        "--output-dir",
        dest="output_dir",
        default="reports/status",
    )
    p.add_argument(
        "--now",
        dest="now",
        default=None,
        help="Override current time (ISO8601) for deterministic tests",
    )
    return p.parse_args()


def _parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def main() -> int:
    args = _parse_args()
    now = _parse_iso8601(args.now) if args.now else datetime.now(timezone.utc)

    src = Path(args.input_path)
    obj = json.loads(src.read_text(encoding="utf-8"))

    policy = obj.get("policy") or {}
    action = policy.get("action") or ""
    reasons = policy.get("reason_codes") or []

    age_h = obj.get("last_successful_schedule_age_hours")
    status = "OK"
    if action == "NO_TRADE":
        if "PRJ_STATUS_NO_SUCCESS" in reasons:
            status = "NO_SUCCESS"
        elif "PRJ_STATUS_STALE" in reasons:
            status = "STALE"
        else:
            status = "NO_TRADE"

    runs_sampled = obj.get("runs_count")

    out = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "policy_action": action,
        "reason_codes": reasons,
        "last_success_age_hours": age_h,
        "runs_sampled": runs_sampled,
        "output_version": 1,
    }

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    (outdir / "prj_health_summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    age_s = "(n/a)" if age_h is None else f"{age_h:.2f}"
    badge = f"PRJ_HEALTH_BADGE: {status} | policy={action or 'none'} | last_success_age_h={age_s} | runs={runs_sampled}"
    md_lines = [
        badge,
        "",
        f"# PR-J Health Summary — {out['generated_at']}",
        f"- Status: **{status}**",
        f"- Policy: **{action or 'none'}**",
        f"- Reasons: {', '.join(reasons) if reasons else '(none)'}",
        f"- Last success age (hours): {age_h if age_h is not None else '(n/a)'}",
        f"- Runs sampled: {runs_sampled}",
    ]
    (outdir / "prj_health_summary.md").write_text(
        "\n".join(md_lines) + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
