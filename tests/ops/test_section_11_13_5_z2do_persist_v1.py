"""§11.13.5.Z2DO Route-C gated productive submit composition persist invariants."""

from __future__ import annotations

from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    CREATE_PATH_ARCHITECTURALLY_COMPLETE,
    CREATE_PATH_CURRENTLY_AUTHORIZED,
    CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE,
    CURRENT_PRODUCTIVE_WIRE_REACHABLE,
    HOST_COMPOSITION_SEAM_IMPLEMENTED,
    HOST_GRAPH_ACTIVATION,
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    PREREQUISITE_08_CLOSED,
    ROUTE_C_OWNER_GO as CODE_OWNER_GO,
    ROUTE_C_PREDECESSOR_SLICE,
    ROUTE_C_THIS_SLICE,
    ROUTE_C_WORKPACKAGE_ID,
    SOURCE_ADJUDICATION,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"

Z2DN_HEADING = "### 11.13.5.Z2DN Prerequisite-08 position-source policy rebind persist"
Z2DO_HEADING = "### 11.13.5.Z2DO Route-C offline gated productive submit composition persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
OWNER_GO = "PEAK_TRADE_OWNER_GO_ROUTE_C_OFFLINE_GATED_PRODUCTIVE_SUBMIT_COMPOSITION_V1"
BASELINE_SHA = "e6edfdde174d093d3b91e662e24dee92a5915c6f"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2do_section(text: str) -> str:
    start = text.find(Z2DO_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DO heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DO"
    return text[start:end]


def test_z2do_heading_is_unique_and_follows_z2dn() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DO_HEADING) == 1
    assert 0 <= text.find(Z2DN_HEADING) < text.find(Z2DO_HEADING) < text.find(LADDER_HEADING)


def test_z2do_docs_bind_route_c_without_wire_or_08() -> None:
    section = _z2do_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DO_ROUTE_C_OFFLINE_GATED_PRODUCTIVE_SUBMIT_COMPOSITION_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={BASELINE_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={ROUTE_C_PREDECESSOR_SLICE}",
        f"THIS_SLICE={ROUTE_C_THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DO",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DO",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "Z2DN_TEXT_REWRITTEN=false",
        "Z2DM_TEXT_REWRITTEN=false",
        "Z2DB_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={ROUTE_C_WORKPACKAGE_ID}",
        f"SOURCE_ADJUDICATION={SOURCE_ADJUDICATION}",
        "ROUTE_C_SUBMIT_COMPOSITION_IMPLEMENTED=true",
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        "POSITION_MODE_FAIL_CLOSED=true",
        "HOST_COMPOSITION_SEAM_IMPLEMENTED=true",
        "HOST_GRAPH_ACTIVATION=false",
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE=true",
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=false",
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE=false",
        "CREATE_PATH_CURRENTLY_AUTHORIZED=false",
        "SECOND_TRADING_AUTHORITY_CREATED=false",
        "CANARY_DEFAULT_SIDE_USED=false",
        "SUI_OPERATIVE_ORDER_SZ_USED_AS_29P=false",
        "VENUE_PATH_PROVEN=false",
        "LIVE_PATH_AUTHORIZED=false",
        "PRODUCTIVE_WIRE_REACHABLE=false",
        "LIVE_SEND_ALLOWED=false",
        "POSITION_CREATION_CURRENTLY_AUTHORIZED=false",
        "REAL_POSITION_CREATED=false",
        "PREREQUISITE_08_CLOSED=false",
        "FUNDING_EXPOSURE_READY=false",
        "CREDENTIAL_ACCOUNT_IDENTITY_READY=false",
        "PRETRADE_GATES_READY=false",
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
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    )
    for token in required:
        assert token in section, token


def test_z2do_docs_forbid_overclaim() -> None:
    section = _z2do_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCREATE_PATH_CURRENTLY_AUTHORIZED=true\n",
        "\nCURRENT_PRODUCTIVE_WIRE_REACHABLE=true\n",
        "\nCREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=true\n",
        "\nHOST_GRAPH_ACTIVATION=true\n",
        "\nVENUE_PATH_PROVEN=true\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nPOST_EXECUTED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nFUNDING_EXPOSURE_READY=true\n",
        "\nCREDENTIAL_ACCOUNT_IDENTITY_READY=true\n",
        "\nPRETRADE_GATES_READY=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()


def test_map_of_truth_has_no_z2do_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DO" not in text
    assert "11.13.5.Z2DO" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CODE_OWNER_GO == OWNER_GO
    assert ROUTE_C_THIS_SLICE == "11.13.5.Z2DO"
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["WORKPACKAGE_ID"] == ROUTE_C_WORKPACKAGE_ID
    assert CREATE_PATH_ARCHITECTURALLY_COMPLETE is True
    assert CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE is False
    assert CURRENT_PRODUCTIVE_WIRE_REACHABLE is False
    assert CREATE_PATH_CURRENTLY_AUTHORIZED is False
    assert PREREQUISITE_08_CLOSED is False
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert POSITION_MODE_FAIL_CLOSED is True
    assert HOST_COMPOSITION_SEAM_IMPLEMENTED is True
    assert HOST_GRAPH_ACTIVATION is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2do_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    marker = "id: RUNTIME_COMPONENT:route_c_offline_gated_productive_submit_composition_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "route_c_submit_composition_v1.py" in block
    assert "id: PHASE:z2do" in catalog
