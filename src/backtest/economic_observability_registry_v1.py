"""Canonical economic observability metric registry v1 (offline contract foundation).

Authority-neutral registry SSOT for the 148 discovery metrics. Does not compute,
persist, or report metrics at runtime in this slice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "economic_observability_metric_registry.v1"
REGISTRY_OWNER = "backtest.economic_observability_registry_v1"
DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[2] / "config/economic_observability_metric_registry_v1.json"
)
DISCOVERY_METRIC_COUNT = 148


class AvailabilityStatus(str, Enum):
    FULLY_AVAILABLE_AND_REPORTED = "FULLY_AVAILABLE_AND_REPORTED"
    COMPUTED_AND_PERSISTED_NOT_REPORTED = "COMPUTED_AND_PERSISTED_NOT_REPORTED"
    COMPUTED_NOT_PERSISTED = "COMPUTED_NOT_PERSISTED"
    RAW_DATA_PERSISTED_RECONSTRUCTABLE = "RAW_DATA_PERSISTED_RECONSTRUCTABLE"
    CAPABILITY_PRESENT_NOT_WIRED = "CAPABILITY_PRESENT_NOT_WIRED"
    NOT_COMPUTED = "NOT_COMPUTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class MetricPriority(str, Enum):
    P0_DECISION_CRITICAL = "P0_DECISION_CRITICAL"
    P1_HIGH_VALUE_DIAGNOSTIC = "P1_HIGH_VALUE_DIAGNOSTIC"
    P2_ADVANCED_ANALYTIC = "P2_ADVANCED_ANALYTIC"
    P3_OPTIONAL_OR_PRESENTATIONAL = "P3_OPTIONAL_OR_PRESENTATIONAL"


REQUIRED_REGISTRY_FIELDS = (
    "metric_id",
    "display_name",
    "domain",
    "description",
    "unit",
    "data_type",
    "canonical_owner",
    "source_field_or_formula",
    "raw_inputs",
    "availability_status",
    "persistence_status",
    "reporting_status",
    "reconstructability",
    "decision_relevance",
    "economic_relevance",
    "risk_relevance",
    "research_relevance",
    "promotion_relevance",
    "runtime_relevance",
    "priority",
    "null_semantics",
    "zero_semantics",
    "sample_requirements",
    "consumer_list",
    "schema_version",
)

SUPPORTED_DOMAINS = frozenset(
    {
        "economic",
        "costs",
        "strategy_quality",
        "risk",
        "trade_analytics",
        "decision_funnel",
        "exposure",
        "portfolio",
        "robustness",
        "provenance",
        "data_quality",
    }
)


class RegistryContractError(ValueError):
    """Raised when registry payload violates the v1 contract."""


@dataclass(frozen=True)
class MetricRegistryEntryV1:
    metric_id: str
    display_name: str
    domain: str
    description: str
    unit: str
    data_type: str
    canonical_owner: str
    source_field_or_formula: str
    raw_inputs: tuple[str, ...]
    availability_status: AvailabilityStatus
    persistence_status: str
    reporting_status: str
    reconstructability: str
    decision_relevance: bool
    economic_relevance: bool
    risk_relevance: bool
    research_relevance: bool
    promotion_relevance: bool
    runtime_relevance: bool
    priority: MetricPriority
    null_semantics: str
    zero_semantics: str
    sample_requirements: str
    consumer_list: tuple[str, ...]
    schema_version: str

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> MetricRegistryEntryV1:
        missing = [field for field in REQUIRED_REGISTRY_FIELDS if field not in payload]
        if missing:
            raise RegistryContractError(f"missing registry fields: {missing}")
        try:
            availability = AvailabilityStatus(str(payload["availability_status"]))
        except ValueError as exc:
            raise RegistryContractError(
                f"invalid availability_status for {payload['metric_id']!r}"
            ) from exc
        try:
            priority = MetricPriority(str(payload["priority"]))
        except ValueError as exc:
            raise RegistryContractError(f"invalid priority for {payload['metric_id']!r}") from exc
        raw_inputs = payload["raw_inputs"]
        consumers = payload["consumer_list"]
        if not isinstance(raw_inputs, list) or not all(isinstance(x, str) for x in raw_inputs):
            raise RegistryContractError(f"raw_inputs must be string list: {payload['metric_id']}")
        if not isinstance(consumers, list) or not all(isinstance(x, str) for x in consumers):
            raise RegistryContractError(
                f"consumer_list must be string list: {payload['metric_id']}"
            )
        domain = str(payload["domain"])
        if domain not in SUPPORTED_DOMAINS:
            raise RegistryContractError(f"unsupported domain {domain!r} for {payload['metric_id']}")
        owner = str(payload["canonical_owner"]).strip()
        if not owner or owner.lower() in {"unknown", "tbd", "see canonical_owner_inventory.json"}:
            raise RegistryContractError(f"unresolved owner for {payload['metric_id']}")
        return MetricRegistryEntryV1(
            metric_id=str(payload["metric_id"]),
            display_name=str(payload["display_name"]),
            domain=domain,
            description=str(payload["description"]),
            unit=str(payload["unit"]),
            data_type=str(payload["data_type"]),
            canonical_owner=owner,
            source_field_or_formula=str(payload["source_field_or_formula"]),
            raw_inputs=tuple(raw_inputs),
            availability_status=availability,
            persistence_status=str(payload["persistence_status"]),
            reporting_status=str(payload["reporting_status"]),
            reconstructability=str(payload["reconstructability"]),
            decision_relevance=bool(payload["decision_relevance"]),
            economic_relevance=bool(payload["economic_relevance"]),
            risk_relevance=bool(payload["risk_relevance"]),
            research_relevance=bool(payload["research_relevance"]),
            promotion_relevance=bool(payload["promotion_relevance"]),
            runtime_relevance=bool(payload["runtime_relevance"]),
            priority=priority,
            null_semantics=str(payload["null_semantics"]),
            zero_semantics=str(payload["zero_semantics"]),
            sample_requirements=str(payload["sample_requirements"]),
            consumer_list=tuple(consumers),
            schema_version=str(payload["schema_version"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "display_name": self.display_name,
            "domain": self.domain,
            "description": self.description,
            "unit": self.unit,
            "data_type": self.data_type,
            "canonical_owner": self.canonical_owner,
            "source_field_or_formula": self.source_field_or_formula,
            "raw_inputs": list(self.raw_inputs),
            "availability_status": self.availability_status.value,
            "persistence_status": self.persistence_status,
            "reporting_status": self.reporting_status,
            "reconstructability": self.reconstructability,
            "decision_relevance": self.decision_relevance,
            "economic_relevance": self.economic_relevance,
            "risk_relevance": self.risk_relevance,
            "research_relevance": self.research_relevance,
            "promotion_relevance": self.promotion_relevance,
            "runtime_relevance": self.runtime_relevance,
            "priority": self.priority.value,
            "null_semantics": self.null_semantics,
            "zero_semantics": self.zero_semantics,
            "sample_requirements": self.sample_requirements,
            "consumer_list": list(self.consumer_list),
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class EconomicObservabilityMetricRegistryV1:
    schema_version: str
    registry_owner: str
    discovery_source_ref: str
    metric_count: int
    entries: tuple[MetricRegistryEntryV1, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "registry_owner": self.registry_owner,
            "discovery_source_ref": self.discovery_source_ref,
            "metric_count": self.metric_count,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @property
    def metric_ids(self) -> tuple[str, ...]:
        return tuple(entry.metric_id for entry in self.entries)

    def entry_by_id(self, metric_id: str) -> MetricRegistryEntryV1:
        for entry in self.entries:
            if entry.metric_id == metric_id:
                return entry
        raise KeyError(metric_id)


def load_registry_payload_v1(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or DEFAULT_REGISTRY_PATH
    if not registry_path.is_file():
        raise RegistryContractError(f"registry file missing: {registry_path}")
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RegistryContractError("registry root must be object")
    return payload


def parse_metric_registry_v1(path: Path | None = None) -> EconomicObservabilityMetricRegistryV1:
    payload = load_registry_payload_v1(path)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise RegistryContractError(
            f"unsupported schema_version: {payload.get('schema_version')!r}"
        )
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list):
        raise RegistryContractError("entries must be a list")
    entries = tuple(MetricRegistryEntryV1.from_dict(item) for item in entries_raw)
    return EconomicObservabilityMetricRegistryV1(
        schema_version=SCHEMA_VERSION,
        registry_owner=str(payload.get("registry_owner", REGISTRY_OWNER)),
        discovery_source_ref=str(payload.get("discovery_source_ref", "")),
        metric_count=int(payload.get("metric_count", len(entries))),
        entries=entries,
    )


@lru_cache(maxsize=1)
def get_canonical_metric_registry_v1() -> EconomicObservabilityMetricRegistryV1:
    return parse_metric_registry_v1()


def validate_registry_contract_v1(registry: EconomicObservabilityMetricRegistryV1) -> list[str]:
    issues: list[str] = []
    ids = [entry.metric_id for entry in registry.entries]
    if len(ids) != len(set(ids)):
        issues.append("duplicate_metric_ids")
    if len(ids) != DISCOVERY_METRIC_COUNT:
        issues.append(f"metric_count_mismatch:expected={DISCOVERY_METRIC_COUNT}:actual={len(ids)}")
    if registry.schema_version != SCHEMA_VERSION:
        issues.append("schema_version_missing_or_invalid")
    owners = [entry.canonical_owner for entry in registry.entries]
    if any(not owner.strip() for owner in owners):
        issues.append("unknown_owner_present")
    domains = {entry.domain for entry in registry.entries}
    if not domains.issubset(SUPPORTED_DOMAINS):
        issues.append("unsupported_domain_present")
    return issues
