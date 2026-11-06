from decimal import Decimal
from pathlib import Path

from tests.aiops.p7.paper_runner_test_helpers_v0 import (
    PAPER_RUN_MIN_SPEC,
    assert_json_outputs_do_not_contain_live_markers,
    load_json,
    run_paper_session,
)

SPEC = PAPER_RUN_MIN_SPEC


def test_paper_runner_two_order_roundtrip_writes_deterministic_outputs(tmp_path: Path) -> None:
    outdir = tmp_path / "paper_two_order_roundtrip"

    result = run_paper_session(SPEC, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    fills = load_json(outdir / "fills.json")
    account = load_json(outdir / "account.json")
    manifest = load_json(outdir / "evidence_manifest.json")

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

    result = run_paper_session(SPEC, outdir)

    assert result.returncode == 0
    assert result.stderr == ""

    assert_json_outputs_do_not_contain_live_markers(outdir)


def test_paper_runner_two_order_fixture_is_minimal_and_offline() -> None:
    spec = load_json(SPEC)

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
