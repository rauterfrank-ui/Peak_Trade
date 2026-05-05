import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_high_vol_no_trade_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_paper_runner_no_order_no_fill_session_writes_flat_outputs(tmp_path: Path) -> None:
    outdir = tmp_path / "paper_no_order_no_fill"

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(SPEC),
            "--outdir",
            str(outdir),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "EMPTY_LEDGER" not in result.stdout
    assert "EMPTY_LEDGER" not in result.stderr

    fills_path = outdir / "fills.json"
    account_path = outdir / "account.json"
    manifest_path = outdir / "evidence_manifest.json"

    assert fills_path.exists()
    assert account_path.exists()
    assert manifest_path.exists()

    fills = _load(fills_path)
    account = _load(account_path)
    manifest = _load(manifest_path)

    assert fills["fills"] == []
    assert account.get("positions") in ({}, {"BTC": 0.0})

    assert manifest["meta"]["kind"] == "p7_paper_manifest"
    assert manifest["meta"]["schema_version"] == "p7.paper_run.v0"
    names = {entry["name"] for entry in manifest["files"]}
    assert names == {"account.json", "fills.json"}


def test_paper_runner_no_order_no_fill_dry_run_does_not_write_outputs(tmp_path: Path) -> None:
    outdir = tmp_path / "paper_no_order_no_fill_dry_run"

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(SPEC),
            "--outdir",
            str(outdir),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert "P7_PAPER_DRY_RUN_OK" in result.stdout
    assert not outdir.exists() or not any(outdir.iterdir())


def test_paper_runner_no_order_no_fill_fixture_is_non_authorizing() -> None:
    spec = _load(SPEC)

    assert spec["orders"] == []
    assert spec["expected_fills"] == []
    assert spec["expected_positions"] == {"BTC": 0.0}

    for key in (
        "activation_authorized",
        "scheduler_authorized",
        "daemon_authorized",
        "testnet_authorized",
        "live_authorized",
        "broker_authorized",
        "exchange_authorized",
        "order_submission_authorized",
    ):
        assert spec[key] is False
