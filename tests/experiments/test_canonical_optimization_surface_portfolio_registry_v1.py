"""Contract tests for Phase 11 optimization surface portfolio registry v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_f5_fresh_futures_input_freshness_optimizable_surface_v1 import (
    SURFACE_ID as F5_FRESH_SURFACE_ID,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    INTEGRATION_CONFIG,
    CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION,
    NO_SELF_DEPLOY,
    OPTIMIZATION_PROMOTION_AUTHORITY,
    PortfolioClassification,
    UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION,
    WORKPACKAGE_ID,
    assert_portfolio_census_closed_v1,
    build_optimization_surface_portfolio_registry_v1,
    evaluate_meta_optimization_family_portfolio_gate_v1,
    list_research_active_surface_ids_v1,
    optimization_surface_portfolio_records_v1,
    prove_phase_11_surface_portfolio_closure_v1,
    resolve_optimization_surface_portfolio_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_integration_config_aligns_with_workpackage() -> None:
    doc = json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert doc["phase_11_surface_portfolio_closure_status"] == "PROVEN_COMPLETE"


def test_every_family_has_exactly_one_portfolio_classification() -> None:
    records = optimization_surface_portfolio_records_v1()
    assert records
    keys = [record.family_key for record in records]
    assert len(keys) == len(set(keys))
    for record in records:
        assert record.portfolio_classification in PortfolioClassification


def test_authorized_research_surfaces_have_bounded_domains() -> None:
    for record in optimization_surface_portfolio_records_v1():
        if record.portfolio_classification != PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE:
            continue
        assert record.bounded_domain_summary
        assert record.bounded_domain_refs
        assert record.surface_id is not None


def test_deferred_and_excluded_not_research_active() -> None:
    for record in optimization_surface_portfolio_records_v1():
        if record.portfolio_classification == PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE:
            continue
        assert record.research_active is False
        resolution = resolve_optimization_surface_portfolio_v1(family_gate_id=record.family_gate_id)
        assert resolution["research_active"] is False


def test_risk_sizing_not_optimizable() -> None:
    resolution = resolve_optimization_surface_portfolio_v1(family_gate_id="RISK-SIZE")
    assert (
        resolution["portfolio_classification"]
        == PortfolioClassification.EXCLUDED_CONSTITUTIONAL.value
    )
    assert resolution["research_active"] is False


def test_universe_membership_does_not_imply_authorization_constants() -> None:
    assert UNIVERSE_MEMBERSHIP_IMPLIES_AUTHORIZATION is False
    registry = build_optimization_surface_portfolio_registry_v1()
    assert registry["universe_member_implies_authorization"] is False


def test_candidate_existence_does_not_imply_productive_configuration() -> None:
    assert CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION is False
    assert direct_productive_write_possible_v1() is False


def test_surface_resolution_is_deterministic() -> None:
    for sid in list_research_active_surface_ids_v1():
        first = resolve_optimization_surface_portfolio_v1(surface_id=sid)
        second = resolve_optimization_surface_portfolio_v1(surface_id=sid)
        assert first["result_digest"] == second["result_digest"]


def test_meta_portfolio_gate_authorizes_only_phase_11_research_surfaces() -> None:
    f1 = evaluate_meta_optimization_family_portfolio_gate_v1(optimization_family="F1")
    assert f1.research_choice_allowed is True
    f2 = evaluate_meta_optimization_family_portfolio_gate_v1(optimization_family=F2_SURFACE_ID)
    assert f2.research_choice_allowed is True
    risk = evaluate_meta_optimization_family_portfolio_gate_v1(optimization_family="RISK-SIZE")
    assert risk.research_choice_allowed is False
    f3 = evaluate_meta_optimization_family_portfolio_gate_v1(optimization_family="F3")
    assert f3.research_choice_allowed is False


def test_no_new_promotion_or_productive_write_authority() -> None:
    assert OPTIMIZATION_PROMOTION_AUTHORITY == "NONE"
    assert PROMOTION_AUTHORITY == "NONE"
    assert NO_SELF_DEPLOY is True


def test_portfolio_closure_proof_and_census() -> None:
    assert prove_phase_11_surface_portfolio_closure_v1()
    assert_portfolio_census_closed_v1()
    active = set(list_research_active_surface_ids_v1())
    assert active == {F1_SURFACE_ID, F2_SURFACE_ID, F5_FRESH_SURFACE_ID}


def test_synthetic_m4_context_excluded_from_research_active() -> None:
    resolution = resolve_optimization_surface_portfolio_v1(
        family_gate_id="M4-SYNTHETIC-OFFLINE-CONTEXT"
    )
    assert resolution["research_active"] is False
    assert (
        resolution["portfolio_classification"]
        == PortfolioClassification.EXCLUDED_CONSTITUTIONAL.value
    )


def test_unknown_surface_fail_closed() -> None:
    resolution = resolve_optimization_surface_portfolio_v1(surface_id="not.a.real.surface.v1")
    assert resolution["resolution"] == "NOT_IN_PORTFOLIO_CENSUS"
    assert resolution["research_active"] is False


@pytest.mark.parametrize(
    "family_gate_id,expected",
    [
        ("F1", PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE),
        ("F2", PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE),
        ("F5-FRESH", PortfolioClassification.AUTHORIZED_RESEARCH_SURFACE),
        ("F5-SURV", PortfolioClassification.DEFERRED),
        ("FUNDING-ONLY", PortfolioClassification.DEFERRED),
        ("F3", PortfolioClassification.EXCLUDED_CONSTITUTIONAL),
        ("OLS-DIAG", PortfolioClassification.EXCLUDED_CONSTITUTIONAL),
    ],
)
def test_blueprint_family_classification_matrix(
    family_gate_id: str, expected: PortfolioClassification
) -> None:
    resolution = resolve_optimization_surface_portfolio_v1(family_gate_id=family_gate_id)
    assert resolution["portfolio_classification"] == expected.value
