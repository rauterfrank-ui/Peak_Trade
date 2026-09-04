"""Persist invariants for authenticated private read / runtime permit issuance."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_AUTHORITY_BOUNDARY,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    execute_authenticated_private_runtime_read_and_permit_issuance_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.persist_claims_v1 import (
    CLAIMS,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs/AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE_V1.md"
)
EVIDENCE_PACK = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / CANONICAL_EVIDENCE_RUN_ID

CENSUS_HEADING = "### 11.13.5 REMAINING_EXECUTION_PATH_END_TO_END_CENSUS"
APRPI_HEADING = "### 11.13.5 AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"

NONZERO_BODY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"pos":"1","posSide":"net","mgnMode":"isolated"}]}'
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _aprpi_section(text: str) -> str:
    start = text.find(APRPI_HEADING)
    assert start >= 0, "missing AUTHENTICATED_PRIVATE_RUNTIME_READ persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after APRPI persist"
    return text[start:end]


def test_aprpi_is_additive_after_census() -> None:
    text = _read(MASTER_RUNBOOK)
    census_start = text.find(CENSUS_HEADING)
    aprpi_start = text.find(APRPI_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= census_start < aprpi_start < ladder
    census = text[census_start:aprpi_start]
    assert "CENSUS_TEXT_REWRITTEN=true" not in census
    assert "REMAINING_EXECUTION_PATH_CENSUS=PASS_OFFLINE_CONTRACT" in census
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=AUTHENTICATED_PRIVATE_RUNTIME_READ" in census


def test_aprpi_runbook_persist_tokens() -> None:
    section = _aprpi_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        f"LAST_CANONICALLY_CLOSED_STEP={LAST_CANONICALLY_CLOSED_STEP}",
        f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY}",
        f"NEXT_OWNER_GO_REQUIRED={NEXT_OWNER_GO_REQUIRED}",
        "POST_PERFORMED=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "NETWORK_SESSION_AUTHORIZED=false",
        "FLATTEN_EXECUTE_AUTHORIZED=false",
        "PRODUCTIVE_FLATTEN_POST_AUTHORIZED=false",
        "EMPTY_DATA_IS_ZERO=false",
        "CENSUS_TEXT_REWRITTEN=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "EXECUTION_READY=false",
        "THIS_GO_DOES_NOT_AUTHORIZE_POST=true",
        "FAIL_CLOSED_IF_MARKED_FLATTEN_PROVEN_FROM_PERMIT_ALONE=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "FRESHNESS_POLICY_MAX_AGE_MS=5000",
        "GET_PERFORMED_THIS_PERSIST=true",
        "PRIVATE_AUTH_USED=true",
        "RUNTIME_PERMIT_ISSUED=true",
        "PERMIT_ISSUANCE_RESULT=PASS",
        "POSITION_OBSERVATION_CLASS=CASE_A_TARGET_NONZERO",
        "G05_STATUS=CLOSED_AUTHENTICATED_PRIVATE_GET_PATH",
        "G06_STATUS=CLOSED_SIZE_AND_OBSERVATION_BINDING",
        (f"EVIDENCE_PACK=evidence/ops/{EVIDENCE_DIRNAME}/{CANONICAL_EVIDENCE_RUN_ID}"),
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nPOST_PERFORMED=true\n",
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nFLATTEN_EXECUTE_AUTHORIZED=true\n",
        "\nNETWORK_SESSION_AUTHORIZED=true\n",
        "\nPRODUCTIVE_FLATTEN_POST_AUTHORIZED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nEXECUTION_READY=true\n",
        "\nCENSUS_TEXT_REWRITTEN=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_aprpi_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE_V1" not in text


def test_atlas_aprpi_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:authenticated_private_runtime_read_and_runtime_permit_issuance" in catalog
    assert (
        "id: RUNTIME_COMPONENT:authenticated_private_runtime_read_and_runtime_permit_issuance_v1"
        in catalog
    )
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert CLAIMS["NETWORK_SESSION_AUTHORIZED"] is False
    assert CLAIMS["PRODUCTIVE_FLATTEN_POST_AUTHORIZED"] is False
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
        "docs_token: DOCS_TOKEN_AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE_V1"
        in text
    )
    assert "LIVE_AUTHORIZED=false" in text
    assert "THIS_GO_DOES_NOT_AUTHORIZE_POST=true" in text
    assert "EMPTY_DATA_IS_ZERO=false" in text
    assert "NEXT_AUTHORITY_BOUNDARY=PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["GET_PERFORMED_THIS_PERSIST"] is True
    assert claims["RUNTIME_PERMIT_ISSUED"] is True
    assert claims["PERMIT_ISSUANCE_RESULT"] == "PASS"
    assert summary["POSITION_OBSERVATION_CLASS"] == "CASE_A_TARGET_NONZERO"
    assert summary["POST_PERFORMED"] is False
    assert summary["NETWORK_SESSION_AUTHORIZED"] is False
    assert summary["PRODUCTIVE_FLATTEN_POST_AUTHORIZED"] is False
    assert summary["FLATTEN_EXECUTE_AUTHORIZED"] is False
    assert summary["LIVE_AUTHORIZED"] is False
    assert summary["CANARY_AUTHORIZED"] is False
    assert adjudication["G05_STATUS"] == "CLOSED_AUTHENTICATED_PRIVATE_GET_PATH"
    assert adjudication["G06_STATUS"] == "CLOSED_SIZE_AND_OBSERVATION_BINDING"
    assert adjudication["RUNTIME_PERMIT_ISSUED"] is True
    assert (EVIDENCE_PACK / "GET_ACCOUNT_POSITIONS.sanitized.json").is_file()
    assert (EVIDENCE_PACK / "RUNTIME_PERMIT.json").is_file()


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = execute_authenticated_private_runtime_read_and_permit_issuance_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        transport=RecordingFakeCanaryTransportV1(body=NONZERO_BODY),
        persist=True,
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    pack = Path(result["EVIDENCE_PACK"])
    verified = verify_manifest_v1(pack)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    assert (pack / "GET_ACCOUNT_POSITIONS.sanitized.json").is_file()
    assert (pack / "RUNTIME_PERMIT.json").is_file()
    assert result["summary"]["POST_PERFORMED"] is False
    assert result["adjudication"]["NETWORK_SESSION_AUTHORIZED"] is False
