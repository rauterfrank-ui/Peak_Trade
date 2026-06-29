#!/usr/bin/env python3
"""
Offline canonical order lifecycle contract v1.

Consumes exactly one verified trading_session_single_writer_v1 bundle and
produces a manifested LEVEL_3 non-authorizing canonical order lifecycle
contract for offline evidence only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    CanonicalOrderIdentity,
    CanonicalOrderIntentIdentity,
    CanonicalOrderLifecycleError,
    CanonicalOrderLifecycleInputs,
    CanonicalOrderLifecycleRequest,
    default_canonical_order_lifecycle_request,
    produce_canonical_order_lifecycle_v1,
    verify_trading_session_single_writer_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline canonical order lifecycle v1: deterministically evaluate "
            "order lifecycle transitions without creating, submitting, or "
            "mutating orders."
        )
    )
    parser.add_argument(
        "--trading-session-single-writer-bundle-dir",
        type=Path,
        required=True,
        help="Explicit path to a published trading_session_single_writer_v1 bundle.",
    )
    parser.add_argument("--client-order-id", default=None)
    parser.add_argument("--order-intent-digest", default=None)
    parser.add_argument("--canonical-order-id", default=None)
    parser.add_argument("--transition-identity", default=None)
    parser.add_argument("--transition-type", default=None)
    parser.add_argument("--previous-order-state", default=None)
    parser.add_argument("--expected-order-state", default=None)
    parser.add_argument("--target-order-state", default=None)
    parser.add_argument("--order-revision", type=int, default=None)
    parser.add_argument("--order-generation", type=int, default=None)
    parser.add_argument("--idempotency-key", default=None)
    parser.add_argument("--replay-identity", default=None)
    parser.add_argument("--instrument-type", default=None)
    parser.add_argument("--prior-order-revision", type=int, default=0)
    parser.add_argument("--prior-order-generation", type=int, default=0)
    parser.add_argument("--prior-lifecycle-evidence-digest", default="")
    parser.add_argument("--prior-idempotency-key", default="")
    parser.add_argument("--prior-transition-identity", default="")
    parser.add_argument("--order-lifecycle-lineage-json", default=None)
    parser.add_argument("--source-revision", default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Explicit canonical order lifecycle output directory (must not exist).",
    )
    return parser.parse_args(argv)


def _resolve_request(
    args: argparse.Namespace,
    *,
    trading_session,
) -> CanonicalOrderLifecycleRequest:
    defaults = default_canonical_order_lifecycle_request(trading_session=trading_session)
    lineage = dict(defaults.order_lifecycle_lineage)
    if args.order_lifecycle_lineage_json:
        loaded = json.loads(args.order_lifecycle_lineage_json)
        if not isinstance(loaded, dict):
            raise CanonicalOrderLifecycleError("order_lifecycle_lineage must be a JSON object")
        lineage = loaded

    intent = defaults.canonical_order_intent_identity
    order = defaults.canonical_order_identity
    return CanonicalOrderLifecycleRequest(
        canonical_order_intent_identity=CanonicalOrderIntentIdentity(
            client_order_id=args.client_order_id or intent.client_order_id,
            order_intent_digest=args.order_intent_digest or intent.order_intent_digest,
            instrument_type=args.instrument_type or intent.instrument_type,
            venue=intent.venue,
            account=intent.account,
            instrument=intent.instrument,
            trading_epoch=intent.trading_epoch,
        ),
        canonical_order_identity=CanonicalOrderIdentity(
            canonical_order_id=args.canonical_order_id or order.canonical_order_id,
            client_order_id=args.client_order_id or order.client_order_id,
        ),
        transition_identity=args.transition_identity or defaults.transition_identity,
        transition_type=args.transition_type or defaults.transition_type,
        previous_order_state=(
            defaults.previous_order_state
            if args.previous_order_state is None
            else args.previous_order_state
        ),
        expected_order_state=(
            defaults.expected_order_state
            if args.expected_order_state is None
            else args.expected_order_state
        ),
        target_order_state=args.target_order_state or defaults.target_order_state,
        order_revision=args.order_revision or defaults.order_revision,
        order_generation=args.order_generation or defaults.order_generation,
        idempotency_key=args.idempotency_key or defaults.idempotency_key,
        replay_identity=args.replay_identity or defaults.replay_identity,
        order_lifecycle_lineage=lineage,
        prior_order_revision=args.prior_order_revision,
        prior_order_generation=args.prior_order_generation,
        prior_lifecycle_evidence_digest=args.prior_lifecycle_evidence_digest,
        prior_idempotency_key=args.prior_idempotency_key,
        prior_transition_identity=args.prior_transition_identity,
        source_revision=args.source_revision or defaults.source_revision,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.trading_session_single_writer_bundle_dir.is_dir():
        print(
            "[canonical_order_lifecycle_v1] ERROR: trading session bundle not found: "
            f"{args.trading_session_single_writer_bundle_dir}",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    try:
        trading_session = verify_trading_session_single_writer_bundle(
            args.trading_session_single_writer_bundle_dir
        )
        lifecycle_request = _resolve_request(args, trading_session=trading_session)
    except (CanonicalOrderLifecycleError, json.JSONDecodeError) as exc:
        print(f"[canonical_order_lifecycle_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    try:
        result = produce_canonical_order_lifecycle_v1(
            inputs=CanonicalOrderLifecycleInputs(
                trading_session_single_writer_bundle_dir=args.trading_session_single_writer_bundle_dir,
                lifecycle_request=lifecycle_request,
            ),
            output_dir=args.output_dir,
        )
    except CanonicalOrderLifecycleError as exc:
        print(f"[canonical_order_lifecycle_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_status": result.contract_status,
                "lifecycle_status": result.lifecycle_status,
                "contract_id": result.contract_id,
                "output_dir": result.output_dir.as_posix(),
            },
            indent=2,
        )
    )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
