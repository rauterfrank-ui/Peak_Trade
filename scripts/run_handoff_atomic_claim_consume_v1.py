#!/usr/bin/env python3
"""
Offline handoff atomic claim/consume contract v1.

Consumes exactly one verified secure_handoff_envelope_v1 bundle, producing a
manifested LEVEL_3 non-authorizing atomic claim/consume contract for offline
evidence only.

Usage:
    python3 scripts/run_handoff_atomic_claim_consume_v1.py \\
        --secure-handoff-envelope-bundle-dir /path/to/envelope \\
        --evaluation-time 2026-06-29T12:00:00+00:00 \\
        --output-dir /var/evidence/handoff_atomic_claim_consume_001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.meta.learning_loop.handoff_atomic_claim_consume_v1 import (
    ClaimStateContext,
    HandoffAtomicClaimConsumeError,
    HandoffAtomicClaimConsumeInputs,
    HandoffAtomicClaimConsumeRequest,
    default_claim_consume_request,
    produce_handoff_atomic_claim_consume_v1,
    verify_secure_handoff_envelope_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline handoff atomic claim/consume v1: deterministically describe "
            "atomic claim and consume transitions for a verified secure handoff "
            "envelope without executing claim, consume, state mutation, lock, "
            "reservation, or consumer invocation."
        )
    )
    parser.add_argument(
        "--secure-handoff-envelope-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published secure_handoff_envelope_v1 bundle.",
    )
    parser.add_argument(
        "--evaluation-time",
        default=None,
        help="Explicit evaluation time UTC instant (+00:00 or Z).",
    )
    parser.add_argument(
        "--consumer-identity-ref",
        default=None,
        help="Consumer identity ref (defaults from secure handoff envelope).",
    )
    parser.add_argument(
        "--consumer-identity-version",
        default=None,
        help="Consumer identity version (defaults from secure handoff envelope).",
    )
    parser.add_argument(
        "--transition-evaluate",
        default="FULL_CONTRACT",
        choices=("FULL_CONTRACT", "CLAIM", "CONSUME"),
        help="Transition evaluation mode (default FULL_CONTRACT).",
    )
    parser.add_argument(
        "--claim-state",
        default=None,
        help="Current claim state for transition evaluation (e.g. UNCLAIMED, CLAIMED).",
    )
    parser.add_argument(
        "--claim-revision",
        type=int,
        default=None,
        help="Current CAS revision for transition evaluation.",
    )
    parser.add_argument(
        "--claim-identity",
        default=None,
        help="Existing claim identity for consume evaluation.",
    )
    parser.add_argument(
        "--consume-identity",
        default=None,
        help="Existing consume identity for duplicate consume evaluation.",
    )
    parser.add_argument(
        "--allowed-offline-capability",
        action="append",
        default=None,
        dest="allowed_offline_capabilities",
        help="Allowed offline capability (repeatable).",
    )
    parser.add_argument(
        "--source-revision",
        default=None,
        help="Source revision for provenance metadata.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit handoff atomic claim/consume output directory (must not exist).",
    )
    return parser.parse_args(argv)


def _resolve_request(args: argparse.Namespace) -> HandoffAtomicClaimConsumeRequest:
    envelope = verify_secure_handoff_envelope_bundle(args.secure_handoff_envelope_bundle_dir)
    defaults = default_claim_consume_request(envelope=envelope)

    claim_state_context = None
    if any(
        field is not None
        for field in (
            args.claim_state,
            args.claim_revision,
            args.claim_identity,
            args.consume_identity,
        )
    ):
        claim_state_context = ClaimStateContext(
            current_state=args.claim_state or "UNCLAIMED",
            current_revision=args.claim_revision if args.claim_revision is not None else 0,
            claim_identity=args.claim_identity or "",
            consume_identity=args.consume_identity or "",
        )

    explicit_fields = (
        args.evaluation_time,
        args.consumer_identity_ref,
        args.consumer_identity_version,
        args.allowed_offline_capabilities,
        args.source_revision,
        claim_state_context,
    )
    if (
        all(field is None for field in explicit_fields)
        and args.transition_evaluate == "FULL_CONTRACT"
    ):
        return defaults

    return HandoffAtomicClaimConsumeRequest(
        evaluation_time=args.evaluation_time or defaults.evaluation_time,
        consumer_identity_ref=args.consumer_identity_ref or defaults.consumer_identity_ref,
        consumer_identity_version=(
            args.consumer_identity_version or defaults.consumer_identity_version
        ),
        transition_evaluate=args.transition_evaluate,
        claim_state_context=claim_state_context,
        allowed_offline_capabilities=tuple(
            args.allowed_offline_capabilities or defaults.allowed_offline_capabilities
        ),
        source_revision=args.source_revision or defaults.source_revision,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.secure_handoff_envelope_bundle_dir.is_dir():
        print(
            "[handoff_atomic_claim_consume_v1] ERROR: secure handoff envelope bundle not found: "
            f"{args.secure_handoff_envelope_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        claim_consume_request = _resolve_request(args)
    except HandoffAtomicClaimConsumeError as exc:
        print(f"[handoff_atomic_claim_consume_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    inputs = HandoffAtomicClaimConsumeInputs(
        secure_handoff_envelope_bundle_dir=args.secure_handoff_envelope_bundle_dir,
        claim_consume_request=claim_consume_request,
    )

    try:
        result = produce_handoff_atomic_claim_consume_v1(
            inputs=inputs,
            output_dir=args.output_dir,
        )
    except HandoffAtomicClaimConsumeError as exc:
        print(f"[handoff_atomic_claim_consume_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        "[handoff_atomic_claim_consume_v1] OK "
        f"contract_id={result.contract_id} "
        f"contract_status={result.contract_status} "
        f"claim_identity={result.claim_identity} "
        f"consume_identity={result.consume_identity} "
        f"output_dir={result.output_dir}"
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
