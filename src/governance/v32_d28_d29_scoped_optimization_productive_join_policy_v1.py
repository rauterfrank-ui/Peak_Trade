"""V32 D28/D29 scoped optimization productive join policy v1 (F1/M9).

Typed fail-closed registry and resolver for (surface_id, productive_target_id) pairs.
Does not flip optimization_universe_join_authorized, authorize apply/promotion, or write runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_M9_SURFACE_ID,
)
from src.governance.explicit_productive_authorization_v1 import AUTHORIZED_FOR_PRODUCTIVE_APPLY
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    JOIN_OWNER as RUNTIME_SEAM_JOIN_OWNER,
    optimization_can_direct_write_runtime_seam_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)

SCHEMA_VERSION: Final[str] = "v32_d28_d29_scoped_optimization_productive_join_policy_v1"
WORKPACKAGE_ID: Final[str] = "V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/V32_D28_D29_SCOPED_OPTIMIZATION_PRODUCTIVE_JOIN_F1_M9_MAX_BUILD_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/"
    "v32_d28_d29_scoped_optimization_productive_join_f1_m9_owner_policy_v1_decision_v1.json"
)
REGISTRY_CONFIG: Final[str] = (
    "config/governance/v32_d28_d29_scoped_optimization_productive_join_registry_v1.json"
)
LEARNING_CLOSED_LOOP_DECISION: Final[str] = (
    "config/governance/learning_outcome_evidence_ingest_and_state_decision_v1.json"
)

GLOBAL_JOIN_BOOLEAN_ROLE: Final[str] = "LEGACY_COMPATIBILITY_ONLY_NOT_PRODUCTIVE_AUTHORITY"
AUTHORITY_EFFECT: Final[str] = "SCOPED_POLICY_ONLY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
TRADING_DECISION_AUTHORITY_CHANGED: Final[bool] = False

F1_M9_SCOPE_PAIR_ID: Final[str] = "F1-M9-VOLATILITY-MAX-AGE-SECONDS"

_REPO_ROOT = Path(__file__).resolve().parents[2]


class ScopedJoinResolutionStatusV1(str, Enum):
    SCOPED_JOIN_AUTHORIZED = "SCOPED_JOIN_AUTHORIZED"
    SCOPED_JOIN_DENIED_FAIL_CLOSED = "SCOPED_JOIN_DENIED_FAIL_CLOSED"
    SCOPED_JOIN_UNKNOWN_FAIL_CLOSED = "SCOPED_JOIN_UNKNOWN_FAIL_CLOSED"


class GlobalJoinBooleanStatusV1(str, Enum):
    LEGACY_COMPATIBILITY_ONLY_UNCHANGED = "LEGACY_COMPATIBILITY_ONLY_UNCHANGED"


@dataclass(frozen=True, slots=True)
class ScopedOptimizationProductiveJoinScopeKeyV1:
    surface_id: str
    productive_target_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "surface_id": self.surface_id,
            "productive_target_id": self.productive_target_id,
        }


@dataclass(frozen=True, slots=True)
class ScopedJoinRegistryEntryV1:
    scope_pair_id: str
    surface_id: str
    productive_target_id: str
    authorization_status: str
    family: str
    lineage: Mapping[str, str]
    evidence_refs: tuple[str, ...]
    owner_policy_ref: str
    registry_policy_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_status": self.authorization_status,
            "evidence_refs": list(self.evidence_refs),
            "family": self.family,
            "lineage": dict(self.lineage),
            "owner_policy_ref": self.owner_policy_ref,
            "productive_target_id": self.productive_target_id,
            "registry_policy_version": self.registry_policy_version,
            "scope_pair_id": self.scope_pair_id,
            "surface_id": self.surface_id,
        }


@dataclass(frozen=True, slots=True)
class ScopedJoinResolutionResultV1:
    status: ScopedJoinResolutionStatusV1
    reason_codes: tuple[str, ...]
    scope_key: ScopedOptimizationProductiveJoinScopeKeyV1
    scope_pair_id: str | None
    registry_digest: str | None
    lineage_refs: Mapping[str, str] | None
    authority_effect: str = AUTHORITY_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "lineage_refs": dict(self.lineage_refs) if self.lineage_refs else None,
            "reason_codes": list(self.reason_codes),
            "registry_digest": self.registry_digest,
            "scope_key": self.scope_key.to_dict(),
            "scope_pair_id": self.scope_pair_id,
            "status": self.status.value,
        }


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def build_canonical_f1_m9_scope_key_v1() -> ScopedOptimizationProductiveJoinScopeKeyV1:
    if F1_M9_SURFACE_ID != OPTIMIZATION_SURFACE_ID:
        raise ValueError("F1_M9_SURFACE_ID_MISMATCH")
    return ScopedOptimizationProductiveJoinScopeKeyV1(
        surface_id=OPTIMIZATION_SURFACE_ID,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )


def compute_scoped_join_registry_digest_v1(
    registry: Mapping[str, Any], *, exclude_keys: tuple[str, ...] = ("registry_digest",)
) -> str:
    body = {k: v for k, v in registry.items() if k not in exclude_keys}
    return compute_content_sha256(body)


def load_scoped_join_registry_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = repo_root or _REPO_ROOT
    registry = _load_json(root, REGISTRY_CONFIG)
    digest = compute_scoped_join_registry_digest_v1(registry)
    return MappingProxyType(
        {
            **registry,
            "registry_digest": digest,
        }
    )


def _parse_registry_entries(registry: Mapping[str, Any]) -> tuple[ScopedJoinRegistryEntryV1, ...]:
    entries: list[ScopedJoinRegistryEntryV1] = []
    for raw in registry.get("entries", []):
        lineage = raw.get("lineage") or {}
        entries.append(
            ScopedJoinRegistryEntryV1(
                scope_pair_id=str(raw["scope_pair_id"]),
                surface_id=str(raw["surface_id"]),
                productive_target_id=str(raw["productive_target_id"]),
                authorization_status=str(raw["authorization_status"]),
                family=str(raw["family"]),
                lineage=MappingProxyType({str(k): str(v) for k, v in lineage.items()}),
                evidence_refs=tuple(str(x) for x in raw.get("evidence_refs", ())),
                owner_policy_ref=str(raw["owner_policy_ref"]),
                registry_policy_version=str(raw["registry_policy_version"]),
            )
        )
    return tuple(entries)


def _validate_f1_m9_lineage(entry: ScopedJoinRegistryEntryV1) -> list[str]:
    reasons: list[str] = []
    expected_surface = OPTIMIZATION_SURFACE_ID
    expected_target = PRODUCTIVE_TARGET_ID
    if entry.surface_id != expected_surface:
        reasons.append("SURFACE_ID_NOT_F1_M9_CANONICAL")
    if entry.productive_target_id != expected_target:
        reasons.append("PRODUCTIVE_TARGET_ID_NOT_F1_M9_CANONICAL")
    if entry.authorization_status != ScopedJoinResolutionStatusV1.SCOPED_JOIN_AUTHORIZED.value:
        reasons.append("REGISTRY_STATUS_NOT_AUTHORIZED")
    consumer = entry.lineage.get("productive_consumer")
    if consumer != POLICY_CONSUMER_MODULE:
        reasons.append("PRODUCTIVE_CONSUMER_MISMATCH")
    runtime_join = entry.lineage.get("runtime_seam_join_owner")
    if runtime_join != RUNTIME_SEAM_JOIN_OWNER:
        reasons.append("RUNTIME_SEAM_JOIN_OWNER_MISMATCH")
    return reasons


def adjudicate_global_optimization_universe_join_boolean_v1(
    *, learning_decision_value: bool | None
) -> Mapping[str, Any]:
    """Global boolean is not productive join authority; scoped registry is SSOT for pairs."""
    return MappingProxyType(
        {
            "global_join_boolean_status": GlobalJoinBooleanStatusV1.LEGACY_COMPATIBILITY_ONLY_UNCHANGED.value,
            "global_join_boolean_role": GLOBAL_JOIN_BOOLEAN_ROLE,
            "learning_decision_value": learning_decision_value,
            "may_derive_scoped_productive_join_authority": False,
            "scoped_registry_is_pair_authority_ssot": True,
        }
    )


def resolve_scoped_optimization_productive_join_v1(
    scope_key: ScopedOptimizationProductiveJoinScopeKeyV1,
    *,
    registry: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
    expected_registry_digest: str | None = None,
) -> ScopedJoinResolutionResultV1:
    root = repo_root or _REPO_ROOT
    reg = dict(registry or load_scoped_join_registry_v1(repo_root=root))
    digest = str(reg.get("registry_digest", ""))
    if expected_registry_digest is not None:
        if not is_valid_sha256_hex(expected_registry_digest):
            return ScopedJoinResolutionResultV1(
                status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED,
                reason_codes=("EXPECTED_REGISTRY_DIGEST_INVALID",),
                scope_key=scope_key,
                scope_pair_id=None,
                registry_digest=digest or None,
                lineage_refs=None,
            )
        if digest != expected_registry_digest:
            return ScopedJoinResolutionResultV1(
                status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED,
                reason_codes=("REGISTRY_DIGEST_MISMATCH",),
                scope_key=scope_key,
                scope_pair_id=None,
                registry_digest=digest,
                lineage_refs=None,
            )

    if scope_key.surface_id in {F2_SURFACE_ID, F5_FRESH_SURFACE_ID}:
        return ScopedJoinResolutionResultV1(
            status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED,
            reason_codes=("FAMILY_F2_OR_F5_PRODUCTIVE_JOIN_FORBIDDEN",),
            scope_key=scope_key,
            scope_pair_id=None,
            registry_digest=digest,
            lineage_refs=None,
        )

    entries = _parse_registry_entries(reg)
    for entry in entries:
        if (
            entry.surface_id == scope_key.surface_id
            and entry.productive_target_id == scope_key.productive_target_id
        ):
            lineage_reasons = _validate_f1_m9_lineage(entry)
            if lineage_reasons:
                return ScopedJoinResolutionResultV1(
                    status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED,
                    reason_codes=tuple(lineage_reasons),
                    scope_key=scope_key,
                    scope_pair_id=entry.scope_pair_id,
                    registry_digest=digest,
                    lineage_refs=entry.lineage,
                )
            return ScopedJoinResolutionResultV1(
                status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_AUTHORIZED,
                reason_codes=("SCOPED_PAIR_REGISTRY_HIT", "F1_M9_LINEAGE_REFS_OK"),
                scope_key=scope_key,
                scope_pair_id=entry.scope_pair_id,
                registry_digest=digest,
                lineage_refs=entry.lineage,
            )

    if scope_key.surface_id == OPTIMIZATION_SURFACE_ID:
        return ScopedJoinResolutionResultV1(
            status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED,
            reason_codes=("M9_SURFACE_TARGET_PAIR_NOT_IN_REGISTRY",),
            scope_key=scope_key,
            scope_pair_id=None,
            registry_digest=digest,
            lineage_refs=None,
        )

    return ScopedJoinResolutionResultV1(
        status=ScopedJoinResolutionStatusV1.SCOPED_JOIN_UNKNOWN_FAIL_CLOSED,
        reason_codes=("UNKNOWN_SURFACE_OR_TARGET_PAIR",),
        scope_key=scope_key,
        scope_pair_id=None,
        registry_digest=digest,
        lineage_refs=None,
    )


def build_denied_scope_isolation_catalog_v1() -> Mapping[str, tuple[str, ...]]:
    return MappingProxyType(
        {
            "F2": (F2_SURFACE_ID,),
            "F5-FRESH": (F5_FRESH_SURFACE_ID,),
        }
    )


def prove_scoped_join_policy_invariants_v1(*, repo_root: Path | None = None) -> bool:
    root = repo_root or _REPO_ROOT
    if int(PRODUCTIVE_NUMERIC_VALUES_SET) != 0:
        return False
    if AUTHORIZED_FOR_PRODUCTIVE_APPLY is not False:
        return False
    if optimization_can_direct_write_runtime_seam_v1() is not False:
        return False
    if OPTIMIZATION_CAN_WRITE_PRODUCTIVE_CONFIG is not False:
        return False
    learning = _load_json(root, LEARNING_CLOSED_LOOP_DECISION)
    if learning.get("optimization_universe_join_authorized") is not False:
        return False
    adjudication = adjudicate_global_optimization_universe_join_boolean_v1(
        learning_decision_value=learning.get("optimization_universe_join_authorized")
    )
    if adjudication["may_derive_scoped_productive_join_authority"] is not False:
        return False
    registry = load_scoped_join_registry_v1(repo_root=root)
    if registry.get("global_optimization_universe_join_boolean_role") != GLOBAL_JOIN_BOOLEAN_ROLE:
        return False
    key = build_canonical_f1_m9_scope_key_v1()
    resolved = resolve_scoped_optimization_productive_join_v1(
        key, registry=registry, repo_root=root
    )
    if resolved.status != ScopedJoinResolutionStatusV1.SCOPED_JOIN_AUTHORIZED:
        return False
    wrong_target = ScopedOptimizationProductiveJoinScopeKeyV1(
        surface_id=OPTIMIZATION_SURFACE_ID,
        productive_target_id="peak_trade.governance.productive_target.unknown/v1",
    )
    denied = resolve_scoped_optimization_productive_join_v1(
        wrong_target, registry=registry, repo_root=root
    )
    if denied.status != ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED:
        return False
    f2_denied = resolve_scoped_optimization_productive_join_v1(
        ScopedOptimizationProductiveJoinScopeKeyV1(
            surface_id=F2_SURFACE_ID,
            productive_target_id=PRODUCTIVE_TARGET_ID,
        ),
        registry=registry,
        repo_root=root,
    )
    if f2_denied.status != ScopedJoinResolutionStatusV1.SCOPED_JOIN_DENIED_FAIL_CLOSED:
        return False
    return True


__all__ = [
    "AUTHORITY_EFFECT",
    "DECISION_CONFIG",
    "F1_M9_SCOPE_PAIR_ID",
    "GLOBAL_JOIN_BOOLEAN_ROLE",
    "GlobalJoinBooleanStatusV1",
    "NORMATIVE_SPEC",
    "REGISTRY_CONFIG",
    "SCHEMA_VERSION",
    "ScopedJoinRegistryEntryV1",
    "ScopedJoinResolutionResultV1",
    "ScopedJoinResolutionStatusV1",
    "ScopedOptimizationProductiveJoinScopeKeyV1",
    "TRADING_DECISION_AUTHORITY_CHANGED",
    "WORKPACKAGE_ID",
    "adjudicate_global_optimization_universe_join_boolean_v1",
    "build_canonical_f1_m9_scope_key_v1",
    "build_denied_scope_isolation_catalog_v1",
    "compute_scoped_join_registry_digest_v1",
    "load_scoped_join_registry_v1",
    "prove_scoped_join_policy_invariants_v1",
    "resolve_scoped_optimization_productive_join_v1",
]
