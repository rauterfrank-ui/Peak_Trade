"""Fail-closed models for R2 Strategy Registry / Suitability / Selection v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, Tuple


class StrategyRegistrySuitabilitySelectionError(ValueError):
    """Fail-closed R2 contract error."""


class SelectionIntent(str, Enum):
    CATALOG_ENUMERATE = "CATALOG_ENUMERATE"
    COMPOSITION_CANDIDATE = "COMPOSITION_CANDIDATE"
    RUNTIME_AUTHORITY = "RUNTIME_AUTHORITY"
    TRADING_ACTIVATE = "TRADING_ACTIVATE"
    PROMOTE = "PROMOTE"


class EligibilityStatus(str, Enum):
    CATALOGED_NON_AUTHORITY = "CATALOGED_NON_AUTHORITY"
    COMPOSITION_INPUT_ONLY = "COMPOSITION_INPUT_ONLY"
    AUTHORITY_OWNER_NOT_STRATEGY = "AUTHORITY_OWNER_NOT_STRATEGY"
    LEGACY_DEAUTHORIZED = "LEGACY_DEAUTHORIZED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class IdentityRecordV1:
    original_key: str
    canonical_strategy_id: str
    strategy_version: str
    alias_applied: bool
    reason_code: str
    identity_digest: str
    catalog_owner: str
    identity_owner: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "alias_applied": self.alias_applied,
                "canonical_strategy_id": self.canonical_strategy_id,
                "catalog_owner": self.catalog_owner,
                "identity_digest": self.identity_digest,
                "identity_owner": self.identity_owner,
                "original_key": self.original_key,
                "reason_code": self.reason_code,
                "strategy_version": self.strategy_version,
            }
        )


@dataclass(frozen=True)
class EligibilityRecordV1:
    strategy_id: str
    classification: str
    status: EligibilityStatus
    composition_eligible: bool
    runtime_authority_eligible: bool
    suitability_disabled: bool
    catalog_present: bool
    max_age_consulted: bool
    reason_code: str

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "catalog_present": self.catalog_present,
                "classification": self.classification,
                "composition_eligible": self.composition_eligible,
                "max_age_consulted": self.max_age_consulted,
                "reason_code": self.reason_code,
                "runtime_authority_eligible": self.runtime_authority_eligible,
                "status": self.status.value,
                "strategy_id": self.strategy_id,
                "suitability_disabled": self.suitability_disabled,
            }
        )


@dataclass(frozen=True)
class SelectionResultV1:
    intent: SelectionIntent
    requested_ids: Tuple[str, ...]
    resolved_ids: Tuple[str, ...]
    eligible_ids: Tuple[str, ...]
    selected_strategy_id: str | None
    classification_by_id: Mapping[str, str]
    selection_digest: str
    registry_semantic_digest: str
    suitability_snapshot_digest: str
    authority_effect: str
    trading_grant: bool
    runtime_effect: bool
    max_age_consulted: bool
    reason_codes: Tuple[str, ...]

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "authority_effect": self.authority_effect,
                "classification_by_id": dict(self.classification_by_id),
                "eligible_ids": list(self.eligible_ids),
                "intent": self.intent.value,
                "max_age_consulted": self.max_age_consulted,
                "reason_codes": list(self.reason_codes),
                "registry_semantic_digest": self.registry_semantic_digest,
                "requested_ids": list(self.requested_ids),
                "resolved_ids": list(self.resolved_ids),
                "runtime_effect": self.runtime_effect,
                "selected_strategy_id": self.selected_strategy_id,
                "selection_digest": self.selection_digest,
                "suitability_snapshot_digest": self.suitability_snapshot_digest,
                "trading_grant": self.trading_grant,
            }
        )
