#!/usr/bin/env python3
"""Offline independent pre-trade safety kernel v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.independent_pre_trade_safety_kernel_v1 import (
    IndependentPreTradeSafetyKernelError,
    IndependentPreTradeSafetyKernelInputs,
    default_pre_trade_safety_evaluation_request,
    produce_independent_pre_trade_safety_kernel_v1,
    verify_authority_lease_bundle,
    verify_clock_trust_and_expiry_bundle,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
    verify_venue_capability_snapshot_bundle,
    _trading_session_from_attestation,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline independent pre-trade safety kernel v1: deterministically evaluate "
            "pre-trade safety gates and produce non-authorizing decision evidence."
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
    parser.add_argument(
        "--venue-capability-snapshot-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--clock-trust-and-expiry-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--authority-lease-bundle-dir",
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
        ("venue_capability", args.venue_capability_snapshot_bundle_dir),
        ("clock_trust", args.clock_trust_and_expiry_bundle_dir),
        ("authority_lease", args.authority_lease_bundle_dir),
    ):
        if not path.is_dir():
            print(
                f"[independent_pre_trade_safety_kernel_v1] ERROR: {label} bundle not found",
                file=sys.stderr,
            )
            return EXIT_USAGE_ERROR

    try:
        idempotency = verify_order_intent_idempotency_bundle(
            args.order_intent_idempotency_bundle_dir
        )
        reconciliation = verify_runtime_state_reconciliation_bundle(
            args.runtime_state_reconciliation_bundle_dir
        )
        attestation = verify_trading_core_decision_attestation_bundle(
            args.trading_core_decision_attestation_bundle_dir
        )
        venue_capability = verify_venue_capability_snapshot_bundle(
            args.venue_capability_snapshot_bundle_dir
        )
        authority_lease = verify_authority_lease_bundle(args.authority_lease_bundle_dir)
        clock_trust = verify_clock_trust_and_expiry_bundle(args.clock_trust_and_expiry_bundle_dir)
        _trading_session_from_attestation(attestation)
        request = default_pre_trade_safety_evaluation_request(
            idempotency=idempotency,
            reconciliation=reconciliation,
            attestation=attestation,
            venue_capability=venue_capability,
            authority_lease=authority_lease,
            clock_trust=clock_trust,
        )
        result = produce_independent_pre_trade_safety_kernel_v1(
            inputs=IndependentPreTradeSafetyKernelInputs(
                runtime_state_reconciliation_bundle_dir=(
                    args.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=args.order_intent_idempotency_bundle_dir,
                trading_core_decision_attestation_bundle_dir=(
                    args.trading_core_decision_attestation_bundle_dir
                ),
                venue_capability_snapshot_bundle_dir=args.venue_capability_snapshot_bundle_dir,
                clock_trust_and_expiry_bundle_dir=args.clock_trust_and_expiry_bundle_dir,
                authority_lease_bundle_dir=args.authority_lease_bundle_dir,
                request=request,
            ),
            output_dir=args.output_dir,
        )
    except IndependentPreTradeSafetyKernelError as exc:
        print(f"[independent_pre_trade_safety_kernel_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "safety_decision_id": result.safety_decision_id,
                "decision": result.decision,
                "contract_status": result.contract_status,
                "evidence_status": result.evidence_status,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
