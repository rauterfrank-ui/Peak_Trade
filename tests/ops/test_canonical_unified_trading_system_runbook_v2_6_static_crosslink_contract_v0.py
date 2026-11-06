"""Static crosslink contract for Canonical Unified Trading System Runbook v2.6.

Machine-anchors docs-only strategic target runbook integration from
PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md. Protects
CI_AUDIT ↔ DOCS_TRUTH_MAP reciprocal visibility without authorizing execution.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "architecture"
    / "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
GOVERNANCE = REPO_ROOT / "docs" / "GOVERNANCE_AND_SAFETY_OVERVIEW.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "docs_token: DOCS_TOKEN_PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6",
    "STATUS: CANONICAL_STRATEGIC_TARGET_AND_IMPLEMENTATION_RUNBOOK",
    "VERSION: 2.6",
    "FUTURES_ONLY: true",
    "LIVE_AUTHORIZED: false",
    "ORDERS_ALLOWED: false",
    "TRADING_DECISION_CORE",
    "SAFETY_EXECUTION_RUNTIME_CORE",
    "PEAK_TRADE_CANONICAL_TRADING_SYSTEM_SINGLE_SSOT=true",
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
    for marker in REQUIRED_MARKERS:
        assert marker in text, f"missing runbook marker: {marker}"


def test_runbook_does_not_claim_live_authorization() -> None:
    text = _read(RUNBOOK).lower()
    for claim in FORBIDDEN_STANDALONE_CLAIMS:
        assert claim not in text, f"forbidden standalone claim in runbook: {claim}"


def test_docs_truth_map_reciprocal_crosslink() -> None:
    text = _read(DOCS_TRUTH_MAP)
    assert "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md" in text
    assert "CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6_INTEGRATED=true" in text


def test_ci_audit_reciprocal_crosslink() -> None:
    text = _read(CI_AUDIT)
    assert "Canonical Unified Trading System Runbook v2.6" in text
    assert "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md" in text
    assert (
        "test_canonical_unified_trading_system_runbook_v2_6_static_crosslink_contract_v0.py" in text
    )


def test_governance_overview_points_to_runbook() -> None:
    text = _read(GOVERNANCE)
    assert "PEAK_TRADE_CANONICAL_UNIFIED_TRADING_SYSTEM_RUNBOOK_V2_6.md" in text
