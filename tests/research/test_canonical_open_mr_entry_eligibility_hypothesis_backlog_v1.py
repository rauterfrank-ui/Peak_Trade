"""Contract tests for canonical open MR entry-eligibility hypothesis backlog v1.

Definition-only governance. No backtest. No economic metrics. No holdout access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.canonical_open_mr_entry_eligibility_hypothesis_backlog_v1 import (
    ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID,
    BACKLOG_REL_PATH,
    FORBIDDEN_FEATURE_FAMILIES,
    GOVERNANCE_REL_PATH,
    HOLDOUT_OPAQUE_ID,
    NEXT_ELIGIBLE,
    QUEUED,
    REQUIRED_TERMINAL_HYPOTHESIS_IDS,
    BacklogValidationError,
    assert_exactly_one_backlog_ssot,
    load_and_validate_repo_backlog,
    validate_backlog_contract,
)

REPO = Path(__file__).resolve().parents[2]
BACKLOG_PATH = REPO / BACKLOG_REL_PATH
GOVERNANCE_PATH = REPO / GOVERNANCE_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_exactly_one_backlog_ssot_exists() -> None:
    assert_exactly_one_backlog_ssot(REPO)
    assert BACKLOG_PATH.is_file()
    assert GOVERNANCE_PATH.is_file()


def test_repo_backlog_validates() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["status"] == "OPEN_BACKLOG"
    assert report["terminal_hypothesis_count"] == 6
    assert report["open_candidate_count"] == 0
    assert report["preregistered_count"] == 1
    assert report["development_run_count"] == 0
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["runtime_locked"] is True
    assert report["next_eligible_hypothesis_id"] is None


def test_macd_terminal_and_adx_di_preregistered() -> None:
    backlog = _load(BACKLOG_PATH)
    open_ids = {c["hypothesis_id"] for c in backlog["open_candidates"]}
    assert "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" not in open_ids
    assert "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" not in open_ids
    assert ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID not in open_ids
    assert backlog["open_candidates"] == []
    assert len(backlog["preregistered_hypotheses"]) == 1
    prereg = backlog["preregistered_hypotheses"][0]
    assert prereg["hypothesis_id"] == ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID
    assert prereg["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert prereg["queue_status"] == "PREREGISTERED_AWAITING_EVALUATION_GO"
    assert prereg["evaluation_authorized"] is False
    assert prereg["development_run_count"] == 0
    assert prereg["feature_family"] == "adx_di_direction_confirmation"
    assert (
        "macd_histogram_sign_countertrend"
        in backlog["forbidden_feature_families_for_open_candidates"]
    )
    assert (
        "price_vs_ma_trend_alignment" in backlog["forbidden_feature_families_for_open_candidates"]
    )
    assert (
        "adx_di_direction_confirmation" in backlog["forbidden_feature_families_for_open_candidates"]
    )
    terminals = {t["hypothesis_id"]: t for t in backlog["terminal_hypotheses"]}
    ma = terminals["MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"]
    assert ma["status"] == "TERMINAL_FAIL"
    assert ma["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    macd = terminals["MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"]
    assert macd["status"] == "TERMINAL_FAIL"
    assert macd["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert macd["fail_finding"] == (
        "net_profit_factor_not_improved_despite_entry_eligibility_divergence"
    )
    assert macd["feature_family"] == "macd_histogram_sign_countertrend"
    assert macd["evidence_ref"].endswith(
        "evaluate_macd_histogram_countertrend_mr_eligibility_development_v1/"
    )
    assert backlog["verdict"] == (
        "CANONICAL_OPEN_MR_ENTRY_ELIGIBILITY_BACKLOG_WITH_ONE_PREREGISTERED_EMPTY_OPEN_QUEUE"
    )
    assert backlog["next_canonical_step"] == (
        "REVIEW_AND_MERGE_ADX_DI_DIRECTION_CONFIRMATION_PREREGISTRATION_BEFORE_ANY_EVALUATION"
    )


def test_all_terminal_hypotheses_captured_unchanged() -> None:
    backlog = _load(BACKLOG_PATH)
    terminals = backlog["terminal_hypotheses"]
    assert [t["hypothesis_id"] for t in terminals] == list(REQUIRED_TERMINAL_HYPOTHESIS_IDS)
    assert all(t["status"] == "TERMINAL_FAIL" for t in terminals)
    assert terminals[0]["fail_finding"] == "identical_arms_gate_inactive_on_entries"
    assert terminals[1]["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert terminals[2]["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert terminals[3]["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert terminals[4]["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert terminals[5]["fail_reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
    assert (
        terminals[5]["hypothesis_id"]
        == "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
    )


def test_open_candidate_count_and_unique_ids() -> None:
    backlog = _load(BACKLOG_PATH)
    candidates = backlog["open_candidates"]
    assert len(candidates) == 0
    ids = [c["hypothesis_id"] for c in candidates]
    assert len(ids) == len(set(ids))
    assert not set(ids) & set(REQUIRED_TERMINAL_HYPOTHESIS_IDS)
    assert "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" not in ids
    assert ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID not in ids


def test_priority_order_complete_deterministic_no_ties() -> None:
    backlog = _load(BACKLOG_PATH)
    candidates = backlog["open_candidates"]
    assert candidates == []
    ranks = sorted(c["priority_rank"] for c in candidates)
    assert ranks == list(range(1, len(candidates) + 1))
    totals = [c["priority_score_total"] for c in candidates]
    assert len(set(totals)) == len(totals)


def test_no_next_eligible_while_adx_di_preregistered() -> None:
    backlog = _load(BACKLOG_PATH)
    next_ones = [c for c in backlog["open_candidates"] if c["queue_status"] == NEXT_ELIGIBLE]
    queued = [c for c in backlog["open_candidates"] if c["queue_status"] == QUEUED]
    assert next_ones == []
    assert queued == []
    assert backlog["governance_rules"]["exactly_one_next_eligible_for_preregistration"] is False
    assert backlog["preregistered_hypotheses"][0]["hypothesis_id"] == (
        ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID
    )


def test_no_semantic_duplicate_feature_families() -> None:
    backlog = _load(BACKLOG_PATH)
    for candidate in backlog["open_candidates"]:
        assert candidate["feature_family"] not in FORBIDDEN_FEATURE_FAMILIES
        for terminal_id in REQUIRED_TERMINAL_HYPOTHESIS_IDS:
            assert terminal_id in candidate["semantic_distance_to_terminal"]
            assert candidate["semantic_distance_to_terminal"][terminal_id]
            assert terminal_id in candidate["not_a_parameter_retune_of"]
    assert "adx_di_direction_confirmation" in FORBIDDEN_FEATURE_FAMILIES


def test_no_embedded_evaluation_results_or_runs() -> None:
    backlog = _load(BACKLOG_PATH)
    blob = json.dumps(backlog)
    for banned in (
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "comparison_decision",
        "probe_summary",
    ):
        assert banned not in backlog
        assert f'"{banned}"' not in blob
    assert backlog["development_run_count"] == 0
    assert backlog["evaluation_results_embedded"] is False
    assert backlog["evaluation_authorized"] is False
    assert backlog["backtest_authorized"] is False
    assert backlog["preregistered_hypotheses"][0]["development_run_count"] == 0


def test_holdout_and_runtime_remain_locked() -> None:
    backlog = _load(BACKLOG_PATH)
    assert backlog["holdout_forbidden"] is True
    assert backlog["sealed_holdout_id"] == HOLDOUT_OPAQUE_ID
    assert backlog["sealed_holdout_content_inspection_authorized"] is False
    runtime = backlog["runtime_policy"]
    assert runtime["runtime_activated"] is False
    assert runtime["shadow_activated"] is False
    assert runtime["paper_activated"] is False
    assert runtime["testnet_activated"] is False
    assert runtime["live_authorized"] is False
    assert runtime["orders_allowed"] is False
    assert runtime["scheduler_authorized"] is False
    promo = backlog["promotion_and_economic_gate_policy"]
    assert promo["promotion_eligible"] is False
    assert promo["economic_validity_offline_gate_pass"] is False


def test_universe_and_governance_bindings() -> None:
    backlog = _load(BACKLOG_PATH)
    universe = backlog["universe_scope"]
    assert universe["bitcoin_excluded"] is True
    assert universe["spot_excluded"] is True
    assert universe["venue"] == "OKX"
    assert universe["instrument_class"] == "LINEAR_USDT_PERPETUAL"
    assert universe["frequency"] == "PT1H"
    assert (
        backlog["dataset_id"]
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
    )
    rules = backlog["governance_rules"]
    assert rules["max_concurrent_open_preregistrations"] == 1
    assert rules["development_runs_per_hypothesis"] == 1
    assert rules["retuning_after_fail_forbidden"] is True
    assert rules["candidate_combination_forbidden"] is True
    assert rules["reprioritization_requires_separate_versioned_governance_pr"] is True
    assert rules["open_candidate_count_min"] == 0
    assert rules["exactly_one_next_eligible_for_preregistration"] is False


def test_validator_rejects_second_next_eligible() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["governance_rules"]["open_candidate_count_min"] = 1
    bad["governance_rules"]["exactly_one_next_eligible_for_preregistration"] = True
    clone_a = {
        "hypothesis_id": "SYNTHETIC_FIRST_NEXT_ELIGIBLE_OPEN_CANDIDATE_V1",
        "status": "OPEN_UNPREREGISTERED",
        "queue_status": NEXT_ELIGIBLE,
        "feature_family": "synthetic_first_next_eligible_family",
        "priority_rank": 1,
        "priority_scores": {
            "semantic_distance": 5,
            "entry_effectiveness": 5,
            "measurability": 5,
            "low_additional_complexity": 5,
            "low_overfitting_risk": 5,
            "repo_support": 5,
        },
        "priority_score_total": 70,
        "causal_thesis": "synthetic",
        "independent_treatment_change": "synthetic",
        "expected_effect": "synthetic",
        "known_failure_modes": ["synthetic"],
        "repo_source_refs": ["synthetic"],
        "frozen_parameter_intent": {"x": 1},
        "not_a_parameter_retune_of": list(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
        "semantic_distance_to_terminal": {
            tid: "synthetic" for tid in REQUIRED_TERMINAL_HYPOTHESIS_IDS
        },
    }
    clone_b = copy.deepcopy(clone_a)
    clone_b["hypothesis_id"] = "SYNTHETIC_SECOND_NEXT_ELIGIBLE_OPEN_CANDIDATE_V1"
    clone_b["feature_family"] = "synthetic_second_next_eligible_family"
    clone_b["priority_rank"] = 2
    clone_b["priority_scores"] = {
        "semantic_distance": 1,
        "entry_effectiveness": 1,
        "measurability": 1,
        "low_additional_complexity": 1,
        "low_overfitting_risk": 1,
        "repo_support": 1,
    }
    clone_b["priority_score_total"] = 14
    clone_b["queue_status"] = NEXT_ELIGIBLE
    bad["open_candidates"] = [clone_a, clone_b]
    with pytest.raises(BacklogValidationError, match="EXACTLY_ONE_NEXT_ELIGIBLE"):
        validate_backlog_contract(bad)


def test_validator_rejects_forbidden_feature_family_retune() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["governance_rules"]["open_candidate_count_min"] = 1
    bad["governance_rules"]["exactly_one_next_eligible_for_preregistration"] = True
    bad["open_candidates"] = [
        {
            "hypothesis_id": "SYNTHETIC_FORBIDDEN_FAMILY_OPEN_CANDIDATE_V1",
            "status": "OPEN_UNPREREGISTERED",
            "queue_status": NEXT_ELIGIBLE,
            "feature_family": "macd_histogram_sign_countertrend",
            "priority_rank": 1,
            "priority_scores": {
                "semantic_distance": 5,
                "entry_effectiveness": 5,
                "measurability": 5,
                "low_additional_complexity": 5,
                "low_overfitting_risk": 5,
                "repo_support": 5,
            },
            "priority_score_total": 70,
            "causal_thesis": "synthetic",
            "independent_treatment_change": "synthetic",
            "expected_effect": "synthetic",
            "known_failure_modes": ["synthetic"],
            "repo_source_refs": ["synthetic"],
            "frozen_parameter_intent": {"x": 1},
            "not_a_parameter_retune_of": list(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
            "semantic_distance_to_terminal": {
                tid: "synthetic" for tid in REQUIRED_TERMINAL_HYPOTHESIS_IDS
            },
        }
    ]
    with pytest.raises(BacklogValidationError, match="SEMANTIC_DUPLICATE_FEATURE_FAMILY"):
        validate_backlog_contract(bad)


def test_validator_rejects_nonzero_development_run_count() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["development_run_count"] = 1
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT_NONZERO"):
        validate_backlog_contract(bad)


def test_governance_doc_marks_definition_only_and_preregistered_adx_di() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "OPEN_BACKLOG" in text
    assert "PROMOTION_ELIGIBLE=false" in text
    assert "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" in text
    assert "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" in text
    assert ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID in text
    assert "DEFINITION_ONLY_PREREGISTERED" in text
    assert "open_candidates=[]" in text
    assert (
        "REVIEW_AND_MERGE_ADX_DI_DIRECTION_CONFIRMATION_PREREGISTRATION_BEFORE_ANY_EVALUATION"
        in text
    )
    assert "EVALUATION_EXECUTED=false" in text
    assert "NOT authorized" in text or "not authorized" in text.lower()
    assert "No second MACD evaluation run is permitted" in text
