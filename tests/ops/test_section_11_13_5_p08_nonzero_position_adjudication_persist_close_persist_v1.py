"""P08 CASE_A nonzero adjudication persist invariants."""

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
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.assemble_v1 import (
    assemble_p08_nonzero_adjudication_v1,
)
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.constants_v1 import (
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
from src.ops.section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P08_NONZERO_POSITION_ADJUDICATION_PERSIST_CLOSE_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p08_nonzero_position_adjudication_persist_close_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

BOUNDARY_HEADING = "### 11.13.5 P08 post-read-only-exhaustion authority-boundary persist"
CASE_A_HEADING = "### 11.13.5 P08 CASE_A nonzero position adjudication persist close"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _case_a_section(text: str) -> str:
    start = text.find(CASE_A_HEADING)
    assert start >= 0, "missing P08 CASE_A persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after CASE_A persist"
    return text[start:end]


def test_case_a_heading_is_unique_and_follows_boundary() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(CASE_A_HEADING) == 1
    assert 0 <= text.find(BOUNDARY_HEADING) < text.find(CASE_A_HEADING) < text.find(LADDER_HEADING)


def test_predecessor_boundary_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    boundary_start = text.find(BOUNDARY_HEADING)
    case_a_start = text.find(CASE_A_HEADING)
    boundary = text[boundary_start:case_a_start]
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_P08_POST_READ_ONLY_EXHAUSTION_AUTHORITY_BOUNDARY_MAXIMUM_SAFE_LEVERAGE_V1"
        in boundary
    )
    assert "P08_CLOSED=false" in boundary
    assert "TARGET_POSITION_NONZERO_PROVEN=false" in boundary
    assert "P08_BOUNDARY_TEXT_REWRITTEN=false" in _case_a_section(text)


def test_case_a_runbook_persist_tokens() -> None:
    section = _case_a_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "AUTHORIZED_HOST=eea.okx.com",
        "AUTHORIZED_ACCOUNT_UID=856964404452495999",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "P08_CLOSED=true",
        "TARGET_POSITION_NONZERO_PROVEN=true",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "EMPTY_DATA_IS_ZERO=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "POSITION_OBSERVATION_CLASS=CASE_A_TARGET_NONZERO",
        f"LAST_CANONICALLY_CLOSED_STEP={LAST_CANONICALLY_CLOSED_STEP}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
        "AUTHORIZED_GET_COUNT=1",
        "ACTUAL_GET_COUNT=1",
        "THIS_GO_GET_COUNT=0",
        "GET_PERFORMED_THIS_PERSIST=false",
        "SECOND_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "POST_COUNT=0",
        "ORIGINAL_WIRE_BODY_BYTES_AVAILABLE=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "P08_CLOSE_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "query_completeness_proven=false",
        "REQUEST_TIMESTAMP=2026-09-03T22:37:25.851429Z",
        "RESPONSE_TIMESTAMP=2026-09-03T22:37:26.102299Z",
        "TARGET_ROW_POS=1",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nP08_CLOSED=false\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=false\n",
        "\nG_POSMODE_SUBMIT_BODY_PROVEN=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nGET_PERFORMED_THIS_PERSIST=true\n",
        "\nSECOND_GET_PERFORMED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nLIVE_ENABLED=true\n",
        "\nLIVE_ARMED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_case_a_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P08_NONZERO_POSITION_ADJUDICATION_PERSIST_CLOSE_V1" not in text


def test_atlas_case_a_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p08_nonzero_position_adjudication_persist_close" in catalog
    assert "id: RUNTIME_COMPONENT:p08_nonzero_position_adjudication_persist_close_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed_except_proven_case_a() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["P08_CLOSED"] is True
    assert CLAIMS["TARGET_POSITION_NONZERO_PROVEN"] is True
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
    assert claims["P08_CLOSED"] is True
    assert claims["TARGET_POSITION_NONZERO_PROVEN"] is True
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["THIS_GO_GET_COUNT"] == 0
    assert summary["POST_COUNT"] == 0
    assert summary["P08_CLOSED"] is True
    assert summary["SECOND_GET_PERFORMED"] is False
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["POSITION_OBSERVATION_CLASS"] == "CASE_A_TARGET_NONZERO"
    assert adjudication["signed_pos"] == "1"
    assert adjudication["LAST_CANONICALLY_CLOSED_STEP"] == LAST_CANONICALLY_CLOSED_STEP
    snapshot = json.loads(
        (EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    )
    assert snapshot["TARGET_MATCHING_ROW"]["pos"] == "1"
    assert snapshot["TARGET_MATCHING_ROW"]["instId"] == "SUI-USD_UM_XPERP-310404"
    assert snapshot["ORIGINAL_WIRE_BODY_BYTES_AVAILABLE"] is False
    text = json.dumps(snapshot).lower()
    assert "api_secret" not in text
    assert "ok-access-" not in text


def test_spec_exists_and_closes_only_on_case_a() -> None:
    text = _read(SPEC)
    assert "docs_token: DOCS_TOKEN_P08_NONZERO_POSITION_ADJUDICATION_PERSIST_CLOSE_V1" in text
    assert "P08_CLOSED=true" in text
    assert "POST_PERFORMED=false" in text
    assert "GET_PERFORMED_THIS_PERSIST=false" in text
    assert "TARGET_POSITION_NONZERO_PROVEN=true" in text


def test_tmp_persist_roundtrip(tmp_path: Path) -> None:
    result = assemble_p08_nonzero_adjudication_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="tmp-run",
    )
    assert int(result["MANIFEST_VERIFY_RC"]) == 0
    verified = verify_manifest_v1(tmp_path / "tmp-run")
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    assert result["adjudication"]["P08_CLOSED"] is True
    assert result["summary"]["POST_PERFORMED"] is False
