#!/usr/bin/env python3
"""Read a decision-linked simulated outcome from a completed Paper archive."""

import argparse
import json
from pathlib import Path
import sys

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.ops.paper_episode_learning_handoff_v1 import paper_episode_learning_handoff_v1  # noqa: E402
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoError  # noqa: E402
from src.ops.bounded_peaktrade_system_composition_v1.paper_episode_outcome_v1 import (  # noqa: E402
    read_paper_episode_outcome_v1,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--episode-id", required=True)
    handoff = parser.add_mutually_exclusive_group()
    handoff.add_argument(
        "--handoff-root", type=Path, help="Publish to a separate offline workspace"
    )
    handoff.add_argument("--verify-handoff-root", type=Path, help="Reverify an existing handoff")
    args = parser.parse_args()
    try:
        output_root = args.handoff_root or args.verify_handoff_root
        if output_root is None:
            outcome = read_paper_episode_outcome_v1(args.run_root, args.episode_id)
        else:
            outcome = paper_episode_learning_handoff_v1(
                archive_root=args.run_root,
                episode_id=args.episode_id,
                output_root=output_root,
                verify=args.verify_handoff_root is not None,
            )
    except (DdoError, OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"Paper episode outcome rejected: {exc}\n")
    print(json.dumps(outcome, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
