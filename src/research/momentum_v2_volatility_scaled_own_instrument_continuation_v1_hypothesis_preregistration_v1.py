"""Definition-only preregistration validator for Momentum V2 vol-scaled continuation v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION=true"
)
CONTRACT_REL_PATH = (
    "config/research/"
    "momentum_v2_volatility_scaled_own_instrument_continuation_v1_preregistered_"
    "economic_hypothesis_measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_momentum_v2_volatility_scaled_own_instrument_"
    "continuation_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
REQUIRED_PROGRAM_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1"
)
REQUIRED_WORKSTREAM_ID = "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_WORKSTREAM_V1"
REQUIRED_SCOPE_ID = (
    "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
    "DEFINITION_ONLY_PREREGISTRATION_V1"
)
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_DIRECTIONAL_FORM = "OWN_INSTRUMENT_LONG_ENTRY_EXIT_EVENT_TIMING_ONLY"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
REQUIRED_BASELINE_ID = "FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1"
REQUIRED_TREATMENT_ID = "VOLATILITY_SCALED_MOMENTUM_SCORE_THRESHOLD_CROSS_V1"
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
    _require(payload.get("scope_id") == REQUIRED_SCOPE_ID, "SCOPE_ID")
    _require(
        payload.get("strategy_identity")
        == "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1",
        "STRATEGY_IDENTITY",
    )
    _require(
        payload.get("signal_family") == "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM",
        "SIGNAL_FAMILY",
    )
    _require(
        payload.get("target_phenomenon")
        == "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM_CONTINUATION",
        "TARGET_PHENOMENON",
    )
    _require(
        payload.get("treatment_type")
        == "OWN_INSTRUMENT_VOLATILITY_SCALED_MOMENTUM_CONTINUATION_ADMISSION",
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
    _require(
        payload.get("development_evaluation_executed") is False,
        "DEVELOPMENT_EVALUATION_EXECUTED",
    )
    _require(payload.get("holdout_authorized") is False, "HOLDOUT_AUTHORIZED")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT_NOT_FORBIDDEN")
    _require(
        payload.get("strategy_implementation_present") is False,
        "STRATEGY_IMPLEMENTATION_PRESENT",
    )
    _require(payload.get("development_run_count") == 0, "DEVELOPMENT_RUN_COUNT")
    _require(payload.get("runner_start_count") == 0, "RUNNER_START_COUNT")
    _require(payload.get("run_slot_consumed") is False, "RUN_SLOT_CONSUMED")

    baseline = payload.get("baseline") or {}
    _require(baseline.get("baseline_id") == REQUIRED_BASELINE_ID, "BASELINE_ID")
    _require(baseline.get("lookback_period") == 20, "BASELINE_LOOKBACK")
    _require(baseline.get("entry_threshold") == 0.02, "BASELINE_ENTRY")
    _require(baseline.get("exit_threshold") == -0.01, "BASELINE_EXIT")
    _require(
        baseline.get("sole_difference_vs_treatment")
        == "VOLATILITY_SCALING_OF_MOMENTUM_SCORE_BEFORE_THRESHOLD_CROSS",
        "SOLE_DIFFERENCE",
    )

    treatment = payload.get("treatment") or {}
    _require(treatment.get("treatment_id") == REQUIRED_TREATMENT_ID, "TREATMENT_ID")
    _require(treatment.get("vol_scaled_entry_z") == 1.0, "ENTRY_Z")
    _require(treatment.get("vol_scaled_exit_z") == 0.0, "EXIT_Z")

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
    _require(directional.get("entry_side_ratification") == "NONE", "ENTRY_SIDE")

    frozen = (payload.get("parameter_governance") or {}).get("frozen_non_grid_parameters") or {}
    _require(frozen.get("lookback_period") == 20, "LOOKBACK_PERIOD")
    _require(frozen.get("vol_scaled_entry_z") == 1.0, "FROZEN_ENTRY_Z")
    _require(frozen.get("vol_scaled_exit_z") == 0.0, "FROZEN_EXIT_Z")
    _require(frozen.get("vol_scaling_required") is True, "VOL_SCALING_REQUIRED")
    _require(frozen.get("pit_safe") is True, "PIT_SAFE")
    _require(frozen.get("short_entry_forbidden") is True, "SHORT_ENTRY")
    _require(frozen.get("registry_mutation_forbidden") is True, "REGISTRY_MUTATION")
    grid = (payload.get("parameter_governance") or {}).get("development_only_bounded_grid") or {}
    _require(grid.get("authorized") is False, "GRID_AUTHORIZED")

    universe = payload.get("universe_scope") or {}
    _require(universe.get("bitcoin_excluded") is True, "BTC_EXCLUDED")
    _require(universe.get("spot_excluded") is True, "SPOT_EXCLUDED")

    pit = payload.get("pit_feature_policy") or {}
    _require(pit.get("pit_safe") is True, "PIT_POLICY")
    _require(pit.get("lookahead_forbidden") is True, "LOOKAHEAD")

    _require(
        payload.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION",
    )
    run_limit = payload.get("run_limit") or {}
    _require(run_limit.get("development_run_limit") == 1, "RUN_LIMIT_NOT_1")
    _require(run_limit.get("retry_forbidden") is True, "RETRY_PERMITTED")
    econ = payload.get("promotion_and_economic_gate_policy") or {}
    _require(econ.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    shared = payload.get("shared_authority_constraints") or {}
    _require(shared.get("master_v2_mutation_forbidden") is True, "MASTER_V2_MUTATION")
    _require(
        shared.get("double_play_sole_directional_transition_authority") is True,
        "DOUBLE_PLAY_AUTHORITY",
    )
    _require(shared.get("registry_second_truth_forbidden") is True, "REGISTRY_SECOND_TRUTH")
    _require(
        shared.get("runtime_bridge_remains_bound_not_activated") is True,
        "RUNTIME_BRIDGE",
    )
    rt = payload.get("runtime_policy") or {}
    for key in (
        "live_authorized",
        "orders_allowed",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "scheduler_authorized",
        "runtime_activated",
    ):
        _require(rt.get(key) is False, f"RUNTIME_POLICY_{key.upper()}")

    thresholds = (payload.get("economic_admission_contract") or {}).get("thresholds") or {}
    _require(thresholds.get("minimum_trade_count", {}).get("value") == 50, "MIN_TRADES")
    _require(thresholds.get("net_profit_factor_min", {}).get("value") == 1.3, "NET_PF_MIN")
    _require(
        (payload.get("economic_admission_contract") or {}).get("primary_decision_metric")
        == "NET_PROFIT_FACTOR",
        "PRIMARY_METRIC",
    )

    digest = compute_contract_digest(payload)
    _require(payload.get("contract_digest") == digest, "CONTRACT_DIGEST_MISMATCH")
    return {
        "valid": True,
        "definition_only": True,
        "contract_digest": digest,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "scope_id": REQUIRED_SCOPE_ID,
        "evaluation_authorized": False,
        "implementation_authorized": False,
        "development_run_count": 0,
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
