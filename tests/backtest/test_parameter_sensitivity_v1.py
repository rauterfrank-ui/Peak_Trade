"""RUNBOOK STEP 29M — deterministic offline parameter sensitivity v1 tests."""

from __future__ import annotations

import json
import math
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import economic_validity_policy_v1 as policy_mod
from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest import parameter_sensitivity_v1 as ps


def _bars(n: int = 24) -> pd.DataFrame:
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
            "bar_interval": ["1h" for _ in close],
        },
        index=idx,
    )


def _cfg(*, bind: bool = True) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
    }
    if bind:
        payload["backtest"]["parameter_sensitivity"] = {
            "bind": True,
            "grid_version": ps.DEFAULT_GRID_VERSION,
            "grid": {
                "grid_id": "test_grid_v1",
                "parameter_names": ["fee_bps", "slippage_bps"],
                "parameter_values": [[8.0, 10.0], [4.0, 6.0]],
                "search_space_bounds": {
                    "fee_bps": {"min": 8.0, "max": 10.0},
                    "slippage_bps": {"min": 4.0, "max": 6.0},
                },
                "seed": 42,
            },
        }
    return payload


def _cfg_policy_unbound(**kwargs: Any) -> Mapping[str, Any]:
    cfg = dict(_cfg(**kwargs))
    cfg["economic_validity_policy"] = {"explicit_unbound": True}
    return cfg


class TestParameterGridContract:
    def test_binding_requested(self) -> None:
        assert ps.parameter_sensitivity_binding_requested(_cfg()) is True
        assert ps.parameter_sensitivity_binding_requested(_cfg(bind=False)) is False

    def test_cartesian_product_count(self) -> None:
        grid = ps.build_parameter_grid_v1(
            strategy_id="ma_crossover",
            strategy_version="v1",
            cfg=_cfg(),
            bars=_bars(),
            data_digest="abc",
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            grid_spec=_cfg()["backtest"]["parameter_sensitivity"]["grid"],
        )
        assert grid.combination_count == 4

    def test_stable_grid_order(self) -> None:
        spec = _cfg()["backtest"]["parameter_sensitivity"]["grid"]
        a = ps._iter_grid_combinations(spec["parameter_names"], spec["parameter_values"])
        b = ps._iter_grid_combinations(spec["parameter_names"], spec["parameter_values"])
        assert a == b

    def test_duplicate_values_rejected(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="duplicate_parameter_value"):
            ps._canonicalize_values([1.0, 1.0])

    def test_nan_rejected(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="parameter_value_non_finite"):
            ps._canonicalize_values([1.0, float("nan")])

    def test_inf_rejected(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="parameter_value_non_finite"):
            ps._canonicalize_values([1.0, float("inf")])

    def test_empty_parameter_list_rejected(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="empty_parameter_list"):
            ps.build_parameter_grid_v1(
                strategy_id="ma_crossover",
                strategy_version="v1",
                cfg=_cfg(),
                bars=_bars(),
                data_digest="abc",
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
                grid_spec={"parameter_names": [], "parameter_values": []},
            )

    def test_out_of_bounds_rejected(self) -> None:
        spec = dict(_cfg()["backtest"]["parameter_sensitivity"]["grid"])
        spec["parameter_values"] = [[100.0], [5.0]]
        with pytest.raises(ps.ParameterSensitivityError, match="parameter_value_out_of_bounds"):
            ps.build_parameter_grid_v1(
                strategy_id="ma_crossover",
                strategy_version="v1",
                cfg=_cfg(),
                bars=_bars(),
                data_digest="abc",
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
                grid_spec=spec,
            )

    def test_forbidden_bitcoin_instrument(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="instrument_kind_forbidden"):
            ps.build_parameter_grid_v1(
                strategy_id="ma_crossover",
                strategy_version="v1",
                cfg=_cfg(),
                bars=_bars(),
                data_digest="abc",
                instrument_id="inst-btc-usdt-perp",
            )


class TestParameterSensitivityExecution:
    def test_run_full_grid_persistence(self) -> None:
        bars = _bars()
        digest = "0" * 64
        result = ps.run_parameter_sensitivity_v1(
            bars=bars,
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest=digest,
        )
        assert result.combination_count == 4
        assert len(result.points) == 4
        assert result.full_grid_persisted is True
        assert result.pipeline_status is ps.PipelineStatus.PIPELINE_PASS

    def test_failed_points_persisted(self) -> None:
        bars = _bars(6)
        with pytest.raises(ps.ParameterSensitivityError, match="insufficient_bars"):
            ps.run_parameter_sensitivity_v1(
                bars=bars,
                cfg=_cfg(),
                strategy_id="ma_crossover",
                strategy_version="v1",
                data_digest="0" * 64,
            )

    def test_missing_data_fail_closed(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="missing_data_digest"):
            ps.run_parameter_sensitivity_v1(
                bars=_bars(),
                cfg=_cfg(),
                strategy_id="ma_crossover",
                strategy_version="v1",
                data_digest="",
            )

    def test_missing_grid_fail_closed(self) -> None:
        cfg = _cfg(bind=False)
        with pytest.raises(ps.ParameterSensitivityError, match="missing_parameter_grid"):
            ps.load_parameter_grid_v1(
                cfg,
                strategy_id="ma_crossover",
                strategy_version="v1",
                bars=_bars(),
                data_digest="0" * 64,
                instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            )

    def test_deterministic_seed_and_digest(self) -> None:
        bars = _bars()
        digest = "abc123"
        a = ps.run_parameter_sensitivity_v1(
            bars=bars,
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest=digest,
        )
        b = ps.run_parameter_sensitivity_v1(
            bars=bars,
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest=digest,
        )
        assert a.result_digest == b.result_digest
        assert a.grid_digest == b.grid_digest

    def test_no_best_result_only_serialization(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        payload = result.to_dict()
        assert "points" in payload
        assert len(payload["points"]) == result.combination_count
        assert "best_parameter" not in payload

    def test_policy_robustness_blocked_without_thresholds(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg_policy_unbound(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        assert result.parameter_robustness_policy_pass is False
        assert (
            result.parameter_robustness_policy_status == policy_mod.POLICY_THRESHOLD_STATUS_BLOCKED
        )

    def test_pipeline_pass_not_policy_pass(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg_policy_unbound(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        assert result.pipeline_status is ps.PipelineStatus.PIPELINE_PASS
        assert result.parameter_robustness_policy_pass is False

    def test_oos_isolation_metadata(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        assert result.oos_tuning_forbidden is True
        for point in result.points:
            assert point.out_of_sample_result_ref.endswith(":out_of_sample")

    def test_non_finite_metrics_not_zero_filled(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        for point in result.points:
            if point.net_return is ps.MetricValueStatus.COMPUTED:
                assert point.net_return_value is not None
                assert math.isfinite(point.net_return_value)
            else:
                assert point.net_return_value is None or math.isfinite(point.net_return_value)

    def test_serialization_round_trip(self) -> None:
        result = ps.run_parameter_sensitivity_v1(
            bars=_bars(),
            cfg=_cfg(),
            strategy_id="ma_crossover",
            strategy_version="v1",
            data_digest="0" * 64,
        )
        payload = ps.serialize_parameter_sensitivity_results_v1(result)
        encoded = json.dumps(payload, sort_keys=True)
        decoded = json.loads(encoded)
        assert decoded["combination_count"] == 4
        assert decoded["pipeline_status"] == "PIPELINE_PASS"


class TestTrainValidationOosSplit:
    def test_split_lengths(self) -> None:
        train, validation, oos = ps.split_bars_train_validation_oos_v1(_bars(24))
        assert len(train) >= ps.MIN_BARS_PER_SPLIT
        assert len(validation) >= ps.MIN_BARS_PER_SPLIT
        assert len(oos) >= ps.MIN_BARS_PER_SPLIT

    def test_insufficient_bars_fail_closed(self) -> None:
        with pytest.raises(ps.ParameterSensitivityError, match="insufficient_bars"):
            ps.split_bars_train_validation_oos_v1(_bars(8))
