#!/usr/bin/env python3
"""Offline runtime-state reconciliation contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.runtime_state_reconciliation_v1 import (
    RuntimeStateReconciliationError,
    RuntimeStateReconciliationInputs,
    default_runtime_reconciliation_request,
    produce_runtime_state_reconciliation_v1,
    verify_trading_logic_semantic_diff_evidence_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline runtime-state reconciliation v1: deterministically evaluate "
            "local versus venue snapshot bindings with R1-R4 reconciliation levels."
        )
    )
    parser.add_argument(
        "--trading-logic-semantic-diff-evidence-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--declared-reconciliation-state", default="CLEAN")
    parser.add_argument("--instrument-type", default="FUTURES")
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.trading_logic_semantic_diff_evidence_bundle_dir.is_dir():
        print(
            "[runtime_state_reconciliation_v1] ERROR: semantic diff evidence bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        semantic_diff = verify_trading_logic_semantic_diff_evidence_bundle(
            args.trading_logic_semantic_diff_evidence_bundle_dir
        )
        request_kwargs: dict[str, object] = {
            "semantic_diff": semantic_diff,
            "declared_reconciliation_state": args.declared_reconciliation_state,
            "instrument_type": args.instrument_type,
        }
        if args.correlation_id is not None:
            request_kwargs["correlation_id"] = args.correlation_id
        request = default_runtime_reconciliation_request(**request_kwargs)
        result = produce_runtime_state_reconciliation_v1(
            inputs=RuntimeStateReconciliationInputs(
                trading_logic_semantic_diff_evidence_bundle_dir=(
                    args.trading_logic_semantic_diff_evidence_bundle_dir
                ),
                reconciliation_request=request,
            ),
            output_dir=args.output_dir,
        )
    except RuntimeStateReconciliationError as exc:
        print(f"[runtime_state_reconciliation_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_id": result.contract_id,
                "contract_status": result.contract_status,
                "evidence_status": result.evidence_status,
                "classification": result.classification,
                "reconciliation_state": result.reconciliation_state,
                "reconciliation_digest": result.reconciliation_digest,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
