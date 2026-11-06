#!/usr/bin/env python3
from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run placeholder for the Finish Level C kill-switch drill. "
            "This command does not mutate runtime, config, or live state."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("status", "dry-run"),
        default="status",
        help="Run mode for the placeholder drill. Defaults to 'status'.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "dry-run":
        print("kill-switch drill placeholder: dry-run only, no mutation performed")
    else:
        print("kill-switch drill placeholder: status ok, no mutation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
