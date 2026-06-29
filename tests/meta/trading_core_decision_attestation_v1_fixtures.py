"""Fixtures for trading_core_decision_attestation_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.trading_core_decision_attestation_v1 import (
    TradingCoreDecisionAttestationInputs,
    default_trading_core_decision_attestation_request,
    produce_trading_core_decision_attestation_v1,
    verify_canonical_order_lifecycle_bundle,
    verify_order_intent_idempotency_bundle,
    verify_trading_session_single_writer_bundle,
)
from tests.meta.order_intent_idempotency_v1_fixtures import (
    produce_order_intent_idempotency_fixture,
)


@dataclass(frozen=True)
class TradingCoreDecisionAttestationFixtureBundle:
    trading_session_single_writer_bundle_dir: Path
    canonical_order_lifecycle_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    trading_core_decision_attestation_bundle_dir: Path | None = None


def produce_trading_core_decision_attestation_fixture(
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
    trading_session_name: str = "trading_session_for_decision_attestation",
    lifecycle_name: str = "canonical_order_lifecycle_for_attestation",
    idempotency_name: str = "order_intent_idempotency_for_attestation",
    attestation_name: str = "trading_core_decision_attestation",
    client_order_id: str = "client-order-001",
    order_intent_digest: str = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899",
    canonical_order_id: str = "canonical-order-001",
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    correlation_id: str = "offline-attestation-correlation-001",
) -> TradingCoreDecisionAttestationFixtureBundle:
    idempotency_fixture = produce_order_intent_idempotency_fixture(
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
        idempotency_name=idempotency_name,
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        canonical_order_id=canonical_order_id,
        instrument_type=instrument_type,
        instrument=instrument,
    )
    assert idempotency_fixture.order_intent_idempotency_bundle_dir is not None
    assert idempotency_fixture.canonical_order_lifecycle_bundle_dir is not None
    assert idempotency_fixture.trading_session_single_writer_bundle_dir is not None

    trading_session = verify_trading_session_single_writer_bundle(
        idempotency_fixture.trading_session_single_writer_bundle_dir
    )
    lifecycle = verify_canonical_order_lifecycle_bundle(
        idempotency_fixture.canonical_order_lifecycle_bundle_dir
    )
    idempotency = verify_order_intent_idempotency_bundle(
        idempotency_fixture.order_intent_idempotency_bundle_dir
    )

    request = default_trading_core_decision_attestation_request(
        trading_session=trading_session,
        lifecycle=lifecycle,
        idempotency=idempotency,
        client_order_id=client_order_id,
        order_intent_digest=order_intent_digest,
        canonical_order_id=canonical_order_id,
        instrument_type=instrument_type,
        correlation_id=correlation_id,
    )

    attestation_dir: Path | None = None
    if produce_output:
        attestation_dir = durable_root / attestation_name
        produce_trading_core_decision_attestation_v1(
            inputs=TradingCoreDecisionAttestationInputs(
                trading_session_single_writer_bundle_dir=idempotency_fixture.trading_session_single_writer_bundle_dir,
                canonical_order_lifecycle_bundle_dir=idempotency_fixture.canonical_order_lifecycle_bundle_dir,
                order_intent_idempotency_bundle_dir=idempotency_fixture.order_intent_idempotency_bundle_dir,
                attestation_request=request,
            ),
            output_dir=attestation_dir,
        )

    return TradingCoreDecisionAttestationFixtureBundle(
        trading_session_single_writer_bundle_dir=idempotency_fixture.trading_session_single_writer_bundle_dir,
        canonical_order_lifecycle_bundle_dir=idempotency_fixture.canonical_order_lifecycle_bundle_dir,
        order_intent_idempotency_bundle_dir=idempotency_fixture.order_intent_idempotency_bundle_dir,
        trading_core_decision_attestation_bundle_dir=attestation_dir,
    )
