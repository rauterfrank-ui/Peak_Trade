"""M9 owner-authorized optimizable surface: volatility numeric max-age research optimization v1.

Materializes versioned constraint refs and a complete optimizable envelope record.
Research optimization only — no threshold selection, enforcement, or Master V2 mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    CANDIDATE_DOMAIN_SCHEMA_VERSION,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)

SCHEMA_VERSION: Final[str] = "canonical_m9_volatility_numeric_max_age_optimizable_surface_v1"
SURFACE_ID: Final[str] = "VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION_V1"
SURFACE_OWNER_REF: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1"
)
TARGET_FAMILY: Final[str] = "MASTER_V2_VOLATILITY_NUMERIC_MAX_AGE_RESEARCH_OPTIMIZATION"
ENVELOPE_ID: Final[str] = "envelope.volatility_numeric_max_age_research_optimization.v1"
OWNER_GRANT_CONFIG: Final[str] = (
    "config/governance/m9_volatility_numeric_max_age_optimizable_surface_owner_grant_v1.json"
)
ALLOWED_POLICY_DOMAIN_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_allowed_policy_domain_v1.json"
)
BOUNDS_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json"
)
CHANGE_RATE_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_change_rate_v1.json"
)
RISK_CONSTRAINTS_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_risk_constraints_v1.json"
)
EVIDENCE_REQUIREMENTS_REF: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_evidence_requirements_v1.json"
)
RESEARCH_OPTIMIZATION_ONLY: Final[bool] = True
PRODUCTIVE_TRADING_EFFECT: Final[str] = "NONE"

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _REPO_ROOT / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"constraint_not_mapping:{relative_path}")
    return payload


def _constraint_content_digest(relative_path: str) -> str:
    return compute_content_sha256(_load_json(relative_path))


def _validate_domain_matches_constants(domain: Mapping[str, Any]) -> None:
    if domain.get("candidate_domain_schema_version") != CANDIDATE_DOMAIN_SCHEMA_VERSION:
        raise ValueError("candidate_domain_schema_version_mismatch")
    candidates = domain.get("candidate_max_age_seconds")
    if not isinstance(candidates, list):
        raise ValueError("candidate_max_age_seconds_invalid")
    if tuple(int(value) for value in candidates) != OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS:
        raise ValueError("candidate_max_age_seconds_not_exact_operator_bound_set")


def _validate_bounds_match_constants(bounds: Mapping[str, Any]) -> None:
    candidates = bounds.get("candidate_max_age_seconds")
    if not isinstance(candidates, list):
        raise ValueError("bounds_candidate_set_invalid")
    if tuple(int(value) for value in candidates) != OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS:
        raise ValueError("bounds_not_exact_operator_bound_set")


def compute_m9_constraint_ref_digests_v1() -> MappingProxyType[str, str]:
    refs = (
        ALLOWED_POLICY_DOMAIN_REF,
        BOUNDS_REF,
        CHANGE_RATE_REF,
        RISK_CONSTRAINTS_REF,
        EVIDENCE_REQUIREMENTS_REF,
        OWNER_GRANT_CONFIG,
    )
    return MappingProxyType({ref: _constraint_content_digest(ref) for ref in refs})


def compute_m9_reproducibility_digest_v1() -> str:
    domain = _load_json(ALLOWED_POLICY_DOMAIN_REF)
    bounds = _load_json(BOUNDS_REF)
    _validate_domain_matches_constants(domain)
    _validate_bounds_match_constants(bounds)
    ref_digests = compute_m9_constraint_ref_digests_v1()
    body = {
        "schema_version": SCHEMA_VERSION,
        "surface_id": SURFACE_ID,
        "surface_owner_ref": SURFACE_OWNER_REF,
        "target_family": TARGET_FAMILY,
        "envelope_id": ENVELOPE_ID,
        "allowed_value_or_policy_domain": ALLOWED_POLICY_DOMAIN_REF,
        "bounds_ref": BOUNDS_REF,
        "change_rate_ref": CHANGE_RATE_REF,
        "risk_constraints_ref": RISK_CONSTRAINTS_REF,
        "evidence_requirements_ref": EVIDENCE_REQUIREMENTS_REF,
        "owner_grant_config": OWNER_GRANT_CONFIG,
        "constraint_ref_digests": {key: ref_digests[key] for key in sorted(ref_digests.keys())},
        "research_optimization_only": RESEARCH_OPTIMIZATION_ONLY,
        "productive_trading_effect": PRODUCTIVE_TRADING_EFFECT,
    }
    return compute_content_sha256(body)


def build_m9_volatility_numeric_max_age_envelope_payload_v1() -> dict[str, Any]:
    reproducibility_digest = compute_m9_reproducibility_digest_v1()
    ref_digests = compute_m9_constraint_ref_digests_v1()
    return {
        "envelope_id": ENVELOPE_ID,
        "envelope_version": "optimizable_envelope_contract_v1",
        "surface_id": SURFACE_ID,
        "surface_owner_ref": SURFACE_OWNER_REF,
        "target_family": TARGET_FAMILY,
        "allowed_value_or_policy_domain": ALLOWED_POLICY_DOMAIN_REF,
        "bounds_ref": BOUNDS_REF,
        "change_rate_ref": CHANGE_RATE_REF,
        "risk_constraints_ref": RISK_CONSTRAINTS_REF,
        "evidence_requirements_ref": EVIDENCE_REQUIREMENTS_REF,
        "provenance": {
            "owner_grant_wp_id": "M9_VOLATILITY_MAX_AGE_OPTIMIZABLE_SURFACE_IMPLEMENTATION_V1",
            "owner_grant_config": OWNER_GRANT_CONFIG,
            "owner_grant_config_digest": ref_digests[OWNER_GRANT_CONFIG],
            "constraint_ref_digests": {
                key: ref_digests[key]
                for key in sorted(ref_digests.keys())
                if key != OWNER_GRANT_CONFIG
            },
            "research_optimization_only": RESEARCH_OPTIMIZATION_ONLY,
            "productive_trading_effect": PRODUCTIVE_TRADING_EFFECT,
        },
        "reproducibility_digest": reproducibility_digest,
        "status": "AUTHORIZED_RESEARCH_OPTIMIZATION",
        "owner_explicit_authorization": True,
        "owner_authorization_ref": SURFACE_OWNER_REF,
        "productive_authority": "NONE",
        "core_mutation_allowed": False,
    }


def apply_volatility_numeric_max_age_surface_registry_v1(
    *,
    catalog: dict[str, MappingProxyType[str, Any]],
) -> frozenset[str]:
    from src.experiments.canonical_optimizable_envelope_v1 import build_optimizable_envelope_v1

    payload = build_m9_volatility_numeric_max_age_envelope_payload_v1()
    envelope = build_optimizable_envelope_v1(payload)
    if envelope["surface_id"] != SURFACE_ID:
        raise ValueError("surface_id_mismatch")
    catalog[SURFACE_ID] = envelope
    return frozenset({SURFACE_ID})
