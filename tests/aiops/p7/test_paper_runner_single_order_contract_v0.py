import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
MIN_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _single_buy_spec_path(tmp_path: Path) -> tuple[Path, dict]:
    """Derive a one-order BUY spec from paper_run_min_v0 (which lists BUY+SELL)."""
    base = _load(MIN_SPEC)
    spec = {
        "schema_version": base["schema_version"],
        "asof_utc": base["asof_utc"],
        "initial_cash": base["initial_cash"],
        "fee_rate": base["fee_rate"],
        "slippage_bps": base["slippage_bps"],
        "mid_prices": base["mid_prices"],
        "orders": [base["orders"][0]],
    }
    path = tmp_path / "paper_run_single_buy_from_min_v0.json"
    path.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, spec


def test_paper_runner_single_order_writes_deterministic_accounting_outputs(tmp_path: Path) -> None:
    spec_path, spec = _single_buy_spec_path(tmp_path)
    outdir = tmp_path / "paper_single_order"

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(spec_path),
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

    fills_path = outdir / "fills.json"
    account_path = outdir / "account.json"
    manifest_path = outdir / "evidence_manifest.json"

    assert fills_path.exists()
    assert account_path.exists()
    assert manifest_path.exists()

    fills = _load(fills_path)
    account = _load(account_path)
    manifest = _load(manifest_path)

    assert fills["schema_version"] == "p7.fills.v0"
    assert len(fills["fills"]) == 1

    fill = fills["fills"][0]
    assert fill["symbol"] == "BTC"
    assert fill["side"] == "BUY"
    assert Decimal(str(fill["qty"])) > Decimal("0")
    assert Decimal(str(fill["price"])) > Decimal("0")
    assert Decimal(str(fill["fee"])) >= Decimal("0")

    assert account["schema_version"] == "p7.account.v0"
    initial = Decimal(str(spec["initial_cash"]))
    assert Decimal(str(account["cash"])) < initial
    assert account["positions"]["BTC"] == fill["qty"]

    assert manifest["meta"]["kind"] == "p7_paper_manifest"
    assert manifest["meta"]["schema_version"] == "p7.paper_run.v0"
    names = {item["name"] for item in manifest["files"]}
    assert names == {"account.json", "fills.json"}


def test_paper_runner_single_order_outputs_are_portable_and_non_authorizing(tmp_path: Path) -> None:
    spec_path, _spec = _single_buy_spec_path(tmp_path)
    outdir = tmp_path / "paper_single_order_portable"

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(spec_path),
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


def test_paper_runner_min_fixture_has_no_embedded_authority_flags() -> None:
    spec = _load(MIN_SPEC)

    assert spec["orders"]
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
