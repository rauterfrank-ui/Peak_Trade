# src/trading/master_v2/strategy_identity_binding_v1.py
"""Fail-closed strategy identity binding for the restored Master-V2 / Double-Play path.

Reuses the canonical catalog owner `src.strategies.registry.resolve_strategy_id`.
This is not a second registry. The R2 identity package is not imported here: its
package ``__init__`` pulls suitability adapters that re-enter ``trading.master_v2``.

AUTH-001 (`ecm_cycle` vs `armstrong_cycle`) remains an unresolved Owner-policy
choice. Explicit canonical IDs bind independently. Nicknames, silent aliases, and
equivalence claims fail closed. This module never collapses the two identities.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from src.strategies.registry import StrategyRegistryError, resolve_strategy_id
from trading.master_v2.suitability_binding_v1 import SuitabilityStrategyRegistryV1

_CATALOG_OWNER = "src.strategies.registry"
_IDENTITY_OWNER = "src.strategies.registry.resolve_strategy_id"

STRATEGY_IDENTITY_BINDING_LAYER_VERSION = "v1"
STRATEGY_IDENTITY_BINDING_OWNER = "trading.master_v2.strategy_identity_binding_v1"

STRATEGY_IDENTITY_ENFORCEMENT_EXPLICIT_INJECTION = "EXPLICIT_INJECTION"
STRATEGY_IDENTITY_ENFORCEMENT_REGISTRY_DERIVED = "REGISTRY_DERIVED"

AUTH_001_POLICY_DECIDED = False
AUTH_001_CANONICAL_IDS: frozenset[str] = frozenset({"ecm_cycle", "armstrong_cycle"})
AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES = "UNRESOLVED_DISTINCT_IDENTITIES"
AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER = "UNRESOLVED_DISTINCT_PEER"
AUTH_001_RELATION_NOT_APPLICABLE = "NOT_APPLICABLE"

# Nicknames / collapsed tokens that cannot uniquely select AUTH-001 without policy.
AUTH_001_AMBIGUOUS_REQUESTS: frozenset[str] = frozenset(
    {
        "ecm",
        "armstrong",
        "ecm_armstrong",
        "armstrong_ecm",
        "ecm-armstrong",
        "armstrong-ecm",
        "ecm_or_armstrong",
        "armstrong_or_ecm",
        "ecm/armstrong",
        "armstrong/ecm",
        "ecm-cycle",
        "armstrong-cycle",
    }
)

REASON_UNKNOWN_STRATEGY_ID = "unknown_strategy_id"
REASON_AMBIGUOUS_STRATEGY_BINDING = "ambiguous_strategy_binding"
REASON_AUTH_001_UNRESOLVED_IDENTITY = "auth_001_unresolved_identity"
REASON_DUPLICATE_REGISTRY_IDENTITY = "duplicate_registry_identity"
REASON_EMPTY_ELIGIBLE_STRATEGY_SET = "empty_eligible_strategy_set"
REASON_EMPTY_REQUESTED_STRATEGY_SET = "empty_requested_strategy_set"


class StrategyIdentityBindingError(ValueError):
    """Fail-closed identity/binding error. Does not grant trading authority."""


@dataclass(frozen=True)
class StrategyIdentityBindingV1:
    requested_id: str
    canonical_strategy_id: str
    strategy_version: str
    alias_applied: bool
    reason_code: str
    identity_digest: str
    auth_001_relation: str
    catalog_owner: str
    identity_owner: str
    live_authorized: bool = False
    orders_allowed: bool = False
    runtime_promoted: bool = False


def _normalize_requested_id(requested_id: Optional[str]) -> str:
    if requested_id is None or not isinstance(requested_id, str):
        raise StrategyIdentityBindingError(REASON_UNKNOWN_STRATEGY_ID)
    if requested_id != requested_id.strip() or not requested_id.strip():
        raise StrategyIdentityBindingError(REASON_AMBIGUOUS_STRATEGY_BINDING)
    return requested_id


def bind_strategy_identity_v1(requested_id: Optional[str]) -> StrategyIdentityBindingV1:
    """Bind one explicit catalog identity. Never maps ECM↔Armstrong."""
    normalized = _normalize_requested_id(requested_id)
    if normalized in AUTH_001_AMBIGUOUS_REQUESTS:
        raise StrategyIdentityBindingError(REASON_AMBIGUOUS_STRATEGY_BINDING)
    try:
        resolution = resolve_strategy_id(normalized)
    except StrategyRegistryError as exc:
        raise StrategyIdentityBindingError(REASON_UNKNOWN_STRATEGY_ID) from exc
    if resolution.alias_applied and resolution.canonical_strategy_id in AUTH_001_CANONICAL_IDS:
        raise StrategyIdentityBindingError(REASON_AMBIGUOUS_STRATEGY_BINDING)
    if (
        resolution.canonical_strategy_id in AUTH_001_CANONICAL_IDS
        and resolution.canonical_strategy_id != normalized
    ):
        raise StrategyIdentityBindingError(REASON_AMBIGUOUS_STRATEGY_BINDING)
    relation = (
        AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER
        if resolution.canonical_strategy_id in AUTH_001_CANONICAL_IDS
        else AUTH_001_RELATION_NOT_APPLICABLE
    )
    identity_digest = hashlib.sha256(
        json.dumps(
            {
                "alias_applied": resolution.alias_applied,
                "canonical_strategy_id": resolution.canonical_strategy_id,
                "reason_code": resolution.reason_code,
                "strategy_version": resolution.strategy_version,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return StrategyIdentityBindingV1(
        requested_id=normalized,
        canonical_strategy_id=resolution.canonical_strategy_id,
        strategy_version=resolution.strategy_version,
        alias_applied=resolution.alias_applied,
        reason_code=resolution.reason_code,
        identity_digest=identity_digest,
        auth_001_relation=relation,
        catalog_owner=_CATALOG_OWNER,
        identity_owner=_IDENTITY_OWNER,
    )


def assert_auth_001_not_collapsed_v1(
    requested_ids: Sequence[str],
    *,
    treat_as_equivalent: bool = False,
) -> None:
    """Reject any attempt to treat ecm_cycle and armstrong_cycle as one Owner identity."""
    if treat_as_equivalent:
        raise StrategyIdentityBindingError(REASON_AUTH_001_UNRESOLVED_IDENTITY)
    lowered = {item.strip() for item in requested_ids if isinstance(item, str)}
    if AUTH_001_CANONICAL_IDS.issubset(lowered) and treat_as_equivalent:
        raise StrategyIdentityBindingError(REASON_AUTH_001_UNRESOLVED_IDENTITY)


def bind_requested_strategy_ids_v1(
    requested_ids: Sequence[str],
    *,
    treat_as_equivalent: bool = False,
) -> Tuple[StrategyIdentityBindingV1, ...]:
    """Bind an explicit requested set. Duplicate raw IDs fail closed. AUTH-001 stays distinct."""
    if treat_as_equivalent:
        raise StrategyIdentityBindingError(REASON_AUTH_001_UNRESOLVED_IDENTITY)
    requested = tuple(requested_ids)
    if not requested:
        raise StrategyIdentityBindingError(REASON_EMPTY_REQUESTED_STRATEGY_SET)
    if len(requested) != len(set(requested)):
        raise StrategyIdentityBindingError(REASON_DUPLICATE_REGISTRY_IDENTITY)
    stripped = tuple(item.strip() for item in requested)
    if stripped != requested or any(not item for item in requested):
        raise StrategyIdentityBindingError(REASON_AMBIGUOUS_STRATEGY_BINDING)
    bindings = tuple(bind_strategy_identity_v1(item) for item in requested)
    canonicals = tuple(item.canonical_strategy_id for item in bindings)
    if len(canonicals) != len(set(canonicals)):
        raise StrategyIdentityBindingError(REASON_DUPLICATE_REGISTRY_IDENTITY)
    return bindings


def auth_001_relation_for_ids_v1(canonical_ids: Iterable[str]) -> str:
    present = AUTH_001_CANONICAL_IDS.intersection(canonical_ids)
    if len(present) >= 2:
        return AUTH_001_RELATION_UNRESOLVED_DISTINCT_IDENTITIES
    if len(present) == 1:
        return AUTH_001_RELATION_UNRESOLVED_DISTINCT_PEER
    return AUTH_001_RELATION_NOT_APPLICABLE


def collect_suitability_identity_failures_v1(
    registry: SuitabilityStrategyRegistryV1,
) -> Tuple[str, ...]:
    """Return fail-closed reason codes for a suitability snapshot under REGISTRY_DERIVED."""
    reasons: list[str] = []
    seen: set[str] = set()
    for entry in registry.entries:
        sid = entry.strategy_id
        if sid in seen:
            reasons.append(REASON_DUPLICATE_REGISTRY_IDENTITY)
            continue
        seen.add(sid)
        try:
            bind_strategy_identity_v1(sid)
        except StrategyIdentityBindingError as exc:
            reasons.append(str(exc) or REASON_UNKNOWN_STRATEGY_ID)
    if len(reasons) != len(set(reasons)):
        reasons = list(dict.fromkeys(reasons))
    return tuple(reasons)
