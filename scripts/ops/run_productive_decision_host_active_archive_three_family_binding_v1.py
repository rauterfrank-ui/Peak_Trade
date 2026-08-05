#!/usr/bin/env python3
"""CLI launcher for CAPABILITY_PRODUCTIVE_DECISION_HOST_ACTIVE_ARCHIVE_THREE_FAMILY_BINDING_V1.

Separate from O2 / peak_trade_runtime (dashboard-only). Does not start via WebUI/Uvicorn.
Requires explicit Owner-GO. Public-MD-capable no-order mode only.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (  # noqa: E402
    ProductiveHostAuthorizationError,
    prove_network_and_order_boundary_v1,
    require_owner_go_v1,
    require_repository_sha_match_v1,
    resolve_git_head_sha_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    DEFAULT_SMOKE_MAX_CYCLES,
    OWNER,
    PACKAGE_MARKER,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.cycle_session_v1 import (  # noqa: E402
    run_productive_host_smoke_session_v1,
)


def cmd_preflight(args: argparse.Namespace) -> int:
    try:
        require_owner_go_v1(owner_go=bool(args.owner_go))
        sha = resolve_git_head_sha_v1(REPO_ROOT)
        require_repository_sha_match_v1(
            actual_sha=sha,
            expected_sha=str(args.expected_repo_sha),
        )
        boundary = prove_network_and_order_boundary_v1(repo_root=REPO_ROOT)
    except ProductiveHostAuthorizationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True, indent=2))
        return 2
    payload = {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "package_marker": PACKAGE_MARKER,
        "repository_sha": sha,
        "boundary": boundary.to_dict(),
        "o2_dashboard_only_unchanged": True,
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


def cmd_smoke(args: argparse.Namespace) -> int:
    mids = [float(x) for x in str(args.mids).split(",") if str(x).strip()]
    session_id = str(args.session_id or f"productive-host-smoke-{uuid.uuid4().hex[:12]}")
    result = run_productive_host_smoke_session_v1(
        owner_go=bool(args.owner_go),
        expected_repository_sha=str(args.expected_repo_sha),
        archive_root=args.archive_root,
        runtime_root=Path(args.runtime_root),
        runtime_session_id=session_id,
        mid_prices=mids,
        expected_instrument=args.expected_instrument,
        enable_activation=not bool(args.disable_activation),
        require_selection_binding=bool(args.require_selection_binding),
        min_cycle_interval_seconds=float(args.min_interval),
        max_cycles=int(args.max_cycles),
        network_session_allowed=bool(args.network_session_allowed),
        repo_root=REPO_ROOT,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_productive_decision_host_active_archive_three_family_binding_v1.py"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("--owner-go", action="store_true")
    p_pre.add_argument("--expected-repo-sha", required=True)
    p_pre.set_defaults(func=cmd_preflight)

    p_smoke = sub.add_parser("smoke")
    p_smoke.add_argument("--owner-go", action="store_true")
    p_smoke.add_argument("--expected-repo-sha", required=True)
    p_smoke.add_argument("--archive-root", required=True)
    p_smoke.add_argument("--runtime-root", required=True)
    p_smoke.add_argument("--session-id", default="")
    p_smoke.add_argument(
        "--mids",
        default="0.00035,0.000351,0.000352,0.000353,0.000354,0.000355,0.000356,0.000357",
    )
    p_smoke.add_argument("--expected-instrument", default="SATS-USDT-SWAP")
    p_smoke.add_argument("--disable-activation", action="store_true")
    p_smoke.add_argument("--require-selection-binding", action="store_true")
    p_smoke.add_argument("--min-interval", default="0.05")
    p_smoke.add_argument("--max-cycles", default=str(DEFAULT_SMOKE_MAX_CYCLES))
    p_smoke.add_argument("--network-session-allowed", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
