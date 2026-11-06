"""F2 owner-authorized optimizable surface: research backtest fee/slippage cost grid v1.

Materializes versioned constraint refs and a complete optimizable envelope record.
Research optimization only — no productive config mutation, promotion, or execution authority.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
)
from src.backtest.parameter_sensitivity_v1 import PARAMETER_SENSITIVITY_OWNER
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_f2_research_backtest_cost_grid_optimizable_surface_v1"
SURFACE_ID: Final[str] = "RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE_OPTIMIZATION_V1"
SURFACE_OWNER_REF: Final[str] = PARAMETER_SENSITIVITY_OWNER
TARGET_FAMILY: Final[str] = "RESEARCH_BACKTEST_COST_GRID_FEE_SLIPPAGE"
ENVELOPE_ID: Final[str] = "envelope.research_backtest_cost_grid_fee_slippage.v1"
OWNER_GRANT_CONFIG: Final[str] = (
    "config/governance/f2_research_backtest_cost_grid_optimizable_surface_owner_grant_v1.json"
)
ALLOWED_POLICY_DOMAIN_REF: Final[str] = (
    "config/governance/optimizable_envelope/research_backtest_cost_grid_allowed_policy_domain_v1.json"
)
BOUNDS_REF: Final[str] = (
    "config/governance/optimizable_envelope/research_backtest_cost_grid_discrete_bounds_v1.json"
)
CHANGE_RATE_REF: Final[str] = (
    "config/governance/optimizable_envelope/research_backtest_cost_grid_change_rate_v1.json"
)
RISK_CONSTRAINTS_REF: Final[str] = (
    "config/governance/optimizable_envelope/research_backtest_cost_grid_risk_constraints_v1.json"
)
EVIDENCE_REQUIREMENTS_REF: Final[str] = (
    "config/governance/optimizable_envelope/research_backtest_cost_grid_evidence_requirements_v1.json"
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
    if domain.get("grid_id") != GRID_ID:
        raise ValueError("grid_id_mismatch")
    fee = domain.get("fee_bps")
    slip = domain.get("slippage_bps")
    if tuple(float(v) for v in fee) != OPERATOR_BOUND_FEE_BPS:
        raise ValueError("fee_bps_not_exact_operator_bound_set")
    if tuple(float(v) for v in slip) != OPERATOR_BOUND_SLIPPAGE_BPS:
        raise ValueError("slippage_bps_not_exact_operator_bound_set")
    if float(domain.get("baseline_fee_bps", -1)) != BASELINE_FEE_BPS:
        raise ValueError("baseline_fee_bps_mismatch")
    if float(domain.get("baseline_slippage_bps", -1)) != BASELINE_SLIPPAGE_BPS:
        raise ValueError("baseline_slippage_bps_mismatch")


def _validate_bounds_match_constants(bounds: Mapping[str, Any]) -> None:
    if tuple(float(v) for v in bounds.get("fee_bps", ())) != OPERATOR_BOUND_FEE_BPS:
        raise ValueError("bounds_fee_bps_mismatch")
    if tuple(float(v) for v in bounds.get("slippage_bps", ())) != OPERATOR_BOUND_SLIPPAGE_BPS:
        raise ValueError("bounds_slippage_bps_mismatch")


def compute_f2_constraint_ref_digests_v1() -> MappingProxyType[str, str]:
    refs = (
        ALLOWED_POLICY_DOMAIN_REF,
        BOUNDS_REF,
        CHANGE_RATE_REF,
        RISK_CONSTRAINTS_REF,
        EVIDENCE_REQUIREMENTS_REF,
        OWNER_GRANT_CONFIG,
    )
    return MappingProxyType({ref: _constraint_content_digest(ref) for ref in refs})


def compute_f2_reproducibility_digest_v1() -> str:
    domain = _load_json(ALLOWED_POLICY_DOMAIN_REF)
    bounds = _load_json(BOUNDS_REF)
    _validate_domain_matches_constants(domain)
    _validate_bounds_match_constants(bounds)
    ref_digests = compute_f2_constraint_ref_digests_v1()
    body = {
        "schema_version": SCHEMA_VERSION,
        "surface_id": SURFACE_ID,
        "surface_owner_ref": SURFACE_OWNER_REF,
        "target_family": TARGET_FAMILY,
        "envelope_id": ENVELOPE_ID,
        "grid_id": GRID_ID,
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


def build_f2_research_backtest_cost_grid_envelope_payload_v1() -> dict[str, Any]:
    reproducibility_digest = compute_f2_reproducibility_digest_v1()
    ref_digests = compute_f2_constraint_ref_digests_v1()
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
            "owner_grant_wp_id": "F2_RESEARCH_BACKTEST_COST_GRID_END_TO_END_V1",
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


def apply_research_backtest_cost_grid_surface_registry_v1(
    *,
    catalog: dict[str, MappingProxyType[str, Any]],
) -> frozenset[str]:
    from src.experiments.canonical_optimizable_envelope_v1 import build_optimizable_envelope_v1

    payload = build_f2_research_backtest_cost_grid_envelope_payload_v1()
    envelope = build_optimizable_envelope_v1(payload)
    if envelope["surface_id"] != SURFACE_ID:
        raise ValueError("surface_id_mismatch")
    catalog[SURFACE_ID] = envelope
    return frozenset({SURFACE_ID})
