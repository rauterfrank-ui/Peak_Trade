#!/usr/bin/env python3
"""CLI for WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1.

Offline probes only. No network, no orders, no credentials.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (  # noqa: E402
    run_bridge_cycles_from_mids_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (  # noqa: E402
    verify_bridge_evidence_root_v1,
    verify_full_economic_reconstruction_v1,
)


def cmd_preflight(_: argparse.Namespace) -> int:
    payload = {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "package_marker": PACKAGE_MARKER,
        "orders_authorized": False,
        "live_authorized": False,
        "testnet_authorized": False,
        "economic_validity_pass": False,
        "promotion_pass": False,
        "network_used": False,
        "notes": ["OFFLINE_PREFLIGHT_ONLY"],
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


def cmd_runtime_probe(args: argparse.Namespace) -> int:
    mids = [float(x) for x in args.mids.split(",")]
    state, cycles = run_bridge_cycles_from_mids_v1(
        mids,
        session_id=args.session_id,
        start_ts_unix=float(args.start_ts),
    )
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cycle_path = out / "bridge_cycle_ledger.jsonl"
    fill_path = out / "bridge_fill_ledger.jsonl"
    with cycle_path.open("w", encoding="utf-8") as fh:
        for c in cycles:
            fh.write(json.dumps(c.to_dict(), sort_keys=True) + "\n")
    with fill_path.open("w", encoding="utf-8") as fh:
        for fill in state.fill_ledger:
            fh.write(json.dumps(fill, sort_keys=True) + "\n")
    portfolio = dict(state.portfolio.snapshot())
    (out / "portfolio_snapshot.json").write_text(
        json.dumps(portfolio, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    verification = verify_full_economic_reconstruction_v1(
        cycle_ledger=state.cycle_ledger,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=portfolio,
    )
    (out / "full_economic_reconstruction_verifier.json").write_text(
        json.dumps(verification.to_dict(), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = {
        "ok": verification.ok,
        "capability_id": CAPABILITY_ID,
        "cycles": len(cycles),
        "fills": len(state.fill_ledger),
        "actionable_intents": sum(
            1 for c in cycles if c.intended_action.get("intended_side") in {"BUY", "SELL"}
        ),
        "equity": str(state.portfolio.economic_metrics().equity),
        "verification": verification.to_dict(),
        "orders_authorized": False,
        "live_authorized": False,
        "economic_validity_pass": False,
    }
    (out / "probe_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0 if verification.ok else 2


def cmd_verify_evidence(args: argparse.Namespace) -> int:
    result = verify_bridge_evidence_root_v1(evidence_root=Path(args.evidence_root))
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.py"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight")
    p_pre.set_defaults(func=cmd_preflight)

    p_probe = sub.add_parser("runtime-probe")
    p_probe.add_argument(
        "--mids",
        default="3500,3510,3520,3550,3600,3650,3700,3750",
        help="Comma-separated mid prices (offline probe)",
    )
    p_probe.add_argument("--session-id", default="offline-runtime-probe")
    p_probe.add_argument("--start-ts", default="1700000000")
    p_probe.add_argument(
        "--out",
        default=str(
            REPO_ROOT
            / "evidence/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/local_runtime_probe"
        ),
    )
    p_probe.set_defaults(func=cmd_runtime_probe)

    p_verify = sub.add_parser("verify-evidence")
    p_verify.add_argument("--evidence-root", required=True)
    p_verify.set_defaults(func=cmd_verify_evidence)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
