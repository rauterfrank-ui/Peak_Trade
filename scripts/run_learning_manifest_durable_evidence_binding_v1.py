#!/usr/bin/env python3
"""
Offline Package G — bind ConfigPatchManifest v1 + CandidateLineageManifest v1 to durable evidence.

Produces a validated durable evidence bundle with binding index and MANIFEST.sha256 only.
No promotion, apply, runtime, registry mutation, or live authority.

Usage:
    python3 scripts/run_learning_manifest_durable_evidence_binding_v1.py \\
        --config-patch-manifest reports/manifests/config_patch.json \\
        --candidate-lineage-manifest reports/manifests/lineage.json \\
        --output-dir /var/evidence/learning_bundle_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.config_patch_manifest_v1 import ConfigPatchManifestValidationError
from src.meta.learning_loop.manifest_durable_evidence_binding_v1 import (
    ManifestDurableEvidenceBindingError,
    produce_learning_manifest_durable_evidence_bundle_v1,
)

EXIT_OK = 0
EXIT_BINDING_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline Package G: bind validated learning manifest artifacts to "
            "durable evidence (index + MANIFEST.sha256)."
        )
    )
    parser.add_argument(
        "--config-patch-manifest",
        type=Path,
        required=True,
        help="Explicit path to validated ConfigPatchManifest v1 JSON.",
    )
    parser.add_argument(
        "--candidate-lineage-manifest",
        type=Path,
        required=True,
        help="Explicit path to validated CandidateLineageManifest v1 JSON.",
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

    if not args.config_patch_manifest.is_file():
        print(
            "[learning_manifest_durable_evidence_binding] ERROR: "
            f"config patch manifest not found: {args.config_patch_manifest}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.candidate_lineage_manifest.is_file():
        print(
            "[learning_manifest_durable_evidence_binding] ERROR: "
            f"candidate lineage manifest not found: {args.candidate_lineage_manifest}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        result = produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=args.config_patch_manifest,
            candidate_lineage_manifest_path=args.candidate_lineage_manifest,
            output_dir=args.output_dir,
        )
    except ManifestDurableEvidenceBindingError as exc:
        print(f"[learning_manifest_durable_evidence_binding] ERROR: {exc}", file=sys.stderr)
        return EXIT_BINDING_ERROR
    except ConfigPatchManifestValidationError as exc:
        print(
            f"[learning_manifest_durable_evidence_binding] VALIDATION_ERROR: {exc}",
            file=sys.stderr,
        )
        if exc.verdict:
            print(
                f"[learning_manifest_durable_evidence_binding] VERDICT={exc.verdict}",
                file=sys.stderr,
            )
        return EXIT_BINDING_ERROR

    print(
        "[learning_manifest_durable_evidence_binding] wrote durable evidence bundle to "
        f"{result.output_dir} "
        f"(config_patch_manifest_id={result.config_patch_manifest_id}, "
        f"candidate_lineage_manifest_id={result.candidate_lineage_manifest_id})"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
