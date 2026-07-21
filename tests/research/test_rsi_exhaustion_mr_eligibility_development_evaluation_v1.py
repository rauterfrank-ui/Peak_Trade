"""Boundary + freeze tests for RSI-exhaustion MR eligibility DEVELOPMENT evaluation v1.

No holdout access. No full panel backtest in unit tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (
    REQUIRED_DATASET_ID,
    assert_not_holdout_path,
)
from src.research.entry_effective_mr_eligibility_hypothesis_preregistration_v1 import (
    HypothesisPreregistrationError as EntryEffectiveHoldoutError,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.decision_v1 import (
    REASON_INSUFFICIENT_CONTROL_TRADE_COUNT,
    REASON_NO_DIVERGENCE,
    REASON_PROFIT_FACTOR_NOT_IMPROVED,
    RESULT_FAIL,
    RESULT_INCONCLUSIVE,
    RESULT_PASS,
    decide_development_evaluation,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.entry_eligibility_gate_v1 import (
    apply_eligibility_gate_to_signals,
    apply_eligibility_to_mapped_position_signal,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.panel_runner_v1 import (
    _optional_treatment_entry_eligibility_gate,
)
from src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.rsi_exhaustion_eligibility_filter_v1 import (
    ELIGIBLE,
    FILTER_ID,
    REQUIRED_FROZEN,
    STAND_ASIDE,
    assert_frozen_parameters_match_contract,
    eligibility_labels_from_bars,
    eligibility_mask_from_rsi,
    feature_formula_sha256,
    formula_freeze_payload,
)
from src.research.rsi_exhaustion_mr_eligibility_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HOLDOUT_OPAQUE_ID,
)

REPO = Path(__file__).resolve().parents[2]


def _contract() -> dict:
    return json.loads((REPO / CONTRACT_REL_PATH).read_text(encoding="utf-8"))


def test_feature_formula_freeze_stable() -> None:
    a = feature_formula_sha256()
    b = feature_formula_sha256()
    assert a == b
    assert len(a) == 64
    payload = formula_freeze_payload()
    assert payload["feature_formula_sha256"] == a
    assert payload["threshold_adjustment_forbidden"] is True
    assert payload["wilder_smoothing_excluded"] is True


def test_frozen_parameters_match_preregistered_contract() -> None:
    contract = _contract()
    assert_frozen_parameters_match_contract(contract)
    assert contract["eligibility_filter"]["filter_id"] == FILTER_ID


def test_frozen_parameters_constant_values() -> None:
    assert REQUIRED_FROZEN == {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70,
        "use_wilder": False,
        "calculator": "ewm_causal_span",
    }


def test_frozen_parameter_drift_rejected() -> None:
    bad_contract = _contract()
    bad_contract["eligibility_filter"] = dict(bad_contract["eligibility_filter"])
    bad_contract["eligibility_filter"]["frozen_parameters"] = {
        **bad_contract["eligibility_filter"]["frozen_parameters"],
        "oversold": 25,
    }
    with pytest.raises(ValueError):
        assert_frozen_parameters_match_contract(bad_contract)


def test_holdout_paths_fail_closed() -> None:
    with pytest.raises(EntryEffectiveHoldoutError):
        assert_not_holdout_path(HOLDOUT_OPAQUE_ID)
    with pytest.raises(EntryEffectiveHoldoutError):
        assert_not_holdout_path(
            "docs/evidence/offline_economic_reevaluation_sealed_long_panel_v1/x.json"
        )


def test_exhaustion_bounds_eligible_at_30_and_70() -> None:
    idx = pd.date_range("2023-01-01", periods=5, freq="h", tz="UTC")
    rsi = pd.Series([10.0, 30.0, 50.0, 70.0, 90.0], index=idx)
    mask = eligibility_mask_from_rsi(rsi, warmup_bars=0)
    assert list(mask) == [True, True, False, True, True]


def test_exhaustion_rejects_nan_rsi() -> None:
    idx = pd.date_range("2023-01-01", periods=3, freq="h", tz="UTC")
    rsi = pd.Series([float("nan"), 20.0, float("nan")], index=idx)
    mask = eligibility_mask_from_rsi(rsi, warmup_bars=0)
    assert list(mask) == [False, True, False]


def test_warmup_bars_always_ineligible() -> None:
    idx = pd.date_range("2023-01-01", periods=3, freq="h", tz="UTC")
    rsi = pd.Series([10.0, 10.0, 10.0], index=idx)
    mask = eligibility_mask_from_rsi(rsi, warmup_bars=2)
    assert list(mask) == [False, False, True]


def test_eligibility_labels_are_eligible_or_stand_aside() -> None:
    idx = pd.date_range("2023-01-01", periods=40, freq="h", tz="UTC")
    # Build a close series that swings enough to produce finite RSI after warmup.
    vals = [100.0]
    for i in range(1, 40):
        step = -1.5 if (i % 8) < 4 else 1.5
        vals.append(vals[-1] + step)
    close = pd.Series(vals, index=idx)
    bars = pd.DataFrame({"open": close, "high": close, "low": close, "close": close}, index=idx)
    labels = eligibility_labels_from_bars(bars)
    assert set(labels.unique()) <= {ELIGIBLE, STAND_ASIDE}
    assert labels.iloc[:14].eq(STAND_ASIDE).all()


def test_gate_zeros_ineligible_signals() -> None:
    idx = pd.date_range("2023-01-01", periods=5, freq="h", tz="UTC")
    signals = pd.Series([1, -1, 1, -1, 1], index=idx)
    mask = pd.Series([True, False, True, False, True], index=idx)
    gated = apply_eligibility_gate_to_signals(signals, mask)
    assert list(gated) == [1, 0, 1, 0, 1]


def test_apply_eligibility_to_mapped_position_signal_blocks_new_entries() -> None:
    assert apply_eligibility_to_mapped_position_signal(1, False) == 0
    assert apply_eligibility_to_mapped_position_signal(-1, False) == 0


def test_apply_eligibility_to_mapped_position_signal_passes_through_when_eligible() -> None:
    assert apply_eligibility_to_mapped_position_signal(1, True) == 1
    assert apply_eligibility_to_mapped_position_signal(-1, True) == -1


def test_apply_eligibility_to_mapped_position_signal_flat_always_passes() -> None:
    assert apply_eligibility_to_mapped_position_signal(0, False) == 0
    assert apply_eligibility_to_mapped_position_signal(0, True) == 0


class _FakeDecisionEvidence:
    def __init__(self, decision_outcome: str) -> None:
        self.decision_outcome = decision_outcome


def test_treatment_gate_disabled_is_a_noop() -> None:
    idx = pd.date_range("2023-01-01", periods=3, freq="h", tz="UTC")
    bars = pd.DataFrame({"close": [1.0, 1.0, 1.0]}, index=idx)
    with _optional_treatment_entry_eligibility_gate(enabled=False, bars=bars) as counters:
        pass
    assert counters["entries_blocked_by_gate"] == 0


def test_treatment_gate_requires_bars_when_enabled() -> None:
    with pytest.raises(ValueError):
        with _optional_treatment_entry_eligibility_gate(enabled=True, bars=None):
            pass


def test_treatment_gate_monkeypatch_zeros_mapped_entry_on_ineligible_bar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.backtest.mv2_research_wiring_v1 as wiring_mod
    import src.research.rsi_exhaustion_mr_eligibility_development_evaluation_v1.panel_runner_v1 as panel_runner_mod

    idx = pd.date_range("2023-01-01", periods=3, freq="h", tz="UTC")
    bars = pd.DataFrame({"close": [1.0, 1.0, 1.0]}, index=idx)

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(evidence) -> int:  # noqa: ARG001
        return 1

    def _fake_mask(_bars: pd.DataFrame) -> pd.Series:
        return pd.Series([True, False, True], index=idx)

    monkeypatch.setattr(wiring_mod, "bind_bar_for_mv2_wiring_v1", _fake_bind_bar)
    monkeypatch.setattr(wiring_mod, "map_decision_evidence_to_position_signal_v1", _fake_map)
    monkeypatch.setattr(panel_runner_mod, "eligibility_mask_from_bars", _fake_mask)

    with _optional_treatment_entry_eligibility_gate(enabled=True, bars=bars) as counters:
        wiring_mod.bind_bar_for_mv2_wiring_v1(
            bar=bars.iloc[0], instrument_id="x", trading_epoch=0, profile_binding=None
        )
        signal_eligible_bar = wiring_mod.map_decision_evidence_to_position_signal_v1(
            _FakeDecisionEvidence("enter_long")
        )

        wiring_mod.bind_bar_for_mv2_wiring_v1(
            bar=bars.iloc[1], instrument_id="x", trading_epoch=1, profile_binding=None
        )
        signal_ineligible_bar = wiring_mod.map_decision_evidence_to_position_signal_v1(
            _FakeDecisionEvidence("enter_long")
        )

    assert signal_eligible_bar == 1
    assert signal_ineligible_bar == 0
    assert counters["entries_blocked_by_gate"] == 1
    assert wiring_mod.map_decision_evidence_to_position_signal_v1 is _fake_map


def test_dataset_id_constant() -> None:
    assert REQUIRED_DATASET_ID == (
        "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )


def _baseline_metrics(**overrides) -> dict:
    base = {
        "trade_count": 100,
        "net_return": 0.01,
        "max_drawdown": -0.05,
        "profit_factor": 0.9,
    }
    base.update(overrides)
    return base


def _treatment_metrics(**overrides) -> dict:
    base = {
        "trade_count": 80,
        "net_return": 0.02,
        "max_drawdown": -0.04,
        "profit_factor": 1.1,
    }
    base.update(overrides)
    return base


def test_decision_inconclusive_low_control_trade_count() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(trade_count=10),
        treatment=_treatment_metrics(trade_count=8),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_INCONCLUSIVE
    assert out["reason"] == REASON_INSUFFICIENT_CONTROL_TRADE_COUNT


def test_decision_fail_on_no_divergence_even_with_good_economics() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=False,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_FAIL
    assert out["reason"] == REASON_NO_DIVERGENCE


def test_decision_pass_when_all_requires_met() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
        max_trade_count_reduction_fraction=0.5,
    )
    assert out["result_class"] == RESULT_PASS
    assert all(out["checks"].values())


def test_decision_fail_when_profit_factor_not_improved() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(profit_factor=1.2),
        treatment=_treatment_metrics(profit_factor=1.0),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    assert out["result_class"] == RESULT_FAIL
    assert out["reason"] == REASON_PROFIT_FACTOR_NOT_IMPROVED
    assert out["checks"]["profit_factor_treatment_gt_control"] is False


def test_decision_technical_failure_is_inconclusive() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
        technical_failure=True,
    )
    assert out["result_class"] == RESULT_INCONCLUSIVE


def test_decision_never_sets_promotion_or_runtime_flags() -> None:
    out = decide_development_evaluation(
        baseline=_baseline_metrics(),
        treatment=_treatment_metrics(),
        entry_eligibility_divergence_observed=True,
        minimum_trade_count=50,
    )
    forbidden_keys = {
        "promotion_eligible",
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "orders_sent",
        "live_authorized",
    }
    assert forbidden_keys.isdisjoint(out.keys())
