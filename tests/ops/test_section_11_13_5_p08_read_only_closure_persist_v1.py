"""P08 read-only closure persist invariants."""

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
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P08_READ_ONLY_CLOSURE_MAX_SAFE_LEVERAGE_V3.md"
EVIDENCE_PACK = (
    REPO_ROOT / "evidence" / "ops" / "section_11_13_5_p08_read_only_closure_v1" / "20260903T210317Z"
)

DISTINCT_HEADING = "### 11.13.5 P08 distinct first-party evidence maximum-safe-leverage persist"
CLOSURE_HEADING = "### 11.13.5 P08 read-only closure maximum-safe-leverage persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
EMPTY_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _closure_section(text: str) -> str:
    start = text.find(CLOSURE_HEADING)
    assert start >= 0, "missing P08 read-only closure heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after read-only closure persist"
    return text[start:end]


def test_closure_heading_is_unique_and_follows_distinct() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(CLOSURE_HEADING) == 1
    assert 0 <= text.find(DISTINCT_HEADING) < text.find(CLOSURE_HEADING) < text.find(LADDER_HEADING)


def test_predecessor_distinct_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    distinct_start = text.find(DISTINCT_HEADING)
    closure_start = text.find(CLOSURE_HEADING)
    distinct = text[distinct_start:closure_start]
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_P08_DISTINCT_FIRST_PARTY_EVIDENCE_MAXIMUM_SAFE_LEVERAGE_V2"
        in distinct
    )
    assert "POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO" in distinct
    assert "GET_COUNT=3" in distinct
    assert "P08_DISTINCT_TEXT_REWRITTEN=false" in _closure_section(text)


def test_closure_runbook_persist_tokens() -> None:
    section = _closure_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "AUTHORIZED_HOST=eea.okx.com",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "TARGET_INST_TYPE=FUTURES",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "RESULT_CLASS=HTTP_200_OKX_0",
        "POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO",
        "EMPTY_DATA_IS_ZERO=false",
        "ORDERS_EMPTY_IS_NEVER_HELD=false",
        "ORDERS_EMPTY_IS_CURRENT_ZERO=false",
        "FILLS_EMPTY_IS_NEVER_HELD=false",
        "FILLS_EMPTY_IS_CURRENT_ZERO=false",
        "HISTORICAL_STATE_IS_CURRENT_STATE=false",
        "P08_CLOSED=false",
        "P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED",
        "P08_VERDICT=P08_NOT_CLOSED_READ_ONLY_IDENTIFIER_CHANNELS_DO_NOT_PROVE_CURRENT_NONZERO",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "TARGET_POS_ID_PROVEN=false",
        "POSITION_STATE_OBSERVED=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "GET_COUNT=6",
        "HTTP_EXCHANGE_COUNT=6",
        "RETRY_COUNT=0",
        "POST_COUNT=0",
        "WRITE_REQUEST_COUNT=0",
        "POSID_POSITIONS_GET_PERFORMED=false",
        "EQUIVALENT_ACCOUNT_POSITIONS_EMPTY_PROBE_REPEATED=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY_READ_ONLY_EXHAUSTED}",
        f"IDENTIFIER_BODY_SHA256={EMPTY_SHA}",
        "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true",
        f"SANITIZED_SECRETREF={SECRETREF}",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nP08_CLOSED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nORDERS_EMPTY_IS_NEVER_HELD=true\n",
        "\nORDERS_EMPTY_IS_CURRENT_ZERO=true\n",
        "\nFILLS_EMPTY_IS_NEVER_HELD=true\n",
        "\nFILLS_EMPTY_IS_CURRENT_ZERO=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nTARGET_POS_ID_PROVEN=true\n",
        "\nPOSITION_STATE_OBSERVED=true\n",
        "\nG_POSMODE_SUBMIT_BODY_PROVEN=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLIVE_EXECUTION=true\n",
        "\nCANARY_EXECUTION=true\n",
        "\nRETRY_ALLOWED=true\n",
        "\nP08_READ_ONLY_CLOSURE_RESULT=CLOSED_NONZERO_PROVEN\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_closure_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P08_READ_ONLY_CLOSURE_V3" not in text


def test_atlas_closure_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p08_read_only_closure" in catalog
    assert "id: RUNTIME_COMPONENT:p08_read_only_closure_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["ORDERS_EMPTY_IS_NEVER_HELD"] is False
    assert CLAIMS["ORDERS_EMPTY_IS_CURRENT_ZERO"] is False
    assert CLAIMS["FILLS_EMPTY_IS_NEVER_HELD"] is False
    assert CLAIMS["FILLS_EMPTY_IS_CURRENT_ZERO"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert CLAIMS["P09_WORK_ALLOWED"] is False
    assert CLAIMS["POSITIONS_UNFILTERED_GET_ALLOWED"] is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False


def test_evidence_pack_manifest_and_channel_fields() -> None:
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
    assert summary["P08_READ_ONLY_CLOSURE_RESULT"] == "READ_ONLY_EXHAUSTED"
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["TARGET_POS_ID_PROVEN"] is False
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["OWNER_GO_CONSUMED"] is True
    assert summary["GET_REQUEST_COUNT"] == 6
    assert summary["POST_COUNT"] == 0
    assert summary["POSID_POSITIONS_GET_PERFORMED"] is False
    raw_pending = json.loads(
        (EVIDENCE_PACK / "GET_ORDERS_PENDING.raw.json").read_text(encoding="utf-8")
    )
    assert raw_pending["BODY_SHA256"] == EMPTY_SHA
    assert raw_pending["BODY_WAS_JSON_RESERIALIZED"] is False
    assert raw_pending["DOCUMENT_ROLE"] == "FORENSIC_RAW_NOT_CANONICAL_NOT_ADJUDICATION"
    assert raw_pending["ENDPOINT_PATH"] == "/api/v5/trade/orders-pending"
    raw_fills = json.loads((EVIDENCE_PACK / "GET_FILLS.raw.json").read_text(encoding="utf-8"))
    assert raw_fills["BODY_SHA256"] == EMPTY_SHA
    assert raw_fills["ENDPOINT_PATH"] == "/api/v5/trade/fills"
    assert not (EVIDENCE_PACK / "GET_POSID_POSITIONS.raw.json").exists()
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["DOCUMENT_ROLE"] == "INTERPRETATION_NOT_RAW_EVIDENCE_NOT_SSOT"
    assert adjudication["P08_READ_ONLY_CLOSURE_RESULT"] == "READ_ONLY_EXHAUSTED"
    lowered = json.dumps(
        {
            "summary": summary,
            "raw_pending": raw_pending,
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
    assert "GET_REQUEST_COUNT=6" in text
    assert "CASE_C_EMPTY_DATA_NOT_ZERO" in text
    assert "EMPTY_DATA_IS_ZERO=false" in text
    assert "ORDERS_EMPTY_IS_NEVER_HELD=false" in text
    assert "P08_CLOSED=false" in text
    assert "P08_READ_ONLY_CLOSURE_RESULT=READ_ONLY_EXHAUSTED" in text
    assert "TARGET_POSITION_ZERO_PROVEN=false" in text
    assert "TARGET_POS_ID_PROVEN=false" in text
