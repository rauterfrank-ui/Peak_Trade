"""Fixtures for adapter_submission_contract_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.adapter_submission_contract_v1 import (
    AdapterSubmissionInputs,
    default_adapter_submission_request,
    produce_adapter_submission_contract_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
    verify_trading_core_decision_attestation_bundle,
)
from tests.meta.runtime_state_reconciliation_v1_fixtures import (
    produce_runtime_state_reconciliation_fixture,
)
from tests.meta.trading_core_decision_attestation_v1_fixtures import (
    produce_trading_core_decision_attestation_fixture,
)


@dataclass(frozen=True)
class AdapterSubmissionContractFixtureBundle:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    trading_core_decision_attestation_bundle_dir: Path
    adapter_submission_contract_bundle_dir: Path | None = None


def produce_adapter_submission_contract_fixture(
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
    reconciliation_name: str = "runtime_state_reconciliation_for_adapter_submission",
    attestation_name: str = "trading_core_decision_attestation_for_adapter_submission",
    adapter_submission_name: str = "adapter_submission_contract",
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    client_order_id: str = "generic-futures-client-order-001",
    correlation_id: str = "offline-adapter-submission-correlation-001",
) -> AdapterSubmissionContractFixtureBundle:
    attestation_fixture = produce_trading_core_decision_attestation_fixture(
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
        idempotency_name="order_intent_idempotency_for_adapter_submission",
        attestation_name=attestation_name,
        client_order_id=client_order_id,
        instrument_type=instrument_type,
        instrument=instrument,
        correlation_id=correlation_id,
    )
    assert attestation_fixture.order_intent_idempotency_bundle_dir is not None
    assert attestation_fixture.trading_core_decision_attestation_bundle_dir is not None

    reconciliation_fixture = produce_runtime_state_reconciliation_fixture(
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
        reconciliation_name=reconciliation_name,
        instrument_type=instrument_type,
        instrument=instrument,
        correlation_id=correlation_id,
    )
    assert reconciliation_fixture.runtime_state_reconciliation_bundle_dir is not None

    idempotency = verify_order_intent_idempotency_bundle(
        attestation_fixture.order_intent_idempotency_bundle_dir
    )
    reconciliation = verify_runtime_state_reconciliation_bundle(
        reconciliation_fixture.runtime_state_reconciliation_bundle_dir
    )
    attestation = verify_trading_core_decision_attestation_bundle(
        attestation_fixture.trading_core_decision_attestation_bundle_dir
    )
    request = default_adapter_submission_request(
        idempotency=idempotency,
        reconciliation=reconciliation,
        attestation=attestation,
    )

    adapter_dir: Path | None = None
    if produce_output:
        adapter_dir = durable_root / adapter_submission_name
        produce_adapter_submission_contract_v1(
            inputs=AdapterSubmissionInputs(
                runtime_state_reconciliation_bundle_dir=(
                    reconciliation_fixture.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=(
                    attestation_fixture.order_intent_idempotency_bundle_dir
                ),
                trading_core_decision_attestation_bundle_dir=(
                    attestation_fixture.trading_core_decision_attestation_bundle_dir
                ),
                request=request,
            ),
            output_dir=adapter_dir,
        )

    return AdapterSubmissionContractFixtureBundle(
        runtime_state_reconciliation_bundle_dir=(
            reconciliation_fixture.runtime_state_reconciliation_bundle_dir
        ),
        order_intent_idempotency_bundle_dir=(
            attestation_fixture.order_intent_idempotency_bundle_dir
        ),
        trading_core_decision_attestation_bundle_dir=(
            attestation_fixture.trading_core_decision_attestation_bundle_dir
        ),
        adapter_submission_contract_bundle_dir=adapter_dir,
    )
