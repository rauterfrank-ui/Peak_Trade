#!/usr/bin/env python3
"""Offline trading-logic semantic-diff evidence contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.trading_logic_semantic_diff_evidence_v1 import (
    TradingLogicSemanticDiffEvidenceError,
    TradingLogicSemanticDiffEvidenceInputs,
    default_semantic_diff_evidence_request,
    produce_trading_logic_semantic_diff_evidence_v1,
    verify_trading_core_decision_attestation_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline trading-logic semantic-diff evidence v1: deterministically evaluate "
            "declared change class against multi-layer semantic diff bindings."
        )
    )
    parser.add_argument(
        "--baseline-trading-core-decision-attestation-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--candidate-trading-core-decision-attestation-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--declared-change-class", default="A")
    parser.add_argument("--declared-semantic-diff-summary-digest", default=None)
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.baseline_trading_core_decision_attestation_bundle_dir.is_dir():
        print(
            "[trading_logic_semantic_diff_evidence_v1] ERROR: baseline attestation bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.candidate_trading_core_decision_attestation_bundle_dir.is_dir():
        print(
            "[trading_logic_semantic_diff_evidence_v1] ERROR: candidate attestation bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        baseline = verify_trading_core_decision_attestation_bundle(
            args.baseline_trading_core_decision_attestation_bundle_dir
        )
        candidate = verify_trading_core_decision_attestation_bundle(
            args.candidate_trading_core_decision_attestation_bundle_dir
        )
        request_kwargs: dict[str, object] = {
            "baseline": baseline,
            "candidate": candidate,
            "declared_change_class": args.declared_change_class,
        }
        if args.declared_semantic_diff_summary_digest is not None:
            request_kwargs["declared_semantic_diff_summary_digest"] = (
                args.declared_semantic_diff_summary_digest
            )
        if args.correlation_id is not None:
            request_kwargs["correlation_id"] = args.correlation_id
        request = default_semantic_diff_evidence_request(**request_kwargs)
        result = produce_trading_logic_semantic_diff_evidence_v1(
            inputs=TradingLogicSemanticDiffEvidenceInputs(
                baseline_trading_core_decision_attestation_bundle_dir=args.baseline_trading_core_decision_attestation_bundle_dir,
                candidate_trading_core_decision_attestation_bundle_dir=args.candidate_trading_core_decision_attestation_bundle_dir,
                semantic_diff_request=request,
            ),
            output_dir=args.output_dir,
        )
    except TradingLogicSemanticDiffEvidenceError as exc:
        print(f"[trading_logic_semantic_diff_evidence_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_id": result.contract_id,
                "contract_status": result.contract_status,
                "evidence_status": result.evidence_status,
                "classification": result.classification,
                "minimum_change_class": result.minimum_change_class,
                "effective_change_class": result.effective_change_class,
                "semantic_diff_digest": result.semantic_diff_digest,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
