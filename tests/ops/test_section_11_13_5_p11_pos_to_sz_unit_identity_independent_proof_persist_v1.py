"""P11 POS_TO_SZ unit-identity persist invariants."""

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
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.assemble_v1 import (
    assemble_p11_pos_to_sz_identity_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_MISSING_QTY_UNIT_PROOF,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P11_POS_TO_SZ_UNIT_IDENTITY_INDEPENDENT_PROOF_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

P10_HEADING = "### 11.13.5 P10 TARGET_POSITION_QTY unit forensic adjudication persist"
P11_HEADING = "### 11.13.5 P11 POS_TO_SZ unit identity independent proof"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _p11_section(text: str) -> str:
    start = text.find(P11_HEADING)
    assert start >= 0, "missing P11 persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after P11 persist"
    return text[start:end]


def test_p11_is_additive_after_p10() -> None:
    text = _read(MASTER_RUNBOOK)
    p10_start = text.find(P10_HEADING)
    p11_start = text.find(P11_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= p10_start < p11_start < ladder
    p10 = text[p10_start:p11_start]
    assert "TARGET_POSITION_QTY_UNIT=UNPROVEN" in p10
    assert "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT=true" in p10
    assert "P10_CASE_A_TEXT_REWRITTEN" not in p10 or "P08_CASE_A_TEXT_REWRITTEN=false" in p10


def test_p11_runbook_persist_tokens() -> None:
    section = _p11_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "TARGET_POSITION_QTY_UNIT=PROVEN",
        "CURRENT_UNIT_CONTRACT=NUMBER_OF_CONTRACTS",
        "POS_TO_SZ_UNIT_IDENTITY=PROVEN",
        "POS_UNIT=NUMBER_OF_CONTRACTS",
        "SZ_UNIT=NUMBER_OF_CONTRACTS",
        "IDENTITY_OR_CONVERSION=IDENTITY",
        "CASE=CASE_1_SAME_QUANTITY_DOMAIN",
        "QTY_UNIT_CENSUS_COMPLETE=true",
        "QTY_UNIT_LINEAGE_COMPLETE=true",
        f"EARLIEST_MISSING_QTY_UNIT_PROOF={EARLIEST_MISSING_QTY_UNIT_PROOF}",
        "CONFLICT_COUNT=0",
        "P08_CLOSED=true",
        "P10_CLOSED=true",
        f"LAST_CANONICALLY_CLOSED_STEP={LAST_CANONICALLY_CLOSED_STEP}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
        "THIS_GO_GET_COUNT=0",
        "GET_PERFORMED_THIS_PERSIST=false",
        "PRIVATE_AUTH_USED=false",
        "PUBLIC_SPEC_RETRIEVAL_PERFORMED=true",
        "POST_PERFORMED=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "P11_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY=true",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "UNIT_CHAIN_VERDICT=IDENTITY_POS_TO_SZ_NUMBER_OF_CONTRACTS_PROVEN",
        "EXECUTION_PREREQUISITE_10_TARGET_POSITION_QTY_UNIT=PASS",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nTARGET_POSITION_QTY_UNIT=contracts\n",
        "\nCURRENT_UNIT_CONTRACT=VENUE_CONTRACT_COUNT\n",
        "\nPOST_PERFORMED=true\n",
        "\nGET_PERFORMED_THIS_PERSIST=true\n",
        "\nPRIVATE_AUTH_USED=true\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLIVE_AUTHORIZED=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_p11_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P11_POS_TO_SZ_UNIT_IDENTITY_INDEPENDENT_PROOF_V1" not in text


def test_atlas_p11_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p11_pos_to_sz_unit_identity_independent_proof" in catalog
    assert "id: RUNTIME_COMPONENT:p11_pos_to_sz_unit_identity_independent_proof_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["TARGET_POSITION_QTY_UNIT"] == "PROVEN"
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
    assert "docs_token: DOCS_TOKEN_P11_POS_TO_SZ_UNIT_IDENTITY_INDEPENDENT_PROOF_V1" in text
    assert "TARGET_POSITION_QTY_UNIT=PROVEN" in text
    assert "P11_DOES_NOT_GRANT_EXECUTION_READINESS=true" in text
    assert "LIVE_AUTHORIZED=false" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    excerpts = json.loads((EVIDENCE_PACK / "OFFICIAL_EXCERPTS.json").read_text(encoding="utf-8"))
    assert claims["TARGET_POSITION_QTY_UNIT"] == "PROVEN"
    assert summary["TARGET_POSITION_QTY_UNIT"] == "PROVEN"
    assert adjudication["POS_TO_SZ_UNIT_IDENTITY"] == "PROVEN"
    assert adjudication["PRIVATE_AUTH_USED"] is False
    assert excerpts["EXCERPT_COUNT"] >= 10
    assert excerpts["AUTHORITY"] == "NONE"


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_p11_pos_to_sz_identity_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert result["adjudication"]["TARGET_POSITION_QTY_UNIT"] == "PROVEN"
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
