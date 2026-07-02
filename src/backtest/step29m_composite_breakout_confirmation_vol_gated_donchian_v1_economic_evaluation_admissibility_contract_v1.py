"""
STEP 29M composite breakout confirmation vol-gated donchian v1 economic evaluation
admissibility contract v1.

Read-only contract diagnostics for operator-ratified confirmed-composite binding,
parameter invariants, sizing policy, dataset compatibility, and staged config
readiness. No economic evaluation execution.
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
    COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1,
    COMPOSITE_STRATEGY_ID,
    COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK,
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_composite_required_warmup_rows_v1,
    parse_composite_strategy_binding_v1,
)
from src.strategies.breakout_confirmation_v1 import CONFIRMATION_EPOCHS_V1
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

CONTRACT_LAYER_VERSION = "v1"
CONTRACT_OWNER = (
    "backtest.step29m_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "economic_evaluation_admissibility_contract_v1"
)

CANDIDATE_BINDING_ID = "composite_breakout_confirmation_vol_gated_donchian_v1"
COMPOSITE_V1_STRATEGY_ID = COMPOSITE_STRATEGY_ID
COMPOSITE_V1_STRATEGY_VERSION = "v1"
COMPOSITE_V1_STRATEGY_OWNER = "src.strategies.composite.CompositeStrategy"
COMPOSITE_V1_CANONICAL_PARAMS: dict[str, Any] = {
    "composite_type": COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1,
    "composition_rule": COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK,
    "signal_strategy_id": "breakout_donchian",
    "filter_strategy_id": "vol_regime_filter",
    "signal_strategy_params": {
        "lookback": 20,
        "price_col": "close",
    },
    "filter_strategy_params": {
        "vol_window": 20,
        "vol_method": "atr",
        "vol_percentile_low": 25,
        "vol_percentile_high": 75,
        "min_bars": 30,
        "lookback_percentile": 100,
        "regime_mode": False,
    },
    "aggregation": "weighted",
    "signal_threshold": 0.3,
    "confirmation_epochs": CONFIRMATION_EPOCHS_V1,
}

OPERATOR_RATIFIED_RISK_PER_TRADE = 0.005
OPERATOR_RATIFIED_STOP_PCT = 0.02
OPERATOR_RATIFIED_MAX_POSITION_PCT = 0.25
OFFLINE_BOUND_OVERSIZE_POLICY = "REJECT_OVERSIZE"
POLICY_INVARIANT = "risk_per_trade <= max_position_pct * stop_pct"
POLICY_INVARIANT_RESULT = "0.005 <= 0.25 * 0.02 = 0.005"
OPERATOR_POLICY_DERIVATION_REF = (
    "operator_policy_decision:COMPOSITE_BREAKOUT_CONFIRMATION_VOL_GATED_DONCHIAN_V1"
)

DEFAULT_EVALUATION_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_composite_breakout_confirmation_"
    "vol_gated_donchian_v1_economic_evaluation_v1.json"
)
CONFIG_SCHEMA_VERSION = (
    "step29m_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "economic_evaluation_admissibility_v1"
)

ARCHITECTURE_BINDING_MERGE_COMMIT = "5eb28206fb49062049c89f43d77da2899f22c93d"
ECONOMIC_EVALUATION_MERGE_COMMIT = "ec0842428b8420fb4d8193d69c307809bcabee75"
ARCHITECTURE_BINDING_CONFIG_PATH = (
    "config/ops/composite_breakout_confirmation_vol_gated_donchian_v1_architecture_binding_v1.json"
)

ARCHITECTURE_HYPOTHESIS_FALSIFIED = True
ARCHITECTURE_REJECTED = True
RESEARCH_LINE_STATUS = "CLOSED_REJECTED"
ECONOMIC_VALIDITY_STATUS = "FAILED"
ECONOMIC_EVALUATION_VERDICT = "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL"
FAILURE_DECOMPOSITION_VERDICT = "ECONOMIC_VALIDITY_FAILURE_DECOMPOSITION_COMPLETE"
ARCHITECTURE_DISPOSITION = "ARCHITECTURE_HYPOTHESIS_FALSIFIED"
FINAL_RESEARCH_DISPOSITION = "REJECTED_CLOSED"
REJECTION_REASON = "STRUCTURALLY_NEGATIVE_NET_EDGE_ACROSS_WALK_FORWARD_MONTE_CARLO_AND_STRESS"

PROMOTION_ELIGIBLE = False
SHADOW_ELIGIBLE = False
PAPER_ELIGIBLE = False
TESTNET_ELIGIBLE = False
RUNTIME_ELIGIBLE = False
RETRY_ALLOWED = False
HOLDOUT_ALLOWED = False
PARAMETER_TUNING_ALLOWED = False
THRESHOLD_RELAXATION_ALLOWED = False
DATASET_SUBSTITUTION_ALLOWED = False
PERIOD_SUBSTITUTION_ALLOWED = False

ARCHITECTURE_RATIFICATION_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "architecture_ratification_and_binding_v0_20260702T183549Z"
)
OFFLINE_EVALUATION_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "offline_economic_validity_evaluation_v0_20260702T185926Z"
)
ECONOMIC_EVALUATION_MERGE_CLOSEOUT_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "economic_evaluation_pr_squash_merge_and_post_merge_closeout_v0_20260702T191014Z"
)
FAILURE_DECOMPOSITION_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "analysis/bounded_composite_breakout_confirmation_vol_gated_donchian_v1_"
    "economic_validity_failure_decomposition_and_research_disposition_read_only_v0_"
    "20260702T211530Z"
)

STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1: tuple[str, ...] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v2.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_macd_v1_economic_evaluation_v3.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_breakout_donchian_v1_economic_evaluation_v1.json",
    "config/ops/step29m_okx_inst_eth_usdt_perp_ma_crossover_v1_economic_evaluation_v1.json",
    DEFAULT_EVALUATION_CONFIG_PATH,
)

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})


class AdmissibilityResult(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CompositeBreakoutConfirmationVolGatedDonchianV1AdmissibilityContractResultV1:
    admissibility_result: AdmissibilityResult
    blocking_reasons: tuple[str, ...]
    candidate_binding_id: str
    strategy_id: str
    strategy_version: str
    strategy_owner: str
    configured_strategy_params: dict[str, Any]
    binding_semantic_digest: str
    evaluation_config_path: str
    config_digest: str
    config_schema_version: str
    cost_binding_status: str
    policy_invariant_result: str
    required_warmup_rows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "admissibility_result": self.admissibility_result.value,
            "blocking_reasons": list(self.blocking_reasons),
            "candidate_binding_id": self.candidate_binding_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_owner": self.strategy_owner,
            "configured_strategy_params": self.configured_strategy_params,
            "binding_semantic_digest": self.binding_semantic_digest,
            "evaluation_config_path": self.evaluation_config_path,
            "config_digest": self.config_digest,
            "config_schema_version": self.config_schema_version,
            "cost_binding_status": self.cost_binding_status,
            "policy_invariant_result": self.policy_invariant_result,
            "required_warmup_rows": self.required_warmup_rows,
        }


def list_step29m_registered_economic_evaluation_configs_v1() -> tuple[str, ...]:
    return STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS_V1


def load_composite_breakout_confirmation_vol_gated_donchian_v1_evaluation_config_v1(
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


def verify_composite_breakout_confirmation_vol_gated_donchian_v1_strategy_identity_v1() -> tuple[
    str, ...
]:
    reasons: list[str] = []
    resolution = resolve_strategy_id(COMPOSITE_V1_STRATEGY_ID)
    if resolution.canonical_strategy_id != COMPOSITE_V1_STRATEGY_ID:
        reasons.append("strategy_id_not_canonical")
    entry = get_strategy_registry_entry(COMPOSITE_V1_STRATEGY_ID)
    if entry.strategy_version != COMPOSITE_V1_STRATEGY_VERSION:
        reasons.append("strategy_version_mismatch")
    if entry.implementation_ref != COMPOSITE_V1_STRATEGY_OWNER:
        reasons.append("strategy_owner_mismatch")
    if not entry.futures_compatible:
        reasons.append("strategy_not_futures_compatible")
    if entry.spot_compatible:
        reasons.append("strategy_spot_compatible_true")
    lowered = entry.strategy_id.lower()
    if "btc" in lowered or "xbt" in lowered:
        reasons.append("strategy_btc_specialization")
    return tuple(reasons)


def verify_composite_breakout_confirmation_vol_gated_donchian_v1_candidate_binding_v1(
    cfg: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if cfg.get("candidate_binding_id") != CANDIDATE_BINDING_ID:
        reasons.append("candidate_binding_id_mismatch")
    return tuple(reasons)


def verify_composite_breakout_confirmation_vol_gated_donchian_v1_config_schema_v1(
    cfg: Mapping[str, Any],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if cfg.get("config_schema_version") != CONFIG_SCHEMA_VERSION:
        reasons.append("config_schema_version_mismatch")

    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        return ("economic_evaluation_v1_missing",)
    if eval_section.get("strategy_id") != COMPOSITE_V1_STRATEGY_ID:
        reasons.append("config_strategy_id_mismatch")
    if eval_section.get("strategy_version") != COMPOSITE_V1_STRATEGY_VERSION:
        reasons.append("config_strategy_version_mismatch")
    if eval_section.get("engine_signal_source") != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY:
        reasons.append("engine_signal_source_not_bound")

    for required_section in ("walk_forward", "monte_carlo", "stress"):
        section = eval_section.get(required_section)
        if not isinstance(section, Mapping) or not section.get("bind"):
            reasons.append(f"{required_section}_not_bound")

    strategy_params = eval_section.get("strategy_params")
    if not isinstance(strategy_params, Mapping):
        reasons.append("strategy_params_missing")
    else:
        try:
            binding = parse_composite_strategy_binding_v1(strategy_params)
            canonical_binding = parse_composite_strategy_binding_v1(COMPOSITE_V1_CANONICAL_PARAMS)
            if binding.binding_semantic_digest != canonical_binding.binding_semantic_digest:
                reasons.append("strategy_params_not_canonical")
        except StrategySignalBindingError as exc:
            reasons.append(str(exc))

    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        reasons.append("backtest_section_missing")
    else:
        param_sensitivity = backtest.get("parameter_sensitivity")
        if not isinstance(param_sensitivity, Mapping) or not param_sensitivity.get("bind"):
            reasons.append("parameter_sensitivity_not_bound")

    return tuple(reasons)


def verify_composite_breakout_confirmation_vol_gated_donchian_v1_sizing_policy_v1(
    cfg: Mapping[str, Any],
) -> tuple[str, ...]:
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
    if sizing.get("stop_pct_derivation_ref") != OPERATOR_POLICY_DERIVATION_REF:
        reasons.append("stop_pct_derivation_ref_not_operator_policy")
    return tuple(reasons)


def verify_composite_breakout_confirmation_vol_gated_donchian_v1_instrument_binding_v1(
    cfg: Mapping[str, Any],
) -> tuple[str, ...]:
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


def evaluate_composite_breakout_confirmation_vol_gated_donchian_v1_admissibility_contract_v1(
    *,
    repo_root: Path,
    config_path: Optional[str] = None,
) -> CompositeBreakoutConfirmationVolGatedDonchianV1AdmissibilityContractResultV1:
    blocking: list[str] = []
    rel_path = config_path or DEFAULT_EVALUATION_CONFIG_PATH
    cfg = load_composite_breakout_confirmation_vol_gated_donchian_v1_evaluation_config_v1(
        repo_root,
        rel_path,
    )
    config_digest = compute_evaluation_config_digest_v1(cfg)

    blocking.extend(
        verify_composite_breakout_confirmation_vol_gated_donchian_v1_strategy_identity_v1()
    )
    blocking.extend(
        verify_composite_breakout_confirmation_vol_gated_donchian_v1_candidate_binding_v1(cfg)
    )
    blocking.extend(
        verify_composite_breakout_confirmation_vol_gated_donchian_v1_config_schema_v1(cfg)
    )
    blocking.extend(
        verify_composite_breakout_confirmation_vol_gated_donchian_v1_sizing_policy_v1(cfg)
    )
    blocking.extend(
        verify_composite_breakout_confirmation_vol_gated_donchian_v1_instrument_binding_v1(cfg)
    )

    cost_status, cost_reasons = verify_cost_binding_v1(cfg)
    blocking.extend(cost_reasons)

    configured = collect_configured_strategy_params_v1(cfg, COMPOSITE_V1_STRATEGY_ID)
    binding_semantic_digest = ""
    required_warmup_rows = 0
    try:
        binding = parse_composite_strategy_binding_v1(configured)
        binding_semantic_digest = binding.binding_semantic_digest
        required_warmup_rows = compute_composite_required_warmup_rows_v1(configured)
        canonical_binding = parse_composite_strategy_binding_v1(COMPOSITE_V1_CANONICAL_PARAMS)
        if binding.binding_semantic_digest != canonical_binding.binding_semantic_digest:
            blocking.append("binding_semantic_digest_not_canonical")
    except StrategySignalBindingError as exc:
        blocking.append(str(exc))

    admissibility = AdmissibilityResult.PASS if not blocking else AdmissibilityResult.BLOCKED
    return CompositeBreakoutConfirmationVolGatedDonchianV1AdmissibilityContractResultV1(
        admissibility_result=admissibility,
        blocking_reasons=tuple(sorted(set(blocking))),
        candidate_binding_id=CANDIDATE_BINDING_ID,
        strategy_id=COMPOSITE_V1_STRATEGY_ID,
        strategy_version=COMPOSITE_V1_STRATEGY_VERSION,
        strategy_owner=COMPOSITE_V1_STRATEGY_OWNER,
        configured_strategy_params=dict(configured),
        binding_semantic_digest=binding_semantic_digest,
        evaluation_config_path=rel_path,
        config_digest=config_digest,
        config_schema_version=str(cfg.get("config_schema_version", "")),
        cost_binding_status=cost_status,
        policy_invariant_result=POLICY_INVARIANT_RESULT,
        required_warmup_rows=required_warmup_rows,
    )
