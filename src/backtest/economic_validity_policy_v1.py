"""
Versioned Economic Validity Policy v1 (RUNBOOK STEP 29M).

Fail-closed, non-authorizing policy contract for offline economic viability evidence.
Thresholds must be explicitly versioned; missing values block economic validity claims.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

ECONOMIC_VALIDITY_POLICY_VERSION = "economic_validity_policy_v1"
ECONOMIC_VALIDITY_POLICY_OWNER = "backtest.economic_validity_policy_v1"
POLICY_THRESHOLD_STATUS_BLOCKED = "BLOCKED_BY_MISSING_VERSIONED_VALUES"

_NUMERIC_THRESHOLD_FIELDS = (
    "minimum_net_expectancy",
    "minimum_profit_factor",
    "maximum_max_drawdown",
    "walk_forward_stability_threshold",
    "minimum_trade_count",
    "single_trade_dominance_limit",
    "regime_dominance_limit",
)

_POLICY_REF_FIELDS = (
    "out_of_sample_pass_policy",
    "parameter_robustness_policy",
    "monte_carlo_pass_policy",
    "stress_pass_policy",
)

_ALL_THRESHOLD_FIELDS = _NUMERIC_THRESHOLD_FIELDS + _POLICY_REF_FIELDS


class ThresholdBindingStatus(str, Enum):
    CONFIGURED = "CONFIGURED"
    REQUIRED_NOT_CONFIGURED = "REQUIRED_NOT_CONFIGURED"


class EconomicValidityPolicyError(ValueError):
    """Fail-closed economic validity policy error."""


@dataclass(frozen=True)
class VersionedThresholdV1:
    status: ThresholdBindingStatus
    value: Optional[float] = None
    policy_ref: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status.value}
        if self.value is not None:
            payload["value"] = self.value
        if self.policy_ref is not None:
            payload["policy_ref"] = self.policy_ref
        return payload


@dataclass(frozen=True)
class EconomicValidityPolicyV1:
    policy_version: str
    owner: str
    minimum_net_expectancy: VersionedThresholdV1
    minimum_profit_factor: VersionedThresholdV1
    maximum_max_drawdown: VersionedThresholdV1
    walk_forward_stability_threshold: VersionedThresholdV1
    out_of_sample_pass_policy: VersionedThresholdV1
    parameter_robustness_policy: VersionedThresholdV1
    monte_carlo_pass_policy: VersionedThresholdV1
    stress_pass_policy: VersionedThresholdV1
    minimum_trade_count: VersionedThresholdV1
    single_trade_dominance_limit: VersionedThresholdV1
    regime_dominance_limit: VersionedThresholdV1
    authority_effect: str = "NONE"
    runtime_effect: bool = False
    order_effect: bool = False
    promotion_effect: bool = False

    def is_version_bound(self) -> bool:
        return (
            self.policy_version == ECONOMIC_VALIDITY_POLICY_VERSION
            and self.owner == ECONOMIC_VALIDITY_POLICY_OWNER
        )

    def thresholds_configured(self) -> bool:
        for field_name in _ALL_THRESHOLD_FIELDS:
            threshold = getattr(self, field_name)
            if threshold.status is not ThresholdBindingStatus.CONFIGURED:
                return False
            if field_name in _NUMERIC_THRESHOLD_FIELDS and threshold.value is None:
                return False
            if field_name in _POLICY_REF_FIELDS and not threshold.policy_ref:
                return False
        return True

    def policy_threshold_status(self) -> str:
        if self.thresholds_configured():
            return "CONFIGURED"
        return POLICY_THRESHOLD_STATUS_BLOCKED

    def unconfigured_fields(self) -> tuple[str, ...]:
        missing: list[str] = []
        for field_name in _ALL_THRESHOLD_FIELDS:
            threshold = getattr(self, field_name)
            if threshold.status is not ThresholdBindingStatus.CONFIGURED:
                missing.append(field_name)
                continue
            if field_name in _NUMERIC_THRESHOLD_FIELDS and threshold.value is None:
                missing.append(field_name)
            elif field_name in _POLICY_REF_FIELDS and not threshold.policy_ref:
                missing.append(field_name)
        return tuple(missing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": self.policy_version,
            "owner": self.owner,
            "minimum_net_expectancy": self.minimum_net_expectancy.to_dict(),
            "minimum_profit_factor": self.minimum_profit_factor.to_dict(),
            "maximum_max_drawdown": self.maximum_max_drawdown.to_dict(),
            "walk_forward_stability_threshold": self.walk_forward_stability_threshold.to_dict(),
            "out_of_sample_pass_policy": self.out_of_sample_pass_policy.to_dict(),
            "parameter_robustness_policy": self.parameter_robustness_policy.to_dict(),
            "monte_carlo_pass_policy": self.monte_carlo_pass_policy.to_dict(),
            "stress_pass_policy": self.stress_pass_policy.to_dict(),
            "minimum_trade_count": self.minimum_trade_count.to_dict(),
            "single_trade_dominance_limit": self.single_trade_dominance_limit.to_dict(),
            "regime_dominance_limit": self.regime_dominance_limit.to_dict(),
            "policy_threshold_status": self.policy_threshold_status(),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "order_effect": self.order_effect,
            "promotion_effect": self.promotion_effect,
        }

    def config_digest(self) -> str:
        return compute_economic_validity_policy_digest(self)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_economic_validity_policy_digest(policy: EconomicValidityPolicyV1) -> str:
    payload = policy.to_dict()
    payload.pop("policy_threshold_status", None)
    return _stable_digest(payload)


def _required_not_configured() -> VersionedThresholdV1:
    return VersionedThresholdV1(status=ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED)


def default_economic_validity_policy_v1() -> EconomicValidityPolicyV1:
    """Canonical default policy with all thresholds explicitly not configured."""
    unset = _required_not_configured()
    return EconomicValidityPolicyV1(
        policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
        owner=ECONOMIC_VALIDITY_POLICY_OWNER,
        minimum_net_expectancy=unset,
        minimum_profit_factor=unset,
        maximum_max_drawdown=unset,
        walk_forward_stability_threshold=unset,
        out_of_sample_pass_policy=unset,
        parameter_robustness_policy=unset,
        monte_carlo_pass_policy=unset,
        stress_pass_policy=unset,
        minimum_trade_count=unset,
        single_trade_dominance_limit=unset,
        regime_dominance_limit=unset,
    )


def _threshold_from_mapping(
    payload: Mapping[str, Any] | None,
    *,
    field_name: str,
    numeric: bool,
) -> VersionedThresholdV1:
    if payload is None:
        return _required_not_configured()
    status_raw = payload.get("status", ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED.value)
    try:
        status = ThresholdBindingStatus(str(status_raw))
    except ValueError as exc:
        raise EconomicValidityPolicyError(f"threshold_status_invalid:{field_name}") from exc
    if status is ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED:
        return VersionedThresholdV1(status=status)
    if numeric:
        if "value" not in payload:
            raise EconomicValidityPolicyError(f"threshold_value_missing:{field_name}")
        return VersionedThresholdV1(status=status, value=float(payload["value"]))
    policy_ref = payload.get("policy_ref")
    if not policy_ref:
        raise EconomicValidityPolicyError(f"threshold_policy_ref_missing:{field_name}")
    return VersionedThresholdV1(status=status, policy_ref=str(policy_ref))


def load_economic_validity_policy_v1(
    cfg: Mapping[str, Any] | None = None,
) -> EconomicValidityPolicyV1:
    """Load versioned policy from config or return canonical default (fail-closed thresholds)."""
    if cfg is None:
        return default_economic_validity_policy_v1()
    section = cfg.get("economic_validity_policy")
    if section is None:
        return default_economic_validity_policy_v1()
    if not isinstance(section, Mapping):
        raise EconomicValidityPolicyError("economic_validity_policy_section_not_mapping")
    policy_version = str(section.get("policy_version", ECONOMIC_VALIDITY_POLICY_VERSION))
    if policy_version != ECONOMIC_VALIDITY_POLICY_VERSION:
        raise EconomicValidityPolicyError(f"policy_version_mismatch:{policy_version}")
    owner = str(section.get("owner", ECONOMIC_VALIDITY_POLICY_OWNER))
    thresholds = section.get("thresholds")
    if thresholds is not None and not isinstance(thresholds, Mapping):
        raise EconomicValidityPolicyError("economic_validity_policy_thresholds_not_mapping")
    thresholds = thresholds or {}
    return EconomicValidityPolicyV1(
        policy_version=policy_version,
        owner=owner,
        minimum_net_expectancy=_threshold_from_mapping(
            thresholds.get("minimum_net_expectancy"),
            field_name="minimum_net_expectancy",
            numeric=True,
        ),
        minimum_profit_factor=_threshold_from_mapping(
            thresholds.get("minimum_profit_factor"),
            field_name="minimum_profit_factor",
            numeric=True,
        ),
        maximum_max_drawdown=_threshold_from_mapping(
            thresholds.get("maximum_max_drawdown"),
            field_name="maximum_max_drawdown",
            numeric=True,
        ),
        walk_forward_stability_threshold=_threshold_from_mapping(
            thresholds.get("walk_forward_stability_threshold"),
            field_name="walk_forward_stability_threshold",
            numeric=True,
        ),
        out_of_sample_pass_policy=_threshold_from_mapping(
            thresholds.get("out_of_sample_pass_policy"),
            field_name="out_of_sample_pass_policy",
            numeric=False,
        ),
        parameter_robustness_policy=_threshold_from_mapping(
            thresholds.get("parameter_robustness_policy"),
            field_name="parameter_robustness_policy",
            numeric=False,
        ),
        monte_carlo_pass_policy=_threshold_from_mapping(
            thresholds.get("monte_carlo_pass_policy"),
            field_name="monte_carlo_pass_policy",
            numeric=False,
        ),
        stress_pass_policy=_threshold_from_mapping(
            thresholds.get("stress_pass_policy"),
            field_name="stress_pass_policy",
            numeric=False,
        ),
        minimum_trade_count=_threshold_from_mapping(
            thresholds.get("minimum_trade_count"),
            field_name="minimum_trade_count",
            numeric=True,
        ),
        single_trade_dominance_limit=_threshold_from_mapping(
            thresholds.get("single_trade_dominance_limit"),
            field_name="single_trade_dominance_limit",
            numeric=True,
        ),
        regime_dominance_limit=_threshold_from_mapping(
            thresholds.get("regime_dominance_limit"),
            field_name="regime_dominance_limit",
            numeric=True,
        ),
    )


def validate_economic_validity_policy_v1(policy: EconomicValidityPolicyV1) -> None:
    """Validate policy structure and configured threshold values (fail-closed)."""
    if not policy.is_version_bound():
        raise EconomicValidityPolicyError("policy_not_version_bound")
    for field_name in _NUMERIC_THRESHOLD_FIELDS:
        threshold = getattr(policy, field_name)
        if threshold.status is ThresholdBindingStatus.CONFIGURED:
            if threshold.value is None:
                raise EconomicValidityPolicyError(
                    f"configured_threshold_missing_value:{field_name}"
                )
            if not math.isfinite(threshold.value):
                raise EconomicValidityPolicyError(f"configured_threshold_non_finite:{field_name}")
    for field_name in _POLICY_REF_FIELDS:
        threshold = getattr(policy, field_name)
        if threshold.status is ThresholdBindingStatus.CONFIGURED and not threshold.policy_ref:
            raise EconomicValidityPolicyError(
                f"configured_threshold_missing_policy_ref:{field_name}"
            )


@dataclass(frozen=True)
class EconomicValidityGateEvaluationV1:
    gates_pass: bool
    reason_codes: tuple[str, ...]
    policy_threshold_status: str


def evaluate_economic_validity_gates_v1(
    *,
    policy: EconomicValidityPolicyV1,
    net_expectancy: Optional[float],
    profit_factor: Optional[float],
    max_drawdown: Optional[float],
    trade_count: Optional[int],
) -> EconomicValidityGateEvaluationV1:
    """
    Evaluate evidence metrics against versioned policy thresholds.

    Fail-closed when thresholds are not configured or metrics are missing.
    Does not mutate policy based on results.
    """
    validate_economic_validity_policy_v1(policy)
    reason_codes: list[str] = []
    threshold_status = policy.policy_threshold_status()
    if threshold_status == POLICY_THRESHOLD_STATUS_BLOCKED:
        reason_codes.append("economic_validity_policy_thresholds_not_configured")
        for field_name in policy.unconfigured_fields():
            reason_codes.append(f"policy_threshold_required_not_configured:{field_name}")
        return EconomicValidityGateEvaluationV1(
            gates_pass=False,
            reason_codes=tuple(sorted(set(reason_codes))),
            policy_threshold_status=threshold_status,
        )

    if net_expectancy is None or not math.isfinite(net_expectancy):
        reason_codes.append("gate_metric_missing:net_expectancy")
    elif net_expectancy < policy.minimum_net_expectancy.value:  # type: ignore[operator]
        reason_codes.append("gate_failed:minimum_net_expectancy")

    if profit_factor is None or not math.isfinite(profit_factor):
        reason_codes.append("gate_metric_missing:profit_factor")
    elif profit_factor < policy.minimum_profit_factor.value:  # type: ignore[operator]
        reason_codes.append("gate_failed:minimum_profit_factor")

    if max_drawdown is None or not math.isfinite(max_drawdown):
        reason_codes.append("gate_metric_missing:max_drawdown")
    elif abs(max_drawdown) > policy.maximum_max_drawdown.value:  # type: ignore[operator]
        reason_codes.append("gate_failed:maximum_max_drawdown")

    if trade_count is None:
        reason_codes.append("gate_metric_missing:trade_count")
    elif trade_count < int(policy.minimum_trade_count.value):  # type: ignore[arg-type]
        reason_codes.append("gate_failed:minimum_trade_count")

    gates_pass = len(reason_codes) == 0
    return EconomicValidityGateEvaluationV1(
        gates_pass=gates_pass,
        reason_codes=tuple(sorted(set(reason_codes))),
        policy_threshold_status=threshold_status,
    )


def economic_validity_policy_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "economic_validity_policy_v1",
        "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "owner": ECONOMIC_VALIDITY_POLICY_OWNER,
        "numeric_threshold_fields": list(_NUMERIC_THRESHOLD_FIELDS),
        "policy_ref_fields": list(_POLICY_REF_FIELDS),
        "threshold_binding_statuses": [status.value for status in ThresholdBindingStatus],
        "default_threshold_status": ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED.value,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
        "promotion_effect": False,
    }
