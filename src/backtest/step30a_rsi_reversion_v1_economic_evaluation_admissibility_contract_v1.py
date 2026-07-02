"""
STEP 30A rsi_reversion v1 economic evaluation admissibility contract v1.

Read-only contract diagnostics for operator-ratified fixed-config policy,
parameter binding, split/holdout separation, and staged config readiness.
No economic evaluation execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

import pandas as pd

from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
    verify_cost_binding_v1,
)
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

CONTRACT_LAYER_VERSION = "v1"
CONTRACT_OWNER = "backtest.step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1"

RSI_REVERSION_V1_STRATEGY_ID = "rsi_reversion"
RSI_REVERSION_V1_STRATEGY_VERSION = "v1"
RSI_REVERSION_V1_STRATEGY_OWNER = "src.strategies.rsi_reversion.RsiReversionStrategy"
RSI_REVERSION_V1_CANONICAL_PARAMS = {
    "rsi_window": 14,
    "lower": 30.0,
    "upper": 70.0,
    "price_col": "close",
}
SIGNAL_SEMANTICS = "LONG_SHORT_REVERSION_-1_0_1"

RSI_WINDOW_MIN = 2
RSI_WINDOW_MAX = 100
ALLOWED_PRICE_COLS = frozenset({"open", "high", "low", "close"})

OPERATOR_RATIFIED_RISK_PER_TRADE = 0.005
OPERATOR_RATIFIED_STOP_PCT = 0.025
OPERATOR_RATIFIED_MAX_POSITION_PCT = 0.25
OFFLINE_BOUND_OVERSIZE_POLICY = "REJECT_OVERSIZE"
POLICY_INVARIANT = "risk_per_trade <= max_position_pct * stop_pct"
POLICY_INVARIANT_RESULT = "0.005 <= 0.25 * 0.025 = 0.00625"
OPERATOR_POLICY_DERIVATION_REF = "operator_policy_decision:STEP30A_RSI_REVERSION_V1"
FLEET_SIZING_PRECEDENT_REF = "fleet_precedent:macd_v3_post_risk_limits_rewire"

DEFAULT_EVALUATION_CONFIG_PATH = (
    "config/ops/step30a_okx_inst_eth_usdt_perp_rsi_reversion_v1_economic_evaluation_v1.json"
)
CONFIG_SCHEMA_VERSION = "step30a_rsi_reversion_v1_economic_evaluation_admissibility_v1"

STEP30A_HOLDOUT_START = "2026-06-17 10:07:00+00:00"
STEP30A_HOLDOUT_END = "2026-07-01 10:07:00+00:00"
STEP30A_HOLDOUT_PERIOD = f"{STEP30A_HOLDOUT_START}..{STEP30A_HOLDOUT_END}"

STEP30A_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1: tuple[str, ...] = (
    DEFAULT_EVALUATION_CONFIG_PATH,
)

STEP30A_DATASET_V2_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/inst-eth-usdt-perp/v2"
)
STEP30A_DATASET_V2_MANIFEST_PATH = STEP30A_DATASET_V2_ROOT / "dataset_manifest.json"
STEP30A_DATASET_V2_BARS_PATH = STEP30A_DATASET_V2_ROOT / "bars.parquet"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class AdmissibilityResult(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Step30aRsiReversionV1AdmissibilityContractResultV1:
    admissibility_result: AdmissibilityResult
    blocking_reasons: tuple[str, ...]
    strategy_id: str
    strategy_version: str
    strategy_owner: str
    configured_strategy_params: dict[str, Any]
    effective_strategy_params: dict[str, Any]
    strategy_params_digest: str
    evaluation_config_path: str
    config_digest: str
    config_schema_version: str
    cost_binding_status: str
    policy_invariant_result: str
    signal_semantics: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "admissibility_result": self.admissibility_result.value,
            "blocking_reasons": list(self.blocking_reasons),
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_owner": self.strategy_owner,
            "configured_strategy_params": self.configured_strategy_params,
            "effective_strategy_params": self.effective_strategy_params,
            "strategy_params_digest": self.strategy_params_digest,
            "evaluation_config_path": self.evaluation_config_path,
            "config_digest": self.config_digest,
            "config_schema_version": self.config_schema_version,
            "cost_binding_status": self.cost_binding_status,
            "policy_invariant_result": self.policy_invariant_result,
            "signal_semantics": self.signal_semantics,
        }


def list_step30a_registered_economic_evaluation_configs_v1() -> tuple[str, ...]:
    return STEP30A_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1


def load_step30a_rsi_reversion_v1_evaluation_config_v1(
    repo_root: Path,
    config_path: Optional[str] = None,
) -> dict[str, Any]:
    rel = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(f"evaluation_config_not_found:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evaluation_config_not_object")
    return payload


def verify_rsi_reversion_v1_strategy_identity_v1() -> tuple[str, ...]:
    reasons: list[str] = []
    resolution = resolve_strategy_id(RSI_REVERSION_V1_STRATEGY_ID)
    if resolution.canonical_strategy_id != RSI_REVERSION_V1_STRATEGY_ID:
        reasons.append("strategy_id_not_canonical")
    entry = get_strategy_registry_entry(RSI_REVERSION_V1_STRATEGY_ID)
    if entry.strategy_version != RSI_REVERSION_V1_STRATEGY_VERSION:
        reasons.append("strategy_version_mismatch")
    if entry.implementation_ref != RSI_REVERSION_V1_STRATEGY_OWNER:
        reasons.append("strategy_owner_mismatch")
    if not entry.futures_compatible:
        reasons.append("strategy_not_futures_compatible")
    if entry.spot_compatible:
        reasons.append("strategy_spot_compatible_true")
    lowered = entry.strategy_id.lower()
    if "btc" in lowered or "xbt" in lowered:
        reasons.append("strategy_btc_specialization")
    return tuple(reasons)


def _validate_rsi_window_v1(value: Any) -> tuple[Optional[int], tuple[str, ...]]:
    if value is None:
        return None, ("rsi_window_missing",)
    if isinstance(value, bool) or not isinstance(value, int):
        return None, ("rsi_window_not_integer",)
    if value < RSI_WINDOW_MIN or value > RSI_WINDOW_MAX:
        return None, ("rsi_window_out_of_range",)
    return value, ()


def _validate_bound_v1(name: str, value: Any) -> tuple[Optional[float], tuple[str, ...]]:
    if value is None:
        return None, (f"{name}_missing",)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, (f"{name}_not_numeric",)
    cast = float(value)
    if cast < 0.0 or cast > 100.0:
        return None, (f"{name}_out_of_range",)
    return cast, ()


def _validate_price_col_v1(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ("price_col_not_string",)
    if value not in ALLOWED_PRICE_COLS:
        return ("price_col_not_allowed",)
    return ()


def verify_rsi_reversion_v1_strategy_params_v1(
    configured: Mapping[str, Any],
    effective: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if set(configured.keys()) - set(RSI_REVERSION_V1_CANONICAL_PARAMS):
        reasons.append("unknown_configured_strategy_param")
    expected_effective_keys = {"rsi_window", "lower", "upper"}
    if set(effective.keys()) != expected_effective_keys:
        reasons.append("unknown_effective_strategy_param")
    if effective.get("rsi_window") != RSI_REVERSION_V1_CANONICAL_PARAMS["rsi_window"]:
        reasons.append("rsi_window_not_canonical")
    if float(effective.get("lower", -1.0)) != RSI_REVERSION_V1_CANONICAL_PARAMS["lower"]:
        reasons.append("lower_not_canonical")
    if float(effective.get("upper", -1.0)) != RSI_REVERSION_V1_CANONICAL_PARAMS["upper"]:
        reasons.append("upper_not_canonical")
    if configured.get("price_col") != RSI_REVERSION_V1_CANONICAL_PARAMS["price_col"]:
        reasons.append("price_col_not_canonical")

    _, rsi_reasons = _validate_rsi_window_v1(effective.get("rsi_window"))
    reasons.extend(rsi_reasons)
    lower, lower_reasons = _validate_bound_v1("lower", effective.get("lower"))
    upper, upper_reasons = _validate_bound_v1("upper", effective.get("upper"))
    reasons.extend(lower_reasons)
    reasons.extend(upper_reasons)
    if lower is not None and upper is not None and lower >= upper:
        reasons.append("lower_not_lt_upper")
    reasons.extend(_validate_price_col_v1(configured.get("price_col")))
    return tuple(reasons)


def verify_rsi_reversion_v1_sizing_policy_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    sizing = cfg.get("offline_evaluation_sizing_contract_v1")
    if not isinstance(sizing, Mapping):
        return ("offline_evaluation_sizing_contract_v1_missing",)

    risk = sizing.get("risk_per_trade")
    stop_pct = sizing.get("stop_pct")
    max_position_pct = sizing.get("max_position_pct")
    oversize_policy = sizing.get("oversize_policy")

    if risk != OPERATOR_RATIFIED_RISK_PER_TRADE:
        reasons.append("risk_per_trade_not_ratified")
    if stop_pct != OPERATOR_RATIFIED_STOP_PCT:
        reasons.append("stop_pct_not_ratified")
    if max_position_pct != OPERATOR_RATIFIED_MAX_POSITION_PCT:
        reasons.append("max_position_pct_not_ratified")
    if oversize_policy != OFFLINE_BOUND_OVERSIZE_POLICY:
        reasons.append("oversize_policy_not_reject")
    if sizing.get("stop_pct_derivation_ref") != FLEET_SIZING_PRECEDENT_REF:
        reasons.append("stop_pct_derivation_ref_not_fleet_precedent")
    if isinstance(risk, (int, float)) and isinstance(stop_pct, (int, float)):
        if isinstance(max_position_pct, (int, float)):
            if float(risk) > float(max_position_pct) * float(stop_pct):
                reasons.append("policy_invariant_violation")
    return tuple(reasons)


def verify_rsi_reversion_v1_instrument_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding, Mapping):
        return ("real_admissible_futures_evaluation_binding_v1_missing",)

    instrument_id = str(binding.get("canonical_instrument_id", ""))
    if instrument_id != "inst-eth-usdt-perp":
        reasons.append("instrument_id_mismatch")
    venue = str(binding.get("source_venue", ""))
    if venue != "OKX":
        reasons.append("source_venue_mismatch")
    native = str(binding.get("native_instrument_id", ""))
    lowered = f"{instrument_id} {native} {venue}".lower()
    for forbidden in _FORBIDDEN_INSTRUMENT_SUBSTRINGS:
        if forbidden in lowered:
            reasons.append(f"forbidden_instrument_binding:{forbidden}")
    if binding.get("dataset_version") != "v2":
        reasons.append("dataset_version_not_v2")
    if binding.get("dataset_schema_version") != "v2":
        reasons.append("dataset_schema_version_not_v2")
    return tuple(reasons)


def verify_step30a_policy_ratification_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    ratification = cfg.get("step30a_policy_ratification_v1")
    if not isinstance(ratification, Mapping):
        return ("step30a_policy_ratification_v1_missing",)

    expected_false = (
        "evaluation_authorized",
        "promotion_authorized",
        "runtime_authorized",
        "parameter_tuning_allowed",
        "threshold_tuning_allowed",
        "dataset_replacement_allowed",
    )
    for field in expected_false:
        if ratification.get(field) is not False:
            reasons.append(f"{field}_not_false")

    if ratification.get("strategy_id") != RSI_REVERSION_V1_STRATEGY_ID:
        reasons.append("ratification_strategy_id_mismatch")
    if ratification.get("strategy_version") != RSI_REVERSION_V1_STRATEGY_VERSION:
        reasons.append("ratification_strategy_version_mismatch")
    if ratification.get("operator_policy_derivation_ref") != OPERATOR_POLICY_DERIVATION_REF:
        reasons.append("operator_policy_derivation_ref_mismatch")
    if ratification.get("sizing_precedent_ref") != FLEET_SIZING_PRECEDENT_REF:
        reasons.append("sizing_precedent_ref_mismatch")
    return tuple(reasons)


def _parse_period_bounds_v1(period: str, field: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if ".." not in period:
        raise ValueError(f"{field}_period_format_invalid")
    left, right = period.split("..", 1)
    start = pd.Timestamp(left)
    end = pd.Timestamp(right)
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError(f"{field}_period_timezone_missing")
    return start, end


def verify_holdout_separation_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding, Mapping):
        return ("real_admissible_futures_evaluation_binding_v1_missing",)

    holdout_period = str(binding.get("out_of_sample_period", ""))
    if holdout_period != STEP30A_HOLDOUT_PERIOD:
        reasons.append("holdout_period_mismatch")

    try:
        train_start, train_end = _parse_period_bounds_v1(
            str(binding.get("training_period", "")),
            "training",
        )
        val_start, val_end = _parse_period_bounds_v1(
            str(binding.get("validation_period", "")),
            "validation",
        )
        holdout_start, holdout_end = _parse_period_bounds_v1(holdout_period, "holdout")
    except ValueError as exc:
        reasons.append(str(exc))
        return tuple(reasons)

    expected_holdout_start = pd.Timestamp(STEP30A_HOLDOUT_START)
    expected_holdout_end = pd.Timestamp(STEP30A_HOLDOUT_END)
    if holdout_start != expected_holdout_start:
        reasons.append("holdout_start_not_frozen")
    if holdout_end != expected_holdout_end:
        reasons.append("holdout_end_not_frozen")
    if train_end >= holdout_start:
        reasons.append("training_not_before_holdout")
    if val_end >= holdout_start:
        reasons.append("validation_not_before_holdout")
    if val_start <= train_start:
        reasons.append("validation_not_after_training_start")
    if val_start > val_end:
        reasons.append("validation_period_invalid")
    return tuple(reasons)


def assert_holdout_access_blocked_before_evaluation_v1(
    bars: pd.DataFrame,
    *,
    evaluation_authorized: bool,
) -> None:
    if evaluation_authorized:
        return
    holdout_start = pd.Timestamp(STEP30A_HOLDOUT_START)
    if (bars.index >= holdout_start).any():
        raise ValueError("holdout_access_blocked_before_evaluation")


def slice_development_partition_bars_v1(bars: pd.DataFrame) -> pd.DataFrame:
    holdout_start = pd.Timestamp(STEP30A_HOLDOUT_START)
    return bars.sort_index().loc[bars.index < holdout_start]


def verify_dataset_v2_digest_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    binding = cfg.get("real_admissible_futures_evaluation_binding_v1")
    if not isinstance(binding, Mapping):
        return ("real_admissible_futures_evaluation_binding_v1_missing",)
    if not STEP30A_DATASET_V2_MANIFEST_PATH.is_file():
        reasons.append("dataset_v2_manifest_missing")
        return tuple(reasons)
    manifest = json.loads(STEP30A_DATASET_V2_MANIFEST_PATH.read_text(encoding="utf-8"))
    expected_dataset_digest = str(binding.get("expected_dataset_digest", ""))
    expected_manifest_digest = str(binding.get("expected_manifest_digest", ""))
    actual_dataset_digest = str(manifest.get("normalized_dataset_digest", ""))
    actual_manifest_digest = str(manifest.get("manifest_digest", ""))
    if expected_dataset_digest.startswith("PLACEHOLDER"):
        reasons.append("expected_dataset_digest_not_frozen")
    elif expected_dataset_digest != actual_dataset_digest:
        reasons.append("expected_dataset_digest_mismatch")
    if expected_manifest_digest.startswith("PLACEHOLDER"):
        reasons.append("expected_manifest_digest_not_frozen")
    elif expected_manifest_digest != actual_manifest_digest:
        reasons.append("expected_manifest_digest_mismatch")
    return tuple(reasons)


def verify_rsi_reversion_v1_config_schema_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if cfg.get("config_schema_version") != CONFIG_SCHEMA_VERSION:
        reasons.append("config_schema_version_mismatch")

    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        return ("economic_evaluation_v1_missing",)
    if eval_section.get("strategy_id") != RSI_REVERSION_V1_STRATEGY_ID:
        reasons.append("config_strategy_id_mismatch")
    if eval_section.get("strategy_version") != RSI_REVERSION_V1_STRATEGY_VERSION:
        reasons.append("config_strategy_version_mismatch")
    if eval_section.get("engine_signal_source") != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        reasons.append("engine_signal_source_not_bound")
    if eval_section.get("economic_validity_policy_version") != "economic_validity_policy_v1":
        reasons.append("economic_validity_policy_version_mismatch")

    strategy_params = eval_section.get("strategy_params")
    if not isinstance(strategy_params, Mapping):
        reasons.append("strategy_params_missing")
    else:
        if "use_trend_filter" in strategy_params:
            reasons.append("forbidden_use_trend_filter_in_strategy_params")
        _, rsi_reasons = _validate_rsi_window_v1(strategy_params.get("rsi_window"))
        reasons.extend(rsi_reasons)
        lower, lower_reasons = _validate_bound_v1("lower", strategy_params.get("lower"))
        upper, upper_reasons = _validate_bound_v1("upper", strategy_params.get("upper"))
        reasons.extend(lower_reasons)
        reasons.extend(upper_reasons)
        if lower is not None and upper is not None and lower >= upper:
            reasons.append("lower_not_lt_upper")
        reasons.extend(_validate_price_col_v1(strategy_params.get("price_col")))
        if set(strategy_params.keys()) != set(RSI_REVERSION_V1_CANONICAL_PARAMS):
            reasons.append("unknown_strategy_params_in_config")
    return tuple(reasons)


def verify_rsi_reversion_v1_signal_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    configured = collect_configured_strategy_params_v1(cfg, RSI_REVERSION_V1_STRATEGY_ID)
    try:
        projected = project_strategy_params_for_binding_v1(RSI_REVERSION_V1_STRATEGY_ID, configured)
        effective, _ = resolve_effective_strategy_params_v1(
            RSI_REVERSION_V1_STRATEGY_ID,
            projected,
        )
        warmup = compute_required_warmup_rows_v1(RSI_REVERSION_V1_STRATEGY_ID, effective)
        if warmup != int(effective["rsi_window"]):
            reasons.append("warmup_not_equal_to_rsi_window")
    except StrategySignalBindingError as exc:
        reasons.append(str(exc))
    return tuple(reasons)


def evaluate_step30a_rsi_reversion_v1_admissibility_contract_v1(
    *,
    repo_root: Path,
    config_path: Optional[str] = None,
) -> Step30aRsiReversionV1AdmissibilityContractResultV1:
    blocking: list[str] = []
    rel_path = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    cfg = load_step30a_rsi_reversion_v1_evaluation_config_v1(repo_root, rel_path)
    config_digest = compute_evaluation_config_digest_v1(cfg)

    blocking.extend(verify_rsi_reversion_v1_strategy_identity_v1())
    blocking.extend(verify_rsi_reversion_v1_config_schema_v1(cfg))
    blocking.extend(verify_rsi_reversion_v1_sizing_policy_v1(cfg))
    blocking.extend(verify_rsi_reversion_v1_instrument_binding_v1(cfg))
    blocking.extend(verify_step30a_policy_ratification_v1(cfg))
    blocking.extend(verify_holdout_separation_v1(cfg))
    blocking.extend(verify_rsi_reversion_v1_signal_binding_v1(cfg))

    cost_status, cost_reasons = verify_cost_binding_v1(cfg)
    blocking.extend(cost_reasons)

    configured = collect_configured_strategy_params_v1(cfg, RSI_REVERSION_V1_STRATEGY_ID)
    try:
        effective, params_digest = resolve_effective_strategy_params_v1(
            RSI_REVERSION_V1_STRATEGY_ID,
            project_strategy_params_for_binding_v1(RSI_REVERSION_V1_STRATEGY_ID, configured),
        )
    except StrategySignalBindingError as exc:
        blocking.append(str(exc))
        effective = {
            "rsi_window": RSI_REVERSION_V1_CANONICAL_PARAMS["rsi_window"],
            "lower": RSI_REVERSION_V1_CANONICAL_PARAMS["lower"],
            "upper": RSI_REVERSION_V1_CANONICAL_PARAMS["upper"],
        }
        params_digest = ""

    blocking.extend(verify_rsi_reversion_v1_strategy_params_v1(configured, effective))
    admissibility = AdmissibilityResult.PASS if not blocking else AdmissibilityResult.BLOCKED
    return Step30aRsiReversionV1AdmissibilityContractResultV1(
        admissibility_result=admissibility,
        blocking_reasons=tuple(sorted(set(blocking))),
        strategy_id=RSI_REVERSION_V1_STRATEGY_ID,
        strategy_version=RSI_REVERSION_V1_STRATEGY_VERSION,
        strategy_owner=RSI_REVERSION_V1_STRATEGY_OWNER,
        configured_strategy_params=dict(configured),
        effective_strategy_params=dict(effective),
        strategy_params_digest=params_digest,
        evaluation_config_path=rel_path,
        config_digest=config_digest,
        config_schema_version=str(cfg.get("config_schema_version", "")),
        cost_binding_status=cost_status,
        policy_invariant_result=POLICY_INVARIANT_RESULT,
        signal_semantics=SIGNAL_SEMANTICS,
    )
