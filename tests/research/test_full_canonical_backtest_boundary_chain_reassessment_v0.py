from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from scripts.research.full_canonical_backtest_boundary_chain_reassessment_v0 import (
    ASSESSMENT_SCHEMA,
    ASSESSMENT_SLICE_ID,
    DEFAULT_PR5026_CLOSEOUT_EVIDENCE,
    FEATURE_BRANCH,
    NEXT_STEP_AFTER_PASS,
    REASON_PR5026_SOURCE_MISSING,
    SLICE_CHANGED_FILES,
    TRACE_PRIORITY,
    build_boundary_chain_reassessment,
    evaluate_closeout_reference,
    render_chain_boundary_matrix_text,
    render_reassessment_markdown,
    scan_forbidden_positive_claims,
    verify_source_manifest,
    write_manifest,
)

REPO_ROOT = Path.cwd()
_SLICE_SOURCE_PATHS = [REPO_ROOT / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]

FAKE_ASSESSMENT = {
    "assessment_verdict": "PASS",
    "boundary_chain_status": "FAIL_CLOSED_DOCUMENTED",
    "plan_type": "ASSESSMENT_ONLY",
    "narrow_rewire_justified": False,
    "trace_next_unbound_node": "NONE",
    "chain_surface_binding_complete": True,
    "gap_records_count": 0,
    "primary_blocker": "operator_go_token_status!=FAIL",
    "next_gap_or_next_step": NEXT_STEP_AFTER_PASS,
    "invariant_table": {
        "FULL_CANONICAL_CHAIN_WIRED": False,
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
        "RUNTIME_REWIRE_ADMISSIBLE": False,
        "NO_RUNTIME_AUTHORITY_CONFIRMED": True,
        "NO_ECONOMIC_CLAIM_CONFIRMED": True,
    },
    "chain_boundary_table": [
        {
            "boundary_id": "runtime_bridge_boundary",
            "display_name": "Runtime Bridge boundary (BOUND_NOT_ACTIVATED)",
            "trace_state": "BOUND_NOT_ACTIVATED_OFFLINE_PARITY_COMPLETE",
            "parity_status": "PARTIAL",
            "matrix_status": "PARTIAL_RUNTIME_ACTIVATION_PENDING",
            "offline_parity_gap": False,
            "missing_contract": "policy-blocked",
            "smallest_next_slice": NEXT_STEP_AFTER_PASS,
        }
    ],
}


def _closeout_dir() -> Path | None:
    path = Path(
        os.environ.get("PEAK_TRADE_PR5026_CLOSEOUT_EVIDENCE", DEFAULT_PR5026_CLOSEOUT_EVIDENCE)
    )
    return path if path.is_dir() else None


@pytest.fixture(scope="module")
def pr5026_closeout() -> Path | None:
    return _closeout_dir()


@pytest.fixture(scope="module")
def module_assessment(pr5026_closeout: Path | None) -> dict | None:
    if pr5026_closeout is None:
        return None
    return build_boundary_chain_reassessment(
        REPO_ROOT,
        pr5026_closeout_dir=pr5026_closeout,
        source_manifest_verify_rc=0,
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


def test_assessment_constants() -> None:
    assert ASSESSMENT_SLICE_ID == "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"
    assert ASSESSMENT_SCHEMA == "FullCanonicalBacktestBoundaryChainReassessmentV0"
    assert FEATURE_BRANCH == (
        "core-system-completion-full-canonical-backtest-boundary-chain-reassessment-v0"
    )
    assert NEXT_STEP_AFTER_PASS == "FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"


def test_pr5026_closeout_manifest_verified_when_available(pr5026_closeout: Path | None) -> None:
    if pr5026_closeout is None:
        pytest.skip("PR5026 closeout evidence not available offline")
    ok, rc, detail = verify_source_manifest(pr5026_closeout)
    assert ok is True
    assert rc == 0
    assert detail == "verified"


def test_fail_closed_reassessment_after_pr5026(module_assessment: dict | None) -> None:
    if module_assessment is None:
        pytest.skip("PR5026 closeout evidence not available offline")
    assert module_assessment["schema"] == ASSESSMENT_SCHEMA
    assert module_assessment["assessment_slice_id"] == ASSESSMENT_SLICE_ID
    assert module_assessment["assessment_verdict"] == "PASS"
    assert module_assessment["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
    assert module_assessment["plan_type"] == "ASSESSMENT_ONLY"
    assert module_assessment["narrow_rewire_justified"] is False
    assert module_assessment["trace_next_unbound_node"] == "NONE"
    assert module_assessment["chain_surface_binding_complete"] is True
    assert module_assessment["gap_records_count"] == 0
    assert module_assessment["runtime_bridge_boundary_status"] == "BOUND_NOT_ACTIVATED"
    assert module_assessment["runtime_bridge_pre_activation_gate_status"] == "FAIL"
    assert module_assessment["next_gap_or_next_step"] == NEXT_STEP_AFTER_PASS
    assert module_assessment["primary_blocker"] == "operator_go_token_status!=FAIL"
    assert module_assessment["parity_gap_matrix"]["summary"]["matrix_gap_count"] == 0

    invariants = module_assessment["invariant_table"]
    assert invariants["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert invariants["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert invariants["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert invariants["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert invariants["NO_RUNTIME_AUTHORITY_CONFIRMED"] is True
    assert invariants["NO_ECONOMIC_CLAIM_CONFIRMED"] is True

    by_id = {row["boundary_id"]: row for row in module_assessment["chain_boundary_table"]}
    for surface_id in TRACE_PRIORITY:
        assert by_id[surface_id]["trace_state"] == "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
    assert by_id["runtime_bridge_boundary"]["offline_parity_gap"] is False
    assert by_id["runtime_bridge_boundary"]["parity_status"] == "PASS"


def test_closeout_reference_missing_fails_closed(tmp_path: Path) -> None:
    _, _, fail_reasons = evaluate_closeout_reference(
        tmp_path / "missing",
        source_manifest_verify_rc=-1,
    )
    assert REASON_PR5026_SOURCE_MISSING in fail_reasons


def test_render_helpers_are_pure() -> None:
    markdown = render_reassessment_markdown(FAKE_ASSESSMENT)
    matrix = render_chain_boundary_matrix_text(FAKE_ASSESSMENT)
    assert "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE" in markdown
    assert "CHAIN_BOUNDARY_MATRIX" in matrix
    assert "NONE" in matrix


def test_forbidden_positive_claims_scan_clean() -> None:
    violations = scan_forbidden_positive_claims(_SLICE_SOURCE_PATHS)
    assert violations == []


def test_slice_sources_exclude_runtime_imports() -> None:
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


def test_write_manifest_verifies_minimal_explicit_artifacts(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "artifact_a.txt").write_text("alpha\n", encoding="utf-8")
    (evidence_dir / "artifact_b.json").write_text(
        json.dumps({"schema": "TinyFixture", "ok": True}) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "final_report.txt").write_text("VERDICT=FIXTURE\n", encoding="utf-8")
    manifest_rc = write_manifest(evidence_dir)
    assert manifest_rc == 0
    ok, rc, detail = verify_source_manifest(evidence_dir)
    assert ok is True
    assert rc == 0
    assert detail == "verified"
