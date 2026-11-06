"""Actual existing close feedback → durable owner → fresh recovery; injected only."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

import pytest

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from tests.ops.test_current_productive_post_close_feedback_v1 import _case, NOW
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _auto
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _produce

EPOCH = "2026-11-03T00:00:00Z"


def _durable_case(tmp_path, monkeypatch, **changes):
    args, old_owner, _, old_instrument = _case(monkeypatch, **changes)
    request = args["post_close_feedback_request"]
    old_owner.close()
    bound = request.bound_instrument
    bindings = {"LANE_1": bound}
    owner = Owner(
        durable_root=tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="create",
        durable_lane_bindings=bindings,
    )
    now = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
    observed = PortfolioTruthSnapshotV1(
        source_id="injected-pre-entry", event_time_unix=now, wall_time_unix=now, max_age_seconds=5
    )
    admitted = _auto(
        owner, tmp_path, output=_produce(epoch=EPOCH), observed=observed, bindings=bindings, now=now
    )
    assert admitted.disposition.value == "ADMITTED"
    observation_id = owner.budget_state_v1().observation_id
    held = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="original-entry",
        cycle_id="entry-cycle",
        observation_id=observation_id,
        amount=Decimal("40"),
    )
    rid = str(held.reservation.reservation_id)
    owner.commit_internal_pre_external_effect_v1(rid)
    args["post_close_feedback_request"] = replace(
        request,
        budget_owner=owner,
        closed_reservation_ids=(rid,),
        expected_budget_observation_id=observation_id,
    )
    return args, owner, bindings, old_instrument


@pytest.mark.parametrize("replace_member", [False, True])
def test_verified_close_refresh_and_replay_survive_durable_restart(
    tmp_path, monkeypatch, replace_member
):
    args, owner, bindings, original = _durable_case(
        tmp_path, monkeypatch, replace_member=replace_member
    )
    try:
        result = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**args)
        feedback = result.post_close_feedback
        assert feedback.position.venue_flat
        assert feedback.capital_refresh.disposition.value == "ADMITTED", feedback.reason_codes
        assert owner.active_sum_v1() == 0
        assert owner.budget_state_v1().canonical_available_capital == 75
        assert (original in feedback.membership_review.ordered_membership) is (not replace_member)
        assert feedback.membership_review.persisted_artifact is None
        assert not result.post_submit_join.resubmit_allowed
    finally:
        owner.close()
    restored = Owner(
        durable_root=tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings=bindings,
    )
    try:
        assert not restored.budget_state_v1().admitted
        assert restored.active_sum_v1() == 0
        request = args["post_close_feedback_request"]
        args["post_close_feedback_request"] = replace(request, budget_owner=restored)
        replay = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            **args
        ).post_close_feedback
        assert replay.capital_refresh.disposition.value == "IDEMPOTENT_REPLAY"
        assert not restored.budget_state_v1().admitted  # replay never bypasses recovery
        now = datetime.fromisoformat(NOW.replace("Z", "+00:00")).timestamp()
        observed = PortfolioTruthSnapshotV1(
            source_id="injected-confirmed-flat",
            event_time_unix=now,
            wall_time_unix=now,
            max_age_seconds=5,
        )
        recovered = _auto(
            restored,
            tmp_path,
            output=request.capital_handoff.producer_output,
            observed=observed,
            bindings=bindings,
            now=now,
        )
        assert recovered.disposition.value == "ADMITTED", recovered.reason_codes
        assert restored.budget_state_v1().canonical_available_capital == 75
        assert restored.active_sum_v1() == 0
    finally:
        restored.close()


def test_partial_close_keeps_durable_capital_and_custody(tmp_path, monkeypatch):
    args, owner, _, _ = _durable_case(
        tmp_path, monkeypatch, state="partially_filled", remaining="0.4"
    )
    try:
        before = owner.budget_state_v1()
        feedback = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
            **args
        ).post_close_feedback
        assert feedback.status == "POSITION_REMAINS_OPEN"
        assert not feedback.ranking_review_allowed
        assert feedback.capital_refresh is None
        assert owner.budget_state_v1() == before
        assert owner.active_sum_v1() == 40
    finally:
        owner.close()
