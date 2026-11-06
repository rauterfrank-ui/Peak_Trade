"""Actual computed split metrics survive through the optional observation port."""

import math
from copy import deepcopy

import pytest

from src.backtest import parameter_sensitivity_v1 as ps
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg
from tests.backtest.test_parameter_sensitivity_v1 import _bars as small_bars
from tests.backtest.test_parameter_sensitivity_v1 import _cfg as small_cfg


def _inputs():
    bars = _bars(768)
    prices = [100 + 5 * math.sin(i / 12) + 0.01 * i for i in range(len(bars))]
    for key in ("open", "close", "mark_price", "index_price"):
        bars[key] = prices
    bars["high"] = [p + 0.5 for p in prices]
    bars["low"] = [p - 0.5 for p in prices]
    bars["best_bid"] = [p - 0.05 for p in prices]
    bars["best_ask"] = [p + 0.05 for p in prices]
    bars["bar_interval"] = "1h"
    cfg = deepcopy(_cfg())
    cfg["risk"]["risk_per_trade"] = 0.002
    cfg["economic_evaluation_v1"]["strategy_params"] = {
        "fast_window": 10,
        "slow_window": 50,
    }
    cfg["backtest"]["parameter_sensitivity"] = {
        "bind": True,
        "grid_version": "v1",
        "grid": {
            "grid_id": "explicit_native_name_synthetic_probe_v1",
            "parameter_names": ["strategy.fast_window", "strategy.slow_window"],
            "parameter_values": [[10], [50, 100]],
            "search_space_bounds": {
                "strategy.fast_window": {"min": 2, "max": 200},
                "strategy.slow_window": {"min": 3, "max": 500},
            },
            "seed": 12,
        },
    }
    return bars, cfg


def _run(bars, cfg, observer):
    return ps.run_parameter_sensitivity_v1(
        bars=bars,
        cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        data_digest="controlled_test_only_not_natural_source_authentication",
        split_result_observer=observer,
    )


def test_actual_split_outputs_are_read_only_and_match_computed_owner(monkeypatch):
    bars, cfg = _inputs()
    owner_outputs = []
    actual_metrics = ps.mv2_wiring.compute_mv2_backtest_metrics_v1

    def observe_actual_owner(result):
        metrics = actual_metrics(result)
        owner_outputs.append(dict(metrics))
        return metrics

    monkeypatch.setattr(ps.mv2_wiring, "compute_mv2_backtest_metrics_v1", observe_actual_owner)
    observations = []

    def collect(observation):
        with pytest.raises(TypeError):
            observation["bar_count"] = 0
        with pytest.raises(TypeError):
            observation["metrics"]["sharpe"] = 999
        observations.append(observation)

    result = _run(bars, cfg, collect)
    assert result.failed_point_count == 0
    assert len(owner_outputs) == len(observations) == 6
    assert [row["bar_count"] for row in observations] == [384, 192, 192] * 2
    for measured, observed in zip(owner_outputs, observations):
        for metric, value in measured.items():
            actual = observed["metrics"][metric]
            assert math.isnan(actual) if math.isnan(value) else actual == value
    for point in result.points:
        rows = [row for row in observations if row["parameter_set_id"] == point.parameter_set_id]
        assert [row["split_name"] for row in rows] == ["train", "validation", "out_of_sample"]
        assert [row["result_ref"] for row in rows] == [
            point.train_result_ref,
            point.validation_result_ref,
            point.out_of_sample_result_ref,
        ]
        assert rows[0]["period_end"] < rows[1]["period_start"]
        assert rows[1]["period_end"] < rows[2]["period_start"]
        assert rows[2]["metrics"]["total_return"] == point.net_return_value
        assert rows[2]["metrics"]["total_trades"] == point.trade_count_value
        assert rows[2]["funding_model_ref"] == "NOT_BOUND"


def test_failed_evaluation_emits_no_fabricated_split_metrics():
    observations = []
    result = _run(small_bars(), small_cfg(), observations.append)
    assert result.failed_point_count == result.combination_count == 4
    assert observations == []


def test_later_observer_failure_retains_partial_evidence_and_failed_point():
    bars, cfg = _inputs()
    observations = []

    def reject_validation(row):
        if row["split_name"] == "validation":
            raise RuntimeError("CONTROL_COLLECTION_FAILED")
        observations.append(row)

    result = _run(bars, cfg, reject_validation)
    assert result.failed_point_count == result.combination_count == 2
    assert len(observations) == 2
    assert all(row["split_name"] == "train" for row in observations)
    assert all(
        "evaluation_failed:CONTROL_COLLECTION_FAILED" in point.reason_codes
        for point in result.points
    )
    evaluated_ids = {
        point.parameter_set_id
        for point in result.points
        if point.evaluation_status is ps.EvaluationStatus.EVALUATED
    }
    assert not [row for row in observations if row["parameter_set_id"] in evaluated_ids]
