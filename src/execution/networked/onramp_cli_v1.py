"""P129 — Execution networked onramp CLI (networkless, default-deny)."""

from __future__ import annotations

import argparse
import json
import os
import sys

from .onramp_runner_v1 import run_networked_onramp_v1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Networked execution onramp CLI (networkless, default-deny)"
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["shadow", "paper", "live"],
        help="shadow|paper allowed; live is rejected by guard",
    )
    parser.add_argument("--intent", required=True, choices=["place_order", "cancel_all"])
    parser.add_argument("--market", required=True)
    parser.add_argument("--qty", type=float, required=True)
    parser.add_argument(
        "--transport-allow",
        default=os.environ.get("TRANSPORT_ALLOW", "NO").strip().upper(),
        help="Default NO; YES is blocked (exit 3)",
    )
    args = parser.parse_args()

    report = run_networked_onramp_v1(
        mode=args.mode,
        dry_run=True,
        intent=args.intent,
        market=args.market,
        qty=args.qty,
        transport_allow=args.transport_allow,
    )

    print(json.dumps(report, indent=2))

    if report["transport"]["rc"] == 3:
        return 3
    if report["guards"]["rc"] != 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
