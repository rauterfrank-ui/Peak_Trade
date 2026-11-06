"""Static contract: STA open-inputs closeout cybersecurity mirror."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_CYBERSECURITY_MIRROR_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT",
    "DECISION_ID=DEC_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT",
    "DECISION_STATUS=RATIFIED",
    "OWNER_GO=OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1",
    "OWNER_GO_BASE_SHA=75ea4dc594a7f27b1fb490477e824a8c0a66d779",
    "CLOSED_INPUTS=non_invented_coverage_counts,provable_eth_usdt_swap_compatibility",
    "PRODUCER_REIMPLEMENTATION=false",
    "CONSUMER_WIRING=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "ORDERS_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
    "LIVE_AUTHORIZED=false",
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "PRODUCER_REIMPLEMENTATION=true",
    "CONSUMER_WIRING=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=true",
    "ORDERS_AUTHORIZED=true",
)


def test_closeout_cybersecurity_mirror_exists_v1() -> None:
    assert NOTE.is_file()


def test_closeout_cybersecurity_mirror_markers_v1() -> None:
    text = NOTE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_security_notes_mirrors_closeout_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_STA_OPEN_INPUTS_CLOSEOUT_V1" in notes
    assert (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_"
        "STA_OPEN_INPUTS_CLOSEOUT_V1.md"
    ) in notes
    assert "### 6.5 Stage-2 Surface B Owner/STA regime-coverage producer" in notes
    assert "75ea4dc594a7f27b1fb490477e824a8c0a66d779" in notes
    assert "non_invented_coverage_counts" in notes
    assert "provable_eth_usdt_swap_compatibility" in notes
