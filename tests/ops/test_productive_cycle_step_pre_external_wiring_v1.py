"""Regression: productive cycle step must project PRE_EXTERNAL for enter-eligible bridge cycles."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)


def _tick() -> ObservationMarketTickV1:
    return ObservationMarketTickV1(
        instrument_id="ETH-USD_UM_XPERP-310404",
        venue="okx_eea",
        market_type="swap",
        sequence=1,
        event_ts_unix=1_700_000_000.0,
        receive_ts_unix=1_700_000_001.0,
        mono_ts=1.0,
        mid_price=3500.0,
    )


def test_default_productive_cycle_step_projects_pre_external_on_enter_long() -> None:
    from src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1 import (
        default_productive_cycle_step_v1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
    )

    bridge_cycle = {
        "cycle_id": "cycle_test_enter",
        "cycle_index": 3,
        "decision_outcome": "enter_long",
        "intended_action": {
            "intended_side": "BUY",
            "intended_quantity": "0.05",
            "safety_blocked": False,
        },
        "price_basis": {"mid_price": 3500.0},
    }
    fake_outcome = SimpleNamespace(
        ok=True,
        bridge_cycle=bridge_cycle,
        md_blockers=(),
        labels={},
    )
    state = HardenedBridgeSessionStateV2()
    with patch(
        "src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1."
        "run_hardened_wallclock_bridge_observation_cycle_v2",
        return_value=fake_outcome,
    ):
        step = default_productive_cycle_step_v1(
            state,
            _tick(),
            Decimal("3500"),
            1_700_000_100.0,
            "paper-shadow-test",
            3,
        )
    assert step.pre_external_event is not None
    assert step.pre_external_event.side == "long"
    assert step.to_dict()["pre_external"] is True


def test_default_productive_cycle_step_no_pre_external_for_no_action() -> None:
    from src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1 import (
        default_productive_cycle_step_v1,
    )
    from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
        HardenedBridgeSessionStateV2,
    )

    fake_outcome = SimpleNamespace(
        ok=True,
        bridge_cycle={"decision_outcome": "no_action", "intended_action": {}},
        md_blockers=(),
        labels={},
    )
    state = HardenedBridgeSessionStateV2()
    with patch(
        "src.ops.paper_shadow_bounded_orchestrator_v1.productive_cycle_step_v1."
        "run_hardened_wallclock_bridge_observation_cycle_v2",
        return_value=fake_outcome,
    ):
        step = default_productive_cycle_step_v1(
            state,
            _tick(),
            Decimal("3500"),
            1_700_000_100.0,
            "paper-shadow-test",
            1,
        )
    assert step.pre_external_event is None
