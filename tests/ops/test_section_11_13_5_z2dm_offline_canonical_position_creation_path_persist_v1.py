"""§11.13.5.Z2DM canonical offline position-creation path persist invariants."""

from __future__ import annotations

from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    HOST_GRAPH_ACTIVATION,
    PATH_WIRING_OWNER_GO as CODE_OWNER_GO,
    PATH_WIRING_PREDECESSOR_SLICE,
    PATH_WIRING_THIS_SLICE,
    PATH_WIRING_WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_persist_claims_v1 import (
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
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"

Z2DL_HEADING = "### 11.13.5.Z2DL Post-remediation single private authenticated GET"
Z2DM_HEADING = "### 11.13.5.Z2DM Canonical offline position-creation path wiring persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1"
BASELINE_SHA = "cfce3b0aa66648179f62477fc18bc94fd5ae8236"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_PREREQUISITE_08"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dm_section(text: str) -> str:
    start = text.find(Z2DM_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DM heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DM"
    return text[start:end]


def test_z2dm_heading_is_unique_and_follows_z2dl() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DM_HEADING) == 1
    assert 0 <= text.find(Z2DL_HEADING) < text.find(Z2DM_HEADING) < text.find(LADDER_HEADING)


def test_z2dm_docs_bind_offline_path_without_venue_or_08() -> None:
    section = _z2dm_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DM_OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PATH_WIRING_PREDECESSOR_SLICE}",
        f"THIS_SLICE={PATH_WIRING_THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DM",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DM",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "Z2DL_TEXT_REWRITTEN=false",
        "Z2DB_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={PATH_WIRING_WORKPACKAGE_ID}",
        "CANONICAL_OFFLINE_POSITION_CREATION_PATH_IMPLEMENTED=true",
        "CANONICAL_OFFLINE_POSITION_CREATION_PATH_WIRED=true",
        "MASTER_V2_DP_IS_SOLE_TRADING_DECISION_CORE=true",
        "SECOND_TRADING_AUTHORITY_CREATED=false",
        "STEP_29Q_NOT_DIRECTLY_SUBMITTABLE=true",
        "HOST_GRAPH_ACTIVATION=false",
        "OFFLINE_PATH_PROVEN=true",
        "VENUE_PATH_PROVEN=false",
        "LIVE_PATH_AUTHORIZED=false",
        "PRODUCTIVE_WIRE_REACHABLE=false",
        "LIVE_SEND_ALLOWED=false",
        "POSITION_CREATION_CURRENTLY_AUTHORIZED=false",
        "REAL_POSITION_CREATED=false",
        "PREREQUISITE_08_CLOSED=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_EXECUTED=false",
        "NETWORK_CALL_PERFORMED=false",
        "SECRET_MATERIALIZED=false",
        "EXECUTION_READY=false",
        "LIVE_AUTHORIZED=false",
        "TESTNET_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "ATLAS_MUTATION=false",
        "ATLAS_IMPACT=UPDATED",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY="
        "NO_AUTHORIZED_REACHABLE_PRODUCER_OF_NONZERO_VENUE_POSITION_REQUIRED_BY_PREREQUISITE_08",
    )
    for token in required:
        assert token in section, token


def test_z2dm_docs_forbid_overclaim() -> None:
    section = _z2dm_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nTESTNET_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPRODUCTIVE_WIRE_REACHABLE=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nREAL_POSITION_CREATED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nHOST_GRAPH_ACTIVATION=true\n",
        "\nSECOND_TRADING_AUTHORITY_CREATED=true\n",
        "\nVENUE_PATH_PROVEN=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "RETRY_ALLOWED=true" not in section
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_z2dm_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DM" not in text
    assert "11.13.5.Z2DM" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CODE_OWNER_GO == OWNER_GO
    assert PATH_WIRING_THIS_SLICE == "11.13.5.Z2DM"
    assert PATH_WIRING_WORKPACKAGE_ID == "OFFLINE_CANONICAL_POSITION_CREATION_PATH_WIRING_V1"
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["CANONICAL_OFFLINE_POSITION_CREATION_PATH_IMPLEMENTED"] is True
    assert CLAIMS["SECOND_TRADING_AUTHORITY_CREATED"] is False
    assert CLAIMS["PRODUCTIVE_WIRE_REACHABLE"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["HOST_GRAPH_ACTIVATION"] is HOST_GRAPH_ACTIVATION
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2dm_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    marker = "id: RUNTIME_COMPONENT:offline_execution_permission_and_position_creation_producer_wiring_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "lineage_assembler_v1.py" in block
    assert "composition_v1.py" in block
    assert "tests/ops/test_canonical_offline_position_creation_path_wiring_v1.py" in block
