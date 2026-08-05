"""Static contract: Stage-2 Notion Mirror sync attestation v1."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTESTATION = REPO_ROOT / "docs" / "ops" / "PRODUCTIVE_PURE_STACK_STAGE2_NOTION_MIRROR_SYNC_V1.md"

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=NOTION_MIRROR_SYNC_ATTESTATION",
    "STATUS=MIRROR_SYNCED_TO_ORIGIN_MAIN",
    "ORIGIN_MAIN_SHA=216c6aa5c6f2a3e52fcf528f1374ca52194445d9",
    "PREVIOUS_MIRROR_SHA=c7111c748300b53884394569da679fcb91993007",
    "REBIND_FROM_SHA=c7111c748300b53884394569da679fcb91993007",
    "REBIND_TO_SHA=216c6aa5c6f2a3e52fcf528f1374ca52194445d9",
    "AUTHORITY_SURFACE=B",
    "PR_5729_RATIFIED=true",
    "PR_5730_MERGED=true",
    "INCLUDE_MERGES=5743,5744,5746,5747,5748",
    "PR_5743_MERGED=true",
    "PR_5744_MERGED=true",
    "PR_5746_MERGED=true",
    "PR_5747_MERGED=true",
    "PR_5748_MERGED=true",
    "SHADOW_CAMPAIGN_STARTABLE=true",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "PRODUCTIVE_NUMERIC_VALUES_SET=0",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "TRADING_LOGIC_CHANGED=false",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=false",
    "CAMPAIGN_START=false",
    "PACK_INPUT_GAP=CLOSED",
    "DASHBOARD_REGIME_BULL_BEAR_SWITCH=REMAINS_BLOCKED_OUT_OF_SCOPE",
    "NOTION_ROLE=MIRROR_ONLY",
    "NOTION_SSOT=false",
    "REPOSITORY_IS_SSOT=true",
    "SECOND_SSOT_CREATED=false",
)

FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "PRODUCTIVE_NUMERIC_VALUES_SET=1",
    "NOTION_SSOT=true",
    "SECOND_SSOT_CREATED=true",
    "DASHBOARD_AUTHORITY_EFFECT=AUTHORITATIVE",
    "ORDERS_TESTNET_LIVE_PAPER_EFFECTS=true",
    "TRADING_LOGIC_CHANGED=true",
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY_FLIP=true",
    "RUNTIME_IMPLEMENTED_FLIP=true",
)


def test_stage2_notion_mirror_attestation_exists_v1() -> None:
    assert ATTESTATION.is_file()


def test_stage2_notion_mirror_attestation_markers_v1() -> None:
    text = ATTESTATION.read_text(encoding="utf-8")
    for marker in REQUIRED_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text, claim


def test_stage2_notion_mirror_attestation_non_authorizing_v1() -> None:
    text = ATTESTATION.read_text(encoding="utf-8")
    assert "documentary Notion Mirror sync attestation" in text
    assert "no runtime, trading, security, or" in text
    assert "PRODUCTIVE_CALIBRATION_AUTHORIZED=false" in text
    assert "SECOND_SSOT_CREATED=false" in text
