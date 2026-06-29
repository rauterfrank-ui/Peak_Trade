"""Fixtures for canonical_order_lifecycle_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.canonical_order_lifecycle_v1 import (
    CanonicalOrderLifecycleInputs,
    default_canonical_order_lifecycle_request,
    produce_canonical_order_lifecycle_v1,
    verify_trading_session_single_writer_bundle,
)
from tests.meta.trading_session_single_writer_v1_fixtures import (
    produce_trading_session_single_writer_fixture,
)


@dataclass(frozen=True)
class CanonicalOrderLifecycleFixtureBundle:
    trading_session_single_writer_bundle_dir: Path
    canonical_order_lifecycle_bundle_dir: Path | None = None


def produce_canonical_order_lifecycle_fixture(
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
    trading_session_name: str = "trading_session_for_order_lifecycle",
    lifecycle_name: str = "canonical_order_lifecycle",
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    transition_identity: str = "transition-initial-bind-001",
    transition_type: str = "INITIAL_BIND",
    previous_order_state: str = "",
    expected_order_state: str = "",
    target_order_state: str = "INTENT_CREATED",
    order_revision: int = 1,
    order_generation: int = 1,
    idempotency_key: str = "idempotency-initial-bind-001",
    replay_identity: str = "replay-initial-bind-001",
    instrument_type: str = "FUTURES",
    instrument: str = "ETH-PERP",
) -> CanonicalOrderLifecycleFixtureBundle:
    trading_session_fixture = produce_trading_session_single_writer_fixture(
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
        single_writer_name=trading_session_name,
        instrument=instrument,
    )
    assert trading_session_fixture.trading_session_single_writer_bundle_dir is not None

    lifecycle_dir: Path | None = None
    if produce_output:
        trading_session = verify_trading_session_single_writer_bundle(
            trading_session_fixture.trading_session_single_writer_bundle_dir
        )
        request = default_canonical_order_lifecycle_request(
            trading_session=trading_session,
            client_order_id=client_order_id,
            order_intent_digest=order_intent_digest,
            canonical_order_id=canonical_order_id,
            transition_identity=transition_identity,
            transition_type=transition_type,
            previous_order_state=previous_order_state,
            expected_order_state=expected_order_state,
            target_order_state=target_order_state,
            order_revision=order_revision,
            order_generation=order_generation,
            idempotency_key=idempotency_key,
            replay_identity=replay_identity,
            instrument_type=instrument_type,
        )
        lifecycle_dir = durable_root / lifecycle_name
        produce_canonical_order_lifecycle_v1(
            inputs=CanonicalOrderLifecycleInputs(
                trading_session_single_writer_bundle_dir=trading_session_fixture.trading_session_single_writer_bundle_dir,
                lifecycle_request=request,
            ),
            output_dir=lifecycle_dir,
        )

    return CanonicalOrderLifecycleFixtureBundle(
        trading_session_single_writer_bundle_dir=trading_session_fixture.trading_session_single_writer_bundle_dir,
        canonical_order_lifecycle_bundle_dir=lifecycle_dir,
    )
