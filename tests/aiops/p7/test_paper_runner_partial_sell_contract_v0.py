import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
BASE_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_spec(tmp_path: Path, payload: dict, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run(spec: Path, outdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(spec),
            "--outdir",
            str(outdir),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_paper_runner_partial_sell_keeps_remaining_position(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 2.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = _write_spec(tmp_path, payload, "buy2_sell1_same_symbol.json")
    outdir = tmp_path / "buy2_sell1_same_symbol_out"

    result = _run(spec, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    fills = _load(outdir / "fills.json")
    account = _load(outdir / "account.json")
    manifest = _load(outdir / "evidence_manifest.json")

    assert fills["schema_version"] == "p7.fills.v0"
    assert [(fill["symbol"], fill["side"], fill["qty"]) for fill in fills["fills"]] == [
        ("BTC", "BUY", 2.0),
        ("BTC", "SELL", 1.0),
    ]

    buy, sell = fills["fills"]
    assert Decimal(str(buy["price"])) == Decimal("100.1")
    assert Decimal(str(buy["fee"])) == Decimal("0.2002")
    assert Decimal(str(sell["price"])) == Decimal("99.9")
    assert Decimal(str(sell["fee"])) == Decimal("0.0999")

    assert account["schema_version"] == "p7.account.v0"
    assert Decimal(str(account["cash"])) == Decimal("899.3999")
    assert account["positions"] == {"BTC": 1.0}

    assert manifest["meta"]["kind"] == "p7_paper_manifest"
    assert manifest["meta"]["schema_version"] == "p7.paper_run.v0"
    assert {item["name"] for item in manifest["files"]} == {"account.json", "fills.json"}


def test_paper_runner_repeated_partial_sells_reduce_position_stepwise(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 3.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = _write_spec(tmp_path, payload, "buy3_sell1_sell1_same_symbol.json")
    outdir = tmp_path / "buy3_sell1_sell1_same_symbol_out"

    result = _run(spec, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    fills = _load(outdir / "fills.json")
    account = _load(outdir / "account.json")

    assert [(fill["symbol"], fill["side"], fill["qty"]) for fill in fills["fills"]] == [
        ("BTC", "BUY", 3.0),
        ("BTC", "SELL", 1.0),
        ("BTC", "SELL", 1.0),
    ]

    buy, sell_1, sell_2 = fills["fills"]
    assert Decimal(str(buy["price"])) == Decimal("100.1")
    assert Decimal(str(buy["fee"])).quantize(Decimal("0.0001")) == Decimal("0.3003")
    assert Decimal(str(sell_1["price"])) == Decimal("99.9")
    assert Decimal(str(sell_1["fee"])) == Decimal("0.0999")
    assert Decimal(str(sell_2["price"])) == Decimal("99.9")
    assert Decimal(str(sell_2["fee"])) == Decimal("0.0999")

    assert Decimal(str(account["cash"])) == Decimal("898.9999000000001")
    assert account["positions"] == {"BTC": 1.0}


def test_paper_runner_partial_sell_outputs_are_portable_and_non_live(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 2.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = _write_spec(tmp_path, payload, "partial_sell_portable.json")
    outdir = tmp_path / "partial_sell_portable_out"

    result = _run(spec, outdir)

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
