"""Tests for P40 backtest runner CLI v1."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backtest.p34.json_io_v1 import read_report_json_v1
from src.ops.p40.backtest_runner_cli_v1 import EXIT_OK, EXIT_USAGE, build_parser, main


def _minimal_bars_json() -> str:
    return """[
  {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 10.0},
  {"open": 100.5, "high": 102.0, "low": 100.0, "close": 101.0, "volume": 12.0}
]"""


def _minimal_orders_json() -> str:
    return """[
  [],
  [{"id": "o1", "symbol": "MOCK", "side": "BUY", "order_type": "MARKET", "qty": 1.0}]
]"""


def test_parser_smoke() -> None:
    p = build_parser()
    ns = p.parse_args(
        [
            "run",
            "--bars-json",
            "/tmp/b.json",
            "--orders-json",
            "/tmp/o.json",
            "--out-dir",
            "/tmp/out",
        ]
    )
    assert ns.cmd == "run"
    assert ns.bars_json == "/tmp/b.json"
    assert ns.orders_json == "/tmp/o.json"
    assert ns.out_dir == "/tmp/out"


def test_run_happy_path(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.json"
    orders_path = tmp_path / "orders.json"
    out_dir = tmp_path / "out"
    bars_path.write_text(_minimal_bars_json(), encoding="utf-8")
    orders_path.write_text(_minimal_orders_json(), encoding="utf-8")

    rc = main(
        [
            "run",
            "--bars-json",
            str(bars_path),
            "--orders-json",
            str(orders_path),
            "--out-dir",
            str(out_dir),
        ]
    )
    assert rc == EXIT_OK

    report_path = out_dir / "report.json"
    assert report_path.exists()
    d = read_report_json_v1(report_path)
    assert d["schema_version"] == 1
    assert "fills" in d
    assert "state" in d
    assert "equity" in d
    assert "metrics" in d


def test_run_deterministic(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.json"
    orders_path = tmp_path / "orders.json"
    bars_path.write_text(_minimal_bars_json(), encoding="utf-8")
    orders_path.write_text(_minimal_orders_json(), encoding="utf-8")

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"
    rc1 = main(
        [
            "run",
            "--bars-json",
            str(bars_path),
            "--orders-json",
            str(orders_path),
            "--out-dir",
            str(out1),
        ]
    )
    rc2 = main(
        [
            "run",
            "--bars-json",
            str(bars_path),
            "--orders-json",
            str(orders_path),
            "--out-dir",
            str(out2),
        ]
    )
    assert rc1 == EXIT_OK
    assert rc2 == EXIT_OK

    c1 = (out1 / "report.json").read_text(encoding="utf-8")
    c2 = (out2 / "report.json").read_text(encoding="utf-8")
    assert c1 == c2


def test_run_with_bundle_and_verify(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.json"
    orders_path = tmp_path / "orders.json"
    out_dir = tmp_path / "out"
    bundle_dir = tmp_path / "bundle"
    bars_path.write_text(_minimal_bars_json(), encoding="utf-8")
    orders_path.write_text(_minimal_orders_json(), encoding="utf-8")

    rc = main(
        [
            "run",
            "--bars-json",
            str(bars_path),
            "--orders-json",
            str(orders_path),
            "--out-dir",
            str(out_dir),
            "--bundle-dir",
            str(bundle_dir),
            "--verify",
        ]
    )
    assert rc == EXIT_OK
    assert (bundle_dir / "report.json").exists()
    assert (bundle_dir / "manifest.json").exists()


def test_run_invalid_lengths(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.json"
    orders_path = tmp_path / "orders.json"
    bars_path.write_text('[{"open":1,"high":1,"low":1,"close":1}]', encoding="utf-8")
    orders_path.write_text("[[], []]", encoding="utf-8")

    rc = main(
        [
            "run",
            "--bars-json",
            str(bars_path),
            "--orders-json",
            str(orders_path),
            "--out-dir",
            str(tmp_path),
        ]
    )
    assert rc == EXIT_USAGE
