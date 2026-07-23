"""Definition-only preregistration validator for VTDC v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION=true"
)
CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_term_structure_depressed_continuation_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1_"
    "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_volatility_term_structure_depressed_continuation_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = (
    "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_V1"
REQUIRED_PREDECESSOR = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "SHORT_VS_LONG_REALIZED_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION"
REQUIRED_DIRECTIONAL_FORM = (
    "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION"
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
    "TERM_STRUCTURE_NORMALIZATION_INVALIDATION",
    "REGIME_INVALIDATION",
    "TIME_EXIT",
    "END_OF_INSTRUMENT_LIQUIDATION",
    "END_OF_PANEL_LIQUIDATION",
]
REQUIRED_ENTRY_POINT_SCRIPT = (
    "scripts/research/run_evaluate_volatility_term_structure_depressed_continuation_"
    "development_v1.py"
)
REQUIRED_TREATMENT = "OWN_INSTRUMENT_VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_ADMISSION"


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
        payload.get("development_evaluation_authorized") is True,
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
        == "VOLATILITY_TERM_STRUCTURE_DEPRESSED_CONTINUATION_ADMISSION",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("family") == "REALIZED_VOLATILITY_TERM_STRUCTURE", "VOL_FAMILY")
    _require(vol.get("short_horizon_completed_bars") == 8, "RV_SHORT")
    _require(vol.get("long_horizon_completed_bars") == 48, "RV_LONG")
    _require(vol.get("method") == "CLOSE_TO_CLOSE_LOG_RETURN_STDEV", "RV_METHOD")

    ts = admission.get("term_structure_state") or {}
    _require(ts.get("depressed_ratio_percentile_inclusive_max") == 0.20, "TS_DEPRESSED_THR")
    _require(ts.get("min_consecutive_depressed_bars") == 2, "TS_DEPRESSED_BARS")
    _require(ts.get("elevated_entry_forbidden_in_v1") is True, "ELEVATED_ENTRY_ALLOWED")

    cont = admission.get("depressed_continuation_entry") or {}
    _require(
        cont.get("entry_only_after_depressed_term_structure_state") is True,
        "CONTINUATION_ORDER",
    )
    _require(cont.get("ex_ante_exit_reachability_required") is True, "REACHABILITY_NOT_REQUIRED")
    _require(cont.get("min_post_fill_bars_required_inclusive") == 48, "MIN_POST_FILL")
    _require(cont.get("no_channel_breakout_required") is True, "CHANNEL_BREAKOUT_REQUIRED")
    _require(cont.get("no_expansion_state_required") is True, "EXPANSION_REQUIRED")
    _require(
        cont.get("vefcf_failed_continuation_fade_entry_forbidden") is True,
        "VEFCF_ENTRY_ALLOWED",
    )
    _require(cont.get("vepc_pullback_continuation_entry_forbidden") is True, "VEPC_ENTRY_ALLOWED")
    _require(cont.get("vcb_compression_breakout_entry_forbidden") is True, "VCB_ENTRY_ALLOWED")
    _require(
        cont.get("vtsr_elevated_reversion_fade_entry_forbidden") is True,
        "VTSR_ENTRY_ALLOWED",
    )
    _require(
        cont.get("direction_rule") == "with_signed_return_over_short_horizon_window",
        "DIRECTION_RULE",
    )
    _require(cont.get("long_short_mutually_exclusive") is True, "LONG_SHORT_NOT_MX")
    _require(cont.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _require(cont.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")

    lifecycle = admission.get("transition_event_lifecycle") or {}
    _require(lifecycle.get("event_consumption") == "SINGLE_USE", "EVENT_NOT_SINGLE_USE")
    _require(lifecycle.get("vefcf_retry_forbidden") is True, "VEFCF_RETRY_ALLOWED")
    _require(lifecycle.get("vepc_retry_forbidden") is True, "VEPC_RETRY_ALLOWED")
    _require(lifecycle.get("vtsr_retry_forbidden") is True, "VTSR_RETRY_ALLOWED")
    _require(
        lifecycle.get("expansion_impulse_prerequisite_forbidden") is True,
        "EXPANSION_PREREQ_ALLOWED",
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
    _require(exits.get("trailing_stop_not_used") is True, "TRAILING_USED")
    _require(exits.get("time_exit_max_bars") == 48, "TIME_EXIT")
    _require(exits.get("every_admitted_entry_must_have_reachable_exit") is True, "EXIT_REACHABLE")
    _require(
        exits.get("precedence_ascending_wins_first") == REQUIRED_PRECEDENCE,
        "PRECEDENCE",
    )
    reclaim = exits.get("term_structure_normalization_invalidation") or {}
    _require(reclaim.get("authorized") is True, "TS_NORM_NOT_AUTHORIZED")
    _require(
        reclaim.get("rule") == "rv_term_structure_ratio_percentile_rises_strictly_above_0_45",
        "TS_NORM_RULE",
    )
    _require(exits.get("second_pnl_truth_forbidden") is True, "SECOND_PNL_TRUTH")
    _require(
        exits.get("productive_exit_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )

    portfolio = payload.get("portfolio") or {}
    _require(
        portfolio.get("portfolio_aggregation_id") == REQUIRED_PORTFOLIO,
        "PORTFOLIO_ID",
    )

    md = payload.get("material_difference_vs_volatility_term_structure_reversion_v1") or {}
    _require(md.get("prior_strategy_identity") == REQUIRED_PREDECESSOR, "MD_VTSR_PRIOR")
    _require(md.get("not_a_parameter_change_of_vtsr_v1") is True, "MD_VTSR_PARAM")
    _require(md.get("not_a_repair_or_retry_of_vtsr_v1") is True, "MD_VTSR_RETRY")
    _require(md.get("vtsr_retry_forbidden") is True, "MD_VTSR_RETRY_FLAG")
    diffs = md.get("differences") or {}
    for key in (
        "admission_polarity",
        "causal_claim",
        "direction_rule",
        "exit_normalization",
        "forbidden_half",
        "target_phenomenon",
    ):
        _require(bool(diffs.get(key)), f"MD_VTSR_MISSING:{key}")

    costs = payload.get("costs") or {}
    _require(costs.get("fee_bps_per_side") == 10.0, "FEE_BPS")
    _require(costs.get("slippage_bps_per_side") == 5.0, "SLIPPAGE_BPS")
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

    time_seg = payload.get("time_segment_definition") or {}
    _require(
        time_seg.get("definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID
        or time_seg.get("id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID
        or "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1" in json.dumps(time_seg, sort_keys=True),
        "TIME_SEGMENT",
    )

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
        "materially_distinct_from_vtsr": True,
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
