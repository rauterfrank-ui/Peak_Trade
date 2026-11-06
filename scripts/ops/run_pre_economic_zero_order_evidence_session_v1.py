#!/usr/bin/env python3
"""CLI for Pre-Economic Zero-Order Evidence session dry-run / verify v1.

Default: offline dry-run simulation for implementation readiness only.
Never starts a real 6h session. Never submits orders. Never grants authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ops.pre_economic_zero_order_evidence_session_runner_v1 import (  # noqa: E402
    ControllableClock,
    PRODUCTION_SESSION_DURATION_SECONDS,
    load_session_config_v1,
    run_pre_economic_zero_order_evidence_session_v1,
)
from src.ops.pre_economic_zero_order_evidence_session_verifier_v1 import (  # noqa: E402
    evaluate_implementation_readiness_binding_v1,
    verify_session_evidence_root_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pre-Economic Zero-Order Evidence session dry-run / verify "
            "(implementation readiness only; no real 6h session)."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dry = sub.add_parser("dry-run", help="Run offline dry-run evidence simulation")
    dry.add_argument("--session-id", default="pez_dry_run")
    dry.add_argument("--max-cycles", type=int, default=None)
    dry.add_argument("--json", action="store_true")
    dry.add_argument("--output-path", type=Path, default=None)
    dry.add_argument(
        "--allow-implementation-dry-run",
        action="store_true",
        help="Required when config implementation_enabled=false (canonical default).",
    )

    verify = sub.add_parser("verify", help="Verify an evidence root (read-only)")
    verify.add_argument("--evidence-root", type=Path, required=True)
    verify.add_argument("--json", action="store_true")
    verify.add_argument("--output-path", type=Path, default=None)

    bind = sub.add_parser(
        "readiness-binding",
        help="Evaluate implementation readiness binding (session remains NOT_AUTHORIZED)",
    )
    bind.add_argument("--evidence-root", type=Path, default=None)
    bind.add_argument("--json", action="store_true")
    bind.add_argument("--output-path", type=Path, default=None)

    reject = sub.add_parser(
        "reject-production-duration",
        help="Demonstrate fail-closed rejection of 21600s without authorization",
    )
    reject.add_argument("--json", action="store_true")
    reject.add_argument("--session-id", default="pez_reject_21600")

    args = parser.parse_args(argv)

    if args.command == "dry-run":
        if not args.allow_implementation_dry_run:
            print(
                "ERROR=IMPLEMENTATION_DRY_RUN_REQUIRES_EXPLICIT_FLAG",
                file=sys.stderr,
            )
            print(
                "HINT=pass --allow-implementation-dry-run for offline readiness proof",
                file=sys.stderr,
            )
            return 2
        cfg = load_session_config_v1(repo_root=ROOT)
        result = run_pre_economic_zero_order_evidence_session_v1(
            repo_root=ROOT,
            config=cfg,
            session_id=args.session_id,
            clock=ControllableClock(0.0),
            max_cycles=args.max_cycles,
            allow_implementation_dry_run=True,
            operator_go_present=False,
            evidence_subdir=args.session_id,
        )
        payload = result.to_dict()
        _emit(payload, json_mode=args.json, output_path=args.output_path)
        return 0 if result.implementation_readiness.endswith("PASS") else 1

    if args.command == "verify":
        verification = verify_session_evidence_root_v1(
            evidence_root=args.evidence_root.resolve(),
            repo_root=ROOT,
        )
        payload = verification.to_dict()
        _emit(payload, json_mode=args.json, output_path=args.output_path)
        return 0 if verification.implementation_readiness.endswith("PASS") else 1

    if args.command == "readiness-binding":
        payload = evaluate_implementation_readiness_binding_v1(
            repo_root=ROOT,
            evidence_root=args.evidence_root.resolve() if args.evidence_root else None,
        )
        _emit(payload, json_mode=args.json, output_path=args.output_path)
        return 0

    if args.command == "reject-production-duration":
        cfg = load_session_config_v1(repo_root=ROOT)
        result = run_pre_economic_zero_order_evidence_session_v1(
            repo_root=ROOT,
            config=cfg,
            session_id=args.session_id,
            clock=ControllableClock(0.0),
            requested_duration_seconds=PRODUCTION_SESSION_DURATION_SECONDS,
            allow_implementation_dry_run=True,
            operator_go_present=False,
            evidence_subdir=args.session_id,
        )
        payload = result.to_dict()
        _emit(payload, json_mode=args.json, output_path=None)
        assert result.abort_reason in {
            "PRODUCTION_DURATION_BLOCKED",
            "SESSION_NOT_AUTHORIZED",
            "TIME_BUDGET_EXCEEDED",
        }
        return 0

    return 2


def _emit(payload: dict, *, json_mode: bool, output_path: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    if json_mode or output_path is None:
        if json_mode:
            print(text, end="")
        else:
            for key in (
                "implementation_readiness",
                "session_evidence_status",
                "session_evidence",
                "terminal_state",
                "abort_reason",
                "orders_attempted",
                "orders_submitted",
                "consumer_eligibility",
                "six_hour_session_executed",
                "session_execution_authorized",
            ):
                if key in payload:
                    print(f"{key}={payload[key]}")


if __name__ == "__main__":
    raise SystemExit(main())
