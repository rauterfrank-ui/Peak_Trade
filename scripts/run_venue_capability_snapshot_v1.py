#!/usr/bin/env python3
"""Offline venue capability snapshot v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.venue_capability_snapshot_v1 import (
    VenueCapabilitySnapshotError,
    classify_venue_capability_drift_v1,
    parse_venue_capability_input,
    produce_venue_capability_snapshot_v1,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline venue capability snapshot v1: deterministically validate "
            "venue capability input and produce snapshot evidence."
        )
    )
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--baseline-snapshot-json", type=Path, default=None)
    parser.add_argument("--drift-output-json", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input_json.is_file():
        print(
            "[venue_capability_snapshot_v1] ERROR: input json not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        payload = read_manifest(args.input_json)
        input_data = parse_venue_capability_input(payload)
        result = produce_venue_capability_snapshot_v1(
            input_data=input_data,
            output_dir=args.output_dir,
        )
        drift_payload = None
        if args.baseline_snapshot_json is not None:
            if not args.baseline_snapshot_json.is_file():
                print(
                    "[venue_capability_snapshot_v1] ERROR: baseline snapshot json not found",
                    file=sys.stderr,
                )
                return EXIT_USAGE_ERROR
            baseline_snapshot = read_manifest(args.baseline_snapshot_json)
            candidate_snapshot = read_manifest(result.snapshot_path)
            drift_payload = classify_venue_capability_drift_v1(
                baseline_snapshot=baseline_snapshot,
                candidate_snapshot=candidate_snapshot,
                baseline_snapshot_ref=args.baseline_snapshot_json.as_posix(),
                candidate_snapshot_ref=result.snapshot_path.as_posix(),
            )
            if args.drift_output_json is not None:
                args.drift_output_json.write_text(
                    json.dumps(drift_payload, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
    except VenueCapabilitySnapshotError as exc:
        print(f"[venue_capability_snapshot_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    output = {
        "snapshot_id": result.snapshot_id,
        "snapshot_status": result.snapshot_status,
        "capability_digest": result.capability_digest,
        "output_dir": result.output_dir.as_posix(),
        "snapshot_path": result.snapshot_path.as_posix(),
    }
    if drift_payload is not None:
        output["drift_classification"] = drift_payload["drift_classification"]
        output["capability_digest_changed"] = drift_payload["capability_digest_changed"]
    print(json.dumps(output, indent=2, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
