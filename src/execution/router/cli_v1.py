"""
P113 — Execution Router CLI v1 (mocks-only)

Safety:
- mode must be shadow|paper
- default dry-run ON (no side effects beyond mock adapter calls)
- no network, no keys
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any, Dict

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.router.router_v1 import (
    ExecutionRouterContextV1,
    build_execution_router_v1,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="peaktrade-execution-router-cli-v1")
    p.add_argument("--mode", choices=["shadow", "paper"], required=True)
    p.add_argument("--adapter", default="mock", help="registry name (default: mock)")
    p.add_argument(
        "--market",
        default="BTC-USD",
        help="symbol/market identifier (adapter-specific)",
    )
    p.add_argument(
        "--intent",
        choices=["place_order", "cancel_all", "batch_cancel"],
        default="place_order",
    )
    p.add_argument("--qty", type=float, default=1.0)
    p.add_argument("--side", choices=["buy", "sell"], default="buy")
    p.add_argument("--order-type", choices=["market", "limit"], default="market")
    p.add_argument("--client-id", default="p113-cli")
    p.add_argument("--dry-run", choices=["YES", "NO"], default="YES")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    dry_run = ns.dry_run == "YES"

    ctx = ExecutionRouterContextV1(
        mode=ns.mode,
        adapter_name=ns.adapter,
        market=None,  # adapter selection uses market type; symbol for order
        dry_run=dry_run,
    )
    router = build_execution_router_v1(ctx)

    report: Dict[str, Any] = {
        "meta": {"ok": False, "mode": ns.mode, "dry_run": dry_run},
        "result": None,
    }

    if ns.intent == "place_order":
        intent = OrderIntentV1(
            symbol=ns.market,
            side=ns.side,
            qty=float(ns.qty),
            order_type=ns.order_type,
            client_id=ns.client_id,
        )
        res = router.place_order(intent)
        report["result"] = asdict(res)
        report["meta"]["ok"] = bool(res.ok)
    elif ns.intent == "cancel_all":
        n = router.cancel_all(symbol=ns.market)
        report["result"] = {"canceled": int(n)}
        report["meta"]["ok"] = True
    else:
        n = router.batch_cancel(order_ids=["o1", "o2"])
        report["result"] = {"batch_canceled": int(n)}
        report["meta"]["ok"] = True

    print(json.dumps(report, sort_keys=True))
    return 0 if report["meta"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
