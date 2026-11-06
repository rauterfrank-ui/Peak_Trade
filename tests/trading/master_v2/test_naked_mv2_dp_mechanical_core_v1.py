"""Isolated tests for naked_mv2_dp_mechanical_core_v1 (no legacy scope authorities)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from trading.master_v2.naked_mv2_dp_mechanical_core_v1 import (
    D_T_INTERNAL_DERIVATION_PRESENT,
    D_T_ROLE,
    NakedMechanicalStateV1,
    NakedMechanicalStepInputV1,
    NakedRegimeV1,
    SOLE_PRICE_SWITCH_RULE,
    execute_naked_mechanical_step_v1,
    next_naked_mechanical_state_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MECHANICAL_SRC = _REPO_ROOT / "src/trading/master_v2/naked_mv2_dp_mechanical_core_v1.py"


def _state(
    *,
    instrument_id: str = "BTC-PERP",
    regime: NakedRegimeV1 = NakedRegimeV1.BULL,
    r_t: float = 100.0,
) -> NakedMechanicalStateV1:
    return NakedMechanicalStateV1(
        instrument_id=instrument_id,
        regime=regime,
        reference_price_r_t=r_t,
    )


def _step(
    *,
    m_t: float,
    d_t: float | None,
    prev: NakedMechanicalStateV1 | None = None,
    instrument_id: str = "BTC-PERP",
) -> NakedMechanicalStepInputV1:
    previous = prev or _state(instrument_id=instrument_id)
    return NakedMechanicalStepInputV1(
        instrument_id=instrument_id,
        mark_price_m_t=m_t,
        previous_state=previous,
        dynamic_scope_d_t=d_t,
    )


def test_contract_constants() -> None:
    assert D_T_ROLE == "EXPLICIT_EXTERNAL_REQUIRED_INPUT"
    assert D_T_INTERNAL_DERIVATION_PRESENT is False
    assert SOLE_PRICE_SWITCH_RULE == "CM_t>=D_t"


def test_single_instrument_per_step() -> None:
    prev = _state(instrument_id="ETH-PERP")
    result = execute_naked_mechanical_step_v1(
        _step(m_t=100.0, d_t=5.0, prev=prev, instrument_id="ETH-PERP")
    )
    assert result.instrument_id == "ETH-PERP"
    mismatch = execute_naked_mechanical_step_v1(
        NakedMechanicalStepInputV1(
            instrument_id="OTHER",
            mark_price_m_t=100.0,
            previous_state=prev,
            dynamic_scope_d_t=5.0,
        )
    )
    assert mismatch.fail_closed
    assert "naked_mechanical_instrument_mismatch" in mismatch.fail_reasons


def test_m_t_consumed_unchanged() -> None:
    m = 123.456
    result = execute_naked_mechanical_step_v1(_step(m_t=m, d_t=1.0))
    assert result.m_t == pytest.approx(m)


def test_bull_r_t_follows_favorable_highs_only() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    up = execute_naked_mechanical_step_v1(_step(m_t=105.0, d_t=50.0, prev=prev))
    assert up.r_t_post == pytest.approx(105.0)
    peaked = _state(regime=NakedRegimeV1.BULL, r_t=110.0)
    down = execute_naked_mechanical_step_v1(_step(m_t=102.0, d_t=50.0, prev=peaked))
    assert down.r_t_post == pytest.approx(110.0)


def test_bear_r_t_follows_favorable_lows_only() -> None:
    prev = _state(regime=NakedRegimeV1.BEAR, r_t=100.0)
    down = execute_naked_mechanical_step_v1(_step(m_t=95.0, d_t=50.0, prev=prev))
    assert down.r_t_post == pytest.approx(95.0)
    troughed = _state(regime=NakedRegimeV1.BEAR, r_t=90.0)
    up = execute_naked_mechanical_step_v1(_step(m_t=98.0, d_t=50.0, prev=troughed))
    assert up.r_t_post == pytest.approx(90.0)


def test_bull_cm_formula() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=94.0, d_t=50.0, prev=prev))
    assert result.cm_t == pytest.approx(6.0)


def test_bear_cm_formula() -> None:
    prev = _state(regime=NakedRegimeV1.BEAR, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=106.0, d_t=50.0, prev=prev))
    assert result.cm_t == pytest.approx(6.0)


def test_favorable_continuation_cm_zero() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=110.0, d_t=5.0, prev=prev))
    assert result.cm_t == pytest.approx(0.0)
    assert result.switch_condition_met is False


def test_cm_below_d_no_switch() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=96.0, d_t=5.0, prev=prev))
    assert result.cm_t == pytest.approx(4.0)
    assert result.switch_condition_met is False
    assert result.state_post is NakedRegimeV1.BULL


def test_cm_equals_d_switches() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=95.0, d_t=5.0, prev=prev))
    assert result.cm_t == pytest.approx(5.0)
    assert result.switch_condition_met is True


def test_cm_above_d_switches() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=90.0, d_t=5.0, prev=prev))
    assert result.switch_condition_met is True


def test_bull_to_bear() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=92.0, d_t=5.0, prev=prev))
    assert result.state_pre is NakedRegimeV1.BULL
    assert result.state_post is NakedRegimeV1.BEAR
    nxt = next_naked_mechanical_state_v1(previous=prev, step=result)
    assert nxt.regime is NakedRegimeV1.BEAR


def test_bear_to_bull() -> None:
    prev = _state(regime=NakedRegimeV1.BEAR, r_t=100.0)
    result = execute_naked_mechanical_step_v1(_step(m_t=108.0, d_t=5.0, prev=prev))
    assert result.state_pre is NakedRegimeV1.BEAR
    assert result.state_post is NakedRegimeV1.BULL


def test_mathematical_symmetry() -> None:
    d = 7.0
    bull = execute_naked_mechanical_step_v1(
        _step(m_t=100.0 - d, d_t=d, prev=_state(regime=NakedRegimeV1.BULL, r_t=100.0))
    )
    bear = execute_naked_mechanical_step_v1(
        _step(m_t=100.0 + d, d_t=d, prev=_state(regime=NakedRegimeV1.BEAR, r_t=100.0))
    )
    assert bull.cm_t == bear.cm_t == pytest.approx(d)
    assert bull.switch_condition_met and bear.switch_condition_met
    assert bull.state_post is NakedRegimeV1.BEAR
    assert bear.state_post is NakedRegimeV1.BULL


def test_r_t_reset_after_switch() -> None:
    prev = _state(regime=NakedRegimeV1.BULL, r_t=100.0)
    m = 92.0
    result = execute_naked_mechanical_step_v1(_step(m_t=m, d_t=5.0, prev=prev))
    assert result.r_t_reset_performed is True
    nxt = next_naked_mechanical_state_v1(previous=prev, step=result)
    assert nxt.reference_price_r_t == pytest.approx(m)


def test_d_t_none_fail_closed() -> None:
    prev = _state()
    result = execute_naked_mechanical_step_v1(_step(m_t=100.0, d_t=None, prev=prev))
    assert result.fail_closed
    assert result.switch_condition_met is False
    assert "naked_boundary_distance_unavailable" in result.fail_reasons
    assert next_naked_mechanical_state_v1(previous=prev, step=result) == prev


def test_d_t_invalid_fail_closed() -> None:
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        prev = _state()
        result = execute_naked_mechanical_step_v1(_step(m_t=100.0, d_t=bad, prev=prev))
        assert result.fail_closed
        assert result.switch_condition_met is False


def test_deterministic_replay() -> None:
    inp = _step(m_t=97.0, d_t=2.5, prev=_state(regime=NakedRegimeV1.BULL, r_t=100.0))
    a = execute_naked_mechanical_step_v1(inp)
    b = execute_naked_mechanical_step_v1(inp)
    assert a == b


def test_no_legacy_distance_constants_in_mechanical_owner() -> None:
    text = _MECHANICAL_SRC.read_text(encoding="utf-8")
    for token in ("200", "80", "120", "up_distance", "reversal_distance"):
        assert token not in text


def _mechanical_code_without_module_docstring() -> str:
    return _MECHANICAL_SRC.read_text(encoding="utf-8").split('"""', 2)[-1]


def test_no_vol_band_dependency_in_mechanical_owner() -> None:
    tree = ast.parse(_MECHANICAL_SRC.read_text(encoding="utf-8"))
    modules = [
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    ]
    assert not any("volatility" in (m or "").lower() for m in modules)
    code = _mechanical_code_without_module_docstring().lower()
    assert "current_upscope" not in code
    assert "current_downscope" not in code
    assert "clamp_band" not in code


def test_no_confirmation_dependency_in_mechanical_owner() -> None:
    code = _mechanical_code_without_module_docstring()
    assert "confirmation_epochs" not in code
    assert "ScopeConfirmationStateV1" not in code
    assert "cooldown_state" not in code


def test_no_c3_composition_entry_exit_imports() -> None:
    tree = ast.parse(_MECHANICAL_SRC.read_text(encoding="utf-8"))
    imports = [
        node.names[0].name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]
    forbidden_fragments = (
        "composition",
        "entry_exit",
        "directional_assessment",
        "execution",
        "order",
        "c3",
        "c4",
    )
    for mod in imports:
        low = mod.lower()
        assert not any(frag in low for frag in forbidden_fragments)


def test_no_order_execution_effect() -> None:
    text = _MECHANICAL_SRC.read_text(encoding="utf-8").lower()
    assert "submit" not in text
    assert "order" not in text
