#!/usr/bin/env python3
"""
Offline Package E21 — bind EXPERIMENT identity manifest + LineageRef to durable evidence.

Produces a validated durable evidence bundle with binding index and MANIFEST.sha256 only.
No experiment execution, promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_experiment_durable_evidence_binding_v1.py \\
        --manifest-dir reports/experiments/identity_manifest_dir \\
        --experiment-lineage-ref reports/lineage_refs/experiment_ref.json \\
        --output-dir /var/evidence/experiment_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.experiment_durable_evidence_binding_v1 import (
    ExperimentDurableEvidenceBindingError,
    produce_experiment_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package E21: bind validated EXPERIMENT identity manifest and "
            "LineageRef to durable evidence (index + MANIFEST.sha256)."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        required=True,
        help="Explicit directory containing experiment_identity_manifest_v1.json.",
    )
    parser.add_argument(
        "--experiment-lineage-ref",
        type=Path,
        required=True,
        help="Explicit path to a validated Package M EXPERIMENT LineageRef JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit durable evidence bundle directory (must not exist; outside /tmp).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.manifest_dir.is_dir():
        print(
            f"[experiment_durable_evidence_binding] ERROR: manifest directory not found: "
            f"{args.manifest_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.experiment_lineage_ref.is_file():
        print(
            "[experiment_durable_evidence_binding] ERROR: "
            f"experiment lineage ref not found: {args.experiment_lineage_ref}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=args.manifest_dir,
            experiment_lineage_ref_path=args.experiment_lineage_ref,
            output_dir=args.output_dir,
        )
    except ExperimentDurableEvidenceBindingError as exc:
        print(f"[experiment_durable_evidence_binding] ERROR: {exc}", file=sys.stderr)
        return EXIT_BINDING_ERROR

    print(
        "[experiment_durable_evidence_binding] wrote durable evidence bundle to "
        f"{result.output_dir} (experiment_identity_id={result.experiment_identity_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
