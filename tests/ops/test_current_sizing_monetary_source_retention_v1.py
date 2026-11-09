"""Actual N1 normalization sources survive original holds and cold recovery."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import socket

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as n1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    root = tmp_path_factory.mktemp("original-monetary-source")
    captures = []
    original = n1.join_current_productive_enter_live_29p_before_venue_plan_v1

    def observe(**kwargs):
        output = original(**kwargs)
        if output.status == "PASS":
            owner = kwargs["portfolio_budget_owner"]
            captures.append((owner.risk_snapshot_v1(), owner.durable_scope_identity_v1()))
        return output

    def no_network(*args, **kwargs):
        raise AssertionError("Explicit synthetic ports only")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(socket.socket, "connect", no_network)
        patch.setattr(n1, "join_current_productive_enter_live_29p_before_venue_plan_v1", observe)
        result = _run_layered_entry_supervisor_v1(root, short=False)
    assert result.policy_result.orchestrator_result.post_count == 0
    assert len(captures) == 1
    return captures[0]


def sample(captured):
    snapshot, _scope = captured
    records = snapshot["state"]["sizing_bindings"]
    assert len(records) == 1
    rid, raw = next(iter(records.items()))
    binding = ReservationSizingBindingV1.from_dict_v1(deepcopy(raw))
    amount = binding.decision.canonical_position_sizing.resulting_notional
    binding.validate_v1(amount=amount, decision_id=binding.applied_input.decision_id)
    return rid, binding, amount


def test_actual_normalization_readback_is_detached_and_exact(captured):
    _rid, binding, amount = sample(captured)
    source = binding.monetary_source
    ctx = source.validate_sizing_v1(binding.applied_input)
    assert ctx.normalization_digest == source.normalization_digest
    assert ctx.reference_price.amount == binding.applied_input.reference_price
    assert ctx.native_reference_price.amount == Decimal(source.native_reference_price)
    assert ctx.reference_price.currency == "USDC"
    stored = binding.to_dict_v1()
    stored["monetary_source"]["native_reference_price"] = "1"
    assert source.native_reference_price != "1"
    binding.validate_v1(amount=amount, decision_id=binding.applied_input.decision_id)


@pytest.mark.parametrize(
    "fault", ["instrument", "native", "equity", "reference", "stop", "digest", "quote", "fx"]
)
def test_relabelled_or_changed_money_cannot_back_the_original_quantity(captured, fault):
    _rid, binding, amount = sample(captured)
    source = binding.monetary_source
    if fault == "quote":
        payload = json.loads(source.instruments_json)
        for row in payload["data"]:
            if row.get("instId") == source.venue_native_id:
                row["quoteCcy"] = row["settleCcy"] = "EUR"
        source = replace(source, instruments_json=json.dumps(payload))
    elif fault == "fx":
        source = replace(source, index_tickers_json="null")
    else:
        changes = {
            "instrument": dict(canonical_instrument_id="another-instrument"),
            "native": dict(venue_native_id="another-native"),
            "equity": dict(account_equity_usdc="1"),
            "reference": dict(native_reference_price="1"),
            "stop": dict(native_protective_stop_price="1"),
            "digest": dict(normalization_digest="0" * 64),
        }
        source = replace(source, **changes[fault])
    broken = replace(binding, monetary_source=source)
    with pytest.raises(ValueError, match="RESERVATION_MONETARY_SOURCE_INVALID"):
        broken.validate_v1(amount=amount, decision_id=binding.applied_input.decision_id)


def test_original_cold_owner_retains_sources_and_stays_fenced(captured):
    snapshot, scope = captured
    rid, binding, amount = sample(captured)
    from pathlib import Path

    cold = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=Path(scope["root"]),
        durable_account_identity=scope["account"],
        durable_mode="recover",
        durable_lane_bindings={
            lane: BoundInstrumentV1(**record["bound"])
            for lane, record in snapshot["state"]["lane_bindings"].items()
        },
    )
    try:
        state = cold.budget_state_v1()
        assert not state.admitted and state.recovery_required
        assert cold.active_sum_v1() == amount
        source = cold.reservation_monetary_source_v1(rid)
        assert source.to_dict_v1() == binding.monetary_source.to_dict_v1()
        assert (
            source.validate_sizing_v1(binding.applied_input).reference_price.amount
            == binding.applied_input.reference_price
        )
        assert not cold.budget_state_v1().admitted
    finally:
        cold.close()


def test_legacy_sizing_record_is_not_automatically_certified(captured):
    _rid, binding, amount = sample(captured)
    legacy = replace(binding, monetary_source=None)
    data = legacy.to_dict_v1()
    assert data["schema"] == "reservation_sizing_binding.v1"
    restored = ReservationSizingBindingV1.from_dict_v1(data)
    assert restored.monetary_source is None
    restored.validate_v1(amount=amount, decision_id=restored.applied_input.decision_id)
