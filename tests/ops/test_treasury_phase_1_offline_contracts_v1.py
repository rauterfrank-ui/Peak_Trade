"""Treasury Phase-1 offline contract tests. No network. No mutation."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.treasury_phase_1_offline_contracts_v1.authority_v1 import phase_1_no_authority_proof_v1
from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    SCHEMA_VERSION,
    VENUE_IDEMPOTENCY_GUARANTEE,
    WIRE_SEND_PERMITTED,
)
from src.ops.treasury_phase_1_offline_contracts_v1.engine_v1 import (
    apply_treasury_lifecycle_transition_v1,
    classify_concurrent_treasury_intents_v1,
    classify_distinct_same_parameters_v1,
    classify_treasury_command_v1,
    evaluate_remote_mutation_eligibility_v1,
    record_treasury_intent_v1,
    restore_treasury_records_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import (
    TreasuryIdempotencyError,
    TreasuryLifecycleError,
    TreasuryPhase1ContractError,
    TreasuryPersistenceError,
    TreasurySecretHygieneError,
)
from src.ops.treasury_phase_1_offline_contracts_v1.identity_v1 import request_fingerprint_v1
from src.ops.treasury_phase_1_offline_contracts_v1.lifecycle_v1 import allowed_transitions_v1
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import (
    TreasuryCommandClassificationV1,
    TreasuryDestinationRefV1,
    TreasuryIntentDraftV1,
    TreasuryLifecycleStateV1,
    TreasuryLifecycleTransitionV1,
    TreasuryOperationKindV1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.persistence_v1 import (
    FileBackedTreasuryIntentStoreV1,
    InMemoryTreasuryIntentStoreV1,
    restore_store_from_bytes_v1,
)
from src.ops.treasury_phase_1_offline_contracts_v1.provenance_v1 import assert_no_secret_fields_v1
from src.ops.treasury_phase_1_offline_contracts_v1.serialization_v1 import (
    deserialize_intent_record_v1,
    round_trip_intent_record_v1,
    serialize_intent_record_v1,
)

_TS = "2026-09-05T20:00:00Z"
_DEST = "d" * 16


def _dest(**overrides) -> TreasuryDestinationRefV1:
    payload = {
        "ref_kind": "DESTINATION_FINGERPRINT",
        "fingerprint": _DEST,
        "scope_id": "",
        "network_id": "ERC20",
        "confirmation_fingerprint": _DEST,
    }
    payload.update(overrides)
    return TreasuryDestinationRefV1(**payload)


def _draft(**overrides) -> TreasuryIntentDraftV1:
    payload = {
        "intent_id": "tintent-withdrawal-001",
        "operation_kind": TreasuryOperationKindV1.WITHDRAWAL.value,
        "asset_id": "USDT",
        "amount_raw": "10.5",
        "denomination": "USDT",
        "source_scope": "funding-main",
        "destination": _dest(),
        "created_at": _TS,
        "policy_version": "policy-v1",
        "authorization_class": "NONE",
        "authorization_evidence_ref": "",
        "evidence_refs": ("ev-1",),
        "venue_operation_ref": "",
        "local_observation_at": _TS,
        "venue_source_at": "",
        "claimed_productive_authority": False,
        "claimed_historical_authority": False,
    }
    payload.update(overrides)
    return TreasuryIntentDraftV1(**payload)


def _observation(**overrides) -> TreasuryIntentDraftV1:
    payload = {
        "intent_id": "tintent-deposit-obs-001",
        "operation_kind": TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value,
        "destination": TreasuryDestinationRefV1(
            ref_kind="NONE",
            fingerprint="",
            scope_id="",
            network_id="",
            confirmation_fingerprint="",
        ),
        "amount_raw": "25.0",
    }
    payload.update(overrides)
    return _draft(**payload)


def _transition(intent_id: str, frm: str, to: str, **overrides) -> TreasuryLifecycleTransitionV1:
    payload = {
        "intent_id": intent_id,
        "from_state": frm,
        "to_state": to,
        "local_observation_at": "2026-09-05T20:01:00Z",
        "venue_source_at": "",
        "venue_operation_ref": "",
        "evidence_refs": (),
        "reason_code": "",
        "confirmation_fingerprint": "",
    }
    payload.update(overrides)
    return TreasuryLifecycleTransitionV1(**payload)


def test_no_authority_and_standing_gates() -> None:
    proof = phase_1_no_authority_proof_v1()
    assert all(value is False for value in proof.values())
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert VENUE_IDEMPOTENCY_GUARANTEE == "NOT_PROVEN"
    assert SCHEMA_VERSION == "treasury_phase_1_offline_contract.v1"


def test_record_intent_is_durable_before_any_remote() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    assert record.lifecycle_state == TreasuryLifecycleStateV1.INTENT_RECORDED.value
    assert record.durable is True
    assert record.remote_attempted is False
    assert record.mutation_authorized is False
    assert record.risk_admissible is False
    eligibility = evaluate_remote_mutation_eligibility_v1(record)
    assert eligibility.eligible is False
    assert eligibility.durable_intent_present is True
    assert eligibility.network_send_permitted is False


def test_deposit_observation_is_not_mutation_and_not_address_retrieval() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _observation())
    assert record.operation_kind == TreasuryOperationKindV1.DEPOSIT_OBSERVATION.value
    with pytest.raises(TreasuryLifecycleError, match="NON_MUTATION_CANNOT_REMOTE_ATTEMPT"):
        apply_treasury_lifecycle_transition_v1(
            store,
            _transition(
                record.intent_id,
                TreasuryLifecycleStateV1.INTENT_RECORDED.value,
                TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            ),
        )
    address = _draft(
        intent_id="tintent-deposit-addr-001",
        operation_kind=TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value,
        amount_raw="",
        destination=_dest(ref_kind="DESTINATION_FINGERPRINT"),
    )
    addr = record_treasury_intent_v1(store, address)
    assert addr.operation_kind == TreasuryOperationKindV1.DEPOSIT_ADDRESS_RETRIEVAL.value
    assert addr.amount_canonical == ""


def test_duplicate_command_is_deterministic() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    first = record_treasury_intent_v1(store, _draft())
    second = record_treasury_intent_v1(store, _draft())
    assert first.intent_id == second.intent_id
    assert first.request_fingerprint == second.request_fingerprint
    decision = classify_treasury_command_v1(store, _draft())
    assert decision.classification == TreasuryCommandClassificationV1.DUPLICATE_SAME_INTENT.value


def test_same_intent_changed_amount_or_destination_or_network_denied() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record_treasury_intent_v1(store, _draft())
    with pytest.raises(TreasuryIdempotencyError, match="CHANGED_ECONOMIC_PARAMETERS"):
        record_treasury_intent_v1(store, _draft(amount_raw="11.0"))
    with pytest.raises(TreasuryIdempotencyError, match="CHANGED_ECONOMIC_PARAMETERS"):
        record_treasury_intent_v1(
            store,
            _draft(destination=_dest(fingerprint="e" * 16, confirmation_fingerprint="e" * 16)),
        )
    with pytest.raises(TreasuryIdempotencyError, match="CHANGED_ECONOMIC_PARAMETERS"):
        record_treasury_intent_v1(store, _draft(destination=_dest(network_id="TRC20")))


def test_different_intent_same_parameters_not_automatically_same_operation() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    first = record_treasury_intent_v1(store, _draft())
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            first.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        ),
    )
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            first.intent_id,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_FAILURE.value,
        ),
    )
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            first.intent_id,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_FAILURE.value,
            TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
        ),
    )
    other = _draft(intent_id="tintent-withdrawal-002")
    decision = classify_distinct_same_parameters_v1(store, other)
    assert (
        decision.classification
        == TreasuryCommandClassificationV1.DISTINCT_INTENT_SAME_PARAMETERS.value
    )
    second = record_treasury_intent_v1(store, other)
    assert second.intent_id != first.intent_id
    assert second.request_fingerprint == first.request_fingerprint


def test_fingerprint_stable_across_round_trip() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    restored = round_trip_intent_record_v1(record)
    assert restored.request_fingerprint == record.request_fingerprint
    assert restored.evidence_hash == record.evidence_hash
    assert request_fingerprint_v1(_draft()) == record.request_fingerprint


def test_malformed_and_unknown_schema_and_unknown_enum() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    encoded = serialize_intent_record_v1(record)
    with pytest.raises(TreasuryPersistenceError, match="CORRUPTED_SERIALIZED_RECORD"):
        deserialize_intent_record_v1("{not-json")
    with pytest.raises(TreasuryPersistenceError, match="UNSUPPORTED_SCHEMA_VERSION"):
        deserialize_intent_record_v1(encoded.replace(SCHEMA_VERSION, "treasury.v0"))
    with pytest.raises(TreasuryPersistenceError, match="UNKNOWN_FIELDS"):
        deserialize_intent_record_v1(encoded[:-1] + ',"extra":"x"}')
    with pytest.raises(TreasuryPhase1ContractError, match="OPERATION_KIND_UNKNOWN"):
        record_treasury_intent_v1(
            store, _draft(intent_id="tintent-bad-kind", operation_kind="SWEEP")
        )
    with pytest.raises(TreasuryPhase1ContractError, match="LIFECYCLE_STATE_UNKNOWN"):
        apply_treasury_lifecycle_transition_v1(
            store,
            _transition(record.intent_id, record.lifecycle_state, "SUCCEEDED"),
        )


def test_zero_negative_nonfinite_mutation_amount_denied() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    with pytest.raises(TreasuryPhase1ContractError, match="MUTATION_AMOUNT_NOT_POSITIVE"):
        record_treasury_intent_v1(store, _draft(intent_id="tintent-zero", amount_raw="0"))
    with pytest.raises(TreasuryPhase1ContractError, match="MUTATION_AMOUNT_NOT_POSITIVE"):
        record_treasury_intent_v1(store, _draft(intent_id="tintent-neg", amount_raw="-1.0"))
    with pytest.raises(TreasuryPhase1ContractError, match="AMOUNT_NOT_FINITE"):
        record_treasury_intent_v1(store, _draft(intent_id="tintent-inf", amount_raw="Infinity"))
    with pytest.raises(TreasuryPhase1ContractError, match="AMOUNT_NOT_CANONICAL_FORM"):
        record_treasury_intent_v1(store, _draft(intent_id="tintent-sci", amount_raw="1e-8"))


def test_deposit_observation_may_omit_amount() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _observation(amount_raw=""))
    assert record.amount_canonical == ""


def test_secret_fields_cannot_enter_serialized_evidence() -> None:
    with pytest.raises(TreasurySecretHygieneError, match="SECRET_FIELD_DENIED"):
        assert_no_secret_fields_v1({"api_key": "ok-secret", "intent_id": "x"})
    with pytest.raises(TreasurySecretHygieneError, match="SECRET_FIELD_DENIED"):
        assert_no_secret_fields_v1({"Authorization": "Bearer abc", "nested": {"passphrase": "x"}})
    with pytest.raises(TreasurySecretHygieneError, match="SECRET_FIELD_DENIED"):
        assert_no_secret_fields_v1({"recovery_code": "abc", "signing_material": "k"})
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    text = serialize_intent_record_v1(record)
    for token in ("api_key", "secret", "passphrase", "Authorization", "private_key"):
        assert token not in text


def test_offline_fixture_round_trip_cannot_claim_productive_authority() -> None:
    fixture = (
        Path(__file__).resolve().parents[0]
        / "fixtures"
        / "treasury_phase_1_offline_contracts_v1"
        / "valid_withdrawal_intent.json"
    )
    record = deserialize_intent_record_v1(fixture.read_text(encoding="utf-8").strip())
    assert record.mutation_authorized is False
    assert record.risk_admissible is False
    assert round_trip_intent_record_v1(record).evidence_hash == record.evidence_hash
    store = InMemoryTreasuryIntentStoreV1()
    with pytest.raises(TreasuryPhase1ContractError, match="TIMESTAMP_NAIVE"):
        record_treasury_intent_v1(
            store, _draft(intent_id="tintent-naive", created_at="2026-09-05T20:00:00")
        )
    with pytest.raises(TreasuryPhase1ContractError, match="TIMESTAMP_NOT_UTC"):
        record_treasury_intent_v1(
            store, _draft(intent_id="tintent-offset", created_at="2026-09-05T20:00:00+02:00")
        )


def test_illegal_and_terminal_transitions() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    record = record_treasury_intent_v1(store, _draft())
    with pytest.raises(TreasuryLifecycleError, match="ILLEGAL_LIFECYCLE_TRANSITION"):
        apply_treasury_lifecycle_transition_v1(
            store,
            _transition(
                record.intent_id,
                TreasuryLifecycleStateV1.INTENT_RECORDED.value,
                TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            ),
        )
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.INTENT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
        ),
    )
    apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
        ),
    )
    success = apply_treasury_lifecycle_transition_v1(
        store,
        _transition(
            record.intent_id,
            TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
        ),
    )
    assert success.lifecycle_state == TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value
    with pytest.raises(TreasuryLifecycleError, match="ILLEGAL_LIFECYCLE_TRANSITION"):
        apply_treasury_lifecycle_transition_v1(
            store,
            _transition(
                record.intent_id,
                TreasuryLifecycleStateV1.ECONOMIC_EFFECT_RECONCILED.value,
                TreasuryLifecycleStateV1.REMOTE_TERMINAL_SUCCESS.value,
            ),
        )
    with pytest.raises(TreasuryIdempotencyError, match="TERMINAL_EFFECT_ALREADY_APPLIED"):
        record_treasury_intent_v1(store, _draft())
    allowed = allowed_transitions_v1()
    assert TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value in allowed
    assert (
        TreasuryLifecycleStateV1.REMOTE_ATTEMPT_RECORDED.value
        not in allowed[TreasuryLifecycleStateV1.OUTCOME_UNKNOWN.value]
    )


def test_destination_confirmation_mismatch_denied() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    with pytest.raises(TreasuryPhase1ContractError, match="DESTINATION_CONFIRMATION_MISMATCH"):
        record_treasury_intent_v1(
            store,
            _draft(
                intent_id="tintent-dest-mismatch",
                destination=_dest(confirmation_fingerprint="x" * 16),
            ),
        )


def test_asset_network_policy_mismatch_denied() -> None:
    store = InMemoryTreasuryIntentStoreV1()
    with pytest.raises(TreasuryPhase1ContractError, match="WITHDRAWAL_NETWORK_REQUIRED"):
        record_treasury_intent_v1(
            store,
            _draft(intent_id="tintent-net-missing", destination=_dest(network_id="")),
        )
    with pytest.raises(
        TreasuryPhase1ContractError, match="INTERNAL_TRANSFER_NETWORK_NOT_APPLICABLE"
    ):
        record_treasury_intent_v1(
            store,
            _draft(
                intent_id="tintent-transfer-net",
                operation_kind=TreasuryOperationKindV1.INTERNAL_TRANSFER.value,
                destination=TreasuryDestinationRefV1(
                    ref_kind="ACCOUNT_SCOPE",
                    fingerprint="",
                    scope_id="trading-main",
                    network_id="ERC20",
                    confirmation_fingerprint="",
                ),
            ),
        )
