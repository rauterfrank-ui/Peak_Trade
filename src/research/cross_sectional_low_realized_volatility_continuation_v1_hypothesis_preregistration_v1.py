"""Definition-only preregistration validator for CSLRVC v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION=true"
)
CONTRACT_REL_PATH = (
    "config/research/"
    "cross_sectional_low_realized_volatility_continuation_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1_"
    "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_cross_sectional_low_realized_volatility_continuation_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_V1"
REQUIRED_PREDECESSOR = "CROSS_SECTIONAL_HIGH_REALIZED_VOLATILITY_FADE_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION"
REQUIRED_DIRECTIONAL_FORM = (
    "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION"
)
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
REQUIRED_DATASET = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_PRODUCTIVE_PNL_REF = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
)
REQUIRED_PORTFOLIO = "RESEARCH_EQUAL_WEIGHT_NORMALIZED_SLEEVE_COMBINE_V1"
REQUIRED_PRECEDENCE = [
    "INITIAL_STOP",
    "CROSS_SECTIONAL_VOL_RANK_NORMALIZATION_INVALIDATION",
    "REGIME_INVALIDATION",
    "TIME_EXIT",
    "END_OF_INSTRUMENT_LIQUIDATION",
    "END_OF_PANEL_LIQUIDATION",
]
REQUIRED_ENTRY_POINT_SCRIPT = "scripts/research/run_evaluate_cross_sectional_low_realized_volatility_continuation_development_v1.py"
REQUIRED_TREATMENT = "OWN_INSTRUMENT_CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_ADMISSION"


class PreregistrationValidationError(ValueError):
    """Fail-closed measurement-contract validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise PreregistrationValidationError(code)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_contract_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k not in {"contract_digest", "provenance"}}
    return hashlib.sha256(_canonical_dumps(body).encode("utf-8")).hexdigest()


def validate_measurement_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(
        payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY,
        "STRATEGY_IDENTITY",
    )
    _require(payload.get("predecessor_strategy_id") == REQUIRED_PREDECESSOR, "PREDECESSOR")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("dataset_id") == REQUIRED_DATASET, "DATASET_ID")
    _require(payload.get("dataset_bound") is True, "DATASET_NOT_BOUND")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is False,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(
        payload.get("development_evaluation_executed") is False,
        "DEVELOPMENT_EVALUATION_EXECUTED",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED",
        "HOLDOUT_NOT_UNBOUND",
    )
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
    run_limit = payload.get("run_limit") or {}
    _require(run_limit.get("development_run_limit") == 1, "RUN_LIMIT_NOT_ONE")
    _require(run_limit.get("retry_forbidden") is True, "RETRY_NOT_FORBIDDEN")
    _require(payload.get("required_treatment_type") == REQUIRED_TREATMENT, "TREATMENT")

    directional = payload.get("directional_form") or {}
    _require(directional.get("selected") == REQUIRED_DIRECTIONAL_FORM, "DIRECTIONAL_FORM")
    _require(
        directional.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )

    baseline = payload.get("baseline") or {}
    _require(baseline.get("baseline_id") == REQUIRED_BASELINE_ID, "BASELINE_ID")
    _require(baseline.get("frozen") is True, "BASELINE_NOT_FROZEN")
    _require(
        baseline.get("sole_difference_vs_treatment")
        == "CROSS_SECTIONAL_LOW_REALIZED_VOLATILITY_CONTINUATION_ADMISSION",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("family") == "REALIZED_VOLATILITY_CROSS_SECTIONAL_RANK", "VOL_FAMILY")
    _require(vol.get("realized_volatility_period_completed_bars") == 24, "RV_PERIOD")
    _require(vol.get("method") == "CLOSE_TO_CLOSE_LOG_RETURN_STDEV", "RV_METHOD")
    _require(
        vol.get("cross_sectional_ranking_authorized_for_this_hypothesis") is True,
        "CS_RANK_NOT_AUTHORIZED",
    )
    _require(
        vol.get("cross_sectional_return_momentum_ranking_forbidden") is True,
        "CS_RETURN_MOMENTUM_ALLOWED",
    )

    state = admission.get("cross_sectional_vol_rank_state") or {}
    _require(state.get("low_rank_percentile_inclusive_max") == 0.20, "CS_LOW_THR")
    _require(state.get("min_consecutive_low_rank_bars") == 2, "CS_LOW_BARS")
    _require(state.get("high_rank_entry_forbidden_in_v1") is True, "HIGH_RANK_ENTRY_ALLOWED")
    _require(state.get("pit_cross_section_only") is True, "PIT_CS_ONLY")

    entry = admission.get("cross_sectional_low_vol_continuation_entry") or {}
    _require(
        entry.get("entry_only_after_cross_sectional_low_rv_rank_state") is True,
        "ENTRY_ORDER",
    )
    _require(entry.get("ex_ante_exit_reachability_required") is True, "REACHABILITY_NOT_REQUIRED")
    _require(entry.get("min_post_fill_bars_required_inclusive") == 48, "MIN_POST_FILL")
    _require(
        entry.get("direction_rule") == "with_signed_return_over_short_horizon_window",
        "DIRECTION_RULE",
    )
    _require(entry.get("high_cross_sectional_vol_entry_forbidden") is True, "HIGH_CS_VOL_ALLOWED")
    _require(entry.get("cshrvf_high_vol_fade_entry_forbidden") is True, "CSHRVF_ENTRY_ALLOWED")
    _require(entry.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _require(entry.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")

    lifecycle = admission.get("transition_event_lifecycle") or {}
    _require(lifecycle.get("event_consumption") == "SINGLE_USE", "EVENT_NOT_SINGLE_USE")
    _require(lifecycle.get("cshrvf_retry_forbidden") is True, "CSHRVF_RETRY_ALLOWED")
    _require(lifecycle.get("cs_momentum_lane_reopen_forbidden") is True, "CS_MOMENTUM_REOPEN")
    _require(
        lifecycle.get("further_term_structure_variant_forbidden") is True,
        "FURTHER_TS_ALLOWED",
    )

    entry_point = payload.get("canonical_development_evaluation_entry_point") or {}
    _require(entry_point.get("definition_only") is True, "ENTRY_POINT_NOT_DEFINITION_ONLY")
    _require(
        entry_point.get("evaluation_authorized_in_this_slice") is False,
        "ENTRY_POINT_EVAL_AUTHORIZED",
    )
    _require(entry_point.get("script_ref") == REQUIRED_ENTRY_POINT_SCRIPT, "ENTRY_POINT_SCRIPT")

    exits = payload.get("exit_semantics") or {}
    _require(exits.get("frozen") is True, "EXIT_NOT_FROZEN")
    _require(exits.get("initial_stop_atr_multiple") == 1.5, "INITIAL_STOP")
    _require(exits.get("trailing_stop_forbidden") is True, "TRAILING_ALLOWED")
    _require(exits.get("time_exit_max_bars") == 48, "TIME_EXIT")
    _require(exits.get("every_admitted_entry_must_have_reachable_exit") is True, "EXIT_REACHABLE")
    _require(
        exits.get("precedence_ascending_wins_first") == REQUIRED_PRECEDENCE,
        "PRECEDENCE",
    )
    reclaim = exits.get("cross_sectional_vol_rank_normalization_invalidation") or {}
    _require(reclaim.get("authorized") is True, "CS_NORM_NOT_AUTHORIZED")
    _require(
        reclaim.get("rule") == "cs_rv_rank_percentile_rises_strictly_above_0_45",
        "CS_NORM_RULE",
    )
    _require(
        exits.get("productive_exit_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )

    portfolio = payload.get("portfolio") or {}
    _require(
        portfolio.get("portfolio_aggregation_id") == REQUIRED_PORTFOLIO,
        "PORTFOLIO_ID",
    )

    md = (
        payload.get("material_difference_vs_cross_sectional_high_realized_volatility_fade_v1") or {}
    )
    _require(md.get("prior_strategy_identity") == REQUIRED_PREDECESSOR, "MD_CSHRVF_PRIOR")
    _require(md.get("not_a_parameter_change_of_cshrvf_v1") is True, "MD_CSHRVF_PARAM")
    _require(md.get("not_a_repair_or_retry_of_cshrvf_v1") is True, "MD_CSHRVF_RETRY")
    _require(md.get("cshrvf_retry_forbidden") is True, "MD_CSHRVF_RETRY_FLAG")
    diffs = md.get("differences") or {}
    for key in (
        "admission_polarity",
        "causal_claim",
        "direction_rule",
        "exit_normalization",
        "forbidden_half",
        "target_phenomenon",
        "estimator_axis",
    ):
        _require(bool(diffs.get(key)), f"MD_CSHRVF_MISSING:{key}")

    rationale = payload.get("successor_selection_rationale") or {}
    _require(rationale.get("selected_successor") == REQUIRED_STRATEGY_IDENTITY, "RATIONALE_ID")
    rejected = rationale.get("alternatives_rejected") or {}
    for key in (
        "FURTHER_TERM_STRUCTURE_VARIANT",
        "VOLATILITY_EXPANSION_COMPRESSION_RETRY",
        "OWN_INSTRUMENT_REALIZED_VOLATILITY_REGIME_TRANSITION",
        "CROSS_SECTIONAL_VOLATILITY_DISPERSION_ONLY",
        "STANDASIDE_ADMISSION_FILTER",
        "CLOSE_LANE_NO_FURTHER_RESEARCH",
        "CSHRVF_PARAMETER_RETUNE_OR_HIGH_HALF_RETRY",
    ):
        _require(bool(rejected.get(key)), f"ALT_REJECT_MISSING:{key}")

    bias = payload.get("bias_and_leakage_controls") or {}
    _require(bias.get("lookahead_forbidden") is True, "LOOKAHEAD_ALLOWED")
    leak = bias.get("leakage_controls") or {}
    _require(leak.get("no_holdout_access") is True, "LEAK_HOLDOUT")

    costs = payload.get("costs") or {}
    _require(costs.get("fee_bps_per_side") == 10.0, "FEE_BPS")
    _require(costs.get("cost_model_weakening_forbidden") is True, "COST_WEAKENING")

    runtime = payload.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        _require(runtime.get(key) is False, f"RUNTIME_{key.upper()}")

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "CONTRACT_DIGEST_MISMATCH")

    return {
        "valid": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "status": REQUIRED_STATUS,
        "contract_digest": digest,
        "development_run_count": 0,
        "run_slot_consumed": False,
        "strategy_implementation_present": False,
        "evaluation_authorized": False,
        "holdout_forbidden": True,
        "materially_distinct_from_cshrvf": True,
    }


def load_and_validate_repo_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    _require(path.is_file(), "CONTRACT_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_measurement_contract(payload)
    gov = repo_root / GOVERNANCE_REL_PATH
    _require(gov.is_file(), "GOVERNANCE_MISSING")
    evidence = repo_root / EVIDENCE_REL_PATH
    _require(evidence.is_dir(), "EVIDENCE_MISSING")
    script = repo_root / REQUIRED_ENTRY_POINT_SCRIPT
    _require(script.is_file(), "ENTRY_SCRIPT_MISSING")
    return report
