"""Phase 11 optimization surface portfolio registry — durable census, classification, resolver.

Navigation/planning closure only. Does not authorize promotion, productive write, search
execution, or trading selection. Universe membership and code presence do not imply
authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f3_strategy_hyperparameter_optimizable_surface_exclusion_v1 import (
    assert_global_f3_surface_not_authorized_v1,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    SYNTHETIC_OFFLINE_SURFACE_ID,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_surface_families_pre_test_preparation_v1 import (
    PreparationStatus,
    optimization_surface_family_records_v1,
    verify_test_ready_cross_surface_isolation_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    UNKNOWN_UNAVAILABLE,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "canonical_optimization_surface_portfolio_registry_v1"
WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_11_SURFACE_PORTFOLIO_CLOSURE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_11_SURFACE_PORTFOLIO_CLOSURE_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_11_surface_portfolio_closure_v1.json"
)
PDF_PORTFOLIO_CONFIG: Final[str] = (
    "config/governance/pdf_v3_3_optimization_surface_portfolio_classification_v1.json"
)

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PROMOTION_AUTHORITY: Final[str] = PROMOTION_AUTHORITY
NO_SELF_DEPLOY: Final[bool] = True
UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION: Final[bool] = False
CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION: Final[bool] = False
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False

REASON_PORTFOLIO_AUTHORIZED_RESEARCH: Final[str] = "PORTFOLIO_AUTHORIZED_RESEARCH_SURFACE"
REASON_PORTFOLIO_DEFERRED: Final[str] = "PORTFOLIO_DEFERRED_NOT_RESEARCH_ACTIVE"
REASON_PORTFOLIO_EXCLUDED: Final[str] = "PORTFOLIO_EXCLUDED_CONSTITUTIONAL"
REASON_PORTFOLIO_UNKNOWN: Final[str] = "PORTFOLIO_UNKNOWN_FAIL_CLOSED"
REASON_META_FAMILY_NOT_IN_CENSUS: Final[str] = "M6_OPTIMIZATION_FAMILY_NOT_IN_PORTFOLIO_CENSUS"
REASON_META_FAMILY_EXCLUDED: Final[str] = "M6_OPTIMIZATION_FAMILY_EXCLUDED_BY_PORTFOLIO"
REASON_META_FAMILY_DEFERRED: Final[str] = "M6_OPTIMIZATION_FAMILY_DEFERRED_BY_PORTFOLIO"

_FAMILY_GATE_OVERRIDES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "FUNDING-ONLY": "DEFERRED",
    }
)

_OPT_FAMILY_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "F1": "F1",
        "F1/M9": "F1",
        "M9": "F1",
        "F1_VOLATILITY_NUMERIC_MAX_AGE": "F1",
        "F2": "F2",
        "F2_FEE_SLIPPAGE_COST_GRID": "F2",
        "F5-FRESH": "F5-FRESH",
        "F5_FRESH": "F5-FRESH",
        "F5-FRESH-FUTURES": "F5-FRESH",
        "F3": "F3",
        "F3_STRATEGY_HYPERPARAMETERS": "F3",
        "RISK-SIZE": "RISK-SIZE",
        "RISK_SIZING": "RISK-SIZE",
        "OLS-DIAG": "OLS-DIAG",
        "OLS_COEFFICIENTS": "OLS-DIAG",
        "FUNDING-ONLY": "FUNDING-ONLY",
        "FUNDING_EVALUATION_BINDING": "FUNDING-ONLY",
        F1_SURFACE_ID: "F1",
        F2_SURFACE_ID: "F2",
        F5_FRESH_SURFACE_ID: "F5-FRESH",
    }
)


class PortfolioClassification(str, Enum):
    AUTHORIZED_RESEARCH_SURFACE = "AUTHORIZED_RESEARCH_SURFACE"
    DEFERRED = "DEFERRED"
    EXCLUDED_CONSTITUTIONAL = "EXCLUDED_CONSTITUTIONAL"


@dataclass(frozen=True)
class OptimizationSurfacePortfolioRecordV1:
    family_key: str
    family_gate_id: str
    display_name: str
    surface_id: str | None
    portfolio_classification: PortfolioClassification
    research_active: bool
    bounded_domain_summary: str | None
    bounded_domain_refs: tuple[str, ...]
    authority_owner_boundary: str
    productive_relevance: str
    evidence_refs: tuple[str, ...]
    resolver_participation: str
    classification_reason: str
    unresolved_conflict: str | None


@dataclass(frozen=True)
class MetaOptimizationFamilyPortfolioGateV1:
    explicit_family_reference: bool
    research_choice_allowed: bool
    reason: str
    payload: Mapping[str, Any]


def _portfolio_classification_for_preparation(
    *,
    family_gate_id: str,
    preparation_status: PreparationStatus,
) -> PortfolioClassification:
    override = _FAMILY_GATE_OVERRIDES.get(family_gate_id)
    if override == "DEFERRED":
        return PortfolioClassification.DEFERRED
    if preparation_status in (
        PreparationStatus.TEST_READY,
        PreparationStatus.TEST_READY_SHADOW_RESEARCH,
    ):
        return PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE
    if preparation_status == PreparationStatus.TEST_READY_PER_TOKEN_SHADOW_CALIBRATION_ONLY:
        return PortfolioClassification.DEFERRED
    if preparation_status == PreparationStatus.OWNER_DECISION_REQUIRED:
        raise ValueError(f"portfolio_owner_decision_required:{family_gate_id}")
    return PortfolioClassification.EXCLUDED_CONSTITUTIONAL


def _research_active_for_record(
    *,
    portfolio_classification: PortfolioClassification,
    surface_id: str | None,
) -> bool:
    if portfolio_classification != PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE:
        return False
    if surface_id is None:
        return False
    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    return resolution["resolution"] == RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION


def _build_portfolio_records_v1() -> tuple[OptimizationSurfacePortfolioRecordV1, ...]:
    records: list[OptimizationSurfacePortfolioRecordV1] = []
    for family in optimization_surface_family_records_v1():
        classification = _portfolio_classification_for_preparation(
            family_gate_id=family.family_gate_id,
            preparation_status=family.preparation_status,
        )
        research_active = _research_active_for_record(
            portfolio_classification=classification,
            surface_id=family.authorized_surface_id,
        )
        domain_refs = tuple(family.existing_seam_refs)
        bounded_summary = (
            family.parameter_domain_summary
            if classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE
            else None
        )
        if classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE:
            reason = REASON_PORTFOLIO_AUTHORIZED_RESEARCH
        elif classification == PortfolioClassification.DEFERRED:
            reason = REASON_PORTFOLIO_DEFERRED
        else:
            reason = REASON_PORTFOLIO_EXCLUDED
        resolver_participation = (
            "optimizable_envelope_resolver_v1"
            if family.authorized_surface_id is not None
            else "portfolio_registry_only"
        )
        records.append(
            OptimizationSurfacePortfolioRecordV1(
                family_key=family.family_gate_id,
                family_gate_id=family.family_gate_id,
                display_name=family.display_name,
                surface_id=family.authorized_surface_id,
                portfolio_classification=classification,
                research_active=research_active,
                bounded_domain_summary=bounded_summary,
                bounded_domain_refs=domain_refs,
                authority_owner_boundary=family.authority_boundary_summary,
                productive_relevance=family.productive_effect,
                evidence_refs=domain_refs + family.owner_refs,
                resolver_participation=resolver_participation,
                classification_reason=reason,
                unresolved_conflict=family.unresolved_blocker,
            )
        )

    records.append(
        OptimizationSurfacePortfolioRecordV1(
            family_key="M4-SYNTHETIC-OFFLINE-CONTEXT",
            family_gate_id="M4-SYNTHETIC-OFFLINE-CONTEXT",
            display_name="M4 synthetic offline experiment plane context",
            surface_id=SYNTHETIC_OFFLINE_SURFACE_ID,
            portfolio_classification=PortfolioClassification.EXCLUDED_CONSTITUTIONAL,
            research_active=False,
            bounded_domain_summary=None,
            bounded_domain_refs=(),
            authority_owner_boundary=(
                "Experiment-plane infrastructure context; not an optimizable parameter surface"
            ),
            productive_relevance="NONE",
            evidence_refs=(
                "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
            ),
            resolver_participation="optimizable_envelope_resolver_v1",
            classification_reason=REASON_PORTFOLIO_EXCLUDED,
            unresolved_conflict=None,
        )
    )
    return tuple(records)


_PORTFOLIO_RECORDS: Final[tuple[OptimizationSurfacePortfolioRecordV1, ...]] = (
    _build_portfolio_records_v1()
)
_BY_FAMILY_GATE: Final[Mapping[str, OptimizationSurfacePortfolioRecordV1]] = MappingProxyType(
    {record.family_gate_id: record for record in _PORTFOLIO_RECORDS}
)
_BY_SURFACE_ID: Final[Mapping[str, OptimizationSurfacePortfolioRecordV1]] = MappingProxyType(
    {record.surface_id: record for record in _PORTFOLIO_RECORDS if record.surface_id is not None}
)


def optimization_surface_portfolio_records_v1() -> tuple[OptimizationSurfacePortfolioRecordV1, ...]:
    return _PORTFOLIO_RECORDS


def build_optimization_surface_portfolio_registry_v1() -> MappingProxyType[str, Any]:
    rows = []
    for record in _PORTFOLIO_RECORDS:
        rows.append(
            {
                "family_key": record.family_key,
                "family_gate_id": record.family_gate_id,
                "display_name": record.display_name,
                "surface_id": record.surface_id,
                "portfolio_classification": record.portfolio_classification.value,
                "research_active": record.research_active,
                "bounded_domain_summary": record.bounded_domain_summary,
                "bounded_domain_refs": list(record.bounded_domain_refs),
                "authority_owner_boundary": record.authority_owner_boundary,
                "productive_relevance": record.productive_relevance,
                "evidence_refs": list(record.evidence_refs),
                "resolver_participation": record.resolver_participation,
                "classification_reason": record.classification_reason,
                "unresolved_conflict": record.unresolved_conflict,
            }
        )
    body = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "universe_member_implies_authorization": UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION,
        "candidate_implies_productive_configuration": CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "no_self_deploy": NO_SELF_DEPLOY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "trading_decision_authority_owner": TRADING_DECISION_AUTHORITY_OWNER,
        "families": rows,
        "authorized_research_surface_ids": list(list_authorized_research_surface_ids_v1()),
        "research_active_surface_ids": list(list_research_active_surface_ids_v1()),
    }
    body["registry_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "registry_digest"}
    )
    return MappingProxyType(body)


def list_authorized_research_surface_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.surface_id
        for record in _PORTFOLIO_RECORDS
        if record.portfolio_classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE
        and record.surface_id is not None
    )


def list_research_active_surface_ids_v1() -> tuple[str, ...]:
    return tuple(
        record.surface_id
        for record in _PORTFOLIO_RECORDS
        if record.research_active and record.surface_id is not None
    )


def list_portfolio_unknown_or_conflicted_family_keys_v1() -> tuple[str, ...]:
    return tuple(
        record.family_key
        for record in _PORTFOLIO_RECORDS
        if record.unresolved_conflict is not None
        and record.portfolio_classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE
        and record.unresolved_conflict.startswith("GLOBAL_SURFACE_NO_GO")
    )


def _normalize_lookup_token(token: str | None) -> str | None:
    if token is None:
        return None
    normalized = token.strip()
    if not normalized or normalized == UNKNOWN_UNAVAILABLE:
        return None
    return normalized


def resolve_optimization_surface_portfolio_v1(
    *,
    family_gate_id: str | None = None,
    surface_id: str | None = None,
) -> MappingProxyType[str, Any]:
    gate = _normalize_lookup_token(family_gate_id)
    sid = _normalize_lookup_token(surface_id)
    if gate is not None:
        alias = _OPT_FAMILY_ALIASES.get(gate, gate)
        record = _BY_FAMILY_GATE.get(alias)
    elif sid is not None:
        record = _BY_SURFACE_ID.get(sid)
        if record is None:
            alias = _OPT_FAMILY_ALIASES.get(sid)
            record = _BY_FAMILY_GATE.get(alias) if alias else None
    else:
        record = None

    if record is None:
        body = {
            "schema_version": SCHEMA_VERSION,
            "resolution": "NOT_IN_PORTFOLIO_CENSUS",
            "reason": REASON_PORTFOLIO_UNKNOWN,
            "family_gate_id": gate,
            "surface_id": sid,
            "research_active": False,
            "portfolio_classification": None,
        }
        body["result_digest"] = compute_content_sha256(body)
        return MappingProxyType(body)

    body = {
        "schema_version": SCHEMA_VERSION,
        "resolution": "PORTFOLIO_RECORD",
        "reason": record.classification_reason,
        "family_gate_id": record.family_gate_id,
        "surface_id": record.surface_id,
        "portfolio_classification": record.portfolio_classification.value,
        "research_active": record.research_active,
        "bounded_domain_summary": record.bounded_domain_summary,
        "bounded_domain_refs": list(record.bounded_domain_refs),
        "resolver_participation": record.resolver_participation,
        "universe_member_implies_authorization": UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)


def assert_portfolio_census_closed_v1() -> None:
    unknowns = list_portfolio_unknown_or_conflicted_family_keys_v1()
    if unknowns:
        raise ValueError(f"portfolio_census_unresolved:{','.join(unknowns)}")
    verify_test_ready_cross_surface_isolation_v1()
    registry = build_authorized_surface_registry_v1()
    authorized_envelope = set(registry["authorized_surface_ids"])
    portfolio_active = set(list_research_active_surface_ids_v1())
    if authorized_envelope != portfolio_active:
        raise ValueError(
            "portfolio_envelope_drift:"
            f"envelope={sorted(authorized_envelope)} portfolio={sorted(portfolio_active)}"
        )
    assert_global_f3_surface_not_authorized_v1(surface_id=None)
    if direct_productive_write_possible_v1():
        raise ValueError("optimizer_direct_productive_write_forbidden")


def evaluate_meta_optimization_family_portfolio_gate_v1(
    *,
    optimization_family: str,
) -> MetaOptimizationFamilyPortfolioGateV1:
    token = _normalize_lookup_token(optimization_family)
    if token is None:
        return MetaOptimizationFamilyPortfolioGateV1(
            explicit_family_reference=False,
            research_choice_allowed=False,
            reason="",
            payload={},
        )

    resolution = resolve_optimization_surface_portfolio_v1(family_gate_id=token, surface_id=token)
    if resolution["resolution"] != "PORTFOLIO_RECORD":
        return MetaOptimizationFamilyPortfolioGateV1(
            explicit_family_reference=True,
            research_choice_allowed=False,
            reason=REASON_META_FAMILY_NOT_IN_CENSUS,
            payload={
                "optimization_family": token,
                "portfolio_resolution": resolution["resolution"],
            },
        )

    classification = str(resolution["portfolio_classification"])
    if classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE.value:
        allowed = bool(resolution["research_active"])
        reason = REASON_PORTFOLIO_AUTHORIZED_RESEARCH if allowed else REASON_PORTFOLIO_DEFERRED
        return MetaOptimizationFamilyPortfolioGateV1(
            explicit_family_reference=True,
            research_choice_allowed=allowed,
            reason=reason,
            payload={
                "optimization_family": token,
                "surface_id": resolution.get("surface_id"),
                "portfolio_classification": classification,
            },
        )
    if classification == PortfolioClassification.DEFERRED.value:
        return MetaOptimizationFamilyPortfolioGateV1(
            explicit_family_reference=True,
            research_choice_allowed=False,
            reason=REASON_META_FAMILY_DEFERRED,
            payload={
                "optimization_family": token,
                "portfolio_classification": classification,
            },
        )
    return MetaOptimizationFamilyPortfolioGateV1(
        explicit_family_reference=True,
        research_choice_allowed=False,
        reason=REASON_META_FAMILY_EXCLUDED,
        payload={
            "optimization_family": token,
            "portfolio_classification": classification,
        },
    )


def prove_phase_11_surface_portfolio_closure_v1() -> bool:
    try:
        assert_portfolio_census_closed_v1()
    except ValueError:
        return False
    if UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION:
        return False
    if CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION:
        return False
    if OPTIMIZATION_PROMOTION_AUTHORITY != "NONE":
        return False
    risk = resolve_optimization_surface_portfolio_v1(family_gate_id="RISK-SIZE")
    if risk.get("research_active") is not False:
        return False
    if (
        risk.get("portfolio_classification")
        != PortfolioClassification.EXCLUDED_CONSTITUTIONAL.value
    ):
        return False
    for sid in list_research_active_surface_ids_v1():
        first = resolve_optimization_surface_portfolio_v1(surface_id=sid)
        second = resolve_optimization_surface_portfolio_v1(surface_id=sid)
        if first["result_digest"] != second["result_digest"]:
            return False
    return True


__all__ = [
    "CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION",
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "NO_SELF_DEPLOY",
    "OPTIMIZATION_PRODUCTIVE_AUTHORITY",
    "OPTIMIZATION_PROMOTION_AUTHORITY",
    "PDF_PORTFOLIO_CONFIG",
    "PortfolioClassification",
    "OptimizationSurfacePortfolioRecordV1",
    "MetaOptimizationFamilyPortfolioGateV1",
    "REASON_META_FAMILY_DEFERRED",
    "REASON_META_FAMILY_EXCLUDED",
    "REASON_META_FAMILY_NOT_IN_CENSUS",
    "REASON_PORTFOLIO_AUTHORIZED_RESEARCH",
    "REASON_PORTFOLIO_DEFERRED",
    "REASON_PORTFOLIO_EXCLUDED",
    "SCHEMA_VERSION",
    "UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION",
    "WORKPACKAGE_ID",
    "assert_portfolio_census_closed_v1",
    "build_optimization_surface_portfolio_registry_v1",
    "evaluate_meta_optimization_family_portfolio_gate_v1",
    "list_authorized_research_surface_ids_v1",
    "list_portfolio_unknown_or_conflicted_family_keys_v1",
    "list_research_active_surface_ids_v1",
    "optimization_surface_portfolio_records_v1",
    "prove_phase_11_surface_portfolio_closure_v1",
    "resolve_optimization_surface_portfolio_v1",
]
