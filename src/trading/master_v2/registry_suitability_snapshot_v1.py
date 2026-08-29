# src/trading/master_v2/registry_suitability_snapshot_v1.py
"""Deterministic Registry → Suitability snapshot for the restored Master-V2 path.

Reuses `build_registry_snapshot` and `build_suitability_registry_from_snapshot`.
Offline, no network, no secrets, no live/order authorization inference.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence, Tuple

from src.strategies.registry import StrategyRegistrySnapshotV1, build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import (
    build_suitability_registry_from_snapshot,
)
from trading.master_v2.strategy_identity_binding_v1 import (
    AUTH_001_POLICY_DECIDED,
    REASON_DUPLICATE_REGISTRY_IDENTITY,
    REASON_EMPTY_ELIGIBLE_STRATEGY_SET,
    REASON_EMPTY_REQUESTED_STRATEGY_SET,
    StrategyIdentityBindingError,
    auth_001_relation_for_ids_v1,
    bind_requested_strategy_ids_v1,
    bind_strategy_identity_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)

REGISTRY_SUITABILITY_SNAPSHOT_LAYER_VERSION = "v1"
REGISTRY_SUITABILITY_SNAPSHOT_OWNER = "trading.master_v2.registry_suitability_snapshot_v1"
METADATA_AUTHORIZATION_EFFECT = "NON_AUTHORIZING"
SNAPSHOT_SOURCE_REGISTRY_DERIVED_DEFAULT = "REGISTRY_DERIVED_DEFAULT"


class RegistrySuitabilitySnapshotError(ValueError):
    """Fail-closed Registry→Suitability snapshot error."""


@dataclass(frozen=True)
class RegistryDerivedSuitabilitySnapshotV1:
    """Immutable value-semantic envelope for Integrated Replay consumption."""

    layer_version: str
    source: str
    suitability_registry: SuitabilityStrategyRegistryV1
    strategy_ids_sorted: Tuple[str, ...]
    eligible_strategy_ids_sorted: Tuple[str, ...]
    consumed_strategy_ids: Tuple[str, ...]
    snapshot_digest: str
    registry_semantic_digest: str
    registry_input_digest: str
    auth_001_relation: str
    auth_001_policy_decided: bool
    production_or_live_ready_strategy_ids: Tuple[str, ...]
    metadata_authorization_effect: str
    live_authorized: bool
    orders_allowed: bool
    runtime_promoted: bool
    network_used: bool


def _stable_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _assert_unique_entry_ids(entries: Sequence[SuitabilityStrategyEntryV1]) -> None:
    seen: set[str] = set()
    for entry in entries:
        if entry.strategy_id in seen:
            raise RegistrySuitabilitySnapshotError(REASON_DUPLICATE_REGISTRY_IDENTITY)
        seen.add(entry.strategy_id)


def finalize_registry_suitability_snapshot_v1(
    suitability_registry: SuitabilityStrategyRegistryV1,
    *,
    registry_snapshot: StrategyRegistrySnapshotV1,
    consumed_strategy_ids: Tuple[str, ...],
    source: str = SNAPSHOT_SOURCE_REGISTRY_DERIVED_DEFAULT,
) -> RegistryDerivedSuitabilitySnapshotV1:
    entries = tuple(sorted(suitability_registry.entries, key=lambda item: item.strategy_id))
    _assert_unique_entry_ids(entries)
    ordered = SuitabilityStrategyRegistryV1(entries=entries)
    ids_sorted = tuple(item.strategy_id for item in entries)
    eligible = tuple(item.strategy_id for item in entries if not item.disabled)
    if not eligible:
        raise RegistrySuitabilitySnapshotError(REASON_EMPTY_ELIGIBLE_STRATEGY_SET)
    for sid in ids_sorted:
        bind_strategy_identity_v1(sid)
    production_or_live_ready = tuple(
        entry.strategy_id
        for entry in registry_snapshot.entries
        if entry.strategy_id in set(ids_sorted)
        and ("production" in entry.capability_tags or "live_ready" in entry.capability_tags)
    )
    digest = _stable_digest(
        {
            "auth_001_relation": auth_001_relation_for_ids_v1(ids_sorted),
            "consumed_strategy_ids": list(consumed_strategy_ids),
            "eligible_strategy_ids_sorted": list(eligible),
            "entries": [
                {
                    "disabled": entry.disabled,
                    "priority_rank": entry.priority_rank,
                    "strategy_id": entry.strategy_id,
                }
                for entry in entries
            ],
            "layer_version": REGISTRY_SUITABILITY_SNAPSHOT_LAYER_VERSION,
            "registry_input_digest": registry_snapshot.input_digest,
            "registry_semantic_digest": registry_snapshot.semantic_digest,
            "source": source,
        }
    )
    return RegistryDerivedSuitabilitySnapshotV1(
        layer_version=REGISTRY_SUITABILITY_SNAPSHOT_LAYER_VERSION,
        source=source,
        suitability_registry=ordered,
        strategy_ids_sorted=ids_sorted,
        eligible_strategy_ids_sorted=eligible,
        consumed_strategy_ids=consumed_strategy_ids,
        snapshot_digest=digest,
        registry_semantic_digest=registry_snapshot.semantic_digest,
        registry_input_digest=registry_snapshot.input_digest,
        auth_001_relation=auth_001_relation_for_ids_v1(ids_sorted),
        auth_001_policy_decided=AUTH_001_POLICY_DECIDED,
        production_or_live_ready_strategy_ids=production_or_live_ready,
        metadata_authorization_effect=METADATA_AUTHORIZATION_EFFECT,
        live_authorized=False,
        orders_allowed=False,
        runtime_promoted=False,
        network_used=False,
    )


def build_registry_derived_suitability_snapshot_v1(
    *,
    strategy_ids: Optional[Sequence[str]] = None,
    registry_snapshot: Optional[StrategyRegistrySnapshotV1] = None,
) -> RegistryDerivedSuitabilitySnapshotV1:
    """Build the default Registry→Suitability snapshot for current-system replay.

    ``strategy_ids=None`` includes the full catalog. An empty sequence fails closed.
    AUTH-001 identities may both appear as distinct entries; they are never equated.
    """
    snapshot = registry_snapshot if registry_snapshot is not None else build_registry_snapshot()
    full = build_suitability_registry_from_snapshot(snapshot)
    if strategy_ids is not None:
        requested = tuple(strategy_ids)
        if not requested:
            raise RegistrySuitabilitySnapshotError(REASON_EMPTY_REQUESTED_STRATEGY_SET)
        try:
            bindings = bind_requested_strategy_ids_v1(requested)
        except StrategyIdentityBindingError as exc:
            raise RegistrySuitabilitySnapshotError(str(exc)) from exc
        wanted = {item.canonical_strategy_id for item in bindings}
        filtered = tuple(entry for entry in full.entries if entry.strategy_id in wanted)
        consumed = tuple(item.canonical_strategy_id for item in bindings)
        return finalize_registry_suitability_snapshot_v1(
            SuitabilityStrategyRegistryV1(entries=filtered),
            registry_snapshot=snapshot,
            consumed_strategy_ids=consumed,
        )
    consumed = tuple(entry.strategy_id for entry in full.entries)
    return finalize_registry_suitability_snapshot_v1(
        full,
        registry_snapshot=snapshot,
        consumed_strategy_ids=consumed,
    )
