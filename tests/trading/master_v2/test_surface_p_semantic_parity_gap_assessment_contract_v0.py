"""Surface P semantic parity gap assessment contract tests (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    parity_surface_assessments_v0,
)
from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
    CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
)
from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
    REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0,
    derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0,
)
from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
    ASSESSMENT_SLICE_ID,
    DEFAULT_PR5022_CLOSEOUT_EVIDENCE,
    DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE,
    PACKAGE_MARKER,
    REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED,
    assessment_result_field_names_v0,
    collect_source_evidence_refs,
    evaluate_surface_p_semantic_parity_gap_assessment_v0,
    render_surface_p_semantic_parity_gap_matrix_json_v0,
    render_surface_p_semantic_parity_gap_report_markdown_v0,
    scan_forbidden_positive_claims,
    verify_source_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/surface_p_semantic_parity_gap_assessment_v0.py",
    "scripts/ops/run_surface_p_semantic_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_surface_p_semantic_parity_gap_assessment_contract_v0.py",
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
    assert ASSESSMENT_SLICE_ID == "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0"
    assert PACKAGE_MARKER == "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0=true"


def test_surface_p_gap_assessment_pre_status_partial_v0() -> None:
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    assert surface_p.parity_status == "PARTIAL"
    assert "BOUND_NOT_ACTIVATED" in surface_p.missing_binding_if_any


def test_semantic_binding_confirmations_complete_from_gap_assessment_v0() -> None:
    confirmations = derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
    assert all(confirmations[key] for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0)


def test_pr5022_source_evidence_manifest_verified_when_available_v0() -> None:
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    closeout = Path(DEFAULT_PR5022_CLOSEOUT_EVIDENCE)
    if not proof_bundle.is_dir() or not closeout.is_dir():
        return
    ok, rc, detail = verify_source_manifest(proof_bundle)
    assert ok is True
    assert rc == 0
    assert detail == "verified"
    refs = collect_source_evidence_refs(
        pr5022_proof_bundle_dir=proof_bundle,
        pr5022_closeout_dir=closeout,
    )
    assert all(ref.manifest_verified for ref in refs if ref.present)


def test_current_head_assessment_proves_semantic_parity_beyond_trace_binding_v0() -> None:
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not proof_bundle.is_dir():
        return
    result = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=proof_bundle,
        source_manifest_verify_rc=0,
    )
    assert result.surface_p_gap_assessment_parity_status == "PARTIAL"
    assert result.semantic_parity_beyond_trace_binding == "PASS"
    assert result.surface_p_post_status == "PASS"
    assert result.offline_four_way_fixtures_complete is True
    assert result.semantic_binding_confirmations_complete is True
    assert result.pr5022_trace_surface_coverage_complete is True
    assert result.pr5022_chain_surface_binding_complete is True
    assert result.source_evidence_referenced is True
    assert result.next_blocker == REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED
    assert CANONICAL_RUNTIME_ENTRYPOINT_STATUS == "BOUND_NOT_ACTIVATED"


def test_final_success_flags_remain_false_v0() -> None:
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not proof_bundle.is_dir():
        return
    result = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=proof_bundle,
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
    result = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=tmp_path / "missing",
        source_manifest_verify_rc=-1,
    )
    assert result.semantic_parity_beyond_trace_binding == "FAIL_CLOSED"
    assert result.surface_p_post_status == "PARTIAL_FAIL_CLOSED"
    assert result.source_evidence_referenced is False


def test_gap_matrix_json_schema_v0() -> None:
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not proof_bundle.is_dir():
        return
    payload = json.loads(
        render_surface_p_semantic_parity_gap_matrix_json_v0(
            pr5022_proof_bundle_dir=proof_bundle,
        )
    )
    assert payload["assessment_slice_id"] == ASSESSMENT_SLICE_ID
    assert payload["surface_p_gap_assessment_parity_status"] == "PARTIAL"
    assert payload["semantic_parity_beyond_trace_binding"] == "PASS"
    assert payload["surface_p_post_status"] == "PASS"
    assert payload["full_canonical_chain_wired"] is False
    assert payload["source_evidence_refs"]


def test_gap_report_markdown_documents_partial_reason_v0() -> None:
    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    if not proof_bundle.is_dir():
        return
    report = render_surface_p_semantic_parity_gap_report_markdown_v0(
        pr5022_proof_bundle_dir=proof_bundle,
    )
    assert "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE" in report
    assert "BOUND_NOT_ACTIVATED" in report
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
    assert "surface_p_post_status" in names
    assert "semantic_parity_beyond_trace_binding" in names
    assert "next_blocker" in names
