"""Optimization universe v1 foundation (identity + research capability registry).

Establishes versioned optimization-universe identity and a fail-closed registry of
research-only capabilities. Integrates the M1 learning-input boundary validator.
Does not define optimizable envelopes, productive targets, search, or promotion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    OPTIMIZATION_LEARNING_INPUT_DOMAIN,
    SCHEMA_VERSION as LEARNING_INPUT_SCHEMA_VERSION,
    CanonicalOptimizationUniverseLearningInputError,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    authorized_productive_target_ids_v1,
    zero_authorized_productive_targets_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_optimization_universe_v1"
OPTIMIZATION_UNIVERSE_DOMAIN: Final[str] = "peak_trade.canonical_optimization_universe.v1"
CAPABILITY_REGISTRY_VERSION: Final[str] = "optimization_universe_capability_registry_v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
UNIVERSE_CLASS: Final[str] = "OPTIMIZATION_UNIVERSE"

BOUNDARY_NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/META_LEARNING_OPTIMIZATION_UNIVERSE_BOUNDARY_AND_LEARNING_EVIDENCE_EXPORT_NORMATIVE_V1.md"
)
FOUNDATION_NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/META_LEARNING_OPTIMIZATION_UNIVERSE_FOUNDATION_NORMATIVE_V1.md"
)
FOUNDATION_DECISION_CONFIG: Final[str] = (
    "config/governance/meta_learning_optimization_universe_foundation_decision_v1.json"
)

CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE: Final[str] = "RESEARCH_EVIDENCE_REUSE"
CAPABILITY_CLASS_OPTIMIZATION_INPUT_BOUNDARY: Final[str] = "OPTIMIZATION_INPUT_BOUNDARY"

OPTIMIZATION_UNIVERSE_PRESENT: Final[bool] = True
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_HAS_RUNTIME_AUTHORITY: Final[bool] = False
OPTIMIZATION_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
OPTIMIZATION_CAN_PROMOTE: Final[bool] = False
OPTIMIZATION_CAN_SUBMIT_ORDER: Final[bool] = False
OPTIMIZATION_CAN_DEFINE_OPTIMIZABLE_ENVELOPE: Final[bool] = False
OPTIMIZATION_CAN_TRIGGER_SEARCH: Final[bool] = False
OPTIMIZABLE_ENVELOPE_CONTRACT_PRESENT: Final[bool] = True
OPTIMIZABLE_ENVELOPE_DEFINED: Final[bool] = False
OPTIMIZABLE_ENVELOPE_REF: Final[str] = "peak_trade.canonical_optimizable_envelope.v1"
ZERO_AUTHORIZED_PRODUCTIVE_TARGETS: Final[bool] = zero_authorized_productive_targets_v1()
UNIVERSE_MEMBERSHIP_IMPLIES_OPTIMIZATION_AUTHORIZATION: Final[bool] = False
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True
NO_SELF_DEPLOY: Final[bool] = True

STATUS_FOUNDATION_OK: Final[str] = "OPTIMIZATION_UNIVERSE_FOUNDATION_OK"
STATUS_ACCEPTED_REGISTERED_RESEARCH_CAPABILITY: Final[str] = (
    "ACCEPTED_REGISTERED_RESEARCH_CAPABILITY"
)
STATUS_REJECTED_UNREGISTERED_CAPABILITY: Final[str] = "REJECTED_UNREGISTERED_CAPABILITY"
STATUS_REJECTED_AUTHORITY_BOUNDARY: Final[str] = "REJECTED_AUTHORITY_BOUNDARY"
STATUS_REJECTED_STALE_INPUT_CONTRACT: Final[str] = "REJECTED_STALE_INPUT_CONTRACT"

_LOGGER = logging.getLogger(__name__)

_AUTHORIZED_PRODUCTIVE_TARGETS: Final[frozenset[str]] = frozenset()

_REGISTRY_ENTRIES: Final[tuple[MappingProxyType[str, Any], ...]] = (
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_experiment_identity.v1",
            "owner_module": "src.experiments.canonical_experiment_identity_v1",
            "schema_version": "canonical_experiment_identity_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_experiment_memory.v1",
            "owner_module": "src.experiments.canonical_experiment_memory_v1",
            "schema_version": "canonical_experiment_memory_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_failure_memory.v1",
            "owner_module": "src.experiments.canonical_failure_memory_v1",
            "schema_version": "canonical_failure_memory_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_comparison_ssot.v1",
            "owner_module": "src.experiments.canonical_comparison_ssot_v1",
            "schema_version": "canonical_comparison_ssot_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_reality_gap_store.v1",
            "owner_module": "src.experiments.canonical_reality_gap_store_v1",
            "schema_version": "canonical_reality_gap_store_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_robustness_suite.v1",
            "owner_module": "src.experiments.canonical_robustness_suite_v1",
            "schema_version": "canonical_robustness_suite_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": "peak_trade.canonical_meta_learning.v1",
            "owner_module": "src.experiments.canonical_meta_learning_v1",
            "schema_version": "canonical_meta_learning_v1",
            "capability_class": CAPABILITY_CLASS_RESEARCH_EVIDENCE_REUSE,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
    MappingProxyType(
        {
            "capability_id": OPTIMIZATION_LEARNING_INPUT_DOMAIN,
            "owner_module": "src.experiments.canonical_optimization_universe_learning_input_v1",
            "schema_version": LEARNING_INPUT_SCHEMA_VERSION,
            "capability_class": CAPABILITY_CLASS_OPTIMIZATION_INPUT_BOUNDARY,
            "productive_authority": "NONE",
            "runtime_reachability": False,
        }
    ),
)


class CanonicalOptimizationUniverseError(ValueError):
    """Fail-closed malformed optimization-universe request."""


@dataclass(frozen=True)
class CanonicalOptimizationUniverseRequestV1:
    capability_id: str | None = None
    learning_evidence: Mapping[str, Any] | None = None
    learning_input_schema_version: str | None = None
    requested_productive_target: str | None = None
    requested_envelope_authorization: bool = False
    requested_productive_join: bool = False
    requested_auto_search: bool = False


def _registry_entry_for_digest(entry: Mapping[str, Any]) -> dict[str, Any]:
    return {key: entry[key] for key in sorted(entry.keys(), key=lambda item: str(item))}


def build_optimization_universe_capability_registry_v1() -> MappingProxyType[str, Any]:
    by_id = {str(entry["capability_id"]): entry for entry in _REGISTRY_ENTRIES}
    registry_body = {
        "capability_registry_version": CAPABILITY_REGISTRY_VERSION,
        "entries": tuple(
            _registry_entry_for_digest(by_id[key])
            for key in sorted(by_id.keys(), key=lambda item: str(item))
        ),
    }
    registry_digest = compute_content_sha256(registry_body)
    return MappingProxyType(
        {
            **registry_body,
            "registry_digest": registry_digest,
            "registered_capability_count": len(by_id),
            "authorized_productive_targets": tuple(sorted(authorized_productive_target_ids_v1())),
            "zero_authorized_productive_targets": ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
        }
    )


def derive_optimization_universe_identity_v1(*, registry_digest: str | None = None) -> str:
    registry = build_optimization_universe_capability_registry_v1()
    digest = registry_digest or str(registry["registry_digest"])
    identity_body = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZATION_UNIVERSE_DOMAIN,
        "universe_class": UNIVERSE_CLASS,
        "capability_registry_version": CAPABILITY_REGISTRY_VERSION,
        "registry_digest": digest,
        "learning_input_boundary_contract_id": OPTIMIZATION_LEARNING_INPUT_DOMAIN,
        "optimizable_envelope_ref": OPTIMIZABLE_ENVELOPE_REF,
        "foundation_normative_spec": FOUNDATION_NORMATIVE_SPEC,
        "boundary_normative_spec": BOUNDARY_NORMATIVE_SPEC,
    }
    return compute_content_sha256(identity_body)


def lookup_registered_optimization_capability_v1(
    capability_id: str,
) -> MappingProxyType[str, Any] | None:
    normalized = capability_id.strip()
    for entry in _REGISTRY_ENTRIES:
        if str(entry["capability_id"]) == normalized:
            return entry
    return None


def validate_registered_optimization_capability_v1(
    capability_id: str,
) -> MappingProxyType[str, Any]:
    entry = lookup_registered_optimization_capability_v1(capability_id)
    if entry is None:
        raise CanonicalOptimizationUniverseError("UNREGISTERED_OPTIMIZATION_CAPABILITY")
    if entry.get("productive_authority") != "NONE":
        raise CanonicalOptimizationUniverseError(
            "REGISTERED_CAPABILITY_PRODUCTIVE_AUTHORITY_FORBIDDEN"
        )
    return entry


def _reject_forbidden_request_flags(request: CanonicalOptimizationUniverseRequestV1) -> None:
    if request.requested_productive_target:
        raise CanonicalOptimizationUniverseError("PRODUCTIVE_TARGET_FORBIDDEN")
    if request.requested_envelope_authorization:
        raise CanonicalOptimizationUniverseError("ENVELOPE_AUTHORIZATION_FORBIDDEN")
    if request.requested_productive_join:
        raise CanonicalOptimizationUniverseError("PRODUCTIVE_JOIN_FORBIDDEN")
    if request.requested_auto_search:
        raise CanonicalOptimizationUniverseError("AUTO_SEARCH_FORBIDDEN")


def validate_canonical_optimization_universe_v1(
    request: CanonicalOptimizationUniverseRequestV1 | None = None,
) -> MappingProxyType[str, Any]:
    req = request or CanonicalOptimizationUniverseRequestV1()
    _reject_forbidden_request_flags(req)

    registry = build_optimization_universe_capability_registry_v1()
    universe_identity = derive_optimization_universe_identity_v1(
        registry_digest=str(registry["registry_digest"])
    )

    capability_status: str | None = None
    capability_reason: str | None = None
    validated_capability_id: str | None = None

    if req.capability_id is not None:
        try:
            entry = validate_registered_optimization_capability_v1(req.capability_id)
        except CanonicalOptimizationUniverseError:
            capability_status = STATUS_REJECTED_UNREGISTERED_CAPABILITY
            capability_reason = "CAPABILITY_NOT_IN_REGISTRY"
        else:
            capability_status = STATUS_ACCEPTED_REGISTERED_RESEARCH_CAPABILITY
            capability_reason = "REGISTERED_RESEARCH_ONLY"
            validated_capability_id = str(entry["capability_id"])

    learning_input_result: Mapping[str, Any] | None = None
    if req.learning_input_schema_version is not None:
        if req.learning_input_schema_version != LEARNING_INPUT_SCHEMA_VERSION:
            return MappingProxyType(
                _foundation_payload(
                    universe_identity=universe_identity,
                    registry=registry,
                    overall_status=STATUS_REJECTED_STALE_INPUT_CONTRACT,
                    overall_reason="LEARNING_INPUT_SCHEMA_VERSION_MISMATCH",
                    capability_status=capability_status,
                    capability_reason=capability_reason,
                    validated_capability_id=validated_capability_id,
                    learning_input_result=None,
                )
            )

    if req.learning_evidence is not None:
        try:
            learning_input_result = dict(
                validate_canonical_optimization_universe_learning_input_v1(
                    CanonicalOptimizationUniverseLearningInputRequestV1(
                        learning_evidence=req.learning_evidence,
                        requested_productive_join=req.requested_productive_join,
                        requested_auto_search=req.requested_auto_search,
                        requested_envelope_mutation=req.requested_envelope_authorization,
                    )
                )
            )
        except CanonicalOptimizationUniverseLearningInputError as exc:
            _LOGGER.debug("learning input boundary rejected request flags: %s", exc)
            return MappingProxyType(
                _foundation_payload(
                    universe_identity=universe_identity,
                    registry=registry,
                    overall_status=STATUS_REJECTED_AUTHORITY_BOUNDARY,
                    overall_reason=str(exc),
                    capability_status=capability_status,
                    capability_reason=capability_reason,
                    validated_capability_id=validated_capability_id,
                    learning_input_result=None,
                )
            )

    overall_status = STATUS_FOUNDATION_OK
    overall_reason = "RESEARCH_ONLY_FOUNDATION"
    if capability_status == STATUS_REJECTED_UNREGISTERED_CAPABILITY:
        overall_status = STATUS_REJECTED_UNREGISTERED_CAPABILITY
        overall_reason = capability_reason or "CAPABILITY_NOT_IN_REGISTRY"
    elif learning_input_result is not None:
        overall_status = str(learning_input_result["status"])
        overall_reason = str(learning_input_result["reason"])

    return MappingProxyType(
        _foundation_payload(
            universe_identity=universe_identity,
            registry=registry,
            overall_status=overall_status,
            overall_reason=overall_reason,
            capability_status=capability_status,
            capability_reason=capability_reason,
            validated_capability_id=validated_capability_id,
            learning_input_result=learning_input_result,
        )
    )


def _foundation_payload(
    *,
    universe_identity: str,
    registry: Mapping[str, Any],
    overall_status: str,
    overall_reason: str,
    capability_status: str | None,
    capability_reason: str | None,
    validated_capability_id: str | None,
    learning_input_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZATION_UNIVERSE_DOMAIN,
        "universe_class": UNIVERSE_CLASS,
        "optimization_universe_identity": universe_identity,
        "capability_registry_version": CAPABILITY_REGISTRY_VERSION,
        "capability_registry_digest": registry["registry_digest"],
        "registered_capability_count": registry["registered_capability_count"],
        "authorized_productive_targets": tuple(sorted(authorized_productive_target_ids_v1())),
        "zero_authorized_productive_targets": ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
        "universe_membership_implies_optimization_authorization": (
            UNIVERSE_MEMBERSHIP_IMPLIES_OPTIMIZATION_AUTHORIZATION
        ),
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "optimizable_envelope_defined": OPTIMIZABLE_ENVELOPE_DEFINED,
        "optimizable_envelope_ref": OPTIMIZABLE_ENVELOPE_REF,
        "learning_input_boundary_contract_id": OPTIMIZATION_LEARNING_INPUT_DOMAIN,
        "learning_input_boundary_schema_version": LEARNING_INPUT_SCHEMA_VERSION,
        "foundation_normative_spec": FOUNDATION_NORMATIVE_SPEC,
        "boundary_normative_spec": BOUNDARY_NORMATIVE_SPEC,
        "foundation_decision_config": FOUNDATION_DECISION_CONFIG,
        "status": overall_status,
        "reason": overall_reason,
        "capability_validation_status": capability_status,
        "capability_validation_reason": capability_reason,
        "validated_capability_id": validated_capability_id,
        "learning_input_validation": learning_input_result,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return body
