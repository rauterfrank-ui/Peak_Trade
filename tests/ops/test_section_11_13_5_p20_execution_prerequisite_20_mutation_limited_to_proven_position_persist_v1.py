"""P20 EXECUTION_PREREQUISITE_20 persist invariants."""

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
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.assemble_v1 import (
    assemble_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1,
)
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.constants_v1 import (
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
from src.ops.section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs/P20_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION_V1.md"
)
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

P16_HEADING = "### 11.13.5 P16 EXECUTION_PREREQUISITE_16 bounded activation"
P20_HEADING = "### 11.13.5 P20 EXECUTION_PREREQUISITE_20 mutation limited to proven position"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _p20_section(text: str) -> str:
    start = text.find(P20_HEADING)
    assert start >= 0, "missing P20 persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after P20 persist"
    return text[start:end]


def test_p20_is_additive_after_p16() -> None:
    text = _read(MASTER_RUNBOOK)
    p16_start = text.find(P16_HEADING)
    p20_start = text.find(P20_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= p16_start < p20_start < ladder
    p16 = text[p16_start:p20_start]
    assert "P16_TEXT_REWRITTEN=true" not in p16
    assert (
        "EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_WITHOUT_GLOBAL_LIVE_AUTHORIZED=PASS_OFFLINE_CONTRACT"
        in p16
    )


def test_p20_runbook_persist_tokens() -> None:
    section = _p20_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CASE=CASE_B_OFFLINE_CLOSABLE_CONTRACT",
        "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION=PASS_OFFLINE_CONTRACT",
        "PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN=false",
        "PREREQUISITE_20_NETWORK_SESSION_AUTHORIZED=false",
        "P20_DOES_NOT_ISSUE_RUNTIME_PERMIT=true",
        "P20_DOES_NOT_SET_LIVE_AUTHORIZED=true",
        "P16_TEXT_REWRITTEN=false",
        "P16_CLOSED=true",
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
        "P20_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "EXECUTION_READY=false",
        "FAIL_CLOSED_IF_PREREQUISITE_20_MARKED_PROVEN_FROM_OFFLINE_CODE_ALONE=true",
        "NO_PROVEN_POSITION_DENIES=true",
        "PARTIAL_FLATTEN_DENIES=true",
        "OVERSIZE_FLATTEN_DENIES=true",
        "GLOBAL_LIVE_AUTHORIZED_SUBSTITUTE_DENIES=true",
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
        "\nP16_TEXT_REWRITTEN=true\n",
        "\nPREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN=true\n",
        "\nBOUNDED_RUNTIME_PERMIT_ISSUANCE=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_p20_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P20_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION_V1" not in text


def test_atlas_p20_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p20_execution_prerequisite_20_mutation_limited_to_proven_position" in catalog
    assert (
        "id: RUNTIME_COMPONENT:p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1"
        in catalog
    )
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"] == (
        "PASS_OFFLINE_CONTRACT"
    )
    assert CLAIMS["PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN"] is False
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
    assert (
        "docs_token: DOCS_TOKEN_P20_EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION_V1"
        in text
    )
    assert (
        "EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION=PASS_OFFLINE_CONTRACT"
    ) in text
    assert "P20_DOES_NOT_GRANT_EXECUTION_READINESS=true" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN=false" in text
    assert "P20_DOES_NOT_ISSUE_RUNTIME_PERMIT=true" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"] == (
        "PASS_OFFLINE_CONTRACT"
    )
    assert summary["P20_DOES_NOT_GRANT_EXECUTION_READINESS"] is True
    assert summary["EXECUTION_READY"] is False
    assert adjudication["PREREQUISITE_20_SEND_TIME_POSITION_REOBSERVATION_PROVEN"] is False
    assert adjudication["PRIVATE_AUTH_USED"] is False
    assert adjudication["POST_PERFORMED"] is False


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_p20_execution_prerequisite_20_mutation_limited_to_proven_position_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert (
        result["adjudication"]["EXECUTION_PREREQUISITE_20_MUTATION_LIMITED_TO_PROVEN_POSITION"]
        == "PASS_OFFLINE_CONTRACT"
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
