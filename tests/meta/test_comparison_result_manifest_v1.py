"""Result, Pareto, and ranking tests for comparison_ssot.v1."""

from __future__ import annotations

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from src.meta.learning_loop.comparison_ssot_v1.comparison_offline_producer_v1 import (
    produce_comparison_offline_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import LEXICOGRAPHIC_RANKING_RULE_V1
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.models import ComparisonSsotError
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_result_manifest_v1
from tests.meta.comparison_ssot_v1_fixtures import (
    produce_comparison_pair,
    produce_two_compatible_backtest_inputs,
)


def test_result_happy_path(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, result_path, definition_id = produce_comparison_pair(
        tmp_path, ssot_durable_output_dir
    )
    result = read_manifest(result_path)
    validate_result_manifest_v1(result)
    assert result["comparison_definition_id"] == definition_id
    assert result["overall_comparable"] is True
    assert "pareto_result" in result
    assert result["ranking_result"]["ranking_status"] == "NONE"
    assert "winner" not in result


def test_pareto_descriptive_only(tmp_path, ssot_durable_output_dir) -> None:
    _, result_path, _ = produce_comparison_pair(tmp_path, ssot_durable_output_dir)
    result = read_manifest(result_path)
    pareto = result["pareto_result"]
    assert pareto["pareto_descriptive_only"] is True
    assert "trade_count" not in pareto["pareto_objective_metrics"]


def test_lexicographic_ranking_explicit(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "ranked"
    produced = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=out,
        ranking_rule_version=LEXICOGRAPHIC_RANKING_RULE_V1,
    )
    ranking = produced.result_manifest["ranking_result"]
    assert ranking["ranking_status"] == "LEXICOGRAPHIC"
    assert len(ranking["ranked_input_ids"]) == 2


def test_ranking_default_none(tmp_path, ssot_durable_output_dir) -> None:
    _, result_path, _ = produce_comparison_pair(tmp_path, ssot_durable_output_dir)
    result = read_manifest(result_path)
    assert result["ranking_result"]["ranking_status"] == "NONE"
    assert result["ranking_result"]["ranked_input_ids"] == []


def test_forbidden_winner_field_rejected() -> None:
    payload = {
        "comparison_contract_version": "comparison_ssot.v1",
        "comparison_definition_id": "abc",
        "input_snapshots": [
            {
                "comparison_metric_input_id": "id1",
                "source_ref": {
                    "owner_domain": "d",
                    "ref_type": "T",
                    "ref_id": "r",
                    "digest": "a" * 64,
                },
                "source_digest": "a" * 64,
                "metrics": {
                    "sharpe": 1.0,
                    "max_drawdown": 0.1,
                    "profit_factor": 1.0,
                    "total_return": 0.1,
                    "volatility": 0.2,
                    "trade_count": 1,
                },
            }
        ],
        "metric_matrix": {
            "sharpe": [1.0],
            "max_drawdown": [0.1],
            "profit_factor": [1.0],
            "total_return": [0.1],
            "volatility": [0.2],
            "trade_count": [1],
        },
        "comparability_gate_outcomes": [],
        "overall_comparable": False,
        "winner": "bad",
        "authority_invariants": {},
        "integrity": {"content_sha256": "b" * 64},
    }
    with pytest.raises(ComparisonSsotError, match="winner"):
        validate_result_manifest_v1(payload)


def test_replay_identical_result_digest(tmp_path, ssot_durable_output_dir) -> None:
    metric_root = ssot_durable_output_dir / "metrics"
    metric_root.mkdir()
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    out = ssot_durable_output_dir / "replay"
    one = produce_comparison_offline_v1(
        input_manifest_paths=[first, second], output_root=out, ranking_rule_version="NONE_V1"
    )
    two = produce_comparison_offline_v1(
        input_manifest_paths=[first, second], output_root=out, ranking_rule_version="NONE_V1"
    )
    assert one.result_manifest["integrity"] == two.result_manifest["integrity"]
