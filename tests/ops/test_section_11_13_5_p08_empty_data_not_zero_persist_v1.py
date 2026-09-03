"""P08 empty-data-not-zero persist invariants."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
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
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_empty_data_not_zero_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P08_EMPTY_DATA_NOT_ZERO_MAX_SAFE_LEVERAGE_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p08_empty_data_not_zero_v1"
    / "20260903T193620Z"
)

P08_HEADING = "### 11.13.5 P08 position observation single GET persist"
EMPTY_DATA_HEADING = "### 11.13.5 P08 empty-data-not-zero maximum-safe-leverage persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
EMPTY_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _empty_data_section(text: str) -> str:
    start = text.find(EMPTY_DATA_HEADING)
    assert start >= 0, "missing P08 empty-data-not-zero heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after empty-data persist"
    return text[start:end]


def test_empty_data_heading_is_unique_and_follows_p08() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(EMPTY_DATA_HEADING) == 1
    assert 0 <= text.find(P08_HEADING) < text.find(EMPTY_DATA_HEADING) < text.find(LADDER_HEADING)


def test_predecessor_p08_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    p08_start = text.find(P08_HEADING)
    empty_start = text.find(EMPTY_DATA_HEADING)
    p08 = text[p08_start:empty_start]
    assert "OWNER_GO=PEAK_TRADE_OWNER_GO_P08_POSITION_OBSERVATION_V1" in p08
    assert "POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO" in p08
    assert "GET_COUNT=1" in p08
    assert "P08_SINGLE_GET_TEXT_REWRITTEN=false" in _empty_data_section(text)


def test_empty_data_runbook_persist_tokens() -> None:
    section = _empty_data_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "AUTHORIZED_ENDPOINT=GET /api/v5/account/positions",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "TARGET_INST_TYPE=FUTURES",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "RESULT_CLASS=HTTP_200_OKX_0",
        "POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO",
        "EMPTY_DATA_IS_ZERO=false",
        "FILTERED_EMPTY_IS_ZERO=false",
        "TYPED_EMPTY_IS_ZERO=false",
        "P08_CLOSED=false",
        "P08_VERDICT=P08_NOT_CLOSED_EMPTY_DATA_REMAINS_NOT_ZERO",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "POSITION_STATE_OBSERVED=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "GET_COUNT=3",
        "HTTP_EXCHANGE_COUNT=3",
        "RETRY_COUNT=0",
        "POST_COUNT=0",
        "WRITE_REQUEST_COUNT=0",
        "UNFILTERED_EMPTY_AND_TYPED_NONEMPTY=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_P08_STILL_NOT_CLOSED_EMPTY_DATA_REMAINS_NOT_ZERO",
        f"BODY_SHA256={EMPTY_SHA}",
        "BYTE_IDENTICAL_HISTORICAL_P08_EMPTY_ENVELOPE_SHA=true",
        "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true",
        f"SANITIZED_SECRETREF={SECRETREF}",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nP08_CLOSED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nFILTERED_EMPTY_IS_ZERO=true\n",
        "\nTYPED_EMPTY_IS_ZERO=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nPOSITION_STATE_OBSERVED=true\n",
        "\nG_POSMODE_SUBMIT_BODY_PROVEN=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nRETRY_ALLOWED=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_empty_data_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P08_EMPTY_DATA_NOT_ZERO_V1" not in text


def test_atlas_empty_data_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p08_empty_data_not_zero" in catalog
    assert "id: RUNTIME_COMPONENT:p08_empty_data_not_zero_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["FILTERED_EMPTY_IS_ZERO"] is False
    assert CLAIMS["TYPED_EMPTY_IS_ZERO"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert CLAIMS["P09_WORK_ALLOWED"] is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False


def test_evidence_pack_manifest_and_case_c_fields() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    assert claims["EMPTY_DATA_IS_ZERO"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["HTTP_STATUS"] == 200
    assert summary["OKX_CODE"] == "0"
    assert summary["RESULT_CLASS"] == "HTTP_200_OKX_0"
    assert summary["POSITION_OBSERVATION_CLASS"] == "CASE_C_EMPTY_DATA_NOT_ZERO"
    assert summary["P08_CLOSED"] is False
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["OWNER_GO_CONSUMED"] is True
    assert summary["GET_REQUEST_COUNT"] == 3
    assert summary["POST_COUNT"] == 0
    raw1 = json.loads((EVIDENCE_PACK / "GET_01_UNFILTERED.raw.json").read_text(encoding="utf-8"))
    assert raw1["BODY_SHA256"] == EMPTY_SHA
    assert raw1["BODY_WAS_JSON_RESERIALIZED"] is False
    assert raw1["DOCUMENT_ROLE"] == "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION"
    raw2 = json.loads((EVIDENCE_PACK / "GET_02_INSTID.raw.json").read_text(encoding="utf-8"))
    assert raw2["QUERY_PARAMETERS"] == {"instId": "SUI-USD_UM_XPERP-310404"}
    raw3 = json.loads((EVIDENCE_PACK / "GET_03_INSTTYPE.raw.json").read_text(encoding="utf-8"))
    assert raw3["QUERY_PARAMETERS"] == {"instType": "FUTURES"}
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["DOCUMENT_ROLE"] == "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT"
    assert adjudication["HYPOTHESIS_IS_NOT_PROOF"] is True
    lowered = json.dumps(
        {
            "summary": summary,
            "raw1": raw1,
            "claims": claims,
        }
    ).lower()
    assert "plaintext:" not in lowered
    assert '"api_secret":' not in lowered
    assert '"ok-access-key":' not in lowered
    assert '"ok-access-sign":' not in lowered


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert "GET_REQUEST_COUNT=3" in text
    assert "CASE_C_EMPTY_DATA_NOT_ZERO" in text
    assert "EMPTY_DATA_IS_ZERO=false" in text
    assert "FILTERED_EMPTY_IS_ZERO=false" in text
    assert "P08_CLOSED=false" in text
    assert "TARGET_POSITION_ZERO_PROVEN=false" in text
