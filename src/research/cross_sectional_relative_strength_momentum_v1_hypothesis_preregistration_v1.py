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
PENDING_THRESHOLD_KEYS = frozenset(
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
        payload.get("development_evaluation_authorized") is False,
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
        admission.get("evaluation_blocked_while_any_threshold_pending") is True,
        "PENDING_NOT_BLOCKING",
    )
    pending = set(admission.get("pending_threshold_keys") or [])
    _require(pending == PENDING_THRESHOLD_KEYS, "PENDING_THRESHOLD_KEYS_MISMATCH")
    thresholds = admission.get("thresholds") or {}
    for key in PENDING_THRESHOLD_KEYS:
        row = thresholds.get(key) or {}
        _require(
            row.get("status") == "REQUIRED_BUT_THRESHOLD_PENDING_OPERATOR_GOVERNANCE",
            f"PENDING_STATUS:{key}",
        )
    for key, expected in (
        ("gross_profit_factor_min", 1.0),
        ("net_profit_factor_min", 1.3),
        ("maximum_max_drawdown", 0.25),
        ("minimum_trade_count", 50),
        ("min_eligible_members_for_rank", 5),
        ("single_trade_dominance_limit", 0.5),
        ("cost_stress_1_5x_net_profit_factor_min", 1.0),
    ):
        row = thresholds.get(key) or {}
        _require(row.get("status") == "CONFIGURED", f"THRESHOLD_NOT_CONFIGURED:{key}")
        _require(row.get("value") == expected, f"THRESHOLD_VALUE:{key}")

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
        "pending_threshold_keys": sorted(PENDING_THRESHOLD_KEYS),
        "evaluation_blocked_while_pending": True,
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
