#!/usr/bin/env python3
"""CLI for WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_HARDENING_V2."""

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

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.acceptance_gates_v2 import (  # noqa: E402
    derive_acceptance_gates_v2,
    write_acceptance_gates_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.canonical_strategy_probe_v2 import (  # noqa: E402
    run_canonical_strategy_probe_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (  # noqa: E402
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.forced_wiring_fixture_v2 import (  # noqa: E402
    run_forced_wiring_fixture_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.stub_fallback_scan_v2 import (  # noqa: E402
    run_stub_fallback_scan_v2,
)


def _print(payload: dict) -> None:
    print(json.dumps(payload, sort_keys=True, indent=2))


def cmd_preflight(_: argparse.Namespace) -> int:
    _print(
        {
            "ok": True,
            "capability_id": CAPABILITY_ID,
            "owner": OWNER,
            "package_marker": PACKAGE_MARKER,
            "orders_authorized": False,
            "live_authorized": False,
            "testnet_authorized": False,
            "network_used": False,
        }
    )
    return 0


def cmd_canonical_probe(args: argparse.Namespace) -> int:
    result = run_canonical_strategy_probe_v2(evidence_root=Path(args.out))
    _print(result)
    return 0 if result.get("ok") else 2


def cmd_forced_fixture(args: argparse.Namespace) -> int:
    result = run_forced_wiring_fixture_v2(evidence_root=Path(args.out))
    _print(result)
    return 0 if result.get("ok") else 2


def cmd_stub_scan(args: argparse.Namespace) -> int:
    result = run_stub_fallback_scan_v2(repo_root=Path(args.repo_root))
    _print(result.to_dict())
    return 0 if result.ok else 2


def cmd_acceptance_gates(args: argparse.Namespace) -> int:
    canonical = json.loads(Path(args.canonical_probe).read_text(encoding="utf-8"))
    forced = json.loads(Path(args.forced_fixture).read_text(encoding="utf-8"))
    stub = json.loads(Path(args.stub_scan).read_text(encoding="utf-8"))
    verification = canonical.get("verification") or forced.get("verification")
    gates = derive_acceptance_gates_v2(
        canonical_probe=canonical,
        forced_fixture=forced,
        stub_scan=stub,
        verification=verification,
    )
    write_acceptance_gates_v2(path=Path(args.out), result=gates)
    _print(gates.to_dict())
    return 0 if gates.ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_wallclock_bridge_hardening_v2.py",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("preflight")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("canonical-strategy-probe")
    p.add_argument(
        "--out",
        default=str(
            REPO_ROOT / "evidence/ops/wallclock_bridge_hardening_v2/canonical_strategy_probe"
        ),
    )
    p.set_defaults(func=cmd_canonical_probe)

    p = sub.add_parser("forced-wiring-fixture")
    p.add_argument(
        "--out",
        default=str(REPO_ROOT / "evidence/ops/wallclock_bridge_hardening_v2/forced_wiring_fixture"),
    )
    p.set_defaults(func=cmd_forced_fixture)

    p = sub.add_parser("stub-fallback-scan")
    p.add_argument("--repo-root", default=str(REPO_ROOT))
    p.set_defaults(func=cmd_stub_scan)

    p = sub.add_parser("acceptance-gates")
    p.add_argument("--canonical-probe", required=True)
    p.add_argument("--forced-fixture", required=True)
    p.add_argument("--stub-scan", required=True)
    p.add_argument(
        "--out",
        default=str(REPO_ROOT / "evidence/ops/wallclock_bridge_hardening_v2/acceptance_gates.json"),
    )
    p.set_defaults(func=cmd_acceptance_gates)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
