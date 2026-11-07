"""Preserve original hold lineage at actual S6/host consumers, without send authority."""

from pathlib import Path
import socket

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_persistent_natural_enter_convergence_v1 as convergence,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    C1_A,
    C1_B,
    C1_C,
    _auth,
    _obs,
    _run,
    _source,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _t2_enter,
    _t2_hold,
)


@pytest.fixture(autouse=True)
def synthetic_ports_and_isolation(monkeypatch, tmp_path):
    from tests.ops._current_productive_pre_external_test_process_isolation_v1 import (
        establish_current_productive_pre_external_test_process_isolation_v1,
        reset_current_productive_pre_external_shared_test_process_state_v1,
    )

    establish_current_productive_pre_external_test_process_isolation_v1(
        monkeypatch=monkeypatch,
        f1_root=tmp_path / "isolated-f1",
        reseed_workspace_f1_m9=False,
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Synthetic handoff proof must never open a network socket")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    yield
    reset_current_productive_pre_external_shared_test_process_state_v1()


def assert_boundary(result):
    assert result.post_count == 0
    assert result.external_effect_count == 0
    assert result.permit_created is False


@pytest.mark.parametrize("short", [False, True])
def test_original_n1_hold_reaches_actual_supervisor_and_retains_cold_recovery_fence(
    tmp_path, monkeypatch, short
):
    from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1

    original_bind = Owner.bind_execution_plan_v1
    original_cycle = convergence.run_current_productive_governed_cycle_v1
    plans = []
    cycles = []

    def observe_bind(owner, rid, envelope, **kwargs):
        output = original_bind(owner, rid, envelope, **kwargs)
        snapshot = owner.risk_snapshot_v1()["state"]
        reservation = next(r for r in snapshot["reservations"] if r["reservation_id"] == rid)
        plans.append((owner, rid, envelope, snapshot, reservation))
        return output

    def observe_cycle(**kwargs):
        output = original_cycle(**kwargs)
        cycles.append(output)
        return output

    monkeypatch.setattr(Owner, "bind_execution_plan_v1", observe_bind)
    monkeypatch.setattr(convergence, "run_current_productive_governed_cycle_v1", observe_cycle)
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    assert result.ok
    assert len(plans) == 1
    owner, rid, envelope, snapshot, reservation = plans[0]
    continuous = result.policy_result.orchestrator_result
    record = continuous.cycle_records[-1]
    assert continuous.disposition == "PRE_EXTERNAL_EFFECT"
    assert cycles[-1].extra["PORTFOLIO_RESERVATION_ID"] == rid
    assert record.portfolio_reservation_id == rid
    assert record.final_order_envelope == envelope
    assert record.final_order_envelope.admission_ref.endswith(":portfolio-reservation:" + rid)
    assert record.pending_decision_context.canonical_decision_id == reservation["decision_id"]
    assert (
        record.pending_decision_context.instrument_id
        == reservation["binding"]["bound"]["instrument_id"]
    )
    assert envelope.side == ("sell" if short else "buy")
    assert record.canonical_order_intent is cycles[-1].canonical_order_intent
    assert_boundary(continuous)
    assert result.trace.post_count == 0
    assert result.policy_result.post_allowed is False
    assert result.policy_result.external_effect_authorized is False

    # The real supervisor has closed its owner. Displayed historical admission
    # fields are not operational rights; the original submit predicate is fenced.
    with pytest.raises(ValueError, match="EXECUTION_SUBMIT_OWNER_FENCED"):
        owner.inspect_execution_submit_context_v1(rid, envelope, None)
    stable_root = Path(result.trace.extra["portfolio_budget_host"]["durable_root"])
    bindings = {
        lane: BoundInstrumentV1(**row["bound"]) for lane, row in snapshot["lane_bindings"].items()
    }
    recovered = Owner(
        durable_root=stable_root / "owner",
        durable_account_identity=snapshot["account_identity"],
        durable_mode="recover",
        durable_lane_bindings=bindings,
    )
    try:
        state = recovered.budget_state_v1()
        assert state.recovery_required and not state.admitted
        assert recovered.active_sum_v1() == owner.active_sum_v1() > 0
        assert recovered.execution_links_v1()[rid]["envelope"] == envelope.to_runtime_json_v1()
        assert recovered.execution_links_v1()[rid]["phase"] == "PLAN_BOUND"
        with pytest.raises(ValueError, match="EXECUTION_SUBMIT_OWNER_FENCED"):
            recovered.inspect_execution_submit_context_v1(rid, envelope, None)
    finally:
        recovered.close()


@pytest.mark.parametrize(
    "hold_rid,enter_rid",
    [("original-rejected-hold", "original-entry-hold"), ("", "original-entry-hold"), ("old", "")],
)
def test_each_record_keeps_its_own_producer_reference_and_entry_still_stops(
    tmp_path, hold_rid, enter_rid
):
    outputs = []
    original_contexts = [object(), None]

    def dispatch(**kwargs):
        output = _t2_hold(**kwargs) if not outputs else _t2_enter(**kwargs)
        output.portfolio_reservation_id = hold_rid if not outputs else enter_rid
        output.execution_plan_context = original_contexts[len(outputs)]
        outputs.append(output)
        return output

    source = _source(_obs(C1_A), _obs(C1_B), _obs(C1_C))
    result = _run(
        tmp_path,
        observation_source=source,
        authorization=_auth(max_cycles_per_run=3),
        t2_cycle_dispatch=dispatch,
    )
    assert [r.portfolio_reservation_id for r in result.cycle_records] == [hold_rid, enter_rid]
    assert result.cycle_records[0].execution_plan_context is original_contexts[0]
    assert result.cycle_records[1].execution_plan_context is None
    assert result.cycle_records[0].final_order_envelope is None
    assert result.cycle_records[1].final_order_envelope == outputs[-1].final_order_envelope
    assert result.disposition == "PRE_EXTERNAL_EFFECT"
    assert len(outputs) == source.poll_count == 2
    assert "does not compose" in result.next_required_owner_decision
    assert_boundary(result)


@pytest.mark.parametrize("embed_reference", [False, True])
def test_missing_producer_reference_stays_empty_without_parsing_an_envelope(
    tmp_path, embed_reference
):
    from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
        FullCoreEnvelopeBoundSendSeamError,
        inspect_original_portfolio_execution_context_v1,
    )

    def dispatch(**kwargs):
        output = _t2_enter(**kwargs)
        if embed_reference:
            body = output.final_order_envelope.to_canonical_payload_v1()
            body.pop("issued_for_exact_action")
            body.pop("schema_version")
            body["admission_ref"] = "synthetic:portfolio-reservation:opaque-envelope-reference"
            envelope = build_final_order_envelope_v1(**body)
            output.final_order_envelope = envelope
            output.final_envelope_id = envelope.envelope_id
            output.final_envelope_digest = envelope.envelope_digest
        return output

    result = _run(tmp_path, t2_cycle_dispatch=dispatch)
    record = result.cycle_records[0]
    assert record.portfolio_reservation_id == ""
    if embed_reference:
        with pytest.raises(
            FullCoreEnvelopeBoundSendSeamError, match="HOST_PORTFOLIO_EXECUTION_CONTEXT_REQUIRED"
        ):
            inspect_original_portfolio_execution_context_v1(
                envelope=record.final_order_envelope,
                portfolio_reservation_id=record.portfolio_reservation_id,
            )
    assert result.disposition == "PRE_EXTERNAL_EFFECT"
    assert_boundary(result)
