#!/usr/bin/env python3
"""Plan, complete or read a DDO learning cycle in an isolated offline workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError  # noqa: E402
from src.learning.deterministic_decision_outcome_v0.offline_learning_follow_up_v1 import (  # noqa: E402
    complete_offline_learning_follow_up_v1,
    prepare_offline_learning_follow_up_v1,
    read_offline_learning_follow_up_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="Absolute offline state root")
    parser.add_argument("--cycle", required=True, help="Unique cycle key inside this root")
    sub = parser.add_subparsers(dest="action", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument(
        "--request",
        type=Path,
        required=True,
        help=(
            "JSON with planned_at_utc, candidate_decision_refs and scope "
            "(session_id, account_scope, code_sha, config_hash, instrument_id, "
            "native_instrument_id, venue, n_bars)"
        ),
    )
    complete = sub.add_parser("complete")
    complete.add_argument("--plan-digest", required=True)
    complete.add_argument(
        "--source",
        type=Path,
        required=True,
        help="JSON with known_at_utc and the original offline O4 snapshot",
    )
    readback = sub.add_parser("readback")
    readback.add_argument("--plan-digest", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "plan":
            result = prepare_offline_learning_follow_up_v1(
                args.root, args.cycle, json.loads(args.request.read_bytes())
            )
        elif args.action == "complete":
            result = complete_offline_learning_follow_up_v1(
                args.root,
                args.cycle,
                plan_digest=args.plan_digest,
                source=json.loads(args.source.read_bytes()),
            )
        else:
            result = read_offline_learning_follow_up_v1(
                args.root, args.cycle, plan_digest=args.plan_digest
            )
    except (DdoError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Offline DDO follow-up stopped: {exc}\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
