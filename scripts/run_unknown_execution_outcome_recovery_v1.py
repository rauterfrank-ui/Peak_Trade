#!/usr/bin/env python3
"""Offline unknown-execution-outcome recovery contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.unknown_execution_outcome_recovery_v1 import (
    UnknownExecutionOutcomeRecoveryError,
    UnknownExecutionRecoveryInputs,
    default_unknown_execution_recovery_request,
    produce_unknown_execution_outcome_recovery_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline unknown-execution-outcome recovery v1: deterministically classify "
            "unknown transport outcomes using snapshot evidence bindings."
        )
    )
    parser.add_argument(
        "--runtime-state-reconciliation-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--order-intent-idempotency-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--recovery-classification", default="FILLED")
    parser.add_argument("--transport-outcome", default="UNKNOWN_OUTCOME")
    parser.add_argument("--instrument-type", default="FUTURES")
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.runtime_state_reconciliation_bundle_dir.is_dir():
        print(
            "[unknown_execution_outcome_recovery_v1] ERROR: reconciliation bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.order_intent_idempotency_bundle_dir.is_dir():
        print(
            "[unknown_execution_outcome_recovery_v1] ERROR: idempotency bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        reconciliation = verify_runtime_state_reconciliation_bundle(
            args.runtime_state_reconciliation_bundle_dir
        )
        idempotency = verify_order_intent_idempotency_bundle(
            args.order_intent_idempotency_bundle_dir
        )
        request_kwargs: dict[str, object] = {
            "reconciliation": reconciliation,
            "idempotency": idempotency,
            "recovery_classification": args.recovery_classification,
            "transport_outcome": args.transport_outcome,
            "instrument_type": args.instrument_type,
        }
        if args.correlation_id is not None:
            request_kwargs["correlation_id"] = args.correlation_id
        request = default_unknown_execution_recovery_request(**request_kwargs)
        result = produce_unknown_execution_outcome_recovery_v1(
            inputs=UnknownExecutionRecoveryInputs(
                runtime_state_reconciliation_bundle_dir=(
                    args.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=args.order_intent_idempotency_bundle_dir,
                recovery_request=request,
            ),
            output_dir=args.output_dir,
        )
    except UnknownExecutionOutcomeRecoveryError as exc:
        print(f"[unknown_execution_outcome_recovery_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_id": result.contract_id,
                "contract_status": result.contract_status,
                "evidence_status": result.evidence_status,
                "recovery_classification": result.recovery_classification,
                "recovery_digest": result.recovery_digest,
                "resubmit_allowed": result.resubmit_allowed,
                "reconciliation_required": result.reconciliation_required,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
