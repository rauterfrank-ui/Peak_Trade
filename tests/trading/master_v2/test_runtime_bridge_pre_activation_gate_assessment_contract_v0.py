"""Runtime Bridge Pre-Activation Gate Assessment contract tests (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0 import (
    ASSESSMENT_SLICE_ID,
    DEFAULT_PR5024_CLOSEOUT_EVIDENCE,
    PACKAGE_MARKER,
    PLAN_TYPE,
    assessment_result_field_names_v0,
    collect_source_evidence_refs,
    evaluate_runtime_bridge_pre_activation_gate_assessment_v0,
    render_runtime_bridge_pre_activation_gate_matrix_json_v0,
    render_runtime_bridge_pre_activation_gate_report_markdown_v0,
    scan_forbidden_positive_claims,
    verify_source_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

_SLICE_CHANGED_FILES = (
    "src/trading/master_v2/runtime_bridge_pre_activation_gate_assessment_v0.py",
    "scripts/ops/run_runtime_bridge_pre_activation_gate_assessment_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_assessment_contract_v0.py",
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
    assert ASSESSMENT_SLICE_ID == "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0"
    assert PACKAGE_MARKER == "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0=true"
    assert PLAN_TYPE == "ASSESSMENT_ONLY"


def test_pr5024_source_evidence_manifest_verified_when_available_v0() -> None:
    closeout = Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    ok, rc, detail = verify_source_manifest(closeout)
    assert ok is True
    assert rc == 0
    assert detail == "verified"
    refs = collect_source_evidence_refs(pr5024_closeout_dir=closeout)
    assert refs[0].manifest_verified is True


def test_current_head_assessment_documents_fail_closed_gate_v0() -> None:
    closeout = Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    result = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=closeout,
        source_manifest_verify_rc=0,
    )
    assert result.assessment_verdict == "PASS"
    assert result.gate_assessment_status == "FAIL_CLOSED_DOCUMENTED"
    assert result.runtime_bridge_pre_activation_gate_status == "FAIL"
    assert result.runtime_bridge_activation_admissible is False
    assert result.surface_p_registry_status == "PARTIAL"
    assert result.surface_p_semantic_post_status == "PASS"
    assert len(result.blocking_reasons) > 0
    assert len(result.required_next_gates) > 0
    assert "surface_p_status!=FAIL" in result.blocking_reasons


def test_final_success_flags_remain_false_v0() -> None:
    closeout = Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    result = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=closeout,
        source_manifest_verify_rc=0,
    )
    assert result.full_canonical_chain_wired is False
    assert result.backtest_runtime_decision_parity_pass is False
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_rewire_admissible is False
    assert result.claim_promotion_allowed is False
    assert result.no_runtime_authority_confirmed is True
    assert result.no_economic_claim_confirmed is True
    assert result.no_runtime_evidence_before_core_system_complete is True


def test_missing_source_evidence_fails_closed_v0(tmp_path: Path) -> None:
    result = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=tmp_path / "missing",
        source_manifest_verify_rc=-1,
    )
    assert result.assessment_verdict == "FAIL_CLOSED"
    assert result.source_evidence_referenced is False


def test_matrix_json_schema_v0() -> None:
    closeout = Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    payload = json.loads(
        render_runtime_bridge_pre_activation_gate_matrix_json_v0(
            pr5024_closeout_dir=closeout,
        )
    )
    assert payload["assessment_slice_id"] == ASSESSMENT_SLICE_ID
    assert payload["gate_assessment_status"] == "FAIL_CLOSED_DOCUMENTED"
    assert payload["runtime_bridge_pre_activation_gate_status"] == "FAIL"
    assert payload["runtime_bridge_activation_admissible"] is False
    assert payload["full_canonical_chain_wired"] is False
    assert payload["source_evidence_refs"]


def test_report_markdown_documents_gate_boundary_v0() -> None:
    closeout = Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    if not closeout.is_dir():
        return
    report = render_runtime_bridge_pre_activation_gate_report_markdown_v0(
        pr5024_closeout_dir=closeout,
    )
    assert "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE" in report
    assert "runtime_bridge_pre_activation_gate_status: FAIL" in report
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
    assert "gate_assessment_status" in names
    assert "primary_blocker" in names
    assert "next_step_after_pr" in names
    assert "no_runtime_evidence_before_core_system_complete" in names
