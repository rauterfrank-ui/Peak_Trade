"""
Offline evaluation sizing contract v1 (RUNBOOK STEP 29M).

Fail-closed explicit binding for offline economic evaluation position sizing.
Does not change global ``calc_position_size`` reject semantics; offline CAP
semantics apply only when ``oversize_policy=CAP_TO_MAX_POSITION_PCT`` and the
contract is bound on the evaluation config.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, MutableMapping, Optional

from src.risk.position_sizer import PositionRequest, PositionResult, calc_position_size

SIZING_CONTRACT_VERSION = "offline_evaluation_sizing_contract_v1"
CONTRACT_OWNER = "backtest.offline_evaluation_sizing_contract_v1"

ACCOUNTING_KEY = "_offline_sizing_accounting_v1"

MACD_V1_CANONICAL_STOP_PCT = 0.025
MACD_V1_CANONICAL_STOP_DERIVATION = "config.toml:[strategy.macd].stop_pct"

ALLOWED_OVERSIZE_POLICIES = frozenset({"REJECT_OVERSIZE", "CAP_TO_MAX_POSITION_PCT"})
ALLOWED_STOP_DISTANCE_POLICIES = frozenset({"FIXED_PCT_FROM_ENTRY_v1"})
ALLOWED_QUANTITY_ROUNDING_POLICIES = frozenset({"NONE_v1"})
ALLOWED_MINIMUM_QUANTITY_POLICIES = frozenset({"REJECT_BELOW_MIN_NOTIONAL_v1"})
ALLOWED_MINIMUM_NOTIONAL_POLICIES = frozenset({"USE_RISK_MIN_POSITION_VALUE_v1"})
ALLOWED_INSTRUMENT_METADATA_SOURCES = frozenset({"versioned_dataset_manifest_v1"})
ALLOWED_PRICE_SOURCES = frozenset({"bar_close_v1"})
ALLOWED_SIZING_MODES = frozenset({"fixed_fractional_risk_per_trade_v1"})

KNOWN_CONTRACT_FIELDS = frozenset(
    {
        "sizing_contract_version",
        "initial_equity",
        "risk_per_trade",
        "stop_distance_policy",
        "stop_pct",
        "max_position_pct",
        "oversize_policy",
        "quantity_rounding_policy",
        "minimum_quantity_policy",
        "minimum_notional_policy",
        "instrument_metadata_source",
        "price_source",
        "sizing_owner",
        "sizing_mode",
        "config_digest",
        "strategy_params_digest",
        "dataset_digest",
        "stop_pct_derivation_ref",
    }
)


class OfflineEvaluationSizingError(ValueError):
    """Fail-closed offline sizing contract error."""


class SizingReasonCode(str, Enum):
    MISSING_STOP_DISTANCE_POLICY = "MISSING_STOP_DISTANCE_POLICY"
    MISSING_STOP_PCT = "MISSING_STOP_PCT"
    MISSING_OVERSIZE_POLICY = "MISSING_OVERSIZE_POLICY"
    REQUESTED_NOTIONAL_EXCEEDS_MAX_POSITION = "REQUESTED_NOTIONAL_EXCEEDS_MAX_POSITION"
    POSITION_CAPPED_TO_MAX_POSITION = "POSITION_CAPPED_TO_MAX_POSITION"
    POSITION_SIZE_ZERO_AFTER_ROUNDING = "POSITION_SIZE_ZERO_AFTER_ROUNDING"
    MINIMUM_NOTIONAL_NOT_MET = "MINIMUM_NOTIONAL_NOT_MET"
    OK = "OK"


class OfflineSizingFeasibilityReasonCode(str, Enum):
    OK = "OK"
    TOTAL_ENTRY_REJECTION_CONFIG_INVARIANT = "TOTAL_ENTRY_REJECTION_CONFIG_INVARIANT"


@dataclass(frozen=True)
class OfflineEvaluationSizingContractV1:
    sizing_contract_version: str
    initial_equity: float
    risk_per_trade: float
    stop_distance_policy: str
    stop_pct: float
    max_position_pct: float
    oversize_policy: str
    quantity_rounding_policy: str
    minimum_quantity_policy: str
    minimum_notional_policy: str
    instrument_metadata_source: str
    price_source: str
    sizing_owner: str
    sizing_mode: str
    config_digest: str
    strategy_params_digest: str
    dataset_digest: str
    stop_pct_derivation_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "sizing_contract_version": self.sizing_contract_version,
            "initial_equity": self.initial_equity,
            "risk_per_trade": self.risk_per_trade,
            "stop_distance_policy": self.stop_distance_policy,
            "stop_pct": self.stop_pct,
            "max_position_pct": self.max_position_pct,
            "oversize_policy": self.oversize_policy,
            "quantity_rounding_policy": self.quantity_rounding_policy,
            "minimum_quantity_policy": self.minimum_quantity_policy,
            "minimum_notional_policy": self.minimum_notional_policy,
            "instrument_metadata_source": self.instrument_metadata_source,
            "price_source": self.price_source,
            "sizing_owner": self.sizing_owner,
            "sizing_mode": self.sizing_mode,
            "config_digest": self.config_digest,
            "strategy_params_digest": self.strategy_params_digest,
            "dataset_digest": self.dataset_digest,
        }
        if self.stop_pct_derivation_ref:
            payload["stop_pct_derivation_ref"] = self.stop_pct_derivation_ref
        return payload


@dataclass(frozen=True)
class OfflineEvaluationSizingFeasibilityResultV1:
    schema_valid: bool
    entry_feasible: bool
    executable_for_economic_evaluation: bool
    reason_code: OfflineSizingFeasibilityReasonCode
    requested_notional_pct: float
    max_position_pct: float
    oversize_policy: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_valid": self.schema_valid,
            "entry_feasible": self.entry_feasible,
            "executable_for_economic_evaluation": self.executable_for_economic_evaluation,
            "reason_code": self.reason_code.value,
            "requested_notional_pct": self.requested_notional_pct,
            "max_position_pct": self.max_position_pct,
            "oversize_policy": self.oversize_policy,
            "detail": self.detail,
        }


@dataclass
class OfflineEntrySizingOutcomeV1:
    accepted: bool
    size: float
    requested_notional: float
    effective_notional: float
    stop_price: float
    reason_code: SizingReasonCode
    detail: str = ""
    capped: bool = False


@dataclass
class OfflineSizingAccountingV1:
    entry_candidate_count: int = 0
    entry_sizing_pass_count: int = 0
    entry_sizing_reject_count: int = 0
    entry_sizing_cap_count: int = 0
    quantity_nonzero_count: int = 0
    quantity_zero_count: int = 0
    requested_notionals: list[float] = field(default_factory=list)
    effective_notionals: list[float] = field(default_factory=list)
    rejection_reason_counts: dict[str, int] = field(default_factory=dict)

    def record_candidate(self) -> None:
        self.entry_candidate_count += 1

    def record_outcome(self, outcome: OfflineEntrySizingOutcomeV1) -> None:
        self.requested_notionals.append(outcome.requested_notional)
        self.effective_notionals.append(outcome.effective_notional)
        if outcome.accepted and outcome.size > 0:
            self.entry_sizing_pass_count += 1
            self.quantity_nonzero_count += 1
            if outcome.capped:
                self.entry_sizing_cap_count += 1
        else:
            self.entry_sizing_reject_count += 1
            self.quantity_zero_count += 1
        if outcome.reason_code is not SizingReasonCode.OK:
            key = outcome.reason_code.value
            self.rejection_reason_counts[key] = self.rejection_reason_counts.get(key, 0) + 1

    def assert_accounting_identity(self) -> None:
        total = self.entry_sizing_pass_count + self.entry_sizing_reject_count
        if self.entry_candidate_count != total:
            raise OfflineEvaluationSizingError(
                f"entry_candidate_accounting_mismatch:{self.entry_candidate_count}!={total}"
            )


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_sizing_contract_digest_v1(contract: OfflineEvaluationSizingContractV1) -> str:
    body = contract.to_dict()
    body.pop("config_digest", None)
    return _stable_digest(body)


def offline_evaluation_sizing_contract_requested(cfg: Mapping[str, Any]) -> bool:
    section = cfg.get("offline_evaluation_sizing_contract_v1")
    return isinstance(section, Mapping) and bool(section)


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise OfflineEvaluationSizingError(f"{name}_invalid:{value}")


def _require_fraction(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise OfflineEvaluationSizingError(f"{name}_invalid:{value}")


def compute_requested_notional_pct_v1(contract: OfflineEvaluationSizingContractV1) -> float:
    """Equity-invariant requested notional fraction: risk_per_trade / stop_pct."""
    _require_fraction("risk_per_trade", contract.risk_per_trade)
    _require_fraction("stop_pct", contract.stop_pct)
    if contract.stop_pct <= 0.0:
        raise OfflineEvaluationSizingError("stop_pct_invalid_for_notional_pct")
    return contract.risk_per_trade / contract.stop_pct


def evaluate_offline_evaluation_sizing_entry_feasibility_v1(
    contract: OfflineEvaluationSizingContractV1,
) -> OfflineEvaluationSizingFeasibilityResultV1:
    """Deterministic pre-run entry feasibility for bound offline sizing contracts."""
    validate_offline_evaluation_sizing_contract_v1(contract)
    requested_notional_pct = compute_requested_notional_pct_v1(contract)
    max_position_pct = contract.max_position_pct

    if contract.oversize_policy == "REJECT_OVERSIZE":
        if requested_notional_pct > max_position_pct:
            return OfflineEvaluationSizingFeasibilityResultV1(
                schema_valid=True,
                entry_feasible=False,
                executable_for_economic_evaluation=False,
                reason_code=OfflineSizingFeasibilityReasonCode.TOTAL_ENTRY_REJECTION_CONFIG_INVARIANT,
                requested_notional_pct=requested_notional_pct,
                max_position_pct=max_position_pct,
                oversize_policy=contract.oversize_policy,
                detail=(
                    f"requested_notional_pct={requested_notional_pct:.6f}"
                    f">max_position_pct={max_position_pct:.6f}"
                ),
            )
    elif contract.oversize_policy != "CAP_TO_MAX_POSITION_PCT":
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_OVERSIZE_POLICY.value)

    return OfflineEvaluationSizingFeasibilityResultV1(
        schema_valid=True,
        entry_feasible=True,
        executable_for_economic_evaluation=True,
        reason_code=OfflineSizingFeasibilityReasonCode.OK,
        requested_notional_pct=requested_notional_pct,
        max_position_pct=max_position_pct,
        oversize_policy=contract.oversize_policy,
    )


def evaluate_offline_evaluation_sizing_entry_feasibility_from_cfg_v1(
    cfg: Mapping[str, Any],
) -> OfflineEvaluationSizingFeasibilityResultV1:
    contract = load_offline_evaluation_sizing_contract_v1(cfg)
    return evaluate_offline_evaluation_sizing_entry_feasibility_v1(contract)


def assert_offline_evaluation_sizing_executable_for_evaluation_v1(
    cfg: Mapping[str, Any],
) -> OfflineEvaluationSizingFeasibilityResultV1:
    if not offline_evaluation_sizing_contract_requested(cfg):
        raise OfflineEvaluationSizingError("offline_evaluation_sizing_contract_v1_missing")
    result = evaluate_offline_evaluation_sizing_entry_feasibility_from_cfg_v1(cfg)
    if not result.executable_for_economic_evaluation:
        raise OfflineEvaluationSizingError(result.reason_code.value)
    return result


def validate_offline_evaluation_sizing_contract_v1(
    contract: OfflineEvaluationSizingContractV1,
) -> None:
    if contract.sizing_contract_version != SIZING_CONTRACT_VERSION:
        raise OfflineEvaluationSizingError("sizing_contract_version_mismatch")
    if contract.sizing_owner != CONTRACT_OWNER:
        raise OfflineEvaluationSizingError("sizing_owner_mismatch")
    if contract.stop_distance_policy not in ALLOWED_STOP_DISTANCE_POLICIES:
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_STOP_DISTANCE_POLICY.value)
    if contract.oversize_policy not in ALLOWED_OVERSIZE_POLICIES:
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_OVERSIZE_POLICY.value)
    _require_positive("initial_equity", contract.initial_equity)
    _require_fraction("risk_per_trade", contract.risk_per_trade)
    _require_fraction("stop_pct", contract.stop_pct)
    _require_fraction("max_position_pct", contract.max_position_pct)
    if contract.quantity_rounding_policy not in ALLOWED_QUANTITY_ROUNDING_POLICIES:
        raise OfflineEvaluationSizingError("quantity_rounding_policy_invalid")
    if contract.minimum_quantity_policy not in ALLOWED_MINIMUM_QUANTITY_POLICIES:
        raise OfflineEvaluationSizingError("minimum_quantity_policy_invalid")
    if contract.minimum_notional_policy not in ALLOWED_MINIMUM_NOTIONAL_POLICIES:
        raise OfflineEvaluationSizingError("minimum_notional_policy_invalid")
    if contract.instrument_metadata_source not in ALLOWED_INSTRUMENT_METADATA_SOURCES:
        raise OfflineEvaluationSizingError("instrument_metadata_source_invalid")
    if contract.price_source not in ALLOWED_PRICE_SOURCES:
        raise OfflineEvaluationSizingError("price_source_invalid")
    if contract.sizing_mode not in ALLOWED_SIZING_MODES:
        raise OfflineEvaluationSizingError("sizing_mode_invalid")
    if not contract.strategy_params_digest.strip():
        raise OfflineEvaluationSizingError("strategy_params_digest_missing")
    if not contract.dataset_digest.strip():
        raise OfflineEvaluationSizingError("dataset_digest_missing")


def load_offline_evaluation_sizing_contract_v1(
    cfg: Mapping[str, Any],
    *,
    strategy_params_digest: str = "",
    dataset_digest: str = "",
) -> OfflineEvaluationSizingContractV1:
    raw = cfg.get("offline_evaluation_sizing_contract_v1")
    if not isinstance(raw, Mapping):
        raise OfflineEvaluationSizingError("offline_evaluation_sizing_contract_v1_missing")

    unknown = set(raw.keys()) - KNOWN_CONTRACT_FIELDS
    if unknown:
        raise OfflineEvaluationSizingError(f"unknown_sizing_fields:{sorted(unknown)}")

    version = str(raw.get("sizing_contract_version", "")).strip()
    if version != SIZING_CONTRACT_VERSION:
        raise OfflineEvaluationSizingError("sizing_contract_version_missing_or_unknown")

    stop_distance_policy = str(raw.get("stop_distance_policy", "")).strip()
    if not stop_distance_policy:
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_STOP_DISTANCE_POLICY.value)

    if raw.get("stop_pct") is None:
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_STOP_PCT.value)

    oversize_policy = str(raw.get("oversize_policy", "")).strip()
    if not oversize_policy:
        raise OfflineEvaluationSizingError(SizingReasonCode.MISSING_OVERSIZE_POLICY.value)

    risk_section = cfg.get("risk")
    if not isinstance(risk_section, Mapping):
        raise OfflineEvaluationSizingError("risk_section_missing")
    if raw.get("risk_per_trade") is None:
        raise OfflineEvaluationSizingError("risk_per_trade_missing")
    if raw.get("max_position_pct") is None:
        raise OfflineEvaluationSizingError("max_position_pct_missing")

    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        raise OfflineEvaluationSizingError("backtest_section_missing")
    if raw.get("initial_equity") is None:
        initial_equity = float(backtest.get("initial_cash", 0.0))
    else:
        initial_equity = float(raw["initial_equity"])

    contract = OfflineEvaluationSizingContractV1(
        sizing_contract_version=version,
        initial_equity=initial_equity,
        risk_per_trade=float(raw["risk_per_trade"]),
        stop_distance_policy=stop_distance_policy,
        stop_pct=float(raw["stop_pct"]),
        max_position_pct=float(raw["max_position_pct"]),
        oversize_policy=oversize_policy,
        quantity_rounding_policy=str(
            raw.get("quantity_rounding_policy", "NONE_v1"),
        ),
        minimum_quantity_policy=str(
            raw.get("minimum_quantity_policy", "REJECT_BELOW_MIN_NOTIONAL_v1"),
        ),
        minimum_notional_policy=str(
            raw.get("minimum_notional_policy", "USE_RISK_MIN_POSITION_VALUE_v1"),
        ),
        instrument_metadata_source=str(
            raw.get("instrument_metadata_source", "versioned_dataset_manifest_v1"),
        ),
        price_source=str(raw.get("price_source", "bar_close_v1")),
        sizing_owner=str(raw.get("sizing_owner", CONTRACT_OWNER)),
        sizing_mode=str(raw.get("sizing_mode", "fixed_fractional_risk_per_trade_v1")),
        config_digest=str(raw.get("config_digest", "")),
        strategy_params_digest=str(raw.get("strategy_params_digest", strategy_params_digest)),
        dataset_digest=str(raw.get("dataset_digest", dataset_digest)),
        stop_pct_derivation_ref=str(raw.get("stop_pct_derivation_ref", "")),
    )
    validate_offline_evaluation_sizing_contract_v1(contract)
    return contract


def resolve_min_position_value_v1(cfg: Mapping[str, Any]) -> float:
    risk_section = cfg.get("risk")
    if not isinstance(risk_section, Mapping):
        return 50.0
    return float(risk_section.get("min_position_value", 50.0))


def resolve_min_stop_distance_v1(cfg: Mapping[str, Any]) -> float:
    risk_section = cfg.get("risk")
    if not isinstance(risk_section, Mapping):
        return 0.005
    return float(risk_section.get("min_stop_distance", 0.005))


def size_offline_evaluation_entry_v1(
    *,
    contract: OfflineEvaluationSizingContractV1,
    equity: float,
    entry_price: float,
    cfg: Mapping[str, Any],
    accounting: Optional[OfflineSizingAccountingV1] = None,
) -> OfflineEntrySizingOutcomeV1:
    if accounting is not None:
        accounting.record_candidate()

    if contract.stop_distance_policy != "FIXED_PCT_FROM_ENTRY_v1":
        outcome = OfflineEntrySizingOutcomeV1(
            accepted=False,
            size=0.0,
            requested_notional=0.0,
            effective_notional=0.0,
            stop_price=0.0,
            reason_code=SizingReasonCode.MISSING_STOP_DISTANCE_POLICY,
            detail=contract.stop_distance_policy,
        )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    stop_pct = contract.stop_pct
    stop_price = entry_price * (1.0 - stop_pct)
    stop_distance = abs(entry_price - stop_price)
    stop_distance_pct = stop_distance / entry_price if entry_price > 0 else 0.0
    min_stop_distance = resolve_min_stop_distance_v1(cfg)
    if stop_distance_pct < min_stop_distance:
        outcome = OfflineEntrySizingOutcomeV1(
            accepted=False,
            size=0.0,
            requested_notional=0.0,
            effective_notional=0.0,
            stop_price=stop_price,
            reason_code=SizingReasonCode.MINIMUM_NOTIONAL_NOT_MET,
            detail=f"stop_distance_pct={stop_distance_pct:.6f}",
        )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    risk_amount = equity * contract.risk_per_trade
    requested_size = risk_amount / stop_distance if stop_distance > 0 else 0.0
    requested_notional = requested_size * entry_price
    max_notional = equity * contract.max_position_pct
    min_notional = resolve_min_position_value_v1(cfg)

    if contract.oversize_policy == "REJECT_OVERSIZE":
        req = PositionRequest(
            equity=equity,
            entry_price=entry_price,
            stop_price=stop_price,
            risk_per_trade=contract.risk_per_trade,
        )
        pos_result = calc_position_size(
            req,
            max_position_pct=contract.max_position_pct,
            min_position_value=min_notional,
            min_stop_distance=min_stop_distance,
        )
        if pos_result.rejected:
            reason = SizingReasonCode.REQUESTED_NOTIONAL_EXCEEDS_MAX_POSITION
            if pos_result.value < min_notional:
                reason = SizingReasonCode.MINIMUM_NOTIONAL_NOT_MET
            elif pos_result.size == 0 and "Stop-Distanz" in pos_result.reason:
                reason = SizingReasonCode.MINIMUM_NOTIONAL_NOT_MET
            outcome = OfflineEntrySizingOutcomeV1(
                accepted=False,
                size=0.0,
                requested_notional=requested_notional,
                effective_notional=0.0,
                stop_price=stop_price,
                reason_code=reason,
                detail=pos_result.reason,
            )
        else:
            outcome = OfflineEntrySizingOutcomeV1(
                accepted=True,
                size=pos_result.size,
                requested_notional=requested_notional,
                effective_notional=pos_result.value,
                stop_price=stop_price,
                reason_code=SizingReasonCode.OK,
            )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    if contract.oversize_policy != "CAP_TO_MAX_POSITION_PCT":
        outcome = OfflineEntrySizingOutcomeV1(
            accepted=False,
            size=0.0,
            requested_notional=requested_notional,
            effective_notional=0.0,
            stop_price=stop_price,
            reason_code=SizingReasonCode.MISSING_OVERSIZE_POLICY,
            detail=contract.oversize_policy,
        )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    effective_notional = min(requested_notional, max_notional)
    capped = requested_notional > max_notional
    if effective_notional < min_notional:
        outcome = OfflineEntrySizingOutcomeV1(
            accepted=False,
            size=0.0,
            requested_notional=requested_notional,
            effective_notional=0.0,
            stop_price=stop_price,
            reason_code=SizingReasonCode.MINIMUM_NOTIONAL_NOT_MET,
            detail=f"effective_notional={effective_notional:.2f}",
        )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    effective_size = effective_notional / entry_price if entry_price > 0 else 0.0
    if contract.quantity_rounding_policy == "NONE_v1":
        effective_size = float(effective_size)
    if effective_size <= 0.0:
        outcome = OfflineEntrySizingOutcomeV1(
            accepted=False,
            size=0.0,
            requested_notional=requested_notional,
            effective_notional=0.0,
            stop_price=stop_price,
            reason_code=SizingReasonCode.POSITION_SIZE_ZERO_AFTER_ROUNDING,
            capped=capped,
        )
        if accounting is not None:
            accounting.record_outcome(outcome)
        return outcome

    actual_notional = effective_size * entry_price
    if actual_notional > max_notional + 1e-9:
        raise OfflineEvaluationSizingError("rounding_increased_risk")

    reason = SizingReasonCode.OK if not capped else SizingReasonCode.POSITION_CAPPED_TO_MAX_POSITION
    outcome = OfflineEntrySizingOutcomeV1(
        accepted=True,
        size=effective_size,
        requested_notional=requested_notional,
        effective_notional=actual_notional,
        stop_price=stop_price,
        reason_code=reason,
        detail="capped_to_max_position" if capped else "ok",
        capped=capped,
    )
    if accounting is not None:
        accounting.record_outcome(outcome)
    return outcome


def bind_offline_evaluation_sizing_v1(
    cfg: MutableMapping[str, Any],
    *,
    strategy_params_digest: str,
    dataset_digest: str,
) -> tuple[OfflineEvaluationSizingContractV1, OfflineSizingAccountingV1]:
    contract = load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=strategy_params_digest,
        dataset_digest=dataset_digest,
    )
    expected_digest = compute_sizing_contract_digest_v1(contract)
    if contract.config_digest and contract.config_digest != expected_digest:
        raise OfflineEvaluationSizingError("sizing_config_digest_mismatch")
    accounting = OfflineSizingAccountingV1()
    cfg[ACCOUNTING_KEY] = accounting
    return contract, accounting


def get_offline_sizing_accounting_v1(cfg: Mapping[str, Any]) -> Optional[OfflineSizingAccountingV1]:
    accounting = cfg.get(ACCOUNTING_KEY)
    if isinstance(accounting, OfflineSizingAccountingV1):
        return accounting
    return None


def _summary_stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def serialize_sizing_provenance_v1(
    contract: OfflineEvaluationSizingContractV1,
    accounting: OfflineSizingAccountingV1,
) -> dict[str, Any]:
    accounting.assert_accounting_identity()
    return {
        "sizing_contract_version": contract.sizing_contract_version,
        "initial_equity": contract.initial_equity,
        "risk_per_trade": contract.risk_per_trade,
        "stop_distance_policy": contract.stop_distance_policy,
        "effective_stop_pct": contract.stop_pct,
        "max_position_pct": contract.max_position_pct,
        "oversize_policy": contract.oversize_policy,
        "requested_notional_summary": _summary_stats(accounting.requested_notionals),
        "effective_notional_summary": _summary_stats(accounting.effective_notionals),
        "entry_candidate_count": accounting.entry_candidate_count,
        "entry_sizing_pass_count": accounting.entry_sizing_pass_count,
        "entry_sizing_reject_count": accounting.entry_sizing_reject_count,
        "entry_sizing_cap_count": accounting.entry_sizing_cap_count,
        "sizing_rejection_reason_counts": dict(accounting.rejection_reason_counts),
        "quantity_nonzero_count": accounting.quantity_nonzero_count,
        "quantity_zero_count": accounting.quantity_zero_count,
        "sizing_config_digest": compute_sizing_contract_digest_v1(contract),
        "sizing_owner": contract.sizing_owner,
        "runtime_sizing_policy_unchanged": True,
        "stop_pct_derivation_ref": contract.stop_pct_derivation_ref,
        "strategy_params_digest": contract.strategy_params_digest,
        "dataset_digest": contract.dataset_digest,
    }


def offline_evaluation_sizing_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": SIZING_CONTRACT_VERSION,
        "owner": CONTRACT_OWNER,
        "allowed_oversize_policies": sorted(ALLOWED_OVERSIZE_POLICIES),
        "allowed_stop_distance_policies": sorted(ALLOWED_STOP_DISTANCE_POLICIES),
        "required_invariants": {
            "NO_IMPLICIT_STOP_PCT": True,
            "NO_IMPLICIT_RISK_PER_TRADE": True,
            "NO_IMPLICIT_MAX_POSITION_PCT": True,
            "NO_IMPLICIT_OVERSIZE_POLICY": True,
            "NO_ZERO_QUANTITY_SILENT_FALLBACK": True,
            "SIZING_PROVENANCE_REQUIRED": True,
            "ROUNDING_MUST_NOT_INCREASE_RISK": True,
            "OFFLINE_SIZING_MUST_NOT_CHANGE_RUNTIME_POLICY": True,
            "REJECT_OVERSIZE_REQUIRES_REQUESTED_NOTIONAL_PCT_LTE_MAX_POSITION_PCT": True,
        },
        "reason_codes": [code.value for code in SizingReasonCode],
        "feasibility_reason_codes": [code.value for code in OfflineSizingFeasibilityReasonCode],
        "requested_notional_pct_formula": "risk_per_trade/stop_pct",
    }
