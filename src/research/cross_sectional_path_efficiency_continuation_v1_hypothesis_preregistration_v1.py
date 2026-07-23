"""Definition-only preregistration validator for CS path-efficiency continuation v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "cross_sectional_path_efficiency_continuation_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_cross_sectional_path_efficiency_continuation_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_PROGRAM_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1"
REQUIRED_WORKSTREAM_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_WORKSTREAM_V1"
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_DIRECTIONAL_FORM = "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
REQUIRED_SCORE_FAMILY = "path_efficiency_ratio_times_sign_net_log_return_fixed_lookback_v1"
REQUIRED_POLARITY = "PATH_EFFICIENCY_CONTINUATION_ER_TIMES_SIGN"
REQUIRED_SOLE_AUTHORITY = "trading.master_v2.double_play_state.transition_state"


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
    _require(payload.get("program_id") == REQUIRED_PROGRAM_ID, "PROGRAM_ID")
    _require(payload.get("workstream_id") == REQUIRED_WORKSTREAM_ID, "WORKSTREAM_ID")
    _require(
        payload.get("strategy_identity") == "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1",
        "STRATEGY_IDENTITY",
    )
    _require(payload.get("signal_family") == "CROSS_SECTIONAL_PATH_EFFICIENCY", "SIGNAL_FAMILY")
    _require(
        payload.get("target_phenomenon")
        == "CROSS_SECTIONAL_PATH_EFFICIENCY_DIRECTIONAL_CONTINUATION",
        "TARGET_PHENOMENON",
    )
    _require(
        payload.get("treatment_type")
        == "OWN_INSTRUMENT_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_ADMISSION",
        "TREATMENT_TYPE",
    )
    _require(
        payload.get("dataset_id")
        == "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1",
        "DATASET_ID",
    )
    _require(payload.get("dataset_class") == "DEVELOPMENT_ONLY", "DATASET_CLASS")
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
    )
    _require(payload.get("implementation_authorized") is False, "IMPLEMENTATION_AUTHORIZED")
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("development_run_count") == 1, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 1, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is True, "RUN_SLOT_CONSUMED")
    run_limit = payload.get("run_limit") or {}
    _require(run_limit.get("development_run_limit") == 1, "DEVELOPMENT_RUN_LIMIT")
    _require(run_limit.get("retry_forbidden") is True, "RETRY_NOT_FORBIDDEN")
    _require(
        run_limit.get("second_development_run_forbidden") is True,
        "SECOND_DEV_RUN_ALLOWED",
    )
    directional = payload.get("directional_form") or {}
    _require(directional.get("selected") == REQUIRED_DIRECTIONAL_FORM, "DIRECTIONAL_FORM")
    _require(
        directional.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )
    _require(
        directional.get("sole_directional_transition_authority") == REQUIRED_SOLE_AUTHORITY,
        "SOLE_AUTHORITY",
    )
    _require(
        directional.get("hypothesis_emits_rank_intent_only") is True,
        "NOT_RANK_INTENT_ONLY",
    )
    score = payload.get("score_and_selection") or {}
    _require(score.get("score_family_policy") == REQUIRED_SCORE_FAMILY, "SCORE_FAMILY")
    _require(score.get("not_a_cs_momentum_parameter_retune") is True, "CS_MOMENTUM_RETUNE")
    _require(
        score.get("not_a_csrhr_continuation_or_semantic_reuse") is True,
        "CSRHR_REUSE",
    )
    _require(score.get("polarity") == REQUIRED_POLARITY, "POLARITY")
    _require(score.get("selection_mode") == "single_top1_by_score_desc", "SELECTION_MODE")
    _require(score.get("selection_count_fixed_n") == 1, "SELECTION_COUNT")
    _require(
        score.get("tie_break_policy") == "score_desc_then_instrument_id_asc",
        "TIE_BREAK",
    )
    _require(score.get("quantile_selection_forbidden_in_v1") is True, "QUANTILES_ALLOWED")
    _require(score.get("adaptive_thresholding_forbidden") is True, "ADAPTIVE_ALLOWED")
    _require(score.get("signal_lag_bars") == 1, "SIGNAL_LAG")
    eligibility = score.get("eligibility_fail_closed") or {}
    _require(eligibility.get("path_sum_zero_ineligible") is True, "PATH_SUM_ZERO")
    _require(eligibility.get("sign_zero_ineligible") is True, "SIGN_ZERO")
    _require(
        eligibility.get("eligible_count_lt_min_rebalance_not_evaluable") is True,
        "ELIGIBLE_COUNT_GATE",
    )
    _require(eligibility.get("fallback_selection_forbidden") is True, "FALLBACK_ALLOWED")
    frozen = (payload.get("parameter_governance") or {}).get("frozen_non_grid_parameters") or {}
    _require(frozen.get("lookback_N") == 48, "LOOKBACK_N")
    _require(frozen.get("rebalance_interval_bars") == 8, "REBALANCE_INTERVAL")
    _require(frozen.get("signal_lag_bars") == 1, "FROZEN_SIGNAL_LAG")
    _require(frozen.get("min_eligible_members_for_rank") == 5, "MIN_ELIGIBLE")
    _require(frozen.get("selection_count_fixed_n") == 1, "FROZEN_SELECTION_COUNT")
    _require(frozen.get("vol_normalization") is False, "VOL_NORM")
    _require(frozen.get("strategy_stop") == "none", "STRATEGY_STOP")
    _require(frozen.get("minimum_hold_policy") == "until_next_rebalance", "HOLD_POLICY")
    grid = (payload.get("parameter_governance") or {}).get("development_only_bounded_grid") or {}
    _require(grid.get("authorized") is False, "GRID_AUTHORIZED")
    costs = payload.get("costs") or {}
    _require(costs.get("fee_bps_per_side") == 10.0, "FEE_BPS")
    _require(costs.get("slippage_bps_per_side") == 5.0, "SLIPPAGE_BPS")
    _require(costs.get("half_spread_bps") == 5.0, "HALF_SPREAD_BPS")
    _require(
        costs.get("predefined_cost_stress_multipliers") == [0.5, 1.0, 1.5, 2.0],
        "COST_MULTIPLIERS",
    )
    thresholds = (payload.get("economic_admission_contract") or {}).get("thresholds") or {}
    _require(thresholds.get("minimum_trade_count", {}).get("value") == 50, "MIN_TRADES")
    _require(
        thresholds.get("minimum_rebalance_observations", {}).get("value") == 30,
        "MIN_REBALANCES",
    )
    _require(thresholds.get("net_profit_factor_min", {}).get("value") == 1.3, "NET_PF")
    _require(thresholds.get("maximum_max_drawdown", {}).get("value") == 0.25, "MAX_DD")
    _require(
        thresholds.get("time_segment_robustness_pass_ratio", {}).get("value") == 0.5,
        "TIME_SEG_RATIO",
    )
    _require(
        payload.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION",
    )
    econ = payload.get("promotion_and_economic_gate_policy") or {}
    _require(econ.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    shared = payload.get("shared_authority_constraints") or {}
    _require(shared.get("master_v2_mutation_forbidden") is True, "MASTER_V2_MUTATION")
    _require(
        shared.get("double_play_sole_directional_transition_authority") is True,
        "DOUBLE_PLAY_AUTHORITY",
    )
    _require(shared.get("execution_kernel_mutation_forbidden") is True, "EXECUTION_MUTATION")
    _require(shared.get("risk_authority_mutation_forbidden") is True, "RISK_MUTATION")
    _require(
        payload.get("sealed_holdout_binding_status") == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN",
        "HOLDOUT_STATUS",
    )
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "CONTRACT_DIGEST_MISMATCH")
    return {
        "valid": True,
        "definition_only": True,
        "contract_digest": digest,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "evaluation_authorized": False,
        "implementation_authorized": False,
        "development_run_count": 1,
        "development_run_limit": 1,
    }


def load_and_validate_repo_contract(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONTRACT_REL_PATH
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = validate_measurement_contract(payload)
    evidence = repo_root / EVIDENCE_REL_PATH
    _require((evidence / "summary.json").is_file(), "EVIDENCE_SUMMARY_MISSING")
    _require((evidence / "safety_attestation.md").is_file(), "SAFETY_ATTESTATION_MISSING")
    gov = repo_root / GOVERNANCE_REL_PATH
    _require(gov.is_file(), "GOVERNANCE_DOC_MISSING")
    return report
