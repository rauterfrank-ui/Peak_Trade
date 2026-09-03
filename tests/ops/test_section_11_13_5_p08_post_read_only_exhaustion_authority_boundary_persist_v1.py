"""P08 post-read-only-exhaustion authority-boundary persist invariants."""

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
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.assemble_v1 import (
    assemble_p08_authority_boundary_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    FUTURE_EXECUTION_GO_DRAFT_STATUS,
    MINIMUM_HIGHER_AUTHORITY,
    NEXT_AUTHORITY_BOUNDARY,
    OWNER_GO,
    P08_NEXT_AUTHORITY_RESULT,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

CLOSURE_HEADING = "### 11.13.5 P08 read-only closure maximum-safe-leverage persist"
BOUNDARY_HEADING = "### 11.13.5 P08 post-read-only-exhaustion authority-boundary persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _boundary_section(text: str) -> str:
    start = text.find(BOUNDARY_HEADING)
    assert start >= 0, "missing P08 authority-boundary heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after authority-boundary persist"
    return text[start:end]


def test_boundary_heading_is_unique_and_follows_closure() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(BOUNDARY_HEADING) == 1
    assert 0 <= text.find(CLOSURE_HEADING) < text.find(BOUNDARY_HEADING) < text.find(LADDER_HEADING)


def test_predecessor_closure_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    closure_start = text.find(CLOSURE_HEADING)
    boundary_start = text.find(BOUNDARY_HEADING)
    closure = text[closure_start:boundary_start]
    assert "OWNER_GO=PEAK_TRADE_OWNER_GO_P08_READ_ONLY_CLOSURE_MAXIMUM_SAFE_LEVERAGE_V3" in closure
    assert "P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED" in closure
    assert "GET_COUNT=6" in closure
    assert "P08_READ_ONLY_CLOSURE_TEXT_REWRITTEN=false" in _boundary_section(text)


def test_boundary_runbook_persist_tokens() -> None:
    section = _boundary_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "AUTHORIZED_HOST=eea.okx.com",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "P08_CLOSED=false",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "EMPTY_DATA_IS_ZERO=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED",
        f"P08_NEXT_AUTHORITY_RESULT={P08_NEXT_AUTHORITY_RESULT}",
        f"MINIMUM_HIGHER_AUTHORITY={MINIMUM_HIGHER_AUTHORITY}",
        "STATE_APPEARANCE_MECHANISM_COUNT=15",
        "VIABLE_MECHANISM_COUNT=1",
        "P08_CLOSURE_CONDITION_STATUS=PROVEN",
        f"FUTURE_EXECUTION_GO_DRAFT_STATUS={FUTURE_EXECUTION_GO_DRAFT_STATUS}",
        "GET_EXECUTED_THIS_PERSIST=false",
        "POST_PERFORMED=false",
        "POST_COUNT=0",
        "WRITE_REQUEST_COUNT=0",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nP08_CLOSED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nG_POSMODE_SUBMIT_BODY_PROVEN=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nGET_EXECUTED_THIS_PERSIST=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nLIVE_ENABLED=true\n",
        "\nLIVE_ARMED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nP08_NEXT_AUTHORITY_RESULT=LIVE_STATE_CREATION_REQUIRED\n",
        "\nP08_NEXT_AUTHORITY_RESULT=TESTNET_STATE_CREATION_REQUIRED\n",
        "\nP08_NEXT_AUTHORITY_RESULT=CANARY_STATE_CREATION_REQUIRED\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_boundary_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1" not in text


def test_atlas_boundary_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p08_post_read_only_exhaustion_authority_boundary" in catalog
    assert "id: RUNTIME_COMPONENT:p08_post_read_only_exhaustion_authority_boundary_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["P08_CLOSED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["FUTURE_GO_AUTHORIZES_POST"] is False
    assert CLAIMS["P08_NEXT_AUTHORITY_RESULT"] == P08_NEXT_AUTHORITY_RESULT
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
    assert claims["P08_CLOSED"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["GET_REQUEST_COUNT"] == 0
    assert summary["POST_COUNT"] == 0
    assert summary["P08_NEXT_AUTHORITY_RESULT"] == P08_NEXT_AUTHORITY_RESULT
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["MINIMUM_HIGHER_AUTHORITY"] == MINIMUM_HIGHER_AUTHORITY
    assert adjudication["VIABLE_MECHANISM_COUNT"] == 1
    assert adjudication["FUTURE_EXECUTION_GO_DRAFT_STATUS"] == FUTURE_EXECUTION_GO_DRAFT_STATUS
    census = json.loads((EVIDENCE_PACK / "MECHANISM_CENSUS.json").read_text(encoding="utf-8"))
    assert census["STATE_APPEARANCE_MECHANISM_COUNT"] == 15
    future_go = json.loads((EVIDENCE_PACK / "FUTURE_GO_DRAFT.json").read_text(encoding="utf-8"))
    assert future_go["PEAK_TRADE_POST_AUTHORIZED"] is False
    assert future_go["SEPARATE_FLATTEN_AUTHORITY_REQUIRED"] is True


def test_spec_exists_and_forbids_post() -> None:
    text = _read(SPEC)
    assert "docs_token: DOCS_TOKEN_P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_V1" in text
    assert "POST_PERFORMED=false" in text
    assert "P08_NEXT_AUTHORITY_RESULT=EXTERNAL_STATE_APPEARANCE_SUFFICIENT" in text


def test_tmp_persist_roundtrip(tmp_path: Path) -> None:
    result = assemble_p08_authority_boundary_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="tmp-run",
    )
    assert int(result["MANIFEST_VERIFY_RC"]) == 0
    verified = verify_manifest_v1(tmp_path / "tmp-run")
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
