"""Generate scrape-friendly dashboard formats from prj_health_summary.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate scrape-friendly dashboard formats from prj_health_summary.json"
    )
    p.add_argument(
        "--input",
        dest="input_path",
        default="reports/status/prj_health_summary.json",
    )
    p.add_argument(
        "--output-dir",
        dest="output_dir",
        default="reports/status",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    src = Path(args.input_path)
    obj = json.loads(src.read_text(encoding="utf-8"))

    status = obj.get("status", "UNKNOWN")
    action = obj.get("policy_action", "none") or "none"
    age = obj.get("last_success_age_hours")
    runs = obj.get("runs_sampled", 0)

    age_val = -1.0 if age is None else float(age)
    runs_val = 0 if runs is None else int(runs)

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    reason_codes = obj.get("reason_codes") or []
    rc = ",".join(reason_codes)
    lines = []
    lines.append(f"generated_at={obj.get('generated_at', '')}")
    lines.append(f"status={status}")
    lines.append(f"policy_action={action}")
    lines.append(f"reason_codes={rc}")
    lines.append(f"last_success_age_hours={age_val}")
    lines.append(f"runs_sampled={runs_val}")
    lines.append(f"output_version={obj.get('output_version', 1)}")
    (outdir / "prj_health_dashboard.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (outdir / "prj_health_dashboard.csv").write_text(
        "generated_at,status,policy_action,last_success_age_hours,runs_sampled\n"
        f"{obj.get('generated_at', '')},{status},{action},{age_val},{runs_val}\n",
        encoding="utf-8",
    )

    dash = {
        "dashboard_version": 1,
        "generated_at": obj.get("generated_at", ""),
        "status": status,
        "policy_action": action,
        "reason_codes": obj.get("reason_codes") or [],
        "runs_sampled": runs_val,
        "last_success_age_hours": (
            None
            if obj.get("last_success_age_hours") is None
            else float(obj["last_success_age_hours"])
        ),
    }
    (outdir / "prj_health_dashboard_v1.json").write_text(
        json.dumps(dash, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    (outdir / "prj_health_dashboard.md").write_text(
        "\n".join(
            [
                "# PR-J Health Dashboard",
                f"- Status: **{status}**",
                f"- Policy action: **{action}**",
                f"- Last success age (hours): {age_val}",
                f"- Runs sampled: {runs_val}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
