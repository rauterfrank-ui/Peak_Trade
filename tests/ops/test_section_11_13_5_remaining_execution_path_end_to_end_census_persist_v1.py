"""REMAINING_EXECUTION_PATH_END_TO_END_CENSUS persist invariants."""

from __future__ import annotations

import json
from pathlib import Path

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
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.assemble_v1 import (
    assemble_remaining_execution_path_end_to_end_census_v1,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_remaining_execution_path_end_to_end_census_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/REMAINING_EXECUTION_PATH_END_TO_END_CENSUS_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_remaining_execution_path_end_to_end_census_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

STPR_HEADING = "### 11.13.5 SEND_TIME_POSITION_REOBSERVATION"
CENSUS_HEADING = "### 11.13.5 REMAINING_EXECUTION_PATH_END_TO_END_CENSUS"
APRPI_HEADING = "### 11.13.5 AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _census_section(text: str) -> str:
    start = text.find(CENSUS_HEADING)
    assert start >= 0, "missing REMAINING_EXECUTION_PATH_END_TO_END_CENSUS persist heading"
    end = text.find(APRPI_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing APRPI or §11.14 boundary after census persist"
    return text[start:end]


def test_census_is_additive_after_stpr() -> None:
    text = _read(MASTER_RUNBOOK)
    stpr_start = text.find(STPR_HEADING)
    census_start = text.find(CENSUS_HEADING)
    aprpi_start = text.find(APRPI_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= stpr_start < census_start < ladder
    if aprpi_start >= 0:
        assert census_start < aprpi_start < ladder
    stpr = text[stpr_start:census_start]
    assert "STPR_TEXT_REWRITTEN=true" not in stpr
    assert "SEND_TIME_POSITION_REOBSERVATION=PASS_OFFLINE_CONTRACT" in stpr
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=BOUNDED_RUNTIME_PERMIT_ISSUANCE" in stpr


def test_census_runbook_persist_tokens() -> None:
    section = _census_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT",
        "REMAINING_EXECUTION_PATH_CENSUS=PASS_OFFLINE_CONTRACT",
        "REMAINING_EXECUTION_PATH_CENSUS_COMPLETE=true",
        "CENSUS_EXHAUSTION_PROVEN=true",
        "LATENT_GAP_CENSUS_COMPLETE=true",
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE=PASS_OFFLINE_CONTRACT",
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN=false",
        "FLATTEN_EXECUTE=PASS_OFFLINE_CONTRACT",
        "FLATTEN_EXECUTE_AUTHORIZED=false",
        "NETWORK_SESSION=PASS_OFFLINE_CONTRACT",
        "NETWORK_SESSION_AUTHORIZED=false",
        "START_NODE=BOUNDED_RUNTIME_PERMIT_ISSUANCE",
        "TERMINAL_EXECUTION_ENDPOINT=LIVE_FLATTEN_PROVABILITY_PROVEN",
        "STPR_TEXT_REWRITTEN=false",
        "STPR_CLOSED=true",
        f"LAST_CANONICALLY_CLOSED_STEP={LAST_CANONICALLY_CLOSED_STEP}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
        "THIS_GO_GET_COUNT=0",
        "GET_PERFORMED_THIS_PERSIST=false",
        "PRIVATE_AUTH_USED=false",
        "POST_PERFORMED=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "RUNTIME_PERMIT_ISSUED=false",
        "CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "EXECUTION_READY=false",
        "FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE=true",
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT=2",
        "WORKPACKAGE_COUNT=3",
        "TOTAL_REMAINING_NODE_COUNT=17",
        "TOTAL_EDGE_COUNT=19",
        "TOTAL_KNOWN_GAP_COUNT=13",
        "LATENT_OFFLINE_GAPS_CLOSED=4",
        "LATENT_OFFLINE_GAPS_REMAINING=2",
        "RUNTIME_GAPS_REMAINING=7",
        "OWNER_DECISIONS_REMAINING=8",
        "POSITION_GET_REQUIRED_THIS_PERSIST=false",
        "POSITION_GET_AUTHORIZED_BY_THIS_OWNER_GO=false",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nPOST_PERFORMED=true\n",
        "\nGET_PERFORMED_THIS_PERSIST=true\n",
        "\nPRIVATE_AUTH_USED=true\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nEXECUTION_READY=true\n",
        "\nSTPR_TEXT_REWRITTEN=true\n",
        "\nBOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN=true\n",
        "\nFLATTEN_EXECUTE_AUTHORIZED=true\n",
        "\nNETWORK_SESSION_AUTHORIZED=true\n",
        "\nBOUNDED_RUNTIME_PERMIT_ISSUANCE=true\n",
        "\nRUNTIME_PERMIT_ISSUED=true\n",
        "\nREMAINING_EXECUTION_PATH_CENSUS=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_census_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "REMAINING_EXECUTION_PATH_END_TO_END_CENSUS_V1" not in text


def test_atlas_census_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:remaining_execution_path_end_to_end_census" in catalog
    assert "id: RUNTIME_COMPONENT:remaining_execution_path_end_to_end_census_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] == "PASS_OFFLINE_CONTRACT"
    assert CLAIMS["BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN"] is False
    assert CLAIMS["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert CLAIMS["NETWORK_SESSION_AUTHORIZED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["GET_ALLOWED"] is False
    assert CLAIMS["PRIVATE_AUTH_USED"] is False
    assert CLAIMS["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_spec_token_and_no_execution_unlock() -> None:
    text = _read(SPEC)
    assert "docs_token: DOCS_TOKEN_REMAINING_EXECUTION_PATH_END_TO_END_CENSUS_V1" in text
    assert "BOUNDED_RUNTIME_PERMIT_ISSUANCE=PASS_OFFLINE_CONTRACT" in text
    assert "CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS=true" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN=false" in text
    assert "CENSUS_DOES_NOT_ISSUE_RUNTIME_PERMIT=true" in text
    assert "TERMINAL_EXECUTION_ENDPOINT=LIVE_FLATTEN_PROVABILITY_PROVEN" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] == "PASS_OFFLINE_CONTRACT"
    assert summary["CENSUS_DOES_NOT_GRANT_EXECUTION_READINESS"] is True
    assert summary["EXECUTION_READY"] is False
    assert adjudication["BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN"] is False
    assert adjudication["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert adjudication["NETWORK_SESSION_AUTHORIZED"] is False
    assert adjudication["PRIVATE_AUTH_USED"] is False
    assert adjudication["POST_PERFORMED"] is False
    assert adjudication["RUNTIME_PERMIT_ISSUED"] is False


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_remaining_execution_path_end_to_end_census_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert result["adjudication"]["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] == "PASS_OFFLINE_CONTRACT"
    assert result["adjudication"]["BOUNDED_RUNTIME_PERMIT_ISSUANCE_RUNTIME_PROVEN"] is False
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
