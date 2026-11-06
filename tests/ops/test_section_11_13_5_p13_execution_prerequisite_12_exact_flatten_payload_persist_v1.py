"""P13 EXECUTION_PREREQUISITE_12 persist invariants."""

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
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.assemble_v1 import (
    assemble_p13_execution_prerequisite_12_exact_flatten_payload_v1,
)
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.constants_v1 import (
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
from src.ops.section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/P13_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_p13_execution_prerequisite_12_exact_flatten_payload_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)

P12_HEADING = "### 11.13.5 P12 EXECUTION_PREREQUISITE_11 position side posSide"
P13_HEADING = "### 11.13.5 P13 EXECUTION_PREREQUISITE_12 exact flatten payload"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _p13_section(text: str) -> str:
    start = text.find(P13_HEADING)
    assert start >= 0, "missing P13 persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after P13 persist"
    return text[start:end]


def test_p13_is_additive_after_p12() -> None:
    text = _read(MASTER_RUNBOOK)
    p12_start = text.find(P12_HEADING)
    p13_start = text.find(P13_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= p12_start < p13_start < ladder
    p12 = text[p12_start:p13_start]
    assert "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE=PASS" in p12
    assert "P12_TEXT_REWRITTEN=true" not in p12
    assert "REQUEST_POS_SIDE=OMITTED" in p12


def test_p13_runbook_persist_tokens() -> None:
    section = _p13_section(_read(MASTER_RUNBOOK))
    required = (
        f"OWNER_GO={OWNER_GO}",
        f"THIS_SLICE={THIS_SLICE}",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "TARGET_INSTRUMENT_ID=SUI-USD_UM_XPERP-310404",
        "CASE=CASE_B_OFFLINE_CLOSABLE",
        "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION=PASS",
        "P12_EXACT_FLATTEN_PAYLOAD_PROVEN=true",
        "P12_EXACT_FLATTEN_PAYLOAD_CLOSED=true",
        "FLATTEN_ORDER_SIDE_RULE=SELL_IF_OBSERVED_SIGNED_POS_GT_0_ELSE_BUY",
        "REQUEST_POS_SIDE=OMITTED",
        "CONTRACT_BOUNDARY=VENUE_NATIVE_JSON_BODY_IMMEDIATELY_BEFORE_HMAC_TRANSPORT",
        "PX_SOURCE_CLASS=BOUND_EXTERNAL_INPUT_NOT_FROM_OBSERVED_POSITION",
        "SEND_TIME_PX_MINTED=false",
        "SZ_UNIT=NUMBER_OF_CONTRACTS",
        "REDUCE_ONLY_WIRE_TYPE_STATUS=UNPROVEN",
        "CONFLICT_COUNT=0",
        "P08_CLOSED=true",
        "P10_CLOSED=true",
        "P11_CLOSED=true",
        "P12_TEXT_REWRITTEN=false",
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
        "P13_DOES_NOT_GRANT_EXECUTION_READINESS=true",
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
        "EXECUTION_PREREQUISITE_11_POSITION_SIDE_POSSIDE=PASS",
        "EXECUTION_READY=false",
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
        "\nREQUEST_POS_SIDE=net\n",
        "\nP12_TEXT_REWRITTEN=true\n",
        "\nSEND_TIME_PX_MINTED=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_p13_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "P13_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_V1" not in text


def test_atlas_p13_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:p13_execution_prerequisite_12_exact_flatten_payload" in catalog
    assert "id: RUNTIME_COMPONENT:p13_execution_prerequisite_12_exact_flatten_payload_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION"] == (
        "PASS"
    )
    assert CLAIMS["REQUEST_POS_SIDE"] == "OMITTED"
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["GET_ALLOWED"] is False
    assert CLAIMS["PRIVATE_AUTH_USED"] is False
    assert CLAIMS["SEND_TIME_PX_MINTED"] is False
    assert CLAIMS["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_spec_token_and_no_execution_unlock() -> None:
    text = _read(SPEC)
    assert "docs_token: DOCS_TOKEN_P13_EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_V1" in text
    assert "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION=PASS" in text
    assert "P13_DOES_NOT_GRANT_EXECUTION_READINESS=true" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "REQUEST_POS_SIDE=OMITTED" in text
    assert "SEND_TIME_PX_MINTED=false" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION"] == (
        "PASS"
    )
    assert summary["REQUEST_POS_SIDE"] == "OMITTED"
    assert adjudication["P12_EXACT_FLATTEN_PAYLOAD_CLOSED"] is True
    assert adjudication["PRIVATE_AUTH_USED"] is False
    assert adjudication["SEND_TIME_PX_MINTED"] is False


def test_assemble_roundtrip(tmp_path: Path) -> None:
    result = assemble_p13_execution_prerequisite_12_exact_flatten_payload_v1(
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        run_id="roundtrip",
    )
    assert (
        result["adjudication"][
            "EXECUTION_PREREQUISITE_12_EXACT_FLATTEN_PAYLOAD_FROM_OBSERVED_POSITION"
        ]
        == "PASS"
    )
    assert result["MANIFEST_VERIFY_RC"] == 0
    verified = verify_manifest_v1(tmp_path / "roundtrip")
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
