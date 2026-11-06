"""§11.13.5.Z2DF offline Funding Account balance read producer persist invariants."""

from __future__ import annotations

from pathlib import Path

from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED,
    FUNDING_BALANCE_ENDPOINT,
    FUNDING_BALANCE_GET_EXECUTED,
    FUNDING_BALANCE_GET_IMPLEMENTED,
    GENERIC_ALLOWLIST_BYPASS_CREATED,
    OWNER_GO as CODE_OWNER_GO,
    PREREQUISITE_08_CLOSED_BY_THIS_PACKAGE,
    PRODUCTIVE_NETWORK_REACHABILITY,
    SECOND_HTTP_CLIENT_CREATED,
    SECOND_SIGNER_CREATED,
    STANDING_LIVE_AUTHORIZED,
    THIS_SLICE,
    USD_USDC_COLLAPSED,
    WORKPACKAGE_ID,
)
from src.ops.offline_funding_balance_read_producer_v1.persist_claims_v1 import CLAIMS
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ASSET_BALANCES,
    GET_ENDPOINTS_PRIVATE,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"

Z2DB_HEADING = (
    "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
)
Z2DF_HEADING = "### 11.13.5.Z2DF Offline Funding Account balance read producer persist"
Z2DG_HEADING = "### 11.13.5.Z2DG Single actual read-only Funding Account balance GET"
Z2DH_HEADING = "### 11.13.5.Z2DH Single actual read-only Funding Account balance GET"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_Z2DF_OFFLINE_FUNDING_BALANCE_READ_PRODUCER_V1"
BASELINE_SHA = "032dfdb9fecc29691bf8d71f8cad8f506280ea28"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2df_section(text: str) -> str:
    start = text.find(Z2DF_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DF heading"
    end = text.find(Z2DG_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DG boundary after Z2DF"
    return text[start:end]


def _z2db_section(text: str) -> str:
    start = text.find(Z2DB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DB heading"
    end = text.find(Z2DF_HEADING, start)
    assert end > start, "missing §11.13.5.Z2DF boundary after Z2DB"
    return text[start:end]


def test_z2df_heading_is_unique_and_follows_z2db() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DF_HEADING) == 1
    z2db = text.find(Z2DB_HEADING)
    z2df = text.find(Z2DF_HEADING)
    z2dg = text.find(Z2DG_HEADING)
    z2dh = text.find(Z2DH_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= z2db < z2df < z2dg < z2dh < ladder


def test_z2db_text_was_not_rewritten() -> None:
    section = _z2db_section(_read(MASTER_RUNBOOK))
    assert "THIS_SLICE=11.13.5.Z2DB" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DB" in section
    assert "Z2DF" not in section
    assert "OFFLINE_FUNDING_BALANCE_READ_PRODUCER_V1" not in section


def test_z2df_docs_bind_offline_read_without_execution() -> None:
    section = _z2df_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DF_OFFLINE_FUNDING_BALANCE_READ_PRODUCER_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_STARTING_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "LAST_MERGED_PR=6217",
        "PREDECESSOR_SLICE=11.13.5.Z2DB",
        "THIS_SLICE=11.13.5.Z2DF",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DF",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DF",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "Z2DB_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "FUNDING_BALANCE_GET_IMPLEMENTED=true",
        "FUNDING_BALANCE_GET_EXECUTED=false",
        "FUNDING_ACCOUNT_STATUS=UNKNOWN",
        "FUNDING_BALANCE_ENDPOINT=/api/v5/asset/balances",
        "FUNDING_BALANCE_ENDPOINT_METHOD=GET",
        "FUNDING_BALANCE_ENDPOINT_CLASS=PRIVATE_READ_ONLY",
        "ABSENT_CURRENCY_ROW_IS_NOT_ZERO=true",
        "USD_USDC_COLLAPSED=false",
        "SECOND_HTTP_CLIENT_CREATED=false",
        "SECOND_SIGNER_CREATED=false",
        "GENERIC_ALLOWLIST_BYPASS_CREATED=false",
        "CAPITAL_MOVEMENT_PRODUCER_CREATED=false",
        "PRODUCTIVE_NETWORK_REACHABILITY_DURING_THIS_GO=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "NETWORK_CALL_PERFORMED=false",
        "SECRET_MATERIALIZED=false",
        "CAPITAL_MOVEMENT_AUTHORIZED=false",
        "INTERNAL_TRANSFER_AUTHORIZED=false",
        "EXTERNAL_DEPOSIT_AUTHORIZED=false",
        "CURRENCY_CONVERSION_AUTHORIZED=false",
        "PREREQUISITE_08_CLOSED=false",
        "PREREQUISITE_08_STATUS=UNRESOLVED",
        "NONZERO_VENUE_POSITION_PROVEN=false",
        "POST_AUTH_VIABILITY=UNPROVEN",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "ORDERS_ALLOWED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "SUBMIT_UNLOCKED=false",
        "ATLAS_MUTATION=false",
        "ATLAS_IMPACT=UPDATED",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY="
        "NO_AUTHORIZED_REACHABLE_PRODUCER_OF_NONZERO_VENUE_POSITION_REQUIRED_BY_PREREQUISITE_08",
    )
    for token in required:
        assert token in section, token


def test_z2df_docs_forbid_activation_and_overclaim() -> None:
    section = _z2df_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nORDERS_ALLOWED=true\n",
        "\nLIVE_ENABLED=true\n",
        "\nLIVE_ARMED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nFUNDING_BALANCE_GET_EXECUTED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCAPITAL_MOVEMENT_AUTHORIZED=true\n",
        "\nINTERNAL_TRANSFER_AUTHORIZED=true\n",
        "\nEXTERNAL_DEPOSIT_AUTHORIZED=true\n",
        "\nCURRENCY_CONVERSION_AUTHORIZED=true\n",
        "\nPRODUCTIVE_NETWORK_REACHABILITY_DURING_THIS_GO=true\n",
        "\nSECOND_HTTP_CLIENT_CREATED=true\n",
        "\nABSENT_CURRENCY_ROW_IS_NOT_ZERO=false\n",
        "\nUSD_USDC_COLLAPSED=true\n",
        "\nATLAS_MUTATION=true\n",
        "\nLANDSCAPE_MUTATION=true\n",
        "\nCURRENT_CANONICAL_SECTION_REPLACED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nPOST_AUTH_VIABILITY=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_z2df_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DF" not in text
    assert "11.13.5.Z2DF" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CODE_OWNER_GO == OWNER_GO
    assert THIS_SLICE == "11.13.5.Z2DF"
    assert ENDPOINT_ASSET_BALANCES == FUNDING_BALANCE_ENDPOINT
    assert FUNDING_BALANCE_ENDPOINT in GET_ENDPOINTS_PRIVATE
    assert CLAIMS["FUNDING_BALANCE_GET_IMPLEMENTED"] is FUNDING_BALANCE_GET_IMPLEMENTED
    assert CLAIMS["FUNDING_BALANCE_GET_EXECUTED"] is FUNDING_BALANCE_GET_EXECUTED
    assert CLAIMS["SECOND_HTTP_CLIENT_CREATED"] is SECOND_HTTP_CLIENT_CREATED
    assert CLAIMS["SECOND_SIGNER_CREATED"] is SECOND_SIGNER_CREATED
    assert CLAIMS["GENERIC_ALLOWLIST_BYPASS_CREATED"] is GENERIC_ALLOWLIST_BYPASS_CREATED
    assert CLAIMS["ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED"] is (
        ABSENT_CURRENCY_ROW_ZERO_SEMANTICS_CREATED
    )
    assert CLAIMS["USD_USDC_COLLAPSED"] is USD_USDC_COLLAPSED
    assert CLAIMS["PRODUCTIVE_NETWORK_REACHABILITY"] is PRODUCTIVE_NETWORK_REACHABILITY
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is PREREQUISITE_08_CLOSED_BY_THIS_PACKAGE
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert STANDING_LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False
    assert PRODUCTIVE_NETWORK_REACHABILITY is False
