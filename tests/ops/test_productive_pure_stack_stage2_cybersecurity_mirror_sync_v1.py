"""Static contract: Stage-2 Cybersecurity Mirror sync attestation v1."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTESTATION = (
    REPO_ROOT / "docs" / "ops" / "PRODUCTIVE_PURE_STACK_STAGE2_CYBERSECURITY_MIRROR_SYNC_V1.md"
)
SECURITY_NOTES = REPO_ROOT / "SECURITY_NOTES.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=CYBERSECURITY_MIRROR_SYNC_ATTESTATION",
    "STATUS=MIRROR_SYNCED_TO_ORIGIN_MAIN",
    "ORIGIN_MAIN_SHA=6db2d4920ace92cab8fc2bab834b75446808d1a1",
    "AUTHORITY_SURFACE=B",
    "PR_5729_RATIFIED=true",
    "PR_5730_MERGED=true",
    "PR_5731_MERGED=true",
    "SHADOW_CAMPAIGN_STARTABLE=true",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "TRADING_LOGIC_CHANGED=false",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false",
    "EXCHANGE_CREDENTIAL_EFFECTS=false",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "PRODUCTIVE_NUMERIC_VALUES_SET=1",
    "NOTION_SSOT=true",
    "DASHBOARD_AUTHORITY_EFFECT=AUTHORITATIVE",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=true",
    "EXCHANGE_CREDENTIAL_EFFECTS=true",
    "TRADING_LOGIC_CHANGED=true",
)

SECURITY_NOTES_REQUIRED: tuple[str, ...] = (
    "STAGE2_SURFACE_B_CYBERSECURITY_MIRROR_SYNC_V1",
    "6db2d4920ace92cab8fc2bab834b75446808d1a1",
    "PRODUCTIVE_PURE_STACK_STAGE2_CYBERSECURITY_MIRROR_SYNC_V1.md",
    "INPUT_AUTHORITY",
    "SHADOW_CAMPAIGN_STARTABLE",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
)


def test_stage2_cybersecurity_mirror_attestation_exists_v1() -> None:
    assert ATTESTATION.is_file()


def test_stage2_cybersecurity_mirror_attestation_markers_v1() -> None:
    text = ATTESTATION.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_stage2_cybersecurity_mirror_attestation_non_authorizing_v1() -> None:
    text = ATTESTATION.read_text(encoding="utf-8")
    assert "documentary Cybersecurity Mirror sync attestation" in text
    assert "PRODUCTIVE_CALIBRATION_AUTHORIZED=false" in text
    assert "CYBERSECURITY_RUNTIME_AUTHORIZATION_EFFECT=NONE" in text
    assert "evidence-collection startability only" in text


def test_security_notes_mirror_stage2_surface_b_boundaries_v1() -> None:
    notes = SECURITY_NOTES.read_text(encoding="utf-8")
    for marker in SECURITY_NOTES_REQUIRED:
        assert marker in notes, marker
    assert "### 6.2 Stage-2 Surface B cybersecurity mirror sync" in notes
    assert "not active productive input authority" in notes
    assert "Exchange credentials / order adapters" in notes
