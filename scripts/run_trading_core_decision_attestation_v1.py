#!/usr/bin/env python3
"""Offline trading-core decision attestation contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.trading_core_decision_attestation_v1 import (
    TradingCoreDecisionAttestationError,
    TradingCoreDecisionAttestationInputs,
    default_trading_core_decision_attestation_request,
    produce_trading_core_decision_attestation_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_order_intent_idempotency_bundle,
    verify_trading_session_single_writer_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline trading-core decision attestation v1: deterministically evaluate "
            "module attestation chain bindings without creating or submitting orders."
        )
    )
    parser.add_argument(
        "--trading-session-single-writer-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--canonical-order-lifecycle-bundle-dir", type=Path, required=True)
    parser.add_argument("--order-intent-idempotency-bundle-dir", type=Path, required=True)
    parser.add_argument("--client-order-id", default=None)
    parser.add_argument("--order-intent-digest", default=None)
    parser.add_argument("--canonical-order-id", default=None)
    parser.add_argument("--instrument-type", default=None)
    parser.add_argument("--correlation-id", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.trading_session_single_writer_bundle_dir.is_dir():
        print(
            "[trading_core_decision_attestation_v1] ERROR: trading session bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.canonical_order_lifecycle_bundle_dir.is_dir():
        print(
            "[trading_core_decision_attestation_v1] ERROR: lifecycle bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.order_intent_idempotency_bundle_dir.is_dir():
        print(
            "[trading_core_decision_attestation_v1] ERROR: idempotency bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        trading_session = verify_trading_session_single_writer_bundle(
            args.trading_session_single_writer_bundle_dir
        )
        lifecycle = verify_canonical_order_lifecycle_bundle(
            args.canonical_order_lifecycle_bundle_dir
        )
        idempotency = verify_order_intent_idempotency_bundle(
            args.order_intent_idempotency_bundle_dir
        )
        defaults = default_trading_core_decision_attestation_request(
            trading_session=trading_session,
            lifecycle=lifecycle,
            idempotency=idempotency,
            client_order_id=args.client_order_id or "client-order-001",
            order_intent_digest=(
                args.order_intent_digest
                or "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
            ),
            canonical_order_id=args.canonical_order_id or "canonical-order-001",
            instrument_type=args.instrument_type or "FUTURES",
            correlation_id=args.correlation_id or "offline-attestation-correlation-001",
        )
        request = defaults
    except TradingCoreDecisionAttestationError as exc:
        print(f"[trading_core_decision_attestation_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    try:
        result = produce_trading_core_decision_attestation_v1(
            inputs=TradingCoreDecisionAttestationInputs(
                trading_session_single_writer_bundle_dir=args.trading_session_single_writer_bundle_dir,
                canonical_order_lifecycle_bundle_dir=args.canonical_order_lifecycle_bundle_dir,
                order_intent_idempotency_bundle_dir=args.order_intent_idempotency_bundle_dir,
                attestation_request=request,
            ),
            output_dir=args.output_dir,
        )
    except TradingCoreDecisionAttestationError as exc:
        print(f"[trading_core_decision_attestation_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_status": result.contract_status,
                "attestation_status": result.attestation_status,
                "classification": result.classification,
                "contract_id": result.contract_id,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
