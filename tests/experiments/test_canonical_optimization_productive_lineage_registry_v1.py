"""Phase 12 productive lineage registry contract tests."""

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
from src.experiments.canonical_optimization_productive_lineage_registry_v1 import (
    INTEGRATION_CONFIG,
    CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION,
    OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
    OPTIMIZATION_PROMOTION_AUTHORITY,
    ProductiveRelevanceDisposition,
    RESEARCH_AUTHORIZATION_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    WORKPACKAGE_ID,
    assert_phase_12_census_closed_v1,
    assert_research_only_cannot_productive_apply_v1,
    build_productive_lineage_registry_v1,
    build_productive_lineage_surface_records_v1,
    derive_lineage_record_digest_v1,
    list_productive_relevance_unknown_surface_ids_v1,
    prove_f1_productive_lineage_chain_on_current_v1,
    prove_phase_12_productive_lineage_closure_v1,
    resolve_productive_lineage_v1,
)
from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    resolve_optimization_surface_portfolio_v1,
)
from src.governance.governed_productive_configuration_v1 import runtime_apply_possible_v1
from src.governance.optimization_proposal_governance_ingress_v1 import (
    direct_productive_write_possible_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_config_aligns_with_workpackage() -> None:
    doc = json.loads((REPO_ROOT / INTEGRATION_CONFIG).read_text(encoding="utf-8"))
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert doc["phase_12_productive_lineage_closure_status"] == "PROVEN_COMPLETE"


def test_productive_relevance_matrix_closed() -> None:
    records = build_productive_lineage_surface_records_v1()
    assert len(records) == 3
    by_id = {r.surface_id: r for r in records}
    assert by_id[F1_SURFACE_ID].disposition == ProductiveRelevanceDisposition.PRODUCTIVE_RELEVANT
    assert (
        by_id[F2_SURFACE_ID].disposition
        == ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
    )
    assert (
        by_id[F5_FRESH_SURFACE_ID].disposition
        == ProductiveRelevanceDisposition.RESEARCH_ONLY_NO_CURRENT_PRODUCTIVE_TARGET
    )
    assert list_productive_relevance_unknown_surface_ids_v1() == ()


def test_f1_lineage_chain_proven_on_current() -> None:
    assert prove_f1_productive_lineage_chain_on_current_v1(repo_root=REPO_ROOT)
    resolution = resolve_productive_lineage_v1(surface_id=F1_SURFACE_ID)
    assert resolution["lineage_chain_proven"] is True
    assert resolution["lineage_complete"] is True
    assert resolution["productive_apply_allowed"] is False
    assert resolution["runtime_apply_possible"] is False


def test_f2_f5_research_only_negative_proofs() -> None:
    for sid in (F2_SURFACE_ID, F5_FRESH_SURFACE_ID):
        assert_research_only_cannot_productive_apply_v1(surface_id=sid)
        resolution = resolve_productive_lineage_v1(surface_id=sid)
        assert resolution["lineage_chain_proven"] is False
        assert resolution["research_only_productive_apply_forbidden"] is True


def test_research_authorization_does_not_imply_productive() -> None:
    assert RESEARCH_AUTHORIZATION_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
    portfolio = resolve_optimization_surface_portfolio_v1(surface_id=F2_SURFACE_ID)
    lineage = resolve_productive_lineage_v1(surface_id=F2_SURFACE_ID)
    assert portfolio["research_active"] is True
    assert lineage["lineage_chain_proven"] is False


def test_optimizer_cannot_direct_write_and_no_promotion() -> None:
    assert OPTIMIZATION_PROMOTION_AUTHORITY == "NONE"
    assert OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE is False
    assert direct_productive_write_possible_v1() is False


def test_configuration_existence_does_not_imply_runtime_apply() -> None:
    assert CANDIDATE_IMPLIES_PRODUCTIVE_CONFIGURATION is False
    assert runtime_apply_possible_v1() is False
    resolution = resolve_productive_lineage_v1(surface_id=F1_SURFACE_ID)
    assert resolution["productive_apply_allowed"] is False


def test_wrong_surface_fail_closed() -> None:
    resolution = resolve_productive_lineage_v1(surface_id="not.a.registered.surface")
    assert resolution["resolution"] == "NOT_IN_PHASE_12_CENSUS"
    assert resolution["productive_apply_allowed"] is False


def test_lineage_replay_deterministic() -> None:
    record = next(
        r for r in build_productive_lineage_surface_records_v1() if r.surface_id == F1_SURFACE_ID
    )
    first = derive_lineage_record_digest_v1(record)
    second = derive_lineage_record_digest_v1(record)
    assert first == second
    reg1 = build_productive_lineage_registry_v1()
    reg2 = build_productive_lineage_registry_v1()
    assert reg1["registry_digest"] == reg2["registry_digest"]


def test_deferred_f5_surv_not_in_phase_12_census() -> None:
    resolution = resolve_productive_lineage_v1(surface_id="F5-SURV-NOT-A-SURFACE")
    assert resolution["resolution"] == "NOT_IN_PHASE_12_CENSUS"


def test_risk_sizing_not_in_authorized_research_surfaces() -> None:
    resolution = resolve_productive_lineage_v1(surface_id="risk.risk_per_trade")
    assert resolution["resolution"] == "NOT_IN_PHASE_12_CENSUS"


def test_phase_12_closure_proof() -> None:
    assert prove_phase_12_productive_lineage_closure_v1()
    assert_phase_12_census_closed_v1()


@pytest.mark.parametrize(
    "surface_id",
    [F1_SURFACE_ID, F2_SURFACE_ID, F5_FRESH_SURFACE_ID],
)
def test_every_authorized_surface_has_lineage_record(surface_id: str) -> None:
    resolution = resolve_productive_lineage_v1(surface_id=surface_id)
    assert resolution["resolution"] == "LINEAGE_RECORD"
