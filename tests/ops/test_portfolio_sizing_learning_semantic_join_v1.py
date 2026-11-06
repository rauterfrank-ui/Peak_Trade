"""Actual internal sizing/reserve/replay/envelope joins, without budget policy."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import signal
import subprocess
import time

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    ReserveDispositionV1 as D,
    admit_sized_slot_reservation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1.current_productive_entry_budget_policy_v1 import (
    EntryBudgetPolicyV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
    reconcile_durable_budget_startup_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PPortfolioSlotContextV1 as Slot,
    join_current_productive_enter_live_29p_before_venue_plan_v1 as join,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_learning_capture_join_v1 import (
    build_productive_ddo_capture_binding_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    bind_capture_session_v0,
    reset_capture_session_v0,
    record_productive_cycle_capture_v0,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _balance_payload,
    _bound,
    _enter_replay,
    _host_enter_cycle,
    _injected,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
    ACCOUNT,
    _obs,
    _p01,
    _eligibility,
    _sizing_input,
    _produce,
)


def _join(owner, replay, cycle="repeatable", injected=None):
    return join(
        replay=replay,
        bound_instrument=_bound(),
        decision_epoch=EPOCH,
        injected=injected or _injected(payload=_balance_payload(avail_eq="100.00")),
        portfolio_budget_owner=owner,
        portfolio_slot=Slot(
            slot_id="LANE_1", decision_id=str(replay.evidence.decision_id), cycle_id=cycle
        ),
        # Isolated regression ceiling for the original 60+40 retry defect.
        # This is an Ops test input, never a fictitious DP account balance.
        entry_budget_policy=EntryBudgetPolicyV1(
            "retry-regression-only", 1, Decimal(100), Decimal(100)
        ),
    )


def _held_before_entry(owner, replay):
    seed = _join(owner, replay, "seed")
    assert seed.status == "PASS"
    owner.cancel_before_external_effect_v1(seed.portfolio_reservation_id)
    owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="prior-obligation",
        cycle_id="prior",
        observation_id=owner.budget_state_v1().observation_id,
        amount=Decimal(60),
    )


def test_retry_preserves_sized_amount_provenance_intent_envelope_and_learning(tmp_path):
    _, cycle, _ = _host_enter_cycle()
    replay = _enter_replay(cycle)
    assert replay is cycle.replay  # Require the actual natural ENTER, no test outcome overlay.
    owner = Owner()
    _held_before_entry(owner, replay)
    binding = build_productive_ddo_capture_binding_v1(ledger_path=tmp_path / "ddo.jsonl")
    summary = record_productive_cycle_capture_v0(
        binding,
        repository_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
        session_id="budget-semantics",
        cycle_index=1,
        event_ts_unix=datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp(),
        replay=replay,
    )
    assert summary["ok"] is True
    initial_learning = binding.ledger_path.read_bytes()
    first = _join(owner, replay)
    repeated = _join(owner, replay)
    assert first.status == repeated.status == "PASS"
    assert repeated.portfolio_reservation_disposition == "IDEMPOTENT_REPLAY"
    first_sizing = first.replay.intermediate.capital_risk_sizing_decision
    retry_sizing = repeated.replay.intermediate.capital_risk_sizing_decision
    assert first_sizing == retry_sizing
    assert first.replay.evidence == repeated.replay.evidence
    assert (
        first.replay.intermediate.canonical_order_intent
        == repeated.replay.intermediate.canonical_order_intent
    )
    held = owner.lookup_v1(
        slot_id="LANE_1",
        decision_id=str(replay.evidence.decision_id),
        cycle_id="repeatable",
        observation_id=owner.budget_state_v1().observation_id,
    )
    assert held.amount == retry_sizing.canonical_position_sizing.resulting_notional < 40
    for field in (
        "decision_id",
        "replay_id",
        "instrument_id",
        "selected_side",
        "decision_outcome",
        "scope_event_ref",
        "state_switch_ref",
        "entry_exit_policy_ref",
    ):
        assert getattr(replay.evidence, field) == getattr(repeated.replay.evidence, field)
    envelopes = []
    for result in (first, repeated):
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=result.replay,
            bound_instrument=_bound(),
            session_id="same-session",
            run_id="same-run",
            composed_epoch=EPOCH,
            execution_mode="LIVE",
        )
        assert status.value == "PASS", reasons
        envelopes.append(
            bind_final_order_envelope_from_venue_plan_v1(
                plan,
                admission_ref="offline-join-proof",
                provenance_ref="canonical-sizing",
                creation_epoch=EPOCH,
            )
        )
    assert envelopes[0] == envelopes[1]
    assert Decimal(envelopes[1].quantity) == retry_sizing.final_quantity
    # A replay of frozen decision state must not be emitted as a new risk decision.
    risk_observations_before = [
        r for r in binding.captured_records if r.get("producer_id") == "capital_risk_sizing_v1"
    ]
    token = bind_capture_session_v0(binding)
    try:
        assert _join(owner, replay).status == "PASS"
    finally:
        reset_capture_session_v0(token)
    # Other decorated producers may add observations when explicitly enabled;
    # the preexisting ledger bytes remain an immutable prefix.
    assert binding.ledger_path.read_bytes().startswith(initial_learning)
    assert [
        r for r in binding.captured_records if r.get("producer_id") == "capital_risk_sizing_v1"
    ] == risk_observations_before
    assert first.post_count == repeated.post_count == "0"
    assert first.permit_created == repeated.permit_created == "false"


def _admit(owner, request):
    return admit_sized_slot_reservation_v1(
        owner,
        observation=_obs(),
        p01=_p01(),
        eligibility=_eligibility(),
        slot_id="LANE_1",
        decision_id=request.decision_id,
        cycle_id="cycle",
        instrument_id=request.instrument_id,
        account_identity=ACCOUNT,
        sizing_input=request,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )


@pytest.mark.parametrize("change", ["price", "policy", "units", "released", "raw_hold"])
def test_incompatible_sizing_context_or_unproven_hold_cannot_replay(tmp_path, change):
    owner = Owner()
    request = _sizing_input()
    original = _admit(owner, request)
    assert original.disposition is D.ADMITTED
    if change == "price":
        request = replace(request, reference_price=Decimal(101))
    elif change == "policy":
        request = replace(request, scope_capital_limit=Decimal(25), policy_version="future-policy")
    elif change == "units":
        request = replace(
            request, instrument=replace(request.instrument, contract_multiplier=Decimal(2))
        )
    elif change == "released":
        owner.cancel_before_external_effect_v1(str(original.reservation.reservation_id))
    else:
        # Low-level holds intentionally have no acknowledged canonical sizing.
        owner = Owner()
        owner.bind_canonical_producer_output_v1(_produce())
        owner.try_reserve_v1(
            slot_id="LANE_1",
            decision_id=request.decision_id,
            cycle_id="cycle",
            observation_id=owner.budget_state_v1().observation_id,
            amount=original.reservation.amount,
        )
    held_before = owner.active_sum_v1()
    denied = _admit(owner, request)
    assert denied.disposition is D.FAIL_CLOSED
    assert denied.sizing_decision is None
    assert owner.active_sum_v1() == held_before


def test_durable_recovery_restores_original_sizing_without_new_learning_or_recalculation(
    tmp_path, monkeypatch
):
    bound = replace(_bound(), instrument_id="ETH-USD-PERP")
    bindings = {"LANE_1": bound}

    def open_owner(mode):
        return Owner(
            durable_root=tmp_path / "budget",
            durable_account_identity=ACCOUNT,
            durable_mode=mode,
            durable_lane_bindings=bindings,
        )

    def recover(owner):
        now = datetime.fromisoformat("2026-09-15T12:03:00+00:00").timestamp()
        return reconcile_durable_budget_startup_v1(
            owner,
            output=_produce(),
            observed=PortfolioTruthSnapshotV1(
                event_time_unix=now,
                wall_time_unix=now,
                max_age_seconds=5,
            ),
            lane_bindings=bindings,
            reconciliation_state_root=tmp_path / "recon",
            session_id="offline",
            repository_sha="242b7974fc93f0bdb47706556101bd6f0c497414",
            now_unix=now,
            capital_max_age_seconds=5,
        )

    owner = open_owner("create")
    assert recover(owner).disposition is D.ADMITTED
    request = _sizing_input()
    admitted = _admit(owner, request)
    assert admitted.disposition is D.ADMITTED
    original = admitted.sizing_decision
    owner.close()
    owner = open_owner("recover")
    try:
        assert not owner.budget_state_v1().admitted
        assert recover(owner).disposition is D.ADMITTED
        binding = build_productive_ddo_capture_binding_v1(
            ledger_path=tmp_path / "restore-learning.jsonl"
        )
        token = bind_capture_session_v0(binding)
        try:

            def forbidden_recalculation(*args, **kwargs):
                raise AssertionError("A held decision must not be sized again")

            monkeypatch.setattr(
                "src.ops.portfolio_capital_reservation_budget_v1.contract_v1.evaluate_capital_risk_sizing_v1",
                forbidden_recalculation,
            )
            repeated = _admit(owner, request)
        finally:
            reset_capture_session_v0(token)
        assert repeated.disposition is D.IDEMPOTENT_REPLAY
        assert repeated.sizing_decision == original
        assert repeated.reservation.amount == original.canonical_position_sizing.resulting_notional
        # Only a frozen result was loaded/reused; no new sizing observation exists.
        assert not [
            r for r in binding.captured_records if r.get("producer_id") == "capital_risk_sizing_v1"
        ]
    finally:
        owner.close()


def test_observer_mutation_cannot_change_frozen_sizing_state():
    owner = Owner()
    request = _sizing_input()
    first = _admit(owner, request)
    assert first.disposition is D.ADMITTED
    first.sizing_decision.scope_capital_envelope.daily_loss_state["observer-added"] = "changed"
    repeated = _admit(owner, request)
    assert "observer-added" not in repeated.sizing_decision.scope_capital_envelope.daily_loss_state
    repeated.sizing_decision.scope_capital_envelope.daily_loss_state["other-observer"] = "changed"
    third = _admit(owner, request)
    assert "other-observer" not in third.sizing_decision.scope_capital_envelope.daily_loss_state


def test_sigkill_restores_exact_sizing_and_provenance_in_a_new_process(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    command = [
        str(repo / "scripts/pt"),
        "-m",
        "tests.ops._durable_budget_crash_worker_v1",
        str(tmp_path),
    ]
    marker = tmp_path / "checkpoint"
    with (tmp_path / "stdout").open("w") as out, (tmp_path / "stderr").open("w") as err:
        child = subprocess.Popen([*command, "sized", "0"], cwd=repo, stdout=out, stderr=err)
        try:
            deadline = time.monotonic() + 20
            while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.03)
            assert marker.exists(), (tmp_path / "stderr").read_text()
            child.send_signal(signal.SIGKILL)
            child.wait(timeout=5)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=5)
    expected = json.loads((tmp_path / "first_sizing.json").read_text())
    after = subprocess.run(
        [*command, "recover_sized", "0"], cwd=repo, capture_output=True, text=True, timeout=20
    )
    assert after.returncode == 0, after.stdout + after.stderr
    result = json.loads(after.stdout.splitlines()[-1])
    assert result == expected
    assert Decimal(result["notional"]) == 40
    assert Decimal(result["held_sum"]) == 100
