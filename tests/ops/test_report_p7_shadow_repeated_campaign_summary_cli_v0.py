import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.ops.report_p7_shadow_repeated_campaign_summary import (
    build_p7_shadow_repeated_campaign_summary,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "report_p7_shadow_repeated_campaign_summary.py"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "p7_shadow_one_shot_acceptance_v0"


def _copy_fixture_run(campaign: Path, run_name: str) -> None:
    outdir = campaign / "runs" / run_name
    shutil.copytree(FIXTURE_DIR, outdir)
    (campaign / f"{run_name}_stdout.txt").write_text("fixture stdout\n", encoding="utf-8")
    (campaign / f"{run_name}_stderr.txt").write_text("", encoding="utf-8")
    (campaign / f"{run_name}_RESULT.md").write_text(
        f"PASS: {run_name} completed and passed acceptance checks\n",
        encoding="utf-8",
    )


def _campaign(tmp_path: Path, run_count: int = 3) -> Path:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    for index in range(1, run_count + 1):
        _copy_fixture_run(campaign, f"run_{index:03d}")
    return campaign


def test_build_campaign_summary_reports_pass_and_false_authority(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path)

    payload = build_p7_shadow_repeated_campaign_summary(campaign, expected_runs=3)

    assert payload["contract"] == "p7_shadow_repeated_campaign_summary_v0"
    assert payload["campaign_status"] == "PASS"
    assert payload["run_count"] == 3
    assert payload["expected_run_count_met"] is True
    assert payload["campaign_checks"] == {
        "per_run_acceptance_pass": True,
        "relative_artifact_set_stable": True,
        "stable_business_artifacts_unchanged": True,
        "risk_scan_clean": True,
    }
    assert payload["activation_authorized"] is False
    assert payload["scheduler_authorized"] is False
    assert payload["daemon_authorized"] is False
    assert payload["testnet_authorized"] is False
    assert payload["live_authorized"] is False
    assert payload["broker_authorized"] is False
    assert payload["exchange_authorized"] is False
    assert payload["order_submission_authorized"] is False


def test_cli_json_output_is_deterministic_and_json_native(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--campaign-dir",
            str(campaign),
            "--expected-runs",
            "3",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["campaign_status"] == "PASS"
    assert payload["run_count"] == 3
    assert [run["run_id"] for run in payload["runs"]] == ["run_001", "run_002", "run_003"]
    assert "does_not_run_paper_or_shadow" in payload["notes"]


def test_cli_human_output_is_bounded_status_only(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--campaign-dir",
            str(campaign),
            "--expected-runs",
            "3",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "campaign_status=PASS",
        "run_count=3",
        "activation_authorized=false",
    ]


def test_reporter_fails_when_expected_run_count_is_not_met(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path, run_count=2)

    payload = build_p7_shadow_repeated_campaign_summary(campaign, expected_runs=3)

    assert payload["campaign_status"] == "FAIL"
    assert payload["run_count"] == 2
    assert payload["expected_run_count_met"] is False


def test_reporter_fails_when_business_artifact_drifts(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path)
    fills_path = campaign / "runs" / "run_002" / "p7" / "fills.json"
    fills = json.loads(fills_path.read_text(encoding="utf-8"))
    fills["fills"][0]["side"] = "SELL" if fills["fills"][0]["side"] == "BUY" else "BUY"
    fills_path.write_text(json.dumps(fills, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = build_p7_shadow_repeated_campaign_summary(campaign, expected_runs=3)

    assert payload["campaign_status"] == "FAIL"
    assert payload["campaign_checks"]["stable_business_artifacts_unchanged"] is False
