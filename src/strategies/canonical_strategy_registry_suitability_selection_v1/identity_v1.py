"""Canonical strategy identity — reuse-only wrapper over src.strategies.registry."""

from __future__ import annotations

from src.strategies.canonical_strategy_registry_suitability_selection_v1.constants_v1 import (
    CATALOG_OWNER,
    IDENTITY_OWNER,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.lineage_v1 import (
    envelope_digest,
)
from src.strategies.canonical_strategy_registry_suitability_selection_v1.models_v1 import (
    IdentityRecordV1,
    StrategyRegistrySuitabilitySelectionError,
)
from src.strategies.registry import StrategyRegistryError, resolve_strategy_id


def resolve_canonical_identity_v1(raw_key: str | None) -> IdentityRecordV1:
    """Fail-closed identity resolution. Does not grant trading or promotion."""
    try:
        resolution = resolve_strategy_id(raw_key)
    except StrategyRegistryError as exc:
        raise StrategyRegistrySuitabilitySelectionError(
            f"unknown_or_invalid_strategy_id:{raw_key!r}:{exc}"
        ) from exc
    digest = envelope_digest(
        kind="strategy_identity_v1",
        payload={
            "alias_applied": resolution.alias_applied,
            "canonical_strategy_id": resolution.canonical_strategy_id,
            "reason_code": resolution.reason_code,
            "strategy_version": resolution.strategy_version,
        },
    )
    return IdentityRecordV1(
        original_key=resolution.original_key,
        canonical_strategy_id=resolution.canonical_strategy_id,
        strategy_version=resolution.strategy_version,
        alias_applied=resolution.alias_applied,
        reason_code=resolution.reason_code,
        identity_digest=digest,
        catalog_owner=CATALOG_OWNER,
        identity_owner=IDENTITY_OWNER,
    )


def assert_unique_requested_ids_v1(requested_ids: tuple[str, ...]) -> None:
    if len(requested_ids) != len(set(requested_ids)):
        raise StrategyRegistrySuitabilitySelectionError("duplicate_requested_strategy_id")
    stripped = tuple(item.strip() for item in requested_ids)
    if stripped != requested_ids:
        raise StrategyRegistrySuitabilitySelectionError("strategy_id_whitespace_ambiguity")
    if any(not item for item in requested_ids):
        raise StrategyRegistrySuitabilitySelectionError("empty_requested_strategy_id")
