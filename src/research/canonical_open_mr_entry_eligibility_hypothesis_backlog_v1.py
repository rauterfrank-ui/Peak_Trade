"""Canonical open MR entry-eligibility hypothesis backlog SSOT validator v1.

Definition-only governance. No preregistration, backtest, economic metrics,
holdout access, runtime activation, or productive trading-logic mutation.

Lane status vocabulary and post-terminal legality are owned solely by
CANONICAL_RESEARCH_LANE_POST_TERMINAL_LIFECYCLE_CONTRACT_V1.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.canonical_research_lane_post_terminal_lifecycle_contract_v1 import (
    CONTRACT_ID as LIFECYCLE_CONTRACT_ID,
    CONTRACT_REL_PATH as LIFECYCLE_CONTRACT_REL_PATH,
    ResearchLaneLifecycleContractError,
    resolve_post_terminal_transition,
    validate_lane_snapshot,
)

PACKAGE_MARKER = "CANONICAL_OPEN_MR_ENTRY_ELIGIBILITY_HYPOTHESIS_BACKLOG_V1=true"
BACKLOG_REL_PATH = "config/research/canonical_open_mr_entry_eligibility_hypothesis_backlog_v1.json"
GOVERNANCE_REL_PATH = "docs/governance/CANONICAL_OPEN_MR_ENTRY_ELIGIBILITY_HYPOTHESIS_BACKLOG_V1.md"
REQUIRED_STATUS = "POST_TERMINAL_OPERATOR_DECISION_REQUIRED"
REQUIRED_LIFECYCLE_AUTHORITY = "SHARED_POST_TERMINAL_LIFECYCLE_CONTRACT_V1_SOLE_AUTHORITY"
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "ENTRY_EFFECTIVE_PRE_ENTRY_ELIGIBILITY_FILTER"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_TERMINAL_FAIL_HYPOTHESIS_IDS = (
    "REGIME_GATED_STANDASIDE_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1",
    "ENTRY_EFFECTIVE_MR_ELIGIBILITY_MEAN_REVERSION_NON_BITCOIN_PERPETUALS_V1",
    "RSI_EXHAUSTION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
    "ADX_RANGE_ADMISSION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
    "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
    "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
)
REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS = (
    "ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1",
)
REQUIRED_TERMINAL_HYPOTHESIS_IDS = (
    REQUIRED_TERMINAL_FAIL_HYPOTHESIS_IDS + REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS
)
FORBIDDEN_FEATURE_FAMILIES = frozenset(
    {
        "multi_feature_absolute_threshold_regime_classifier",
        "atr_rolling_percentile_midband",
        "rsi_exhaustion_level",
        "adx_level_range_admission",
        "price_vs_ma_trend_alignment",
        "macd_histogram_sign_countertrend",
        "adx_di_direction_confirmation",
    }
)
REQUIRED_PREREGISTERED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
MA_TREND_ALIGNMENT_HYPOTHESIS_ID = (
    "MA_TREND_ALIGNMENT_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
)
MACD_HISTOGRAM_COUNTERTREND_HYPOTHESIS_ID = (
    "MACD_HISTOGRAM_COUNTERTREND_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
)
ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID = (
    "ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_V1"
)
ADX_DI_DIRECTION_CONFIRMATION_HOLDOUT_V2_HYPOTHESIS_ID = (
    "ADX_DI_DIRECTION_CONFIRMATION_MR_ENTRY_ELIGIBILITY_NON_BITCOIN_PERPETUALS_HOLDOUT_V2"
)
REQUIRED_HOLDOUT_V2_PREREGISTERED_STATUS = "DEFINITION_ONLY_HOLDOUT_PREREGISTERED"
FORBIDDEN_EMBEDDED_RESULT_KEYS = frozenset(
    {
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "RESULT_CLASS",
        "result_class",
        "comparison_decision",
        "probe_summary",
    }
)
NEXT_ELIGIBLE = "NEXT_ELIGIBLE_FOR_PREREGISTRATION"
QUEUED = "QUEUED"
OPEN_UNPREREGISTERED = "OPEN_UNPREREGISTERED"
PRIORITY_DIMENSIONS = (
    "semantic_distance",
    "entry_effectiveness",
    "measurability",
    "low_additional_complexity",
    "low_overfitting_risk",
    "repo_support",
)
PRIORITY_WEIGHTS = {
    "semantic_distance": 3,
    "entry_effectiveness": 3,
    "measurability": 2,
    "low_additional_complexity": 2,
    "low_overfitting_risk": 2,
    "repo_support": 2,
}


class BacklogValidationError(ValueError):
    """Fail-closed backlog SSOT validation error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_true(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise BacklogValidationError(f"{code}{suffix}")


def _contains_banned_result_keys(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if key in FORBIDDEN_EMBEDDED_RESULT_KEYS:
                # Allow documenting terminal fail_reason/result references only
                # under terminal_hypotheses.*.fail_reason / fail_finding.
                if key in {"RESULT_CLASS", "result_class"} and ".terminal_hypotheses[" not in path:
                    found.append(key_path)
                elif key not in {"RESULT_CLASS", "result_class"}:
                    found.append(key_path)
            found.extend(_contains_banned_result_keys(value, key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_contains_banned_result_keys(item, f"{path}[{idx}]"))
    return found


def compute_priority_score_total(scores: Mapping[str, Any]) -> int:
    total = 0
    for dim, weight in PRIORITY_WEIGHTS.items():
        if dim not in scores:
            raise BacklogValidationError(f"PRIORITY_SCORE_MISSING: {dim}")
        value = scores[dim]
        if not isinstance(value, int) or value < 1 or value > 5:
            raise BacklogValidationError(f"PRIORITY_SCORE_RANGE: {dim}={value!r}")
        total += weight * value
    return total


def validate_backlog_contract(backlog: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the canonical open MR eligibility backlog SSOT fail-closed."""
    _assert_true(
        backlog.get("status") == REQUIRED_STATUS,
        "STATUS_NOT_POST_TERMINAL_OPERATOR_DECISION_REQUIRED",
    )
    _assert_true(
        backlog.get("lifecycle_contract_id") == LIFECYCLE_CONTRACT_ID,
        "LIFECYCLE_CONTRACT_ID_MISMATCH",
    )
    _assert_true(
        backlog.get("lifecycle_contract_ref") == LIFECYCLE_CONTRACT_REL_PATH,
        "LIFECYCLE_CONTRACT_REF_MISMATCH",
    )
    _assert_true(
        backlog.get("lifecycle_authority") == REQUIRED_LIFECYCLE_AUTHORITY,
        "LIFECYCLE_AUTHORITY_MISMATCH",
    )
    _assert_true(backlog.get("explicit_closeout_decision") is False, "UNEXPECTED_CLOSEOUT_DECISION")
    _assert_true(backlog.get("explicit_waiting_decision") is False, "UNEXPECTED_WAITING_DECISION")
    _assert_true(backlog.get("lane_auto_closed") is False, "LANE_AUTO_CLOSED_FORBIDDEN")
    _assert_true(backlog.get("canonical_ssot") is True, "NOT_CANONICAL_SSOT")
    _assert_true(
        backlog.get("exactly_one_authoritative_truth") is True,
        "NOT_EXACTLY_ONE_AUTHORITATIVE_TRUTH",
    )
    _assert_true(
        backlog.get("productive_trading_logic_included") is False,
        "PRODUCTIVE_TRADING_LOGIC_INCLUDED",
    )
    _assert_true(backlog.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _assert_true(backlog.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _assert_true(
        backlog.get("preregistration_authorized_in_this_slice") is False,
        "PREREGISTRATION_AUTHORIZED_IN_SLICE",
    )
    _assert_true(
        backlog.get("evaluation_results_embedded") is False,
        "EVALUATION_RESULTS_EMBEDDED_FLAG",
    )
    _assert_true(backlog.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT_NONZERO")
    _assert_true(backlog.get("dataset_id") == REQUIRED_DATASET_ID, "DATASET_ID_MISMATCH")
    _assert_true(backlog.get("dataset_class") == "DEVELOPMENT_ONLY", "DATASET_CLASS")
    _assert_true(backlog.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _assert_true(
        backlog.get("sealed_holdout_id") == HOLDOUT_OPAQUE_ID,
        "HOLDOUT_ID_MISMATCH",
    )
    _assert_true(
        backlog.get("sealed_holdout_content_inspection_authorized") is False,
        "HOLDOUT_INSPECTION_AUTHORIZED",
    )
    _assert_true(
        backlog.get("required_treatment_type") == REQUIRED_TREATMENT_TYPE,
        "TREATMENT_TYPE_MISMATCH",
    )

    universe = backlog.get("universe_scope")
    _assert_true(isinstance(universe, Mapping), "UNIVERSE_SCOPE_MISSING")
    assert isinstance(universe, Mapping)
    _assert_true(universe.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _assert_true(universe.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")
    _assert_true(universe.get("venue") == "OKX", "VENUE_NOT_OKX")
    _assert_true(
        universe.get("instrument_class") == "LINEAR_USDT_PERPETUAL",
        "INSTRUMENT_CLASS",
    )
    _assert_true(universe.get("frequency") == "PT1H", "FREQUENCY")

    runtime = backlog.get("runtime_policy")
    _assert_true(isinstance(runtime, Mapping), "RUNTIME_POLICY_MISSING")
    assert isinstance(runtime, Mapping)
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        _assert_true(runtime.get(key) is False, f"RUNTIME_UNLOCKED:{key}")

    promo = backlog.get("promotion_and_economic_gate_policy")
    _assert_true(isinstance(promo, Mapping), "PROMOTION_POLICY_MISSING")
    assert isinstance(promo, Mapping)
    _assert_true(promo.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _assert_true(
        promo.get("economic_validity_offline_gate_pass") is False,
        "ECONOMIC_GATE_OPEN",
    )
    _assert_true(
        promo.get("economic_validity_offline_gate_changed") is False,
        "ECONOMIC_GATE_CHANGED",
    )

    banned = _contains_banned_result_keys(backlog)
    _assert_true(not banned, "EMBEDDED_RESULT_METRICS", ", ".join(banned[:8]))

    terminals = backlog.get("terminal_hypotheses")
    _assert_true(isinstance(terminals, list), "TERMINAL_HYPOTHESES_MISSING")
    assert isinstance(terminals, list)
    _assert_true(
        len(terminals) == len(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
        "TERMINAL_HYPOTHESIS_COUNT",
        str(len(terminals)),
    )
    terminal_ids = [t.get("hypothesis_id") for t in terminals]
    _assert_true(
        tuple(terminal_ids) == REQUIRED_TERMINAL_HYPOTHESIS_IDS,
        "TERMINAL_HYPOTHESIS_IDS",
        str(terminal_ids),
    )
    for terminal in terminals:
        _assert_true(isinstance(terminal, Mapping), "TERMINAL_ENTRY_TYPE")
        assert isinstance(terminal, Mapping)
        status = terminal.get("status")
        _assert_true(
            status in {"TERMINAL_FAIL", "TERMINAL_PASS"},
            "TERMINAL_STATUS",
            str(status),
        )
        if status == "TERMINAL_FAIL":
            _assert_true(isinstance(terminal.get("fail_reason"), str), "TERMINAL_FAIL_REASON")
            _assert_true(isinstance(terminal.get("fail_finding"), str), "TERMINAL_FAIL_FINDING")
        else:
            _assert_true(isinstance(terminal.get("pass_reason"), str), "TERMINAL_PASS_REASON")
            _assert_true(isinstance(terminal.get("pass_finding"), str), "TERMINAL_PASS_FINDING")
        _assert_true(isinstance(terminal.get("feature_family"), str), "TERMINAL_FEATURE_FAMILY")
        _assert_true(
            isinstance(terminal.get("feature_ids"), list) and terminal["feature_ids"],
            "TERMINAL_FEATURE_IDS",
        )
    fail_ids = [t["hypothesis_id"] for t in terminals if t.get("status") == "TERMINAL_FAIL"]
    pass_ids = [t["hypothesis_id"] for t in terminals if t.get("status") == "TERMINAL_PASS"]
    _assert_true(
        tuple(fail_ids) == REQUIRED_TERMINAL_FAIL_HYPOTHESIS_IDS,
        "TERMINAL_FAIL_IDS",
        str(fail_ids),
    )
    _assert_true(
        tuple(pass_ids) == REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS,
        "TERMINAL_PASS_IDS",
        str(pass_ids),
    )

    forbidden_families = backlog.get("forbidden_feature_families_for_open_candidates")
    _assert_true(isinstance(forbidden_families, list), "FORBIDDEN_FAMILIES_MISSING")
    assert isinstance(forbidden_families, list)
    _assert_true(
        FORBIDDEN_FEATURE_FAMILIES.issubset(set(forbidden_families)),
        "FORBIDDEN_FAMILIES_INCOMPLETE",
    )

    candidates = backlog.get("open_candidates")
    _assert_true(isinstance(candidates, list), "OPEN_CANDIDATES_MISSING")
    assert isinstance(candidates, list)
    rules = backlog.get("governance_rules")
    _assert_true(isinstance(rules, Mapping), "GOVERNANCE_RULES_MISSING")
    assert isinstance(rules, Mapping)
    min_c = int(rules.get("open_candidate_count_min", 2))
    max_c = int(rules.get("open_candidate_count_max", 4))
    _assert_true(min_c <= len(candidates) <= max_c, "OPEN_CANDIDATE_COUNT", str(len(candidates)))

    _assert_true(rules.get("max_concurrent_open_preregistrations") == 1, "MAX_CONCURRENT_PREREG")
    _assert_true(rules.get("development_runs_per_hypothesis") == 1, "DEV_RUNS_PER_HYP")
    _assert_true(rules.get("retuning_after_fail_forbidden") is True, "RETUNE_ALLOWED")
    _assert_true(rules.get("holdout_use_forbidden") is True, "HOLDOUT_USE_ALLOWED")
    _assert_true(rules.get("candidate_combination_forbidden") is True, "COMBINATION_ALLOWED")
    _assert_true(
        rules.get("reprioritization_requires_separate_versioned_governance_pr") is True,
        "REPRIORITIZATION_UNLOCKED",
    )
    _assert_true(
        rules.get("evaluation_requires_separate_preregistration_pr_and_operator_go") is True,
        "EVAL_WITHOUT_GO",
    )
    _assert_true(rules.get("economic_gate_closed") is True, "ECONOMIC_GATE_NOT_CLOSED")
    _assert_true(rules.get("promotion_closed") is True, "PROMOTION_NOT_CLOSED")

    candidate_ids: list[str] = []
    ranks: list[int] = []
    totals: list[int] = []
    next_eligible: list[str] = []
    for candidate in candidates:
        _assert_true(isinstance(candidate, Mapping), "CANDIDATE_TYPE")
        assert isinstance(candidate, Mapping)
        hyp_id = candidate.get("hypothesis_id")
        _assert_true(isinstance(hyp_id, str) and hyp_id, "CANDIDATE_ID_MISSING")
        assert isinstance(hyp_id, str)
        _assert_true(hyp_id not in candidate_ids, "DUPLICATE_CANDIDATE_ID", hyp_id)
        _assert_true(
            hyp_id not in REQUIRED_TERMINAL_HYPOTHESIS_IDS, "CANDIDATE_IS_TERMINAL", hyp_id
        )
        candidate_ids.append(hyp_id)

        _assert_true(candidate.get("status") == OPEN_UNPREREGISTERED, "CANDIDATE_STATUS", hyp_id)
        queue_status = candidate.get("queue_status")
        _assert_true(queue_status in {NEXT_ELIGIBLE, QUEUED}, "QUEUE_STATUS", hyp_id)
        if queue_status == NEXT_ELIGIBLE:
            next_eligible.append(hyp_id)

        family = candidate.get("feature_family")
        _assert_true(isinstance(family, str) and family, "FEATURE_FAMILY", hyp_id)
        assert isinstance(family, str)
        _assert_true(
            family not in FORBIDDEN_FEATURE_FAMILIES,
            "SEMANTIC_DUPLICATE_FEATURE_FAMILY",
            f"{hyp_id}:{family}",
        )

        scores = candidate.get("priority_scores")
        _assert_true(isinstance(scores, Mapping), "PRIORITY_SCORES_MISSING", hyp_id)
        assert isinstance(scores, Mapping)
        for dim in PRIORITY_DIMENSIONS:
            _assert_true(dim in scores, "PRIORITY_DIMENSION_MISSING", f"{hyp_id}:{dim}")
        computed = compute_priority_score_total(scores)
        declared = candidate.get("priority_score_total")
        _assert_true(
            declared == computed, "PRIORITY_TOTAL_MISMATCH", f"{hyp_id}:{declared}!={computed}"
        )
        totals.append(computed)

        rank = candidate.get("priority_rank")
        _assert_true(isinstance(rank, int) and rank >= 1, "PRIORITY_RANK", hyp_id)
        assert isinstance(rank, int)
        ranks.append(rank)

        distance = candidate.get("semantic_distance_to_terminal")
        _assert_true(isinstance(distance, Mapping), "SEMANTIC_DISTANCE_MISSING", hyp_id)
        assert isinstance(distance, Mapping)
        for terminal_id in REQUIRED_TERMINAL_HYPOTHESIS_IDS:
            _assert_true(
                terminal_id in distance and isinstance(distance[terminal_id], str),
                "SEMANTIC_DISTANCE_INCOMPLETE",
                f"{hyp_id}:{terminal_id}",
            )

        for required in (
            "causal_thesis",
            "independent_treatment_change",
            "expected_effect",
            "known_failure_modes",
            "repo_source_refs",
            "frozen_parameter_intent",
            "not_a_parameter_retune_of",
        ):
            _assert_true(required in candidate, "CANDIDATE_FIELD_MISSING", f"{hyp_id}:{required}")
        _assert_true(
            set(candidate.get("not_a_parameter_retune_of", []))
            >= set(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
            "RETUNE_DENIAL_INCOMPLETE",
            hyp_id,
        )

    if len(candidates) == 0:
        _assert_true(min_c == 0, "OPEN_EMPTY_REQUIRES_MIN_ZERO")
        _assert_true(
            rules.get("exactly_one_next_eligible_for_preregistration") is False,
            "EMPTY_OPEN_MUST_DISABLE_EXACTLY_ONE_NEXT_RULE",
        )
        _assert_true(len(next_eligible) == 0, "EMPTY_OPEN_MUST_HAVE_NO_NEXT_ELIGIBLE")
        ordered: list[Any] = []
    else:
        _assert_true(
            rules.get("exactly_one_next_eligible_for_preregistration") is True,
            "EXACTLY_ONE_NEXT_RULE_MISSING",
        )
        _assert_true(len(next_eligible) == 1, "EXACTLY_ONE_NEXT_ELIGIBLE", str(next_eligible))
        _assert_true(
            sorted(ranks) == list(range(1, len(candidates) + 1)),
            "PRIORITY_RANKS_NOT_PERMUTATION",
        )
        _assert_true(len(set(totals)) == len(totals), "PRIORITY_TOTAL_TIE")

        ordered = sorted(candidates, key=lambda c: int(c["priority_rank"]))
        _assert_true(
            ordered[0].get("queue_status") == NEXT_ELIGIBLE,
            "NEXT_ELIGIBLE_NOT_RANK_ONE",
        )
        for candidate in ordered[1:]:
            _assert_true(candidate.get("queue_status") == QUEUED, "NON_NEXT_NOT_QUEUED")

        # Deterministic descending score order must match ascending rank.
        score_order = sorted(
            candidates,
            key=lambda c: (-int(c["priority_score_total"]), str(c["hypothesis_id"])),
        )
        _assert_true(
            [c["hypothesis_id"] for c in score_order] == [c["hypothesis_id"] for c in ordered],
            "PRIORITY_ORDER_NOT_DETERMINISTIC",
        )

    criteria = backlog.get("priority_criteria")
    _assert_true(isinstance(criteria, Mapping), "PRIORITY_CRITERIA_MISSING")
    assert isinstance(criteria, Mapping)
    _assert_true(
        criteria.get("selection_performance_forbidden") is True,
        "PERFORMANCE_SELECTION_ALLOWED",
    )
    _assert_true(criteria.get("criteria_locked_a_priori") is True, "CRITERIA_NOT_LOCKED")

    _assert_true(
        MA_TREND_ALIGNMENT_HYPOTHESIS_ID not in candidate_ids,
        "MA_TREND_ALIGNMENT_MUST_NOT_BE_OPEN_CANDIDATE",
    )
    _assert_true(
        MACD_HISTOGRAM_COUNTERTREND_HYPOTHESIS_ID not in candidate_ids,
        "MACD_HISTOGRAM_COUNTERTREND_MUST_NOT_BE_OPEN_CANDIDATE",
    )
    _assert_true(
        ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID not in candidate_ids,
        "ADX_DI_DIRECTION_CONFIRMATION_MUST_NOT_BE_OPEN_CANDIDATE",
    )

    preregistered = backlog.get("preregistered_hypotheses") or []
    _assert_true(isinstance(preregistered, list), "PREREGISTERED_HYPOTHESES_TYPE")
    preregistered_ids: list[str] = []
    for entry in preregistered:
        _assert_true(isinstance(entry, Mapping), "PREREGISTERED_ENTRY_TYPE")
        assert isinstance(entry, Mapping)
        hyp_id = entry.get("hypothesis_id")
        _assert_true(isinstance(hyp_id, str) and hyp_id, "PREREGISTERED_ID_MISSING")
        assert isinstance(hyp_id, str)
        _assert_true(hyp_id not in preregistered_ids, "DUPLICATE_PREREGISTERED_ID", hyp_id)
        _assert_true(
            hyp_id not in REQUIRED_TERMINAL_HYPOTHESIS_IDS,
            "PREREGISTERED_IS_TERMINAL",
            hyp_id,
        )
        _assert_true(hyp_id not in candidate_ids, "PREREGISTERED_STILL_OPEN", hyp_id)
        _assert_true(
            entry.get("status") == REQUIRED_PREREGISTERED_STATUS,
            "PREREGISTERED_STATUS",
            hyp_id,
        )
        _assert_true(
            entry.get("evaluation_authorized") is False,
            "PREREGISTERED_EVALUATION_AUTHORIZED",
            hyp_id,
        )
        _assert_true(
            entry.get("development_run_count") == 0,
            "PREREGISTERED_DEVELOPMENT_RUN_COUNT",
            hyp_id,
        )
        preregistered_ids.append(hyp_id)
    _assert_true(
        preregistered_ids == [],
        "PREREGISTERED_MUST_BE_EMPTY_AFTER_HOLDOUT_V2_TERMINAL",
        str(preregistered_ids),
    )
    adx_entry = None
    for entry in terminals:
        if entry.get("hypothesis_id") == ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID:
            adx_entry = entry
            break
    _assert_true(adx_entry is not None, "ADX_DI_TERMINAL_ENTRY_MISSING")
    assert isinstance(adx_entry, Mapping)
    _assert_true(
        adx_entry.get("successor_holdout_evaluation_hypothesis_id")
        == ADX_DI_DIRECTION_CONFIRMATION_HOLDOUT_V2_HYPOTHESIS_ID,
        "HOLDOUT_V2_SUCCESSOR_ID",
    )
    _assert_true(
        adx_entry.get("successor_holdout_preregistration_status")
        == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL",
        "HOLDOUT_V2_SUCCESSOR_STATUS",
    )
    _assert_true(
        int(adx_entry.get("successor_holdout_run_count") or 0) == 1,
        "HOLDOUT_V2_SUCCESSOR_RUN_COUNT",
    )
    _assert_true(
        int(adx_entry.get("successor_holdout_run_limit") or 0) == 1,
        "HOLDOUT_V2_SUCCESSOR_RUN_LIMIT",
    )
    _assert_true(
        adx_entry.get("successor_holdout_executed") is True, "HOLDOUT_V2_SUCCESSOR_EXECUTED"
    )
    _assert_true(
        adx_entry.get("successor_holdout_result_class") == "FAIL",
        "HOLDOUT_V2_SUCCESSOR_RESULT",
    )
    _assert_true(
        adx_entry.get("successor_new_evaluation_not_rerun") is True,
        "HOLDOUT_V2_SUCCESSOR_NEW_EVAL",
    )
    _assert_true(
        int(adx_entry.get("holdout_run_count") or 0) == 1, "V1_HOLDOUT_RUN_COUNT_PRESERVED"
    )
    _assert_true(
        adx_entry.get("holdout_result_class") == "ARTIFACT_OR_EXECUTION_FAILURE_NO_RERUN",
        "V1_HOLDOUT_RESULT_PRESERVED",
    )
    _assert_true(
        ADX_DI_DIRECTION_CONFIRMATION_HYPOTHESIS_ID in REQUIRED_TERMINAL_PASS_HYPOTHESIS_IDS,
        "ADX_DI_MUST_BE_TERMINAL_PASS",
    )
    _assert_true(
        MACD_HISTOGRAM_COUNTERTREND_HYPOTHESIS_ID in REQUIRED_TERMINAL_HYPOTHESIS_IDS,
        "MACD_MUST_BE_TERMINAL",
    )

    # Shared post-terminal lifecycle is the sole status authority.
    lifecycle_snapshot = {
        "status": backlog.get("status"),
        "open_unpreregistered_candidates": list(candidates),
        "preregistered_hypotheses": list(preregistered),
        "explicit_closeout_decision": bool(backlog.get("explicit_closeout_decision")),
        "explicit_waiting_decision": bool(backlog.get("explicit_waiting_decision")),
        "go_executable": False,
        "auto_created_successor": False,
        "implicit_successor": False,
        "lane_auto_closed": bool(backlog.get("lane_auto_closed")),
    }
    try:
        lifecycle_report = validate_lane_snapshot(lifecycle_snapshot)
    except ResearchLaneLifecycleContractError as exc:
        raise BacklogValidationError(f"LIFECYCLE_CONTRACT_REJECTED:{exc}") from exc
    _assert_true(lifecycle_report.get("valid") is True, "LIFECYCLE_SNAPSHOT_INVALID")
    _assert_true(
        lifecycle_report.get("status") == REQUIRED_STATUS,
        "LIFECYCLE_STATUS_DRIFT",
    )
    _assert_true(
        lifecycle_report.get("inventory_non_empty") is False,
        "LIFECYCLE_INVENTORY_MUST_BE_EMPTY",
    )
    resolved = resolve_post_terminal_transition(
        result_class="FAIL",
        inventory_non_empty_flag=False,
    )
    _assert_true(
        resolved.get("next_state") == REQUIRED_STATUS,
        "POST_TERMINAL_RESOLUTION_DRIFT",
        str(resolved.get("next_state")),
    )
    _assert_true(
        resolved.get("operator_decision_required") is True,
        "POST_TERMINAL_OPERATOR_DECISION_NOT_REQUIRED",
    )

    return {
        "valid": True,
        "status": REQUIRED_STATUS,
        "lifecycle_contract_id": LIFECYCLE_CONTRACT_ID,
        "lifecycle_authority": REQUIRED_LIFECYCLE_AUTHORITY,
        "terminal_hypothesis_count": len(REQUIRED_TERMINAL_HYPOTHESIS_IDS),
        "open_candidate_count": len(candidates),
        "preregistered_count": len(preregistered_ids),
        "next_eligible_hypothesis_id": next_eligible[0] if next_eligible else None,
        "priority_order": [c["hypothesis_id"] for c in ordered],
        "development_run_count": 0,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "runtime_locked": True,
    }


def load_and_validate_repo_backlog(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / BACKLOG_REL_PATH
    _assert_true(path.is_file(), "BACKLOG_SSOT_MISSING", str(path))
    governance = root / GOVERNANCE_REL_PATH
    _assert_true(governance.is_file(), "GOVERNANCE_DOC_MISSING", str(governance))
    backlog = _load_json(path)
    report = validate_backlog_contract(backlog)
    report["backlog_path"] = BACKLOG_REL_PATH
    report["governance_path"] = GOVERNANCE_REL_PATH
    return report


def assert_exactly_one_backlog_ssot(repo_root: Path | None = None) -> None:
    """Fail-closed: exactly one canonical open MR eligibility backlog SSOT file."""
    root = repo_root or _repo_root()
    matches = sorted((root / "config" / "research").glob("*open*mr*eligibility*backlog*.json"))
    # Also catch alternate naming for the same surface.
    matches += sorted(
        (root / "config" / "research").glob("*mr_entry_eligibility_hypothesis_backlog*.json")
    )
    unique = sorted({p.resolve() for p in matches})
    _assert_true(len(unique) == 1, "BACKLOG_SSOT_COUNT", str([str(p) for p in unique]))
    _assert_true(
        unique[0] == (root / BACKLOG_REL_PATH).resolve(),
        "BACKLOG_SSOT_PATH_UNEXPECTED",
        str(unique[0]),
    )
