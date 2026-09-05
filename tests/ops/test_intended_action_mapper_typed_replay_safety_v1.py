"""Mapper consumes typed ReplayExecutionSafetyV1; legacy string fallback is explicit."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    POST_29Q_CONSUMPTION_GUARD_REASON,
    POST_29Q_CONSUMPTION_GUARD_ROLE,
    PRE_29Q_REPLAY_SAFETY_REASON,
    CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK,
    ReplayExecutionSafetyV1,
)


def _mapper_result(
    *,
    outcome: str,
    reasons: tuple[str, ...] = (),
    replay_pass: bool = True,
    coi_action: str | None = None,
    coi_qty: str | None = None,
    sizing_qty: str | None = None,
    replay_execution_safety: ReplayExecutionSafetyV1 | None = None,
) -> SimpleNamespace:
    coi = None
    if coi_action is not None:
        coi = SimpleNamespace(intent_action=coi_action, quantity=Decimal(str(coi_qty or "0")))
    sizing = None
    if sizing_qty is not None:
        sizing = SimpleNamespace(final_quantity=Decimal(str(sizing_qty)))
    return SimpleNamespace(
        replay_pass=replay_pass,
        replay_execution_safety=replay_execution_safety,
        evidence=SimpleNamespace(
            decision_outcome=outcome,
            selected_side="long",
            reason_codes=reasons,
        ),
        intermediate=SimpleNamespace(
            canonical_order_intent=coi,
            capital_risk_sizing_decision=sizing,
        ),
    )


def _typed(*, entry_blocked: bool = False, emergency: bool = False) -> ReplayExecutionSafetyV1:
    return ReplayExecutionSafetyV1(
        entry_blocked=entry_blocked,
        emergency_boundary_active=emergency,
        emergency_mode="emergency_flatten" if emergency else None,
        flatten_only=emergency,
        reduce_only=False,
        cancel_only=False,
        reason_codes=("typed_emergency",) if emergency else (),
        source_refs=("safety:test",),
        runtime_authority_effect="NONE",
        post_29q_role=POST_29Q_CONSUMPTION_GUARD_ROLE if emergency else "NONE",
        consumption_guard_effect=CONSUMPTION_GUARD_EFFECT_ENTER_BLOCK if emergency else "NONE",
    )


def test_typed_safety_hard_block_enter_without_coi_is_hold() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            sizing_qty="1.0",
            replay_execution_safety=_typed(entry_blocked=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.intended_quantity == Decimal("0")
    assert mapped.safety_blocked is True


def test_typed_emergency_with_coi_is_hold_not_buy() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            coi_action="ENTER_LONG",
            coi_qty="0.2",
            replay_execution_safety=_typed(emergency=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.intended_quantity == Decimal("0")
    assert mapped.safety_blocked is True
    assert mapped.decision_outcome == "enter_long"
    assert mapped.quantity_source == "post_29q_consumption_guard"
    assert POST_29Q_CONSUMPTION_GUARD_REASON in mapped.reason_codes
    assert mapped.reason_codes.count("FILEGATE_KILLED") == 0


def test_typed_contract_leads_when_reason_strings_absent() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            reasons=(),
            coi_action="ENTER_LONG",
            coi_qty="0.2",
            replay_execution_safety=_typed(emergency=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.safety_blocked is True


def test_exit_remains_executable_with_typed_emergency() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="exit",
            replay_pass=False,
            replay_execution_safety=_typed(emergency=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        portfolio_snapshot={
            "state": {
                "positions": {
                    PRODUCTION_INSTRUMENT_ID: {"quantity": "0.1", "avg_entry_price": "3500"}
                }
            }
        },
    )
    assert mapped.intended_side == "SELL"
    assert mapped.quantity_source == "exit_or_reduce"


def test_legacy_fallback_hold_without_typed_contract() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            reasons=("safety_mode_blocked",),
            sizing_qty="9.0",
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.safety_blocked is True


def test_mapper_does_not_invent_buy_without_coi() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(outcome="enter_long", sizing_qty="1.0", replay_execution_safety=_typed()),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert "NO_CANONICAL_ORDER_INTENT" in mapped.reason_codes


def test_typed_pre_29q_block_is_distinct_from_post_29q_guard() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            coi_action="ENTER_LONG",
            coi_qty="0.2",
            replay_execution_safety=_typed(entry_blocked=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert mapped.decision_outcome == "enter_long"
    assert mapped.quantity_source == "pre_29q_replay_safety"
    assert PRE_29Q_REPLAY_SAFETY_REASON in mapped.reason_codes
    assert POST_29Q_CONSUMPTION_GUARD_REASON not in mapped.reason_codes


def test_mapper_hold_does_not_authorize_submission_or_imitate_filegate() -> None:
    mapped = map_replay_result_to_intended_analytical_action_v1(
        _mapper_result(
            outcome="enter_long",
            coi_action="ENTER_LONG",
            coi_qty="0.2",
            replay_execution_safety=_typed(emergency=True),
        ),
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert mapped.intended_side == "HOLD"
    assert (
        not hasattr(mapped, "submission_authorized")
        or getattr(mapped, "submission_authorized", False) is False
    )
    assert "FILEGATE_KILLED" not in mapped.reason_codes
    assert "KILL_ALL" not in mapped.reason_codes
