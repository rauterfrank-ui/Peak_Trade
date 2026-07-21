"""Contract/unit tests for midband exit-efficiency DEVELOPMENT evaluation closeout.

No real panel evaluation. Synthetic fixtures only.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.decision_v1 import (
    RESULT_FAIL,
    RESULT_INCONCLUSIVE,
    RESULT_PASS,
    decide_development_evaluation,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    assert_frozen_parameters_match_contract,
    force_exit_signal_for_open_side,
    long_exit_mask_from_bars,
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    load_json,
    reject_holdout_dataset_or_path,
)
from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.constants_v1 import (
    REQUIRED_FROZEN_EXIT_PARAMETERS,
)
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v1"
TEST_FILE = Path(__file__).resolve()


def _synthetic_bars() -> pd.DataFrame:
    idx = pd.date_range("2023-05-20", periods=40, freq="h", tz="UTC")
    close = [100.0] * 20 + list(range(90, 110))
    close = close[:40]
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 1 for c in close],
            "low": [c - 1 for c in close],
            "close": close,
        },
        index=idx,
    )


def test_unit_tests_do_not_call_panel_runner() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    banned = {"run_development_evaluation", "run_arm", "load_member_bars"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in banned:
                raise AssertionError(f"banned_call:{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in banned:
                raise AssertionError(f"banned_call:{node.func.attr}")


def test_terminal_contract_validates() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["evaluation_run_count"] == 1
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    contract = load_json(REPO / CONTRACT_REL_PATH)
    assert contract["pass"] is False
    assert contract["fail"] is False
    assert contract["holdout_data_accessed"] is False
    assert_frozen_parameters_match_contract(contract)
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert float(contract["cost_model"]["cost_multiplier"]) == 1.0


def test_terminal_backlog_validates() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 0
    assert report["terminal_count"] == 4
    assert report["development_run_count"] == 4
    assert report["v2_evaluation_run_count"] == 1
    assert report["v3_evaluation_run_count"] == 1
    assert report["v3_result_class"] == "FAIL"
    assert report["rerun_allowed"] is False


def test_terminal_summary_evidence() -> None:
    summary = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_started"] is True
    assert summary["evaluation_completed"] is False
    assert summary["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert summary["economic_verdict"] == "NOT_EVALUATED"
    assert summary["pass"] is False
    assert summary["fail"] is False
    assert summary["baseline_members_completed"] == "2/46"
    assert summary["treatment_members_completed"] == "0/46"
    assert summary["holdout_data_accessed"] is False
    assert summary["rerun_allowed"] is False
    assert summary["baseline_metrics"] is None
    assert summary["treatment_metrics"] is None
    death = json.loads((EVIDENCE / "process_death_root_cause.json").read_text(encoding="utf-8"))
    assert death["process_death_root_cause"] == "UNKNOWN"


def test_long_short_masks_and_force_exit() -> None:
    bars = _synthetic_bars()
    assert long_exit_mask_from_bars(bars).dtype == bool
    assert short_exit_mask_from_bars(bars).dtype == bool
    assert force_exit_signal_for_open_side("long") == -1
    assert force_exit_signal_for_open_side("short") == 1


def test_decision_helpers_synthetic_only() -> None:
    baseline = {
        "trade_count": 40,
        "net_profit_factor": 0.8,
        "net_pnl": -100.0,
        "net_return": -0.01,
        "mean_realized_pnl_over_mfe_capture_ratio": -1.0,
        "mean_mfe_to_exit_leakage": 50.0,
        "turnover": 40.0,
        "worst1_abs_net_share": 0.2,
    }
    treatment = {
        **baseline,
        "trade_count": 38,
        "net_profit_factor": 0.9,
        "net_pnl": -50.0,
        "net_return": -0.005,
        "mean_realized_pnl_over_mfe_capture_ratio": -0.5,
        "mean_mfe_to_exit_leakage": 40.0,
        "turnover": 38.0,
    }
    assert (
        decide_development_evaluation(
            baseline=baseline, treatment=treatment, exit_divergence_observed=True
        )["result_class"]
        == RESULT_PASS
    )
    assert (
        decide_development_evaluation(
            baseline=baseline, treatment=treatment, exit_divergence_observed=False
        )["result_class"]
        == RESULT_FAIL
    )
    assert (
        decide_development_evaluation(
            baseline={**baseline, "trade_count": 5},
            treatment=treatment,
            exit_divergence_observed=True,
        )["result_class"]
        == RESULT_INCONCLUSIVE
    )


def test_holdout_rejected() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")
