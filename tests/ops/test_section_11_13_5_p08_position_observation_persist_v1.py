"""P08 position-observation persist invariants."""

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
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_position_observation_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P08_POSITION_OBSERVATION_SINGLE_GET_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p08_position_observation_v1"
    / "20260903T190424Z"
)

ATTESTATION_HEADING = (
    "### 11.13.5 Post-Z2DS post-whitelist private auth attestation single GET persist"
)
P08_HEADING = "### 11.13.5 P08 position observation single GET persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"
Z2CN_EMPTY_SHA = "fc24d69479edbb84f22c7d5bd4525349734056ad3baf7a5adf7e553f68c06a3a"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _p08_section(text: str) -> str:
    start = text.find(P08_HEADING)
    assert start >= 0, "missing P08 position observation heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after P08 persist"
    return text[start:end]


def test_p08_heading_is_unique_and_follows_attestation() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(P08_HEADING) == 1
    assert 0 <= text.find(ATTESTATION_HEADING) < text.find(P08_HEADING) < text.find(LADDER_HEADING)


def test_attestation_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    attest_start = text.find(ATTESTATION_HEADING)
    p08_start = text.find(P08_HEADING)
    attest = text[attest_start:p08_start]
    assert (
        "OWNER_GO=PEAK_TRADE_OWNER_GO_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1"
        in attest
    )
    assert "POSITIONS_GET_PERFORMED=false" in attest
    assert "PREREQUISITE_08_CLOSED=false" in attest


def test_p08_runbook_persist_tokens() -> None:
    section = _p08_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "AUTHORIZED_ENDPOINT=GET /api/v5/account/positions",
        "INSTID_FILTER_USED=false",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "RESULT_CLASS=HTTP_200_OKX_0",
        "POSITION_OBSERVATION_CLASS=CASE_C_EMPTY_DATA_NOT_ZERO",
        "EMPTY_DATA_IS_ZERO=false",
        "P08_CLOSED=false",
        "P08_VERDICT=P08_NOT_CLOSED_EMPTY_DATA_IS_NOT_ZERO",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "POSITION_STATE_OBSERVED=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "GET_COUNT=1",
        "HTTP_EXCHANGE_COUNT=1",
        "RETRY_COUNT=0",
        "POST_COUNT=0",
        "WRITE_REQUEST_COUNT=0",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "NEXT_AUTHORITY_BOUNDARY=SEPARATE_OWNER_GO_REQUIRED_P08_EMPTY_DATA_IS_NOT_ZERO",
        f"BODY_SHA256={Z2CN_EMPTY_SHA}",
        "BYTE_IDENTICAL_Z2CN_EMPTY_ENVELOPE_SHA=true",
        "BYTE_IDENTICAL_EMPTY_SHA_IS_NOT_CURRENT_08_PROOF=true",
        f"SANITIZED_SECRETREF={SECRETREF}",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nP08_CLOSED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
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


def test_map_of_truth_has_no_p08_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P08_POSITION_OBSERVATION_V1" not in text


def test_atlas_p08_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p08_position_observation" in catalog
    assert "id: RUNTIME_COMPONENT:p08_position_observation_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
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
    assert summary["TARGET_POSITION_NONZERO_PROVEN"] is False
    assert summary["POSITION_STATE_OBSERVED"] is False
    assert summary["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert summary["OWNER_GO_CONSUMED"] is True
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    snapshot = json.loads(
        (EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    )
    assert snapshot["BODY_SHA256"] == Z2CN_EMPTY_SHA
    assert snapshot["REDACTED_PAYLOAD"]["data"] == []
    assert snapshot["DATA_ROW_COUNT"] == 0
    assert SECRETREF in json.dumps(snapshot)
    lowered = json.dumps(snapshot).lower()
    assert "plaintext:" not in lowered
    assert '"api_secret":' not in lowered
    assert '"ok-access-key":' not in lowered
    assert '"ok-access-sign":' not in lowered
    assert snapshot["SECRETREF_IDENTITY"]["VALUES_INCLUDED"] is False


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert "GET_REQUEST_COUNT=1" in text
    assert "CASE_C_EMPTY_DATA_NOT_ZERO" in text
    assert "EMPTY_DATA_IS_ZERO=false" in text
    assert "P08_CLOSED=false" in text
