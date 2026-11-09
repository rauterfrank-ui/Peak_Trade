"""Original reconciled closing evidence releases exactly one bounded slot."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1 as lifecycle,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    execute_current_productive_treasury_single_source_capital_handoff_v1 as capital_handoff,
    build_full_core_margin_inputs_from_budget_owner_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from tests.ops.test_current_productive_post_close_feedback_v1 import (
    _case,
    isolated_capital_observation_ordering as isolated_capital_observation_ordering,
)
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _auto
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _produce, _obs
from tests.ops.test_current_mf_n5_isolated_lane_instance_topology_v1 import _five_ranking, _cid
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)

EPOCH = "2026-11-03T00:00:00Z"
FRESH = "2026-11-03T00:00:04Z"
T0 = 1793664000.0


def closing_case(
    tmp_path,
    monkeypatch,
    *,
    count=5,
    capital="125",
    remaining="0",
    commit_target=True,
    lane_id="LANE_1",
):
    ranking = _five_ranking()
    natives = [c["venue_native_id"] for c in ranking["ranked_candidates"]][:count]
    target_native = natives[int(lane_id.split("_")[1]) - 1]
    target_bound = replace(
        _bound(),
        instrument_id=_cid(ranking, target_native),
        venue_native_id=target_native,
        universe_snapshot_id=ranking["universe_snapshot_id"],
    )
    args, memory, _, _ = _case(
        monkeypatch,
        state="filled" if remaining == "0" else "partially_filled",
        remaining=remaining,
        lane_id=lane_id,
        initial_ranking=ranking,
        bound_instrument=target_bound,
    )
    request = args["post_close_feedback_request"]
    memory.close()
    bound = request.bound_instrument
    bindings = {
        f"LANE_{i}": replace(
            bound,
            instrument_id=_cid(ranking, natives[i - 1]),
            venue_native_id=natives[i - 1],
            selection_id=f"selection-{i}",
        )
        for i in range(1, count + 1)
    }
    bindings[lane_id] = bound
    owner = Owner(
        durable_root=tmp_path / "owner",
        durable_account_identity="acct-1",
        durable_mode="create",
        durable_lane_bindings=bindings,
        entry_budget_policy=policy(),
    )
    admitted = _auto(
        owner,
        tmp_path,
        output=_produce(value="125", epoch=EPOCH),
        observed=PortfolioTruthSnapshotV1(event_time_unix=T0, wall_time_unix=T0, max_age_seconds=5),
        bindings=bindings,
        now=T0,
    )
    assert admitted.disposition.value == "ADMITTED", admitted.reason_codes
    observation = owner.budget_state_v1().observation_id
    held = {}
    for lane in bindings:
        reservation = owner.try_reserve_v1(
            slot_id=lane,
            decision_id="entry:" + lane,
            cycle_id="entry",
            observation_id=observation,
            amount=Decimal(25),
        ).reservation
        held[lane] = str(reservation.reservation_id)
        if lane != lane_id or commit_target:
            owner.commit_internal_pre_external_effect_v1(held[lane])
    body = json.dumps(
        {"synthetic_available_usdc": capital, "observed_at": FRESH, "account": "acct-1"},
        sort_keys=True,
    )
    margin = replace(
        _obs(value=capital, epoch=FRESH),
        provenance_digest=hashlib.sha256(body.encode()).hexdigest(),
    )
    handoff = capital_handoff(
        margin_observation=margin,
        instrument_id=bound.instrument_id,
        body_sha256=margin.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=owner
        ),
    )
    assert not handoff.fail_closed, handoff.reason_codes
    args["post_close_feedback_request"] = replace(
        request,
        observed_at_utc=FRESH,
        capital_handoff=handoff,
        budget_owner=owner,
        closed_reservation_ids=(held[lane_id],),
        expected_budget_observation_id=observation,
    )
    return args, owner, held, bindings


@pytest.mark.parametrize(
    ("count", "lane_id"), [(2, "LANE_1"), (2, "LANE_2")] + [(5, f"LANE_{i}") for i in range(1, 6)]
)
def test_confirmed_slot_close_preserves_other_original_holds_and_replay_cannot_free_new_entry(
    tmp_path, monkeypatch, count, lane_id
):
    args, owner, held, bindings = closing_case(tmp_path, monkeypatch, count=count, lane_id=lane_id)
    try:
        before = owner.risk_snapshot_v1()["state"]
        feedback = lifecycle(**args).post_close_feedback
        assert feedback.capital_refresh.disposition.value == "ADMITTED", feedback.reason_codes
        assert owner.active_slot_sum_v1(lane_id) == 0
        assert owner.active_sum_v1() == Decimal(25) * (count - 1)
        after = owner.risk_snapshot_v1()["state"]

        def others(state):
            return {
                r["reservation_id"]: r for r in state["reservations"] if r["slot_id"] != lane_id
            }

        assert others(after) == others(before)
        assert after["lane_bindings"] == before["lane_bindings"]
        assert after["execution_links"] == before["execution_links"]
        new = owner.try_reserve_v1(
            slot_id=lane_id,
            decision_id="next-entry",
            cycle_id="next",
            observation_id=owner.budget_state_v1().observation_id,
            amount=Decimal(25),
        )
        assert new.disposition.value == "ADMITTED"
        snapshot = owner.risk_snapshot_v1()
        replay = lifecycle(**args).post_close_feedback
        assert replay.capital_refresh.disposition.value == "IDEMPOTENT_REPLAY"
        assert owner.risk_snapshot_v1() == snapshot
        owner.close()
        cold = Owner(
            durable_root=tmp_path / "owner",
            durable_account_identity="acct-1",
            durable_mode="recover",
            durable_lane_bindings=bindings,
        )
        try:
            assert not cold.budget_state_v1().admitted and cold.budget_state_v1().recovery_required
            assert cold.active_sum_v1() == Decimal(25) * count
            assert cold.risk_snapshot_v1()["state"] == snapshot["state"]
        finally:
            cold.close()
    finally:
        owner.close()


@pytest.mark.parametrize(
    "fault",
    [
        "foreign-id",
        "missing-id",
        "uncommitted",
        "wrong-bound",
        "replay-wrong-slot",
        "partial",
        "capital-below-other-holds",
    ],
)
def test_unproven_slot_release_preserves_all_holds(tmp_path, monkeypatch, fault):
    args, owner, held, bindings = closing_case(
        tmp_path,
        monkeypatch,
        capital="75" if fault == "capital-below-other-holds" else "125",
        remaining="0.4" if fault == "partial" else "0",
        commit_target=fault != "uncommitted",
    )
    try:
        request = args["post_close_feedback_request"]
        if fault == "foreign-id":
            request = replace(request, closed_reservation_ids=(held["LANE_1"], held["LANE_2"]))
        if fault == "missing-id":
            request = replace(request, closed_reservation_ids=())
        if fault == "wrong-bound":
            request = replace(
                request, bound_instrument=replace(bindings["LANE_1"], selection_id="foreign")
            )
        if fault == "uncommitted":
            assert (
                next(
                    r
                    for r in owner.risk_snapshot_v1()["state"]["reservations"]
                    if r["reservation_id"] == held["LANE_1"]
                )["state"]
                == "RESERVED"
            )
        if fault == "replay-wrong-slot":
            assert (
                lifecycle(**args).post_close_feedback.capital_refresh.disposition.value
                == "ADMITTED"
            )
            result = owner.refresh_after_reconciled_flat_v1(
                output=request.capital_handoff.producer_output,
                slot_id="LANE_2",
                reservation_ids=(held["LANE_2"],),
                expected_observation_id=request.expected_budget_observation_id,
                account_identity="acct-1",
                close_evidence_ref=request.execution.envelope.envelope_digest,
                bound_instrument=bindings["LANE_2"],
            )
            assert result.disposition.value == "FAIL_CLOSED" and result.reason_codes == (
                "CLOSE_REFRESH_REPLAY_CONFLICT",
            )
            assert owner.active_slot_sum_v1("LANE_2") == 25
            return
        args["post_close_feedback_request"] = request
        before = owner.risk_snapshot_v1()["state"]
        result = lifecycle(**args).post_close_feedback
        assert (
            result.capital_refresh is None
            or result.capital_refresh.disposition.value == "FAIL_CLOSED"
        )
        assert owner.risk_snapshot_v1()["state"] == before
        if fault == "capital-below-other-holds":
            assert (
                not owner.budget_state_v1().admitted and owner.budget_state_v1().recovery_required
            )
    finally:
        owner.close()


def test_old_close_replay_after_original_rebinding_never_rewrites_new_generation(
    tmp_path, monkeypatch
):
    args, owner, held, bindings = closing_case(tmp_path, monkeypatch)
    try:
        assert lifecycle(**args).post_close_feedback.capital_refresh.disposition.value == "ADMITTED"
        next_bindings = {
            **bindings,
            "LANE_1": replace(bindings["LANE_1"], selection_id="explicit-next-generation"),
        }
        result = _auto(
            owner,
            tmp_path,
            output=args["post_close_feedback_request"].capital_handoff.producer_output,
            observed=PortfolioTruthSnapshotV1(
                event_time_unix=T0 + 4, wall_time_unix=T0 + 4, max_age_seconds=5
            ),
            bindings=next_bindings,
            now=T0 + 4,
        )
        assert result.disposition.value == "ADMITTED", result.reason_codes
        before = owner.risk_snapshot_v1()
        assert (
            lifecycle(**args).post_close_feedback.capital_refresh.disposition.value
            == "IDEMPOTENT_REPLAY"
        )
        assert owner.risk_snapshot_v1() == before
    finally:
        owner.close()


@pytest.mark.parametrize("lane_id", [f"LANE_{i}" for i in range(1, 6)])
@pytest.mark.parametrize(
    "fault",
    [
        "wrong-fill",
        "missing-flat",
        "old-position",
        "stale-capital",
        "foreign-reservation",
        "foreign-fill",
        "foreign-capital-claim",
    ],
)
def test_every_slot_requires_its_own_fill_flat_chronology_and_fresh_capital(
    tmp_path, monkeypatch, lane_id, fault
):
    args, owner, held, bindings = closing_case(tmp_path, monkeypatch, lane_id=lane_id)
    try:
        fixture = args["offline_fixture"]
        request = args["post_close_feedback_request"]
        other = next(l for l in bindings if l != lane_id)
        if fault == "wrong-fill":
            fixture.order_history["data"][0]["accFillSz"] = "0.6"
        if fault == "missing-flat":
            args["offline_fixture"] = replace(fixture, positions={"code": "0", "data": []})
        if fault == "old-position":
            fixture.positions["data"][0]["uTime"] = "1793663999000"
        if fault == "stale-capital":
            args["post_close_feedback_request"] = replace(
                request, observed_at_utc="2026-11-03T00:00:20Z"
            )
        if fault == "foreign-reservation":
            args["post_close_feedback_request"] = replace(
                request, closed_reservation_ids=(held[other],)
            )
        if fault == "foreign-fill":
            fixture.order_history["data"][0]["instId"] = bindings[other].venue_native_id
        if fault == "foreign-capital-claim":
            handoff = request.capital_handoff
            foreign = bindings[other].instrument_id
            args["post_close_feedback_request"] = replace(
                request,
                capital_handoff=replace(
                    handoff,
                    step_29p_claim=replace(
                        handoff.step_29p_claim,
                        expected_instrument_id=foreign,
                        observed_instrument_id=foreign,
                    ),
                    capital_admission=replace(
                        handoff.capital_admission,
                        expected_instrument_id=foreign,
                        observed_instrument_id=foreign,
                    ),
                ),
            )
        before = owner.risk_snapshot_v1()
        result = lifecycle(**args).post_close_feedback
        assert (
            result.capital_refresh is None
            or result.capital_refresh.disposition.value == "FAIL_CLOSED"
        ), result.reason_codes
        assert owner.risk_snapshot_v1() == before
    finally:
        owner.close()
