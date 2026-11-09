"""Observe existing financial owners on actual N1 with synthetic, offline ports."""

from decimal import Decimal
import socket

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as invoke,
)
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1


@pytest.mark.parametrize("short", [False, True])
def test_actual_n1_preserves_original_risk_quantity_into_reservation_and_final_envelope(
    tmp_path, monkeypatch, short
):
    def no_network(*args, **kwargs):
        raise AssertionError("This evidence uses synthetic ports only")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    original = invoke.join_current_productive_enter_live_29p_before_venue_plan_v1
    captured = []

    def observe(**kwargs):
        result = original(**kwargs)
        if result.status == "PASS":
            owner = kwargs["portfolio_budget_owner"]
            slot = kwargs["portfolio_slot"]
            held = owner.lookup_v1(
                slot_id=slot.slot_id,
                decision_id=slot.decision_id,
                cycle_id=slot.cycle_id,
                observation_id=owner.budget_state_v1().observation_id,
            )
            captured.append((kwargs, result, held, owner.risk_snapshot_v1()))
        return result

    monkeypatch.setattr(
        invoke, "join_current_productive_enter_live_29p_before_venue_plan_v1", observe
    )
    run = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    sequence = run.policy_result.orchestrator_result
    envelope = sequence.cycle_records[-1].final_order_envelope
    assert len(captured) == 1 and envelope is not None
    kwargs, result, held, snapshot = captured[0]
    sizing = result.replay.intermediate.capital_risk_sizing_decision
    before, after = kwargs["replay"].evidence, result.replay.evidence
    # The existing boundary sizes an original decision; it does not decide the
    # direction again or turn an offline model into productive authority.
    assert kwargs.get("restrictive_risk") is None
    for name in ("decision_id", "selected_side", "decision_outcome", "scope_event_ref"):
        assert getattr(before, name) == getattr(after, name)
    assert result.capital_risk_mode == "LIVE_ACCOUNT_BOUND"
    assert result.used_offline_default_equity == "false"
    assert held.reservation_id == result.portfolio_reservation_id
    assert held.decision_id == before.decision_id
    assert held.amount == sizing.canonical_position_sizing.resulting_notional
    assert held.amount == sizing.post_sizing_risk.resulting_notional
    assert Decimal(envelope.quantity) == sizing.final_quantity
    assert sizing.final_quantity == sizing.quantity_provenance.final_quantity
    assert sizing.final_quantity == sizing.canonical_position_sizing.rounded_quantity
    assert sizing.final_quantity == sizing.post_sizing_risk.final_allowed_quantity
    assert envelope.quantity_unit == "CONTRACTS"
    assert envelope.side == ("sell" if short else "buy")
    bindings = list(snapshot["state"]["sizing_bindings"].values())
    assert len(bindings) == 1
    stored = bindings[0]
    assert stored["schema"] == "reservation_sizing_binding.v1" and "risk_binding" not in stored
    applied = stored["applied_input"]
    multiplier = Decimal(applied["instrument"]["contract_multiplier"])
    assert held.amount == Decimal(applied["reference_price"]) * multiplier * sizing.final_quantity
    assert sizing.post_sizing_risk.resulting_max_loss == (
        sizing.pre_sizing_risk.stop_or_risk_distance * multiplier * sizing.final_quantity
    )
    assert sizing.post_sizing_risk.resulting_max_loss <= sizing.pre_sizing_risk.maximum_loss_budget
    assert 0 < held.amount <= sizing.scope_capital_envelope.per_order_cap == Decimal("25")
    assert sizing.scope_capital_envelope.total_capital_limit == Decimal("25")
    assert Decimal(stored["decision"]["final_quantity"]) == Decimal(envelope.quantity)
    assert envelope.admission_ref.endswith(":portfolio-reservation:" + str(held.reservation_id))
    assert sequence.post_count == 0 and sequence.permit_created is False
