"""Original TESTNET writer retains session time separately from Core scope."""

from dataclasses import replace
from datetime import timedelta

import pytest

from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
from src.ops.btc_demo_session_control_v1 import BoundedDemoSessionRegistrationV1
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1 as clock_owner
from tests.ops.test_btc_demo_entry_reservation_v1 import demo_entry as demo_entry
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network


def registration(case):
    host, _, _, _, instant, _ = case
    return BoundedDemoSessionRegistrationV1(
        session_id=host.writer_session_id,
        account_identity=host.budget.account,
        instrument_id=host.budget.bound.instrument_id,
        started_at_utc=instant.isoformat(),
        operator_start_digest="a" * 64,
    )


def test_original_writer_retains_start_deadline_and_no_additional_capital(demo_entry, monkeypatch):
    host, entry, reads, movement, instant, _ = demo_entry
    owner = host.budget.owner
    reg = registration(demo_entry)
    cursor = {p: p.read_bytes() for p in host.cursor_root.rglob("*") if p.is_file()}
    allocation = owner.risk_snapshot_v1()["state"]["slot_capital_allocation"]
    monkeypatch.setattr(clock_owner, "utc_now_iso_v1", instant.isoformat)
    row = owner.register_bounded_demo_session_v1(
        reg, expected_head=host.budget.budget_revision_ref_v1()[1], now_utc=instant.isoformat()
    )
    assert row["registration_digest"] == reg.digest_v1()
    assert reg.deadline_utc == (instant + timedelta(seconds=3600)).isoformat()
    result, _ = host.reserve_testnet_entry_v1(
        entry=entry, reads=reads, movement_input=movement, clock=instant.timestamp
    )
    assert result.disposition.value == "ADMITTED"
    before = owner.local_commitment_readback_v1().active_commitment_sum
    monkeypatch.setattr(
        clock_owner, "utc_now_iso_v1", (instant + timedelta(seconds=3600)).isoformat
    )
    with pytest.raises(ValueError, match="NEW_RISK_WINDOW_CLOSED"):
        owner.require_bounded_demo_risk_window_v1()
    assert owner.local_commitment_readback_v1().active_commitment_sum == before
    assert owner.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
    assert {p: p.read_bytes() for p in host.cursor_root.rglob("*") if p.is_file()} == cursor
    path = owner.durable_scope_identity_v1()["root"]
    owner.close()
    reopened = BtcDemoBudgetOwnerV3(
        durable_root=path,
        durable_account_identity=host.budget.account,
        durable_mode="recover",
        durable_lane_bindings={"LANE_3": host.budget.bound},
    )
    try:
        assert reopened._bounded_demo_session_control == row
        assert reopened.local_commitment_readback_v1().active_commitment_sum == before
        with pytest.raises(ValueError, match="NEW_RISK_WINDOW_CLOSED"):
            reopened.require_bounded_demo_risk_window_v1()
        assert reopened.risk_snapshot_v1()["state"]["slot_capital_allocation"] == allocation
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "fault",
    [
        "account",
        "instrument",
        "duration",
        "environment",
        "future-start",
        "stale-start",
        "head",
        "duplicate",
    ],
)
def test_invalid_session_registration_cannot_change_the_original_store(demo_entry, fault):
    host, _, _, _, instant, _ = demo_entry
    owner = host.budget.owner
    reg = registration(demo_entry)
    now = instant
    if fault == "account":
        reg = replace(reg, account_identity="foreign")
    elif fault == "instrument":
        reg = replace(reg, instrument_id="foreign")
    elif fault == "duration":
        reg = replace(reg, duration_seconds=7200)
    elif fault == "environment":
        reg = replace(reg, execution_environment="LIVE")
    elif fault == "future-start":
        now = instant - timedelta(seconds=1)
    elif fault == "stale-start":
        now = instant + timedelta(seconds=6)
    if fault == "duplicate":
        owner.register_bounded_demo_session_v1(
            reg, expected_head=host.budget.budget_revision_ref_v1()[1], now_utc=instant.isoformat()
        )
    before = host.budget.budget_revision_ref_v1()
    with pytest.raises(ValueError):
        owner.register_bounded_demo_session_v1(
            reg, expected_head="0" * 64 if fault == "head" else before[1], now_utc=now.isoformat()
        )
    assert host.budget.budget_revision_ref_v1() == before
