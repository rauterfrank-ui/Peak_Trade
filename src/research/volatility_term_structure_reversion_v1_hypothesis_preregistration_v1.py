"""Definition-only preregistration validator for VTSR v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_term_structure_reversion_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_TERM_STRUCTURE_REVERSION_V1_"
    "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = "docs/evidence/preregister_volatility_term_structure_reversion_hypothesis_v1/"
REQUIRED_HYPOTHESIS_ID = "VOLATILITY_TERM_STRUCTURE_REVERSION_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_TERM_STRUCTURE_REVERSION_V1"
REQUIRED_PREDECESSOR = "VOLATILITY_EXPANSION_FAILED_CONTINUATION_FADE_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "SHORT_VS_LONG_REALIZED_VOLATILITY_TERM_STRUCTURE_REVERSION"
REQUIRED_DIRECTIONAL_FORM = "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_VOLATILITY_TERM_STRUCTURE_REVERSION"
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
    "scripts/research/run_evaluate_volatility_term_structure_reversion_development_v1.py"
)
CONFIGURED_OPERATOR_THRESHOLD_KEYS = frozenset(
    {
        "min_evaluable_treatment_breakout_events",
        "min_executed_treatment_trades",
        "min_evaluable_treatment_events_per_time_segment",
        "time_segment_robustness_pass_ratio",
        "max_single_instrument_positive_gross_pnl_share_max",
    }
)


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
        payload.get("development_evaluation_executed") is True,
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
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_CONSUMED")
    run_limit = payload.get("run_limit") or {}
    _require(run_limit.get("development_run_limit") == 1, "RUN_LIMIT_NOT_ONE")
    _require(run_limit.get("retry_forbidden") is True, "RETRY_NOT_FORBIDDEN")

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
        == "VOLATILITY_TERM_STRUCTURE_REVERSION_ADMISSION",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("family") == "REALIZED_VOLATILITY_TERM_STRUCTURE", "VOL_FAMILY")
    _require(vol.get("short_horizon_completed_bars") == 8, "RV_SHORT")
    _require(vol.get("long_horizon_completed_bars") == 48, "RV_LONG")
    _require(vol.get("method") == "CLOSE_TO_CLOSE_LOG_RETURN_STDEV", "RV_METHOD")

    ts = admission.get("term_structure_state") or {}
    _require(ts.get("elevated_ratio_percentile_inclusive_min") == 0.80, "TS_ELEVATED_THR")
    _require(ts.get("min_consecutive_elevated_bars") == 2, "TS_ELEVATED_BARS")
    _require(ts.get("depressed_entry_forbidden_in_v1") is True, "DEPRESSED_ENTRY_ALLOWED")

    fade = admission.get("reversion_fade_entry") or {}
    _require(
        fade.get("entry_only_after_elevated_term_structure_state") is True,
        "FADE_ORDER",
    )
    _require(fade.get("ex_ante_exit_reachability_required") is True, "REACHABILITY_NOT_REQUIRED")
    _require(fade.get("min_post_fill_bars_required_inclusive") == 48, "MIN_POST_FILL")
    _require(fade.get("no_channel_breakout_required") is True, "CHANNEL_BREAKOUT_REQUIRED")
    _require(fade.get("no_expansion_state_required") is True, "EXPANSION_REQUIRED")
    _require(
        fade.get("vefcf_failed_continuation_fade_entry_forbidden") is True, "VEFCF_ENTRY_ALLOWED"
    )
    _require(fade.get("vepc_pullback_continuation_entry_forbidden") is True, "VEPC_ENTRY_ALLOWED")
    _require(fade.get("vcb_compression_breakout_entry_forbidden") is True, "VCB_ENTRY_ALLOWED")
    _require(
        fade.get("direction_rule") == "opposite_to_signed_return_over_short_horizon_window",
        "DIRECTION_RULE",
    )
    _require(fade.get("long_short_mutually_exclusive") is True, "LONG_SHORT_NOT_MX")
    _require(fade.get("bitcoin_excluded") is True, "BTC_NOT_EXCLUDED")
    _require(fade.get("spot_excluded") is True, "SPOT_NOT_EXCLUDED")

    lifecycle = admission.get("transition_event_lifecycle") or {}
    _require(lifecycle.get("event_consumption") == "SINGLE_USE", "EVENT_NOT_SINGLE_USE")
    _require(lifecycle.get("vefcf_retry_forbidden") is True, "VEFCF_RETRY_ALLOWED")
    _require(lifecycle.get("vepc_retry_forbidden") is True, "VEPC_RETRY_ALLOWED")
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
    _require(exits.get("second_pnl_truth_forbidden") is True, "SECOND_PNL_TRUTH")
    _require(
        exits.get("productive_exit_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )

    events = payload.get("event_sufficiency_gates") or {}
    _require(events.get("frozen") is True, "EVENT_GATES_NOT_FROZEN")
    _require(events.get("min_evaluable_treatment_breakout_events") == 50, "MIN_EVENTS")
    _require(events.get("min_executed_treatment_trades") == 30, "MIN_TRADES")

    economic = payload.get("economic_admission_contract") or {}
    _require(
        economic.get("evaluation_blocked_while_any_threshold_pending") is False,
        "PENDING_STILL_BLOCKING",
    )
    _require(set(economic.get("pending_threshold_keys") or []) == set(), "PENDING_THRESHOLD_KEYS")
    thresholds = economic.get("thresholds") or {}
    for key, expected in (
        ("gross_profit_factor_min", 1.0),
        ("net_profit_factor_min", 1.3),
        ("maximum_max_drawdown", 0.25),
        ("min_evaluable_treatment_breakout_events", 50),
        ("min_executed_treatment_trades", 30),
        ("min_evaluable_treatment_events_per_time_segment", 10),
        ("cost_stress_1_5x_net_profit_factor_min", 1.0),
        ("time_segment_robustness_pass_ratio", 0.5),
        ("max_single_instrument_positive_gross_pnl_share_max", 0.35),
    ):
        row = thresholds.get(key) or {}
        _require(row.get("status") == "CONFIGURED", f"THRESHOLD_NOT_CONFIGURED:{key}")
        _require(row.get("value") == expected, f"THRESHOLD_VALUE:{key}")
    for key in CONFIGURED_OPERATOR_THRESHOLD_KEYS:
        row = thresholds.get(key) or {}
        _require(row.get("authority") == "EXPLICIT_OPERATOR_AUTHORIZATION", f"THRESHOLD_AUTH:{key}")
        _require(row.get("not_result_calibrated") is True, f"THRESHOLD_CALIBRATED:{key}")

    costs = payload.get("costs") or {}
    _require(costs.get("fee_bps_per_side") == 10.0, "FEE_BPS")
    _require(costs.get("slippage_bps_per_side") == 5.0, "SLIPPAGE_BPS")

    portfolio = payload.get("portfolio") or {}
    _require(portfolio.get("portfolio_aggregation_id") == REQUIRED_PORTFOLIO, "PORTFOLIO")

    param_gov = payload.get("parameter_governance") or {}
    _require(param_gov.get("open_parameters_remaining") is False, "OPEN_PARAMETERS")
    _require(param_gov.get("definition_semantics_complete") is True, "SEMANTICS_INCOMPLETE")
    frozen = param_gov.get("frozen_parameters") or {}
    _require(frozen.get("realized_volatility_period") == 24, "FROZEN_RV_PERIOD")
    _require(frozen.get("expansion_percentile_inclusive_min") == 0.65, "FROZEN_EXP")
    _require(
        frozen.get("fade_requires_failed_continuation_trigger") is True,
        "FROZEN_FADE_TRIGGER",
    )
    _require(frozen.get("vepc_continuation_entry_forbidden") is True, "FROZEN_VEPC_FORBIDDEN")
    _require(frozen.get("trailing_stop_forbidden") is True, "FROZEN_TRAILING")

    md_vefcf = (
        payload.get("material_difference_vs_volatility_expansion_failed_continuation_fade_v1") or {}
    )
    _require(md_vefcf.get("prior_strategy_identity") == REQUIRED_PREDECESSOR, "PRIOR_VEFCF")
    _require(md_vefcf.get("vefcf_retry_forbidden") is True, "VEFCF_RETRY_ALLOWED")
    _require(md_vefcf.get("not_a_repair_or_retry_of_vefcf_v1") is True, "VEFCF_REPAIR")

    for key, code in (
        ("material_difference_vs_volatility_compression_breakout_v1", "VCB"),
        ("material_difference_vs_volatility_expansion_persistence_v1", "VEP"),
        ("material_difference_vs_volatility_decay_breakout_v1", "VDB"),
        (
            "material_difference_vs_volatility_decay_breakout_with_explicit_decay_exit_v1",
            "VDBX",
        ),
        ("material_difference_vs_volatility_contraction_expansion_breakout_v1", "VCEB"),
    ):
        md = payload.get(key) or {}
        retry_key = f"{code.lower()}_retry_forbidden"
        _require(md.get(retry_key) is True, f"{code}_RETRY_ALLOWED")

    on_fail = (payload.get("terminal_decision_semantics") or {}).get("on_fail") or {}
    _require(on_fail.get("retry_allowed") is False, "ON_FAIL_RETRY")

    shared = payload.get("shared_authority_constraints") or {}
    for key in (
        "master_v2_mutation_forbidden",
        "double_play_sole_directional_transition_authority",
        "risk_authority_mutation_forbidden",
        "execution_kernel_mutation_forbidden",
    ):
        _require(shared.get(key) is True, f"SHARED_AUTH_{key.upper()}")

    runtime = payload.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        _require(runtime.get(key) is False, f"RUNTIME_FLAG_{key.upper()}")

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "CONTRACT_DIGEST_MISMATCH")

    return {
        "valid": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "predecessor_strategy_id": REQUIRED_PREDECESSOR,
        "directional_form": REQUIRED_DIRECTIONAL_FORM,
        "baseline_id": REQUIRED_BASELINE_ID,
        "contract_digest": digest,
        "definition_only": True,
        "evaluation_authorized": False,
        "development_evaluation_authorized": True,
        "development_evaluation_executed": True,
        "holdout_authorized": False,
        "dataset_bound": True,
        "development_run_count": 1,
        "runner_start_count": 1,
        "run_slot_consumed": True,
        "open_parameters_remaining": False,
        "definition_semantics_complete": True,
        "entry_semantics_complete": True,
        "exit_semantics_complete": True,
        "entry_exit_pairable": True,
        "material_difference_from_vefcf_v1": True,
        "productive_pnl_evaluator_referenced": True,
        "second_pnl_truth_created": False,
        "canonical_entry_point": REQUIRED_ENTRY_POINT_SCRIPT,
        "time_segment_definition_id": REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "portfolio_aggregation_id": REQUIRED_PORTFOLIO,
    }


def reject_holdout_dataset_or_path(token: str) -> None:
    lowered = str(token).lower()
    if (
        "offline_economic_reevaluation_sealed_long_panel_v1" in lowered
        or "holdout" in lowered
        or "final_audit" in lowered
    ):
        raise PreregistrationValidationError("HOLDOUT_ACCESS_FORBIDDEN")


def load_and_validate_repo_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    _require(path.is_file(), "CONTRACT_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_measurement_contract(payload)
