"""Boundary + freeze tests for regime-gated standaside DEVELOPMENT evaluation v1.

No holdout access. No full panel backtest in unit tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.research.regime_gated_standaside_mr_development_evaluation_v1.decision_v1 import (
    decide_development_evaluation,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
    REQUIRED_DATASET_ID,
    assert_not_holdout_path,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.entry_eligibility_gate_v1 import (
    apply_standaside_gate_to_signals,
)
from src.research.regime_gated_standaside_mr_development_evaluation_v1.regime_features_v1 import (
    REGIME_RANGE,
    REGIME_TREND,
    assert_thresholds_match_contract,
    feature_formula_sha256,
    formula_freeze_payload,
    regime_labels_from_close,
)
from src.research.regime_gated_standaside_mr_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HypothesisPreregistrationError,
    HOLDOUT_OPAQUE_ID,
)

REPO = Path(__file__).resolve().parents[2]


def test_feature_formula_freeze_stable() -> None:
    a = feature_formula_sha256()
    b = feature_formula_sha256()
    assert a == b
    assert len(a) == 64
    payload = formula_freeze_payload()
    assert payload["feature_formula_sha256"] == a
    assert payload["threshold_adjustment_forbidden"] is True


def test_thresholds_match_preregistered_contract() -> None:
    contract = json.loads((REPO / CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    assert_thresholds_match_contract(contract)


def test_holdout_paths_fail_closed() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        assert_not_holdout_path(HOLDOUT_OPAQUE_ID)
    with pytest.raises(HypothesisPreregistrationError):
        assert_not_holdout_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/x.json"
        )


def test_regime_gate_zeros_outside_range() -> None:
    idx = pd.date_range("2023-01-01", periods=5, freq="h", tz="UTC")
    signals = pd.Series([1, -1, 1, -1, 1], index=idx)
    labels = pd.Series(
        [REGIME_RANGE, REGIME_TREND, REGIME_RANGE, REGIME_TREND, REGIME_RANGE],
        index=idx,
    )
    gated = apply_standaside_gate_to_signals(signals, labels)
    assert list(gated) == [1, 0, 1, 0, 1]


def test_regime_labels_causal_warmup() -> None:
    idx = pd.date_range("2023-01-01", periods=200, freq="h", tz="UTC")
    vals = [100.0]
    for i in range(1, 200):
        vals.append(vals[-1] * (1.0 + (0.0005 if i > 100 else 0.0)))
    close = pd.Series(vals, index=idx)
    labels = regime_labels_from_close(close)
    assert labels.iloc[:167].eq(REGIME_TREND).all()  # warmup => stand aside
    assert set(labels.unique()) <= {REGIME_RANGE, REGIME_TREND}


def test_decision_inconclusive_low_trades() -> None:
    out = decide_development_evaluation(
        baseline={
            "trade_count": 10,
            "net_return": 0.01,
            "max_drawdown": -0.02,
            "turnover": 10,
            "cost_drag": 1.0,
        },
        treatment={
            "trade_count": 8,
            "net_return": 0.02,
            "max_drawdown": -0.01,
            "turnover": 8,
            "cost_drag": 0.5,
        },
        minimum_trade_count=50,
        materiality_epsilon_net_return_abs=0.005,
    )
    assert out["result_class"] == "INCONCLUSIVE"


def test_decision_pass_all_requires() -> None:
    out = decide_development_evaluation(
        baseline={
            "trade_count": 100,
            "net_return": 0.01,
            "max_drawdown": -0.05,
            "turnover": 100.0,
            "cost_drag": 10.0,
        },
        treatment={
            "trade_count": 80,
            "net_return": 0.009,
            "max_drawdown": -0.04,
            "turnover": 70.0,
            "cost_drag": 7.0,
        },
        minimum_trade_count=50,
        materiality_epsilon_net_return_abs=0.005,
    )
    assert out["result_class"] == "PASS"


def test_dataset_id_constant() -> None:
    assert REQUIRED_DATASET_ID == (
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
