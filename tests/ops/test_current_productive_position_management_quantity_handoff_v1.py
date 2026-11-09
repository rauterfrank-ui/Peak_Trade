"""Position contracts are carried exactly and never manufacture reducing size."""

from dataclasses import replace
from decimal import Decimal
from types import SimpleNamespace

import pytest

from src.governance.canonical_order_intent_v1 import build_canonical_order_intent_v1
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
    resolve_per_lane_position_truth_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    bind_position_management_quantity_handoff_v1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    produce_current_productive_instrument_quantity_constraints_from_okx_row_v1,
)
from tests.governance.test_canonical_order_intent_v1 import _build_input
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.double_play_entry_exit_policy_v0 import PositionState, ReconciliationState
from trading.master_v2.replay_execution_safety_contract_v1 import ReplayExecutionSafetyV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    compose_position_management_full_close_intent_v1,
)


def _case(*, side="long", action="reduce", lane_id="LANE_1"):
    bound = _bound()
    identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(lane_id=lane_id, bound=bound)
    metadata = produce_current_productive_instrument_quantity_constraints_from_okx_row_v1(
        venue_native_id=bound.venue_native_id,
        bound_instrument_id=bound.instrument_id,
        observed_at_as_of="2026-11-03T00:00:00Z",
        instruments_payload={
            "code": "0",
            "data": [
                {
                    "instId": bound.venue_native_id,
                    "instType": "SWAP",
                    "ctType": "linear",
                    "ctVal": "1",
                    "lotSz": "0.01",
                    "minSz": "0.01",
                    "tickSz": "0.01",
                    "state": "live",
                }
            ],
        },
    )
    assert metadata.produced
    inp = _build_input(
        intent_action=action.upper(),
        trading_epoch="1",
        sizing_overrides={
            "instrument_id": bound.instrument_id,
            "instrument": metadata.constraints,
            "selected_side": side.upper(),
            "decision_outcome": action,
            "reconciled_open_position_quantity": Decimal("1"),
            "current_open_side": side.upper(),
            "current_open_positions_count": 1,
            "current_reconciled_exposure": Decimal("1"),
            "protective_stop_price": Decimal("1900") if side == "long" else Decimal("2100"),
        },
        current_reconciled_exposure=Decimal("1"),
    )
    built = build_canonical_order_intent_v1(inp)
    assert built.intent is not None, built.reason_codes
    qty = built.intent.quantity if action == "exit" else Decimal("1")
    position = _position(identity, side=side, quantity=str(qty))
    replay = SimpleNamespace(
        replay_pass=True,
        evidence=SimpleNamespace(
            instrument_id=bound.instrument_id,
            decision_id=built.intent.decision_id,
            decision_outcome=action,
            trading_epoch=1,
        ),
        intermediate=SimpleNamespace(
            entry_exit_decision=SimpleNamespace(
                instrument_id=bound.instrument_id,
                reduce_only=True,
                decision_outcome=DecisionOutcome(action),
                trading_epoch=1,
            ),
            canonical_order_intent=built.intent,
            capital_risk_sizing_decision=inp.sizing_decision,
        ),
    )
    return dict(
        identity=identity,
        position=position,
        replay=replay,
        metadata=metadata,
        reconciliation_admitted=True,
    )


def _position(identity, *, side, quantity):
    return resolve_per_lane_position_truth_v1(
        identity=identity,
        allow_global_fallback=False,
        occupancy_payloads={
            "POSITIONS": {
                "code": "0",
                "data": [
                    {
                        "instId": identity.venue_native_id,
                        "posSide": side,
                        "pos": quantity,
                    }
                ],
            }
        },
    )


@pytest.mark.parametrize("side", ["long", "short"])
@pytest.mark.parametrize("action", ["reduce", "exit"])
def test_existing_canonical_action_binds_to_matching_position_without_resizing(side, action):
    args = _case(side=side, action=action)
    intent = args["replay"].intermediate.canonical_order_intent
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.status == "BOUND_TO_CANONICAL_INTENT", result.reason_codes
    assert result.requested_quantity == intent.quantity
    assert result.requested_quantity <= result.open_quantity
    assert result.quantity_unit == "CONTRACTS"
    assert result.submission_authorized is False
    assert result.canonical_intent_ref == intent.semantic_digest


def test_position_precision_is_not_lost_in_float_conversion():
    args = _case()
    quantity = "1.12345678901234567890123456789"
    position = _position(args["identity"], side="long", quantity=quantity)
    assert position.quantity_observation.quantity == Decimal(quantity)
    args["position"] = position
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.to_dict()["open_quantity"] == quantity


@pytest.mark.parametrize(
    "problem,reason",
    [
        ("foreign_lane", "POSITION_QUANTITY_IDENTITY_MISMATCH"),
        ("foreign_native", "POSITION_QUANTITY_IDENTITY_MISMATCH"),
        ("old_generation", "POSITION_QUANTITY_IDENTITY_MISMATCH"),
        ("oversize", "REDUCING_QUANTITY_EXCEEDS_OPEN_POSITION"),
        ("wrong_decision", "REDUCING_INTENT_POSITION_BINDING_MISMATCH"),
        ("wrong_side", "REDUCING_INTENT_POSITION_BINDING_MISMATCH"),
        ("no_reconciliation", "POSITION_RECONCILIATION_OR_REPLAY_UNAVAILABLE"),
        ("no_quantity", "OBSERVED_POSITION_QUANTITY_REQUIRED"),
        ("unbound_sizing", "REDUCING_INTENT_SIZING_BINDING_MISMATCH"),
    ],
)
def test_unbound_or_risk_increasing_quantity_is_rejected(problem, reason):
    args = _case()
    obs = args["position"].quantity_observation
    if problem in {"foreign_lane", "foreign_native", "old_generation", "oversize"}:
        changes = {
            "foreign_lane": {"lane_id": "LANE_2"},
            "foreign_native": {"venue_native_id": "foreign"},
            "old_generation": {"instrument_epoch": "old"},
            "oversize": {
                "quantity": args["replay"].intermediate.canonical_order_intent.quantity / 2
            },
        }[problem]
        args["position"] = replace(args["position"], quantity_observation=replace(obs, **changes))
    elif problem == "wrong_decision":
        args["replay"].evidence.decision_id = "another-decision"
    elif problem == "wrong_side":
        args["position"] = _position(args["identity"], side="short", quantity="1")
    elif problem == "no_reconciliation":
        args["reconciliation_admitted"] = False
    elif problem == "no_quantity":
        args["position"] = replace(args["position"], quantity_observation=None)
    else:
        args["replay"].intermediate.capital_risk_sizing_decision = None
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.status == "REJECTED"
    assert reason in result.reason_codes
    assert result.submission_authorized is False


def test_exit_with_partial_quantity_does_not_claim_to_close_position():
    args = _case(action="exit")
    obs = args["position"].quantity_observation
    args["position"] = replace(
        args["position"], quantity_observation=replace(obs, quantity=obs.quantity * 2)
    )
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.status == "REJECTED"
    assert result.reason_codes == ("EXIT_QUANTITY_DOES_NOT_CLOSE_POSITION",)


def test_missing_intent_carries_position_limit_without_inventing_requested_quantity():
    args = _case()
    args["replay"].intermediate.canonical_order_intent = None
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.status == "POSITION_QUANTITY_BOUND"
    assert result.open_quantity == 1
    assert result.requested_quantity is None
    assert result.reason_codes == ("CANONICAL_REDUCING_INTENT_REQUIRED",)


def test_missing_metadata_never_assigns_contract_units():
    args = _case()
    args["metadata"] = None
    result = bind_position_management_quantity_handoff_v1(**args)
    assert result.quantity_unit == "UNBOUND"
    assert result.status == "POSITION_OBSERVATION_BOUND"


@pytest.mark.parametrize("problem", ["unreconciled", "submission_unknown", "cancel_only"])
def test_existing_intent_does_not_bypass_unresolved_close_safety(problem):
    args = _case(action="exit")
    replay = args["replay"]
    replay.intermediate.entry_exit_decision.position_state = PositionState.OPEN_FULL
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
    if problem == "unreconciled":
        replay.intermediate.entry_exit_decision.reconciliation_state = ReconciliationState.UNKNOWN
    elif problem == "submission_unknown":
        replay.intermediate.entry_exit_decision.position_state = PositionState.SUBMISSION_UNKNOWN
    else:
        replay.replay_execution_safety = replace(replay.replay_execution_safety, cancel_only=True)
    result = compose_position_management_full_close_intent_v1(**args)
    assert result.canonical_intent is None
    assert result.quantity_handoff.status == "REJECTED"
