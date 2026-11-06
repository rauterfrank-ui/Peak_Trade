#!/usr/bin/env python3
"""Offline KillSwitch writer-fencing and independent read paths v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KillSwitchWriterFencingError,
    default_killswitch_writer_fencing_evaluation_input,
    produce_killswitch_writer_fencing_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline KillSwitch writer-fencing and independent read paths v1: "
            "deterministically evaluate writer fencing, event digest chain, and "
            "independent read-path invariants; produce non-authorizing evidence."
        )
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output_dir.exists():
        print(
            "[killswitch_writer_fencing_and_independent_read_paths_v1] ERROR: output exists",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_killswitch_writer_fencing_v1(
            request=default_killswitch_writer_fencing_evaluation_input(),
            output_dir=args.output_dir,
        )
    except KillSwitchWriterFencingError as exc:
        print(
            f"[killswitch_writer_fencing_and_independent_read_paths_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "evidence_id": result.evidence_id,
                "decision": result.decision,
                "decision_code": result.decision_code,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
