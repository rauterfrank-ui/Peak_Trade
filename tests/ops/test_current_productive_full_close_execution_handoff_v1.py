"""Full-close composition → existing non-network send seam → reconciliation.

Permits and exchange responses here are explicit offline test fixtures.
These checks do not assert that a kill-switch exit may bypass send admission.
"""

from dataclasses import replace
from decimal import Decimal

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    PositionManagementExecutionHandoffV1,
    compose_position_management_full_close_intent_v1,
    validates_position_management_execution_handoff_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
    compute_final_order_envelope_digest_v1,
)
from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
    attempt_envelope_bound_external_effect_send_v1,
    FullCoreEnvelopeBoundSendSeamError,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from tests.ops.test_current_productive_position_management_quantity_handoff_v1 import (
    _case,
    _position,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
    _handle,
)
from tests.ops.test_full_core_exchange_reconciliation_v1 import _binding
from trading.master_v2.double_play_entry_exit_policy_v0 import PositionState, ReconciliationState
from trading.master_v2.replay_execution_safety_contract_v1 import ReplayExecutionSafetyV1


def _prepared(side="long", *, lane_id="LANE_1"):
    args = _case(side=side, action="exit", lane_id=lane_id)
    args["position"] = _position(args["identity"], side=side, quantity="1.2")
    replay = args["replay"]
    replay.evidence.replay_id = "offline-full-close"
    replay.evidence.reason_codes = ()
    replay.evidence.safety_boundary_ref = "offline-safety"
    replay.intermediate.composition_result = object()
    replay.intermediate.canonical_order_intent = None
    # Existing entry sizing is deliberately unavailable; a close uses its own owner.
    replay.intermediate.capital_risk_sizing_decision = None
    replay.intermediate.entry_exit_decision.position_state = PositionState.OPEN_PARTIAL
    replay.intermediate.entry_exit_decision.reconciliation_state = ReconciliationState.RECONCILED
    replay.replay_execution_safety = ReplayExecutionSafetyV1(
        entry_blocked=False,
        emergency_boundary_active=False,
        emergency_mode=None,
        flatten_only=False,
        reduce_only=False,
        cancel_only=False,
        reason_codes=(),
        source_refs=("safety:" + "ab" * 32,),
    )
    source = compose_position_management_full_close_intent_v1(**args)
    assert source.canonical_intent is not None
    return args, source


def _bind(args, source):
    return try_bind_current_productive_venue_plan_v1(
        replay=args["replay"],
        bound_instrument=_bound(),
        session_id="offline-close",
        run_id="abcdef123456",
        composed_epoch="2026-11-03T00:00:00Z",
        execution_mode="INTERNAL_SIMULATED_EXECUTION",
        full_close_handoff=source,
    )


def _envelope(plan, source):
    return bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="offline-close-admission",
        provenance_ref=source.canonical_intent.semantic_digest,
        creation_epoch="2026-11-03T00:00:00Z",
    )


@pytest.mark.parametrize("side", ["long", "short"])
@pytest.mark.parametrize(
    "state,remaining", [("live", "1.2"), ("partially_filled", "0.4"), ("filled", "0")]
)
def test_close_reaches_existing_send_and_observed_position_feedback(
    tmp_path, side, state, remaining
):
    args, source = _prepared(side)
    status, reasons, plan = _bind(args, source)
    assert status.value == "PASS", reasons
    envelope = _envelope(plan, source)
    assert envelope.side == ("sell" if side == "long" else "buy")
    assert envelope.quantity == "1.2" and envelope.reduce_only

    class AckTransport(FullCoreNonNetworkingTestPostTransportV1):
        def post_trade_order(self, **kwargs):
            super().post_trade_order(**kwargs)
            return _ack_fixture(envelope)

    transport = AckTransport()
    # Lack of authority cannot be bypassed by a valid reducing intent.
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError, match="NO_PERMIT"):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=None,
            store_root=tmp_path,
            transport=transport,
            handle=_handle(),
        )
    assert transport.post_count == 0
    sent = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=_permit(envelope),
        store_root=tmp_path,
        transport=transport,
        handle=_handle(),
    )
    assert sent.real_post_count == 0 and not sent.venue_live_contact
    assert transport.last_payload["reduceOnly"] is True
    assert transport.last_payload["sz"] == "1.2"
    # An explicit mock ACK is not position feedback or a fill.
    ack = sent.post_submit_join
    assert ack.typed_outcome == "ACKNOWLEDGED" and not ack.fill_observed
    original = args["position"]
    assert original.quantity_observation.quantity == Decimal("1.2")
    positions = {
        "code": "0",
        "data": [{"instId": envelope.instrument_id, "posSide": side, "pos": remaining}],
    }
    order = {
        "clOrdId": envelope.client_order_id,
        "ordId": "offline-close-order",
        "instId": envelope.instrument_id,
        "state": state,
        "sz": "1.2",
        "accFillSz": str(Decimal("1.2") - Decimal(remaining)),
        "sCode": "0",
    }
    binding = replace(
        _binding(),
        instrument_id=envelope.instrument_id,
        native_id=envelope.instrument_id,
        canonical_decision_id=source.canonical_intent.decision_id,
        selected_direction="EXIT",
        order_side=envelope.side,
        final_quantity=envelope.quantity,
        order_type="market",
        order_price="",
        clordid=envelope.client_order_id,
        envelope_digest=envelope.envelope_digest,
    )
    reconciled = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        post_submit_join=ack,
        binding=binding,
        decision_outcome="EXIT",
        venue_plan_identity=plan.clordid,
        envelope_identity=envelope.envelope_digest,
        submit_attempt_id="offline-close-attempt",
        local_durable_state_version="v1",
        offline_fixture=OfflineExchangeFixtureV1(
            pending_orders={"code": "0", "data": [order]},
            positions=positions,
        ),
    )
    assert reconciled.ghv_forward_join == reconciled.ghv_reverse_join == "PASS"
    assert (
        reconciled.reconciliation.decision.outcome
        == {
            "live": "CONFIRMED_OPEN",
            "partially_filled": "CONFIRMED_PARTIALLY_FILLED",
            "filled": "CONFIRMED_FILLED",
        }[state]
    )
    # FILLED still retains exposure at the order-reconciliation boundary.
    assert reconciled.reconciliation.decision.exposure_retained is True
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
        resolve_per_lane_position_truth_v1,
    )

    feedback = resolve_per_lane_position_truth_v1(
        identity=args["identity"],
        occupancy_payloads={"POSITIONS": positions},
        allow_global_fallback=False,
    )
    assert feedback.venue_flat is (remaining == "0")
    if remaining != "0":
        assert feedback.quantity_observation.quantity == Decimal(remaining)
    assert original.quantity_observation.quantity == Decimal("1.2")
    with pytest.raises(FullCoreEnvelopeBoundSendSeamError):
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=_permit(envelope),
            store_root=tmp_path,
            transport=transport,
            handle=_handle(),
        )
    assert transport.post_count == 1


def _ack_fixture(envelope):
    from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
        FullCoreTradeOrderPostResultV1,
    )

    return FullCoreTradeOrderPostResultV1(
        post_attempted=True,
        venue_live_contact=False,
        method="POST",
        http_status=200,
        payload={
            "code": "0",
            "data": [
                {"clOrdId": envelope.client_order_id, "ordId": "offline-close-order", "sCode": "0"}
            ],
        },
        unknown_outcome=False,
        transport_class="OFFLINE_CLOSE_ACK_FIXTURE",
        endpoint="/api/v5/trade/order",
    )


@pytest.mark.parametrize(
    "problem", ["quantity", "side", "decision", "epoch", "generation", "safety", "action"]
)
def test_corrupt_or_cross_bound_close_never_produces_a_plan(problem):
    args, source = _prepared()
    if problem in {"quantity", "side"}:
        source = replace(
            source,
            canonical_intent=replace(
                source.canonical_intent,
                **({"quantity": Decimal("2")} if problem == "quantity" else {"side": "SHORT"}),
            ),
        )
    elif problem == "generation":
        source = replace(
            source, quantity_handoff=replace(source.quantity_handoff, instrument_epoch="old")
        )
    elif problem == "decision":
        args["replay"].evidence.decision_id = "different-decision"
    elif problem == "epoch":
        args["replay"].evidence.trading_epoch = 99
    elif problem == "safety":
        args["replay"].replay_execution_safety = replace(
            args["replay"].replay_execution_safety, cancel_only=True
        )
    else:
        args["replay"].evidence.decision_outcome = "reduce"
    status, reasons, plan = _bind(args, source)
    assert status.value == "DENY" and plan is None
    assert "FULL_CLOSE_EXECUTION_SOURCE_INVALID" in reasons


@pytest.mark.parametrize(
    "problem", ["stale_snapshot", "non_reducing", "wrong_side", "wrong_native"]
)
def test_host_rechecks_original_snapshot_and_exact_envelope(problem):
    args, source = _prepared()
    _, _, plan = _bind(args, source)
    envelope = _envelope(plan, source)
    payload = {
        "code": "0",
        "data": [{"instId": envelope.instrument_id, "posSide": "long", "pos": "1.2"}],
    }
    assert validates_position_management_execution_handoff_v1(
        PositionManagementExecutionHandoffV1(source, envelope),
        native_id=envelope.instrument_id,
        positions_payload=payload,
    )
    if problem == "stale_snapshot":
        payload["data"][0]["pos"] = "0.4"
    else:
        envelope = replace(
            envelope,
            **{
                "non_reducing": {"reduce_only": False},
                "wrong_side": {"side": "buy"},
                "wrong_native": {"instrument_id": "foreign"},
            }[problem],
        )
        digest = compute_final_order_envelope_digest_v1(envelope.to_canonical_payload_v1())
        envelope = replace(envelope, envelope_digest=digest, envelope_id=f"env-{digest[:32]}")
    assert not validates_position_management_execution_handoff_v1(
        PositionManagementExecutionHandoffV1(source, envelope),
        native_id=args["identity"].venue_native_id,
        positions_payload=payload,
    )


def test_close_does_not_override_send_kill_switch():
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
        FullCoreExternalEffectPermitError,
        issue_external_effect_permit_v1,
    )

    args, source = _prepared()
    _, _, plan = _bind(args, source)
    with pytest.raises(FullCoreExternalEffectPermitError, match="KILL_SWITCH_BLOCKED"):
        issue_external_effect_permit_v1(
            _envelope(plan, source),
            authority_ref="OFFLINE_CLOSE_TEST_ONLY",
            kill_switch_blocked=True,
            durable_kill_switch_evidence_status="TRUSTED_PRESENT",
            filegate_denied=False,
            step_29q_status="PLAN_ONLY",
        )


def test_explicit_inverse_metadata_cannot_be_misclassified_as_linear_close():
    from tests.ops.test_governed_productive_instrument_metadata_authority_producer_v1 import (
        _row,
        INST,
    )
    from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
        produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
    )

    def metadata(kind):
        return produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
            venue_native_id=INST,
            bound_instrument_id=_bound().instrument_id,
            instruments_payload=_row(ctType=kind),
            observed_at_as_of="2026-11-03T00:00:00Z",
        )

    linear, inverse = metadata("linear"), metadata("inverse")
    assert inverse.produced and inverse.constraints.contract_kind == "INVERSE"
    assert inverse.instrument_metadata_version != linear.instrument_metadata_version
    args, _ = _prepared()
    args["metadata"] = inverse
    denied = compose_position_management_full_close_intent_v1(**args)
    assert denied.canonical_intent is None
    assert denied.reason_codes == ("POSITION_QUANTITY_METADATA_MISMATCH",)
    assert not metadata("unknown").produced
