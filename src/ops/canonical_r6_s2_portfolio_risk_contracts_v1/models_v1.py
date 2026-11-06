"""Fail-closed models for R6 S2 portfolio-risk contracts v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class R6S2PortfolioRiskError(ValueError):
    """Fail-closed R6 S2 portfolio-risk contract error."""


class ContractItemStatus(str, Enum):
    CLOSED_PROVEN = "CLOSED_PROVEN"
    CLOSED_BOUNDARY = "CLOSED_BOUNDARY"
    PARTIAL = "PARTIAL"
    IMPLEMENTED_NOT_PROVEN = "IMPLEMENTED_NOT_PROVEN"
    PLANNED_ONLY = "PLANNED_ONLY"
    MISSING_CONTRACT = "MISSING_CONTRACT"
    BLOCKED_BY_S3_IMPLEMENTATION = "BLOCKED_BY_S3_IMPLEMENTATION"
    BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF = "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF"
    BLOCKED_BY_SEPARATE_OWNER_GO = "BLOCKED_BY_SEPARATE_OWNER_GO"
    NOT_REQUIRED_AT_S2 = "NOT_REQUIRED_AT_S2"


S2_CLOSABLE_STATUSES = frozenset(
    {
        ContractItemStatus.CLOSED_PROVEN,
        ContractItemStatus.CLOSED_BOUNDARY,
        ContractItemStatus.NOT_REQUIRED_AT_S2,
    }
)


@dataclass(frozen=True)
class ContractDimensionRowV1:
    item_id: str
    family: str
    status: ContractItemStatus
    current_binding: str
    owner: str
    reuse_candidate: str
    later_requirement: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "item_id": self.item_id,
                "family": self.family,
                "status": self.status.value,
                "current_binding": self.current_binding,
                "owner": self.owner,
                "reuse_candidate": self.reuse_candidate,
                "later_requirement": self.later_requirement,
            }
        )


@dataclass(frozen=True)
class IntentForensicRowV1:
    intent_id: str
    current_state: str
    current_runtime_reachability: str
    current_authority_effect: str
    current_callers: str
    current_config: str
    current_tests: str
    current_evidence: str
    canonical_owner: str
    duplicate_authority_risk: str
    long_term_role: str
    s2_requirement: str
    s2_gap: str
    implementation_required_later: str
    safe_to_bind_read_only: bool

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "intent_id": self.intent_id,
                "current_state": self.current_state,
                "current_runtime_reachability": self.current_runtime_reachability,
                "current_authority_effect": self.current_authority_effect,
                "current_callers": self.current_callers,
                "current_config": self.current_config,
                "current_tests": self.current_tests,
                "current_evidence": self.current_evidence,
                "canonical_owner": self.canonical_owner,
                "duplicate_authority_risk": self.duplicate_authority_risk,
                "long_term_role": self.long_term_role,
                "s2_requirement": self.s2_requirement,
                "s2_gap": self.s2_gap,
                "implementation_required_later": self.implementation_required_later,
                "safe_to_bind_read_only": self.safe_to_bind_read_only,
            }
        )
