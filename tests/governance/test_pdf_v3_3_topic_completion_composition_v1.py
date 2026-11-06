"""PDF v3.3 topic completion composition — positive closure and fail-closed negatives."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
    CONSUMER_BINDING_REGISTRY,
    F1_CAMPAIGN_ADJUDICATION,
    PROMOTION_RESULTS_REGISTRY,
    SURFACE_PORTFOLIO_CONFIG,
    WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION,
    build_pdf_v3_3_completion_flags_v1,
    prove_pdf_v3_3_integrated_evidence_plane_v1,
    prove_pdf_v3_3_m10_promotion_boundary_v1,
    prove_pdf_v3_3_productive_parameter_lineage_chain_v1,
    prove_pdf_v3_3_promotion_relevant_results_closure_v1,
    prove_pdf_v3_3_surface_isolation_v1,
    prove_pdf_v3_3_topic_completion_composition_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    direct_productive_write_possible_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_wire_send_not_required_for_pdf_completion() -> None:
    assert WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION is False


def test_topic_completion_composition_positive_closure() -> None:
    assert prove_pdf_v3_3_topic_completion_composition_v1(repo_root=REPO_ROOT)
    flags = build_pdf_v3_3_completion_flags_v1(repo_root=REPO_ROOT)
    assert flags["composition_proven"] is True
    assert flags["s02_required_for_pdf_completion"] is False
    assert flags["s02_authorized"] is False
    assert flags["m10_boundary_proven"] is True


def test_integrated_evidence_plane_and_isolation() -> None:
    assert prove_pdf_v3_3_integrated_evidence_plane_v1(repo_root=REPO_ROOT)
    assert prove_pdf_v3_3_surface_isolation_v1(repo_root=REPO_ROOT)


def test_promotion_results_registry_finite() -> None:
    reg = json.loads((REPO_ROOT / PROMOTION_RESULTS_REGISTRY).read_text(encoding="utf-8"))
    results = reg.get("results")
    assert isinstance(results, list)
    assert len(results) == int(reg.get("promotion_relevant_result_count", 0))
    assert prove_pdf_v3_3_promotion_relevant_results_closure_v1(repo_root=REPO_ROOT)


def test_m10_boundary_no_self_deploy() -> None:
    assert prove_pdf_v3_3_m10_promotion_boundary_v1(repo_root=REPO_ROOT)
    assert direct_productive_write_possible_v1() is False


def test_productive_lineage_without_direct_write() -> None:
    assert prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=REPO_ROOT)


def test_foreign_promotion_registry_breaks_closure(tmp_path: Path) -> None:
    root = tmp_path
    for rel in (
        SURFACE_PORTFOLIO_CONFIG,
        CONSUMER_BINDING_REGISTRY,
        F1_CAMPAIGN_ADJUDICATION,
        "config/governance/f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1_decision_v1.json",
    ):
        src = REPO_ROOT / rel
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    bad = json.loads((REPO_ROOT / PROMOTION_RESULTS_REGISTRY).read_text(encoding="utf-8"))
    bad["promotion_relevant_result_count"] = 99
    (root / PROMOTION_RESULTS_REGISTRY).parent.mkdir(parents=True, exist_ok=True)
    (root / PROMOTION_RESULTS_REGISTRY).write_text(json.dumps(bad), encoding="utf-8")

    assert prove_pdf_v3_3_promotion_relevant_results_closure_v1(repo_root=root) is False


def test_s02_required_flag_breaks_block_a(tmp_path: Path) -> None:
    root = tmp_path
    adj_src = json.loads((REPO_ROOT / F1_CAMPAIGN_ADJUDICATION).read_text(encoding="utf-8"))
    adj_src["s02_required_for_pdf_completion"] = True
    dest = root / F1_CAMPAIGN_ADJUDICATION
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(adj_src), encoding="utf-8")
    from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
        prove_pdf_v3_3_f1_campaign_block_a_v1,
    )

    assert prove_pdf_v3_3_f1_campaign_block_a_v1(repo_root=root) is False
