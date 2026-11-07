"""Projection contracts: historical labels cannot promote an observed HOLD.

These are explicit observation-port unit cases, not integrated runtime proofs.
The existing WP03/WP04 integration tests exercise the actual supervisor separately.
"""

from types import SimpleNamespace
from dataclasses import replace
from decimal import Decimal
import json

import pytest

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    prove_wp03_golden_convergence_v1,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.trace_projection_v1 import (
    project_supervisor_golden_trace_v1,
    prove_contiguous_confirmation_epochs_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.runtime_supervisor_proof_v1 import (
    prove_standing_supervisor_from_runtime_session_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.trace_v1 import (
    StandingSupervisorTraceV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    PendingDecisionContextV1,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.runtime_boundary_evidence_v1 import (
    current_runtime_boundary_evidence_v1,
)


def _case(*, historical="enter_long", disposition="HOLD_CLOSED"):
    records = tuple(
        SimpleNamespace(
            s5_disposition=disposition,
            s5_reason_code="OBSERVED_RESULT",
            cycle_instance_id=f"current-cycle-{i}",
            c1_venue_event_time=1000.0 + i * 60,
        )
        for i in range(2)
    )
    terminal = (
        "PRE_EXTERNAL_EFFECT" if disposition == "PRE_EXTERNAL_EFFECT" else "MAX_CYCLES_BOUND_STOP"
    )
    trace = StandingSupervisorTraceV1(
        run_id="observation-port-unit-case",
        bound_instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        recovery_completed=True,
        observation_recovery_completed=True,
        public_supply_refreshed=True,
        pretrade_truth_refreshed=True,
        continuous_admission_granted=True,
        wp02_hook_invoked=True,
        wp02_cap21_refresh_invoked=True,
        wp02_hard_facts_handoff_invoked=True,
        governed_cycle_count=2,
        accepted_c1_count=2,
        terminal_disposition=terminal,
        extra={"natural_enter_decision": historical},
    )
    orch = SimpleNamespace(
        cycle_records=records,
        disposition=terminal,
        cycles_completed=2,
        accepted_c1_count=2,
        last_accepted_c1=1060.0,
        cursor_floor_before=940.0,
        cursor_floor_after=1060.0,
        permit_created=False,
        post_count=0,
        external_effect_count=0,
    )
    return SimpleNamespace(
        ok=True,
        run_id=trace.run_id,
        trace=trace,
        owner_go_consumed=True,
        authority_invariants_ok=True,
        policy_result=SimpleNamespace(
            orchestrator_result=orch, post_allowed=False, external_effect_authorized=False
        ),
    )


@pytest.mark.parametrize("side,historical", [("LONG", "enter_long"), ("SHORT", "enter_short")])
def test_historical_entry_does_not_promote_current_hold(side, historical):
    result = _case(historical=historical)
    projected = project_supervisor_golden_trace_v1(
        result, side=side, observation_scope="scoped_readonly_inject"
    )
    assert projected["pre_external"] is False
    assert projected["terminal"] == "HOLD"
    assert projected["final_order_envelope"]["envelope_identity"] == ""


@pytest.mark.parametrize("override", [None, True])
def test_standing_proof_cannot_override_current_hold(override):
    proof = prove_standing_supervisor_from_runtime_session_v1(
        _case(), pre_external_reached=override
    )
    assert not proof.continuous_n1_pre_external
    assert not proof.ok


def test_historical_entry_labels_cannot_close_bilateral_convergence():
    proof = prove_wp03_golden_convergence_v1(
        long_result=_case(),
        short_result=_case(historical="enter_short"),
        hold_result=_case(historical=""),
        two_epoch_result=_case(historical=""),
    )
    assert not proof.ok
    assert not proof.scenarios[0].pre_external_reached
    assert not proof.scenarios[1].pre_external_reached


def _completed_case(*, short=False, outcome=None, reduce_only=False):
    from tests.governance.test_canonical_order_intent_v1 import _intent, _instrument

    result = _case(historical="opposite-or-stale-label")
    result.trace.terminal_disposition = "PRE_EXTERNAL_EFFECT"
    orch = result.policy_result.orchestrator_result
    orch.disposition = "PRE_EXTERNAL_EFFECT"
    last = orch.cycle_records[-1]
    last.s5_disposition = "PRE_EXTERNAL_EFFECT"
    close = None
    if outcome == "exit":
        from tests.ops.test_current_productive_position_management_quantity_handoff_v1 import (
            _case as close_case,
        )
        from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
            compose_position_management_full_close_intent_v1,
        )

        close_args = close_case(side="long" if short else "short", action="exit")
        from trading.master_v2.double_play_entry_exit_policy_v0 import (
            ReconciliationState,
            PositionState,
        )

        close_args[
            "replay"
        ].intermediate.entry_exit_decision.reconciliation_state = ReconciliationState.RECONCILED
        close_args[
            "replay"
        ].intermediate.entry_exit_decision.position_state = PositionState.OPEN_FULL
        close_args["replay"].intermediate.canonical_order_intent = None
        from trading.master_v2.replay_execution_safety_contract_v1 import ReplayExecutionSafetyV1

        close_args["replay"].replay_execution_safety = ReplayExecutionSafetyV1(
            entry_blocked=False,
            emergency_boundary_active=False,
            emergency_mode=None,
            flatten_only=False,
            reduce_only=False,
            cancel_only=False,
            reason_codes=(),
            source_refs=("safety:" + "ab" * 32,),
        )
        close = compose_position_management_full_close_intent_v1(**close_args)
        intent = close.canonical_intent
        assert intent is not None, close.reason_codes
        result.trace.bound_instrument_id = intent.instrument_id
        result.trace.venue_native_id = close.quantity_handoff.venue_native_id
    else:
        intent = _intent(
            intent_action="ENTER_SHORT" if short else "ENTER_LONG",
            sizing_overrides={
                "instrument_id": result.trace.bound_instrument_id,
                "instrument": _instrument(instrument_id=result.trace.bound_instrument_id),
                "protective_stop_price": Decimal("2100" if short else "1900"),
            },
        )
    last.canonical_order_intent = intent
    last.final_order_envelope = build_final_order_envelope_v1(
        instrument_id=result.trace.venue_native_id,
        side="sell" if short else "buy",
        order_type="market",
        quantity=str(intent.quantity),
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=reduce_only,
        client_order_id="observation-unit-plan",
        venue_plan_clordid="observation-unit-plan",
        path_kind="observation-port-unit-case",
        quantity_source="explicit-unit-input",
        side_source="explicit-unit-input",
        instrument_source="explicit-unit-input",
        admission_ref="unit-admission-ref",
        provenance_ref="unit-provenance-ref",
        creation_epoch="unit-creation-epoch",
    )
    if close is not None:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
            PositionManagementExecutionHandoffV1,
        )

        last.final_order_envelope = replace(
            last.final_order_envelope, provenance_ref=intent.semantic_digest
        )
        from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
            compute_final_order_envelope_digest_v1,
        )

        digest = compute_final_order_envelope_digest_v1(
            last.final_order_envelope.to_canonical_payload_v1()
        )
        last.final_order_envelope = replace(
            last.final_order_envelope, envelope_id=f"env-{digest[:32]}", envelope_digest=digest
        )
        last.position_management_execution_handoff = PositionManagementExecutionHandoffV1(
            close, last.final_order_envelope
        )
    last.envelope_created = True
    last.envelope_identity = (
        f"envelope_id={last.final_order_envelope.envelope_id};"
        f"digest={last.final_order_envelope.envelope_digest}"
    )
    last.pending_decision_context = PendingDecisionContextV1(
        cycle_id="actual-unit-core-cycle",
        instrument_id=result.trace.bound_instrument_id,
        native_id=result.trace.venue_native_id,
        decision_timestamp_unix=last.c1_venue_event_time + 1,
        reference_price=100.0,
        market_context_ref="unit-original-context",
        canonical_decision_id=intent.decision_id,
        producer_payload_json=json.dumps(
            {
                "instrument_id": result.trace.bound_instrument_id,
                "decision_outcome": outcome or ("enter_short" if short else "enter_long"),
                "selected_side": "short" if short else "long",
                "trading_epoch": intent.trading_epoch,
                "reduce_only": outcome == "exit",
            }
        ),
    )
    return result


@pytest.mark.parametrize(
    "fault",
    [
        "opposite-core",
        "hold-core",
        "reduce-only-entry",
        "missing-intent",
        "intent-parent",
        "intent-quantity",
        "intent-epoch",
        "intent-side",
        "exit-without-close",
    ],
)
def test_decision_intent_envelope_contradictions_are_not_boundary_evidence(fault):
    result = (
        _completed_case(outcome="exit", reduce_only=True)
        if fault == "exit-without-close"
        else _completed_case()
    )
    last = result.policy_result.orchestrator_result.cycle_records[-1]
    if fault in {"opposite-core", "hold-core", "reduce-only-entry"}:
        payload = json.loads(last.pending_decision_context.producer_payload_json)
        if fault == "opposite-core":
            payload.update(decision_outcome="enter_short", selected_side="short")
        elif fault == "hold-core":
            payload["decision_outcome"] = "hold"
        else:
            payload["reduce_only"] = True
        last.pending_decision_context = replace(
            last.pending_decision_context, producer_payload_json=json.dumps(payload)
        )
    elif fault == "missing-intent":
        last.canonical_order_intent = None
    elif fault == "intent-parent":
        last.pending_decision_context = replace(
            last.pending_decision_context, canonical_decision_id="foreign-decision"
        )
    elif fault == "exit-without-close":
        last.position_management_execution_handoff = None
    else:
        from src.governance.canonical_order_intent_v1 import compute_semantic_digest

        changes = {
            "intent-quantity": {"quantity": last.canonical_order_intent.quantity + 1},
            "intent-epoch": {"trading_epoch": "foreign-epoch"},
            "intent-side": {"side": "SHORT"},
        }[fault]
        intent = replace(last.canonical_order_intent, **changes)
        last.canonical_order_intent = replace(
            intent, semantic_digest=compute_semantic_digest(intent)
        )
    assert not current_runtime_boundary_evidence_v1(result).reached
    projected = project_supervisor_golden_trace_v1(
        result, side="HOLD", observation_scope="unit-test-port"
    )
    assert projected["terminal"] == "UNPROVEN"


@pytest.mark.parametrize("short", [False, True])
def test_current_output_uses_original_envelope_and_direction(short):
    result = _completed_case(short=short)
    projected = project_supervisor_golden_trace_v1(
        result, side="LONG" if short else "SHORT", observation_scope="unit-test-port"
    )
    assert projected["pre_external"]
    assert projected["side"] == ("SHORT" if short else "LONG")
    assert projected["final_order_envelope"]["envelope_identity"] == (
        result.policy_result.orchestrator_result.cycle_records[-1].final_order_envelope.envelope_id
    )
    assert projected["final_order_envelope"]["envelope_identity"] != "current-cycle-1"
    assert prove_standing_supervisor_from_runtime_session_v1(result).ok
    assert not prove_standing_supervisor_from_runtime_session_v1(
        result, pre_external_reached=False
    ).ok


def test_hold_label_cannot_hide_actual_pre_external():
    projected = project_supervisor_golden_trace_v1(
        _completed_case(), side="HOLD", observation_scope="unit-test-port"
    )
    assert projected["pre_external"]
    assert projected["terminal"] == "PRE_EXTERNAL"


def test_opposite_current_entries_do_not_satisfy_expected_scenarios():
    proof = prove_wp03_golden_convergence_v1(
        long_result=_completed_case(short=True),
        short_result=_completed_case(short=False),
        hold_result=_case(historical=""),
        two_epoch_result=_case(historical=""),
    )
    assert not proof.ok
    assert not proof.scenarios[0].golden_compare.ok
    assert not proof.scenarios[1].golden_compare.ok


@pytest.mark.parametrize(
    "times,expected",
    [
        (None, False),
        ((), False),
        ((1000.0, 1060.0), True),
        ((1000.0, 1120.0), False),
        ((1000.0, 1000.0), False),
        ((1060.0, 1000.0), False),
        ((float("nan"), 1060.0), False),
        ((1000.0,), False),
    ],
)
def test_confirmation_requires_actual_contiguous_event_times(times, expected):
    assert (
        prove_contiguous_confirmation_epochs_v1(
            accepted_c1_count=2, governed_cycle_count=2, observed_event_times=times
        )
        is expected
    )


@pytest.mark.parametrize("fault", ["missing-hold", "missing-two-policy", "two-time-gap"])
def test_convergence_requires_observed_hold_and_two_epoch_consumption(fault):
    hold = _case(historical="")
    two = _case(historical="")
    if fault == "missing-hold":
        hold.policy_result = None
    elif fault == "missing-two-policy":
        two.policy_result = None
    else:
        orch = two.policy_result.orchestrator_result
        orch.cycle_records[-1].c1_venue_event_time = 1120.0
        orch.last_accepted_c1 = orch.cursor_floor_after = 1120.0
    proof = prove_wp03_golden_convergence_v1(
        long_result=_completed_case(),
        short_result=_completed_case(short=True),
        hold_result=hold,
        two_epoch_result=two,
    )
    assert not proof.ok
    if fault != "missing-hold":
        assert not proof.confirmation_two_epoch_proven


@pytest.mark.parametrize(
    "outcome,reduce_only,expected",
    [
        ("enter_long", False, False),
        ("exit", False, False),
        ("exit", True, True),
    ],
)
def test_exit_gate_requires_current_exit_and_reduce_only(outcome, reduce_only, expected):
    from dataclasses import fields
    from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.done_gate_v1 import (
        evaluate_current_n1_endgame_done_gate_v1,
    )
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
        PreExternalAutonomyAdmissionV1,
    )

    # Isolate EXIT evidence while explicitly supplying the unrelated admission
    # ports. This does not attest an integrated account/exit/restart.
    inputs = {field.name: True for field in fields(PreExternalAutonomyAdmissionV1)}
    inputs.update(
        post_count=0,
        post_allowed=False,
        external_effect_authorized=False,
        real_venue_post_allowed=False,
    )
    scenario = SimpleNamespace(pre_external_reached=True, golden_compare=SimpleNamespace(ok=True))
    gate = evaluate_current_n1_endgame_done_gate_v1(
        admission=PreExternalAutonomyAdmissionV1(**inputs),
        wp03=SimpleNamespace(
            scenarios=(scenario, scenario, scenario), confirmation_two_epoch_proven=True, ok=True
        ),
        reference_supervisor_run=_completed_case(outcome=outcome, reduce_only=reduce_only),
        ci_snapshot=SimpleNamespace(recorded=True, all_required_ci_green_at_admission=False),
    )
    assert gate.EXIT_PATH_VALID is expected


@pytest.mark.parametrize(
    "fault",
    [
        "missing-records",
        "missing-policy",
        "trace-terminal",
        "s5-terminal",
        "trace-count",
        "owner-go",
        "post",
        "permit",
        "external-effect",
        "cursor",
        "missing-envelope",
        "envelope-digest",
        "envelope-identity",
        "envelope-instrument",
        "missing-decision",
        "decision-native",
        "decision-instrument",
        "decision-before-c1",
        "decision-nan",
        "decision-json",
        "earlier-pre-external",
        "missing-envelope-identity",
        "duplicate-cycle",
        "duplicate-event",
        "invalid-earlier-s5",
    ],
)
def test_conflicting_or_missing_current_outputs_stay_unproven(fault):
    result = _completed_case()
    orch = result.policy_result.orchestrator_result
    last = orch.cycle_records[-1]
    if fault == "missing-records":
        orch.cycle_records = ()
    elif fault == "missing-policy":
        result.policy_result = None
    elif fault == "trace-terminal":
        result.trace.terminal_disposition = "MAX_CYCLES_BOUND_STOP"
    elif fault == "s5-terminal":
        last.s5_disposition = "HOLD_CLOSED"
    elif fault == "trace-count":
        result.trace.governed_cycle_count += 1
    elif fault == "owner-go":
        result.owner_go_consumed = False
    elif fault == "post":
        orch.post_count = 1
    elif fault == "permit":
        orch.permit_created = True
    elif fault == "external-effect":
        result.policy_result.external_effect_authorized = True
    elif fault == "cursor":
        orch.cursor_floor_after -= 60
    elif fault == "missing-envelope":
        last.final_order_envelope = None
    elif fault == "envelope-digest":
        last.final_order_envelope = replace(last.final_order_envelope, quantity="99")
    elif fault == "envelope-identity":
        last.envelope_identity = "foreign-envelope"
    elif fault == "envelope-instrument":
        result.trace.bound_instrument_id = "foreign-instrument"
    elif fault == "missing-decision":
        last.pending_decision_context = None
    elif fault == "decision-native":
        last.pending_decision_context = replace(
            last.pending_decision_context, native_id="foreign-native"
        )
    elif fault == "decision-instrument":
        last.pending_decision_context = replace(
            last.pending_decision_context, instrument_id="foreign-canonical"
        )
    elif fault == "decision-before-c1":
        last.pending_decision_context = replace(
            last.pending_decision_context, decision_timestamp_unix=1
        )
    elif fault == "decision-nan":
        last.pending_decision_context = replace(
            last.pending_decision_context, decision_timestamp_unix=float("nan")
        )
    elif fault == "decision-json":
        last.pending_decision_context = replace(
            last.pending_decision_context, producer_payload_json="{}"
        )
    elif fault == "earlier-pre-external":
        orch.cycle_records[0].s5_disposition = "PRE_EXTERNAL_EFFECT"
    elif fault == "missing-envelope-identity":
        del last.envelope_identity
    elif fault == "duplicate-cycle":
        orch.cycle_records[0].cycle_instance_id = last.cycle_instance_id
    elif fault == "duplicate-event":
        orch.cycle_records[0].c1_venue_event_time = last.c1_venue_event_time
    elif fault == "invalid-earlier-s5":
        orch.cycle_records[0].s5_disposition = "FAIL_CLOSED"
    assert not current_runtime_boundary_evidence_v1(result).reached
