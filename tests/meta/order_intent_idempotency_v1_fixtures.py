"""Fixtures for order_intent_idempotency_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.order_intent_idempotency_v1 import (
    OrderIntentIdempotencyInputs,
    default_order_intent_idempotency_request,
    prior_binding_from_request,
    produce_order_intent_idempotency_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_trading_session_single_writer_bundle,
)
from tests.meta.canonical_order_lifecycle_v1_fixtures import (
    produce_canonical_order_lifecycle_fixture,
)


@dataclass(frozen=True)
class OrderIntentIdempotencyFixtureBundle:
    trading_session_single_writer_bundle_dir: Path
    canonical_order_lifecycle_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path | None = None


def produce_order_intent_idempotency_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    all_domains_pass: bool = True,
    use_candidate_lineage: bool = True,
    include_ai_assessment: bool = False,
    evaluation_time: str = "2026-06-29T12:00:00+00:00",
    valid_from: str = "2026-06-29T00:00:00+00:00",
    valid_until: str = "2026-06-30T00:00:00+00:00",
    revocation_state: str = "NOT_REVOKED",
    produce_output: bool = True,
    trading_session_name: str = "trading_session_for_order_intent_idempotency",
    lifecycle_name: str = "canonical_order_lifecycle_for_idempotency",
    idempotency_name: str = "order_intent_idempotency",
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    instrument_type: str = "FUTURES",
    instrument: str = "ETH-PERP",
    with_prior_binding: bool = False,
    prior_exact_match: bool = True,
) -> OrderIntentIdempotencyFixtureBundle:
    lifecycle_fixture = produce_canonical_order_lifecycle_fixture(
        tmp_path,
        durable_root,
        all_domains_pass=all_domains_pass,
        use_candidate_lineage=use_candidate_lineage,
        include_ai_assessment=include_ai_assessment,
        evaluation_time=evaluation_time,
        valid_from=valid_from,
        valid_until=valid_until,
        revocation_state=revocation_state,
        produce_output=True,
        trading_session_name=trading_session_name,
        lifecycle_name=lifecycle_name,
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        canonical_order_id=canonical_order_id,
        instrument_type=instrument_type,
        instrument=instrument,
    )
    assert lifecycle_fixture.canonical_order_lifecycle_bundle_dir is not None
    assert lifecycle_fixture.trading_session_single_writer_bundle_dir is not None

    trading_session = verify_trading_session_single_writer_bundle(
        lifecycle_fixture.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        lifecycle_fixture.canonical_order_lifecycle_bundle_dir
    )

    prior_binding = None
    if with_prior_binding:
        base_request = default_order_intent_idempotency_request(
            trading_session=trading_session,
            lifecycle=lifecycle,
            client_order_id=client_order_id,
            order_intent_digest=order_intent_digest,
            canonical_order_id=canonical_order_id,
            instrument_type=instrument_type,
            evaluation_time=evaluation_time,
            issued_at=valid_from,
            expires_at=valid_until,
        )
        prior_binding = prior_binding_from_request(
            base_request,
            session_identity_digest=trading_session.session_identity_digest,
            writer_identity=trading_session.writer_identity,
        )
        if not prior_exact_match:
            prior_binding = type(prior_binding)(
                **{**prior_binding.__dict__, "intent_payload_digest": "tampered-payload-digest"}
            )

    request = default_order_intent_idempotency_request(
        trading_session=trading_session,
        lifecycle=lifecycle,
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        canonical_order_id=canonical_order_id,
        instrument_type=instrument_type,
        evaluation_time=evaluation_time,
        issued_at=valid_from,
        expires_at=valid_until,
        prior_artifact_binding=prior_binding,
    )

    idempotency_dir: Path | None = None
    if produce_output:
        idempotency_dir = durable_root / idempotency_name
        produce_order_intent_idempotency_v1(
            inputs=OrderIntentIdempotencyInputs(
                trading_session_single_writer_bundle_dir=lifecycle_fixture.trading_session_single_writer_bundle_dir,
                canonical_order_lifecycle_bundle_dir=lifecycle_fixture.canonical_order_lifecycle_bundle_dir,
                idempotency_request=request,
            ),
            output_dir=idempotency_dir,
        )

    return OrderIntentIdempotencyFixtureBundle(
        trading_session_single_writer_bundle_dir=lifecycle_fixture.trading_session_single_writer_bundle_dir,
        canonical_order_lifecycle_bundle_dir=lifecycle_fixture.canonical_order_lifecycle_bundle_dir,
        order_intent_idempotency_bundle_dir=idempotency_dir,
    )
