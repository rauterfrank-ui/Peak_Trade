"""Definition-only preregistration validator for volatility compression breakout v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "VOLATILITY_COMPRESSION_BREAKOUT_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_compression_breakout_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_COMPRESSION_BREAKOUT_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = "docs/evidence/preregister_volatility_compression_breakout_hypothesis_v1/"
REQUIRED_HYPOTHESIS_ID = "VOLATILITY_COMPRESSION_BREAKOUT_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_COMPRESSION_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "VOLATILITY_COMPRESSION_TO_EXPANSION_TRANSITION"
REQUIRED_DIRECTIONAL_FORM = "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT"
REQUIRED_BASELINE_ID = "UNCONDITIONAL_20_BAR_PRICE_CHANNEL_BREAKOUT_V1"
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
REQUIRED_DATASET = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_PRIOR = "VOL_BREAKOUT_COILED_SPRING_NON_BITCOIN_FUTURES_V1"
CONFIGURED_OPERATOR_THRESHOLD_KEYS = frozenset(
    {
        "min_evaluable_treatment_breakout_events",
        "min_executed_treatment_trades",
        "min_evaluable_treatment_events_per_time_segment",
        "time_segment_robustness_pass_ratio",
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
    body = {k: v for k, v in payload.items() if k not in ("contract_digest", "provenance")}
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
        payload.get("development_evaluation_authorized") is False,
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
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")
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
        baseline.get("sole_difference_vs_treatment") == "COMPRESSION_TO_EXPANSION_ADMISSION",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("period") == 20, "ATR_PERIOD")
    _require(vol.get("normalization") == "ATR_DIV_CLOSE", "ATR_NORMALIZATION")
    _require(vol.get("lookahead_forbidden") is True, "LOOKAHEAD")
    compression = admission.get("compression_metric") or {}
    _require(compression.get("rolling_lookback_bars") == 120, "COMPRESSION_LOOKBACK")
    _require(compression.get("compression_threshold_inclusive_max") == 0.20, "COMPRESSION_THR")
    _require(
        compression.get("range_ratio_substitution_forbidden") is True,
        "RANGE_RATIO_SUBSTITUTION",
    )
    duration = admission.get("min_compression_duration") or {}
    _require(duration.get("bars") == 12, "MIN_COMPRESSION_BARS")
    _require(duration.get("tolerance_gap_bars") == 0, "COMPRESSION_TOLERANCE")
    expansion = admission.get("expansion_release") or {}
    _require(expansion.get("threshold_inclusive_min") == 0.75, "EXPANSION_THR")
    _require(expansion.get("max_bars_after_last_compression_bar") == 6, "EXPANSION_MAX_GAP")
    entry = admission.get("directional_entry") or {}
    _require(entry.get("channel_lookback_completed_bars") == 20, "CHANNEL_LOOKBACK")
    _require(entry.get("ambiguity_fail_closed_no_entry") is True, "AMBIGUITY_FAIL_CLOSED")

    exits = payload.get("exit_semantics") or {}
    _require(exits.get("frozen") is True, "EXIT_NOT_FROZEN")
    _require(exits.get("initial_stop_atr_multiple") == 1.5, "INITIAL_STOP")
    _require(exits.get("trailing_stop_atr_multiple") == 2.0, "TRAILING_STOP")
    _require(exits.get("regime_exit_percentile_rank_lt") == 0.50, "REGIME_EXIT")
    _require(exits.get("time_exit_max_bars") == 48, "TIME_EXIT")
    _require(exits.get("first_event_wins") is True, "FIRST_EVENT")
    _require(exits.get("reversal_forbidden") is True, "REVERSAL")
    _require(exits.get("scale_in_forbidden") is True, "SCALE_IN")
    _require(exits.get("pyramiding_forbidden") is True, "PYRAMIDING")

    events = payload.get("event_sufficiency_gates") or {}
    _require(events.get("frozen") is True, "EVENT_GATES_NOT_FROZEN")
    _require(events.get("min_evaluable_treatment_breakout_events") == 50, "MIN_EVENTS")
    _require(events.get("min_executed_treatment_trades") == 20, "MIN_TRADES")
    _require(events.get("min_evaluable_treatment_events_per_time_segment") == 10, "MIN_SEG_EVENTS")
    _require(events.get("both_event_and_trade_gates_required") is True, "BOTH_GATES")

    economic = payload.get("economic_admission_contract") or {}
    _require(
        economic.get("evaluation_blocked_while_any_threshold_pending") is False,
        "PENDING_STILL_BLOCKING",
    )
    pending = set(economic.get("pending_threshold_keys") or [])
    _require(pending == set(), "PENDING_THRESHOLD_KEYS_NONEMPTY")
    thresholds = economic.get("thresholds") or {}
    for key, expected in (
        ("gross_profit_factor_min", 1.0),
        ("net_profit_factor_min", 1.3),
        ("maximum_max_drawdown", 0.25),
        ("min_evaluable_treatment_breakout_events", 50),
        ("min_executed_treatment_trades", 20),
        ("min_evaluable_treatment_events_per_time_segment", 10),
        ("cost_stress_1_5x_net_profit_factor_min", 1.0),
        ("time_segment_robustness_pass_ratio", 0.5),
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
    _require(param_gov.get("all_parameters_preregistered") is True, "NOT_ALL_PREREGISTERED")
    _require(param_gov.get("post_hoc_tuning_forbidden") is True, "POST_HOC_TUNING")
    grid = param_gov.get("development_only_bounded_grid") or {}
    _require(grid.get("authorized") is False, "GRID_AUTHORIZED")

    md = payload.get("material_difference_vs_terminal_coiled_spring") or {}
    _require(md.get("prior_terminal_hypothesis_id") == REQUIRED_PRIOR, "PRIOR_HYPOTHESIS")
    _require(md.get("unchanged_binding_retry_forbidden") is True, "UNCHANGED_RETRY")
    diffs = md.get("differences") or {}
    for key in (
        "vol_estimator",
        "compression_gate",
        "expansion_gate",
        "entry",
        "baseline",
        "program_identity",
    ):
        _require(bool(diffs.get(key)), f"MISSING_MATERIAL_DIFFERENCE:{key}")

    tsd = payload.get("time_segment_definition") or {}
    _require(
        tsd.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_ID",
    )
    _require(tsd.get("authority") == "EXPLICIT_OPERATOR_AUTHORIZATION", "TIME_SEGMENT_AUTH")
    _require(tsd.get("total_time_segments") == 4, "TIME_SEGMENT_COUNT")
    _require(tsd.get("all_segments_must_be_evaluable") is True, "TIME_SEGMENT_ALL_EVALUABLE")
    _require(tsd.get("generic_walk_forward_v1_bound") is False, "WALK_FORWARD_BOUND")

    on_fail = (payload.get("terminal_decision_semantics") or {}).get("on_fail") or {}
    _require(on_fail.get("retry_allowed") is False, "ON_FAIL_RETRY")
    _require(on_fail.get("post_hoc_tuning_forbidden") is True, "ON_FAIL_TUNING")
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
        "development_run_count": 0,
        "runner_start_count": 0,
        "open_parameters_remaining": False,
        "material_difference_explicit": True,
        "exit_semantics_frozen": True,
        "event_sufficiency_frozen": True,
        "pending_threshold_keys": [],
        "time_segment_definition_id": REQUIRED_TIME_SEGMENT_DEFINITION_ID,
    }


def reject_holdout_dataset_or_path(token: str) -> None:
    """Fail closed on sealed-holdout identifiers or paths."""
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
