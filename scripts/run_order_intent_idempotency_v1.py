#!/usr/bin/env python3
"""Offline order intent idempotency contract v1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.meta.learning_loop.order_intent_idempotency_v1 import (
    OrderIntentIdempotencyError,
    OrderIntentIdempotencyInputs,
    default_order_intent_idempotency_request,
    produce_order_intent_idempotency_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_trading_session_single_writer_bundle,
)

EXIT_OK = 0
EXIT_CONTRACT_ERROR = 1
EXIT_USAGE_ERROR = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Offline order intent idempotency v1: deterministically evaluate "
            "order intent replay and duplicate protection without creating or "
            "submitting orders."
        )
    )
    parser.add_argument(
        "--trading-session-single-writer-bundle-dir",
        type=Path,
        required=True,
    )
    parser.add_argument("--canonical-order-lifecycle-bundle-dir", type=Path, required=True)
    parser.add_argument("--client-order-id", default=None)
    parser.add_argument("--order-intent-digest", default=None)
    parser.add_argument("--canonical-order-id", default=None)
    parser.add_argument("--instrument-type", default=None)
    parser.add_argument("--evaluation-time", default=None)
    parser.add_argument("--issued-at", default=None)
    parser.add_argument("--expires-at", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.trading_session_single_writer_bundle_dir.is_dir():
        print(
            "[order_intent_idempotency_v1] ERROR: trading session bundle not found",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    if not args.canonical_order_lifecycle_bundle_dir.is_dir():
        print(
            "[order_intent_idempotency_v1] ERROR: lifecycle bundle not found",
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
        defaults = default_order_intent_idempotency_request(
            trading_session=trading_session,
            lifecycle=lifecycle,
            evaluation_time=args.evaluation_time or "2026-06-29T12:00:00+00:00",
            issued_at=args.issued_at or "2026-06-29T00:00:00+00:00",
            expires_at=args.expires_at or "2026-06-30T00:00:00+00:00",
        )
        intent = defaults.canonical_order_intent_identity
        order = defaults.canonical_order_identity
        from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
            CanonicalOrderIdentity,
            CanonicalOrderIntentIdentity,
        )
        from src.meta.learning_loop.order_intent_idempotency_v1 import (
            OrderIntentIdempotencyRequest,
            derive_canonical_idempotency_key,
            replace_request_idempotency_key,
        )
        from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
            _compute_order_identity_digest,
            _compute_order_intent_identity_digest,
        )

        intent = CanonicalOrderIntentIdentity(
            client_order_id=args.client_order_id or intent.client_order_id,
            order_intent_digest=args.order_intent_digest or intent.order_intent_digest,
            instrument_type=args.instrument_type or intent.instrument_type,
            venue=intent.venue,
            account=intent.account,
            instrument=intent.instrument,
            trading_epoch=intent.trading_epoch,
        )
        order = CanonicalOrderIdentity(
            canonical_order_id=args.canonical_order_id or order.canonical_order_id,
            client_order_id=args.client_order_id or order.client_order_id,
        )
        request = OrderIntentIdempotencyRequest(
            **{
                **defaults.__dict__,
                "canonical_order_intent_identity": intent,
                "canonical_order_identity": order,
            }
        )
        derived = derive_canonical_idempotency_key(
            market_type=intent.instrument_type,
            canonical_order_identity_digest=_compute_order_identity_digest(order=order),
            canonical_order_intent_identity_digest=_compute_order_intent_identity_digest(
                intent=intent
            ),
            session_identity_digest=trading_session.session_identity_digest,
            writer_identity=trading_session.writer_identity,
            writer_generation=request.writer_generation,
            writer_revision=request.writer_revision,
            order_generation=request.order_generation,
            order_revision=request.order_revision,
            intent_semantic_digest=request.intent_semantic_digest,
            lifecycle_contract_digest=request.lifecycle_contract_digest,
            authority_lease_digest=request.authority_lease_digest,
            clock_trust_digest=request.clock_trust_digest,
            provenance_digest=request.provenance_digest,
            cross_domain_lineage_digest=request.cross_domain_lineage_digest,
            idempotency_scope=request.idempotency_scope,
            contract_version=request.idempotency_contract_version,
        )
        request = replace_request_idempotency_key(request, derived)
    except OrderIntentIdempotencyError as exc:
        print(f"[order_intent_idempotency_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    try:
        result = produce_order_intent_idempotency_v1(
            inputs=OrderIntentIdempotencyInputs(
                trading_session_single_writer_bundle_dir=args.trading_session_single_writer_bundle_dir,
                canonical_order_lifecycle_bundle_dir=args.canonical_order_lifecycle_bundle_dir,
                idempotency_request=request,
            ),
            output_dir=args.output_dir,
        )
    except OrderIntentIdempotencyError as exc:
        print(f"[order_intent_idempotency_v1] ERROR: {exc}", file=sys.stderr)
        return EXIT_CONTRACT_ERROR

    print(
        json.dumps(
            {
                "contract_status": result.contract_status,
                "idempotency_status": result.idempotency_status,
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
