"""Contract tests for canonical open MR entry-eligibility hypothesis backlog v1.

Definition-only governance. No backtest. No economic metrics. No holdout access.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.canonical_open_mr_entry_eligibility_hypothesis_backlog_v1 import (
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
    assert report["terminal_hypothesis_count"] == 4
    assert report["open_candidate_count"] == 2
    assert report["preregistered_count"] == 1
    assert report["development_run_count"] == 0
    assert report["evaluation_authorized"] is False
    assert report["holdout_forbidden"] is True
    assert report["runtime_locked"] is True
    assert report["next_eligible_hypothesis_id"] == (
        "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
    )


def test_ma_preregistered_and_not_open() -> None:
    backlog = _load(BACKLOG_PATH)
    open_ids = {c["hypothesis_id"] for c in backlog["open_candidates"]}
    assert "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" not in open_ids
    prereg = backlog["preregistered_hypotheses"]
    assert len(prereg) == 1
    assert (
        prereg[0]["hypothesis_id"]
        == "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
    )
    assert prereg[0]["status"] == "DEFINITION_ONLY_PREREGISTERED"
    assert prereg[0]["evaluation_authorized"] is False
    assert prereg[0]["development_run_count"] == 0
    assert (
        "price_vs_ma_trend_alignment" in backlog["forbidden_feature_families_for_open_candidates"]
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


def test_open_candidate_count_and_unique_ids() -> None:
    backlog = _load(BACKLOG_PATH)
    candidates = backlog["open_candidates"]
    assert len(candidates) == 2
    ids = [c["hypothesis_id"] for c in candidates]
    assert len(ids) == len(set(ids))
    assert not set(ids) & set(REQUIRED_TERMINAL_HYPOTHESIS_IDS)


def test_priority_order_complete_deterministic_no_ties() -> None:
    backlog = _load(BACKLOG_PATH)
    candidates = backlog["open_candidates"]
    ranks = sorted(c["priority_rank"] for c in candidates)
    assert ranks == list(range(1, len(candidates) + 1))
    totals = [c["priority_score_total"] for c in candidates]
    assert len(set(totals)) == len(totals)
    ordered = sorted(candidates, key=lambda c: c["priority_rank"])
    by_score = sorted(
        candidates,
        key=lambda c: (-c["priority_score_total"], c["hypothesis_id"]),
    )
    assert [c["hypothesis_id"] for c in ordered] == [c["hypothesis_id"] for c in by_score]


def test_exactly_one_next_eligible_for_preregistration() -> None:
    backlog = _load(BACKLOG_PATH)
    next_ones = [c for c in backlog["open_candidates"] if c["queue_status"] == NEXT_ELIGIBLE]
    queued = [c for c in backlog["open_candidates"] if c["queue_status"] == QUEUED]
    assert len(next_ones) == 1
    assert next_ones[0]["priority_rank"] == 1
    assert next_ones[0]["status"] == "OPEN_UNPREREGISTERED"
    assert all(c["queue_status"] == QUEUED for c in queued)
    assert all(c["status"] == "OPEN_UNPREREGISTERED" for c in backlog["open_candidates"])


def test_no_semantic_duplicate_feature_families() -> None:
    backlog = _load(BACKLOG_PATH)
    for candidate in backlog["open_candidates"]:
        assert candidate["feature_family"] not in FORBIDDEN_FEATURE_FAMILIES
        for terminal_id in REQUIRED_TERMINAL_HYPOTHESIS_IDS:
            assert terminal_id in candidate["semantic_distance_to_terminal"]
            assert candidate["semantic_distance_to_terminal"][terminal_id]
            assert terminal_id in candidate["not_a_parameter_retune_of"]


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


def test_validator_rejects_second_next_eligible() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["open_candidates"][1]["queue_status"] = NEXT_ELIGIBLE
    with pytest.raises(BacklogValidationError, match="EXACTLY_ONE_NEXT_ELIGIBLE"):
        validate_backlog_contract(bad)


def test_validator_rejects_forbidden_feature_family_retune() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["open_candidates"][0]["feature_family"] = "adx_level_range_admission"
    with pytest.raises(BacklogValidationError, match="SEMANTIC_DUPLICATE_FEATURE_FAMILY"):
        validate_backlog_contract(bad)


def test_validator_rejects_nonzero_development_run_count() -> None:
    backlog = _load(BACKLOG_PATH)
    bad = copy.deepcopy(backlog)
    bad["development_run_count"] = 1
    with pytest.raises(BacklogValidationError, match="DEVELOPMENT_RUN_COUNT_NONZERO"):
        validate_backlog_contract(bad)


def test_governance_doc_marks_definition_only_and_next_eligible() -> None:
    text = GOVERNANCE_PATH.read_text(encoding="utf-8")
    assert "OPEN_BACKLOG" in text
    assert "PROMOTION_ELIGIBLE=false" in text
    assert "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" in text
    assert "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1" in text
    assert "NEXT_ELIGIBLE_FOR_PREREGISTRATION" in text
    assert "DEFINITION_ONLY_PREREGISTERED" in text
    assert "EVALUATION_EXECUTED=false" in text
    assert "NOT authorized" in text or "not authorized" in text.lower()
