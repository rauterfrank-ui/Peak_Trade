"""Static crosslink contract for Vollautonomie-Runbook v4.4.10 + Implementation Contract.

Machine-anchors docs-only canonical governance runbook adoption from
Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md
and PEAK_TRADE_IMPLEMENTATION_CONTRACT.md. Protects CI_AUDIT ↔ DOCS_TRUTH_MAP
reciprocal visibility without authorizing execution.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "governance"
    / "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md"
)
SHORT_CONTRACT = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_IMPLEMENTATION_CONTRACT.md"
GOVERNANCE_README = REPO_ROOT / "docs" / "governance" / "README.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

RUNBOOK_MARKERS: tuple[str, ...] = (
    "Kanonisches Vollautonomie-Runbook v4.4.10",
    "4.4.10-core-trading-ssot-state-independent-implementation-contract",
    "RUNBOOK_CANONICAL_NORMS_ARE_STATE_INDEPENDENT=true",
    "FUTURES_ONLY=true",
    "LIVE_AUTHORIZED=false",
    "CURSOR_MAY_NOT_REWRITE_RUNBOOK_FOR_PROGRESS_TRACKING=true",
)

SHORT_CONTRACT_MARKERS: tuple[str, ...] = (
    "CANONICAL_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md",
    "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true",
    "THIS_DOCUMENT_MAY_NOT_OVERRIDE_CANONICAL_RUNBOOK=true",
    "CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true",
    "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md",
)

FORBIDDEN_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "approved for live trading",
    "orders are authorized",
    "scheduler runtime allowed",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def test_runbook_exists_with_required_metadata_markers() -> None:
    text = _read(RUNBOOK)
    for marker in RUNBOOK_MARKERS:
        assert marker in text, f"missing runbook marker: {marker}"


def test_runbook_does_not_claim_live_authorization() -> None:
    text = _read(RUNBOOK).lower()
    for claim in FORBIDDEN_STANDALONE_CLAIMS:
        assert claim not in text, f"forbidden standalone claim in runbook: {claim}"


def test_short_contract_is_navigation_only_not_second_ssot() -> None:
    text = _read(SHORT_CONTRACT)
    for marker in SHORT_CONTRACT_MARKERS:
        assert marker in text, f"missing short contract marker: {marker}"


def test_governance_readme_points_to_runbook_and_short_contract() -> None:
    text = _read(GOVERNANCE_README)
    assert "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md" in text
    assert "PEAK_TRADE_IMPLEMENTATION_CONTRACT.md" in text
    assert "THIS_DOCUMENT_IS_NOT_A_SECOND_SSOT=true" in text


def test_docs_truth_map_reciprocal_crosslink() -> None:
    text = _read(DOCS_TRUTH_MAP)
    assert "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md" in text
    assert "PEAK_TRADE_IMPLEMENTATION_CONTRACT.md" in text
    assert "CANONICAL_VOLLAUTONOMIE_RUNBOOK_V4_4_10_REPO_ADOPTED=true" in text
    assert "CURSOR_MUST_READ_CANONICAL_RUNBOOK_FIRST=true" in text


def test_ci_audit_reciprocal_crosslink() -> None:
    text = _read(CI_AUDIT)
    assert "Vollautonomie-Runbook v4.4.10" in text
    assert "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md" in text
    assert "PEAK_TRADE_IMPLEMENTATION_CONTRACT.md" in text
    assert (
        "test_canonical_vollautonomie_runbook_v4_4_10_and_implementation_contract_static_crosslink_contract_v0.py"
        in text
    )
