"""P40 — Backtest Runner CLI v1: deterministic run of P32 pipeline."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from src.backtest.p29.accounting_v2 import PositionCashStateV2
from src.backtest.p32.report_v1 import run_backtest_report_v1
from src.backtest.p33.report_artifacts_v1 import report_to_dict
from src.backtest.p34.json_io_v1 import write_report_json_v1
from src.backtest.p35.bundle_v1 import write_report_bundle_v1, verify_report_bundle_v1
from src.backtest.p36.tarball_v1 import write_bundle_tarball_v1, verify_bundle_tarball_v1
from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import ExecutionModelV2
from src.execution.p26.adapter import ExecutionAdapterV1
from src.execution.p26.types import AdapterOrder

EXIT_OK = 0
EXIT_USAGE = 3
EXIT_UNEXPECTED = 4


def _load_bars(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("bars.json must be a JSON array")
    return raw


def _load_orders(path: Path) -> list[list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("orders.json must be a JSON array")
    return raw


def _bar_to_obj(b: dict[str, Any], _: int) -> Any:
    return type(
        "Bar",
        (),
        {
            "open": float(b.get("open", 0.0)),
            "high": float(b.get("high", 0.0)),
            "low": float(b.get("low", 0.0)),
            "close": float(b.get("close", 0.0)),
            "volume": float(b.get("volume", 0.0)),
        },
    )()


def _order_to_adapter(o: dict[str, Any]) -> AdapterOrder:
    return AdapterOrder(
        id=str(o["id"]),
        symbol=str(o["symbol"]),
        side=str(o["side"]),
        order_type=str(o.get("order_type", "MARKET")),
        qty=float(o["qty"]),
        limit_price=float(o["limit_price"]) if o.get("limit_price") is not None else None,
        stop_price=float(o["stop_price"]) if o.get("stop_price") is not None else None,
    )


def _cmd_run(args: argparse.Namespace) -> int:
    bars_path = Path(args.bars_json)
    orders_path = Path(args.orders_json)
    out_dir = Path(args.out_dir)
    symbol = args.symbol or "MOCK"
    initial_cash = float(args.initial_cash or 1000.0)

    if not bars_path.exists():
        sys.stderr.write(f"bars.json not found: {bars_path}\n")
        return EXIT_USAGE
    if not orders_path.exists():
        sys.stderr.write(f"orders.json not found: {orders_path}\n")
        return EXIT_USAGE

    bars_raw = _load_bars(bars_path)
    orders_raw = _load_orders(orders_path)

    if len(orders_raw) != len(bars_raw):
        sys.stderr.write(
            f"orders_by_bar length ({len(orders_raw)}) must equal bars length ({len(bars_raw)})\n"
        )
        return EXIT_USAGE

    bars = [_bar_to_obj(b, i) for i, b in enumerate(bars_raw)]
    orders_by_bar: list[list[AdapterOrder]] = []
    for ob in orders_raw:
        if not isinstance(ob, list):
            raise ValueError("each orders_by_bar[i] must be a list")
        orders_by_bar.append([_order_to_adapter(o) for o in ob])

    cfg = ExecutionModelV2Config(fee_rate=0.0, slippage_bps=0.0)
    model = ExecutionModelV2(cfg)
    adapter = ExecutionAdapterV1(model=model, cfg=cfg)
    init_state = PositionCashStateV2.empty(initial_cash)
    initial_equity = initial_cash

    report = run_backtest_report_v1(
        bars=bars,
        orders_by_bar=orders_by_bar,
        adapter=adapter,
        initial_state=init_state,
        initial_equity=initial_equity,
        symbol=symbol,
    )

    report_dict = report_to_dict(report)
    out_dir.mkdir(parents=True, exist_ok=True)

    report_path = out_dir / "report.json"
    write_report_json_v1(report_path, report_dict)

    if args.bundle_dir:
        bundle_dir = Path(args.bundle_dir)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        write_report_bundle_v1(bundle_dir, report_dict, include_metrics_summary=True)
        if args.verify:
            verify_report_bundle_v1(bundle_dir)
    elif args.tarball:
        bundle_tmp = out_dir / "_bundle_tmp"
        bundle_tmp.mkdir(parents=True, exist_ok=True)
        write_report_bundle_v1(bundle_tmp, report_dict, include_metrics_summary=True)
        tar_path = Path(args.tarball)
        write_bundle_tarball_v1(bundle_tmp, tar_path)
        shutil.rmtree(bundle_tmp, ignore_errors=True)
        if args.verify:
            verify_bundle_tarball_v1(tar_path)

    sys.stdout.write(f"report.json written to {report_path}\n")
    if args.json:
        sys.stdout.write(
            json.dumps({"report_path": str(report_path), "ok": True}, sort_keys=True) + "\n"
        )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="backtest_runner_cli_v1", add_help=True)
    p.add_argument("--json", action="store_true", help="emit JSON status")
    sub = p.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="run backtest and emit report.json")
    run_p.add_argument("--bars-json", type=str, required=True, help="path to bars.json")
    run_p.add_argument("--orders-json", type=str, required=True, help="path to orders.json")
    run_p.add_argument("--out-dir", type=str, required=True, help="output directory")
    run_p.add_argument("--symbol", type=str, default="MOCK", help="symbol (default: MOCK)")
    run_p.add_argument("--initial-cash", type=str, default="1000.0", help="initial cash")
    run_p.add_argument("--bundle-dir", type=str, help="write P35 bundle to this dir")
    run_p.add_argument("--tarball", type=str, help="write P36 tarball to this path")
    run_p.add_argument("--verify", action="store_true", help="verify bundle/tarball after write")
    run_p.set_defaults(_fn=_cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args._fn(args))
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return EXIT_USAGE
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"unexpected error: {e}\n")
        return EXIT_UNEXPECTED


if __name__ == "__main__":
    raise SystemExit(main())
