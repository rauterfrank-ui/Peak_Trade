# tests/trading/master_v2/test_double_play_capital_slot.py
from __future__ import annotations

import ast
from pathlib import Path

from trading.master_v2.double_play_capital_slot import (
    DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION,
    CapitalSlotBlockReason,
    CapitalSlotConfig,
    CapitalSlotReleaseReason,
    CapitalSlotState,
    CapitalSlotStatus,
    apply_loss_following_base,
    calculate_ratchet_target,
    cashflow_split_valid,
    evaluate_capital_slot_ratchet,
    evaluate_capital_slot_release,
)


def _cfg(**overrides: object) -> CapitalSlotConfig:
    d: dict = {
        "profit_step_pct": 0.10,
        "cashflow_lock_fraction": 0.30,
        "reinvest_fraction": 0.70,
        "allow_auto_top_up": False,
        "live_authorization": False,
        "min_realized_volatility": 0.05,
        "min_atr_or_range": 0.05,
        "max_time_without_cashflow_step": 10_000,
        "min_opportunity_score": 0.2,
    }
    d.update(overrides)
    return CapitalSlotConfig(**d)


def _st(**overrides: object) -> CapitalSlotState:
    d: dict = {
        "selected_future": "BTC-USD-PERP",
        "initial_slot_base": 300.0,
        "active_slot_base": 300.0,
        "realized_or_settled_slot_equity": 300.0,
        "unrealized_pnl": 0.0,
        "locked_cashflow": 0.0,
        "time_without_cashflow_step": 0,
        "realized_volatility": 0.5,
        "atr_or_range": 0.5,
        "opportunity_score": 0.8,
        "survival_allows_slot": True,
    }
    d.update(overrides)
    return CapitalSlotState(**d)


def test_layer_version_is_v0() -> None:
    assert DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION == "v0"


def test_ratchet_target_from_active_base() -> None:
    assert calculate_ratchet_target(300.0, 0.10) == 330.0
    assert calculate_ratchet_target(270.0, 0.10) == 297.0


def test_reset_requires_realized_settled_equity() -> None:
    cfg = _cfg()
    st = _st(realized_or_settled_slot_equity=340.0)
    d = evaluate_capital_slot_ratchet(cfg, st)
    assert d.can_ratchet
    assert d.ratchet_target == 330.0
    assert d.new_active_slot_base == 340.0

    st2 = _st(realized_or_settled_slot_equity=320.0)
    d2 = evaluate_capital_slot_ratchet(cfg, st2)
    assert not d2.can_ratchet
    assert d2.ratchet_target == 330.0


def test_unrealized_pnl_alone_cannot_satisfy_ratchet() -> None:
    cfg = _cfg()
    st = _st(realized_or_settled_slot_equity=200.0, unrealized_pnl=1_000_000.0)
    d = evaluate_capital_slot_ratchet(cfg, st)
    assert not d.can_ratchet
    assert d.ratchet_target == 330.0


def test_losses_reduce_active_base_via_loss_following() -> None:
    assert apply_loss_following_base(300.0, 270.0) == 270.0


def test_losses_do_not_trigger_auto_top_up_in_apply() -> None:
    out = apply_loss_following_base(300.0, 270.0)
    assert out < 300.0
    assert out == 270.0


def test_reduced_base_defines_next_target() -> None:
    assert calculate_ratchet_target(270.0, 0.10) == 297.0


def test_cashflow_split_explicit_and_valid() -> None:
    assert cashflow_split_valid(0.3, 0.7)
    assert not cashflow_split_valid(0.5, 0.4)


def test_locked_cashflow_not_in_ratchet_basis() -> None:
    t = calculate_ratchet_target(300.0, 0.10, locked_cashflow=50.0)
    assert t == 250.0 * 1.1


def test_invalid_split_blocks_ratchet() -> None:
    cfg = _cfg(cashflow_lock_fraction=0.5, reinvest_fraction=0.4)
    d = evaluate_capital_slot_ratchet(cfg, _st())
    assert not d.can_ratchet
    assert CapitalSlotBlockReason.INVALID_CASHFLOW_SPLIT in d.block_reasons


def test_inactivity_release_low_movement() -> None:
    cfg = _cfg()
    st = _st(realized_volatility=0.01, atr_or_range=0.01)
    rel = evaluate_capital_slot_release(cfg, st)
    assert rel.released
    assert rel.release_reason is CapitalSlotReleaseReason.INACTIVITY
    assert rel.status is CapitalSlotStatus.RELEASED
    assert not rel.authorizes_new_future_selection
    assert not rel.authorizes_new_trade


def test_opportunity_cost_release() -> None:
    cfg = _cfg()
    st = _st(opportunity_score=0.05)
    rel = evaluate_capital_slot_release(cfg, st)
    assert rel.released
    assert rel.release_reason is CapitalSlotReleaseReason.OPPORTUNITY_COST


def test_release_does_not_authorize_new_future_or_trade() -> None:
    cfg = _cfg()
    st = _st(opportunity_score=0.05)
    rel = evaluate_capital_slot_release(cfg, st)
    assert not rel.authorizes_new_future_selection
    assert not rel.authorizes_new_trade
    assert not rel.live_authorization


def test_survival_blocker_prevents_ratchet() -> None:
    cfg = _cfg()
    st = _st(realized_or_settled_slot_equity=400.0, survival_allows_slot=False)
    d = evaluate_capital_slot_ratchet(cfg, st)
    assert not d.can_ratchet
    assert CapitalSlotBlockReason.SURVIVAL_NOT_ALLOWED in d.block_reasons


def test_live_authorization_false_on_decisions() -> None:
    cfg = _cfg()
    st = _st()
    assert not evaluate_capital_slot_ratchet(cfg, st).live_authorization
    assert not evaluate_capital_slot_release(cfg, st).live_authorization


def test_config_live_authorization_true_fail_closed() -> None:
    cfg = _cfg(live_authorization=True)
    st = _st()
    dr = evaluate_capital_slot_ratchet(cfg, st)
    dl = evaluate_capital_slot_release(cfg, st)
    assert CapitalSlotBlockReason.CONFIG_LIVE_AUTHORIZATION_CONTRADICTION in dr.block_reasons
    assert CapitalSlotBlockReason.CONFIG_LIVE_AUTHORIZATION_CONTRADICTION in dl.block_reasons
    assert not dr.live_authorization
    assert not dl.live_authorization


def test_no_forbidden_top_level_imports_in_module() -> None:
    root = Path(__file__).resolve().parent.parent.parent.parent / "src" / "trading" / "master_v2"
    path = root / "double_play_capital_slot.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = {"requests", "urllib3", "ccxt", "httpx", "socket", "aiohttp"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad
        if isinstance(node, ast.ImportFrom) and node.module:
            mod0 = node.module.split(".")[0]
            if mod0 == "trading":
                continue
            assert mod0 not in bad
