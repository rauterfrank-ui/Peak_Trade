from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.experiments.stress_tests import StressScenarioResult
from src.trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
    with_computed_evidence_semantic_digest,
)


def _cfg(*, fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }


def _bars(n: int = 12) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def _run(**kwargs: Any) -> wiring.MV2ResearchWiringResultV1:
    return wiring.run_mv2_research_backtest_wiring_v1(
        bars=kwargs.pop("bars", _bars()),
        strategy_id=kwargs.pop("strategy_id", "ma_crossover"),
        cfg=kwargs.pop("cfg", _cfg()),
        **kwargs,
    )


def test_matrix_01_layer_version_constant() -> None:
    assert wiring.MV2_RESEARCH_WIRING_LAYER_VERSION == "v1"


def test_matrix_02_owner_constant() -> None:
    assert wiring.MV2_RESEARCH_WIRING_OWNER == "backtest.mv2_research_wiring_v1"


def test_matrix_03_required_instrument_constant() -> None:
    assert wiring.MV2_REQUIRED_INSTRUMENT_ID == "inst-eth-usdt-perp"


def test_matrix_04_reject_non_step29l_instrument() -> None:
    with pytest.raises(ValueError, match="instrument_not_supported_for_step29l"):
        _run(instrument_id="inst-sol-usdt-perp")


def test_matrix_05_reject_bitcoin_instrument() -> None:
    with pytest.raises(ValueError, match="instrument_not_supported_for_step29l"):
        _run(instrument_id="inst-btc-usdt-perp")


def test_matrix_06_reject_spot_instrument() -> None:
    with pytest.raises(ValueError, match="instrument_not_supported_for_step29l"):
        _run(instrument_id="inst-eth-usdt-spot")


def test_matrix_07_fail_on_unfinalized_bar() -> None:
    bars = _bars()
    bars.loc[bars.index[0], "is_final"] = False
    with pytest.raises(ValueError, match="bar_unfinalized"):
        _run(bars=bars)


def test_matrix_08_fail_on_lookahead_decision_time() -> None:
    bars = _bars()
    bars["decision_time"] = [ts + pd.Timedelta(hours=2) for ts in bars.index]
    with pytest.raises(ValueError, match="lookahead_decision_after_market_event"):
        _run(bars=bars)


def test_matrix_09_fail_on_non_monotonic_index() -> None:
    bars = _bars().sort_index(ascending=False)
    with pytest.raises(ValueError, match="lookahead_index_not_monotonic"):
        _run(bars=bars)


def test_matrix_10_fail_on_missing_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    class _EmptyRegistry:
        entries: tuple[Any, ...] = ()

    monkeypatch.setattr(
        wiring, "build_suitability_registry_from_snapshot", lambda s: _EmptyRegistry()
    )
    with pytest.raises(ValueError, match="missing_registry"):
        _run()


def test_matrix_11_fail_on_registry_input_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="registry_input_digest_mismatch"):
        _run(expected_registry_input_digest="0" * 64)


def test_matrix_12_fail_on_registry_semantic_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="registry_semantic_digest_mismatch"):
        _run(expected_registry_semantic_digest="0" * 64)


def test_matrix_13_fail_on_cost_model_version_mismatch() -> None:
    with pytest.raises(ValueError, match="cost_model_version_mismatch"):
        _run(expected_cost_model_version="backtest_cost_v999")


def test_matrix_14_fail_on_data_layer_version_mismatch() -> None:
    with pytest.raises(ValueError, match="data_layer_version_mismatch"):
        _run(expected_data_layer_version="v999")


def test_matrix_15_fail_on_replay_layer_version_mismatch() -> None:
    with pytest.raises(ValueError, match="replay_layer_version_mismatch"):
        _run(expected_replay_layer_version="v999")


def test_matrix_16_fail_on_implementation_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="implementation_digest_mismatch"):
        _run(expected_implementation_digest="f" * 64)


def test_matrix_17_fail_on_zero_cost_without_explicit_flag() -> None:
    with pytest.raises(Exception):
        _run(cfg=_cfg(fee_bps=0.0, slippage_bps=0.0))


def test_matrix_18_allow_zero_cost_with_explicit_flag() -> None:
    result = _run(cfg=_cfg(fee_bps=0.0, slippage_bps=0.0), explicit_zero_cost_non_economic=True)
    assert result.effective_cost_config.zero_cost_explicitly_requested is True


def test_matrix_19_fail_on_unknown_strategy() -> None:
    with pytest.raises(ValueError, match="unknown_strategy"):
        _run(strategy_id="does_not_exist")


def test_matrix_20_signal_adapter_enter_long() -> None:
    ev = CanonicalTradingDecisionEvidenceV1(
        decision_id="d",
        replay_id="r",
        instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
        trading_epoch=1,
        market_context_ref="m",
        scope_initialization_ref="s",
        scope_event_ref="se",
        bull_assessment_ref="b1",
        bear_assessment_ref="b2",
        state_switch_ref="sw",
        bull_survival_ref="su1",
        bear_survival_ref="su2",
        bull_suitability_ref="sb1",
        bear_suitability_ref="sb2",
        composition_result_ref="c",
        entry_exit_policy_ref="p",
        current_scope_ref="cs",
        next_scope_ref="ns",
        previous_direction_state="NEUTRAL",
        next_direction_state="LONG_ARMED",
        selected_side="long",
        selected_strategy_ref="st",
        decision_outcome="enter_long",
        entry_or_exit_policy_ref="p",
        reason_codes=(),
        decision_precedence_trace=(),
        component_versions={},
        policy_versions={},
        config_digest="a" * 64,
        implementation_digest="b" * 64,
        input_digest="c" * 64,
        semantic_digest="",
    )
    ev = with_computed_evidence_semantic_digest(ev)
    assert wiring.map_decision_evidence_to_position_signal_v1(ev) == 1


def test_matrix_21_signal_adapter_enter_short() -> None:
    ev = replace(_run().bar_outcomes[0].evidence, decision_outcome="enter_short")
    assert wiring.map_decision_evidence_to_position_signal_v1(ev) == -1


def test_matrix_22_signal_adapter_other_to_flat() -> None:
    ev = replace(_run().bar_outcomes[0].evidence, decision_outcome="blocked")
    assert wiring.map_decision_evidence_to_position_signal_v1(ev) == 0


def test_matrix_23_end_to_end_returns_signal_series() -> None:
    result = _run()
    assert len(result.signals) == len(_bars())


def test_matrix_24_end_to_end_returns_backtest_result() -> None:
    result = _run()
    assert result.backtest_result is not None
    assert "cost_model_version" in result.backtest_result.metadata


def test_matrix_25_backtest_uses_bound_cost_config() -> None:
    result = _run()
    assert result.backtest_result.metadata["fee_bps"] == 10.0
    assert result.backtest_result.metadata["slippage_bps"] == 5.0


def test_matrix_26_registry_snapshot_bound() -> None:
    result = _run()
    assert result.registry_snapshot.registry_schema_version == "strategy_registry_v1"
    assert result.registry_snapshot.input_digest


def test_matrix_27_context_digest_is_populated() -> None:
    result = _run()
    assert result.bar_outcomes[0].context.input_digest


def test_matrix_28_evidence_digest_is_populated() -> None:
    result = _run()
    assert result.bar_outcomes[0].evidence.semantic_digest


def test_matrix_29_walk_forward_binding_valid() -> None:
    windows = wiring.bind_walk_forward_windows_v1(_bars(20), train_bars=8, test_bars=4, step_bars=4)
    assert len(windows) == 3


def test_matrix_30_walk_forward_train_invalid() -> None:
    with pytest.raises(ValueError, match="walk_forward_train_bars_invalid"):
        wiring.bind_walk_forward_windows_v1(_bars(20), train_bars=0, test_bars=4, step_bars=2)


def test_matrix_31_walk_forward_test_invalid() -> None:
    with pytest.raises(ValueError, match="walk_forward_test_bars_invalid"):
        wiring.bind_walk_forward_windows_v1(_bars(20), train_bars=8, test_bars=0, step_bars=2)


def test_matrix_32_walk_forward_step_invalid() -> None:
    with pytest.raises(ValueError, match="walk_forward_step_bars_invalid"):
        wiring.bind_walk_forward_windows_v1(_bars(20), train_bars=8, test_bars=4, step_bars=0)


def test_matrix_33_walk_forward_insufficient_data() -> None:
    with pytest.raises(ValueError, match="walk_forward_insufficient_bars"):
        wiring.bind_walk_forward_windows_v1(_bars(10), train_bars=8, test_bars=4, step_bars=2)


def test_matrix_34_monte_carlo_binding_runs() -> None:
    result = _run()
    summary = wiring.bind_monte_carlo_analysis_v1(
        result.backtest_result, wiring.MonteCarloConfig(num_runs=8, seed=42)
    )
    assert summary.num_runs > 0


def test_matrix_35_monte_carlo_binding_deterministic_seed() -> None:
    result = _run()
    cfg = wiring.MonteCarloConfig(num_runs=8, seed=42)
    s1 = wiring.bind_monte_carlo_analysis_v1(result.backtest_result, cfg)
    s2 = wiring.bind_monte_carlo_analysis_v1(result.backtest_result, cfg)
    assert s1.metric_quantiles["total_return"]["p50"] == s2.metric_quantiles["total_return"]["p50"]


def test_matrix_36_stress_binding_required_classes_supported() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(returns)
    for cls in ("single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open"):
        assert outcome.statuses[cls] != wiring.StressClassBindingStatus.UNSUPPORTED_BLOCKING


def test_matrix_37_stress_binding_marks_unknown_class_blocking() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(returns, requested_classes=("unknown_class",))
    assert outcome.statuses["unknown_class"] == wiring.StressClassBindingStatus.UNSUPPORTED_BLOCKING


def test_matrix_38_stress_binding_returns_suite_for_supported() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(returns, requested_classes=("single_crash_bar",))
    assert outcome.suite_result is not None
    assert isinstance(outcome.suite_result.scenario_results, list)


def test_matrix_39_stress_binding_keeps_required_classes_present() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(returns, requested_classes=("single_crash_bar",))
    assert set(("single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open")).issubset(
        set(outcome.statuses.keys())
    )


def test_matrix_40_stress_suite_produces_scenario_result() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(
        returns, requested_classes=("single_crash_bar", "vol_spike")
    )
    assert outcome.suite_result is not None
    assert len(outcome.suite_result.scenario_results) == 2
    assert isinstance(outcome.suite_result.scenario_results[0], StressScenarioResult)


def test_matrix_41_metrics_binding_has_total_return() -> None:
    result = _run()
    metrics = wiring.compute_mv2_backtest_metrics_v1(result.backtest_result)
    assert "total_return" in metrics


def test_matrix_42_metrics_binding_has_trade_count() -> None:
    result = _run()
    metrics = wiring.compute_mv2_backtest_metrics_v1(result.backtest_result)
    assert metrics["total_trades"] >= 0


def test_matrix_43_evidence_chain_digest_shape() -> None:
    result = _run()
    first = result.bar_outcomes[0]
    chain = wiring.compute_mv2_evidence_chain_digests_v1(
        context=first.context,
        evidence=first.evidence,
        registry_snapshot=result.registry_snapshot,
        cost_config=result.effective_cost_config,
    )
    assert "wiring_chain_digest" in chain
    assert len(chain["wiring_chain_digest"]) == 64


def test_matrix_44_evidence_chain_digest_deterministic() -> None:
    result = _run()
    first = result.bar_outcomes[0]
    chain_a = wiring.compute_mv2_evidence_chain_digests_v1(
        context=first.context,
        evidence=first.evidence,
        registry_snapshot=result.registry_snapshot,
        cost_config=result.effective_cost_config,
    )
    chain_b = wiring.compute_mv2_evidence_chain_digests_v1(
        context=first.context,
        evidence=first.evidence,
        registry_snapshot=result.registry_snapshot,
        cost_config=result.effective_cost_config,
    )
    assert chain_a["wiring_chain_digest"] == chain_b["wiring_chain_digest"]


def test_matrix_45_evidence_chain_digest_changes_with_evidence() -> None:
    result = _run()
    first = result.bar_outcomes[0]
    chain_a = wiring.compute_mv2_evidence_chain_digests_v1(
        context=first.context,
        evidence=first.evidence,
        registry_snapshot=result.registry_snapshot,
        cost_config=result.effective_cost_config,
    )
    ev2 = replace(first.evidence, decision_outcome="observe")
    ev2 = with_computed_evidence_semantic_digest(ev2)
    chain_b = wiring.compute_mv2_evidence_chain_digests_v1(
        context=first.context,
        evidence=ev2,
        registry_snapshot=result.registry_snapshot,
        cost_config=result.effective_cost_config,
    )
    assert chain_a["wiring_chain_digest"] != chain_b["wiring_chain_digest"]


def test_matrix_46_signals_are_only_minus1_zero_plus1() -> None:
    result = _run()
    assert set(result.signals.unique()).issubset({-1, 0, 1})


def test_matrix_47_outcomes_signals_are_only_minus1_zero_plus1() -> None:
    result = _run()
    assert set(o.position_signal for o in result.bar_outcomes).issubset({-1, 0, 1})


def test_matrix_48_stress_outcome_type_contract() -> None:
    returns = _run().backtest_result.equity_curve.pct_change().dropna()
    outcome = wiring.bind_stress_class_suite_v1(returns)
    assert isinstance(outcome, wiring.StressClassBindingOutcomeV1)
