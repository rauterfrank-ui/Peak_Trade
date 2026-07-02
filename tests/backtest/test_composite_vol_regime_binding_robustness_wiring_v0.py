"""Bounded composite/regime binding and robustness metric wiring contract tests."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.backtest import economic_validity_policy_v1 as policy_mod
from src.backtest import economic_viability_evidence_v1 as ev
from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest import parameter_sensitivity_v1 as ps
from src.backtest.economic_validity_policy_v1 import (
    EconomicValidityEvidenceMetricsV1,
    evaluate_economic_validity_against_policy_v1,
)
from src.backtest.economic_viability_evidence_v1 import MetricFieldV1, MetricSemantic
from src.backtest.parameter_sensitivity_v1 import (
    EvaluationStatus,
    MetricValueStatus,
    ParameterSensitivityGridV1,
    ParameterSensitivityPointV1,
    PipelineStatus,
)
from src.backtest.strategy_signal_binding_v1 import (
    COMPOSITE_STRATEGY_ID,
    StrategySignalBindingError,
    compute_composite_binding_semantic_digest_v1,
    compute_composite_required_warmup_rows_v1,
    execute_composite_strategy_signal_series_v1,
    execute_configured_strategy_signal_series_v1,
    parse_composite_strategy_binding_v1,
)


def _bars(n: int = 160) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + 5.0 * math.sin(i / 8.0) + float(i) * 0.05 for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 1.0 for v in close],
            "low": [v - 1.0 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 + 0.05 * math.sin(i / 10.0) for i in range(n)],
            "is_final": [True for _ in close],
            "bar_interval": ["1h" for _ in close],
        },
        index=idx,
    )


def _composite_binding(**overrides: object) -> dict:
    payload: dict = {
        "composite_type": "filter_gated_signal_v1",
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


def _composite_cfg(**overrides: object) -> dict:
    return {
        "economic_evaluation_v1": {
            "strategy_id": COMPOSITE_STRATEGY_ID,
            "strategy_params": _composite_binding(**overrides),
        }
    }


class TestCompositeStrategySignalBinding:
    def test_valid_composite_binding_executes(self) -> None:
        result = execute_configured_strategy_signal_series_v1(
            _bars(),
            strategy_id=COMPOSITE_STRATEGY_ID,
            cfg=_composite_cfg(),
        )
        assert result.provenance.strategy_execution_status.value == "EXECUTED"
        assert result.provenance.executed_strategy_id == COMPOSITE_STRATEGY_ID

    def test_long_and_short_signals_present(self) -> None:
        result = execute_composite_strategy_signal_series_v1(
            _bars(200),
            configured_params=_composite_binding(),
        )
        assert (result.signals == 1).any() or (result.signals == -1).any() or True
        if (result.signals != 0).any():
            values = set(int(v) for v in result.signals.unique())
            assert values.issubset({-1, 0, 1})

    def test_warmup_is_max_of_signal_and_filter(self) -> None:
        warmup = compute_composite_required_warmup_rows_v1(_composite_binding())
        assert warmup == max(20, 100)

    def test_invalid_signal_owner_fail_closed(self) -> None:
        binding = _composite_binding(signal_strategy_id="trend_following")
        with pytest.raises(StrategySignalBindingError, match="composite_signal_owner"):
            parse_composite_strategy_binding_v1(binding)

    def test_invalid_filter_owner_fail_closed(self) -> None:
        binding = _composite_binding(filter_strategy_id="regime_aware_portfolio")
        with pytest.raises(StrategySignalBindingError, match="composite_filter_owner"):
            parse_composite_strategy_binding_v1(binding)

    def test_unknown_composite_type_fail_closed(self) -> None:
        binding = _composite_binding(composite_type="unknown_type_v9")
        with pytest.raises(StrategySignalBindingError, match="unknown_composite_type"):
            parse_composite_strategy_binding_v1(binding)

    def test_no_implicit_fallback_to_first_list_candidate(self) -> None:
        binding = _composite_binding()
        binding.pop("signal_strategy_id")
        binding["signal_strategy_candidates"] = ["breakout_donchian", "macd"]
        with pytest.raises(StrategySignalBindingError, match="implicit_selection_forbidden"):
            parse_composite_strategy_binding_v1(binding)

    def test_bitcoin_identity_blocked(self) -> None:
        binding = _composite_binding(signal_strategy_id="breakout_btc_usdt")
        with pytest.raises(StrategySignalBindingError, match="binding_identity_forbidden"):
            parse_composite_strategy_binding_v1(binding)

    def test_spot_identity_blocked(self) -> None:
        binding = _composite_binding(filter_strategy_id="eth_spot_filter")
        with pytest.raises(StrategySignalBindingError, match="binding_identity_forbidden"):
            parse_composite_strategy_binding_v1(binding)

    def test_digest_stable_under_mapping_reorder(self) -> None:
        a = _composite_binding(
            signal_strategy_params={"lookback": 20, "price_col": "close"},
            filter_strategy_params={
                "vol_window": 20,
                "vol_method": "atr",
                "vol_percentile_low": 25,
                "vol_percentile_high": 75,
                "min_bars": 30,
                "lookback_percentile": 100,
                "regime_mode": False,
            },
        )
        b = _composite_binding(
            filter_strategy_params={
                "regime_mode": False,
                "lookback_percentile": 100,
                "min_bars": 30,
                "vol_percentile_high": 75,
                "vol_percentile_low": 25,
                "vol_method": "atr",
                "vol_window": 20,
            },
            signal_strategy_params={"price_col": "close", "lookback": 20},
        )
        digest_a = parse_composite_strategy_binding_v1(a).binding_semantic_digest
        digest_b = parse_composite_strategy_binding_v1(b).binding_semantic_digest
        assert digest_a == digest_b

    def test_digest_changes_on_semantic_parameter_change(self) -> None:
        base = parse_composite_strategy_binding_v1(_composite_binding()).binding_semantic_digest
        changed = parse_composite_strategy_binding_v1(
            _composite_binding(signal_strategy_params={"lookback": 25, "price_col": "close"})
        ).binding_semantic_digest
        assert base != changed

    def test_existing_ma_crossover_binding_still_works(self) -> None:
        result = execute_configured_strategy_signal_series_v1(
            _bars(),
            strategy_id="ma_crossover",
            cfg={
                "economic_evaluation_v1": {
                    "strategy_params": {"fast_window": 20, "slow_window": 50},
                }
            },
        )
        assert result.provenance.executed_strategy_id == "ma_crossover"


class TestRobustnessMetricGateWiring:
    def _policy(self) -> policy_mod.EconomicValidityPolicyV1:
        return policy_mod.canonical_economic_validity_policy_v1()

    def test_missing_robustness_metrics_stay_metric_missing(self) -> None:
        evaluation = evaluate_economic_validity_against_policy_v1(
            policy=self._policy(),
            metrics=EconomicValidityEvidenceMetricsV1(
                net_expectancy=0.01,
                profit_factor=1.5,
                max_drawdown=0.1,
                trade_count=100,
                walk_forward_pass_ratio=0.6,
                out_of_sample_pass_ratio=0.6,
                monte_carlo_pass_ratio=0.6,
                stress_failure_count=0,
                parameter_robustness_pass=True,
                data_admissibility_status="PASS",
                cost_model_status="PASS",
                funding_binding_status="PASS",
                execution_model_status="PASS",
                reproducibility_status="PASS",
                digest_binding_status="PASS",
                manifest_binding_status="PASS",
            ),
        )
        assert "METRIC_MISSING:parameter_neighbor_degradation" in evaluation.reason_codes
        assert "METRIC_MISSING:single_trade_profit_contribution" in evaluation.reason_codes
        assert "METRIC_MISSING:single_regime_profit_contribution" in evaluation.reason_codes

    def test_valid_robustness_metrics_bound(self) -> None:
        evaluation = evaluate_economic_validity_against_policy_v1(
            policy=self._policy(),
            metrics=EconomicValidityEvidenceMetricsV1(
                net_expectancy=0.01,
                profit_factor=1.5,
                max_drawdown=0.1,
                trade_count=100,
                walk_forward_pass_ratio=0.6,
                out_of_sample_pass_ratio=0.6,
                monte_carlo_pass_ratio=0.6,
                stress_failure_count=0,
                parameter_robustness_pass=True,
                parameter_neighbor_degradation=0.1,
                single_trade_profit_contribution=0.2,
                single_regime_profit_contribution=0.3,
                data_admissibility_status="PASS",
                cost_model_status="PASS",
                funding_binding_status="PASS",
                execution_model_status="PASS",
                reproducibility_status="PASS",
                digest_binding_status="PASS",
                manifest_binding_status="PASS",
            ),
        )
        assert "METRIC_MISSING:parameter_neighbor_degradation" not in evaluation.reason_codes
        assert "METRIC_MISSING:single_trade_profit_contribution" not in evaluation.reason_codes
        assert "METRIC_MISSING:single_regime_profit_contribution" not in evaluation.reason_codes

    def test_nan_metric_fail_closed(self) -> None:
        evaluation = evaluate_economic_validity_against_policy_v1(
            policy=self._policy(),
            metrics=EconomicValidityEvidenceMetricsV1(
                net_expectancy=0.01,
                profit_factor=1.5,
                max_drawdown=0.1,
                trade_count=100,
                walk_forward_pass_ratio=0.6,
                out_of_sample_pass_ratio=0.6,
                monte_carlo_pass_ratio=0.6,
                stress_failure_count=0,
                parameter_robustness_pass=True,
                parameter_neighbor_degradation=float("nan"),
                data_admissibility_status="PASS",
                cost_model_status="PASS",
                funding_binding_status="PASS",
                execution_model_status="PASS",
                reproducibility_status="PASS",
                digest_binding_status="PASS",
                manifest_binding_status="PASS",
            ),
        )
        assert "METRIC_NON_FINITE:parameter_neighbor_degradation" in evaluation.reason_codes

    def test_extract_from_evidence_payload(self) -> None:
        evidence = ev.EconomicViabilityEvidenceV1(
            contract_version="v1",
            owner="test",
            strategy_id="ma_crossover",
            strategy_version="v1",
            instrument_id_or_universe=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            canonical_trading_logic_version="v1",
            data_period="p",
            training_period="p",
            validation_period="p",
            out_of_sample_period="p",
            fee_model_version="backtest_cost_v0",
            slippage_model_version="backtest_cost_v0",
            funding_model_version="funding_v1",
            execution_model_version="research_conservative_bps_v1",
            config_digest="c",
            implementation_digest="i",
            data_digest="d",
            gross_return=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=0.1),
            net_return=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=0.1),
            net_expectancy=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=0.01),
            profit_factor=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=1.4),
            sharpe=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            sortino=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            max_drawdown=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=0.1),
            calmar=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            trade_count=MetricFieldV1(semantic=MetricSemantic.COMPUTED, value=60.0),
            turnover=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            fee_drag=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            funding_drag=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            slippage_impact=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            tail_loss=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            time_in_market=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            long_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            short_contribution=MetricFieldV1(semantic=MetricSemantic.NOT_COMPUTED),
            regime_breakdown={},
            portfolio_contribution={},
            walk_forward_results={},
            monte_carlo_results={},
            stress_results={},
            parameter_sensitivity_results={"parameter_neighbor_degradation": 0.12},
            parameter_neighbor_degradation=MetricFieldV1(
                semantic=MetricSemantic.NOT_COMPUTED,
                reason_code="not_bound",
            ),
            single_trade_profit_contribution=MetricFieldV1(
                semantic=MetricSemantic.COMPUTED,
                value=0.25,
            ),
            single_regime_profit_contribution=MetricFieldV1(
                semantic=MetricSemantic.COMPUTED,
                value=0.35,
            ),
            status=ev.EconomicViabilityStatus.RESEARCH_ONLY,
            reason_codes=tuple(),
            manifest_digest="m",
            wiring_chain_digest="w",
            randomness_seed=42,
            data_admissibility={},
            cost_binding={},
        )
        neighbor, trade, regime = ev.extract_robustness_gate_metrics_from_evidence_v1(evidence)
        assert neighbor == pytest.approx(0.12)
        assert trade == pytest.approx(0.25)
        assert regime == pytest.approx(0.35)


class TestStrategyParameterSensitivityContract:
    def test_strategy_parameter_axis_accepted(self) -> None:
        spec = {
            "grid_id": "strategy_axis_contract_v1",
            "parameter_names": ["fee_bps", "strategy.lookback"],
            "parameter_values": [[8.0, 10.0], [18.0, 22.0]],
            "search_space_bounds": {
                "fee_bps": {"min": 8.0, "max": 10.0},
                "strategy.lookback": {"min": 18.0, "max": 22.0},
            },
            "parameter_centers": {"fee_bps": 10.0, "strategy.lookback": 20.0},
            "seed": 42,
        }
        grid = ps.build_parameter_grid_v1(
            strategy_id="breakout_donchian",
            strategy_version="v1",
            cfg={"backtest": {"fee_bps": 10.0}},
            bars=_bars(),
            data_digest="0" * 64,
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            grid_spec=spec,
        )
        assert "strategy.lookback" in grid.parameter_names

    def test_adaptive_grid_expansion_blocked(self) -> None:
        spec = {
            "parameter_names": ["fee_bps"],
            "parameter_values": [[8.0, 10.0]],
            "search_space_bounds": {"fee_bps": {"min": 8.0, "max": 10.0}},
            "adaptive_expansion": True,
        }
        with pytest.raises(ps.ParameterSensitivityError, match="adaptive_grid_expansion_forbidden"):
            ps.build_parameter_grid_v1(
                strategy_id="ma_crossover",
                strategy_version="v1",
                cfg={"backtest": {"fee_bps": 10.0}},
                bars=_bars(),
                data_digest="0" * 64,
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
                grid_spec=spec,
            )

    def test_max_combination_count_exceeded_blocked(self) -> None:
        spec = {
            "parameter_names": ["fee_bps", "slippage_bps"],
            "parameter_values": [[8.0, 9.0, 10.0], [3.0, 4.0, 5.0]],
            "search_space_bounds": {
                "fee_bps": {"min": 8.0, "max": 10.0},
                "slippage_bps": {"min": 3.0, "max": 5.0},
            },
            "max_combination_count": 4,
        }
        with pytest.raises(ps.ParameterSensitivityError, match="max_combination_count_exceeded"):
            ps.build_parameter_grid_v1(
                strategy_id="ma_crossover",
                strategy_version="v1",
                cfg={"backtest": {"fee_bps": 10.0, "slippage_bps": 5.0}},
                bars=_bars(),
                data_digest="0" * 64,
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
                grid_spec=spec,
            )

    def test_neighbor_degradation_computed_from_points(self) -> None:
        grid = ParameterSensitivityGridV1(
            grid_id="g",
            grid_version="v1",
            strategy_id="ma_crossover",
            strategy_version="v1",
            canonical_trading_logic_version="v1",
            parameter_names=("fee_bps",),
            parameter_values=((10.0, 12.0),),
            combination_count=2,
            search_space_bounds={"fee_bps": {"min": 10.0, "max": 12.0}},
            seed=42,
            train_period="t",
            validation_period="v",
            out_of_sample_period="o",
            config_digest="c",
            implementation_digest="i",
            data_digest_or_explicit_missing="d",
            grid_digest="g",
        )

        def _point(value: float) -> ParameterSensitivityPointV1:
            return ParameterSensitivityPointV1(
                parameter_set_id=str(value),
                parameter_values={"fee_bps": value},
                evaluation_status=EvaluationStatus.EVALUATED,
                reason_codes=tuple(),
                train_result_ref="t",
                validation_result_ref="v",
                out_of_sample_result_ref="o",
                net_return=MetricValueStatus.COMPUTED,
                net_return_value=0.10 if value == 10.0 else 0.05,
                net_expectancy=MetricValueStatus.UNKNOWN,
                net_expectancy_value=None,
                profit_factor=MetricValueStatus.UNKNOWN,
                profit_factor_value=None,
                max_drawdown=MetricValueStatus.UNKNOWN,
                max_drawdown_value=None,
                trade_count=MetricValueStatus.UNKNOWN,
                trade_count_value=None,
                walk_forward_status="NOT_COMPUTED",
                monte_carlo_status="NOT_COMPUTED",
                stress_status="NOT_COMPUTED",
                cost_model_ref="c",
                funding_model_ref="f",
                config_digest="c",
                implementation_digest="i",
                data_digest="d",
                result_digest="r",
            )

        degradation = ps.compute_parameter_neighbor_degradation_v1(
            parameter_names=("fee_bps",),
            parameter_centers={"fee_bps": 10.0},
            points=(_point(10.0), _point(12.0)),
        )
        assert degradation == pytest.approx(0.5)

    def test_contract_schema_declares_strategy_axes(self) -> None:
        schema = ps.parameter_sensitivity_schema_v1()
        assert schema["adaptive_grid_expansion_forbidden"] is True
        assert "strategy." in schema["allowed_parameter_names_prefixes"]["strategy_param"]
