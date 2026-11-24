"""Publish a fresh original entry for a later explicitly started five-slot procedure."""

import argparse
from pathlib import Path
import time

from scripts.ops.prepared_five_slot_run_v1 import read, admit_entry_v1, verify_plan_v1, REPO
from src.experiments.canonical_experiment_identity_v1 import inspect_code_provenance_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    immutable_json_v1,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--lane", required=True, choices=[f"LANE_{i}" for i in range(1, 6)])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--slot-config", type=Path)
    source.add_argument("--operator-start", type=Path)
    args = parser.parse_args(argv)
    plan = read(args.plan)
    verify_plan_v1(plan, code=inspect_code_provenance_v1(REPO))
    slot = next(row for row in plan["slots"] if row["lane_id"] == args.lane)
    field = "operator_start" if args.operator_start else "slot_config"
    path = args.operator_start or args.slot_config
    entry = dict(
        plan_digest=plan["plan_digest"],
        lane_id=args.lane,
        session_id=slot["session_id"],
        **{field: str(path.resolve(strict=True))},
    )
    admit_entry_v1(plan, slot, entry, now=time.time())
    target = Path(slot["entry_input"])
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # A later valid generation may replace an expired pointer, never its originals.
    from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
        atomic_write_json,
    )

    archive = target.parent / ("entry-" + str(time.time_ns()) + ".json")
    immutable_json_v1(archive, entry)
    atomic_write_json(path=target, payload=entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
