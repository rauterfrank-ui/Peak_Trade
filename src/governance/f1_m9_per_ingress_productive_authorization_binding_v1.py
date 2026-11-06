"""F1/M9 per-ingress productive authorization binding v1 (typed dimensions, fail-closed).

Binds explicit authorization inputs to scoped join pair and ingress identity.
Does not authorize productive apply, promotion, or external effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    OwnerExplicitProductiveAuthorizationInputV1,
    compute_candidate_parameter_value_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    PRODUCTIVE_TARGET_ID,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    validate_optimization_proposal_governance_ingress_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    F1_M9_SCOPE_PAIR_ID,
    ScopedJoinResolutionStatusV1,
    ScopedOptimizationProductiveJoinScopeKeyV1,
    resolve_scoped_optimization_productive_join_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_per_ingress_productive_authorization_binding/v1"
BINDING_DOMAIN: Final[str] = "peak_trade.governance.f1_m9_per_ingress_authorization_binding.v1"

BINDING_DIMENSION_KEYS: Final[tuple[str, ...]] = (
    "schema_version",
    "scoped_join_pair_id",
    "surface_id",
    "productive_target_id",
    "ingress_digest",
    "experiment_id",
    "candidate_ref",
    "candidate_parameter_value_digest",
    "optimization_evidence_content_hash",
    "optimization_evidence_reproducibility_digest",
    "learning_evidence_digest",
    "owner_authorization_id",
    "owner_authorization_record_digest",
    "authorizer_identity",
    "risk_constraints_ref",
    "governance_risk_constraints_ref",
    "registry_digest",
    "binding_digest",
)


class PerIngressBindingStatusV1(str, Enum):
    BOUND = "BOUND"
    DENIED_FAIL_CLOSED = "DENIED_FAIL_CLOSED"


@dataclass(frozen=True, slots=True)
class PerIngressAuthorizationBindingV1:
    """Typed per-ingress binding record (digest-sealed)."""

    binding_record: Mapping[str, Any]
    binding_digest: str
    status: PerIngressBindingStatusV1
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_digest": self.binding_digest,
            "binding_record": dict(self.binding_record),
            "reason_codes": list(self.reason_codes),
            "status": self.status.value,
        }


def build_per_ingress_binding_body_v1(
    *,
    ingress: Mapping[str, Any],
    owner_input: OwnerExplicitProductiveAuthorizationInputV1,
    registry_digest: str,
    scoped_join_pair_id: str = F1_M9_SCOPE_PAIR_ID,
) -> MappingProxyType[str, Any]:
    validated = validate_optimization_proposal_governance_ingress_v1(ingress)
    delta = dict(validated["parameter_config_delta"])
    owner_record = owner_input.owner_authorization_record
    body = {
        "schema_version": SCHEMA_VERSION,
        "scoped_join_pair_id": scoped_join_pair_id,
        "surface_id": str(validated["optimization_surface_id"]),
        "productive_target_id": PRODUCTIVE_TARGET_ID,
        "ingress_digest": str(validated["ingress_digest"]),
        "experiment_id": str(validated["experiment_id"]),
        "candidate_ref": str(validated["candidate_ref"]),
        "candidate_parameter_value_digest": compute_candidate_parameter_value_digest_v1(delta),
        "optimization_evidence_content_hash": str(validated["optimization_evidence_content_hash"]),
        "optimization_evidence_reproducibility_digest": str(
            validated["optimization_evidence_reproducibility_digest"]
        ),
        "learning_evidence_digest": str(validated["learning_evidence_digest"]),
        "owner_authorization_id": str(owner_record.get("owner_authorization_id") or ""),
        "owner_authorization_record_digest": owner_input.owner_authorization_record_digest,
        "authorizer_identity": str(owner_record.get("authorizer_identity") or ""),
        "risk_constraints_ref": str(validated["risk_constraints_ref"]),
        "governance_risk_constraints_ref": str(validated["governance_risk_constraints_ref"]),
        "registry_digest": registry_digest,
    }
    missing = [key for key in BINDING_DIMENSION_KEYS if key != "binding_digest" and key not in body]
    if missing:
        raise ValueError(f"BINDING_BODY_INCOMPLETE:{','.join(missing)}")
    return MappingProxyType(body)


def compute_per_ingress_binding_digest_v1(binding_body: Mapping[str, Any]) -> str:
    sealed = {key: binding_body[key] for key in BINDING_DIMENSION_KEYS if key != "binding_digest"}
    return compute_content_sha256(sealed)


def verify_per_ingress_binding_digest_v1(binding_record: Mapping[str, Any]) -> bool:
    stored = binding_record.get("binding_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    body = {
        key: binding_record[key]
        for key in BINDING_DIMENSION_KEYS
        if key != "binding_digest" and key in binding_record
    }
    return compute_content_sha256(body) == stored


def evaluate_f1_m9_per_ingress_authorization_binding_v1(
    *,
    ingress: Mapping[str, Any],
    owner_input: OwnerExplicitProductiveAuthorizationInputV1,
    registry_digest: str,
    expected_surface_id: str = OPTIMIZATION_SURFACE_ID,
    expected_productive_target_id: str = PRODUCTIVE_TARGET_ID,
) -> PerIngressAuthorizationBindingV1:
    """Fail-closed binding: scoped join + dimension alignment; no apply authority."""
    reason_codes: list[str] = []
    scope_key = ScopedOptimizationProductiveJoinScopeKeyV1(
        surface_id=expected_surface_id,
        productive_target_id=expected_productive_target_id,
    )
    scoped = resolve_scoped_optimization_productive_join_v1(
        scope_key,
        expected_registry_digest=registry_digest,
    )
    if scoped.status != ScopedJoinResolutionStatusV1.SCOPED_JOIN_AUTHORIZED:
        reason_codes.append(f"SCOPED_JOIN_NOT_AUTHORIZED:{scoped.status.value}")
    if scoped.scope_pair_id != F1_M9_SCOPE_PAIR_ID:
        reason_codes.append("SCOPED_JOIN_PAIR_ID_MISMATCH")

    try:
        validated = validate_optimization_proposal_governance_ingress_v1(ingress)
    except Exception as exc:
        reason_codes.append(str(exc))
        return PerIngressAuthorizationBindingV1(
            binding_record={},
            binding_digest="",
            status=PerIngressBindingStatusV1.DENIED_FAIL_CLOSED,
            reason_codes=tuple(reason_codes),
        )

    ingress_digest = str(validated["ingress_digest"])
    if str(validated["optimization_surface_id"]) != expected_surface_id:
        reason_codes.append("SURFACE_ID_MISMATCH")
    if owner_input.owner_authorization_record.get("bound_ingress_digest") != ingress_digest:
        reason_codes.append("OWNER_INGRESS_DIGEST_MISMATCH")

    body = dict(
        build_per_ingress_binding_body_v1(
            ingress=ingress,
            owner_input=owner_input,
            registry_digest=registry_digest,
            scoped_join_pair_id=scoped.scope_pair_id or F1_M9_SCOPE_PAIR_ID,
        )
    )
    digest = compute_per_ingress_binding_digest_v1(body)
    body["binding_digest"] = digest

    if reason_codes:
        return PerIngressAuthorizationBindingV1(
            binding_record=body,
            binding_digest=digest,
            status=PerIngressBindingStatusV1.DENIED_FAIL_CLOSED,
            reason_codes=tuple(reason_codes),
        )

    return PerIngressAuthorizationBindingV1(
        binding_record=body,
        binding_digest=digest,
        status=PerIngressBindingStatusV1.BOUND,
        reason_codes=("PER_INGRESS_BINDING_OK",),
    )


__all__ = [
    "BINDING_DIMENSION_KEYS",
    "BINDING_DOMAIN",
    "PerIngressAuthorizationBindingV1",
    "PerIngressBindingStatusV1",
    "SCHEMA_VERSION",
    "build_per_ingress_binding_body_v1",
    "compute_per_ingress_binding_digest_v1",
    "evaluate_f1_m9_per_ingress_authorization_binding_v1",
    "verify_per_ingress_binding_digest_v1",
]
