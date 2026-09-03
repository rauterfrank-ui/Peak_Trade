"""§11.13.5.Z2DQ Route-C net-mode posSide first-party contract evidence persist invariants."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_adjudicate_v1 import (
    adjudicate_route_c_net_mode_posside_first_party_contract_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_census_v1 import (
    census_summary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_contract_evidence_constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    MISSING_EVIDENCE_EDGE,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_net_mode_posside_first_party_persist_claims_v1 import (
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
SPEC = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "specs"
    / "ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1.md"
)
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dq_route_c_net_mode_posside_first_party_contract_evidence_v1"
    / "20260903T153000Z"
)

Z2DP_HEADING = "### 11.13.5.Z2DP Post-Z2DO fresh Route-C create-readiness GET evidence persist"
Z2DQ_HEADING = "### 11.13.5.Z2DQ Route-C net-mode posSide first-party contract evidence persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_VENUE_WIRE_OR_GET_OR_POST_"
    "OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dq_section(text: str) -> str:
    start = text.find(Z2DQ_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DQ heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DQ"
    return text[start:end]


def test_z2dq_heading_is_unique_and_follows_z2dp() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DQ_HEADING) == 1
    assert 0 <= text.find(Z2DP_HEADING) < text.find(Z2DQ_HEADING) < text.find(LADDER_HEADING)


def test_z2dq_docs_bind_offline_census_without_wire() -> None:
    section = _z2dq_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DQ_ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DQ",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DQ",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "CENSUS_STATUS=EXHAUSTIVE_COMPLETE",
        "CENSUS_EXHAUSTION_PROVEN=true",
        "RESULT_CLASS=FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED",
        "FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT=false",
        "FIRST_PARTY_ROUTE_C_NET_MODE_POSSIDE_CONTRACT_FOUND=false",
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        "POSITION_MODE_FAIL_CLOSED=true",
        "CANARY_SEMANTICS_TRANSFER_USED=false",
        f"MISSING_EVIDENCE_EDGE={MISSING_EVIDENCE_EDGE}",
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
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY="
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    )
    for token in required:
        assert token in section, token


def test_z2dq_docs_forbid_overclaim() -> None:
    section = _z2dq_section(_read(MASTER_RUNBOOK))
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
        "\nFIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT=true\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_OMIT_POSSIDE\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_EMIT_POSSIDE_NET\n",
        "\nCANARY_SEMANTICS_TRANSFER_USED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()


def test_map_of_truth_has_no_z2dq_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DQ" not in text
    assert "11.13.5.Z2DQ" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EVIDENCE_EXHAUSTION_PROVEN"] is True
    assert CLAIMS["FIRST_PARTY_CONTRACT_EVIDENCE_SUFFICIENT"] is False
    assert CLAIMS["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
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


def test_atlas_z2dq_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:z2dq" in catalog
    marker = "id: RUNTIME_COMPONENT:route_c_net_mode_posside_first_party_contract_evidence_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "route_c_net_mode_posside_first_party_census_v1.py" in block
    assert "route_c_net_mode_posside_first_party_adjudicate_v1.py" in block


def test_evidence_pack_manifest_verifies_and_matches_adjudication() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["RESULT_CLASS"] == "FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED"
    assert adjudication["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == "UNPROVEN"
    assert adjudication["PREREQUISITE_08_CLOSED"] is False
    assert adjudication["MISSING_EVIDENCE_EDGE"] == MISSING_EVIDENCE_EDGE
    assert adjudication["CANARY_SEMANTICS_TRANSFER_USED"] is False
    assert adjudication["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
    assert adjudication["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    census = json.loads((EVIDENCE_PACK / "CENSUS.json").read_text(encoding="utf-8"))
    assert census["FIRST_PARTY_CANDIDATE_COUNT"] == 14
    assert census["UNADJUDICATED_RELEVANT_HIT_COUNT"] == 0
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["GET_COUNT"] == 0
    assert summary["POST_COUNT"] == 0
    assert summary["NETWORK_CALL_PERFORMED"] is False
    spec = _read(SPEC)
    assert "RESULT_CLASS=FIRST_PARTY_CONTRACT_EVIDENCE_INSUFFICIENT_FAIL_CLOSED" in spec
    assert (
        "docs_token: DOCS_TOKEN_ROUTE_C_NET_MODE_POSSIDE_FIRST_PARTY_CONTRACT_EVIDENCE_V1" in spec
    )
    live = adjudicate_route_c_net_mode_posside_first_party_contract_v1()
    assert live["RESULT_CLASS"] == adjudication["RESULT_CLASS"]
    assert (
        census_summary_v1()["FIRST_PARTY_CANDIDATE_COUNT"] == census["FIRST_PARTY_CANDIDATE_COUNT"]
    )
