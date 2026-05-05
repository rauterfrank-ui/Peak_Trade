#!/usr/bin/env python3
"""Report a read-only summary for a P7 Shadow repeated one-shot campaign.

The reporter inspects an existing campaign directory. It does not execute
Paper/Shadow runners, does not invoke the scheduler, and does not authorize
daemon, 24/7, Testnet, Live, broker, exchange, or order paths.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


_root = str(_repo_root())
if _root not in sys.path:
    sys.path.insert(0, _root)

from tests.ops.p7_shadow_one_shot_acceptance_bundle_v0 import (  # noqa: E402
    assert_p7_shadow_repeated_run_stability_v0,
)


CONTRACT = "p7_shadow_repeated_campaign_summary_v0"
RISK_PATTERN = re.compile(
    r"live|testnet|broker|exchange|api_key|secret|network|http|websocket|"
    r"ERROR|FAIL|Traceback|exception|submit_order|real_order",
    re.IGNORECASE,
)


def _json_files(outdir: Path) -> list[Path]:
    return sorted(outdir.rglob("*.json"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_pass_line(campaign_dir: Path, run_name: str) -> bool:
    result = campaign_dir / f"{run_name}_RESULT.md"
    if not result.exists():
        return False
    text = result.read_text(encoding="utf-8")
    return f"PASS: {run_name} completed and passed acceptance checks" in text


def _stderr_empty(campaign_dir: Path, run_name: str) -> bool:
    stderr = campaign_dir / f"{run_name}_stderr.txt"
    return stderr.exists() and stderr.read_text(encoding="utf-8") == ""


def _stdout_exists(campaign_dir: Path, run_name: str) -> bool:
    return (campaign_dir / f"{run_name}_stdout.txt").exists()


def _risk_scan_clean(outdir: Path) -> bool:
    for path in sorted(p for p in outdir.rglob("*") if p.is_file()):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if RISK_PATTERN.search(text):
            return False
    return True


def _expected_artifacts_present(relpaths: set[str]) -> bool:
    return (
        "shadow_session_summary.json" in relpaths
        and any("manifest" in path.lower() for path in relpaths)
        and any("evidence" in path.lower() for path in relpaths)
        and any("account" in path.lower() for path in relpaths)
        and any("fills" in path.lower() for path in relpaths)
    )


def _run_payload(campaign_dir: Path, run_name: str) -> dict[str, Any]:
    outdir = campaign_dir / "runs" / run_name
    json_files = _json_files(outdir)
    json_valid = True
    payloads: dict[str, Any] = {}

    for path in json_files:
        rel = path.relative_to(outdir).as_posix()
        try:
            payloads[rel] = _load_json(path)
        except Exception:
            json_valid = False

    relpaths = set(payloads)

    return {
        "run_id": run_name,
        "outdir": str(outdir),
        "result_file": str(campaign_dir / f"{run_name}_RESULT.md"),
        "stdout_file": str(campaign_dir / f"{run_name}_stdout.txt"),
        "stderr_file": str(campaign_dir / f"{run_name}_stderr.txt"),
        "pass_line_present": _run_pass_line(campaign_dir, run_name),
        "stdout_exists": _stdout_exists(campaign_dir, run_name),
        "stderr_empty": _stderr_empty(campaign_dir, run_name),
        "json_valid": json_valid,
        "artifact_count": len(json_files),
        "relative_artifacts": sorted(relpaths),
        "expected_artifacts_present": _expected_artifacts_present(relpaths),
        "risk_scan_clean": _risk_scan_clean(outdir),
    }


def _relative_artifact_set_stable(runs: list[dict[str, Any]]) -> bool:
    if not runs:
        return False
    first = runs[0]["relative_artifacts"]
    return all(run["relative_artifacts"] == first for run in runs)


def _stable_business_artifacts_unchanged(campaign_dir: Path, run_names: list[str]) -> bool:
    payloads_by_run: dict[str, dict[str, Any]] = {}
    try:
        for run_name in run_names:
            outdir = campaign_dir / "runs" / run_name
            payloads_by_run[run_name] = {
                path.relative_to(outdir).as_posix(): _load_json(path)
                for path in _json_files(outdir)
            }
        assert_p7_shadow_repeated_run_stability_v0(payloads_by_run)
    except Exception:
        return False
    return True


def build_p7_shadow_repeated_campaign_summary(
    campaign_dir: Path,
    *,
    expected_runs: int | None = None,
) -> dict[str, Any]:
    campaign = campaign_dir.resolve()
    run_dirs = sorted(path for path in (campaign / "runs").glob("run_*") if path.is_dir())
    run_names = [path.name for path in run_dirs]
    runs = [_run_payload(campaign, run_name) for run_name in run_names]

    per_run_pass = all(
        run["pass_line_present"]
        and run["stderr_empty"]
        and run["json_valid"]
        and run["expected_artifacts_present"]
        and run["risk_scan_clean"]
        for run in runs
    )
    relative_artifact_set_stable = _relative_artifact_set_stable(runs)
    stable_business_artifacts_unchanged = _stable_business_artifacts_unchanged(campaign, run_names)
    expected_run_count_met = expected_runs is None or len(run_names) == expected_runs

    campaign_pass = (
        bool(runs)
        and per_run_pass
        and relative_artifact_set_stable
        and stable_business_artifacts_unchanged
        and expected_run_count_met
    )

    return {
        "contract": CONTRACT,
        "schema_version": 0,
        "campaign_dir": str(campaign),
        "campaign_status": "PASS" if campaign_pass else "FAIL",
        "run_count": len(run_names),
        "expected_runs": expected_runs,
        "expected_run_count_met": expected_run_count_met,
        "runs": runs,
        "campaign_checks": {
            "per_run_acceptance_pass": per_run_pass,
            "relative_artifact_set_stable": relative_artifact_set_stable,
            "stable_business_artifacts_unchanged": stable_business_artifacts_unchanged,
            "risk_scan_clean": all(run["risk_scan_clean"] for run in runs),
        },
        "activation_authorized": False,
        "scheduler_authorized": False,
        "daemon_authorized": False,
        "paper_shadow_24_7_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "broker_authorized": False,
        "exchange_authorized": False,
        "order_submission_authorized": False,
        "notes": [
            "read_only_reporter",
            "does_not_run_paper_or_shadow",
            "does_not_run_scheduler",
            "does_not_start_daemon",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-dir", required=True, help="Campaign directory to inspect.")
    parser.add_argument("--expected-runs", type=int, default=None)
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args(argv)

    payload = build_p7_shadow_repeated_campaign_summary(
        Path(args.campaign_dir),
        expected_runs=args.expected_runs,
    )

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"campaign_status={payload['campaign_status']}")
        print(f"run_count={payload['run_count']}")
        print(f"activation_authorized={str(payload['activation_authorized']).lower()}")

    return 0 if payload["campaign_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
