"""PDF v3.3 final completion forensic adjudication tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1 import (
    DECISION_CONFIG,
    DoDStatusV1,
    POST_PDF_RUNTIME_EXTERNAL_BOUNDARY,
    WORKPACKAGE_ID,
    adjudicate_pdf_v3_3_d1_d29_v1,
    adjudicate_pdf_v3_3_rest_blocks_a_h_v1,
    build_pdf_v3_3_final_completion_summary_v1,
    compute_pdf_completion_v1,
    prove_meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_adjudication_proof_and_decision_binding() -> None:
    assert prove_meta_learning_optimization_universe_pdf_v3_3_final_completion_adjudication_v1(
        repo_root=REPO_ROOT
    )
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["pdf_completion"] is True
    assert decision["topic_composition_proven"] is True
    assert decision["earliest_remaining_pdf_blocker"] is None
    assert decision["post_pdf_runtime_external_boundary"] == POST_PDF_RUNTIME_EXTERNAL_BOUNDARY
    assert decision["external_order_effect_authorized"] is False
    assert decision["wire_send_required_for_pdf_completion"] is False
    assert decision["mv2_double_play_sole_trading_decision_authority_preserved"] is True


def test_pdf_completion_all_dod_proven() -> None:
    rows = adjudicate_pdf_v3_3_d1_d29_v1(repo_root=REPO_ROOT)
    assert len(rows) == 29
    statuses = {r.requirement_id: r.status for r in rows}
    assert statuses["D7"] == DoDStatusV1.PROVEN
    assert statuses["D12"] == DoDStatusV1.PROVEN
    assert statuses["D16"] == DoDStatusV1.PROVEN
    assert statuses["D17"] == DoDStatusV1.PROVEN
    assert statuses["D19"] == DoDStatusV1.PROVEN
    assert statuses["D20"] == DoDStatusV1.PROVEN
    assert statuses["D29"] == DoDStatusV1.PROVEN
    assert all(r.status == DoDStatusV1.PROVEN for r in rows)
    assert compute_pdf_completion_v1(repo_root=REPO_ROOT) is True


def test_rest_blocks_a_h_all_proven() -> None:
    blocks = adjudicate_pdf_v3_3_rest_blocks_a_h_v1(repo_root=REPO_ROOT)
    by_id = {b.block_id: b for b in blocks}
    for block_id in "ABCDEFGH":
        assert by_id[block_id].status.value == "PROVEN"
        assert by_id[block_id].remaining_blocker is None


def test_summary_counts_align_with_decision() -> None:
    summary = build_pdf_v3_3_final_completion_summary_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert summary["pdf_completion"] is True
    assert summary["topic_composition_proven"] is True
    assert summary["f3_status"] == "GLOBAL_SURFACE_EXCLUDED"
    assert summary["external_order_effect_authorized"] is False
    assert decision["d1_d29_proven"] == summary["d1_d29_counts"]["PROVEN"]
    assert summary["d1_d29_counts"]["PARTIAL"] == 0
