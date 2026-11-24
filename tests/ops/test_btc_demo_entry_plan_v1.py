"""Original Core -> reserved 29P -> original TESTNET 29Q; no submit or network."""

import pytest

from src.ops.btc_demo_entry_plan_v1 import prepare_btc_demo_entry_plan_v1
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def _reserve(case):
    host, entry, reads, movement, instant, _ = case
    result, _ = host.reserve_testnet_entry_v1(
        entry=entry, reads=reads, movement_input=movement, clock=instant.timestamp
    )
    return host, entry, instant, result.reservation.reservation_id


def test_original_sized_plan_keeps_testnet_and_core_parent_without_submit(demo_entry):
    host, entry, instant, rid = _reserve(demo_entry)
    core_files = {
        p.relative_to(host.cursor_root): p.read_bytes()
        for p in host.cursor_root.rglob("*")
        if p.is_file()
    }
    envelope, context = host.plan_testnet_entry_v1(
        entry=entry,
        reservation_id=rid,
        expected_revision=host.budget.budget_revision_ref_v1(),
        clock=instant.timestamp,
    )
    assert envelope.instrument_id == host.budget.bound.venue_native_id
    assert envelope.quantity == "0.0003"
    assert envelope.side == ("buy" if entry.cycle.decision_outcome == "enter_long" else "sell")
    assert context.order_environment == "TESTNET"
    link = host.budget.owner.execution_links_v1()[rid]
    assert link["phase"] == "PLAN_BOUND" and link["identity"] is None
    assert "external_effect_permit" not in link
    origin = link["plan_origin"]
    assert origin["venue_plan"]["environment"] == "TESTNET"
    assert (
        origin["canonical_order_intent"]["decision_id"] == entry.cycle.replay.evidence.decision_id
    )
    assert (
        origin["core_cursor_source"]["entry_frame_reference"]["decision_id"]
        == entry.cycle.replay.evidence.decision_id
    )
    assert {
        p.relative_to(host.cursor_root): p.read_bytes()
        for p in host.cursor_root.rglob("*")
        if p.is_file()
    } == core_files
    with pytest.raises(ValueError, match="ORIGINAL_HOLD_REQUIRED"):
        prepare_btc_demo_entry_plan_v1(
            host,
            entry=entry,
            reservation_id=rid,
            expected_revision=host.budget.budget_revision_ref_v1(),
            clock=instant.timestamp,
        )
    owner = host.budget.owner
    root = owner.durable_scope_identity_v1()["root"]
    before = owner.execution_links_v1()
    owner.close()
    from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3

    reopened = BtcDemoBudgetOwnerV3(
        durable_root=root,
        durable_account_identity=host.budget.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.budget.bound},
    )
    try:
        assert reopened.execution_links_v1() == before
        assert reopened.budget_state_v1().recovery_required is True
    finally:
        reopened.close()


@pytest.mark.parametrize("fault", ["revision", "expired", "reservation", "expires-during-plan"])
def test_unbound_or_stale_plan_leaves_original_journal_unchanged(demo_entry, fault):
    host, entry, instant, rid = _reserve(demo_entry)
    revision = host.budget.budget_revision_ref_v1()
    times = iter((instant.timestamp(), instant.timestamp() + 16))
    with pytest.raises(ValueError, match="HEAD_CHANGED|ACQUISITION_STALE|ORIGINAL_HOLD_REQUIRED"):
        prepare_btc_demo_entry_plan_v1(
            host,
            entry=entry,
            reservation_id="foreign" if fault == "reservation" else rid,
            expected_revision=(0, "0" * 64) if fault == "revision" else revision,
            clock=(lambda: next(times))
            if fault == "expires-during-plan"
            else lambda: instant.timestamp() + (16 if fault == "expired" else 0),
        )
    assert host.budget.budget_revision_ref_v1() == revision
    assert host.budget.owner.execution_links_v1() == {}
