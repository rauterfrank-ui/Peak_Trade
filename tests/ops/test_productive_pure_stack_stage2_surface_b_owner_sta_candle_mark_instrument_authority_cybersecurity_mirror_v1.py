"""Static contract: Owner/STA candle-mark-instrument cybersecurity mirror."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_CYBERSECURITY_MIRROR_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION",
    "BASELINE_ORIGIN_MAIN_SHA=3b6b75bc4fa4b3ba6887ed055fa7fb88dd3d87b7",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "CANDLE_AUTHORITY_RATIFIED=true",
    "MARK_AUTHORITY_RATIFIED=true",
    "INSTRUMENT_BINDING_RATIFIED=true",
    "CAMPAIGN_START_AUTHORIZED=false",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false",
    "EXCHANGE_CREDENTIAL_EFFECTS=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "CANDLE_AUTHORITY_RATIFIED=false",
    "MARK_AUTHORITY_RATIFIED=false",
    "INSTRUMENT_BINDING_RATIFIED=false",
    "CAMPAIGN_START_AUTHORIZED=true",
    "NOTION_SSOT=true",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=true",
)


def test_owner_sta_cybersecurity_mirror_exists_v1() -> None:
    assert NOTE.is_file()


def test_owner_sta_cybersecurity_mirror_markers_v1() -> None:
    text = NOTE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_security_notes_mirrors_owner_sta_authority_decision_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "STAGE2_SURFACE_B_OWNER_STA_CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1" in notes
    assert (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_OWNER_STA_"
        "CANDLE_MARK_INSTRUMENT_AUTHORITY_DECISION_V1.md"
    ) in notes
    assert "### 6.4 Stage-2 Surface B Owner/STA candle-mark-instrument authority" in notes
    assert "CANDLE_AUTHORITY_RATIFIED=true" in notes
    assert "MARK_AUTHORITY_RATIFIED=true" in notes
    assert "INSTRUMENT_BINDING_RATIFIED=true" in notes
    assert "OWNER_STA_AUTHORITIES_RATIFIED_INSTANCE_FIELDS_STILL_OPEN" in notes
    assert "NOTION_SSOT=false" in notes
    assert "REPOSITORY_IS_SSOT=true" in notes
