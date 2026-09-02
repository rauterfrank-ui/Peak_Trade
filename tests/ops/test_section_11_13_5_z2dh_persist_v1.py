"""§11.13.5.Z2DH persist invariants for the one-shot Funding Account GET."""

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
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO as CODE_OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1"
    / "20260902T143840Z"
)

Z2DG_HEADING = "### 11.13.5.Z2DG Single actual read-only Funding Account balance GET"
Z2DH_HEADING = "### 11.13.5.Z2DH Single actual read-only Funding Account balance GET"
Z2DI_HEADING = "### 11.13.5.Z2DI Post-Z2DH dual-401 whitelist-block census SSOT persist"
Z2DJ_HEADING = "### 11.13.5.Z2DJ OKX EEA API-key IP whitelist management-plane reconcile"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1"
BASELINE_SHA = "79bb087a8531714b1fdb8d65d4077bc31068b67b"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dh_section(text: str) -> str:
    start = text.find(Z2DH_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DH heading"
    end = text.find(Z2DI_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DI boundary after Z2DH"
    return text[start:end]


def _z2dg_section(text: str) -> str:
    start = text.find(Z2DG_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DG heading"
    end = text.find(Z2DH_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DH boundary after Z2DG"
    return text[start:end]


def test_z2dh_heading_is_unique_and_follows_z2dg() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DH_HEADING) == 1
    assert (
        0
        <= text.find(Z2DG_HEADING)
        < text.find(Z2DH_HEADING)
        < text.find(Z2DI_HEADING)
        < text.find(Z2DJ_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_z2dg_text_was_not_rewritten() -> None:
    section = _z2dg_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DG" in section
    assert "FUNDING_BALANCE_GET_EXECUTED=true" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DG" in section
    assert "11.13.5.Z2DH" not in section
    assert "PEAK_TRADE_OWNER_GO_Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1" not in section


def test_z2dh_text_excludes_z2di_tokens() -> None:
    section = _z2dh_section(_read(MASTER_RUNBOOK))
    assert "11.13.5.Z2DI" not in section
    assert (
        "PEAK_TRADE_OWNER_GO_Z2DI_POST_Z2DH_DUAL_401_WHITELIST_BLOCK_CENSUS_SSOT_PERSIST_V1"
        not in section
    )
    assert "11.13.5.Z2DJ" not in section
    assert "PEAK_TRADE_OWNER_GO_Z2DJ_OKX_API_KEY_IP_WHITELIST_RECONCILE_V1" not in section


def test_z2dh_docs_bind_one_get_without_success_or_activation() -> None:
    section = _z2dh_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "LAST_MERGED_PR=6219",
        "PREDECESSOR_SLICE=11.13.5.Z2DG",
        "THIS_SLICE=11.13.5.Z2DH",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DH",
        "GET_COUNT=1",
        "AUTHENTICATED_GET_CALLS=1",
        "GET_EXECUTED_THIS_PERSIST=true",
        "FUNDING_BALANCE_GET_EXECUTED=true",
        "FUNDING_BALANCE_GET_SUCCESS=false",
        "FUNDING_ACCOUNT_STATUS=GET_PERFORMED_NOT_SUCCESS",
        "HTTP_STATUS=401",
        "VENUE_CODE=50110",
        "VENUE_MSG_CLASS=API_KEY_IP_WHITELIST_BLOCK",
        "BALANCES_OBSERVED=false",
        "POST_EXECUTED=false",
        "TRANSFER_EXECUTED=false",
        "CAPITAL_MOVEMENT_AUTHORIZED=false",
        "PREREQUISITE_08_CLOSED=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "RETRY_UNDER_THIS_OWNER_GO=false",
        "RETRY_ALLOWED=false",
        "WHITELIST_MUTATION_ALLOWED=false",
        "WHITELIST_MUTATION_PERFORMED=false",
        "Z2DG_OWNER_GO_REUSED=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "Z2DG_TEXT_REWRITTEN=false",
        "Z2DH_DOES_NOT_REWRITE_Z2DG=true",
        "NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_FURTHER_GET_OR_IP_WHITELIST_RETRY",
    )
    for token in required:
        assert token in section, token


def test_z2dh_docs_forbid_activation_and_overclaim() -> None:
    section = _z2dh_section(_read(MASTER_RUNBOOK))
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
        "\nCAPITAL_MOVEMENT_AUTHORIZED=true\n",
        "\nRETRY_UNDER_THIS_OWNER_GO=true\n",
        "\nRETRY_ALLOWED=true\n",
        "\nWHITELIST_MUTATION_ALLOWED=true\n",
        "\nWHITELIST_MUTATION_PERFORMED=true\n",
        "\nZ2DG_OWNER_GO_REUSED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nZ2DG_TEXT_REWRITTEN=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_z2dh_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DH" not in text
    assert "11.13.5.Z2DH" not in text


def test_evidence_pack_verifies_and_records_one_get() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    summary = _read(EVIDENCE_PACK / "SUMMARY.json")
    assert '"HTTP_STATUS": 401' in summary
    assert '"GET_REQUEST_COUNT": 1' in summary
    assert '"POST_COUNT": 0' in summary
    assert '"WRITE_REQUEST_COUNT": 0' in summary
    assert '"TRANSFER_REQUEST_COUNT": 0' in summary
    assert '"LIVE_AUTHORIZED": false' in summary
    snapshot = _read(EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json")
    assert '"VENUE_CODE": "50110"' in snapshot
    assert '"HOST": "eea.okx.com"' in snapshot
    assert '"api_secret"' not in snapshot.lower()
    assert '"ok-access-key":' not in snapshot.lower()
    claims = _read(EVIDENCE_PACK / "claims.json")
    assert '"RETRY_ALLOWED": false' in claims
    assert '"WHITELIST_MUTATION_ALLOWED": false' in claims


def test_code_claims_remain_fail_closed() -> None:
    assert CODE_OWNER_GO == OWNER_GO
    assert THIS_SLICE == "11.13.5.Z2DH"
    assert WORKPACKAGE_ID == "SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1"
    assert CLAIMS["EXPECTED_ORIGIN_MAIN_SHA"] == EXPECTED_ORIGIN_MAIN_SHA
    assert CLAIMS["PREDECESSOR_SLICE"] == "11.13.5.Z2DG"
    assert CLAIMS["LIVE_AUTHORIZED"] is False
    assert CLAIMS["CANARY_AUTHORIZED"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["CAPITAL_MOVEMENT_ALLOWED"] is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["WHITELIST_MUTATION_ALLOWED"] is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False
