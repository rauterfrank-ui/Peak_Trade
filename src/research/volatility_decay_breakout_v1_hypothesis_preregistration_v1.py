"""Definition-only preregistration validator for volatility decay breakout v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_DECAY_BREAKOUT_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_decay_breakout_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_DECAY_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = "docs/evidence/preregister_volatility_decay_breakout_hypothesis_v1/"
REQUIRED_HYPOTHESIS_ID = "VOLATILITY_DECAY_BREAKOUT_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_DECAY_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "VOLATILITY_DECAY_AFTER_HIGH_VOL_THEN_CHANNEL_BREAKOUT"
REQUIRED_DIRECTIONAL_FORM = "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT"
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
REQUIRED_DATASET = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_PRIOR = "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
REQUIRED_PRIOR_VCB = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
REQUIRED_PRIOR_VEP = "VOLATILITY_EXPANSION_PERSISTENCE_V1"
REQUIRED_PRODUCTIVE_PNL_REF = (
    "src/research/volatility_compression_breakout_v1_development_evaluation_v1/"
    "productive_exit_pnl_evaluator_v1.py"
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


_DIGEST_EXCLUDED_KEYS = frozenset(
    {
        "contract_digest",
        "provenance",
        # Post-freeze corrective governance (must not mutate frozen measurement digest).
        "corrective_measurement_reevaluation_authorized",
        "corrective_measurement_reevaluation_count",
        "corrective_measurement_reevaluation_limit",
        "measurement_repair_merge_commit",
        "original_development_run_count",
    }
)


def compute_contract_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k not in _DIGEST_EXCLUDED_KEYS}
    return hashlib.sha256(_canonical_dumps(body).encode("utf-8")).hexdigest()


def validate_measurement_contract(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require(payload.get("status") == REQUIRED_STATUS, "STATUS_NOT_DEFINITION_ONLY")
    _require(payload.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _require(
        payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY,
        "STRATEGY_IDENTITY",
    )
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
        baseline.get("sole_difference_vs_treatment") == "VOLATILITY_DECAY_ADMISSION",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("period") == 14, "ATR_PERIOD")
    _require(vol.get("normalization") == "ATR_DIV_CLOSE", "ATR_NORMALIZATION")
    pct = vol.get("percentile_metric") or {}
    _require(pct.get("rolling_lookback_bars") == 120, "PERCENTILE_LOOKBACK")
    _require(
        pct.get("percentile_tie_method") == "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF",
        "PERCENTILE_TIE_METHOD",
    )
    _require(pct.get("percentile_rank_window_includes_current_value") is True, "PERCENTILE_CURRENT")

    decay = admission.get("decay_confirmation") or {}
    _require(decay.get("threshold_exclusive_max") == 0.40, "DECAY_THR")
    _require(decay.get("high_vol_prior_threshold_inclusive_min") == 0.70, "HIGH_VOL_PRIOR")
    _require(
        decay.get("normalized_atr_strictly_decreasing_on_confirmation_bar") is True,
        "DECAY_ATR_NOT_DECREASING",
    )
    _require(
        decay.get("must_be_fully_confirmed_from_past_completed_bars_only") is True,
        "DECAY_NOT_PAST_ONLY",
    )

    lifecycle = admission.get("decay_event_lifecycle") or {}
    _require(lifecycle.get("event_consumption") == "SINGLE_USE", "EVENT_NOT_SINGLE_USE")
    _require(lifecycle.get("compression_regime_not_required") is True, "COMPRESSION_REQUIRED")
    _require(
        lifecycle.get("expansion_persistence_not_required") is True,
        "EXPANSION_PERSISTENCE_REQUIRED",
    )
    _require(
        lifecycle.get("decay_window_start_offset_after_confirmation_bar") == 1,
        "DECAY_START",
    )
    _require(
        lifecycle.get("decay_window_end_offset_after_confirmation_bar") == 8,
        "DECAY_END",
    )
    _require(lifecycle.get("decay_window_bars") == [1, 2, 3, 4, 5, 6, 7, 8], "DECAY_BARS")
    _require(lifecycle.get("max_entries_per_decay_event") == 1, "MAX_ENTRIES_NOT_ONE")
    _require(lifecycle.get("rearm_threshold_inclusive_min") == 0.70, "REARM_THRESHOLD")
    _require(
        lifecycle.get(
            "rearm_requires_normalized_atr_percentile_at_or_above_high_vol_threshold_"
            "for_at_least_one_completed_bar"
        )
        is True,
        "REARM_NOT_BOUND",
    )
    _require(lifecycle.get("no_entry_on_decay_confirmation_bar_t") is True, "ENTRY_ON_T_ALLOWED")

    entry = admission.get("directional_entry") or {}
    _require(entry.get("channel_lookback_completed_bars") == 20, "CHANNEL_LOOKBACK")
    _require(
        entry.get("entry_on_decay_confirmation_bar_t_forbidden") is True,
        "ENTRY_ON_T_ALLOWED_DIR",
    )
    _require(
        entry.get("double_play_remains_sole_downstream_authority") is True,
        "DOUBLE_PLAY_DOWNSTREAM",
    )

    exits = payload.get("exit_semantics") or {}
    _require(exits.get("frozen") is True, "EXIT_NOT_FROZEN")
    _require(exits.get("initial_stop_atr_multiple") == 1.5, "INITIAL_STOP")
    _require(exits.get("trailing_stop_atr_multiple") == 2.0, "TRAILING_STOP")
    _require(exits.get("time_exit_max_bars") == 48, "TIME_EXIT")
    _require(exits.get("second_pnl_truth_forbidden") is True, "SECOND_PNL_TRUTH")
    _require(
        exits.get("productive_exit_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )

    events = payload.get("event_sufficiency_gates") or {}
    _require(events.get("frozen") is True, "EVENT_GATES_NOT_FROZEN")
    _require(events.get("min_evaluable_treatment_breakout_events") == 50, "MIN_EVENTS")
    _require(events.get("min_executed_treatment_trades") == 30, "MIN_TRADES")
    _require(events.get("min_evaluable_treatment_events_per_time_segment") == 10, "MIN_SEG_EVENTS")

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

    param_gov = payload.get("parameter_governance") or {}
    _require(param_gov.get("open_parameters_remaining") is False, "OPEN_PARAMETERS")
    _require(param_gov.get("definition_semantics_complete") is True, "SEMANTICS_INCOMPLETE")
    frozen = param_gov.get("frozen_parameters") or {}
    _require(frozen.get("atr_period") == 14, "FROZEN_ATR_PERIOD")
    _require(frozen.get("decay_confirmation_threshold_exclusive_max") == 0.40, "FROZEN_DECAY_THR")
    _require(frozen.get("high_vol_prior_threshold_inclusive_min") == 0.70, "FROZEN_HIGH_VOL")
    _require(frozen.get("decay_window_start_offset") == 1, "FROZEN_DECAY_START")
    _require(frozen.get("decay_window_end_offset") == 8, "FROZEN_DECAY_END")
    _require(frozen.get("decay_event_consumption") == "SINGLE_USE", "FROZEN_EVENT_MODE")

    md = payload.get("material_difference_vs_terminal_coiled_spring") or {}
    _require(md.get("prior_terminal_hypothesis_id") == REQUIRED_PRIOR, "PRIOR_HYPOTHESIS")
    _require(md.get("unchanged_binding_retry_forbidden") is True, "UNCHANGED_RETRY")

    md_vcb = payload.get("material_difference_vs_volatility_compression_breakout_v1") or {}
    _require(md_vcb.get("prior_strategy_identity") == REQUIRED_PRIOR_VCB, "PRIOR_VCB")
    _require(md_vcb.get("vcb_retry_forbidden") is True, "VCB_RETRY_ALLOWED")
    _require(md_vcb.get("not_a_parameter_change_of_vcb_v1") is True, "VCB_PARAM_CHANGE")

    md_vep = payload.get("material_difference_vs_volatility_expansion_persistence_v1") or {}
    _require(md_vep.get("prior_strategy_identity") == REQUIRED_PRIOR_VEP, "PRIOR_VEP")
    _require(md_vep.get("vep_retry_forbidden") is True, "VEP_RETRY_ALLOWED")
    _require(md_vep.get("not_a_parameter_change_of_vep_v1") is True, "VEP_PARAM_CHANGE")
    _require(md_vep.get("not_a_repair_or_retry_of_vep_v1") is True, "VEP_REPAIR")
    vep_diffs = md_vep.get("differences") or {}
    for key in (
        "admission_polarity",
        "confirmation_rule",
        "entry_window",
        "not_an_exit_repair",
        "rearm_rule",
        "target_phenomenon",
    ):
        _require(bool(vep_diffs.get(key)), f"MISSING_VEP_MATERIAL_DIFFERENCE:{key}")

    tsd = payload.get("time_segment_definition") or {}
    _require(
        tsd.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_ID",
    )

    on_fail = (payload.get("terminal_decision_semantics") or {}).get("on_fail") or {}
    _require(on_fail.get("retry_allowed") is False, "ON_FAIL_RETRY")
    _require(on_fail.get("terminal_result") == "FAIL_CLOSED_NO_RETRY", "ON_FAIL_TERMINAL")

    shared = payload.get("shared_authority_constraints") or {}
    for key in (
        "master_v2_mutation_forbidden",
        "double_play_sole_directional_transition_authority",
        "risk_authority_mutation_forbidden",
        "execution_kernel_mutation_forbidden",
    ):
        _require(shared.get(key) is True, f"SHARED_AUTH_{key.upper()}")

    gates = payload.get("promotion_and_economic_gate_policy") or {}
    _require(gates.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _require(gates.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
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
        "directional_form": REQUIRED_DIRECTIONAL_FORM,
        "baseline_id": REQUIRED_BASELINE_ID,
        "contract_digest": digest,
        "definition_only": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "dataset_bound": True,
        "development_run_count": 1,
        "runner_start_count": 1,
        "open_parameters_remaining": False,
        "definition_semantics_complete": True,
        "decay_event_consumption": "SINGLE_USE",
        "decay_window_bars": [1, 2, 3, 4, 5, 6, 7, 8],
        "material_difference_explicit": True,
        "material_difference_from_vcb_v1": True,
        "material_difference_from_vep_v1": True,
        "exit_semantics_frozen": True,
        "event_sufficiency_frozen": True,
        "productive_pnl_evaluator_referenced": True,
        "second_pnl_truth_created": False,
        "pending_threshold_keys": [],
        "time_segment_definition_id": REQUIRED_TIME_SEGMENT_DEFINITION_ID,
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
