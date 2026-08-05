"""Static contract: Surface-B raw PT1M input-pack cybersecurity mirror note."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
NOTE = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_CYBERSECURITY_MIRROR_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_NOTE",
    "CAPABILITY_SCOPE=SURFACE_B_RAW_PT1M_CANDLE_MARK_INPUT_PACK_AND_CAMPAIGN_INSTANCE_BINDING",
    "BASELINE_ORIGIN_MAIN_SHA=81315806a9501ab7872b9fc0c54bafa82eff5920",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
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
    "CAMPAIGN_START_AUTHORIZED=true",
    "NOTION_SSOT=true",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=true",
)


def test_raw_input_pack_cybersecurity_mirror_exists_v1() -> None:
    assert NOTE.is_file()


def test_raw_input_pack_cybersecurity_mirror_markers_v1() -> None:
    text = NOTE.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_security_notes_mirrors_raw_input_pack_owner_decision_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    assert "STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1" in notes
    assert (
        "PRODUCTIVE_PURE_STACK_STAGE2_SURFACE_B_RAW_PT1M_INPUT_PACK_OWNER_DECISION_V1.md" in notes
    )
    assert "CAMPAIGN_START_AUTHORIZED=false" in notes
    assert "### 6.3 Stage-2 Surface B raw PT1M input-pack Owner Decision" in notes
    assert "NOTION_SSOT=false" in notes
    assert "REPOSITORY_IS_SSOT=true" in notes
