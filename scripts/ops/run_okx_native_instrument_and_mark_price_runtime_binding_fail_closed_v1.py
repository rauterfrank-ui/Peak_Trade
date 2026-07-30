#!/usr/bin/env python3
"""CLI for OKX native instrument + mark-price binding (offline probe / inventory)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (REPO_ROOT, REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.authority_inventory_v1 import (  # noqa: E402
    verify_okx_native_instrument_mark_price_authority_inventory_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.offline_integration_probe_v1 import (  # noqa: E402
    load_fixture_json,
    run_offline_okx_native_mark_price_binding_probe_v1,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=CAPABILITY_ID)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preflight")
    inv = sub.add_parser("authority-inventory")
    inv.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    probe = sub.add_parser("offline-probe")
    probe.add_argument("--instruments-fixture", type=Path, required=True)
    probe.add_argument("--mark-price-fixture", type=Path, required=True)
    probe.add_argument("--ticker-fixture", type=Path, required=True)
    probe.add_argument("--receive-ts-unix", type=float, default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "preflight":
        print(
            json.dumps(
                {
                    "ok": True,
                    "capability_id": CAPABILITY_ID,
                    "network_used": False,
                    "authorization_consumed": False,
                    "notes": ["OFFLINE_PREFLIGHT_ONLY"],
                },
                sort_keys=True,
                indent=2,
            )
        )
        return 0
    if args.cmd == "authority-inventory":
        result = verify_okx_native_instrument_mark_price_authority_inventory_v1(
            repo_root=args.repo_root
        )
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.ok else 2
    receive_ts = (
        float(args.receive_ts_unix) if args.receive_ts_unix is not None else float(time.time())
    )
    result = run_offline_okx_native_mark_price_binding_probe_v1(
        instruments_payload=load_fixture_json(args.instruments_fixture),
        mark_price_payload=load_fixture_json(args.mark_price_fixture),
        ticker_payload=load_fixture_json(args.ticker_fixture),
        receive_ts_unix=receive_ts,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
