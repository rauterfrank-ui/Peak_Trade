"""Definition-only preregistration validator for CS relative-strength momentum v1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_HYPOTHESIS_PREREGISTRATION=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "cross_sectional_relative_strength_momentum_v1_preregistered_economic_hypothesis_"
    "measurement_contract_v1.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_cross_sectional_relative_strength_momentum_hypothesis_v1/"
)
REQUIRED_HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_NON_BITCOIN_PERPETUALS_V1"
REQUIRED_DIRECTIONAL_FORM = "D_MUTUALLY_EXCLUSIVE_DIRECTIONAL_SELECTION"
REQUIRED_STATUS = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_TIME_SEGMENT_DEFINITION_ID = "CHRONOLOGICAL_EQUAL_DURATION_QUARTERS_V1"
CONFIGURED_ROBUSTNESS_THRESHOLD_KEYS = frozenset(
    {
        "minimum_rebalance_observations",
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
        payload.get("strategy_identity") == "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1",
        "STRATEGY_IDENTITY",
    )
    _require(payload.get("signal_family") == "CROSS_SECTIONAL_MOMENTUM", "SIGNAL_FAMILY")
    _require(
        payload.get("target_phenomenon")
        == "PERSISTENCE_OF_RELATIVE_RETURNS_ACROSS_NON_BTC_LINEAR_USDT_FUTURES",
        "TARGET_PHENOMENON",
    )
    _require(payload.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED")
    _require(
        payload.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED",
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

    directional = payload.get("directional_form") or {}
    _require(
        directional.get("selected") == REQUIRED_DIRECTIONAL_FORM,
        "DIRECTIONAL_FORM_NOT_D",
    )
    _require(
        directional.get("double_play_remains_sole_authority") is True,
        "DOUBLE_PLAY_NOT_SOLE",
    )

    admission = payload.get("economic_admission_contract") or {}
    _require(
        admission.get("evaluation_blocked_while_any_threshold_pending") is False,
        "PENDING_STILL_BLOCKING",
    )
    pending = set(admission.get("pending_threshold_keys") or [])
    _require(pending == set(), "PENDING_THRESHOLD_KEYS_NONEMPTY")
    thresholds = admission.get("thresholds") or {}
    for key, expected in (
        ("gross_profit_factor_min", 1.0),
        ("net_profit_factor_min", 1.3),
        ("maximum_max_drawdown", 0.25),
        ("minimum_trade_count", 50),
        ("min_eligible_members_for_rank", 5),
        ("single_trade_dominance_limit", 0.5),
        ("cost_stress_1_5x_net_profit_factor_min", 1.0),
        ("minimum_rebalance_observations", 30),
        ("time_segment_robustness_pass_ratio", 0.5),
    ):
        row = thresholds.get(key) or {}
        _require(row.get("status") == "CONFIGURED", f"THRESHOLD_NOT_CONFIGURED:{key}")
        _require(row.get("value") == expected, f"THRESHOLD_VALUE:{key}")
    for key in CONFIGURED_ROBUSTNESS_THRESHOLD_KEYS:
        row = thresholds.get(key) or {}
        _require(row.get("authority") == "EXPLICIT_OPERATOR_AUTHORIZATION", f"THRESHOLD_AUTH:{key}")
        _require(row.get("not_result_calibrated") is True, f"THRESHOLD_CALIBRATED:{key}")

    tsd = payload.get("time_segment_definition") or {}
    _require(
        tsd.get("time_segment_definition_id") == REQUIRED_TIME_SEGMENT_DEFINITION_ID,
        "TIME_SEGMENT_DEFINITION_ID",
    )
    _require(tsd.get("authority") == "EXPLICIT_OPERATOR_AUTHORIZATION", "TIME_SEGMENT_AUTH")
    _require(tsd.get("not_result_calibrated") is True, "TIME_SEGMENT_CALIBRATED")
    _require(tsd.get("total_time_segments") == 4, "TIME_SEGMENT_COUNT")
    _require(tsd.get("denominator") == 4, "TIME_SEGMENT_DENOMINATOR")
    _require(tsd.get("expected_minimum_passing_segments") == 2, "TIME_SEGMENT_MIN_PASS")
    _require(tsd.get("all_segments_must_be_evaluable") is True, "TIME_SEGMENT_ALL_EVALUABLE")
    _require(tsd.get("non_evaluable_segments_are_pass") is False, "TIME_SEGMENT_NONEVAL_PASS")
    _require(
        tsd.get("non_evaluable_segments_removed_from_denominator") is False,
        "TIME_SEGMENT_NONEVAL_REMOVED",
    )
    _require(tsd.get("generic_walk_forward_v1_bound") is False, "WALK_FORWARD_BOUND")
    _require(
        tsd.get("illustrative_60_20_20_partition_is_not_authority") is True,
        "PARTITION_60_20_20_AS_AUTHORITY",
    )
    _require(
        tsd.get("segment_ids")
        == [
            "TIME_SEGMENT_Q1",
            "TIME_SEGMENT_Q2",
            "TIME_SEGMENT_Q3",
            "TIME_SEGMENT_Q4",
        ],
        "TIME_SEGMENT_IDS",
    )

    grid = (payload.get("parameter_governance") or {}).get("development_only_bounded_grid") or {}
    _require(grid.get("authorized") is True, "GRID_NOT_AUTHORIZED")
    _require(
        grid.get("holdout_forbidden_for_grid_selection") is True,
        "GRID_HOLDOUT_NOT_FORBIDDEN",
    )
    _require(
        grid.get("lookback_N_candidates") == [10, 20, 48],
        "LOOKBACK_GRID_MISMATCH",
    )
    _require(
        grid.get("rebalance_interval_bars_candidates") == [1, 4, 24],
        "REBALANCE_GRID_MISMATCH",
    )

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
        "contract_digest": digest,
        "definition_only": True,
        "evaluation_authorized": False,
        "holdout_authorized": False,
        "development_run_count": 0,
        "runner_start_count": 0,
        "pending_threshold_keys": [],
        "evaluation_blocked_while_pending": False,
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
