"""P10 TARGET_POSITION_QTY unit forensic persist invariants."""

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
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.assemble_v1 import (
    assemble_p10_qty_unit_adjudication_v1,
)
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.constants_v1 import (
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
from src.ops.section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P10_TARGET_POSITION_QTY_UNIT_FORENSIC_ADJUDICATION_PERSIST_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p10_target_position_qty_unit_forensic_adjudicate_persist_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

CASE_A_HEADING = "### 11.13.5 P08 CASE_A nonzero position adjudication persist close"
P10_HEADING = "### 11.13.5 P10 TARGET_POSITION_QTY unit forensic adjudication persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _p10_section(text: str) -> str:
    start = text.find(P10_HEADING)
    assert start >= 0, "missing P10 persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after P10 persist"
    return text[start:end]


def test_p10_heading_is_unique_and_follows_p08() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(P10_HEADING) == 1
    assert 0 <= text.find(CASE_A_HEADING) < text.find(P10_HEADING) < text.find(LADDER_HEADING)


def test_p08_case_a_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    case_start = text.find(CASE_A_HEADING)
    p10_start = text.find(P10_HEADING)
    case_a = text[case_start:p10_start]
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_P08_NONZERO_POSITION_ADJUDICATE_PERSIST_CLOSE_AND_PR_MAX_LEVERAGE_V1"
        in case_a
    )
    assert "P08_CLOSED=true" in case_a
    assert "TARGET_POSITION_QTY_UNIT=UNPROVEN" in case_a
    assert "P08_CASE_A_TEXT_REWRITTEN=false" in _p10_section(text)


def test_p10_runbook_persist_tokens() -> None:
    section = _p10_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "TARGET_POSITION_QTY_UNIT=UNPROVEN",
        "CURRENT_UNIT_CONTRACT=UNPROVEN",
        "QTY_UNIT_CENSUS_COMPLETE=true",
        "QTY_UNIT_LINEAGE_COMPLETE=true",
        f"EARLIEST_MISSING_QTY_UNIT_PROOF={EARLIEST_MISSING_QTY_UNIT_PROOF}",
        "CONFLICT_COUNT=0",
        "P08_CLOSED=true",
        f"LAST_CANONICALLY_CLOSED_STEP={LAST_CANONICALLY_CLOSED_STEP}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
        "THIS_GO_GET_COUNT=0",
        "GET_PERFORMED_THIS_PERSIST=false",
        "SECOND_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "POST_COUNT=0",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "P10_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT=true",
        "ORDER_PLAN_QTY_IS_NOT_TARGET_POSITION_QTY=true",
        "ONE_CONTRACT_EQUALS_ONE_SUI=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "UNIT_CHAIN_VERDICT=PASSTHROUGH_POS_TO_SZ_UNIT_IDENTITY_UNPROVEN",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nTARGET_POSITION_QTY_UNIT=PROVEN\n",
        "\nTARGET_POSITION_QTY_UNIT=contracts\n",
        "\nCURRENT_UNIT_CONTRACT=VENUE_CONTRACT_COUNT\n",
        "\nPOST_PERFORMED=true\n",
        "\nGET_PERFORMED_THIS_PERSIST=true\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nONE_CONTRACT_EQUALS_ONE_SUI=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_p10_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P10_TARGET_POSITION_QTY_UNIT_FORENSIC_ADJUDICATION_PERSIST_V1" not in text


def test_atlas_p10_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p10_target_position_qty_unit_forensic_adjudicate_persist" in catalog
    assert (
        "id: RUNTIME_COMPONENT:p10_target_position_qty_unit_forensic_adjudicate_persist_v1"
        in catalog
    )
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed_unproven() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["GET_ALLOWED"] is False
    assert CLAIMS["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_evidence_pack_manifest_and_verdict() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    assert claims["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["THIS_GO_GET_COUNT"] == 0
    assert summary["POST_COUNT"] == 0
    assert summary["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["EARLIEST_MISSING_QTY_UNIT_PROOF"] == EARLIEST_MISSING_QTY_UNIT_PROOF
    assert adjudication["CONFLICT_COUNT"] == 0
    lineage = json.loads((EVIDENCE_PACK / "LINEAGE.json").read_text(encoding="utf-8"))
    assert lineage["AUTHORITY"] == "NONE"
    assert len(lineage["SEAMS"]) >= 16
    census = json.loads((EVIDENCE_PACK / "CENSUS.json").read_text(encoding="utf-8"))
    assert census["QTY_UNIT_CENSUS_COMPLETE"] is True
    assert census["TARGET_POSITION_QTY_PROVEN_UNITS_FOUND"] == []
    text = json.dumps(census).lower()
    assert "api_secret" not in text
    assert "ok-access-" not in text


def test_spec_exists_and_keeps_unit_unproven() -> None:
    text = _read(SPEC)
    assert (
        "docs_token: DOCS_TOKEN_P10_TARGET_POSITION_QTY_UNIT_FORENSIC_ADJUDICATION_PERSIST_V1"
        in text
    )
    assert "TARGET_POSITION_QTY_UNIT=UNPROVEN" in text
    assert "POST_PERFORMED=false" in text
    assert "GET_PERFORMED_THIS_PERSIST=false" in text
    assert "P10_DOES_NOT_PROVE_TARGET_POSITION_QTY_UNIT=true" in text


def test_tmp_persist_roundtrip(tmp_path: Path) -> None:
    result = assemble_p10_qty_unit_adjudication_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="tmp-run",
    )
    assert int(result["MANIFEST_VERIFY_RC"]) == 0
    verified = verify_manifest_v1(tmp_path / "tmp-run")
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    assert result["adjudication"]["TARGET_POSITION_QTY_UNIT"] == "UNPROVEN"
    assert result["summary"]["POST_PERFORMED"] is False
