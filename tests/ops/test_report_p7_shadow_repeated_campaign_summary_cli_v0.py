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


def test_high_vol_pass_line_is_recognized(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path, run_count=1)
    (campaign / "run_001_RESULT.md").write_text(
        "PASS: high_vol_no_trade run_001 completed and passed acceptance checks.\n",
        encoding="utf-8",
    )
    payload = build_p7_shadow_repeated_campaign_summary(campaign, expected_runs=1)
    assert payload["runs"][0]["pass_line_present"] is True
    assert payload["campaign_status"] == "PASS"


def test_risk_scan_ignores_governance_suffix_keys(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path)
    outlook = campaign / "runs" / "run_001" / "p4c" / "market_outlook.json"
    data = json.loads(outlook.read_text(encoding="utf-8"))
    data["live_authorized"] = False
    data["testnet_authorized"] = False
    outlook.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = build_p7_shadow_repeated_campaign_summary(campaign, expected_runs=3)

    assert payload["campaign_checks"]["risk_scan_clean"] is True
    assert payload["campaign_status"] == "PASS"


def test_explicit_run_subset_skips_extra_run_dirs(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    for name in ("run_001", "run_001_clean_main_after_reconcile_fix", "run_002", "run_003"):
        _copy_fixture_run(campaign, name)

    payload = build_p7_shadow_repeated_campaign_summary(
        campaign,
        expected_runs=3,
        runs=["run_001_clean_main_after_reconcile_fix", "run_002", "run_003"],
    )

    assert payload["run_count"] == 3
    assert payload["expected_run_count_met"] is True
    assert [run["run_id"] for run in payload["runs"]] == [
        "run_001_clean_main_after_reconcile_fix",
        "run_002",
        "run_003",
    ]
    assert payload["campaign_status"] == "PASS"


def test_cli_accepts_comma_separated_runs(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    campaign.mkdir()
    for name in ("run_001", "run_002", "run_003"):
        _copy_fixture_run(campaign, name)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--campaign-dir",
            str(campaign),
            "--expected-runs",
            "1",
            "--runs",
            "run_002",
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["run_count"] == 1
    assert payload["runs"][0]["run_id"] == "run_002"


def test_cli_json_with_explicit_runs_is_bounded_and_non_authorizing(tmp_path: Path) -> None:
    campaign = _campaign(tmp_path, run_count=3)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--campaign-dir",
            str(campaign),
            "--expected-runs",
            "2",
            "--runs",
            "run_001,run_003",
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
    assert payload["contract"] == "p7_shadow_repeated_campaign_summary_v0"
    assert payload["campaign_status"] == "PASS"
    assert payload["run_count"] == 2
    assert payload["expected_runs"] == 2
    assert payload["expected_run_count_met"] is True
    assert [run["run_id"] for run in payload["runs"]] == ["run_001", "run_003"]

    assert payload["campaign_checks"] == {
        "per_run_acceptance_pass": True,
        "relative_artifact_set_stable": True,
        "stable_business_artifacts_unchanged": True,
        "risk_scan_clean": True,
    }

    for key in (
        "activation_authorized",
        "scheduler_authorized",
        "daemon_authorized",
        "paper_shadow_24_7_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert payload[key] is False

    for run in payload["runs"]:
        assert run["pass_line_present"] is True
        assert run["stderr_empty"] is True
        assert run["json_valid"] is True
        assert run["expected_artifacts_present"] is True
        assert run["risk_scan_clean"] is True
        assert run["artifact_count"] == 11
