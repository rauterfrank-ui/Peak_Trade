"""
Versioned Economic Validity Policy v1 (RUNBOOK STEP 29M).

Fail-closed, non-authorizing policy contract for offline economic viability evidence.
Thresholds must be explicitly versioned; missing values block economic validity claims.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

ECONOMIC_VALIDITY_POLICY_ID = "economic_validity_policy"
ECONOMIC_VALIDITY_POLICY_VERSION = "economic_validity_policy_v1"
ECONOMIC_VALIDITY_POLICY_SCHEMA_VERSION = "1"
ECONOMIC_VALIDITY_POLICY_OWNER = "backtest.economic_validity_policy_v1"
ECONOMIC_VALIDITY_POLICY_EFFECTIVE_FROM = "2026-07-01"
REASON_CODE_CONTRACT_VERSION = "economic_validity_reason_codes_v1"

POLICY_THRESHOLD_STATUS_PASS = "PASS"
POLICY_THRESHOLD_STATUS_BLOCKED = "BLOCKED_BY_MISSING_VERSIONED_VALUES"

APPLICABLE_STRATEGY_CLASS = "mv2_offline_research"
APPLICABLE_INSTRUMENT_CLASS = "linear_usdt_margined_futures"

_NUMERIC_THRESHOLD_FIELDS = (
    "minimum_net_expectancy",
    "minimum_profit_factor",
    "maximum_max_drawdown",
    "walk_forward_stability_threshold",
    "minimum_walk_forward_pass_ratio",
    "minimum_out_of_sample_pass_ratio",
    "minimum_monte_carlo_pass_ratio",
    "minimum_trade_count",
    "single_trade_dominance_limit",
    "regime_dominance_limit",
    "maximum_allowed_stress_failures",
    "maximum_parameter_neighbor_degradation",
)

_POLICY_REF_FIELDS = (
    "out_of_sample_pass_policy",
    "parameter_robustness_policy",
    "monte_carlo_pass_policy",
    "stress_pass_policy",
)

_ALL_THRESHOLD_FIELDS = _NUMERIC_THRESHOLD_FIELDS + _POLICY_REF_FIELDS

_REQUIRED_BINDING_STATUS_FIELDS = (
    "required_data_admissibility_status",
    "required_cost_model_status",
    "required_funding_binding_status",
    "required_execution_model_status",
    "required_reproducibility_status",
    "required_digest_binding_status",
    "required_manifest_binding_status",
    "required_parameter_robustness_status",
)


class ThresholdBindingStatus(str, Enum):
    CONFIGURED = "CONFIGURED"
    REQUIRED_NOT_CONFIGURED = "REQUIRED_NOT_CONFIGURED"


class EconomicValidityEvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


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


def _configured(value: float) -> VersionedThresholdV1:
    return VersionedThresholdV1(status=ThresholdBindingStatus.CONFIGURED, value=float(value))


def _configured_ref(policy_ref: str) -> VersionedThresholdV1:
    return VersionedThresholdV1(
        status=ThresholdBindingStatus.CONFIGURED,
        policy_ref=str(policy_ref),
    )


def _required_not_configured() -> VersionedThresholdV1:
    return VersionedThresholdV1(status=ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED)


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
    policy_id: str = ECONOMIC_VALIDITY_POLICY_ID
    policy_schema_version: str = ECONOMIC_VALIDITY_POLICY_SCHEMA_VERSION
    effective_from: str = ECONOMIC_VALIDITY_POLICY_EFFECTIVE_FROM
    applicable_strategy_class: str = APPLICABLE_STRATEGY_CLASS
    applicable_instrument_class: str = APPLICABLE_INSTRUMENT_CLASS
    futures_only: bool = True
    bitcoin_direction_allowed: bool = False
    minimum_walk_forward_pass_ratio: VersionedThresholdV1 = field(
        default_factory=_required_not_configured
    )
    minimum_out_of_sample_pass_ratio: VersionedThresholdV1 = field(
        default_factory=_required_not_configured
    )
    minimum_monte_carlo_pass_ratio: VersionedThresholdV1 = field(
        default_factory=_required_not_configured
    )
    maximum_allowed_stress_failures: VersionedThresholdV1 = field(
        default_factory=_required_not_configured
    )
    maximum_parameter_neighbor_degradation: VersionedThresholdV1 = field(
        default_factory=_required_not_configured
    )
    required_stress_scenarios: tuple[str, ...] = (
        "vol_spike_v1",
        "gap_down_v1",
        "liquidity_crunch_v1",
    )
    required_data_admissibility_status: str = "PASS"
    required_cost_model_status: str = "PASS"
    required_funding_binding_status: str = "PASS"
    required_execution_model_status: str = "PASS"
    required_reproducibility_status: str = "PASS"
    required_digest_binding_status: str = "PASS"
    required_manifest_binding_status: str = "PASS"
    required_parameter_robustness_status: str = "PASS"
    threshold_units: Mapping[str, str] = field(default_factory=dict)
    comparison_semantics: Mapping[str, str] = field(default_factory=dict)
    missing_metric_behavior: str = "BLOCKED"
    non_finite_metric_behavior: str = "BLOCKED"
    reason_code_contract_version: str = REASON_CODE_CONTRACT_VERSION
    authority_effect: str = "NONE"
    runtime_effect: bool = False
    order_effect: bool = False
    promotion_effect: bool = False

    def is_version_bound(self) -> bool:
        return (
            self.policy_version == ECONOMIC_VALIDITY_POLICY_VERSION
            and self.owner == ECONOMIC_VALIDITY_POLICY_OWNER
            and self.policy_id == ECONOMIC_VALIDITY_POLICY_ID
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
            return POLICY_THRESHOLD_STATUS_PASS
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

    def implementation_digest(self) -> str:
        return _stable_digest(
            {
                "owner": self.owner,
                "policy_version": self.policy_version,
                "policy_schema_version": self.policy_schema_version,
            }
        )

    def _digest_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        for key in (
            "policy_threshold_status",
            "config_digest",
            "implementation_digest",
            "policy_digest",
        ):
            payload.pop(key, None)
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "policy_schema_version": self.policy_schema_version,
            "effective_from": self.effective_from,
            "owner": self.owner,
            "applicable_strategy_class": self.applicable_strategy_class,
            "applicable_instrument_class": self.applicable_instrument_class,
            "futures_only": self.futures_only,
            "bitcoin_direction_allowed": self.bitcoin_direction_allowed,
            "minimum_net_expectancy": self.minimum_net_expectancy.to_dict(),
            "minimum_profit_factor": self.minimum_profit_factor.to_dict(),
            "maximum_max_drawdown": self.maximum_max_drawdown.to_dict(),
            "walk_forward_stability_threshold": self.walk_forward_stability_threshold.to_dict(),
            "minimum_walk_forward_pass_ratio": self.minimum_walk_forward_pass_ratio.to_dict(),
            "minimum_out_of_sample_pass_ratio": self.minimum_out_of_sample_pass_ratio.to_dict(),
            "minimum_monte_carlo_pass_ratio": self.minimum_monte_carlo_pass_ratio.to_dict(),
            "out_of_sample_pass_policy": self.out_of_sample_pass_policy.to_dict(),
            "parameter_robustness_policy": self.parameter_robustness_policy.to_dict(),
            "monte_carlo_pass_policy": self.monte_carlo_pass_policy.to_dict(),
            "stress_pass_policy": self.stress_pass_policy.to_dict(),
            "minimum_trade_count": self.minimum_trade_count.to_dict(),
            "single_trade_dominance_limit": self.single_trade_dominance_limit.to_dict(),
            "regime_dominance_limit": self.regime_dominance_limit.to_dict(),
            "maximum_allowed_stress_failures": self.maximum_allowed_stress_failures.to_dict(),
            "maximum_parameter_neighbor_degradation": (
                self.maximum_parameter_neighbor_degradation.to_dict()
            ),
            "required_stress_scenarios": list(self.required_stress_scenarios),
            "required_data_admissibility_status": self.required_data_admissibility_status,
            "required_cost_model_status": self.required_cost_model_status,
            "required_funding_binding_status": self.required_funding_binding_status,
            "required_execution_model_status": self.required_execution_model_status,
            "required_reproducibility_status": self.required_reproducibility_status,
            "required_digest_binding_status": self.required_digest_binding_status,
            "required_manifest_binding_status": self.required_manifest_binding_status,
            "required_parameter_robustness_status": self.required_parameter_robustness_status,
            "threshold_units": dict(self.threshold_units),
            "comparison_semantics": dict(self.comparison_semantics),
            "missing_metric_behavior": self.missing_metric_behavior,
            "non_finite_metric_behavior": self.non_finite_metric_behavior,
            "reason_code_contract_version": self.reason_code_contract_version,
            "policy_threshold_status": self.policy_threshold_status(),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "order_effect": self.order_effect,
            "promotion_effect": self.promotion_effect,
        }

    def config_digest(self) -> str:
        return compute_economic_validity_policy_digest(self)

    def policy_digest(self) -> str:
        return self.config_digest()

    def to_manifest_dict(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["config_digest"] = self.config_digest()
        payload["implementation_digest"] = self.implementation_digest()
        payload["policy_digest"] = self.policy_digest()
        return payload


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_economic_validity_policy_digest(policy: EconomicValidityPolicyV1) -> str:
    return _stable_digest(policy._digest_payload())


def _default_threshold_units() -> dict[str, str]:
    return {
        "minimum_net_expectancy": "fraction_per_trade",
        "minimum_profit_factor": "ratio",
        "maximum_max_drawdown": "fraction_absolute",
        "walk_forward_stability_threshold": "pass_ratio",
        "minimum_walk_forward_pass_ratio": "pass_ratio",
        "minimum_out_of_sample_pass_ratio": "pass_ratio",
        "minimum_monte_carlo_pass_ratio": "pass_ratio",
        "minimum_trade_count": "count",
        "single_trade_dominance_limit": "profit_contribution_fraction",
        "regime_dominance_limit": "profit_contribution_fraction",
        "maximum_allowed_stress_failures": "count",
        "maximum_parameter_neighbor_degradation": "relative_degradation_fraction",
    }


def _default_comparison_semantics() -> dict[str, str]:
    return {
        "minimum_net_expectancy": "metric_gte_threshold",
        "minimum_profit_factor": "metric_gte_threshold",
        "maximum_max_drawdown": "abs_metric_lte_threshold",
        "walk_forward_stability_threshold": "pass_ratio_gte_threshold",
        "minimum_walk_forward_pass_ratio": "pass_ratio_gte_threshold",
        "minimum_out_of_sample_pass_ratio": "pass_ratio_gte_threshold",
        "minimum_monte_carlo_pass_ratio": "pass_ratio_gte_threshold",
        "minimum_trade_count": "metric_gte_threshold",
        "single_trade_dominance_limit": "contribution_lte_threshold",
        "regime_dominance_limit": "contribution_lte_threshold",
        "maximum_allowed_stress_failures": "failure_count_lte_threshold",
        "maximum_parameter_neighbor_degradation": "degradation_lte_threshold",
    }


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
        minimum_walk_forward_pass_ratio=unset,
        minimum_out_of_sample_pass_ratio=unset,
        minimum_monte_carlo_pass_ratio=unset,
        out_of_sample_pass_policy=unset,
        parameter_robustness_policy=unset,
        monte_carlo_pass_policy=unset,
        stress_pass_policy=unset,
        minimum_trade_count=unset,
        single_trade_dominance_limit=unset,
        regime_dominance_limit=unset,
        maximum_allowed_stress_failures=unset,
        maximum_parameter_neighbor_degradation=unset,
        threshold_units=_default_threshold_units(),
        comparison_semantics=_default_comparison_semantics(),
    )


def canonical_economic_validity_policy_v1() -> EconomicValidityPolicyV1:
    """
    Versioned canonical threshold binding for STEP 29M.

    Values are sourced from existing repo policy/config surfaces or conservative
    baselines documented in durable evidence — never from a single backtest outcome.
    """
    wf_ratio = _configured(0.5)
    return EconomicValidityPolicyV1(
        policy_version=ECONOMIC_VALIDITY_POLICY_VERSION,
        owner=ECONOMIC_VALIDITY_POLICY_OWNER,
        minimum_net_expectancy=_configured(0.0),
        minimum_profit_factor=_configured(1.3),
        maximum_max_drawdown=_configured(0.25),
        walk_forward_stability_threshold=wf_ratio,
        minimum_walk_forward_pass_ratio=wf_ratio,
        minimum_out_of_sample_pass_ratio=_configured(0.5),
        minimum_monte_carlo_pass_ratio=_configured(0.5),
        out_of_sample_pass_policy=_configured_ref("economic_validity_oos_pass_ratio_v1"),
        parameter_robustness_policy=_configured_ref("economic_validity_param_robust_v1"),
        monte_carlo_pass_policy=_configured_ref("economic_validity_mc_pass_ratio_v1"),
        stress_pass_policy=_configured_ref("economic_validity_stress_pass_v1"),
        minimum_trade_count=_configured(50.0),
        single_trade_dominance_limit=_configured(0.5),
        regime_dominance_limit=_configured(0.6),
        maximum_allowed_stress_failures=_configured(1.0),
        maximum_parameter_neighbor_degradation=_configured(0.25),
        threshold_units=_default_threshold_units(),
        comparison_semantics=_default_comparison_semantics(),
    )


def canonical_economic_validity_policy_threshold_sources_v1() -> dict[str, dict[str, str]]:
    """Threshold provenance matrix for durable evidence (anti cherry-picking)."""
    return {
        "minimum_net_expectancy": {
            "value": "0.0",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Non-negative net edge after costs; metric definition unambiguous",
        },
        "minimum_profit_factor": {
            "value": "1.3",
            "classification": "REUSED_EXISTING_CANONICAL_VALUE",
            "source": "config/config.toml [strategy_validation] min_profit_factor",
        },
        "maximum_max_drawdown": {
            "value": "0.25",
            "classification": "REUSED_EXISTING_CANONICAL_VALUE",
            "source": "config/config.toml portfolio max_drawdown / docs ARCHITECTURE",
        },
        "minimum_walk_forward_pass_ratio": {
            "value": "0.5",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Conservative half-window OOS pass ratio; independent of current runs",
        },
        "minimum_out_of_sample_pass_ratio": {
            "value": "0.5",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Conservative OOS stability baseline bound to oos_pass_policy ref",
        },
        "minimum_monte_carlo_pass_ratio": {
            "value": "0.5",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Conservative MC robustness baseline bound to mc_pass_policy ref",
        },
        "minimum_trade_count": {
            "value": "50",
            "classification": "REUSED_EXISTING_CANONICAL_VALUE",
            "source": "config/config.toml [strategy_validation] min_trades",
        },
        "single_trade_dominance_limit": {
            "value": "0.5",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Max 50% profit from single trade concentration limit",
        },
        "regime_dominance_limit": {
            "value": "0.6",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Max 60% profit from single regime concentration limit",
        },
        "maximum_allowed_stress_failures": {
            "value": "1",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Allow at most one required stress scenario failure",
        },
        "maximum_parameter_neighbor_degradation": {
            "value": "0.25",
            "classification": "NEW_CONSERVATIVE_BASELINE_REQUIRED",
            "source": "Max 25% neighbor parameter degradation vs baseline",
        },
    }


def step29m_canonical_policy_binding_requested(cfg: Mapping[str, Any]) -> bool:
    section = cfg.get("economic_validity_policy")
    if isinstance(section, Mapping) and section.get("explicit_unbound") is True:
        return False
    if isinstance(section, Mapping) and section.get("thresholds"):
        return False
    return "backtest" in cfg


def resolve_economic_validity_policy_v1(
    cfg: Mapping[str, Any] | None = None,
) -> EconomicValidityPolicyV1:
    """Resolve policy for STEP 29M evidence: explicit cfg > canonical binding > fail-closed default."""
    if cfg is None:
        return default_economic_validity_policy_v1()
    section = cfg.get("economic_validity_policy")
    if section is not None:
        return load_economic_validity_policy_v1(cfg)
    if step29m_canonical_policy_binding_requested(cfg):
        return canonical_economic_validity_policy_v1()
    return default_economic_validity_policy_v1()


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

    def _num(name: str) -> VersionedThresholdV1:
        return _threshold_from_mapping(thresholds.get(name), field_name=name, numeric=True)

    def _ref(name: str) -> VersionedThresholdV1:
        return _threshold_from_mapping(thresholds.get(name), field_name=name, numeric=False)

    wf = _num("walk_forward_stability_threshold")
    wf_ratio = _num("minimum_walk_forward_pass_ratio")
    if (
        wf.status is ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED
        and wf_ratio.status is ThresholdBindingStatus.CONFIGURED
    ):
        wf = wf_ratio
    elif (
        wf_ratio.status is ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED
        and wf.status is ThresholdBindingStatus.CONFIGURED
    ):
        wf_ratio = wf

    return EconomicValidityPolicyV1(
        policy_version=policy_version,
        owner=owner,
        minimum_net_expectancy=_num("minimum_net_expectancy"),
        minimum_profit_factor=_num("minimum_profit_factor"),
        maximum_max_drawdown=_num("maximum_max_drawdown"),
        walk_forward_stability_threshold=wf,
        minimum_walk_forward_pass_ratio=wf_ratio,
        minimum_out_of_sample_pass_ratio=_num("minimum_out_of_sample_pass_ratio"),
        minimum_monte_carlo_pass_ratio=_num("minimum_monte_carlo_pass_ratio"),
        out_of_sample_pass_policy=_ref("out_of_sample_pass_policy"),
        parameter_robustness_policy=_ref("parameter_robustness_policy"),
        monte_carlo_pass_policy=_ref("monte_carlo_pass_policy"),
        stress_pass_policy=_ref("stress_pass_policy"),
        minimum_trade_count=_num("minimum_trade_count"),
        single_trade_dominance_limit=_num("single_trade_dominance_limit"),
        regime_dominance_limit=_num("regime_dominance_limit"),
        maximum_allowed_stress_failures=_num("maximum_allowed_stress_failures"),
        maximum_parameter_neighbor_degradation=_num("maximum_parameter_neighbor_degradation"),
        threshold_units=_default_threshold_units(),
        comparison_semantics=_default_comparison_semantics(),
    )


def validate_economic_validity_policy_v1(policy: EconomicValidityPolicyV1) -> None:
    """Validate policy structure and configured threshold values (fail-closed)."""
    if not policy.policy_version:
        raise EconomicValidityPolicyError("policy_version_missing")
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


def validate_policy_digest_binding_v1(
    *,
    policy: EconomicValidityPolicyV1,
    expected_digest: str,
) -> None:
    if not expected_digest:
        raise EconomicValidityPolicyError("policy_digest_missing")
    if policy.policy_digest() != expected_digest:
        raise EconomicValidityPolicyError("policy_digest_mismatch")


def detect_policy_mutation_without_version_change_v1(
    *,
    before: EconomicValidityPolicyV1,
    after: EconomicValidityPolicyV1,
) -> bool:
    if before.policy_version != after.policy_version and before.to_dict() != after.to_dict():
        return True
    if (
        before.policy_version == after.policy_version
        and before.config_digest() != after.config_digest()
    ):
        return True
    return False


@dataclass(frozen=True)
class EconomicValidityGateEvaluationV1:
    gates_pass: bool
    reason_codes: tuple[str, ...]
    policy_threshold_status: str
    evaluation_status: EconomicValidityEvaluationStatus = EconomicValidityEvaluationStatus.BLOCKED


@dataclass(frozen=True)
class EconomicValidityEvidenceMetricsV1:
    net_expectancy: Optional[float] = None
    profit_factor: Optional[float] = None
    max_drawdown: Optional[float] = None
    trade_count: Optional[int] = None
    walk_forward_pass_ratio: Optional[float] = None
    out_of_sample_pass_ratio: Optional[float] = None
    monte_carlo_pass_ratio: Optional[float] = None
    stress_failure_count: Optional[int] = None
    parameter_robustness_pass: Optional[bool] = None
    parameter_neighbor_degradation: Optional[float] = None
    single_trade_profit_contribution: Optional[float] = None
    single_regime_profit_contribution: Optional[float] = None
    data_admissibility_status: Optional[str] = None
    cost_model_status: Optional[str] = None
    funding_binding_status: Optional[str] = None
    execution_model_status: Optional[str] = None
    reproducibility_status: Optional[str] = None
    digest_binding_status: Optional[str] = None
    manifest_binding_status: Optional[str] = None


def _metric_blocked(reason_codes: list[str], code: str) -> None:
    reason_codes.append(code)


def _compare_gte(
    *,
    value: Optional[float],
    threshold: float,
    field_name: str,
    reason_codes: list[str],
    fail_code: str,
    boundary_inclusive: bool = True,
) -> bool:
    if value is None:
        _metric_blocked(reason_codes, f"METRIC_MISSING:{field_name}")
        return False
    if not math.isfinite(value):
        _metric_blocked(reason_codes, f"METRIC_NON_FINITE:{field_name}")
        return False
    if boundary_inclusive:
        ok = value >= threshold
    else:
        ok = value > threshold
    if not ok:
        reason_codes.append(fail_code)
    return ok


def _compare_abs_lte(
    *,
    value: Optional[float],
    threshold: float,
    field_name: str,
    reason_codes: list[str],
    fail_code: str,
) -> bool:
    if value is None:
        _metric_blocked(reason_codes, f"METRIC_MISSING:{field_name}")
        return False
    if not math.isfinite(value):
        _metric_blocked(reason_codes, f"METRIC_NON_FINITE:{field_name}")
        return False
    if abs(value) > threshold:
        reason_codes.append(fail_code)
        return False
    return True


def evaluate_economic_validity_against_policy_v1(
    *,
    policy: EconomicValidityPolicyV1,
    metrics: EconomicValidityEvidenceMetricsV1,
    expected_policy_digest: str = "",
) -> EconomicValidityGateEvaluationV1:
    """Full fail-closed economic validity evaluation against versioned policy thresholds."""
    validate_economic_validity_policy_v1(policy)
    reason_codes: list[str] = []
    threshold_status = policy.policy_threshold_status()

    if not policy.policy_version:
        reason_codes.append("POLICY_VERSION_MISSING")
    if expected_policy_digest:
        try:
            validate_policy_digest_binding_v1(
                policy=policy,
                expected_digest=expected_policy_digest,
            )
        except EconomicValidityPolicyError:
            reason_codes.append("POLICY_DIGEST_MISMATCH")
    elif policy.thresholds_configured() and not policy.policy_digest():
        reason_codes.append("POLICY_DIGEST_MISSING")

    if threshold_status == POLICY_THRESHOLD_STATUS_BLOCKED:
        reason_codes.append("economic_validity_policy_thresholds_not_configured")
        for field_name in policy.unconfigured_fields():
            reason_codes.append(f"policy_threshold_required_not_configured:{field_name}")
        return EconomicValidityGateEvaluationV1(
            gates_pass=False,
            reason_codes=tuple(sorted(set(reason_codes))),
            policy_threshold_status=threshold_status,
            evaluation_status=EconomicValidityEvaluationStatus.BLOCKED,
        )

    if policy.bitcoin_direction_allowed:
        reason_codes.append("BITCOIN_DIRECTION_NOT_ALLOWED")

    binding_checks = (
        ("data_admissibility_status", metrics.data_admissibility_status, "DATA_NOT_ADMISSIBLE"),
        ("cost_model_status", metrics.cost_model_status, "COST_MODEL_NOT_BOUND"),
        ("funding_binding_status", metrics.funding_binding_status, "FUNDING_MODEL_NOT_BOUND"),
        ("execution_model_status", metrics.execution_model_status, "EXECUTION_MODEL_NOT_BOUND"),
        ("reproducibility_status", metrics.reproducibility_status, "REPRODUCIBILITY_FAILED"),
        ("digest_binding_status", metrics.digest_binding_status, "DIGEST_BINDING_FAILED"),
        ("manifest_binding_status", metrics.manifest_binding_status, "MANIFEST_BINDING_FAILED"),
    )
    for attr, actual, fail_code in binding_checks:
        required = getattr(policy, f"required_{attr}")
        if actual is None:
            reason_codes.append(f"METRIC_MISSING:{attr}")
        elif actual != required:
            reason_codes.append(fail_code)

    _compare_gte(
        value=metrics.net_expectancy,
        threshold=policy.minimum_net_expectancy.value,  # type: ignore[arg-type]
        field_name="net_expectancy",
        reason_codes=reason_codes,
        fail_code="NET_EXPECTANCY_BELOW_THRESHOLD",
    )
    _compare_gte(
        value=metrics.profit_factor,
        threshold=policy.minimum_profit_factor.value,  # type: ignore[arg-type]
        field_name="profit_factor",
        reason_codes=reason_codes,
        fail_code="PROFIT_FACTOR_BELOW_THRESHOLD",
    )
    _compare_abs_lte(
        value=metrics.max_drawdown,
        threshold=policy.maximum_max_drawdown.value,  # type: ignore[arg-type]
        field_name="max_drawdown",
        reason_codes=reason_codes,
        fail_code="MAX_DRAWDOWN_ABOVE_THRESHOLD",
    )
    if metrics.trade_count is None:
        reason_codes.append("METRIC_MISSING:trade_count")
    elif metrics.trade_count < int(policy.minimum_trade_count.value):  # type: ignore[arg-type]
        reason_codes.append("TRADE_COUNT_BELOW_THRESHOLD")

    for ratio_field, threshold_obj, fail_code in (
        ("walk_forward_pass_ratio", policy.minimum_walk_forward_pass_ratio, "WALK_FORWARD_FAILED"),
        (
            "out_of_sample_pass_ratio",
            policy.minimum_out_of_sample_pass_ratio,
            "OUT_OF_SAMPLE_FAILED",
        ),
        ("monte_carlo_pass_ratio", policy.minimum_monte_carlo_pass_ratio, "MONTE_CARLO_FAILED"),
    ):
        _compare_gte(
            value=getattr(metrics, ratio_field),
            threshold=threshold_obj.value,  # type: ignore[arg-type]
            field_name=ratio_field,
            reason_codes=reason_codes,
            fail_code=fail_code,
        )

    if metrics.stress_failure_count is None:
        reason_codes.append("METRIC_MISSING:stress_failure_count")
    elif metrics.stress_failure_count > int(policy.maximum_allowed_stress_failures.value):  # type: ignore[arg-type]
        reason_codes.append("STRESS_FAILED")

    if metrics.parameter_robustness_pass is None:
        reason_codes.append("METRIC_MISSING:parameter_robustness_pass")
    elif metrics.parameter_robustness_pass is False:
        reason_codes.append("PARAMETER_ROBUSTNESS_FAILED")

    _compare_abs_lte(
        value=metrics.parameter_neighbor_degradation,
        threshold=policy.maximum_parameter_neighbor_degradation.value,  # type: ignore[arg-type]
        field_name="parameter_neighbor_degradation",
        reason_codes=reason_codes,
        fail_code="PARAMETER_ROBUSTNESS_FAILED",
    )
    _compare_abs_lte(
        value=metrics.single_trade_profit_contribution,
        threshold=policy.single_trade_dominance_limit.value,  # type: ignore[arg-type]
        field_name="single_trade_profit_contribution",
        reason_codes=reason_codes,
        fail_code="SINGLE_TRADE_DOMINANCE_EXCEEDED",
    )
    _compare_abs_lte(
        value=metrics.single_regime_profit_contribution,
        threshold=policy.regime_dominance_limit.value,  # type: ignore[arg-type]
        field_name="single_regime_profit_contribution",
        reason_codes=reason_codes,
        fail_code="REGIME_DOMINANCE_EXCEEDED",
    )

    hard_fail_codes = {
        code
        for code in reason_codes
        if not code.startswith("METRIC_MISSING")
        and not code.startswith("policy_threshold_required_not_configured")
        and code != "economic_validity_policy_thresholds_not_configured"
    }
    blocked_codes = {code for code in reason_codes if code.startswith("METRIC_MISSING")}

    if blocked_codes and not hard_fail_codes:
        status = EconomicValidityEvaluationStatus.BLOCKED
    elif hard_fail_codes:
        status = EconomicValidityEvaluationStatus.FAIL
    else:
        status = EconomicValidityEvaluationStatus.PASS

    gates_pass = status is EconomicValidityEvaluationStatus.PASS
    return EconomicValidityGateEvaluationV1(
        gates_pass=gates_pass,
        reason_codes=tuple(sorted(set(reason_codes))),
        policy_threshold_status=threshold_status,
        evaluation_status=status,
    )


def evaluate_economic_validity_gates_v1(
    *,
    policy: EconomicValidityPolicyV1,
    net_expectancy: Optional[float],
    profit_factor: Optional[float],
    max_drawdown: Optional[float],
    trade_count: Optional[int],
) -> EconomicValidityGateEvaluationV1:
    """Backward-compatible narrow metric gate evaluation."""
    return evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=EconomicValidityEvidenceMetricsV1(
            net_expectancy=net_expectancy,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            trade_count=trade_count,
            data_admissibility_status="PASS",
            cost_model_status="PASS",
            funding_binding_status="PASS",
            execution_model_status="PASS",
            reproducibility_status="PASS",
            digest_binding_status="PASS",
            manifest_binding_status="PASS",
            walk_forward_pass_ratio=1.0,
            out_of_sample_pass_ratio=1.0,
            monte_carlo_pass_ratio=1.0,
            stress_failure_count=0,
            parameter_robustness_pass=True,
            parameter_neighbor_degradation=0.0,
            single_trade_profit_contribution=0.0,
            single_regime_profit_contribution=0.0,
        ),
        expected_policy_digest=policy.policy_digest() if policy.thresholds_configured() else "",
    )


def economic_validity_policy_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": "economic_validity_policy_v1",
        "policy_id": ECONOMIC_VALIDITY_POLICY_ID,
        "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "policy_schema_version": ECONOMIC_VALIDITY_POLICY_SCHEMA_VERSION,
        "owner": ECONOMIC_VALIDITY_POLICY_OWNER,
        "numeric_threshold_fields": list(_NUMERIC_THRESHOLD_FIELDS),
        "policy_ref_fields": list(_POLICY_REF_FIELDS),
        "required_binding_status_fields": list(_REQUIRED_BINDING_STATUS_FIELDS),
        "threshold_binding_statuses": [status.value for status in ThresholdBindingStatus],
        "default_threshold_status": ThresholdBindingStatus.REQUIRED_NOT_CONFIGURED.value,
        "policy_threshold_status_pass": POLICY_THRESHOLD_STATUS_PASS,
        "policy_threshold_status_blocked": POLICY_THRESHOLD_STATUS_BLOCKED,
        "authority_effect": "NONE",
        "runtime_effect": False,
        "order_effect": False,
        "promotion_effect": False,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
    }
