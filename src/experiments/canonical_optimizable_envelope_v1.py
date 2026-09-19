"""Optimizable envelope v1 — contract schema and fail-closed resolver.

Defines versioned envelope records and deterministic resolution. The authorized
surface registry is empty by default. Owner maps and universe membership never
imply surface authorization. No search, promotion, or runtime mutation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_optimizable_envelope_v1"
OPTIMIZABLE_ENVELOPE_DOMAIN: Final[str] = "peak_trade.canonical_optimizable_envelope.v1"
SYNTHETIC_OFFLINE_SURFACE_ID: Final[str] = "offline.synthetic.research.m4.v1"
ENVELOPE_CONTRACT_VERSION: Final[str] = "optimizable_envelope_contract_v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/OPTIMIZABLE_ENVELOPE_V1_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = "config/governance/optimizable_envelope_v1_decision_v1.json"
SECTION5_OWNER_MAP_EVIDENCE_REF: Final[str] = (
    "docs/ops/planning/SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)

STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION: Final[str] = "AUTHORIZED_RESEARCH_OPTIMIZATION"
STATUS_NOT_OPTIMIZABLE: Final[str] = "NOT_OPTIMIZABLE"
STATUS_UNKNOWN_FAIL_CLOSED: Final[str] = "UNKNOWN_FAIL_CLOSED"
ENVELOPE_STATUSES: Final[frozenset[str]] = frozenset(
    {
        STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION,
        STATUS_NOT_OPTIMIZABLE,
        STATUS_UNKNOWN_FAIL_CLOSED,
    }
)

RESOLUTION_NOT_AUTHORIZED: Final[str] = "NOT_AUTHORIZED"
RESOLUTION_FORBIDDEN: Final[str] = "FORBIDDEN"
RESOLUTION_NOT_OPTIMIZABLE: Final[str] = "NOT_OPTIMIZABLE"
RESOLUTION_UNKNOWN_FAIL_CLOSED: Final[str] = "UNKNOWN_FAIL_CLOSED"
RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION: Final[str] = "AUTHORIZED_RESEARCH_OPTIMIZATION"

REASON_UNREGISTERED_SURFACE: Final[str] = "UNREGISTERED_SURFACE"
REASON_UNKNOWN_SURFACE: Final[str] = "UNKNOWN_SURFACE"
REASON_MISSING_CONSTRAINT: Final[str] = "MISSING_CONSTRAINT"
REASON_PARTIAL: Final[str] = "PARTIAL"
REASON_AMBIGUOUS_AUTHORITY: Final[str] = "AMBIGUOUS_AUTHORITY"
REASON_STALE_VERSION: Final[str] = "STALE_VERSION"
REASON_OWNER_MISMATCH: Final[str] = "OWNER_MISMATCH"
REASON_CORE_MUTATION_REQUEST: Final[str] = "CORE_MUTATION_REQUEST"
REASON_NOT_OPTIMIZABLE: Final[str] = "NOT_OPTIMIZABLE"
REASON_UNKNOWN_FAIL_CLOSED: Final[str] = "UNKNOWN_FAIL_CLOSED"
REASON_OWNER_MAP_NOT_AUTHORITY: Final[str] = "OWNER_MAP_EVIDENCE_NOT_AUTHORITY"
REASON_SURFACE_NOT_OWNER_AUTHORIZED: Final[str] = "SURFACE_NOT_OWNER_AUTHORIZED"
REASON_SURFACE_NOT_IN_AUTHORIZED_REGISTRY: Final[str] = "SURFACE_NOT_IN_AUTHORIZED_REGISTRY"

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
ZERO_AUTHORIZED_PRODUCTIVE_TARGETS: Final[bool] = True
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True
NO_SELF_DEPLOY: Final[bool] = True
OWNER_MAP_IMPLIES_AUTHORIZATION: Final[bool] = False

_PARTIAL_TOKENS: Final[frozenset[str]] = frozenset(
    {
        "",
        "PARTIAL",
        "UNKNOWN",
        "UNRESOLVED",
        "UNRESOLVED_NOT_AUTHORIZED",
        "TBD",
    }
)

_REQUIRED_STRING_FIELDS: Final[tuple[str, ...]] = (
    "envelope_id",
    "envelope_version",
    "surface_id",
    "surface_owner_ref",
    "target_family",
    "allowed_value_or_policy_domain",
    "bounds_ref",
    "change_rate_ref",
    "risk_constraints_ref",
    "evidence_requirements_ref",
)

_LOGGER = logging.getLogger(__name__)

_ENVELOPE_CATALOG_BY_SURFACE: dict[str, MappingProxyType[str, Any]] = {}
_AUTHORIZED_SURFACE_IDS: frozenset[str] = frozenset()
_AUTHORIZED_SURFACE_REGISTRY_BOOTSTRAPPED: bool = False


def _ensure_authorized_surface_registry_v1() -> None:
    global _AUTHORIZED_SURFACE_REGISTRY_BOOTSTRAPPED, _AUTHORIZED_SURFACE_IDS
    if _AUTHORIZED_SURFACE_REGISTRY_BOOTSTRAPPED:
        return
    from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
        apply_research_backtest_cost_grid_surface_registry_v1,
    )
    from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
        apply_f5_fresh_futures_input_freshness_surface_registry_v1,
    )
    from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
        apply_volatility_numeric_max_age_surface_registry_v1,
    )

    surface_ids: set[str] = set()
    surface_ids |= apply_volatility_numeric_max_age_surface_registry_v1(
        catalog=_ENVELOPE_CATALOG_BY_SURFACE,
    )
    surface_ids |= apply_research_backtest_cost_grid_surface_registry_v1(
        catalog=_ENVELOPE_CATALOG_BY_SURFACE,
    )
    surface_ids |= apply_f5_fresh_futures_input_freshness_surface_registry_v1(
        catalog=_ENVELOPE_CATALOG_BY_SURFACE,
    )
    _AUTHORIZED_SURFACE_IDS = frozenset(surface_ids)
    _AUTHORIZED_SURFACE_REGISTRY_BOOTSTRAPPED = True


def _ensure_m9_surface_registry_v1() -> None:
    """Backward-compatible alias for registry bootstrap."""
    _ensure_authorized_surface_registry_v1()


class CanonicalOptimizableEnvelopeError(ValueError):
    """Fail-closed malformed optimizable envelope record or request."""


@dataclass(frozen=True)
class OptimizableEnvelopeResolveRequestV1:
    surface_id: str | None
    envelope: Mapping[str, Any] | None = None
    claimed_surface_owner_ref: str | None = None
    owner_map_provenance_ref: str | None = None
    requested_core_mutation: bool = False


def build_authorized_surface_registry_v1() -> MappingProxyType[str, Any]:
    _ensure_m9_surface_registry_v1()
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "domain": OPTIMIZABLE_ENVELOPE_DOMAIN,
            "envelope_contract_version": ENVELOPE_CONTRACT_VERSION,
            "authorized_surface_ids": tuple(sorted(_AUTHORIZED_SURFACE_IDS)),
            "authorized_surface_count": len(_AUTHORIZED_SURFACE_IDS),
            "zero_authorized_productive_targets": ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
            "catalog_surface_count": len(_ENVELOPE_CATALOG_BY_SURFACE),
        }
    )


def _require_non_partial_string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise CanonicalOptimizableEnvelopeError(f"{field}_MUST_BE_STRING")
    normalized = value.strip()
    if normalized in _PARTIAL_TOKENS:
        raise CanonicalOptimizableEnvelopeError(f"{field}_PARTIAL_OR_MISSING")
    return normalized


def build_optimizable_envelope_v1(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    if not isinstance(payload, Mapping):
        raise CanonicalOptimizableEnvelopeError("ENVELOPE_MUST_BE_MAPPING")
    canonical: dict[str, Any] = {}
    for field in _REQUIRED_STRING_FIELDS:
        canonical[field] = _require_non_partial_string(payload.get(field), field)
    if canonical["envelope_version"] != ENVELOPE_CONTRACT_VERSION:
        raise CanonicalOptimizableEnvelopeError("ENVELOPE_VERSION_STALE_OR_UNSUPPORTED")
    provenance = payload.get("provenance")
    if not isinstance(provenance, Mapping):
        raise CanonicalOptimizableEnvelopeError("PROVENANCE_MUST_BE_MAPPING")
    if not provenance:
        raise CanonicalOptimizableEnvelopeError("PROVENANCE_EMPTY")
    reproducibility_digest = _require_non_partial_string(
        payload.get("reproducibility_digest"), "reproducibility_digest"
    )
    if not is_valid_sha256_hex(reproducibility_digest):
        raise CanonicalOptimizableEnvelopeError("REPRODUCIBILITY_DIGEST_INVALID")
    status = _require_non_partial_string(payload.get("status"), "status")
    if status not in ENVELOPE_STATUSES:
        raise CanonicalOptimizableEnvelopeError("ENVELOPE_STATUS_INVALID")
    if payload.get("productive_authority", "NONE") != "NONE":
        raise CanonicalOptimizableEnvelopeError("PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    if payload.get("core_mutation_allowed") is True:
        raise CanonicalOptimizableEnvelopeError("CORE_MUTATION_ALLOWED_FORBIDDEN")
    owner_explicit = payload.get("owner_explicit_authorization")
    if owner_explicit is not None and not isinstance(owner_explicit, bool):
        raise CanonicalOptimizableEnvelopeError("OWNER_EXPLICIT_AUTHORIZATION_MUST_BE_BOOL")
    owner_authorization_ref = payload.get("owner_authorization_ref")
    if owner_authorization_ref is not None:
        owner_authorization_ref = _require_non_partial_string(
            owner_authorization_ref, "owner_authorization_ref"
        )
    canonical["provenance"] = MappingProxyType(dict(provenance))
    canonical["reproducibility_digest"] = reproducibility_digest
    canonical["status"] = status
    canonical["productive_authority"] = "NONE"
    canonical["core_mutation_allowed"] = False
    canonical["owner_explicit_authorization"] = bool(owner_explicit)
    canonical["owner_authorization_ref"] = owner_authorization_ref
    canonical["schema_version"] = SCHEMA_VERSION
    canonical["domain"] = OPTIMIZABLE_ENVELOPE_DOMAIN
    canonical["envelope_identity"] = derive_optimizable_envelope_identity_v1(canonical)
    return MappingProxyType(canonical)


def derive_optimizable_envelope_identity_v1(envelope: Mapping[str, Any]) -> str:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZABLE_ENVELOPE_DOMAIN,
        "envelope_contract_version": ENVELOPE_CONTRACT_VERSION,
        "envelope_id": envelope.get("envelope_id"),
        "envelope_version": envelope.get("envelope_version"),
        "surface_id": envelope.get("surface_id"),
        "surface_owner_ref": envelope.get("surface_owner_ref"),
        "target_family": envelope.get("target_family"),
        "allowed_value_or_policy_domain": envelope.get("allowed_value_or_policy_domain"),
        "bounds_ref": envelope.get("bounds_ref"),
        "change_rate_ref": envelope.get("change_rate_ref"),
        "risk_constraints_ref": envelope.get("risk_constraints_ref"),
        "evidence_requirements_ref": envelope.get("evidence_requirements_ref"),
        "reproducibility_digest": envelope.get("reproducibility_digest"),
        "status": envelope.get("status"),
    }
    return compute_content_sha256(body)


def _normalize_surface_id(surface_id: str | None) -> str | None:
    if surface_id is None:
        return None
    normalized = surface_id.strip()
    if not normalized or normalized in _PARTIAL_TOKENS:
        return None
    if normalized.upper() == "UNKNOWN":
        return None
    return normalized


def _resolution_payload(
    *,
    resolution: str,
    reason: str,
    surface_id: str | None,
    envelope_identity: str | None = None,
    owner_map_provenance_ref: str | None = None,
) -> dict[str, Any]:
    registry = build_authorized_surface_registry_v1()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": OPTIMIZABLE_ENVELOPE_DOMAIN,
        "resolution": resolution,
        "reason": reason,
        "surface_id": surface_id,
        "envelope_identity": envelope_identity,
        "authorized_surface_count": registry["authorized_surface_count"],
        "zero_authorized_productive_targets": ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "owner_map_provenance_ref": owner_map_provenance_ref,
        "owner_map_implies_authorization": OWNER_MAP_IMPLIES_AUTHORIZATION,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return body


def resolve_optimizable_envelope_v1(
    request: OptimizableEnvelopeResolveRequestV1,
) -> MappingProxyType[str, Any]:
    _ensure_m9_surface_registry_v1()
    if request.requested_core_mutation:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_FORBIDDEN,
                reason=REASON_CORE_MUTATION_REQUEST,
                surface_id=_normalize_surface_id(request.surface_id),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    surface_id = _normalize_surface_id(request.surface_id)
    if request.surface_id is not None and surface_id is None:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=REASON_UNKNOWN_SURFACE,
                surface_id=request.surface_id.strip()
                if isinstance(request.surface_id, str)
                else None,
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )
    if surface_id is None:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_UNKNOWN_FAIL_CLOSED,
                reason=REASON_UNKNOWN_FAIL_CLOSED,
                surface_id=None,
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    envelope_raw: Mapping[str, Any] | None = request.envelope
    if envelope_raw is None:
        catalog_entry = _ENVELOPE_CATALOG_BY_SURFACE.get(surface_id)
        if catalog_entry is None:
            return MappingProxyType(
                _resolution_payload(
                    resolution=RESOLUTION_NOT_AUTHORIZED,
                    reason=REASON_UNREGISTERED_SURFACE,
                    surface_id=surface_id,
                    owner_map_provenance_ref=request.owner_map_provenance_ref,
                )
            )
        envelope_raw = catalog_entry
    else:
        if str(envelope_raw.get("surface_id", "")).strip() != surface_id:
            return MappingProxyType(
                _resolution_payload(
                    resolution=RESOLUTION_NOT_AUTHORIZED,
                    reason=REASON_OWNER_MISMATCH,
                    surface_id=surface_id,
                    owner_map_provenance_ref=request.owner_map_provenance_ref,
                )
            )

    try:
        envelope = build_optimizable_envelope_v1(envelope_raw)
    except CanonicalOptimizableEnvelopeError as exc:
        message = str(exc)
        _LOGGER.debug("envelope build failed: %s", message)
        if "STALE" in message or "VERSION" in message:
            reason = REASON_STALE_VERSION
        elif "PARTIAL" in message or "MISSING" in message or "EMPTY" in message:
            reason = REASON_PARTIAL if "PARTIAL" in message else REASON_MISSING_CONSTRAINT
        else:
            reason = REASON_MISSING_CONSTRAINT
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=reason,
                surface_id=surface_id,
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    if envelope["status"] == STATUS_NOT_OPTIMIZABLE:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_OPTIMIZABLE,
                reason=REASON_NOT_OPTIMIZABLE,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )
    if envelope["status"] == STATUS_UNKNOWN_FAIL_CLOSED:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_UNKNOWN_FAIL_CLOSED,
                reason=REASON_UNKNOWN_FAIL_CLOSED,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    if request.claimed_surface_owner_ref is not None:
        claimed = request.claimed_surface_owner_ref.strip()
        if claimed != envelope["surface_owner_ref"]:
            return MappingProxyType(
                _resolution_payload(
                    resolution=RESOLUTION_NOT_AUTHORIZED,
                    reason=REASON_OWNER_MISMATCH,
                    surface_id=surface_id,
                    envelope_identity=str(envelope["envelope_identity"]),
                    owner_map_provenance_ref=request.owner_map_provenance_ref,
                )
            )

    owner_ref = envelope.get("owner_authorization_ref")
    if owner_ref is not None and owner_ref != envelope["surface_owner_ref"]:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=REASON_AMBIGUOUS_AUTHORITY,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    if not envelope.get("owner_explicit_authorization"):
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=REASON_SURFACE_NOT_OWNER_AUTHORIZED,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    if request.owner_map_provenance_ref:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=REASON_OWNER_MAP_NOT_AUTHORITY,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
                owner_map_provenance_ref=request.owner_map_provenance_ref,
            )
        )

    if surface_id not in _AUTHORIZED_SURFACE_IDS:
        return MappingProxyType(
            _resolution_payload(
                resolution=RESOLUTION_NOT_AUTHORIZED,
                reason=REASON_SURFACE_NOT_IN_AUTHORIZED_REGISTRY,
                surface_id=surface_id,
                envelope_identity=str(envelope["envelope_identity"]),
            )
        )

    return MappingProxyType(
        _resolution_payload(
            resolution=RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
            reason=STATUS_AUTHORIZED_RESEARCH_OPTIMIZATION,
            surface_id=surface_id,
            envelope_identity=str(envelope["envelope_identity"]),
        )
    )
