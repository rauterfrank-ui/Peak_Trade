"""Fail-closed models for R6 Phase-8.1 policy precondition v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class R6Phase81PolicyError(ValueError):
    """Fail-closed R6 Phase-8.1 policy precondition error."""


class PolicyItemStatus(str, Enum):
    CLOSED_PROVEN = "CLOSED_PROVEN"
    PARTIAL = "PARTIAL"
    IMPLEMENTED_NOT_PROVEN = "IMPLEMENTED_NOT_PROVEN"
    PLANNED_ONLY = "PLANNED_ONLY"
    BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF = "BLOCKED_BY_SINGLE_FUTURE_LIVE_PROOF"
    BLOCKED_BY_SEPARATE_OWNER_GO = "BLOCKED_BY_SEPARATE_OWNER_GO"
    NOT_REQUIRED_AT_THIS_STAGE = "NOT_REQUIRED_AT_THIS_STAGE"


@dataclass(frozen=True)
class PolicyChecklistRowV1:
    item_id: str
    status: PolicyItemStatus
    current_binding: str
    owner: str
    mf_expansion: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "item_id": self.item_id,
                "status": self.status.value,
                "current_binding": self.current_binding,
                "owner": self.owner,
                "mf_expansion": self.mf_expansion,
            }
        )
