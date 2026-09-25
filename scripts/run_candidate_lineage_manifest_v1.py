#!/usr/bin/env python3
"""
Offline CandidateLineageManifest v1 producer — explicit reference input to manifest JSON.

Produces a validated, deterministic CandidateLineageManifestV1 JSON artifact only.
No promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_candidate_lineage_manifest_v1.py \\
        --input-path reports/lineage_inputs/example.json \\
        --output-path reports/lineage_manifests/example_lineage.json
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateLineageManifestError,
    CandidateLineageManifestValidationError,
    produce_candidate_lineage_manifest_v1_from_paths,
)

EXIT_OK = 0
EXIT_PRODUCER_ERROR = 1
EXIT_USAGE_ERROR = 2


def _parse_created_at(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("created-at must be an ISO8601 timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline CandidateLineageManifest v1 producer: explicit reference-only "
            "JSON input to validated manifest artifact."
        )
    )
    parser.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="Explicit offline lineage producer input (.json).",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Destination path for the validated CandidateLineageManifest v1 JSON file.",
    )
    parser.add_argument(
        "--created-at",
        type=_parse_created_at,
        default=None,
        help="Optional ISO8601 timestamp override for manifest created_at (default: input or UTC now).",
    )
    parser.add_argument(
        "--created-by",
        default="package_f_candidate_lineage_manifest_producer_v1",
        help="Optional created_by label stored in the manifest envelope.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input_path.is_file():
        print(
            f"[candidate_lineage_manifest] ERROR: input file not found: {args.input_path}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        manifest = produce_candidate_lineage_manifest_v1_from_paths(
            input_path=args.input_path,
            output_path=args.output_path,
            created_at=args.created_at,
            created_by=args.created_by,
        )
    except CandidateLineageManifestValidationError as exc:
        print(f"[candidate_lineage_manifest] VALIDATION_ERROR: {exc}", file=sys.stderr)
        if exc.verdict:
            print(f"[candidate_lineage_manifest] VERDICT={exc.verdict}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except CandidateLineageManifestError as exc:
        print(f"[candidate_lineage_manifest] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR
    except OSError as exc:
        print(f"[candidate_lineage_manifest] ERROR: {exc}", file=sys.stderr)
        return EXIT_PRODUCER_ERROR

    print(
        "[candidate_lineage_manifest] wrote validated CandidateLineageManifest v1 to "
        f"{args.output_path} (lineage_manifest_id={manifest.lineage_manifest_id}, "
        f"refs={len(manifest.refs)})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
