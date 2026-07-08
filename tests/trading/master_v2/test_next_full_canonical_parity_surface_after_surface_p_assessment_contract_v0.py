"""Next full canonical parity surface after Surface P assessment contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.next_full_canonical_parity_surface_after_surface_p_assessment_v0 import (
    ASSESSMENT_SLICE_ID,
    DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE,
    DEFAULT_PR5023_CLOSEOUT_EVIDENCE,
    PACKAGE_MARKER,
    PLAN_TYPE,
    REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED,
    SELECTED_SURFACE,
    assessment_result_field_names_v0,
    collect_source_evidence_refs,
    evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0,
    render_next_full_canonical_parity_surface_matrix_json_v0,
    render_next_full_canonical_parity_surface_report_markdown_v0,
    resolve_next_unbound_canonical_parity_node_v0,
    scan_forbidden_positive_claims,
    verify_source_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/next_full_canonical_parity_surface_after_surface_p_assessment_v0.py",
    "scripts/ops/run_next_full_canonical_parity_surface_after_surface_p_assessment_v0.py",
    "tests/trading/master_v2/test_next_full_canonical_parity_surface_after_surface_p_assessment_contract_v0.py",
)

_SLICE_SOURCE_PATHS = tuple(REPO_ROOT / p for p in _SLICE_CHANGED_FILES if p.endswith(".py"))


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def test_assessment_constants_v0() -> None:
    assert ASSESSMENT_SLICE_ID == "NEXT_FULL_CANONICAL_PARITY_SURFACE_AFTER_SURFACE_P_ASSESSMENT_V0"
    assert PACKAGE_MARKER == "NEXT_FULL_CANONICAL_PARITY_SURFACE_AFTER_SURFACE_P_ASSESSMENT_V0=true"
    assert SELECTED_SURFACE == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"
    assert PLAN_TYPE == "ASSESSMENT_ONLY"
    assert NEXT_RECOMMENDED_SLICE == SELECTED_SURFACE


def test_surface_p_registry_partial_semantic_pass_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PARTIAL"


def test_resolve_next_unbound_node_when_trace_none_v0() -> None:
    resolved = resolve_next_unbound_canonical_parity_node_v0(
        trace_next_unbound_node="NONE",
        gap_assessment_next_recommended_slice=SELECTED_SURFACE,
        surface_p_semantic_post_status="PASS",
    )
    assert resolved == SELECTED_SURFACE


def test_pr5023_source_evidence_manifest_verified_when_available_v0() -> None:
    closeout = Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not closeout.is_dir() or not proof_bundle.is_dir():
        return
    ok, rc, detail = verify_source_manifest(closeout)
    assert ok is True
    assert rc == 0
    assert detail == "verified"
    refs = collect_source_evidence_refs(
        pr5023_closeout_dir=closeout,
        pr5022_proof_bundle_dir=proof_bundle,
    )
    assert all(ref.manifest_verified for ref in refs if ref.present)


def test_current_head_assessment_selects_boundary_chain_reassessment_v0() -> None:
    closeout = Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not closeout.is_dir():
        return
    result = evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
        repo_root=REPO_ROOT,
        pr5023_closeout_dir=closeout,
        pr5022_proof_bundle_dir=proof_bundle if proof_bundle.is_dir() else None,
        source_manifest_verify_rc=0,
    )
    assert result.assessment_verdict == "PASS"
    assert result.trace_next_unbound_node_before == "NONE"
    assert result.next_unbound_node == SELECTED_SURFACE
    assert result.selected_surface == SELECTED_SURFACE
    assert result.plan_type == PLAN_TYPE
    assert result.surface_p_registry_status == "PARTIAL"
    assert result.surface_p_semantic_post_status == "PASS"
    assert result.chain_surface_binding_complete is True
    assert result.blocked_reason == REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED
    assert result.next_step_after_pr == "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0"


def test_final_success_flags_remain_false_v0() -> None:
    closeout = Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    result = evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
        repo_root=REPO_ROOT,
        pr5023_closeout_dir=closeout,
        source_manifest_verify_rc=0,
    )
    assert result.full_canonical_chain_wired is False
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_rewire_admissible is False
    assert result.claim_promotion_allowed is False
    assert result.no_runtime_authority_confirmed is True
    assert result.no_economic_claim_confirmed is True


def test_missing_source_evidence_fails_closed_v0(tmp_path: Path) -> None:
    result = evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
        repo_root=REPO_ROOT,
        pr5023_closeout_dir=tmp_path / "missing",
        source_manifest_verify_rc=-1,
    )
    assert result.assessment_verdict == "FAIL_CLOSED"
    assert result.source_evidence_referenced is False


def test_matrix_json_schema_v0() -> None:
    closeout = Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    payload = json.loads(
        render_next_full_canonical_parity_surface_matrix_json_v0(
            repo_root=REPO_ROOT,
            pr5023_closeout_dir=closeout,
        )
    )
    assert payload["assessment_slice_id"] == ASSESSMENT_SLICE_ID
    assert payload["next_unbound_node"] == SELECTED_SURFACE
    assert payload["selected_surface"] == SELECTED_SURFACE
    assert payload["plan_type"] == PLAN_TYPE
    assert payload["full_canonical_chain_wired"] is False
    assert payload["source_evidence_refs"]


def test_report_markdown_documents_selection_v0() -> None:
    closeout = Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    report = render_next_full_canonical_parity_surface_report_markdown_v0(
        repo_root=REPO_ROOT,
        pr5023_closeout_dir=closeout,
    )
    assert "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE" in report
    assert SELECTED_SURFACE in report
    assert "NO_RUNTIME_AUTHORITY_CONFIRMED=true" in report
    assert "FULL_CANONICAL_CHAIN_WIRED=false" in report


def test_forbidden_positive_claims_scan_clean_v0() -> None:
    violations = scan_forbidden_positive_claims(REPO_ROOT, list(_SLICE_CHANGED_FILES))
    assert violations == []


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
        }
    )
    for path in _SLICE_SOURCE_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_assessment_result_has_required_fields_v0() -> None:
    names = assessment_result_field_names_v0()
    assert "trace_next_unbound_node_before" in names
    assert "next_unbound_node" in names
    assert "selected_surface" in names
    assert "blocked_reason" in names
    assert "next_step_after_pr" in names
