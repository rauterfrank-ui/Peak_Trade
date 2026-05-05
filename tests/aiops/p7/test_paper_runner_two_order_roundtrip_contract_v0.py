import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_paper_runner_two_order_roundtrip_writes_deterministic_outputs(tmp_path: Path) -> None:
    outdir = tmp_path / "paper_two_order_roundtrip"

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

    fills = _load(outdir / "fills.json")
    account = _load(outdir / "account.json")
    manifest = _load(outdir / "evidence_manifest.json")

    assert fills["schema_version"] == "p7.fills.v0"
    assert len(fills["fills"]) == 2

    buy, sell = fills["fills"]
    assert buy["symbol"] == "BTC"
    assert buy["side"] == "BUY"
    assert buy["qty"] == 1.0
    assert Decimal(str(buy["price"])) == Decimal("100.1")
    assert Decimal(str(buy["fee"])) == Decimal("0.1001")

    assert sell["symbol"] == "BTC"
    assert sell["side"] == "SELL"
    assert sell["qty"] == 1.0
    assert Decimal(str(sell["price"])) == Decimal("99.9")
    assert Decimal(str(sell["fee"])) == Decimal("0.0999")

    assert account["schema_version"] == "p7.account.v0"
    assert Decimal(str(account["cash"])) == Decimal("999.6")
    assert account["positions"] == {"BTC": 0.0}

    assert manifest["meta"]["kind"] == "p7_paper_manifest"
    assert manifest["meta"]["schema_version"] == "p7.paper_run.v0"
    assert {item["name"] for item in manifest["files"]} == {"account.json", "fills.json"}


def test_paper_runner_two_order_roundtrip_output_is_portable_and_non_live(tmp_path: Path) -> None:
    outdir = tmp_path / "paper_two_order_roundtrip_portable"

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

    for path in sorted(outdir.rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text
        assert "api_key" not in text.lower()
        assert "secret" not in text.lower()
        assert "submit_order" not in text.lower()
        assert "real_order" not in text.lower()
        assert "broker_connect" not in text.lower()
        assert "exchange_connect" not in text.lower()


def test_paper_runner_two_order_fixture_is_minimal_and_offline() -> None:
    spec = _load(SPEC)

    assert spec["schema_version"] == "p7.paper_run.v0"
    assert len(spec["orders"]) == 2
    assert [order["side"] for order in spec["orders"]] == ["BUY", "SELL"]
    assert spec["initial_cash"] == 1000.0
    assert spec["fee_rate"] == 0.001
    assert spec["slippage_bps"] == 10.0
    assert spec["mid_prices"] == {"BTC": 100.0}

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
        assert key not in spec
