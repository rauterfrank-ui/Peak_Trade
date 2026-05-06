from decimal import Decimal
from pathlib import Path

from tests.aiops.p7.paper_runner_test_helpers_v0 import (
    PAPER_RUN_MIN_SPEC,
    assert_json_outputs_do_not_contain_live_markers,
    load_json,
    run_paper_session,
    write_json_spec,
)

BASE_SPEC = PAPER_RUN_MIN_SPEC


def test_paper_runner_partial_sell_keeps_remaining_position(tmp_path: Path) -> None:
    payload = load_json(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 2.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = write_json_spec(tmp_path, payload, "buy2_sell1_same_symbol.json")
    outdir = tmp_path / "buy2_sell1_same_symbol_out"

    result = run_paper_session(spec, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    fills = load_json(outdir / "fills.json")
    account = load_json(outdir / "account.json")
    manifest = load_json(outdir / "evidence_manifest.json")

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
    payload = load_json(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 3.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = write_json_spec(tmp_path, payload, "buy3_sell1_sell1_same_symbol.json")
    outdir = tmp_path / "buy3_sell1_sell1_same_symbol_out"

    result = run_paper_session(spec, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    fills = load_json(outdir / "fills.json")
    account = load_json(outdir / "account.json")

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
    payload = load_json(BASE_SPEC)
    payload["orders"] = [
        {"symbol": "BTC", "side": "BUY", "qty": 2.0},
        {"symbol": "BTC", "side": "SELL", "qty": 1.0},
    ]
    payload["mid_prices"] = {"BTC": 100.0}

    spec = write_json_spec(tmp_path, payload, "partial_sell_portable.json")
    outdir = tmp_path / "partial_sell_portable_out"

    result = run_paper_session(spec, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    assert_json_outputs_do_not_contain_live_markers(outdir)
