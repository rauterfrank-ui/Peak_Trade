"""Canonical economic observability snapshot v1 (offline evidence contract).

Authority-neutral snapshot SSOT for reporting consumers. Materialization is
contract-only in this slice; no runtime rewire or economic evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from src.backtest.economic_observability_registry_v1 import (
    EconomicObservabilityMetricRegistryV1,
    get_canonical_metric_registry_v1,
)

SCHEMA_VERSION = "canonical_economic_observability_snapshot.v1"
SNAPSHOT_OWNER = "backtest.economic_observability_snapshot_v1"
ZERO_IS_A_VALID_VALUE = True
NULL_MEANS_ABSENT_OR_UNAVAILABLE = True

SNAPSHOT_DOMAIN_KEYS = (
    "economic",
    "costs",
    "strategy_quality",
    "risk",
    "trade_analytics",
    "decision_funnel",
    "exposure",
    "portfolio",
    "robustness",
    "data_quality",
    "provenance",
)


class MetricMaterializationStatus(str, Enum):
    COMPUTED = "COMPUTED"
    RECONSTRUCTED = "RECONSTRUCTED"
    NOT_COMPUTED = "NOT_COMPUTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SOURCE_MISSING = "SOURCE_MISSING"
    OWNER_NOT_BOUND = "OWNER_NOT_BOUND"
    INVALID_INPUT = "INVALID_INPUT"


REASON_REQUIRED_STATUSES = frozenset(
    {
        MetricMaterializationStatus.NOT_COMPUTED,
        MetricMaterializationStatus.NOT_APPLICABLE,
        MetricMaterializationStatus.INSUFFICIENT_DATA,
        MetricMaterializationStatus.SOURCE_MISSING,
        MetricMaterializationStatus.OWNER_NOT_BOUND,
        MetricMaterializationStatus.INVALID_INPUT,
    }
)


class SnapshotContractError(ValueError):
    """Raised when snapshot payload violates the v1 contract."""


@dataclass(frozen=True)
class MetricValueV1:
    value: Optional[float]
    unit: str
    status: MetricMaterializationStatus
    owner: str
    source: str
    formula_version: str
    sample_count: Optional[int]
    quality_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "value": self.value,
            "unit": self.unit,
            "status": self.status.value,
            "owner": self.owner,
            "source": self.source,
            "formula_version": self.formula_version,
            "sample_count": self.sample_count,
            "quality_flags": list(self.quality_flags),
            "reason_codes": list(self.reason_codes),
        }
        return payload

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> MetricValueV1:
        required = (
            "value",
            "unit",
            "status",
            "owner",
            "source",
            "formula_version",
            "sample_count",
            "quality_flags",
            "reason_codes",
        )
        missing = [name for name in required if name not in payload]
        if missing:
            raise SnapshotContractError(f"missing metric value fields: {missing}")
        try:
            status = MetricMaterializationStatus(str(payload["status"]))
        except ValueError as exc:
            raise SnapshotContractError(f"invalid metric status: {payload['status']!r}") from exc
        quality_flags = payload["quality_flags"]
        reason_codes = payload["reason_codes"]
        if not isinstance(quality_flags, list) or not all(
            isinstance(x, str) for x in quality_flags
        ):
            raise SnapshotContractError("quality_flags must be string list")
        if not isinstance(reason_codes, list) or not all(isinstance(x, str) for x in reason_codes):
            raise SnapshotContractError("reason_codes must be string list")
        if status in REASON_REQUIRED_STATUSES and not reason_codes:
            raise SnapshotContractError(f"status {status.value} requires reason_codes")
        return MetricValueV1(
            value=payload["value"],
            unit=str(payload["unit"]),
            status=status,
            owner=str(payload["owner"]),
            source=str(payload["source"]),
            formula_version=str(payload["formula_version"]),
            sample_count=payload["sample_count"],
            quality_flags=tuple(quality_flags),
            reason_codes=tuple(reason_codes),
        )


@dataclass
class CanonicalEconomicObservabilitySnapshotV1:
    schema_version: str = SCHEMA_VERSION
    run_identity: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    economic: dict[str, MetricValueV1] = field(default_factory=dict)
    costs: dict[str, MetricValueV1] = field(default_factory=dict)
    strategy_quality: dict[str, MetricValueV1] = field(default_factory=dict)
    risk: dict[str, MetricValueV1] = field(default_factory=dict)
    trade_analytics: dict[str, MetricValueV1] = field(default_factory=dict)
    decision_funnel: dict[str, MetricValueV1] = field(default_factory=dict)
    exposure: dict[str, MetricValueV1] = field(default_factory=dict)
    portfolio: dict[str, MetricValueV1] = field(default_factory=dict)
    robustness: dict[str, MetricValueV1] = field(default_factory=dict)
    data_quality: dict[str, MetricValueV1] = field(default_factory=dict)
    metric_statuses: dict[str, str] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    manifest_digest: str = ""

    def domain_map(self) -> dict[str, dict[str, MetricValueV1]]:
        return {
            "economic": self.economic,
            "costs": self.costs,
            "strategy_quality": self.strategy_quality,
            "risk": self.risk,
            "trade_analytics": self.trade_analytics,
            "decision_funnel": self.decision_funnel,
            "exposure": self.exposure,
            "portfolio": self.portfolio,
            "robustness": self.robustness,
            "data_quality": self.data_quality,
            "provenance": self.provenance_metrics,
        }

    @property
    def provenance_metrics(self) -> dict[str, MetricValueV1]:
        provenance_bucket = self.provenance.get("metrics")
        if isinstance(provenance_bucket, dict):
            return provenance_bucket
        return {}

    def to_dict(self) -> dict[str, Any]:
        metric_domains = (
            "economic",
            "costs",
            "strategy_quality",
            "risk",
            "trade_analytics",
            "decision_funnel",
            "exposure",
            "portfolio",
            "robustness",
            "data_quality",
        )
        domain_payload: dict[str, Any] = {}
        for domain in metric_domains:
            bucket = getattr(self, domain)
            domain_payload[domain] = {
                metric_id: metric.to_dict() for metric_id, metric in sorted(bucket.items())
            }
        provenance_payload = {
            key: value for key, value in self.provenance.items() if key != "metrics"
        }
        provenance_metrics = self.provenance_metrics
        if provenance_metrics:
            provenance_payload["metrics"] = {
                metric_id: metric.to_dict()
                for metric_id, metric in sorted(provenance_metrics.items())
            }
        return {
            "schema_version": self.schema_version,
            "run_identity": self.run_identity,
            "provenance": provenance_payload,
            "economic": domain_payload["economic"],
            "costs": domain_payload["costs"],
            "strategy_quality": domain_payload["strategy_quality"],
            "risk": domain_payload["risk"],
            "trade_analytics": domain_payload["trade_analytics"],
            "decision_funnel": domain_payload["decision_funnel"],
            "exposure": domain_payload["exposure"],
            "portfolio": domain_payload["portfolio"],
            "robustness": domain_payload["robustness"],
            "data_quality": domain_payload["data_quality"],
            "metric_statuses": dict(sorted(self.metric_statuses.items())),
            "reason_codes": sorted(self.reason_codes),
            "source_refs": sorted(self.source_refs),
            "manifest_digest": self.manifest_digest,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> CanonicalEconomicObservabilitySnapshotV1:
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise SnapshotContractError(
                f"unsupported schema_version: {payload.get('schema_version')!r}"
            )
        snapshot = CanonicalEconomicObservabilitySnapshotV1(
            schema_version=SCHEMA_VERSION,
            run_identity=dict(payload.get("run_identity", {})),
            provenance=dict(payload.get("provenance", {})),
            metric_statuses=dict(payload.get("metric_statuses", {})),
            reason_codes=list(payload.get("reason_codes", [])),
            source_refs=list(payload.get("source_refs", [])),
            manifest_digest=str(payload.get("manifest_digest", "")),
        )
        metric_domains = (
            "economic",
            "costs",
            "strategy_quality",
            "risk",
            "trade_analytics",
            "decision_funnel",
            "exposure",
            "portfolio",
            "robustness",
            "data_quality",
        )
        for domain in metric_domains:
            raw_bucket = payload.get(domain, {})
            if not isinstance(raw_bucket, dict):
                raise SnapshotContractError(f"{domain} must be object")
            parsed: dict[str, MetricValueV1] = {}
            for metric_id, metric_payload in raw_bucket.items():
                parsed[metric_id] = MetricValueV1.from_dict(metric_payload)
            setattr(snapshot, domain, parsed)
        provenance_metrics_raw = snapshot.provenance.get("metrics", {})
        if provenance_metrics_raw:
            parsed_provenance: dict[str, MetricValueV1] = {}
            if not isinstance(provenance_metrics_raw, dict):
                raise SnapshotContractError("provenance.metrics must be object")
            for metric_id, metric_payload in provenance_metrics_raw.items():
                parsed_provenance[metric_id] = MetricValueV1.from_dict(metric_payload)
            snapshot.provenance["metrics"] = parsed_provenance
        return snapshot


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str
    )


def compute_snapshot_digest(snapshot: Mapping[str, Any]) -> str:
    body = {key: value for key, value in snapshot.items() if key != "manifest_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def materialize_empty_snapshot_v1(
    *,
    registry: EconomicObservabilityMetricRegistryV1 | None = None,
    run_identity: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
) -> CanonicalEconomicObservabilitySnapshotV1:
    """Materialize an authority-neutral empty snapshot with NOT_COMPUTED placeholders."""
    resolved_registry = registry or get_canonical_metric_registry_v1()
    snapshot = CanonicalEconomicObservabilitySnapshotV1(
        run_identity=dict(run_identity or {"snapshot_owner": SNAPSHOT_OWNER}),
        provenance={"registry_owner": resolved_registry.registry_owner, "metrics": {}},
        source_refs=list(source_refs or []),
    )
    for entry in resolved_registry.entries:
        if entry.domain == "provenance":
            bucket = snapshot.provenance["metrics"]
        else:
            bucket = getattr(snapshot, entry.domain)
        status = _availability_to_materialization_status(entry.availability_status.value)
        reason_codes: tuple[str, ...] = ()
        if status in REASON_REQUIRED_STATUSES:
            reason_codes = (_availability_reason_code(entry.availability_status.value),)
        bucket[entry.metric_id] = MetricValueV1(
            value=None,
            unit=entry.unit,
            status=status,
            owner=entry.canonical_owner,
            source=entry.source_field_or_formula,
            formula_version="registry_reference_only_v0",
            sample_count=None,
            quality_flags=(),
            reason_codes=reason_codes,
        )
        snapshot.metric_statuses[entry.metric_id] = status.value
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    return snapshot


def _availability_to_materialization_status(availability: str) -> MetricMaterializationStatus:
    if availability == "NOT_APPLICABLE":
        return MetricMaterializationStatus.NOT_APPLICABLE
    if availability in {
        "FULLY_AVAILABLE_AND_REPORTED",
        "COMPUTED_AND_PERSISTED_NOT_REPORTED",
        "COMPUTED_NOT_PERSISTED",
        "RAW_DATA_PERSISTED_RECONSTRUCTABLE",
        "CAPABILITY_PRESENT_NOT_WIRED",
    }:
        return MetricMaterializationStatus.NOT_COMPUTED
    return MetricMaterializationStatus.NOT_COMPUTED


def _availability_reason_code(availability: str) -> str:
    return {
        "NOT_APPLICABLE": "METRIC_NOT_APPLICABLE_IN_CURRENT_SCOPE",
        "NOT_COMPUTED": "METRIC_NOT_COMPUTED_AWAITING_REWIRE",
        "CAPABILITY_PRESENT_NOT_WIRED": "CAPABILITY_PRESENT_NOT_WIRED",
        "COMPUTED_NOT_PERSISTED": "COMPUTED_NOT_PERSISTED_AWAITING_PERSISTENCE_REWIRE",
        "RAW_DATA_PERSISTED_RECONSTRUCTABLE": "RAW_DATA_RECONSTRUCTION_PENDING",
        "COMPUTED_AND_PERSISTED_NOT_REPORTED": "REPORTING_CONSUMER_REWIRE_PENDING",
        "FULLY_AVAILABLE_AND_REPORTED": "MATERIALIZATION_REWIRE_PENDING",
    }.get(availability, "METRIC_NOT_COMPUTED_AWAITING_REWIRE")
