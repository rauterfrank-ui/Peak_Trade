"""§11.13.5.Z2DR post-Z2DQ Route-C create-path blocker census persist invariants."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_adjudicate_v1 import (
    adjudicate_route_c_create_path_blocker_census_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_census_v1 import (
    census_summary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_constants_v1 import (
    CREATE_READINESS_AFTER_ALL_BOUND_SLICES,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    G_POSMODE_RESULT_CLASS,
    G_POSMODE_STATUS,
    G_POSMODE_STATUS_CLOSED_AS,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_create_path_blocker_persist_claims_v1 import (
    CLAIMS,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    PREREQUISITE_08_CLOSED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
SPEC = REPO_ROOT / "docs" / "ops" / "specs" / "POST_Z2DQ_ROUTE_C_CREATE_PATH_BLOCKER_CENSUS_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dr_post_z2dq_route_c_create_path_blocker_census_v1"
    / "20260903T174500Z"
)

Z2DQ_HEADING = "### 11.13.5.Z2DQ Route-C net-mode posSide first-party contract evidence persist"
Z2DR_HEADING = "### 11.13.5.Z2DR Post-Z2DQ Route-C create-path blocker census SSOT persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dr_section(text: str) -> str:
    start = text.find(Z2DR_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DR heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DR"
    return text[start:end]


def test_z2dr_heading_is_unique_and_follows_z2dq() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DR_HEADING) == 1
    assert 0 <= text.find(Z2DQ_HEADING) < text.find(Z2DR_HEADING) < text.find(LADDER_HEADING)


def test_z2dr_docs_bind_offline_census_without_wire() -> None:
    section = _z2dr_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DR_POST_Z2DQ_ROUTE_C_CREATE_PATH_BLOCKER_CENSUS_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DR",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DR",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "CENSUS_STATUS=EXHAUSTIVE_COMPLETE",
        "CENSUS_EXHAUSTION_PROVEN=true",
        "RESULT_CLASS=CREATE_PATH_BLOCKER_CENSUS_EXHAUSTIVE_COMPLETE",
        f"CREATE_READINESS_AFTER_ALL_BOUND_SLICES={CREATE_READINESS_AFTER_ALL_BOUND_SLICES}",
        f"G_POSMODE_STATUS={G_POSMODE_STATUS}",
        f"G_POSMODE_STATUS_CLOSED_AS={G_POSMODE_STATUS_CLOSED_AS}",
        f"G_POSMODE_RESULT_CLASS={G_POSMODE_RESULT_CLASS}",
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        "POSITION_MODE_FAIL_CLOSED=true",
        "OFFLINE_CLOSABLE_GAP_COUNT=0",
        "MAX_SAFE_OFFLINE_BUNDLE_REMAINING=0",
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE=true",
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=false",
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE=false",
        "CREATE_PATH_CURRENTLY_AUTHORIZED=false",
        "PREREQUISITE_08_CLOSED=false",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_PERFORMED=false",
        "NETWORK_CALL_PERFORMED=false",
        "VENUE_NETWORK_ACCESS=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "ATLAS_MUTATION=false",
        "ATLAS_IMPACT=UPDATED",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        f"CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
    )
    for token in required:
        assert token in section, token


def test_z2dr_docs_forbid_overclaim() -> None:
    section = _z2dr_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCREATE_PATH_CURRENTLY_AUTHORIZED=true\n",
        "\nCURRENT_PRODUCTIVE_WIRE_REACHABLE=true\n",
        "\nCREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nOFFLINE_CLOSABLE_GAP_COUNT=1\n",
        "\nMAX_SAFE_OFFLINE_BUNDLE_REMAINING=1\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_OMIT_POSSIDE\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_z2dr_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DR" not in text
    assert "11.13.5.Z2DR" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["GET_EXECUTED_THIS_PERSIST"] is False
    assert CLAIMS["NETWORK_CALL_PERFORMED"] is False
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert POSITION_MODE_FAIL_CLOSED is True
    assert PREREQUISITE_08_CLOSED is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2dr_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:z2dr" in catalog
    marker = "id: RUNTIME_COMPONENT:route_c_create_path_blocker_census_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "route_c_create_path_blocker_census_v1.py" in block


def test_evidence_pack_manifest_verifies_and_matches_adjudication() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["RESULT_CLASS"] == "CREATE_PATH_BLOCKER_CENSUS_EXHAUSTIVE_COMPLETE"
    assert adjudication["OFFLINE_CLOSABLE_GAP_COUNT"] == 0
    assert adjudication["MAX_SAFE_OFFLINE_BUNDLE_REMAINING"] == 0
    assert adjudication["PREREQUISITE_08_CLOSED"] is False
    assert adjudication["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    census = json.loads((EVIDENCE_PACK / "CENSUS.json").read_text(encoding="utf-8"))
    assert census["BLOCKER_RECORD_COUNT"] == 9
    assert census["UNADJUDICATED_BLOCKER_COUNT"] == 0
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["GET_COUNT"] == 0
    assert summary["POST_COUNT"] == 0
    assert summary["NETWORK_CALL_PERFORMED"] is False
    spec = _read(SPEC)
    assert "RESULT_CLASS=CREATE_PATH_BLOCKER_CENSUS_EXHAUSTIVE_COMPLETE" in spec
    assert "docs_token: DOCS_TOKEN_POST_Z2DQ_ROUTE_C_CREATE_PATH_BLOCKER_CENSUS_V1" in spec
    live = adjudicate_route_c_create_path_blocker_census_v1()
    assert live["RESULT_CLASS"] == adjudication["RESULT_CLASS"]
    assert census_summary_v1()["BLOCKER_RECORD_COUNT"] == census["BLOCKER_RECORD_COUNT"]
