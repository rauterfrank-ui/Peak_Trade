"""S4 — L8–L10 running mechanics (delegates canonical formulas)."""

from __future__ import annotations

import pytest

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    RunningReferenceStateV1,
    ScopeStateV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.running_mechanics_pipeline_v1 import (
    run_running_mechanics_l8_through_l10_v1,
)
from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import NakedRegimeV1


def _scope(*, d: float = 5.0, nullline: float = 100.0) -> ScopeStateV1:
    return ScopeStateV1(
        instrument_id="BTC-PERP",
        d_t=d,
        nullline_price=nullline,
        nullline_provenance_epoch=2,
        generator_id="test/v1",
        valid=True,
    )


def _running(*, r: float) -> RunningReferenceStateV1:
    return RunningReferenceStateV1(instrument_id="BTC-PERP", reference_price_r_t=r)


def test_bull_r_t_tracks_highs_nullline_unchanged() -> None:
    scope = _scope(nullline=100.0)
    up = run_running_mechanics_l8_through_l10_v1(
        scope=scope,
        regime=NakedRegimeV1.BULL,
        mark_price_m_t=105.0,
        running_reference=_running(r=100.0),
    )
    assert up.r_t_post == pytest.approx(105.0)
    assert up.nullline_price == pytest.approx(100.0)
    down = run_running_mechanics_l8_through_l10_v1(
        scope=scope,
        regime=NakedRegimeV1.BULL,
        mark_price_m_t=102.0,
        running_reference=_running(r=105.0),
    )
    assert down.r_t_post == pytest.approx(105.0)
    assert down.nullline_price == pytest.approx(100.0)


def test_bull_to_bear_switch_symmetry() -> None:
    scope = _scope(d=5.0)
    bull = run_running_mechanics_l8_through_l10_v1(
        scope=scope,
        regime=NakedRegimeV1.BULL,
        mark_price_m_t=95.0,
        running_reference=_running(r=100.0),
    )
    assert bull.switch_condition_met is True
    assert bull.state_post is NakedRegimeV1.BEAR
    bear = run_running_mechanics_l8_through_l10_v1(
        scope=scope,
        regime=NakedRegimeV1.BEAR,
        mark_price_m_t=105.0,
        running_reference=_running(r=100.0),
    )
    assert bear.switch_condition_met is True
    assert bear.state_post is NakedRegimeV1.BULL
    assert bull.cm_t == bear.cm_t == pytest.approx(5.0)


def test_mechanical_core_regression_still_passes() -> None:
    from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import (
        execute_naked_mechanical_step_v1,
        NakedMechanicalStateV1,
        NakedMechanicalStepInputV1,
    )

    prev = NakedMechanicalStateV1(
        instrument_id="BTC-PERP",
        regime=NakedRegimeV1.BULL,
        reference_price_r_t=100.0,
    )
    result = execute_naked_mechanical_step_v1(
        NakedMechanicalStepInputV1(
            instrument_id="BTC-PERP",
            mark_price_m_t=95.0,
            previous_state=prev,
            dynamic_scope_d_t=5.0,
        )
    )
    assert result.switch_condition_met is True
    assert result.state_post is NakedRegimeV1.BEAR
