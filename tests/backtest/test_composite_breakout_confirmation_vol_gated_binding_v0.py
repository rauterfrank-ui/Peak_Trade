"""Bounded composite breakout confirmation + vol-gated binding contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.strategy_signal_binding_v1 import (
    COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1,
    COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1,
    COMPOSITE_STRATEGY_ID,
    COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK,
    StrategySignalBindingError,
    compute_composite_required_warmup_rows_v1,
    execute_composite_strategy_signal_series_v1,
    execute_configured_strategy_signal_series_v1,
    parse_composite_strategy_binding_v1,
)
from src.strategies.breakout_confirmation_v1 import (
    CONFIRMATION_EPOCHS_V1,
    compute_donchian_channel_bounds_v1,
    generate_confirmed_breakout_signals_v1,
)


def _frame(closes: list[float], *, finals: list[bool] | None = None) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=len(closes), freq="1h", tz="UTC")
    if finals is None:
        finals = [True] * len(closes)
    close = [float(v) for v in closes]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "is_final": finals,
        },
        index=idx,
    )


def _confirmed_binding(**overrides: object) -> dict:
    payload: dict = {
        "composite_type": COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1,
        "composition_rule": COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK,
        "signal_strategy_id": "breakout_donchian",
        "filter_strategy_id": "vol_regime_filter",
        "signal_strategy_params": {"lookback": 3, "price_col": "close"},
        "filter_strategy_params": {
            "vol_window": 3,
            "vol_method": "range",
            "vol_percentile_low": 0,
            "vol_percentile_high": 100,
            "min_bars": 3,
            "lookback_percentile": 3,
            "regime_mode": False,
        },
        "aggregation": "weighted",
        "signal_threshold": 0.3,
        "confirmation_epochs": CONFIRMATION_EPOCHS_V1,
    }
    payload.update(overrides)
    return payload


def _legacy_binding(**overrides: object) -> dict:
    payload: dict = {
        "composite_type": COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1,
        "composition_rule": "signal_times_filter_mask",
        "signal_strategy_id": "breakout_donchian",
        "filter_strategy_id": "vol_regime_filter",
        "signal_strategy_params": {"lookback": 20, "price_col": "close"},
        "filter_strategy_params": {
            "vol_window": 20,
            "vol_method": "atr",
            "vol_percentile_low": 25,
            "vol_percentile_high": 75,
            "min_bars": 30,
            "lookback_percentile": 100,
            "regime_mode": False,
        },
        "aggregation": "weighted",
        "signal_threshold": 0.3,
    }
    payload.update(overrides)
    return payload


class TestBreakoutConfirmationSemantics:
    def test_long_candidate_then_confirmation_on_next_bar(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 10.7, 10.7, 10.7]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0
        assert signals.iloc[5] == 1

    def test_long_reset_when_confirmation_fails(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 9.8, 9.8, 9.8]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0
        assert signals.iloc[5] == 0

    def test_short_candidate_and_confirmation_mirrored(self) -> None:
        closes = [10, 10, 10, 10, 9.4, 9.3, 9.3, 9.3]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0
        assert signals.iloc[5] == -1

    def test_short_reset_mirrored(self) -> None:
        closes = [10, 10, 10, 10, 9.4, 10.2, 10.2, 10.2]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0
        assert signals.iloc[5] == 0

    def test_candidate_boundary_is_immutable_when_channel_moves(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 10.05, 10.05, 10.05]
        frame = _frame(closes)
        rolling_high, _ = compute_donchian_channel_bounds_v1(frame["close"], lookback=3)
        bound_at_candidate = float(rolling_high.iloc[4])
        assert bound_at_candidate == 10.0
        assert float(rolling_high.iloc[5]) != bound_at_candidate
        signals = generate_confirmed_breakout_signals_v1(frame, lookback=3, price_col="close")
        assert signals.iloc[5] == 1

    def test_unfinalized_bar_does_not_confirm(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 10.7, 10.7]
        finals = [True, True, True, True, True, False, True]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes, finals=finals),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[5] == 0
        assert signals.iloc[6] == 0

    def test_invalid_data_blocks_candidate_and_confirmation(self) -> None:
        closes = [10, 10, float("nan"), 10, 10.6, 10.7, 10.7]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[5] == 0

    def test_opposite_breach_resets_pending_candidate(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 9.3, 9.2, 9.2]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0
        assert signals.iloc[5] == 0
        assert signals.iloc[6] == -1

    def test_no_signal_before_confirmation(self) -> None:
        closes = [10, 10, 10, 10, 10.6, 10.7]
        signals = generate_confirmed_breakout_signals_v1(
            _frame(closes),
            lookback=3,
            price_col="close",
        )
        assert signals.iloc[4] == 0

    def test_deterministic_repeat(self) -> None:
        frame = _frame([10, 10, 10, 10, 10.6, 10.7, 10.7, 10.7])
        first = generate_confirmed_breakout_signals_v1(frame, lookback=3, price_col="close")
        second = generate_confirmed_breakout_signals_v1(frame, lookback=3, price_col="close")
        assert first.equals(second)

    def test_confirmation_epochs_other_than_one_blocked(self) -> None:
        with pytest.raises(Exception, match="confirmation_epochs_not_allowed"):
            generate_confirmed_breakout_signals_v1(
                _frame([10, 10, 10, 10, 10.6, 10.7]),
                lookback=3,
                confirmation_epochs=2,
            )


class TestConfirmedCompositeBinding:
    def test_parse_and_execute_confirmed_binding(self) -> None:
        binding = parse_composite_strategy_binding_v1(_confirmed_binding())
        assert binding.composite_type == COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1
        assert binding.confirmation_epochs == CONFIRMATION_EPOCHS_V1
        result = execute_composite_strategy_signal_series_v1(
            _frame([10, 10, 10, 10, 10.6, 10.7, 10.7, 10.7, 10.7, 10.7] * 3),
            configured_params=_confirmed_binding(),
        )
        assert result.provenance.strategy_execution_status.value == "EXECUTED"

    def test_vol_regime_filter_remains_bound(self) -> None:
        binding = parse_composite_strategy_binding_v1(_confirmed_binding())
        assert binding.filter_strategy_id == "vol_regime_filter"

    def test_registry_binding_unique_from_legacy(self) -> None:
        legacy = parse_composite_strategy_binding_v1(_legacy_binding())
        confirmed = parse_composite_strategy_binding_v1(_confirmed_binding())
        assert legacy.binding_semantic_digest != confirmed.binding_semantic_digest

    def test_legacy_binding_unchanged(self) -> None:
        legacy = parse_composite_strategy_binding_v1(_legacy_binding())
        assert legacy.composite_type == COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1
        assert legacy.confirmation_epochs is None

    def test_bitcoin_identity_blocked(self) -> None:
        with pytest.raises(StrategySignalBindingError, match="binding_identity_forbidden"):
            parse_composite_strategy_binding_v1(
                _confirmed_binding(signal_strategy_id="breakout_btc_usdt")
            )

    def test_spot_identity_blocked(self) -> None:
        with pytest.raises(StrategySignalBindingError, match="binding_identity_forbidden"):
            parse_composite_strategy_binding_v1(
                _confirmed_binding(filter_strategy_id="eth_spot_filter")
            )

    def test_non_one_confirmation_epochs_fail_closed(self) -> None:
        with pytest.raises(
            StrategySignalBindingError,
            match="composite_confirmation_epochs_not_allowed",
        ):
            parse_composite_strategy_binding_v1(_confirmed_binding(confirmation_epochs=2))

    def test_warmup_includes_confirmation_epoch(self) -> None:
        warmup = compute_composite_required_warmup_rows_v1(_confirmed_binding())
        assert warmup >= 3 + CONFIRMATION_EPOCHS_V1

    def test_configured_strategy_execution_has_no_runtime_authority_fields(self) -> None:
        result = execute_configured_strategy_signal_series_v1(
            _frame([10, 10, 10, 10, 10.6, 10.7, 10.7, 10.7] * 5),
            strategy_id=COMPOSITE_STRATEGY_ID,
            cfg={"economic_evaluation_v1": {"strategy_params": _confirmed_binding()}},
        )
        payload = result.provenance.to_dict()
        assert payload["strategy_execution_status"] == "EXECUTED"
        assert "runtime" not in json.dumps(payload).lower()
        assert "order_effect" not in payload

    def test_architecture_binding_config_present_and_distinct(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        new_path = (
            repo_root
            / "config/ops/composite_breakout_confirmation_vol_gated_donchian_v1_architecture_binding_v1.json"
        )
        old_path = (
            repo_root
            / "config/ops/composite_vol_gated_breakout_donchian_v1_economic_evaluation_v1.json"
        )
        assert new_path.exists()
        new_cfg = json.loads(new_path.read_text(encoding="utf-8"))
        old_cfg = json.loads(old_path.read_text(encoding="utf-8"))
        assert (
            new_cfg["candidate_binding_id"]
            == "composite_breakout_confirmation_vol_gated_donchian_v1"
        )
        assert old_cfg["candidate_binding_id"] == "composite_vol_gated_breakout_donchian_v1"
        assert (
            new_cfg["economic_evaluation_v1"]["strategy_params"]["composite_type"]
            == COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1
        )
        assert "monte_carlo" not in new_cfg["economic_evaluation_v1"]
        assert "walk_forward" not in new_cfg["economic_evaluation_v1"]
        assert "stress" not in new_cfg["economic_evaluation_v1"]
