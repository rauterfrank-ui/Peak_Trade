#!/usr/bin/env python3
"""Offline adapter submission contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.adapter_submission_contract_v1 import (
    AdapterSubmissionContractError,
    AdapterSubmissionInputs,
    default_adapter_submission_request,
    produce_adapter_submission_contract_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline adapter submission contract v1: deterministically validate "
            "submission prerequisites and produce normalized payload evidence."
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
    parser.add_argument(
        "--trading-core-decision-attestation-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    for label, path in (
        ("reconciliation", args.runtime_state_reconciliation_bundle_dir),
        ("idempotency", args.order_intent_idempotency_bundle_dir),
        ("attestation", args.trading_core_decision_attestation_bundle_dir),
    ):
        if not path.is_dir():
            print(
                f"[adapter_submission_contract_v1] ERROR: {label} bundle not found",
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
        attestation = verify_trading_core_decision_attestation_bundle(
            args.trading_core_decision_attestation_bundle_dir
        )
        request = default_adapter_submission_request(
            idempotency=idempotency,
            reconciliation=reconciliation,
            attestation=attestation,
        )
        result = produce_adapter_submission_contract_v1(
            inputs=AdapterSubmissionInputs(
                runtime_state_reconciliation_bundle_dir=(
                    args.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=args.order_intent_idempotency_bundle_dir,
                trading_core_decision_attestation_bundle_dir=(
                    args.trading_core_decision_attestation_bundle_dir
                ),
                request=request,
            ),
            output_dir=args.output_dir,
        )
    except AdapterSubmissionContractError as exc:
        print(f"[adapter_submission_contract_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_id": result.contract_id,
                "contract_status": result.contract_status,
                "evidence_status": result.evidence_status,
                "output_dir": result.output_dir.as_posix(),
                "normalized_payload_path": (
                    result.normalized_payload_path.as_posix()
                    if result.normalized_payload_path is not None
                    else None
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
