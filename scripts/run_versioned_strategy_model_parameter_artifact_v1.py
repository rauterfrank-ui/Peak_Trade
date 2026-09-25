#!/usr/bin/env python3
"""
Offline versioned strategy/model/parameter artifact v1.

Consumes verified candidate identity binding and model/parameter identity binding
bundles, optionally with an AI promotion assessment provenance bundle, producing a
manifested LEVEL_3 non-authorizing versioned artifact.

Usage:
    python3 scripts/run_versioned_strategy_model_parameter_artifact_v1.py \\
        --candidate-identity-binding-bundle-dir /path/to/candidate_identity_binding \\
        --model-parameter-identity-binding-bundle-dir /path/to/model_parameter_binding \\
        [--ai-promotion-assessment-bundle-dir /path/to/ai_assessment] \\
        --output-dir /var/evidence/versioned_artifact_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.versioned_strategy_model_parameter_artifact_v1 import (
    VersionedStrategyModelParameterArtifactError,
    VersionedStrategyModelParameterArtifactInputs,
    produce_versioned_strategy_model_parameter_artifact_v1,
)

EXIT_OK = 0
EXIT_ARTIFACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline versioned strategy/model/parameter artifact v1: deterministically "
            "bind verified strategy, model, and parameter identities without strategy "
            "execution, model inference, parameter optimization, promotion authority, "
            "ConfigPatch mutation, or runtime authority."
        )
    )
    parser.add_argument(
        "--candidate-identity-binding-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to comparison_promotion_candidate_identity_binding_v1 bundle.",
    )
    parser.add_argument(
        "--model-parameter-identity-binding-bundle-dir",
        type=Path,
        required=True,
        help=(
            "Explicit path to comparison_promotion_candidate_model_parameter_identity_binding_v1 "
            "bundle."
        ),
    )
    parser.add_argument(
        "--ai-promotion-assessment-bundle-dir",
        type=Path,
        default=None,
        help="Optional ai_promotion_assessment_v1 provenance bundle.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit versioned artifact output directory (must not exist).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.candidate_identity_binding_bundle_dir.is_dir():
        print(
            "[versioned_strategy_model_parameter_artifact_v1] ERROR: "
            "candidate identity binding bundle not found: "
            f"{args.candidate_identity_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.model_parameter_identity_binding_bundle_dir.is_dir():
        print(
            "[versioned_strategy_model_parameter_artifact_v1] ERROR: "
            "model parameter identity binding bundle not found: "
            f"{args.model_parameter_identity_binding_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if (
        args.ai_promotion_assessment_bundle_dir is not None
        and not args.ai_promotion_assessment_bundle_dir.is_dir()
    ):
        print(
            "[versioned_strategy_model_parameter_artifact_v1] ERROR: "
            "ai promotion assessment bundle not found: "
            f"{args.ai_promotion_assessment_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    inputs = VersionedStrategyModelParameterArtifactInputs(
        candidate_identity_binding_bundle_dir=args.candidate_identity_binding_bundle_dir,
        model_parameter_identity_binding_bundle_dir=(
            args.model_parameter_identity_binding_bundle_dir
        ),
        ai_promotion_assessment_bundle_dir=args.ai_promotion_assessment_bundle_dir,
    )

    try:
        result = produce_versioned_strategy_model_parameter_artifact_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except VersionedStrategyModelParameterArtifactError as exc:
        print(
            f"[versioned_strategy_model_parameter_artifact_v1] ERROR: {exc}",
            file=sys.stderr,
        )
        return EXIT_ARTIFACT_ERROR

    print(
        "[versioned_strategy_model_parameter_artifact_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"versioned_artifact_binding_status={result.versioned_artifact_binding_status} "
        f"strategy_identity_ref={result.strategy_identity_ref} "
        f"model_identity_ref={result.model_identity_ref} "
        f"parameter_set_identity_ref={result.parameter_set_identity_ref} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
