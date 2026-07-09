"""Contract tests for offline economic viability evidence gap assessment v0."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.research.offline_economic_viability_evidence_gap_assessment_v0 import (
    ASSESSMENT_SLICE_ID,
    DEFAULT_GAP_SCAN_EVIDENCE,
    DEFAULT_PARITY_CLOSEOUT_EVIDENCE,
    PACKAGE_MARKER,
    BindingReadiness,
    evaluate_offline_economic_viability_evidence_gap_assessment_v0,
    evaluate_system_economic_evidence_admissibility_preconditions_v0,
    inventory_reuse_owners_v0,
    render_admissibility_decision_json_v0,
    render_economic_gap_assessment_json_v0,
    scan_forbidden_positive_claims,
    verify_source_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_SLICE_CHANGED_FILES = (
    "src/research/offline_economic_viability_evidence_gap_assessment_v0.py",
    "scripts/research/run_offline_economic_viability_evidence_gap_assessment_v0.py",
    "tests/research/test_offline_economic_viability_evidence_gap_assessment_v0_contract.py",
)


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
    assert ASSESSMENT_SLICE_ID == "OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_V0"
    assert PACKAGE_MARKER == "OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_V0=true"


def test_reuse_inventory_complete_v0() -> None:
    rows = inventory_reuse_owners_v0(REPO_ROOT)
    assert rows
    assert all(row.present for row in rows)


@pytest.fixture(scope="module")
def module_assessment() -> object | None:
    parity = Path(DEFAULT_PARITY_CLOSEOUT_EVIDENCE)
    scan = Path(DEFAULT_GAP_SCAN_EVIDENCE)
    if not parity.is_dir() or not scan.is_dir():
        return None
    parity_ok, parity_rc, _ = verify_source_manifest(parity)
    scan_ok, scan_rc, _ = verify_source_manifest(scan)
    if not parity_ok or not scan_ok:
        return None
    return evaluate_offline_economic_viability_evidence_gap_assessment_v0(
        repo_root=REPO_ROOT,
        parity_closeout_dir=parity,
        gap_scan_dir=scan,
        parity_manifest_verify_rc=parity_rc,
        gap_scan_manifest_verify_rc=scan_rc,
    )


def test_current_head_assessment_documents_gap_no_evaluation_v0(
    module_assessment: object | None,
) -> None:
    if module_assessment is None:
        pytest.skip("source evidence bundles unavailable")
    result = module_assessment
    assert result.assessment_verdict == "PASS"
    assert result.plan_type == "ASSESSMENT_ONLY"
    assert result.primary_blocker == "SYSTEM_ECONOMIC_EVIDENCE_NOT_PROVEN"
    assert result.binding_completion_valid is True
    assert result.reuse_inventory_complete is True
    assert result.full_canonical_chain_wired is True
    assert result.backtest_runtime_decision_parity_pass is True
    assert result.system_economic_evidence_admissible is False
    assert result.runtime_rewire_admissible is False
    assert result.promotion_admissible is False
    assert result.forbidden_economic_evaluation_started is False
    assert len(result.candidate_rows) == 3


def test_fleet_candidates_have_expected_gap_reasons_v0(module_assessment: object | None) -> None:
    if module_assessment is None:
        pytest.skip("source evidence bundles unavailable")
    for row in module_assessment.candidate_rows:
        assert row.cost_binding_complete is True
        assert row.digest_binding_complete is True
        assert row.robustness_wiring_complete is True
        assert row.economic_evaluation_authorized is False
        assert row.manifest_verified_evidence_present is False
        assert "manifest_verified_economic_viability_evidence_missing" in row.gap_reasons
        assert row.binding_readiness is BindingReadiness.GAP


def test_admissibility_preconditions_fail_closed_v0(module_assessment: object | None) -> None:
    if module_assessment is None:
        pytest.skip("source evidence bundles unavailable")
    admissible, reasons = evaluate_system_economic_evidence_admissibility_preconditions_v0(
        binding_completion_valid=module_assessment.binding_completion_valid,
        candidate_rows=module_assessment.candidate_rows,
        parity_closeout_manifest_verified=module_assessment.parity_closeout_manifest_verified,
        reuse_inventory_complete=module_assessment.reuse_inventory_complete,
    )
    assert admissible is False
    assert reasons


def test_admissibility_decision_json_fail_closed_v0() -> None:
    payload = json.loads(render_admissibility_decision_json_v0(repo_root=REPO_ROOT))
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["promotion_admissible"] is False
    assert payload["economic_evaluation_authorized_in_assessment_scope"] is False


def test_economic_gap_assessment_json_has_dimension_summary_v0() -> None:
    payload = json.loads(render_economic_gap_assessment_json_v0(repo_root=REPO_ROOT))
    assert payload["dimension_summary"]["robustness_evidence_pass"] == "GAP"
    assert payload["dimension_summary"]["manifest_verified_economic_evidence_bundle"] == "GAP"
    assert payload["final_research_fleet"] == [
        "trend_following",
        "bollinger_bands",
        "momentum_1h",
    ]


def test_slice_has_no_forbidden_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "broker",
            "exchange",
            "testnet",
            "live",
            "scheduler",
        }
    )
    for rel in _SLICE_CHANGED_FILES:
        path = REPO_ROOT / rel
        if path.suffix != ".py":
            continue
        hits = _scan_forbidden_imports(path, forbidden)
        assert not hits, f"{rel}: {hits}"


def test_slice_forbidden_positive_claim_scan_clean_v0() -> None:
    violations = scan_forbidden_positive_claims(REPO_ROOT, list(_SLICE_CHANGED_FILES))
    assert violations == []
