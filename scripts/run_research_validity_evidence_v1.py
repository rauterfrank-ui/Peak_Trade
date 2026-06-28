#!/usr/bin/env python3
"""
Offline learning loop research validity evidence v1.

Consumes verified comparison_checkpoint_v1 and research input artifact bundles,
producing a manifested LEVEL_3 non-authorizing research validity evidence artifact.

Usage:
    python3 scripts/run_research_validity_evidence_v1.py \\
        --checkpoint-bundle-dir /path/to/checkpoint \\
        --experiment-identity-bundle-dir /path/to/experiment_identity \\
        ... (all required input bundle dirs) \\
        --output-dir /var/evidence/research_validity_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.research_validity_evidence_v1 import (
    ResearchValidityEvidenceError,
    ResearchValidityProducerInputs,
    produce_research_validity_evidence_v1,
)

EXIT_OK = 0
EXIT_VALIDITY_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline research validity evidence v1: produce LEVEL_3 non-authorizing "
            "research validity evidence from verified input bundles."
        )
    )
    parser.add_argument("--checkpoint-bundle-dir", type=Path, required=True)
    parser.add_argument("--experiment-identity-bundle-dir", type=Path, required=True)
    parser.add_argument("--dataset-identity-bundle-dir", type=Path, required=True)
    parser.add_argument("--partition-evidence-bundle-dir", type=Path, required=True)
    parser.add_argument("--selection-procedure-bundle-dir", type=Path, required=True)
    parser.add_argument("--walk-forward-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--cost-stress-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--slippage-stress-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--funding-stress-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--parameter-stability-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--regime-breakdown-bundle-dir", type=Path, required=True)
    parser.add_argument("--overfitting-risk-result-bundle-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    required_dirs = (
        args.checkpoint_bundle_dir,
        args.experiment_identity_bundle_dir,
        args.dataset_identity_bundle_dir,
        args.partition_evidence_bundle_dir,
        args.selection_procedure_bundle_dir,
        args.walk_forward_result_bundle_dir,
        args.cost_stress_result_bundle_dir,
        args.slippage_stress_result_bundle_dir,
        args.funding_stress_result_bundle_dir,
        args.parameter_stability_result_bundle_dir,
        args.regime_breakdown_bundle_dir,
        args.overfitting_risk_result_bundle_dir,
    )
    for bundle_dir in required_dirs:
        if not bundle_dir.is_dir():
            print(
                f"[research_validity_evidence_v1] ERROR: bundle not found: {bundle_dir}",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

    inputs = ResearchValidityProducerInputs(
        checkpoint_bundle_dir=args.checkpoint_bundle_dir,
        experiment_identity_bundle_dir=args.experiment_identity_bundle_dir,
        dataset_identity_bundle_dir=args.dataset_identity_bundle_dir,
        partition_evidence_bundle_dir=args.partition_evidence_bundle_dir,
        selection_procedure_bundle_dir=args.selection_procedure_bundle_dir,
        walk_forward_result_bundle_dir=args.walk_forward_result_bundle_dir,
        cost_stress_result_bundle_dir=args.cost_stress_result_bundle_dir,
        slippage_stress_result_bundle_dir=args.slippage_stress_result_bundle_dir,
        funding_stress_result_bundle_dir=args.funding_stress_result_bundle_dir,
        parameter_stability_result_bundle_dir=args.parameter_stability_result_bundle_dir,
        regime_breakdown_bundle_dir=args.regime_breakdown_bundle_dir,
        overfitting_risk_result_bundle_dir=args.overfitting_risk_result_bundle_dir,
    )

    try:
        result = produce_research_validity_evidence_v1(inputs=inputs, output_dir=args.output_dir)
    except ResearchValidityEvidenceError as exc:
        print(f"[research_validity_evidence_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_VALIDITY_ERROR

    print(
        "[research_validity_evidence_v1] OK "
        f"comparison_definition_id={result.comparison_definition_id} "
        f"research_validity_status={result.research_validity_status} "
        f"artifact_id={result.artifact_id} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
