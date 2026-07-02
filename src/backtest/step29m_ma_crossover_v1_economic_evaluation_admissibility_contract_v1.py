"""
STEP 29M ma_crossover v1 economic evaluation admissibility contract v1.

Read-only contract diagnostics for operator-ratified fixed-config policy,
parameter binding, sizing invariants, signal-binding provenance, and staged
config readiness. No economic evaluation execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
    verify_cost_binding_v1,
)
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

CONTRACT_LAYER_VERSION = "v1"
CONTRACT_OWNER = "backtest.step29m_ma_crossover_v1_economic_evaluation_admissibility_contract_v1"

MA_CROSSOVER_V1_STRATEGY_ID = "ma_crossover"
MA_CROSSOVER_V1_STRATEGY_VERSION = "v1"
MA_CROSSOVER_V1_STRATEGY_OWNER = "src.strategies.ma_crossover.MACrossoverStrategy"
MA_CROSSOVER_V1_CANONICAL_PARAMS = {
    "fast_window": 20,
    "slow_window": 50,
    "price_col": "close",
}

FAST_WINDOW_MIN = 2
SLOW_WINDOW_MIN = 3
WINDOW_MAX = 500
ALLOWED_PRICE_COLS = frozenset({"open", "high", "low", "close"})
ALLOWED_MA_CROSSOVER_SIGNAL_VALUES = frozenset({0, 1})

OPERATOR_RATIFIED_RISK_PER_TRADE = 0.005
OPERATOR_RATIFIED_STOP_PCT = 0.025
OPERATOR_RATIFIED_MAX_POSITION_PCT = 0.25
OFFLINE_BOUND_OVERSIZE_POLICY = "REJECT_OVERSIZE"
POLICY_INVARIANT = "risk_per_trade <= max_position_pct * stop_pct"
POLICY_INVARIANT_RESULT = "0.005 <= 0.25 * 0.025 = 0.00625"
OPERATOR_POLICY_DERIVATION_REF = "operator_policy_decision:STEP29M_MA_CROSSOVER_V1"
FLEET_SIZING_PRECEDENT_REF = "fleet_precedent:macd_v3_post_risk_limits_rewire"

DEFAULT_EVALUATION_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_ma_crossover_v1_economic_evaluation_v1.json"
)
CONFIG_SCHEMA_VERSION = "step29m_ma_crossover_v1_economic_evaluation_admissibility_v1"

STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1: tuple[str, ...] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_breakout_donchian_v1_economic_evaluation_v1.json",
    DEFAULT_EVALUATION_CONFIG_PATH,
)

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

RATIFICATION_SLICE_SAFETY_FLAGS: dict[str, Any] = {
    "futures_only": True,
    "bitcoin_direction_allowed": False,
    "spot_allowed": False,
    "synthetic_spot_allowed": False,
    "fixed_config_required": True,
    "parameter_tuning_allowed": False,
    "dataset_change_allowed": False,
    "policy_threshold_change_allowed": False,
    "productive_runner_invocations_allowed": 0,
    "economic_evaluation_allowed": False,
    "promotion_allowed": False,
    "runtime_effect": False,
    "order_effect": False,
    "profitability_claim_allowed": False,
}


class AdmissibilityResult(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class MaCrossoverV1AdmissibilityContractResultV1:
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


def list_step29m_registered_economic_evaluation_configs_v1() -> tuple[str, ...]:
    return STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1


def load_ma_crossover_v1_evaluation_config_v1(
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


def verify_ma_crossover_v1_strategy_identity_v1() -> tuple[str, ...]:
    reasons: list[str] = []
    resolution = resolve_strategy_id(MA_CROSSOVER_V1_STRATEGY_ID)
    if resolution.canonical_strategy_id != MA_CROSSOVER_V1_STRATEGY_ID:
        reasons.append("strategy_id_not_canonical")
    entry = get_strategy_registry_entry(MA_CROSSOVER_V1_STRATEGY_ID)
    if entry.strategy_version != MA_CROSSOVER_V1_STRATEGY_VERSION:
        reasons.append("strategy_version_mismatch")
    if entry.implementation_ref != MA_CROSSOVER_V1_STRATEGY_OWNER:
        reasons.append("strategy_owner_mismatch")
    if not entry.futures_compatible:
        reasons.append("strategy_not_futures_compatible")
    if entry.spot_compatible:
        reasons.append("strategy_spot_compatible_true")
    lowered = entry.strategy_id.lower()
    if "btc" in lowered or "xbt" in lowered:
        reasons.append("strategy_btc_specialization")
    return tuple(reasons)


def _validate_window_v1(
    name: str,
    value: Any,
    *,
    minimum: int,
) -> tuple[Optional[int], tuple[str, ...]]:
    if value is None:
        return None, (f"{name}_missing",)
    if isinstance(value, bool) or not isinstance(value, int):
        return None, (f"{name}_not_integer",)
    if value < minimum or value > WINDOW_MAX:
        return None, (f"{name}_out_of_range",)
    return value, ()


def _validate_price_col_v1(value: Any) -> tuple[str, ...]:
    if not isinstance(value, str):
        return ("price_col_not_string",)
    if value not in ALLOWED_PRICE_COLS:
        return ("price_col_not_allowed",)
    return ()


def _window_params_for_binding_v1(configured: Mapping[str, Any]) -> dict[str, Any]:
    return {key: configured[key] for key in ("fast_window", "slow_window") if key in configured}


def verify_ma_crossover_v1_strategy_params_v1(
    configured: Mapping[str, Any],
    effective: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if set(configured.keys()) - set(MA_CROSSOVER_V1_CANONICAL_PARAMS):
        reasons.append("unknown_configured_strategy_param")
    expected_window_keys = {"fast_window", "slow_window"}
    if set(effective.keys()) != expected_window_keys:
        reasons.append("unknown_effective_strategy_param")
    if effective.get("fast_window") != MA_CROSSOVER_V1_CANONICAL_PARAMS["fast_window"]:
        reasons.append("fast_window_not_canonical")
    if effective.get("slow_window") != MA_CROSSOVER_V1_CANONICAL_PARAMS["slow_window"]:
        reasons.append("slow_window_not_canonical")

    _, fast_reasons = _validate_window_v1(
        "fast_window", effective.get("fast_window"), minimum=FAST_WINDOW_MIN
    )
    reasons.extend(fast_reasons)
    _, slow_reasons = _validate_window_v1(
        "slow_window", effective.get("slow_window"), minimum=SLOW_WINDOW_MIN
    )
    reasons.extend(slow_reasons)

    fast = effective.get("fast_window")
    slow = effective.get("slow_window")
    if isinstance(fast, int) and isinstance(slow, int) and fast >= slow:
        reasons.append("fast_window_not_lt_slow_window")

    if configured.get("price_col") != MA_CROSSOVER_V1_CANONICAL_PARAMS["price_col"]:
        reasons.append("price_col_not_canonical")
    reasons.extend(_validate_price_col_v1(configured.get("price_col")))
    return tuple(reasons)


def verify_ma_crossover_v1_sizing_policy_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
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
    if not isinstance(risk, (int, float)) or float(risk) <= 0:
        reasons.append("risk_per_trade_non_positive")
    if not isinstance(stop_pct, (int, float)) or float(stop_pct) <= 0:
        reasons.append("stop_pct_non_positive")
    if not isinstance(max_position_pct, (int, float)) or float(max_position_pct) <= 0:
        reasons.append("max_position_pct_non_positive")
    if isinstance(risk, (int, float)) and isinstance(stop_pct, (int, float)):
        if isinstance(max_position_pct, (int, float)):
            if float(risk) > float(max_position_pct) * float(stop_pct):
                reasons.append("policy_invariant_violation")
    if sizing.get("stop_pct_derivation_ref") != FLEET_SIZING_PRECEDENT_REF:
        reasons.append("stop_pct_derivation_ref_not_fleet_precedent")
    return tuple(reasons)


def verify_ma_crossover_v1_instrument_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
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
    return tuple(reasons)


def verify_ma_crossover_v1_ratification_authority_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    ratification = cfg.get("step29m_policy_ratification_v1")
    if not isinstance(ratification, Mapping):
        return ("step29m_policy_ratification_v1_missing",)

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

    if ratification.get("instrument_id") != "inst-eth-usdt-perp":
        reasons.append("ratification_instrument_id_mismatch")
    if ratification.get("strategy_id") != MA_CROSSOVER_V1_STRATEGY_ID:
        reasons.append("ratification_strategy_id_mismatch")
    if ratification.get("strategy_version") != MA_CROSSOVER_V1_STRATEGY_VERSION:
        reasons.append("ratification_strategy_version_mismatch")
    if ratification.get("venue_id") != "okx":
        reasons.append("ratification_venue_id_mismatch")
    if ratification.get("operator_policy_derivation_ref") != OPERATOR_POLICY_DERIVATION_REF:
        reasons.append("operator_policy_derivation_ref_mismatch")
    if ratification.get("sizing_precedent_ref") != FLEET_SIZING_PRECEDENT_REF:
        reasons.append("sizing_precedent_ref_mismatch")
    return tuple(reasons)


def verify_ma_crossover_v1_config_schema_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if cfg.get("config_schema_version") != CONFIG_SCHEMA_VERSION:
        reasons.append("config_schema_version_mismatch")

    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        return ("economic_evaluation_v1_missing",)
    if eval_section.get("strategy_id") != MA_CROSSOVER_V1_STRATEGY_ID:
        reasons.append("config_strategy_id_mismatch")
    if eval_section.get("strategy_version") != MA_CROSSOVER_V1_STRATEGY_VERSION:
        reasons.append("config_strategy_version_mismatch")
    if eval_section.get("engine_signal_source") != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        reasons.append("engine_signal_source_not_bound")
    if eval_section.get("economic_validity_policy_version") != "economic_validity_policy_v1":
        reasons.append("economic_validity_policy_version_mismatch")

    strategy_params = eval_section.get("strategy_params")
    if not isinstance(strategy_params, Mapping):
        reasons.append("strategy_params_missing")
    else:
        _, fast_reasons = _validate_window_v1(
            "fast_window",
            strategy_params.get("fast_window"),
            minimum=FAST_WINDOW_MIN,
        )
        reasons.extend(fast_reasons)
        _, slow_reasons = _validate_window_v1(
            "slow_window",
            strategy_params.get("slow_window"),
            minimum=SLOW_WINDOW_MIN,
        )
        reasons.extend(slow_reasons)
        fast = strategy_params.get("fast_window")
        slow = strategy_params.get("slow_window")
        if isinstance(fast, int) and isinstance(slow, int) and fast >= slow:
            reasons.append("fast_window_not_lt_slow_window")
        reasons.extend(_validate_price_col_v1(strategy_params.get("price_col")))
        if set(strategy_params.keys()) != set(MA_CROSSOVER_V1_CANONICAL_PARAMS):
            reasons.append("unknown_strategy_params_in_config")

    return tuple(reasons)


def verify_ma_crossover_v1_signal_binding_v1(cfg: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    configured = collect_configured_strategy_params_v1(cfg, MA_CROSSOVER_V1_STRATEGY_ID)
    try:
        effective, _ = resolve_effective_strategy_params_v1(
            MA_CROSSOVER_V1_STRATEGY_ID,
            _window_params_for_binding_v1(configured),
        )
        warmup = compute_required_warmup_rows_v1(MA_CROSSOVER_V1_STRATEGY_ID, effective)
        if warmup != int(effective["slow_window"]):
            reasons.append("warmup_not_equal_to_slow_window")
    except StrategySignalBindingError as exc:
        reasons.append(str(exc))
    return tuple(reasons)


def evaluate_ma_crossover_v1_admissibility_contract_v1(
    *,
    repo_root: Path,
    config_path: Optional[str] = None,
) -> MaCrossoverV1AdmissibilityContractResultV1:
    blocking: list[str] = []
    rel_path = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    cfg = load_ma_crossover_v1_evaluation_config_v1(repo_root, rel_path)
    config_digest = compute_evaluation_config_digest_v1(cfg)

    blocking.extend(verify_ma_crossover_v1_strategy_identity_v1())
    blocking.extend(verify_ma_crossover_v1_config_schema_v1(cfg))
    blocking.extend(verify_ma_crossover_v1_sizing_policy_v1(cfg))
    blocking.extend(verify_ma_crossover_v1_instrument_binding_v1(cfg))
    blocking.extend(verify_ma_crossover_v1_ratification_authority_v1(cfg))
    blocking.extend(verify_ma_crossover_v1_signal_binding_v1(cfg))

    cost_status, cost_reasons = verify_cost_binding_v1(cfg)
    blocking.extend(cost_reasons)

    configured = collect_configured_strategy_params_v1(cfg, MA_CROSSOVER_V1_STRATEGY_ID)
    try:
        effective, params_digest = resolve_effective_strategy_params_v1(
            MA_CROSSOVER_V1_STRATEGY_ID,
            _window_params_for_binding_v1(configured),
        )
    except StrategySignalBindingError as exc:
        blocking.append(str(exc))
        effective = {
            "fast_window": MA_CROSSOVER_V1_CANONICAL_PARAMS["fast_window"],
            "slow_window": MA_CROSSOVER_V1_CANONICAL_PARAMS["slow_window"],
        }
        params_digest = ""

    blocking.extend(verify_ma_crossover_v1_strategy_params_v1(configured, effective))

    admissibility = AdmissibilityResult.PASS if not blocking else AdmissibilityResult.BLOCKED
    return MaCrossoverV1AdmissibilityContractResultV1(
        admissibility_result=admissibility,
        blocking_reasons=tuple(sorted(set(blocking))),
        strategy_id=MA_CROSSOVER_V1_STRATEGY_ID,
        strategy_version=MA_CROSSOVER_V1_STRATEGY_VERSION,
        strategy_owner=MA_CROSSOVER_V1_STRATEGY_OWNER,
        configured_strategy_params=dict(configured),
        effective_strategy_params=dict(effective),
        strategy_params_digest=params_digest,
        evaluation_config_path=rel_path,
        config_digest=config_digest,
        config_schema_version=str(cfg.get("config_schema_version", "")),
        cost_binding_status=cost_status,
        policy_invariant_result=POLICY_INVARIANT_RESULT,
        signal_semantics="LONG_OR_FLAT_ONLY_0_1",
    )
