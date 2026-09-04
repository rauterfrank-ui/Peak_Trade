"""PR #6252 merge-closeout persist invariants."""

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
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.assemble_v1 import (
    assemble_pr_6252_merge_closeout_v1,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_pr_6252_merge_closeout_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/PR_6252_MERGE_CLOSEOUT_V1.md"
EVIDENCE_PACK = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / CANONICAL_EVIDENCE_RUN_ID

FLATTEN_HEADING = "### 11.13.5 PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
CLOSEOUT_HEADING = "### 11.13.5 PR_6252_MERGE_CLOSEOUT"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _closeout_section(text: str) -> str:
    start = text.find(CLOSEOUT_HEADING)
    assert start >= 0, "missing PR_6252_MERGE_CLOSEOUT persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after closeout persist"
    return text[start:end]


def test_closeout_is_additive_after_flatten() -> None:
    text = _read(MASTER_RUNBOOK)
    flatten_start = text.find(FLATTEN_HEADING)
    closeout_start = text.find(CLOSEOUT_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= flatten_start < closeout_start < ladder
    flatten = text[flatten_start:closeout_start]
    assert "PRODUCTIVE_FLATTEN_TEXT_REWRITTEN=true" not in flatten
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_MERGE_GO" in flatten
    assert "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN" in flatten


def test_closeout_runbook_persist_tokens() -> None:
    section = _closeout_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "PR_6252_STATUS=SQUASH_MERGED",
        "OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS=CONSUMED_CLOSED",
        "PRODUCTIVE_FLATTEN_TEXT_REWRITTEN=false",
        "STALE_NEXT_POINTER_CORRECTED=true",
        "STALE_POINTER_WAS=OWNER_MERGE_GO",
        "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "LIVE_FLATTEN_PROVABILITY_PROVEN=false",
        "RECOVERY_POSITION_SEMANTICS=CASE_C_EMPTY_DATA_NOT_ZERO",
        "EMPTY_DATA_IS_ZERO=false",
        "SECTION_11_14_AUTHORIZED=false",
        "RETRY_ALLOWED=false",
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
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "EXECUTION_READY=false",
        "FAIL_CLOSED_IF_G12_MARKED_CLOSED=true",
        "FAIL_CLOSED_IF_EMPTY_DATA_PROMOTED_TO_ZERO=true",
        "FAIL_CLOSED_IF_SECTION_11_14_AUTHORIZED=true",
        "MINIMUM_ADDITIONAL_OWNER_GO_COUNT=1",
        f"EVIDENCE_PACK=evidence/ops/{EVIDENCE_DIRNAME}/{CANONICAL_EVIDENCE_RUN_ID}",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nPOST_PERFORMED=true\n",
        "\nGET_PERFORMED_THIS_PERSIST=true\n",
        "\nPRIVATE_AUTH_USED=true\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nEXECUTION_READY=true\n",
        "\nPRODUCTIVE_FLATTEN_TEXT_REWRITTEN=true\n",
        "\nLIVE_FLATTEN_PROVABILITY_PROVEN=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nSECTION_11_14_AUTHORIZED=true\n",
        "\nRETRY_ALLOWED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nG12_STATUS=CLOSED\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_is_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "PR_6252_MERGE_CLOSEOUT" in text


def test_atlas_closeout_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:pr_6252_merge_closeout" in catalog
    assert "id: RUNTIME_COMPONENT:pr_6252_merge_closeout_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["G12_STATUS"] == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert CLAIMS["TARGET_POSITION_ZERO_PROVEN"] is False
    assert CLAIMS["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert CLAIMS["SECTION_11_14_AUTHORIZED"] is False
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
    assert "docs_token:" in text
    assert "DOCS_TOKEN_PR_6252_MERGE_CLOSEOUT_V1" in text
    assert "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN" in text
    assert "TARGET_POSITION_ZERO_PROVEN=false" in text
    assert "LIVE_FLATTEN_PROVABILITY_PROVEN=false" in text
    assert "SECTION_11_14_AUTHORIZED=false" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert (
        "OWNER_MERGE_GO_FOR_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_PR_STATUS=CONSUMED_CLOSED"
        in text
    )


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["G12_STATUS"] == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["SECTION_11_14_AUTHORIZED"] is False
    assert adjudication["POST_PERFORMED"] is False
    assert adjudication["GET_PERFORMED_THIS_PERSIST"] is False
    assert adjudication["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert adjudication["RECOVERY_POSITION_SEMANTICS"] == "CASE_C_EMPTY_DATA_NOT_ZERO"


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_pr_6252_merge_closeout_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert result["adjudication"]["G12_STATUS"] == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert result["adjudication"]["TARGET_POSITION_ZERO_PROVEN"] is False
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
