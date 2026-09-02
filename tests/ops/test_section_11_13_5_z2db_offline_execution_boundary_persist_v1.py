"""§11.13.5.Z2DB offline execution-boundary persist invariants. Docs plus code claims."""

from __future__ import annotations

from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    BLIND_RESEND_ALLOWED,
    EXECUTION_PERMISSION_AUTHORITY_EFFECT,
    EXECUTION_READY,
    OWNER_GO as CODE_OWNER_GO,
    PREREQUISITE_08_CLOSED_BY_THIS_PACKAGE,
    PRODUCTIVE_WIRE_REACHABLE,
    SECOND_PERMISSION_AUTHORITY_CREATED,
    STANDING_CANARY_AUTHORIZED,
    STANDING_LIVE_ARMED,
    STANDING_LIVE_AUTHORIZED,
    STANDING_LIVE_ENABLED,
    STANDING_ORDERS_ALLOWED,
    STANDING_SUBMIT_UNLOCKED,
    STANDING_TESTNET_AUTHORIZED,
    THIS_SLICE,
    VENUE_MUTATION_ALLOWED,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
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
WP_FS_B1_HEADING = (
    "### 11.13.5 Parallel-track WP-FS-B1 canonical persist and Atlas navigation census rebind"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_OFFLINE_EXECUTION_PERMISSION_AND_POSITION_CREATION_PRODUCER_WIRING_V1"
)
BASELINE_SHA = "7147c53f03b7aab99108a2330b6efc833f09ce04"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2db_section(text: str) -> str:
    start = text.find(Z2DB_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DB heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DB"
    return text[start:end]


def test_z2db_heading_is_unique_and_follows_wp_fs_b1() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DB_HEADING) == 1
    wp_fs_b1 = text.find(WP_FS_B1_HEADING)
    z2db = text.find(Z2DB_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= wp_fs_b1 < z2db < ladder


def test_z2db_docs_bind_offline_boundary_without_closing_08() -> None:
    section = _z2db_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DB_OFFLINE_EXECUTION_PERMISSION_AND_POSITION_CREATION_PRODUCER_WIRING_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        f"EXPECTED_STARTING_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        "LAST_MERGED_PR=6216",
        "PREDECESSOR_SLICE=11.13.5.Z2DA",
        "PREDECESSOR_LIVE_SLICE=11.13.5.Z2DA",
        "THIS_SLICE=11.13.5.Z2DB",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DB",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DB",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "Z2DA_TEXT_REWRITTEN=false",
        "WP_FS_B1_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "EXECUTION_PERMISSION_CONTROLLER_IMPLEMENTED=true",
        "EXECUTION_PERMISSION_AUTHORIZED=false",
        "EXECUTION_PERMISSION_AUTHORITY_EFFECT=NONE",
        "SECOND_PERMISSION_AUTHORITY_CREATED=false",
        "OFFLINE_POSITION_CREATION_REQUEST_PRODUCER_IMPLEMENTED=true",
        "POSITION_CREATION_RUNTIME_WIRE_REACHABLE=false",
        "AUTHORIZED_REACHABLE_VENUE_POSITION_PRODUCER=false",
        "REAL_POSITION_CREATED=false",
        "PRODUCTIVE_WIRE_REACHABLE=false",
        "VENUE_MUTATION_ALLOWED=false",
        "BLIND_RESEND_ALLOWED=false",
        "PREREQUISITE_08_CLOSED=false",
        "PREREQUISITE_08_STATUS=UNRESOLVED",
        "NONZERO_VENUE_POSITION_PROVEN=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "FLATTEN_EXECUTED=false",
        "NETWORK_CALL_PERFORMED=false",
        "SECRET_MATERIALIZED=false",
        "CLASS_D_CONSUMED=false",
        "Z2AP_CONSUMED=false",
        "EXECUTION_READY=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "ORDERS_ALLOWED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "SUBMIT_UNLOCKED=false",
        "ATLAS_MUTATION=false",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "RUNTIME_AUTHORIZATION_EFFECT=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "GRANT_NE_LIVE_WIRE=true",
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY="
        "NO_AUTHORIZED_REACHABLE_PRODUCER_OF_NONZERO_VENUE_POSITION_REQUIRED_BY_PREREQUISITE_08",
    )
    for token in required:
        assert token in section, token


def test_z2db_docs_forbid_activation_and_overclaim() -> None:
    section = _z2db_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nORDERS_ALLOWED=true\n",
        "\nLIVE_ENABLED=true\n",
        "\nLIVE_ARMED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nCLASS_D_CONSUMED=true\n",
        "\nZ2AP_CONSUMED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nFLATTEN_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nEXECUTION_PERMISSION_AUTHORIZED=true\n",
        "\nVENUE_EXECUTION_AUTHORIZED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nREAL_POSITION_CREATED=true\n",
        "\nPRODUCTIVE_WIRE_REACHABLE=true\n",
        "\nBLIND_RESEND_ALLOWED=true\n",
        "\nATLAS_MUTATION=true\n",
        "\nLANDSCAPE_MUTATION=true\n",
        "\nCURRENT_CANONICAL_SECTION_REPLACED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "WP_FA_08_EXACT_SCOPE=",
        "WORKPACKAGE_ID=WP_FA_08",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_z2db_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DB" not in text
    assert "11.13.5.Z2DB" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CODE_OWNER_GO == OWNER_GO
    assert THIS_SLICE == "11.13.5.Z2DB"
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["EXECUTION_PERMISSION_CONTROLLER_IMPLEMENTED"] is True
    assert CLAIMS["EXECUTION_PERMISSION_AUTHORIZED"] is False
    assert CLAIMS["EXECUTION_PERMISSION_AUTHORITY_EFFECT"] == EXECUTION_PERMISSION_AUTHORITY_EFFECT
    assert CLAIMS["SECOND_PERMISSION_AUTHORITY_CREATED"] is SECOND_PERMISSION_AUTHORITY_CREATED
    assert CLAIMS["OFFLINE_POSITION_CREATION_REQUEST_PRODUCER_IMPLEMENTED"] is True
    assert CLAIMS["POSITION_CREATION_RUNTIME_WIRE_REACHABLE"] is False
    assert CLAIMS["AUTHORIZED_REACHABLE_VENUE_POSITION_PRODUCER"] is False
    assert CLAIMS["REAL_POSITION_CREATED"] is False
    assert CLAIMS["PRODUCTIVE_WIRE_REACHABLE"] is PRODUCTIVE_WIRE_REACHABLE
    assert CLAIMS["VENUE_MUTATION_ALLOWED"] is VENUE_MUTATION_ALLOWED
    assert CLAIMS["BLIND_RESEND_ALLOWED"] is BLIND_RESEND_ALLOWED
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is PREREQUISITE_08_CLOSED_BY_THIS_PACKAGE
    assert CLAIMS["EXECUTION_READY"] is EXECUTION_READY
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert STANDING_LIVE_AUTHORIZED is False
    assert STANDING_TESTNET_AUTHORIZED is False
    assert STANDING_CANARY_AUTHORIZED is False
    assert STANDING_ORDERS_ALLOWED is False
    assert STANDING_LIVE_ENABLED is False
    assert STANDING_LIVE_ARMED is False
    assert STANDING_SUBMIT_UNLOCKED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert PRODUCTIVE_WIRE_REACHABLE is False
    assert VENUE_MUTATION_ALLOWED is False
    assert BLIND_RESEND_ALLOWED is False
