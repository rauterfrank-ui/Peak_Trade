#!/usr/bin/env python3
"""Compare archived K1 taker fees or an existing Meta investigation with the F2 result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.experiments.canonical_research_prepared_execution_v1 import publish_v1, read_v1  # noqa: E402
from src.experiments.f2_meta_cost_model_follow_up_v1 import (  # noqa: E402
    build_f2_fill_fee_meta_follow_up_v1,
    build_f2_meta_cost_model_follow_up_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--meta-record", type=Path)
    mode.add_argument(
        "--fill-input",
        type=Path,
        help=(
            "JSON with root, budget_owner_root, account, session_id, reservation_id, "
            "revision_ref [sequence, digest], metadata_path, metadata_sha256, "
            "fee_model_digest, and as_of_utc. The metadata capture contains venue_host, "
            "endpoint, known_at_utc and the original OKX instruments response."
        ),
    )
    mode.add_argument("--readback", action="store_true", help="Verify and read the saved --output.")
    parser.add_argument("--meta-identity")
    parser.add_argument("--proposal-id")
    parser.add_argument("--f2-result", type=Path)
    parser.add_argument("--f2-execution-digest")
    parser.add_argument("--offline-fixture", action="store_true", help="Label simulated K1 inputs.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.readback:
            print(json.dumps(read_v1(args.output), sort_keys=True))
            return 0
        if args.f2_result is None or args.f2_execution_digest is None:
            parser.error("--f2-result and --f2-execution-digest are required for a follow-up")
        archive = {
            "f2_result_path": args.f2_result,
            "expected_f2_execution_digest": args.f2_execution_digest,
        }
        if args.fill_input:
            packet = json.loads(args.fill_input.read_bytes())
            proof_args = {
                "root": Path(packet["root"]),
                "budget_owner_root": Path(packet["budget_owner_root"]),
                "account": packet["account"],
                "session_id": packet["session_id"],
                "reservation_id": packet["reservation_id"],
                "revision_ref": tuple(packet["revision_ref"]),
            }
            result = build_f2_fill_fee_meta_follow_up_v1(
                **archive,
                proof_args=proof_args,
                metadata_path=Path(packet["metadata_path"]),
                expected_metadata_sha256=packet["metadata_sha256"],
                expected_fee_model_digest=packet["fee_model_digest"],
                as_of_utc=packet["as_of_utc"],
                offline_fixture=args.offline_fixture,
            )
        else:
            if args.meta_identity is None or args.proposal_id is None:
                parser.error("--meta-identity and --proposal-id are required with --meta-record")
            result = build_f2_meta_cost_model_follow_up_v1(
                **archive,
                meta_record=json.loads(args.meta_record.read_bytes()),
                expected_meta_identity=args.meta_identity,
                proposal_id=args.proposal_id,
            )
        publish_v1(args.output, result)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        parser.exit(2, f"F2 Meta follow-up stopped: {exc}\n")
    print(result["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
