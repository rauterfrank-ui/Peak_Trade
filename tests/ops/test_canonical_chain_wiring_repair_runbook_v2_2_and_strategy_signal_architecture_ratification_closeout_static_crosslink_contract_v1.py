"""Static crosslink contract for Chain Wiring Repair Runbook v2.2 + ratification closeout.

Machine-anchors docs-only adoption of
Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md and
STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md.
Protects CI_AUDIT ↔ DOCS_TRUTH_MAP reciprocal visibility without authorizing
Slice 2, runtime, orders, economic validity, or promotion.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md"
)
CLOSEOUT = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md"
)
GOVERNANCE_README = REPO_ROOT / "docs" / "governance" / "README.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

RUNBOOK_MARKERS: tuple[str, ...] = (
    "SLICE_1_COMPLETE=true",
    "PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1",
    "CANONICAL_REPLAY_INPUT_BUILDER_SINGLE_OWNER=true",
    "PR5226_SQUASH_MERGED=true",
    "SLICE_2_IMPLEMENTATION_BLOCKED=true",
    "CURRENT_CANONICAL_BASELINE_HEAD=",
    "6a37df8ab433b4d99a0a12d4c7c3c43d45774ea7",
)

CLOSEOUT_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=ARCHITECTURE_RATIFICATION_CLOSEOUT",
    "STATUS=RATIFIED_NEGATIVE",
    "ARCHITECTURE_RATIFICATION_SELECTION=D",
    "SLICE_2_IMPLEMENTATION_BLOCKED=true",
    "PROVENANCE_ONLY_BINDING_ALLOWED=false",
    "NEXT_AUTOMATIC_IMPLEMENTATION_SCOPE=NONE",
    "STRATEGY_SIGNAL_VALUE_CANONICAL_CONSUMER_STATUS=",
    "NO_SAFE_EXISTING_CANONICAL_CONSUMER",
)

FORBIDDEN_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "approved for live trading",
    "orders are authorized",
    "economic validity achieved",
    "promotion authorized",
    "mission complete=true",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def test_canonical_runbook_exists_with_post_slice_1_markers() -> None:
    text = _read(RUNBOOK)
    for marker in RUNBOOK_MARKERS:
        assert marker in text, f"missing runbook marker: {marker}"


def test_ratification_closeout_exists_with_selection_d_markers() -> None:
    text = _read(CLOSEOUT)
    for marker in CLOSEOUT_MARKERS:
        assert marker in text, f"missing closeout marker: {marker}"


def test_governance_readme_references_runbook_and_closeout() -> None:
    text = _read(GOVERNANCE_README)
    assert "Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md" in text
    assert "STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md" in text


def test_docs_truth_map_references_runbook_and_closeout() -> None:
    text = _read(DOCS_TRUTH_MAP)
    assert "Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md" in text
    assert "STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md" in text
    assert "CANONICAL_CHAIN_WIRING_REPAIR_RUNBOOK_V2_2_REPO_ADOPTED=true" in text
    assert "STRATEGY_SIGNAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1_REGISTERED=true" in text
    assert "SLICE_2_IMPLEMENTATION_BLOCKED=true" in text


def test_ci_audit_references_blocked_slice_2_status() -> None:
    text = _read(CI_AUDIT)
    assert "Peak_Trade_Canonical_Chain_Wiring_Repair_Master_Runbook_v2.2.md" in text
    assert "STRATEGY_SIGNAL_CANONICAL_ARCHITECTURE_RATIFICATION_CLOSEOUT_V1.md" in text
    assert "SLICE_2_IMPLEMENTATION_BLOCKED=true" in text
    assert (
        "test_canonical_chain_wiring_repair_runbook_v2_2_and_strategy_signal_architecture_ratification_closeout_static_crosslink_contract_v1.py"
        in text
    )


def test_docs_do_not_claim_mission_complete_or_live_authorization() -> None:
    for path in (RUNBOOK, CLOSEOUT):
        lowered = _read(path).lower()
        for claim in FORBIDDEN_STANDALONE_CLAIMS:
            assert claim not in lowered, f"forbidden claim in {path.name}: {claim}"
        # Explicit negative mission claim must remain.
        text = _read(path)
        assert "MISSION_COMPLETE=false" in text
