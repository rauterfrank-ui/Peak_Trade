"""Fixtures for unknown_execution_outcome_recovery_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.unknown_execution_outcome_recovery_v1 import (
    UnknownExecutionRecoveryInputs,
    default_unknown_execution_recovery_request,
    produce_unknown_execution_outcome_recovery_v1,
    verify_order_intent_idempotency_bundle,
    verify_runtime_state_reconciliation_bundle,
)
from tests.meta.order_intent_idempotency_v1_fixtures import (
    produce_order_intent_idempotency_fixture,
)
from tests.meta.runtime_state_reconciliation_v1_fixtures import (
    produce_runtime_state_reconciliation_fixture,
)


@dataclass(frozen=True)
class UnknownExecutionOutcomeRecoveryFixtureBundle:
    runtime_state_reconciliation_bundle_dir: Path
    order_intent_idempotency_bundle_dir: Path
    unknown_execution_outcome_recovery_bundle_dir: Path | None = None


def produce_unknown_execution_outcome_recovery_fixture(
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
    reconciliation_name: str = "runtime_state_reconciliation_for_unknown_outcome",
    idempotency_name: str = "order_intent_idempotency_for_unknown_outcome",
    recovery_name: str = "unknown_execution_outcome_recovery",
    recovery_classification: str = "FILLED",
    transport_outcome: str = "UNKNOWN_OUTCOME",
    instrument_type: str = "FUTURES",
    instrument: str = "GENERIC-FUTURES-PERP-001",
    client_order_id: str = "generic-futures-client-order-001",
    correlation_id: str = "offline-unknown-outcome-recovery-correlation-001",
    margin_snapshot_required: bool = False,
) -> UnknownExecutionOutcomeRecoveryFixtureBundle:
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
    )
    assert reconciliation_fixture.runtime_state_reconciliation_bundle_dir is not None

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
        idempotency_name=idempotency_name,
        client_order_id=client_order_id,
        instrument_type=instrument_type,
        instrument=instrument,
    )
    assert idempotency_fixture.order_intent_idempotency_bundle_dir is not None

    reconciliation = verify_runtime_state_reconciliation_bundle(
        reconciliation_fixture.runtime_state_reconciliation_bundle_dir
    )
    idempotency = verify_order_intent_idempotency_bundle(
        idempotency_fixture.order_intent_idempotency_bundle_dir
    )
    request = default_unknown_execution_recovery_request(
        reconciliation=reconciliation,
        idempotency=idempotency,
        recovery_classification=recovery_classification,
        transport_outcome=transport_outcome,
        instrument_type=instrument_type,
        correlation_id=correlation_id,
        margin_snapshot_required=margin_snapshot_required,
    )

    recovery_dir: Path | None = None
    if produce_output:
        recovery_dir = durable_root / recovery_name
        produce_unknown_execution_outcome_recovery_v1(
            inputs=UnknownExecutionRecoveryInputs(
                runtime_state_reconciliation_bundle_dir=(
                    reconciliation_fixture.runtime_state_reconciliation_bundle_dir
                ),
                order_intent_idempotency_bundle_dir=(
                    idempotency_fixture.order_intent_idempotency_bundle_dir
                ),
                recovery_request=request,
            ),
            output_dir=recovery_dir,
        )

    return UnknownExecutionOutcomeRecoveryFixtureBundle(
        runtime_state_reconciliation_bundle_dir=(
            reconciliation_fixture.runtime_state_reconciliation_bundle_dir
        ),
        order_intent_idempotency_bundle_dir=idempotency_fixture.order_intent_idempotency_bundle_dir,
        unknown_execution_outcome_recovery_bundle_dir=recovery_dir,
    )
