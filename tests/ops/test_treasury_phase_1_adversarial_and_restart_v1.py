"""Treasury Phase-1 adversarial and restart contract tests. Offline only."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.treasury_phase_1_offline_contracts_v1.capital_boundary_v1 import (
    treasury_lifecycle_cannot_mint_risk_admissible_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.engine_v1 import (
    apply_treasury_lifecycle_transition_v1,
    classify_concurrent_treasury_intents_v1,
    classify_treasury_command_v1,
    evaluate_remote_mutation_eligibility_v1,
    record_treasury_intent_v1,
    restore_treasury_records_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import (
    TreasuryIdempotencyError,
    TreasuryPhase1ContractError,
)
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    TreasuryCommandClassificationV1,
    TreasuryLifecycleStateV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.persistence_v1 import (
    FileBackedTreasuryIntentStoreV1,
    InMemoryTreasuryIntentStoreV1,
    recover_record_without_second_effect_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.serialization_v1 import (
    round_trip_intent_record_v1,
)
from tests.ops.test_treasury_phase_1_offline_contracts_v1 import (
    _draft,
    _observation,
    _transition,
)


def _attempt_unknown(store, record):
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        ),
    )
    return apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value,
        ),
    )


def test_at03_timeout_after_possible_remote_acceptance_is_unknown_not_retry() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    unknown = _attempt_unknown(store, record)
    assert unknown.lifecycle_state == TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value
    assert unknown.reconciliation_status == "UNKNOWN_NOT_FAILED"
    eligibility = evaluate_remote_mutation_eligibility_v1(unknown)
    assert eligibility.eligible is False
    assert "OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY" in eligibility.reason_codes
    decision = classify_treasury_command_v1(store, _draft())
    assert (
        decision.classification
        == TreasuryCommandClassificationV1.UNSAFE_RETRY_UNKNOWN_OUTCOME.value
    )
    with pytest.raises(TreasuryIdempotencyError, match="OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY"):
        record_treasury_intent_v1(store, _draft())


def test_at04_remote_success_missing_local_terminal_recovers_one_effect(tmp_path: Path) -> None:
    path = tmp_path / "treasury.jsonl"
    store = FileBackedTreasuryIntentStoreV1(path)
    record = record_treasury_intent_v1(store, _draft())
    attempted = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        ),
    )
    success = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            attempted.intent_id,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            venue_operation_ref="venue-op-1",
        ),
    )
    recovered = recover_record_without_second_effect_v1(
        FileBackedTreasuryIntentStoreV1(path), success
    )
    assert recovered.intent_id == success.intent_id
    restored_store = FileBackedTreasuryIntentStoreV1(path)
    restored = restore_treasury_records_v1(restored_store)
    assert len(restored) == 1
    terminal = apply_treasury_lifecycle_transition_v1(
        restored_store,
        _transition(
            recovered.intent_id,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
        ),
    )
    again = recover_record_without_second_effect_v1(restored_store, terminal)
    assert again.sequence == terminal.sequence
    assert again.lifecycle_state == TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value


def test_at05_duplicate_replay_after_restart_never_second_effect(tmp_path: Path) -> None:
    path = tmp_path / "treasury.jsonl"
    store = FileBackedTreasuryIntentStoreV1(path)
    record_treasury_intent_v1(store, _draft())
    restarted = FileBackedTreasuryIntentStoreV1(path)
    restored = restore_treasury_records_v1(restarted)
    assert restored[0].lifecycle_state == TreasuryLifecycleStateV1.INTENT_RECORDED.value
    replayed = record_treasury_intent_v1(restarted, _draft())
    assert replayed.intent_id == restored[0].intent_id
    assert len(restarted.list_all()) == 1


def test_at12_restart_with_pending_unknown_survives(tmp_path: Path) -> None:
    path = tmp_path / "treasury.jsonl"
    store = FileBackedTreasuryIntentStoreV1(path)
    record = record_treasury_intent_v1(store, _draft())
    _attempt_unknown(store, record)
    restarted = FileBackedTreasuryIntentStoreV1(path)
    restored = restore_treasury_records_v1(restarted)
    assert restored[0].lifecycle_state == TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value
    assert restored[0].remote_attempted is True
    with pytest.raises(TreasuryIdempotencyError, match="OUTCOME_UNKNOWN_NOT_SAFE_TO_RETRY"):
        record_treasury_intent_v1(restarted, _draft())


def test_case_a_persisted_never_attempted(tmp_path: Path) -> None:
    path = tmp_path / "treasury.jsonl"
    store = FileBackedTreasuryIntentStoreV1(path)
    record_treasury_intent_v1(store, _draft())
    restarted = FileBackedTreasuryIntentStoreV1(path)
    restored = restore_treasury_records_v1(restarted)[0]
    assert restored.lifecycle_state == TreasuryLifecycleStateV1.INTENT_RECORDED.value
    assert restored.remote_attempted is False
    eligibility = evaluate_remote_mutation_eligibility_v1(restored)
    assert eligibility.durable_intent_present is True
    assert eligibility.network_send_permitted is False


def test_at14_decimal_precision_exact_no_rounding() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    tiny = record_treasury_intent_v1(
        store, _draft(intent_id="tintent-tiny", amount_raw="0.00000001")
    )
    large = record_treasury_intent_v1(
        store,
        _draft(
            intent_id="tintent-large",
            amount_raw="1000000000.12345678",
            source_scope="funding-other",
        ),
    )
    assert tiny.amount_canonical == "0.00000001"
    assert large.amount_canonical == "1000000000.12345678"
    assert Decimal(tiny.amount_canonical) == Decimal("0.00000001")
    assert Decimal(large.amount_canonical) == Decimal("1000000000.12345678")
    assert round_trip_intent_record_v1(tiny).amount_canonical == tiny.amount_canonical
    assert round_trip_intent_record_v1(large).amount_canonical == large.amount_canonical


def test_at15_concurrent_mutation_intents_require_serialization() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record_treasury_intent_v1(store, _draft())
    decision = classify_concurrent_treasury_intents_v1(
        store, _draft(intent_id="tintent-withdrawal-002")
    )
    assert (
        decision.classification
        == TreasuryCommandClassificationV1.CONFLICT_REQUIRES_SERIALIZATION.value
    )
    with pytest.raises(TreasuryPhase1ContractError, match="CONCURRENT_MUTATION"):
        record_treasury_intent_v1(store, _draft(intent_id="tintent-withdrawal-002"))
    obs = record_treasury_intent_v1(store, _observation())
    assert obs.operation_kind == "DEPOSIT_OBSERVATION"


def test_observed_and_reconciled_capital_do_not_mint_risk_admissible() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    observed = record_treasury_intent_v1(store, _observation())
    assert treasury_lifecycle_cannot_mint_risk_admissible_v1(observed) == "OBSERVED_CAPITAL"
    reconciled = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            observed.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
        ),
    )
    assert treasury_lifecycle_cannot_mint_risk_admissible_v1(reconciled) == "RECONCILED_CAPITAL"
    assert reconciled.risk_admissible is False
    mutation = record_treasury_intent_v1(store, _draft(intent_id="tintent-wd-risk"))
    attempted = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            mutation.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        ),
    )
    success = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            attempted.intent_id,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
        ),
    )
    assert treasury_lifecycle_cannot_mint_risk_admissible_v1(success) == "OBSERVED_CAPITAL"
    assert success.risk_admissible is False


def test_fixture_and_historical_authority_claims_denied() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    with pytest.raises(TreasuryPhase1ContractError, match="FIXTURE_PRODUCTIVE_AUTHORITY"):
        record_treasury_intent_v1(
            store, _draft(intent_id="tintent-fixture", claimed_productive_authority=True)
        )
    with pytest.raises(TreasuryPhase1ContractError, match="HISTORICAL_EVIDENCE"):
        record_treasury_intent_v1(
            store, _draft(intent_id="tintent-hist", claimed_historical_authority=True)
        )


def test_network_gaps_are_not_claimed_closed() -> None:
    from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
        CURRENT_END_TO_END_TREASURY_GATE,
        PRODUCTIVE_DEPOSIT_PATH,
        PRODUCTIVE_INTERNAL_TRANSFER_PATH,
        PRODUCTIVE_WITHDRAWAL_PATH,
        TRANSFER_RECONCILIATION,
        TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN,
        TREASURY_PHASE_2_STATUS,
        VENUE_PERMISSION_GET_PERFORMED,
    )

    assert PRODUCTIVE_DEPOSIT_PATH is False
    assert PRODUCTIVE_WITHDRAWAL_PATH is False
    assert PRODUCTIVE_INTERNAL_TRANSFER_PATH is False
    assert TRANSFER_RECONCILIATION is False
    assert CURRENT_END_TO_END_TREASURY_GATE is False
    assert TREASURY_COMPLETE_PRODUCTIVE_SUBSYSTEM_PROVEN is False
    assert TREASURY_PHASE_2_STATUS == "NOT_STARTED"
    assert VENUE_PERMISSION_GET_PERFORMED is False
