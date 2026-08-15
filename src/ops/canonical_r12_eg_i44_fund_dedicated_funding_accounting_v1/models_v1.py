"""Fail-closed models for R12 EG-I44 dedicated funding accounting v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class R12EgI44FundError(ValueError):
    """Fail-closed R12 EG-I44 funding contract error."""


class ContractItemStatus(str, Enum):
    CLOSED_PROVEN = "CLOSED_PROVEN"
    CLOSED_BOUNDARY = "CLOSED_BOUNDARY"
    IMPLEMENTED_NOT_PROVEN = "IMPLEMENTED_NOT_PROVEN"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    NOT_REQUIRED_UNTIL_ACTIVATION = "NOT_REQUIRED_UNTIL_ACTIVATION"


STRUCTURAL_CLOSABLE_STATUSES = frozenset(
    {
        ContractItemStatus.CLOSED_PROVEN,
        ContractItemStatus.CLOSED_BOUNDARY,
        ContractItemStatus.NOT_REQUIRED_UNTIL_ACTIVATION,
    }
)


@dataclass(frozen=True)
class ContractRowV1:
    item_id: str
    family: str
    status: ContractItemStatus
    current_binding: str
    owner: str
    g16_relevance: str
    later_requirement: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "item_id": self.item_id,
                "family": self.family,
                "status": self.status.value,
                "current_binding": self.current_binding,
                "owner": self.owner,
                "g16_relevance": self.g16_relevance,
                "later_requirement": self.later_requirement,
            }
        )


@dataclass(frozen=True)
class FundingDimensionRowV1:
    dimension_id: str
    current_producer: str
    current_consumer: str
    current_runtime_reachability: str
    current_authority_effect: str
    current_accounting_effect: str
    current_evidence: str
    current_tests: str
    claim_allowed_today: bool
    g16_relevance: str
    status: ContractItemStatus

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "dimension_id": self.dimension_id,
                "current_producer": self.current_producer,
                "current_consumer": self.current_consumer,
                "current_runtime_reachability": self.current_runtime_reachability,
                "current_authority_effect": self.current_authority_effect,
                "current_accounting_effect": self.current_accounting_effect,
                "current_evidence": self.current_evidence,
                "current_tests": self.current_tests,
                "claim_allowed_today": self.claim_allowed_today,
                "g16_relevance": self.g16_relevance,
                "status": self.status.value,
            }
        )
