"""Definition-only preregistration validator for VDBX explicit-decay-exit v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_HYPOTHESIS_PREREGISTRATION=true"
)
CONTRACT_REL_PATH = (
    "config/research/"
    "volatility_decay_breakout_with_explicit_decay_exit_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_"
    "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_volatility_decay_breakout_with_explicit_decay_exit_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = (
    "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"
REQUIRED_PREDECESSOR = "VOLATILITY_DECAY_BREAKOUT_V1"
REQUIRED_PROGRAM_ID = "VOLATILITY_REGIME_RESEARCH_PROGRAM_V1"
REQUIRED_SIGNAL_FAMILY = "VOLATILITY_REGIME"
REQUIRED_TARGET = "VOLATILITY_DECAY_AFTER_HIGH_VOL_THEN_CHANNEL_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT"
REQUIRED_DIRECTIONAL_FORM = "OWN_INSTRUMENT_MUTUALLY_EXCLUSIVE_CHANNEL_BREAKOUT"
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
    "TRAILING_STOP",
    "SIGNAL_EXIT",
    "REGIME_INVALIDATION",
    "TIME_EXIT",
    "END_OF_INSTRUMENT_LIQUIDATION",
    "END_OF_PANEL_LIQUIDATION",
]


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
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("predecessor_strategy_id") == REQUIRED_PREDECESSOR, "PREDECESSOR")
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("signal_family") == REQUIRED_SIGNAL_FAMILY, "SIGNAL_FAMILY")
    _require(payload.get("target_phenomenon") == REQUIRED_TARGET, "TARGET_PHENOMENON")
    _require(payload.get("dataset_id") == REQUIRED_DATASET, "DATASET_ID")
    _require(payload.get("dataset_bound") is True, "DATASET_NOT_BOUND")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    # Terminal post-execution state after the single authorized Development evaluation
    # consumed the run slot with FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT.
    _require(payload.get("development_evaluation_authorized") is True, "DEV_EVAL_NOT_AUTHORIZED")
    _require(payload.get("development_evaluation_executed") is True, "DEV_EVAL_NOT_EXECUTED")
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED",
        "HOLDOUT_NOT_UNBOUND",
    )
    _require(payload.get("strategy_implementation_present") is True, "STRATEGY_IMPL_MISSING")
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_NOT_CONSUMED")
    run_limit = payload.get("run_limit") or {}
    _require(run_limit.get("development_run_limit") == 1, "RUN_LIMIT_NOT_ONE")
    _require(run_limit.get("retry_forbidden") is True, "RETRY_NOT_FORBIDDEN")

    directional = payload.get("directional_form") or {}
    _require(directional.get("selected") == REQUIRED_DIRECTIONAL_FORM, "DIRECTIONAL_FORM")
    _require(directional.get("double_play_remains_sole_authority") is True, "DOUBLE_PLAY_NOT_SOLE")

    baseline = payload.get("baseline") or {}
    _require(baseline.get("baseline_id") == REQUIRED_BASELINE_ID, "BASELINE_ID")
    _require(baseline.get("frozen") is True, "BASELINE_NOT_FROZEN")
    _require(
        baseline.get("sole_difference_vs_treatment")
        == "VOLATILITY_DECAY_ADMISSION_PLUS_EXPLICIT_DECAY_EXIT_STATE_MACHINE",
        "BASELINE_SOLE_DIFF",
    )

    admission = payload.get("admission_mechanism") or {}
    vol = admission.get("vol_estimator") or {}
    _require(vol.get("period") == 14, "ATR_PERIOD")
    decay = admission.get("decay_confirmation") or {}
    _require(decay.get("threshold_exclusive_max") == 0.40, "DECAY_THR")
    _require(decay.get("high_vol_prior_threshold_inclusive_min") == 0.70, "HIGH_VOL_PRIOR")
    lifecycle = admission.get("decay_event_lifecycle") or {}
    _require(lifecycle.get("decay_window_bars") == [1, 2, 3, 4, 5, 6, 7, 8], "DECAY_BARS")
    entry = admission.get("directional_entry") or {}
    _require(entry.get("ex_ante_exit_reachability_required") is True, "REACHABILITY_NOT_REQUIRED")
    _require(entry.get("min_post_fill_bars_required_inclusive") == 48, "MIN_POST_FILL")

    exits = payload.get("exit_semantics") or {}
    _require(exits.get("frozen") is True, "EXIT_NOT_FROZEN")
    _require(exits.get("exit_state_machine_implemented") is True, "EXIT_SM_MISSING")
    _require(exits.get("every_admitted_entry_must_have_reachable_exit") is True, "EXIT_REACHABLE")
    _require(
        exits.get("evaluator_side_reconstruction_of_missing_strategy_exits_forbidden") is True,
        "EVALUATOR_RECONSTRUCTION_ALLOWED",
    )
    _require(
        exits.get("synthetic_fills_solely_to_pair_trades_forbidden") is True, "SYNTHETIC_FILLS"
    )
    _require(exits.get("second_pnl_truth_forbidden") is True, "SECOND_PNL_TRUTH")
    _require(exits.get("second_equity_truth_forbidden") is True, "SECOND_EQUITY_TRUTH")
    _require(exits.get("second_stats_truth_forbidden") is True, "SECOND_STATS_TRUTH")
    _require(exits.get("precedence_ascending_wins_first") == REQUIRED_PRECEDENCE, "PRECEDENCE")
    _require(exits.get("initial_stop_atr_multiple") == 1.5, "INITIAL_STOP")
    _require(exits.get("trailing_stop_atr_multiple") == 2.0, "TRAILING_STOP")
    _require(exits.get("time_exit_max_bars") == 48, "TIME_EXIT")
    _require(
        exits.get("productive_exit_pnl_evaluator_ref") == REQUIRED_PRODUCTIVE_PNL_REF,
        "PRODUCTIVE_PNL_REF",
    )
    signal_exit = exits.get("signal_exit") or {}
    _require(signal_exit.get("threshold_inclusive_min") == 0.70, "SIGNAL_EXIT_THR")
    _require(exits.get("regime_invalidation_percentile_rank_lt") == 0.50, "REGIME_INV")
    _require((exits.get("end_of_panel_liquidation") or {}).get("authorized") is True, "EOP")
    _require((exits.get("end_of_instrument_liquidation") or {}).get("authorized") is True, "EOI")
    _require(
        (exits.get("same_bar_entry_exit") or {}).get(
            "same_bar_fill_and_non_terminal_exit_forbidden"
        )
        is True,
        "SAME_BAR",
    )

    portfolio = payload.get("portfolio") or {}
    _require(portfolio.get("portfolio_aggregation_id") == REQUIRED_PORTFOLIO, "PORTFOLIO")

    pg = payload.get("parameter_governance") or {}
    _require(pg.get("open_parameters_remaining") is False, "OPEN_PARAMETERS")
    _require(pg.get("all_parameters_preregistered") is True, "PARAMS_NOT_PREREG")

    md_vdb = payload.get("material_difference_vs_volatility_decay_breakout_v1") or {}
    _require(md_vdb.get("predecessor_strategy_identity") == REQUIRED_PREDECESSOR, "MD_PRED")
    _require(md_vdb.get("vdb_retry_forbidden") is True, "VDB_RETRY_ALLOWED")
    _require(md_vdb.get("not_a_corrective_retry_of_vdb_v1") is True, "VDB_CORRECTIVE_RETRY")
    md_vep = payload.get("material_difference_vs_volatility_expansion_persistence_v1") or {}
    _require(md_vep.get("vep_retry_forbidden") is True, "VEP_RETRY_ALLOWED")
    md_vcb = payload.get("material_difference_vs_volatility_compression_breakout_v1") or {}
    _require(md_vcb.get("vcb_retry_forbidden") is True, "VCB_RETRY_ALLOWED")

    runtime = payload.get("runtime_policy") or {}
    _require(runtime.get("live_authorized") is False, "LIVE_AUTHORIZED")
    _require(runtime.get("orders_allowed") is False, "ORDERS")

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "DIGEST_MISMATCH")

    return {
        "valid": True,
        "definition_only": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "predecessor_strategy_id": REQUIRED_PREDECESSOR,
        "directional_form": REQUIRED_DIRECTIONAL_FORM,
        "baseline_id": REQUIRED_BASELINE_ID,
        "evaluation_authorized": False,
        "development_evaluation_authorized": True,
        "development_evaluation_executed": True,
        "holdout_authorized": False,
        "dataset_bound": True,
        "development_run_count": 1,
        "runner_start_count": 1,
        "open_parameters_remaining": False,
        "exit_state_machine_complete": True,
        "exit_precedence_complete": True,
        "materially_distinct_from_predecessor": True,
        "productive_pnl_evaluator_referenced": True,
        "second_pnl_truth_created": False,
        "second_equity_truth_created": False,
        "second_stats_truth_created": False,
        "time_segment_definition_id": REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "portfolio_aggregation_id": REQUIRED_PORTFOLIO,
        "contract_digest": digest,
    }


def reject_holdout_dataset_or_path(token: str) -> None:
    lowered = token.lower()
    if "holdout" in lowered or "sealed_long_panel" in lowered:
        raise PreregistrationValidationError("HOLDOUT")


def load_and_validate_repo_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    _require(path.is_file(), "CONTRACT_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return validate_measurement_contract(payload)
