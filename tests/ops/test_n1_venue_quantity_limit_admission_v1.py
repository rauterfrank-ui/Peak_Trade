"""Actual N1 final-plan consumer with explicit synthetic, non-network GET ports."""

from __future__ import annotations

import socket
import json

import pytest

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    invoke_join_v1 as invoke,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_MAX_SIZE,
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from tests.ops import test_full_core_current_productive_pre_external_closure_v1 as fixtures
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1


@pytest.mark.parametrize(
    ("case", "short", "allowed"),
    [
        ("private_zero", False, False),
        ("private_zero", True, False),
        ("public_zero", False, False),
        ("missing_private", False, False),
        ("invalid_private", False, False),
        ("wrong_instrument", False, False),
        ("valid", False, True),
        ("valid", True, True),
        ("equal_buy_one", False, True),
    ],
)
def test_n1_final_quantity_uses_original_limits_and_release(
    tmp_path, monkeypatch, case: str, short: bool, allowed: bool
) -> None:
    def no_network(*args, **kwargs):
        raise AssertionError("Synthetic N1 proof must not open a socket")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    original_transport = fixtures._productive_transport
    original_finalize = invoke._finalize_portfolio_reservation_after_enter_join_v1
    finalized = []
    release_results = []
    original_release = PortfolioCapitalReservationBudgetOwnerV1.release_sizing_or_admission_deny_v1

    def release(owner, reservation_id):
        result = original_release(owner, reservation_id)
        release_results.append(result)
        return result

    def transport():
        port = original_transport()
        row = port.payloads[ENDPOINT_ACCOUNT_MAX_SIZE]["data"][0]
        row.update(maxBuy="1000000", maxSell="1000000")
        for instrument in port.payloads[ENDPOINT_PUBLIC_INSTRUMENTS]["data"]:
            instrument.update(maxMktSz="1000000", maxLmtSz="1000000")
            if case == "public_zero":
                instrument["maxMktSz"] = "0"
            if case == "equal_buy_one":
                instrument["maxMktSz"] = "1"
        if case == "private_zero":
            row.update(maxBuy="0", maxSell="0")
        elif case == "missing_private":
            row.pop("maxBuy")
            row.pop("maxSell")
        elif case == "invalid_private":
            row["maxBuy"] = "not-a-number"
        elif case == "wrong_instrument":
            row["instId"] = "foreign-instrument"
        elif case == "equal_buy_one":
            row.update(maxBuy="1", maxSell="0")
        return port

    def finalize(owner, **kwargs):
        original_finalize(owner, **kwargs)
        finalized.append((kwargs["venue_plan_pass"], owner.active_sum_v1()))

    monkeypatch.setattr(fixtures, "_productive_transport", transport)
    monkeypatch.setattr(invoke, "_finalize_portfolio_reservation_after_enter_join_v1", finalize)
    monkeypatch.setattr(
        PortfolioCapitalReservationBudgetOwnerV1, "release_sizing_or_admission_deny_v1", release
    )
    result = _run_layered_entry_supervisor_v1(tmp_path, short=short)
    last = result.policy_result.orchestrator_result.cycle_records[-1]
    envelope = last.final_order_envelope
    assert result.policy_result.orchestrator_result.post_count == 0
    assert result.policy_result.orchestrator_result.permit_created is False
    assert (envelope is not None) is allowed
    if allowed:
        assert envelope.side == ("sell" if short else "buy")
        assert envelope.quantity == ("3" if short else "1")
        assert envelope.quantity_unit == "CONTRACTS"
        assert finalized and finalized[-1][0] is True and finalized[-1][1] > 0
    elif case != "wrong_instrument":
        assert finalized and finalized[-1] == (False, 0)
        assert release_results[-1].reservation.state.value == "RELEASED"
        assert release_results[-1].reservation.terminal_reason == "SIZING_OR_ADMISSION_DENY"
    if case != "wrong_instrument":
        ledgers = [
            json.loads(file.read_text())
            for file in tmp_path.rglob("governed_cycle_orchestrator_ledger_v1.json")
        ]
        assessments = [
            row["venue_quantity_limit_assessment"]
            for row in ledgers
            if row.get("venue_quantity_limit_assessment") is not None
        ]
        assert len(assessments) == 1
        assessment = assessments[0]
        assert assessment["allowed"] is allowed
        assert assessment["scope"] == "N1_FINAL_PLAN_ONLY"
        assert assessment["runtime_authorization_effect"] == "NONE"
        assert assessment["source_binding"]["cycle_id"]
        assert len(assessment["source_binding"]["account_identity_digest"]) == 64
        if not allowed:
            denied = [row for row in ledgers if row.get("venue_quantity_limit_assessment")]
            assert denied[0]["terminal_class"] == "VENUE_QUANTITY_ADMISSION_DENIED"
            assert denied[0]["portfolio_reservation_id"]
