"""Wallclock PRE_EXTERNAL projection from bridge_cycle (integration seam only)."""

from __future__ import annotations

from decimal import Decimal

from src.ops.paper_shadow_bounded_orchestrator_v1.wallclock_pre_external_projection_v1 import (
    project_wallclock_pre_external_from_bridge_cycle_v1,
)


def test_project_pre_external_from_enter_long_bridge_cycle() -> None:
    ev = project_wallclock_pre_external_from_bridge_cycle_v1(
        {
            "cycle_id": "cycle_abc",
            "cycle_index": 7,
            "decision_outcome": "enter_long",
            "intended_action": {
                "intended_side": "BUY",
                "intended_quantity": "0.1",
                "safety_blocked": False,
            },
            "price_basis": {"mid_price": 3500.0},
        },
        session_id="paper-shadow-PAPER_SHADOW_RUN_TEST",
        instrument_id="ETH-USD_UM_XPERP-310404",
    )
    assert ev is not None
    assert ev.side == "long"
    assert ev.quantity == "0.1"
    assert ev.terminal_disposition == "PRE_EXTERNAL_EFFECT"


def test_project_pre_external_from_enter_short_bridge_cycle() -> None:
    ev = project_wallclock_pre_external_from_bridge_cycle_v1(
        {
            "cycle_id": "cycle_xyz",
            "cycle_index": 3,
            "decision_outcome": "enter_short",
            "intended_action": {
                "intended_side": "SELL",
                "intended_quantity": "0.2",
                "safety_blocked": False,
            },
            "price_basis": {"mid_price": 3400.0},
        },
        session_id="paper-shadow-PAPER_SHADOW_RUN_TEST",
        instrument_id="ETH-USD_UM_XPERP-310404",
    )
    assert ev is not None
    assert ev.side == "short"
    assert ev.quantity == "0.2"


def test_no_pre_external_for_observe_outcome() -> None:
    assert (
        project_wallclock_pre_external_from_bridge_cycle_v1(
            {"decision_outcome": "observe", "intended_action": {}},
            session_id="s",
            instrument_id="ETH-USD_UM_XPERP-310404",
        )
        is None
    )


def test_no_pre_external_for_blocked_outcome() -> None:
    assert (
        project_wallclock_pre_external_from_bridge_cycle_v1(
            {"decision_outcome": "blocked", "intended_action": {}},
            session_id="s",
            instrument_id="ETH-USD_UM_XPERP-310404",
        )
        is None
    )


def test_no_pre_external_for_no_action() -> None:
    assert (
        project_wallclock_pre_external_from_bridge_cycle_v1(
            {"decision_outcome": "no_action", "intended_action": {}},
            session_id="s",
            instrument_id="ETH-USD_UM_XPERP-310404",
        )
        is None
    )


def test_no_pre_external_when_safety_blocked() -> None:
    assert (
        project_wallclock_pre_external_from_bridge_cycle_v1(
            {
                "decision_outcome": "enter_long",
                "intended_action": {
                    "intended_side": "BUY",
                    "intended_quantity": "1",
                    "safety_blocked": True,
                },
                "price_basis": {"mid_price": 1.0},
            },
            session_id="s",
            instrument_id="ETH-USD_UM_XPERP-310404",
        )
        is None
    )
