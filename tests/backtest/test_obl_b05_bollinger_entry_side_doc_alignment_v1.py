"""Static contracts for Bollinger entry-side doc alignment + open decision v1.

Non-authorizing: no productive src mutation, no side activation.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = (
    REPO_ROOT
    / "config"
    / "governance"
    / "obl_b05_bollinger_entry_side_doc_alignment_then_long_decision_v1.json"
)
GOV_DOC = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1.md"
)
AUTHORITY_SSOT = (
    REPO_ROOT
    / "config"
    / "governance"
    / "obl_b05_entry_exit_producer_side_authority_decision_v1.json"
)
AUTHORITY_DOC = (
    REPO_ROOT / "docs" / "governance" / "OBL_B05_ENTRY_EXIT_PRODUCER_SIDE_AUTHORITY_DECISION_V1.md"
)
SEMANTIC_DOC = REPO_ROOT / "docs" / "governance" / "OBL_B05_BOLLINGER_LONG_SEMANTIC_DECISION_V1.md"
CARRIER_DOC = (
    REPO_ROOT / "docs" / "governance" / "OBL_B05_ENTRY_EXIT_OPTIONAL_SIDE_CARRIER_CONTRACT_V1.md"
)
DECISION_D = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "STRATEGY_SIGNAL_CANONICAL_CONSUMER_ARCHITECTURE_DECISION_D_V1.md"
)

_OPTION_IDS = frozenset(
    {
        "OPTION_A_AUTHORIZE_LONG",
        "OPTION_B_KEEP_AMBIGUOUS_FAIL_CLOSED",
        "OPTION_C_EXTEND_PRODUCER_CONTRACT_DIFFERENTLY",
    }
)


def _ssot() -> dict:
    return json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def test_alignment_markers_and_non_authorizing_invariants() -> None:
    assert SSOT_PATH.is_file()
    assert GOV_DOC.is_file()
    data = _ssot()
    body = GOV_DOC.read_text(encoding="utf-8")
    assert data["slice_id"] == "OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1"
    assert data["BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_COMPLETE"] is True
    assert data["ACTIVE_SSOT_ALIGNED"] is True
    assert data["ENTRY_SIDE_CURRENT"] == "NONE"
    assert data["CONTRACT_STATE"] == "CONTRACT_REMAINS_AMBIGUOUS"
    assert data["BOLLINGER_SIDE_ACTIVATED"] is False
    assert data["SIDE_ACTIVATED"] is False
    assert data["PRODUCTIVE_SRC_CHANGED"] is False
    assert data["LONG_DECISION_MADE_IN_THIS_SLICE"] is False
    assert data["LIVE_AUTHORIZED"] is False
    assert data["ORDERS_ENABLED"] is False
    assert data["OPEN_DECISION"] == "BOLLINGER_ENTRY_SIDE_AUTHORITY_PENDING_SEPARATE_OPERATOR_GO"
    assert "DOCS_TOKEN_OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1" in body
    assert "ENTRY_SIDE_CURRENT: NONE" in body
    assert "LONG_DECISION_MADE_IN_THIS_SLICE: false" in body


def test_findings_matrix_separates_active_historical_and_productive() -> None:
    data = _ssot()
    matrix = data["findings_matrix"]
    assert isinstance(matrix, list) and len(matrix) >= 10
    layers = {row["layer"] for row in matrix}
    assert "ACTIVE_SSOT" in layers
    assert "HISTORICAL_EVIDENCE" in layers
    assert "PRODUCTIVE_SOURCE_OUT_OF_SCOPE" in layers
    preserved = [r for r in matrix if r["status"] == "PRESERVED_NOT_REINTERPRETED"]
    assert preserved
    untouched = [r for r in matrix if r["status"] == "CONTRADICTION_REMAINS_UNTOUCHED"]
    assert any("bollinger.py" in r["path"] for r in untouched)


def test_before_after_contract_and_open_options() -> None:
    data = _ssot()
    ba = data["before_after_contract_statement"]
    assert ba["before"]["bollinger_entry_authorized_side"] == "NONE"
    assert ba["after"]["bollinger_entry_authorized_side"] == "NONE"
    assert ba["after"]["cycle_signal_plus_one_authorizes_long"] is False
    assert ba["after"]["entry_side_none_is_intentional_fail_closed"] is True
    assert ba["after"]["long_activation_requires_separate_go"] is True
    options = {opt["id"] for opt in data["open_decision_brief"]["options"]}
    assert options == _OPTION_IDS
    assert data["LONG_DECISION_MADE_IN_THIS_SLICE"] is False


def test_active_authority_ssot_updated_without_activation() -> None:
    authority = json.loads(AUTHORITY_SSOT.read_text(encoding="utf-8"))
    assert authority["bollinger_entry_side_decision"] == "BLOCKED_AMBIGUITY"
    assert authority["bollinger_side_activated"] is False
    boll = next(r for r in authority["producers"] if r["producer_id"] == "bollinger_bands")
    assert boll["governance_docs_aligned_to_fail_closed_none"] is True
    assert boll["entry_side_current"] == "NONE"
    assert boll["cycle_signal_plus_one_authorizes_long"] is False
    assert boll["activation_slice_eligible"] is False
    assert (
        boll["open_authority_decision"]
        == "BOLLINGER_ENTRY_SIDE_AUTHORITY_PENDING_SEPARATE_OPERATOR_GO"
    )
    future = {row["slice_id_candidate"]: row for row in authority["future_activation_slices"]}
    assert (
        future["OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1"]["status"]
        == "COMPLETE_NON_AUTHORIZING"
    )
    assert (
        future["OBL_B05_BOLLINGER_ENTRY_SIDE_LONG_ACTIVATION_V1"]["status"]
        == "PENDING_SEPARATE_OPERATOR_GO"
    )


def test_active_narratives_point_to_alignment_and_fail_closed_law() -> None:
    for path in (AUTHORITY_DOC, SEMANTIC_DOC, CARRIER_DOC, DECISION_D, GOV_DOC):
        body = path.read_text(encoding="utf-8")
        assert "OBL_B05_BOLLINGER_ENTRY_SIDE_DOC_ALIGNMENT_THEN_LONG_DECISION_V1" in body
    authority_body = AUTHORITY_DOC.read_text(encoding="utf-8")
    assert "entry_side=NONE" in authority_body or "entry_side` bleibt `NONE`" in authority_body
    assert "cycle_signal_value=+1" in authority_body
    semantic_body = SEMANTIC_DOC.read_text(encoding="utf-8")
    assert "BOLLINGER_ENTRY_SIDE_AUTHORITY_PENDING_SEPARATE_OPERATOR_GO" in semantic_body


def test_diff_contains_no_productive_src_paths() -> None:
    """Guard: this slice must not change productive src/ (vs origin/main when available)."""
    proc = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        proc = subprocess.run(
            ["git", "diff", "--name-only", "origin/main"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
    files = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    # Also include unstaged/staged working tree against origin/main for local runs.
    proc2 = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    files.extend(ln.strip() for ln in proc2.stdout.splitlines() if ln.strip())
    proc3 = subprocess.run(
        ["git", "diff", "--name-only", "--cached", "origin/main"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    files.extend(ln.strip() for ln in proc3.stdout.splitlines() if ln.strip())
    src_hits = sorted({f for f in files if f.startswith("src/")})
    assert src_hits == [], f"unexpected productive src changes: {src_hits}"
