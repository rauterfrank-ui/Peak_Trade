#!/usr/bin/env python3
"""
Offline comparison config patch manifest cross-domain lineage binding v1.

Consumes exactly one verified comparison_promotion_candidate_model_parameter_identity_binding_v1
bundle and one validated config_patch_manifest_v1.json artifact, producing a manifested LEVEL_3
non-authorizing cross-domain lineage binding artifact.

Usage:
    python3 scripts/run_comparison_config_patch_manifest_cross_domain_lineage_binding_v1.py \\
        --model-parameter-identity-binding-bundle-dir /path/to/step1_bundle \\
        --config-patch-manifest-path /path/to/config_patch_manifest_v1.json \\
        --output-dir /var/evidence/cross_domain_lineage_binding_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.comparison_config_patch_manifest_cross_domain_lineage_binding_v1 import (
    ComparisonConfigPatchManifestCrossDomainLineageBindingError,
    ComparisonConfigPatchManifestCrossDomainLineageBindingInputs,
    produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1,
)

EXIT_OK = 0
EXIT_EVIDENCE_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline comparison config patch manifest cross-domain lineage binding v1: "
            "digest-bind verified comparison candidate lineage to an existing ConfigPatch "
            "manifest without creating, modifying, or applying patches."
        )
    )
    parser.add_argument(
        "--model-parameter-identity-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to a published "
            "comparison_promotion_candidate_model_parameter_identity_binding_v1 bundle."
        ),
    )
    parser.add_argument(
        "--config-patch-manifest-path",
        type=Path,
        required=True,
        help="Explicit path to a validated config_patch_manifest_v1.json artifact.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit cross-domain lineage binding output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.model_parameter_identity_binding_bundle_dir.is_dir():
        print(
            "[comparison_config_patch_manifest_cross_domain_lineage_binding_v1] ERROR: "
            "model parameter identity binding bundle not found: "
            f"{args.model_parameter_identity_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    if not args.config_patch_manifest_path.is_file():
        print(
            "[comparison_config_patch_manifest_cross_domain_lineage_binding_v1] ERROR: "
            f"config patch manifest not found: {args.config_patch_manifest_path}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = ComparisonConfigPatchManifestCrossDomainLineageBindingInputs(
        model_parameter_identity_binding_bundle_dir=(
            args.model_parameter_identity_binding_bundle_dir
        ),
        config_patch_manifest_path=args.config_patch_manifest_path,
    )

    try:
        result = produce_comparison_config_patch_manifest_cross_domain_lineage_binding_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except ComparisonConfigPatchManifestCrossDomainLineageBindingError as exc:
        print(
            f"[comparison_config_patch_manifest_cross_domain_lineage_binding_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_EVIDENCE_ERROR

    print(
        "[comparison_config_patch_manifest_cross_domain_lineage_binding_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"cross_domain_lineage_binding_status={result.cross_domain_lineage_binding_status} "
        f"candidate_identity_ref={result.candidate_identity_ref} "
        f"config_patch_manifest_id={result.config_patch_manifest_id} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
