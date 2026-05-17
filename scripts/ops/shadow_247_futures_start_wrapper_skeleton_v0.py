#!/usr/bin/env python3
"""Default-off skeleton for a future Shadow 24/7 Futures *perpetual* start wrapper.

This module is intentionally **not** a daemon, does not touch the scheduler at runtime,
does not open network or broker paths, and **always** exits fail-closed until a separate
governance implementation replaces this placeholder.

Importing this file has no side effects beyond loading this module.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence, TextIO

# -----------------------------------------------------------------------------
# Safety / scope constants (documentation + static-test anchors; not authority)
# -----------------------------------------------------------------------------

BOUNDARY_NO_LIVE = "NO_LIVE"
BOUNDARY_NO_TESTNET_UNLESS_APPROVED = "NO_TESTNET_UNLESS_SEPARATELY_APPROVED"
BOUNDARY_NO_BROKER = "NO_BROKER"
BOUNDARY_NO_PRIVATE_EXCHANGE = "NO_PRIVATE_EXCHANGE_ENDPOINT"
BOUNDARY_NO_ORDER_SUBMISSION = "NO_ORDER_SUBMISSION"
BOUNDARY_NO_NETWORK = "NO_NETWORK"
BOUNDARY_FUTURES_PERP_SCOPE = "FUTURES_OR_PERPETUAL_SCOPE_REQUIRED"
BOUNDARY_EVIDENCE_ROOT_TMP = "/tmp/peak_trade_* evidence root convention"
BOUNDARY_SUPERVISOR_LATER = "SUPERVISOR_TIMEOUT_REQUIRED_IN_FUTURE_GATE"
BOUNDARY_ABORT_LATER = "ABORT_STOP_CRITERIA_REQUIRED_IN_FUTURE_GATE"

EXIT_FAIL_CLOSED_DEFAULT = 64

# Future-only gate token (explicit operator string). **Presence does NOT enable runtime.**
FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0 = (
    "I_EXPLICITLY_CONFIRM_SHADOW_247_FUTURES_START_WRAPPER_BEYOND_DEFAULT_OFF_SKELETON_V0"
)

_MACHINE_LINES_ALWAYS = """\
RUN_STARTED=false
SCHEDULER_STARTED=false
RUNTIME_STARTED=false
READY_TO_START_FUTURES_SHADOW_247_DAEMON=false
SKELETON_ONLY=true
NETWORK_USED=false
BROKER_USED=false
EXCHANGE_USED=false
ORDER_SUBMISSION_USED=false
"""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Shadow 24/7 Futures start-wrapper **skeleton** (fail-closed, no runtime)."),
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print documented boundaries and diagnostic machine lines only.",
    )
    parser.add_argument(
        "--confirm-token",
        metavar="TOKEN",
        default="",
        help=(
            "Optional future governance token placeholder. Skeleton still exits "
            f"{EXIT_FAIL_CLOSED_DEFAULT} and never starts workloads."
        ),
    )
    parser.add_argument(
        "--evidence-root",
        metavar="PATH",
        default="",
        help=(
            "Optional `/tmp/peak_trade_*`-style absolute path checked for conventions only "
            "(this skeleton does not write files except stdout/stderr)."
        ),
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _validate_evidence_root(path_str: str) -> str | None:
    """Return error message string if invalid, else None."""
    if not path_str:
        return None
    normalized = path_str.strip()
    if not normalized.startswith("/tmp/peak_trade"):
        return "evidence-root must use /tmp/peak_trade_* operator convention when supplied"
    if ".." in normalized:
        return "evidence-root must not contain path traversal"
    return None


def _emit_banner(out: TextIO) -> None:
    out.write(
        "peak_trade shadow_247_futures_start_wrapper_skeleton_v0: "
        "FAIL-CLOSED SKELETON — no scheduler, daemon, runtime, broker, exchange, orders, "
        "or network in this artifact.\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    out = sys.stdout
    err = sys.stderr

    ev_err = _validate_evidence_root(args.evidence_root)
    if ev_err:
        err.write(ev_err + "\n")
        _emit_banner(err)
        err.write(_MACHINE_LINES_ALWAYS)
        err.write(f"EXIT_REASON=invalid_evidence_root\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n")
        return EXIT_FAIL_CLOSED_DEFAULT

    if args.inspect:
        _emit_banner(out)
        out.write("\nBoundary markers:\n")
        boundary_rows = (
            ("BOUNDARY_ABORT_LATER", BOUNDARY_ABORT_LATER),
            ("BOUNDARY_EVIDENCE_ROOT_TMP", BOUNDARY_EVIDENCE_ROOT_TMP),
            ("BOUNDARY_FUTURES_PERP_SCOPE", BOUNDARY_FUTURES_PERP_SCOPE),
            ("BOUNDARY_NO_BROKER", BOUNDARY_NO_BROKER),
            ("BOUNDARY_NO_LIVE", BOUNDARY_NO_LIVE),
            ("BOUNDARY_NO_NETWORK", BOUNDARY_NO_NETWORK),
            ("BOUNDARY_NO_ORDER_SUBMISSION", BOUNDARY_NO_ORDER_SUBMISSION),
            ("BOUNDARY_NO_PRIVATE_EXCHANGE", BOUNDARY_NO_PRIVATE_EXCHANGE),
            ("BOUNDARY_NO_TESTNET_UNLESS_APPROVED", BOUNDARY_NO_TESTNET_UNLESS_APPROVED),
            ("BOUNDARY_SUPERVISOR_LATER", BOUNDARY_SUPERVISOR_LATER),
        )
        for label, marker in boundary_rows:
            out.write(f"  {label}={marker}\n")
        out.write("\nMachine summary:\n")
        out.write(_MACHINE_LINES_ALWAYS)
        out.write(
            f"EXIT_REASON=inspect_mode_fail_closed_skeleton\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
        )
        return EXIT_FAIL_CLOSED_DEFAULT

    token = args.confirm_token.strip()

    _emit_banner(err)
    if not token:
        err.write(
            "No --confirm-token provided. This skeleton does not execute any start path "
            "(default-off).\n"
        )
    elif token != FUTURE_OPERATOR_CONFIRMATION_TOKEN_V0:
        err.write(
            "confirm-token mismatch: future governance gate not satisfied for any implementation "
            "beyond skeleton (still fail-closed for this artifact).\n"
        )
    else:
        err.write(
            "Future confirmation token accepted for bookkeeping only — this PR skeleton still "
            "does not schedule, supervise, network, broker, exchange, submit orders, "
            "or mutate trading state.\n"
        )

    if args.evidence_root:
        err.write(f"Validated evidence-root convention hint: '{args.evidence_root.strip()}'\n")

    err.write(_MACHINE_LINES_ALWAYS)
    err.write(
        f"EXIT_REASON=default_fail_closed_skeleton_v0\nEXIT_CODE={EXIT_FAIL_CLOSED_DEFAULT}\n"
    )
    return EXIT_FAIL_CLOSED_DEFAULT


if __name__ == "__main__":
    raise SystemExit(main())
