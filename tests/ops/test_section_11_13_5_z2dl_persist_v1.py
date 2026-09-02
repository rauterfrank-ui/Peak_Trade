"""§11.13.5.Z2DL persist invariants for the one-shot account/config GET."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO as CODE_OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dl_post_remediation_single_private_auth_get_v1"
    / "20260902T193121Z"
)

Z2DK_HEADING = "### 11.13.5.Z2DK GET redirect fail-closed on existing canary urllib transport"
Z2DL_HEADING = "### 11.13.5.Z2DL Post-remediation single private authenticated GET"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1"
Z2DK_OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DK_GET_REDIRECT_FAILCLOSED_TRANSPORT_REMEDIATION_V1"
BASELINE_SHA = "a074995099ad8473a79cf281adc8052de0b874bd"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_FURTHER_PRIVATE_GET_OR_POST_"
    "OR_FUNDING_OR_POSITIONS_OR_EXECUTION"
)
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dl_section(text: str) -> str:
    start = text.find(Z2DL_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DL heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DL"
    return text[start:end]


def _z2dk_section(text: str) -> str:
    start = text.find(Z2DK_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DK heading"
    end = text.find(Z2DL_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DL boundary after Z2DK"
    return text[start:end]


def test_z2dl_heading_is_unique_and_follows_z2dk() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DL_HEADING) == 1
    assert 0 <= text.find(Z2DK_HEADING) < text.find(Z2DL_HEADING) < text.find(LADDER_HEADING)


def test_z2dk_text_was_not_rewritten() -> None:
    section = _z2dk_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DK" in section
    assert f"OWNER_GO={Z2DK_OWNER_GO}" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DK" in section
    assert "GET_REDIRECT_FAILCLOSED=true" in section
    assert "PRIVATE_GET_PERFORMED=false" in section
    assert "PRIVATE_API_AUTH_SUCCESS=UNPROVEN" in section
    assert "11.13.5.Z2DL" not in section
    assert OWNER_GO not in section


def test_z2dl_docs_bind_one_account_config_get_without_activation() -> None:
    section = _z2dl_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DL_POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_ONLY",
        "Z2DL_SCOPE=EXACTLY_ONE_ACCOUNT_CONFIG_GET_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"CURRENT_EXECUTION_BASE_SHA={BASELINE_SHA}",
        f"Z2DK_SQUASH_SHA={BASELINE_SHA}",
        "LAST_MERGED_PR=6223",
        "PREDECESSOR_SLICE=11.13.5.Z2DK",
        "THIS_SLICE=11.13.5.Z2DL",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DL",
        "AUTHORIZED_ENDPOINT=GET /api/v5/account/config",
        "EXECUTED_ENDPOINT=/api/v5/account/config",
        "EXECUTED_HOST=eea.okx.com",
        "EXECUTED_HTTP_METHOD=GET",
        "UTC_TIMESTAMP=2026-09-02T19:31:21Z",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "GET_COUNT=1",
        "ACTUAL_NETWORK_REQUEST_COUNT=1",
        "HTTP_EXCHANGE_COUNT=1",
        "SECOND_REQUEST_PERFORMED=false",
        "REDIRECT_FOLLOWED=false",
        "PRIVATE_GET_PERFORMED=true",
        "PRIVATE_API_AUTH_SUCCESS=true",
        "AUTHENTICATED_PRIVATE_API_REACHABILITY_PROVEN=true",
        "RUNTIME_50110_CLEARANCE=true",
        "ROOT_CAUSE=UNPROVEN",
        "FUNDING_GET_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "ORDER_PERFORMED=false",
        "EXECUTION_PERFORMED=false",
        "FUNDING_STATE=UNPROVEN",
        "POSITION_STATE=UNPROVEN",
        "POST_AUTH_VIABILITY=UNPROVEN",
        "EXECUTION_READY=false",
        "PREREQUISITE_08_CLOSED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "DATA_VALUES_INCLUDED=false",
        "Z2DK_TEXT_REWRITTEN=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "ATLAS_AUTHORITY=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        (
            "EVIDENCE_PACK=evidence/ops/section_11_13_5_z2dl_post_remediation_"
            "single_private_auth_get_v1/20260902T193121Z"
        ),
        "BODY_SHA256=a214481b329ca7ff4e21bbe2b2e6ec2fdf3ade3a86cef70bd4c4fef8d5b2a7dd",
    )
    for token in required:
        assert token in section, token


def test_z2dl_docs_forbid_overclaim() -> None:
    section = _z2dl_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nORDERS_ALLOWED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nTRANSFER_EXECUTED=true\n",
        "\nFUNDING_BALANCE_GET_SUCCESS=true\n",
        "\nBALANCES_OBSERVED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nFUNDING_GET_PERFORMED=true\n",
        "\nPOSITIONS_GET_PERFORMED=true\n",
        "\nSECOND_REQUEST_PERFORMED=true\n",
        "\nREDIRECT_FOLLOWED=true\n",
        "\nZ2DK_TEXT_REWRITTEN=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nCANONICAL_LIVE_NEXT_POINTER_CHANGED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
        "\nZ2DL_RUNTIME_CONSUMER_CREATED=true\n",
        "\nPOST_AUTH_VIABILITY=true\n",
        "\nFUNDING_STATE=PROVEN\n",
        "\nPOSITION_STATE=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "RETRY_ALLOWED=true" not in section
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_z2dl_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DL" not in text
    assert "11.13.5.Z2DL" not in text


def test_standing_flags_and_claims_remain_fail_closed() -> None:
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False
    assert CODE_OWNER_GO == OWNER_GO
    assert THIS_SLICE == "11.13.5.Z2DL"
    assert WORKPACKAGE_ID == "POST_REMEDIATION_SINGLE_PRIVATE_AUTH_GET_V1"
    assert CLAIMS["LIVE_AUTHORIZED"] is False
    assert CLAIMS["EXECUTION_READY"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["EXPECTED_ORIGIN_MAIN_SHA"] == EXPECTED_ORIGIN_MAIN_SHA


def test_evidence_pack_matches_runbook_and_has_no_secrets() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    summary = (EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8")
    snapshot = (EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    assert '"HTTP_STATUS": 200' in summary
    assert '"OKX_CODE": "0"' in summary
    assert '"PRIVATE_API_AUTH_SUCCESS": true' in summary
    assert '"RUNTIME_50110_CLEARANCE": true' in summary
    assert '"GET_REQUEST_COUNT": 1' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"REDIRECT_FOLLOWED": false' in summary
    assert '"EXECUTION_READY": false' in summary
    assert SECRETREF in snapshot
    lowered = (summary + snapshot).lower()
    assert "plaintext:" not in lowered
    assert "api_secret" not in lowered
    assert '"ok-access-key":' not in lowered
    assert "acctlv" not in lowered
    assert "net_mode" not in lowered


def test_atlas_z2dl_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    marker = "id: RUNTIME_COMPONENT:z2dl_post_remediation_single_private_auth_get_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "tests/ops/test_section_11_13_5_z2dl_persist_v1.py" in block
    assert "20260902T193121Z" in block
