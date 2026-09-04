"""SEND_TIME_POSITION_REOBSERVATION persist invariants."""

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
from src.ops.section_11_13_5_send_time_position_reobservation_v1.assemble_v1 import (
    assemble_send_time_position_reobservation_v1,
)
from src.ops.section_11_13_5_send_time_position_reobservation_v1.constants_v1 import (
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
from src.ops.section_11_13_5_send_time_position_reobservation_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/SEND_TIME_POSITION_REOBSERVATION_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_send_time_position_reobservation_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

APT_HEADING = "### 11.13.5 AUTHENTICATED_PRODUCTIVE_TRANSPORT"
STPR_HEADING = "### 11.13.5 SEND_TIME_POSITION_REOBSERVATION"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _stpr_section(text: str) -> str:
    start = text.find(STPR_HEADING)
    assert start >= 0, "missing SEND_TIME_POSITION_REOBSERVATION persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after SEND_TIME_POSITION_REOBSERVATION persist"
    return text[start:end]


def test_stpr_is_additive_after_apt() -> None:
    text = _read(MASTER_RUNBOOK)
    apt_start = text.find(APT_HEADING)
    stpr_start = text.find(STPR_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= apt_start < stpr_start < ladder
    apt = text[apt_start:stpr_start]
    assert "APT_TEXT_REWRITTEN=true" not in apt
    assert "AUTHENTICATED_PRODUCTIVE_TRANSPORT=PASS_OFFLINE_CONTRACT" in apt


def test_stpr_runbook_persist_tokens() -> None:
    section = _stpr_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT",
        "SEND_TIME_POSITION_REOBSERVATION=PASS_OFFLINE_CONTRACT",
        "SEND_TIME_POSITION_REOBSERVATION_OFFLINE_CONTRACT=PASS_OFFLINE_CONTRACT",
        "SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN=false",
        "PREREQUISITE_18_PROVEN_AT_SEND=false",
        "PREREQUISITE_19_PROVEN_AT_SEND=false",
        "PREREQUISITE_21_PROVEN_AT_SEND=false",
        "PREREQUISITE_24_PROVEN_AT_SEND=false",
        "NETWORK_PROVEN=false",
        "CREDENTIAL_USE_PROVEN=false",
        "PRIVATE_GET_PROVEN=false",
        "POST_PROVEN=false",
        "STPR_FLATTEN_EXECUTE_AUTHORIZED=false",
        "STPR_NETWORK_SESSION_AUTHORIZED=false",
        "STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT=true",
        "STPR_DOES_NOT_SET_LIVE_AUTHORIZED=true",
        "APT_TEXT_REWRITTEN=false",
        "APT_CLOSED=true",
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
        "BOUNDED_RUNTIME_PERMIT_ISSUANCE=false",
        "STPR_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "EXECUTION_READY=false",
        "FAIL_CLOSED_IF_MARKED_RUNTIME_PROVEN_FROM_OFFLINE_CODE_ALONE=true",
        "FAIL_CLOSED_IF_MARKED_PROVEN_AT_SEND_FROM_OFFLINE_CODE_ALONE=true",
        "RUNTIME_PERMIT_CLAIM_DENIES=true",
        "FLATTEN_EXECUTE_CLAIM_DENIES=true",
        "GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES=true",
        "EMPTY_DATA_NOT_ZERO_DENIES=true",
        "HISTORICAL_REUSE_DENIES=true",
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
        "\nAPT_TEXT_REWRITTEN=true\n",
        "\nSEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN=true\n",
        "\nPREREQUISITE_18_PROVEN_AT_SEND=true\n",
        "\nSTPR_FLATTEN_EXECUTE_AUTHORIZED=true\n",
        "\nBOUNDED_RUNTIME_PERMIT_ISSUANCE=true\n",
        "\nSEND_TIME_POSITION_REOBSERVATION=PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_stpr_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "SEND_TIME_POSITION_REOBSERVATION_V1" not in text


def test_atlas_stpr_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:send_time_position_reobservation" in catalog
    assert "id: RUNTIME_COMPONENT:send_time_position_reobservation_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["SEND_TIME_POSITION_REOBSERVATION"] == "PASS_OFFLINE_CONTRACT"
    assert CLAIMS["SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN"] is False
    assert CLAIMS["PREREQUISITE_18_PROVEN_AT_SEND"] is False
    assert CLAIMS["STPR_FLATTEN_EXECUTE_AUTHORIZED"] is False
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
    assert "docs_token: DOCS_TOKEN_SEND_TIME_POSITION_REOBSERVATION_V1" in text
    assert "SEND_TIME_POSITION_REOBSERVATION=PASS_OFFLINE_CONTRACT" in text
    assert "STPR_DOES_NOT_GRANT_EXECUTION_READINESS=true" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN=false" in text
    assert "STPR_DOES_NOT_ISSUE_RUNTIME_PERMIT=true" in text
    assert "PREREQUISITE_18_PROVEN_AT_SEND=false" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["SEND_TIME_POSITION_REOBSERVATION"] == "PASS_OFFLINE_CONTRACT"
    assert summary["STPR_DOES_NOT_GRANT_EXECUTION_READINESS"] is True
    assert summary["EXECUTION_READY"] is False
    assert adjudication["SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN"] is False
    assert adjudication["PREREQUISITE_18_PROVEN_AT_SEND"] is False
    assert adjudication["STPR_FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert adjudication["PRIVATE_AUTH_USED"] is False
    assert adjudication["POST_PERFORMED"] is False
    assert adjudication["BOUNDED_RUNTIME_PERMIT_ISSUANCE"] is False


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_send_time_position_reobservation_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert result["adjudication"]["SEND_TIME_POSITION_REOBSERVATION"] == "PASS_OFFLINE_CONTRACT"
    assert result["adjudication"]["SEND_TIME_POSITION_REOBSERVATION_RUNTIME_PROVEN"] is False
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
