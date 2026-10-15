"""G004 offline regression: persisted post-attempt reconciliation disposition."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from unittest import mock

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    persist_enter_post_lifecycle_correlation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persisted_reconciliation_disposition_v1 import (
    PersistedReconciliationDispositionError,
    load_persisted_reconciliation_disposition_v1,
    lookup_post_attempt_reconciliation_disposition_v1,
    persist_post_attempt_reconciliation_disposition_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    identity_from_full_core_binding_v1,
    run_full_core_offline_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
    build_offline_exchange_reconciliation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_CONFIRMED_PARTIALLY_FILLED,
    OUTCOME_HALTED_UNRESOLVED,
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    FullCorePostSubmitLifecycleReconciliationJoinError,
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_capital_guard_atomic_one_shot_v1 import (
    FullCoreAuthorizationBindingV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreTradeOrderPostResultV1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import (
    CL,
    INST,
    _binding,
    _order_row,
)

ORD = "ord-g004-1"
SUBMIT_ATTEMPT = "submit-attempt-g004-1"
LANE = "acct-shadow-1"


def _binding_for_envelope(envelope) -> FullCoreAuthorizationBindingV1:
    """Align authorization binding with envelope identity (BU01/G004 contract)."""
    base = _binding()
    return replace(
        base,
        clordid=envelope.client_order_id,
        envelope_digest=envelope.envelope_digest,
    )


def _seed_correlation(tmp_path: Path, binding, envelope) -> None:
    atomic = tmp_path / "full_core_enter_post_guard_atomic_v1"
    persist_enter_post_lifecycle_correlation_v1(
        store_root=tmp_path,
        envelope=envelope,
        authorization_binding=binding,
        pretrade_decision_id="pretrade-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        atomic_state_dir=atomic,
    )


def _ack_post_result(*, clordid: str) -> FullCoreTradeOrderPostResultV1:
    return FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        http_status=200,
        payload={
            "code": "0",
            "data": [{"clOrdId": clordid, "ordId": ORD, "sCode": "0"}],
        },
        unknown_outcome=False,
        transport_class="INJECTED_TEST_DOUBLE",
        endpoint="/api/v5/trade/order",
    )


def _fixture_filled(*, clordid: str | None = None) -> OfflineExchangeFixtureV1:
    row = _order_row(state="filled", acc="10")
    row["ordId"] = ORD
    row["clOrdId"] = clordid or CL
    return OfflineExchangeFixtureV1(order_history={"data": [row]})


def _identity(binding, *, exchange_ord_id: str | None = ORD):
    return identity_from_full_core_binding_v1(
        binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        exchange_ord_id=exchange_ord_id,
    )


def test_valid_attempt_to_recon_binding_and_restart_lookup(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    fixture = _fixture_filled(clordid=sent)
    joined = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=fixture,
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    assert joined.reconciliation.decision.outcome == OUTCOME_CONFIRMED_FILLED
    loaded = lookup_post_attempt_reconciliation_disposition_v1(
        store_root=tmp_path,
        envelope=envelope,
        binding=binding,
        submit_attempt_id=SUBMIT_ATTEMPT,
        lane_id=LANE,
    )
    assert loaded["reconciliation_outcome"] == OUTCOME_CONFIRMED_FILLED
    assert loaded["local_submit_outcome"] == LocalSubmitOutcome.TRANSPORT_ACK.value
    assert loaded["typed_post_submit_outcome"] == "ACKNOWLEDGED"
    assert loaded["ack_is_not_fill"] is True


def test_duplicate_same_result_idempotent(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    kwargs = dict(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=_fixture_filled(clordid=sent),
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(**kwargs)
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(**kwargs)
    assert load_persisted_reconciliation_disposition_v1(store_root=tmp_path) is not None


def test_duplicate_conflicting_result_rejected(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    identity = _identity(binding)
    recon_a = run_full_core_offline_exchange_reconciliation_v1(
        identity=identity,
        binding=binding,
        fixture=_fixture_filled(clordid=sent),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    persist_post_attempt_reconciliation_disposition_v1(
        store_root=tmp_path,
        envelope=envelope,
        binding=binding,
        identity=identity,
        decision=recon_a.decision,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        post_submit_join=post_join,
        submit_attempt_id=SUBMIT_ATTEMPT,
        lane_id=LANE,
    )
    partial_row = _order_row(state="partially_filled", acc="4")
    partial_row["ordId"] = ORD
    partial_row["clOrdId"] = sent
    partial_fixture = OfflineExchangeFixtureV1(order_history={"data": [partial_row]})
    recon_b = run_full_core_offline_exchange_reconciliation_v1(
        identity=identity,
        binding=binding,
        fixture=partial_fixture,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    with pytest.raises(PersistedReconciliationDispositionError, match="CONFLICTING"):
        persist_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=binding,
            identity=identity,
            decision=recon_b.decision,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
            post_submit_join=post_join,
            submit_attempt_id=SUBMIT_ATTEMPT,
            lane_id=LANE,
        )


def test_unknown_remains_unknown(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=sent,
        transport_error="TimeoutError",
    )
    fixture = OfflineExchangeFixtureV1()
    joined = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=fixture,
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    assert joined.reconciliation.decision.outcome == OUTCOME_HALTED_UNRESOLVED
    loaded = lookup_post_attempt_reconciliation_disposition_v1(
        store_root=tmp_path,
        envelope=envelope,
        binding=binding,
        submit_attempt_id=SUBMIT_ATTEMPT,
        lane_id=LANE,
    )
    assert loaded["reconciliation_outcome"] == OUTCOME_HALTED_UNRESOLVED
    assert loaded["typed_post_submit_outcome"] == "UNKNOWN"


def test_partial_not_interpreted_as_full() -> None:
    binding = _binding()
    identity = _identity(binding)
    partial_row = _order_row(state="partially_filled", acc="4")
    partial_row["ordId"] = ORD
    snapshot = build_offline_exchange_reconciliation_snapshot_v1(
        identity=identity,
        fixture=OfflineExchangeFixtureV1(order_history={"data": [partial_row]}),
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    assert decision.outcome == OUTCOME_CONFIRMED_PARTIALLY_FILLED
    assert decision.outcome != OUTCOME_CONFIRMED_FILLED


def test_persistence_failure_fail_closed(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    identity = _identity(binding)
    recon = run_full_core_offline_exchange_reconciliation_v1(
        identity=identity,
        binding=binding,
        fixture=_fixture_filled(clordid=sent),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    with mock.patch(
        "src.ops.full_core_live_path_composition_root_v1."
        "current_productive_persisted_reconciliation_disposition_v1.os.replace",
        side_effect=OSError("disk"),
    ):
        with pytest.raises(PersistedReconciliationDispositionError, match="PERSISTENCE_FAILURE"):
            persist_post_attempt_reconciliation_disposition_v1(
                store_root=tmp_path,
                envelope=envelope,
                binding=binding,
                identity=identity,
                decision=recon.decision,
                local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
                post_submit_join=post_join,
                submit_attempt_id=SUBMIT_ATTEMPT,
                lane_id=LANE,
            )
    assert load_persisted_reconciliation_disposition_v1(store_root=tmp_path) is None


def test_missing_correlation_fail_closed(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    with pytest.raises(
        FullCorePostSubmitLifecycleReconciliationJoinError,
        match="MISSING_LIFECYCLE_CORRELATION",
    ):
        run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            post_submit_join=post_join,
            binding=binding,
            decision_outcome="ENTER",
            venue_plan_identity="vp-g004",
            envelope_identity="env-g004",
            submit_attempt_id=SUBMIT_ATTEMPT,
            local_durable_state_version="v1",
            offline_fixture=_fixture_filled(clordid=sent),
            post_durable_store_root=tmp_path,
            persist_reconciliation_disposition=True,
            post_attempt_envelope=envelope,
            reconciliation_disposition_lane_id=LANE,
        )


def test_wrong_lane_account_instrument_rejected(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=_fixture_filled(clordid=sent),
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    with pytest.raises(PersistedReconciliationDispositionError, match="WRONG_LANE"):
        lookup_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=binding,
            submit_attempt_id=SUBMIT_ATTEMPT,
            lane_id="other-lane",
        )
    wrong_acct = replace(binding, account_scope="other-acct")
    with pytest.raises(PersistedReconciliationDispositionError, match="WRONG_ACCOUNT"):
        lookup_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=wrong_acct,
            submit_attempt_id=SUBMIT_ATTEMPT,
            lane_id=LANE,
        )
    wrong_inst = replace(binding, native_id="BTC-USDT-SWAP")
    with pytest.raises(PersistedReconciliationDispositionError, match="WRONG_INSTRUMENT"):
        lookup_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=wrong_inst,
            submit_attempt_id=SUBMIT_ATTEMPT,
            lane_id=LANE,
        )


def test_no_blind_post_retry_semantics_on_join() -> None:
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=None,
        sent_clordid=CL,
        transport_error="TimeoutError",
    )
    assert post_join.resubmit_allowed is False
    assert post_join.blind_retry_forbidden is True


def test_bu01_root_binding_reused_in_correlation(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    atomic = tmp_path / "full_core_enter_post_guard_atomic_v1"
    persist_enter_post_lifecycle_correlation_v1(
        store_root=tmp_path,
        envelope=envelope,
        authorization_binding=binding,
        pretrade_decision_id="pretrade-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        atomic_state_dir=atomic,
    )
    correlation = json.loads(
        (
            tmp_path / "full_core_mandatory_new_risk_enter_post_lifecycle_correlation_v1.json"
        ).read_text()
    )
    assert correlation["envelope_digest"] == envelope.envelope_digest
    assert correlation["clordid"] == envelope.client_order_id


def _persist_once(tmp_path: Path, *, binding, envelope, post_join, identity) -> None:
    sent = envelope.client_order_id
    recon = run_full_core_offline_exchange_reconciliation_v1(
        identity=identity,
        binding=binding,
        fixture=_fixture_filled(clordid=sent),
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
    )
    persist_post_attempt_reconciliation_disposition_v1(
        store_root=tmp_path,
        envelope=envelope,
        binding=binding,
        identity=identity,
        decision=recon.decision,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
        post_submit_join=post_join,
        submit_attempt_id=SUBMIT_ATTEMPT,
        lane_id=LANE,
    )


def test_wrong_client_order_id_rejected_on_persist(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    bad_binding = replace(binding, clordid="other-clordid-not-envelope")
    identity = _identity(bad_binding)
    with pytest.raises(PersistedReconciliationDispositionError, match="BINDING_CLORDID_ENVELOPE"):
        _persist_once(
            tmp_path,
            binding=bad_binding,
            envelope=envelope,
            post_join=post_join,
            identity=identity,
        )


def test_wrong_native_order_id_rejected_on_persist(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    identity = _identity(binding, exchange_ord_id="wrong-native-ord-id")
    with pytest.raises(PersistedReconciliationDispositionError, match="IDENTITY_VENUE_ORD_ID"):
        _persist_once(
            tmp_path,
            binding=binding,
            envelope=envelope,
            post_join=post_join,
            identity=identity,
        )


def test_wrong_submit_attempt_id_rejected_on_persist(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    identity = _identity(binding)
    with pytest.raises(
        PersistedReconciliationDispositionError,
        match="SUBMIT_ATTEMPT_ID_CORRELATION_MISMATCH",
    ):
        persist_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=binding,
            identity=identity,
            decision=run_full_core_offline_exchange_reconciliation_v1(
                identity=identity,
                binding=binding,
                fixture=_fixture_filled(clordid=sent),
                local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
            ).decision,
            local_submit_outcome=LocalSubmitOutcome.TRANSPORT_ACK,
            post_submit_join=post_join,
            submit_attempt_id="other-submit-attempt",
            lane_id=LANE,
        )


def test_wrong_envelope_digest_on_binding_rejected(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    bad_binding = replace(binding, envelope_digest="deadbeef" * 8)
    identity = _identity(bad_binding)
    with pytest.raises(PersistedReconciliationDispositionError, match="BINDING_ENVELOPE_DIGEST"):
        _persist_once(
            tmp_path,
            binding=bad_binding,
            envelope=envelope,
            post_join=post_join,
            identity=identity,
        )


def test_wrong_clordid_rejected_on_restart_lookup(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=_fixture_filled(clordid=sent),
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    with pytest.raises(PersistedReconciliationDispositionError, match="BINDING_CLORDID_ENVELOPE"):
        lookup_post_attempt_reconciliation_disposition_v1(
            store_root=tmp_path,
            envelope=envelope,
            binding=replace(binding, clordid="alien-clordid-0001"),
            submit_attempt_id=SUBMIT_ATTEMPT,
            lane_id=LANE,
        )


def test_record_clordid_authoritative_from_envelope(tmp_path: Path) -> None:
    envelope = _new_risk_envelope()
    binding = _binding_for_envelope(envelope)
    sent = envelope.client_order_id
    _seed_correlation(tmp_path, binding, envelope)
    post_join = join_full_core_post_result_to_lifecycle_v1(
        result=_ack_post_result(clordid=sent),
        sent_clordid=sent,
    )
    run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=post_join,
        binding=binding,
        decision_outcome="ENTER",
        venue_plan_identity="vp-g004",
        envelope_identity="env-g004",
        submit_attempt_id=SUBMIT_ATTEMPT,
        local_durable_state_version="v1",
        offline_fixture=_fixture_filled(clordid=sent),
        post_durable_store_root=tmp_path,
        persist_reconciliation_disposition=True,
        post_attempt_envelope=envelope,
        reconciliation_disposition_lane_id=LANE,
    )
    record = load_persisted_reconciliation_disposition_v1(store_root=tmp_path)
    assert record is not None
    assert record["clordid"] == envelope.client_order_id
    assert record.get("venue_ord_id") == ORD
