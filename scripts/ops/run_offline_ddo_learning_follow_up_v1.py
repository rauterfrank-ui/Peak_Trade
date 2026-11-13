#!/usr/bin/env python3
"""Plan, complete or read a DDO learning cycle in an isolated offline workspace."""

from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError  # noqa: E402
from src.learning.deterministic_decision_outcome_v0.offline_learning_follow_up_v1 import (  # noqa: E402
    complete_offline_learning_follow_up_v1,
    export_completed_offline_learning_evidence_v1,
    prepare_offline_learning_follow_up_v1,
    read_offline_learning_follow_up_v1,
)


def _research(args):
    import pandas as pd

    from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1
    from src.experiments.offline_ddo_research_cycle_v1 import (
        OfflineDdoResearchProfileV1,
        OfflineDdoResearchRequestV1,
        run_offline_ddo_research_cycle_v1,
    )

    declaration = (
        OfflineDdoResearchProfileV1.model_validate_json(args.profile.read_bytes())
        if args.profile is not None
        else OfflineDdoResearchRequestV1.model_validate_json(args.request.read_bytes())
    )
    frame = pd.read_csv(BytesIO(args.bars.read_bytes()), index_col=0, float_precision="round_trip")
    if any(pd.Timestamp(value).tzinfo is None for value in frame.index):
        raise ValueError("EXPLICIT_BAR_TIMEZONE_REQUIRED")
    frame.index = pd.to_datetime(frame.index, utc=True, format="ISO8601")
    return run_offline_ddo_research_cycle_v1(
        args.root,
        args.cycle,
        plan_digest=args.plan_digest,
        request=declaration,
        bars=frame,
        cfg=json.loads(args.config.read_bytes()),
        code=inspect_code_provenance_v1(ROOT),
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
    export = sub.add_parser("export-evidence", help="Export the verified completed learning state")
    export.add_argument("--plan-digest", required=True)
    research = sub.add_parser("research", help="Run bounded native trials and scoped GVEF replay")
    research.add_argument("--plan-digest", required=True)
    declaration = research.add_mutually_exclusive_group(required=True)
    declaration.add_argument("--request", type=Path, help="Bound offline research request JSON")
    declaration.add_argument(
        "--profile", type=Path, help="Offline profile with one GVEF-gated follow-up"
    )
    research.add_argument(
        "--bars", type=Path, required=True, help="Explicit timestamp-indexed UTC CSV"
    )
    research.add_argument(
        "--config", type=Path, required=True, help="Explicit resolved backtest JSON"
    )
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
        elif args.action == "export-evidence":
            result = export_completed_offline_learning_evidence_v1(
                args.root, args.cycle, plan_digest=args.plan_digest
            )
        elif args.action == "research":
            result = _research(args)
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
