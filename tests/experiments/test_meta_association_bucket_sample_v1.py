"""Independent test/metric buckets cannot pool counts to satisfy a claim minimum."""
from dataclasses import replace

from src.experiments.canonical_meta_learning_v1 import (
    build_canonical_meta_learning_v1, QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION,
    QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION,
)
from tests.experiments.test_canonical_meta_learning_v1 import _identity, _unit, _request, _question


def _build(metric_names):
    identities = tuple(_identity(seed=200 + i) for i in range(len(metric_names)))
    units = []
    for identity, name in zip(identities, metric_names, strict=True):
        unit = _unit(identity)
        units.append(replace(unit, backtest_metrics={name: 1.2}, later_outcome=replace(unit.later_outcome, metric_name=name)))
    return build_canonical_meta_learning_v1(_request(identities=identities, units=tuple(units)))


def test_many_robustness_tests_on_one_experiment_do_not_create_large_sample():
    question = _question(_build(("sharpe",)), QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION)
    assert question["evidence_status"] == "INSUFFICIENT_SAMPLE"
    assert question["claim_type"] == "NONE"
    assert question["findings"] == [] and question["research_proposals"] == []


def test_different_metrics_do_not_share_paired_sample_counts():
    question = _question(_build(("sharpe", "profit_factor")), QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION)
    assert question["evidence_status"] == "INSUFFICIENT_SAMPLE"
    assert question["claim_type"] == "NONE"
    assert question["findings"] == [] and question["research_proposals"] == []


def test_supported_metric_cannot_rescue_sparse_other_metric():
    question = _question(_build(("sharpe", "sharpe", "profit_factor")), QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION)
    assert question["evidence_status"] == "COMPUTED"
    assert [finding["metric_name"] for finding in question["findings"]] == ["sharpe"]
    assert question["findings"][0]["n_pairs"] == 2


def test_supported_same_metric_still_emits_weak_association():
    question = _question(_build(("sharpe", "sharpe")), QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION)
    assert question["evidence_status"] == "COMPUTED"
    assert question["claim_type"] == "ASSOCIATION" and question["claim_strength"] == "WEAK"
    assert question["findings"][0]["n_pairs"] == 2
