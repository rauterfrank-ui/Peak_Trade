"""Static contract: Owner/STA regime-coverage producer cybersecurity mirror."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_CYBERSECURITY_MIRROR_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION",
    "DECISION_ID=DEC_REGIME_COVERAGE_PRODUCER",
    "DECISION_STATUS=OPEN",
    "OWNER_VALUE=null",
    "BASELINE_ORIGIN_MAIN_SHA=42e8527c929264c702d8f7d59a80fc38f850baff",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "REGIME_COVERAGE_STATUS=SEMANTICALLY_UNRESOLVED",
    "EXISTING_PRODUCERS_ELEVATED=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false",
    "EXCHANGE_CREDENTIAL_EFFECTS=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CAMPAIGN_START_AUTHORIZED=true",
    "NOTION_SSOT=true",
    "EXISTING_PRODUCERS_ELEVATED=true",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=true",
)


def test_regime_coverage_cybersecurity_mirror_exists_v1() -> None:
    assert NOTE.is_file()


def test_regime_coverage_cybersecurity_mirror_markers_v1() -> None:
    text = NOTE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_security_notes_mirrors_regime_coverage_producer_decision_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1" in notes
    assert (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_REGIME_COVERAGE_PRODUCER_DECISION_V1.md"
    ) in notes
    assert "### 6.5 Stage-2 Surface B Owner/STA regime-coverage producer" in notes
    assert "DEC_REGIME_COVERAGE_PRODUCER" in notes
    assert "DECISION_STATUS=OPEN" in notes or "`OPEN`" in notes
    assert "EXISTING_PRODUCERS_ELEVATED=false" in notes
    assert "NOTION_SSOT=false" in notes
    assert "REPOSITORY_IS_SSOT=true" in notes
