"""Post-whitelist private auth attestation persist invariants."""

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
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_AUTHORITY_BOUNDARY_CASE_A,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = (
    REPO_ROOT / "docs/ops/specs/POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_V1.md"
)
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_post_z2ds_post_whitelist_private_auth_attestation_v1"
    / "20260903T181718Z"
)

WHITELIST_HEADING = "### 11.13.5 Post-Z2DS captured-50110 egress IP whitelist minimum add persist"
ATTESTATION_HEADING = (
    "### 11.13.5 Post-Z2DS post-whitelist private auth attestation single GET persist"
)
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


P08_HEADING = "### 11.13.5 P08 position observation single GET persist"


def _attestation_section(text: str) -> str:
    start = text.find(ATTESTATION_HEADING)
    assert start >= 0, "missing post-whitelist private auth attestation heading"
    end = text.find(P08_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing P08 or §11.14 boundary after attestation persist"
    return text[start:end]


def test_attestation_heading_is_unique_and_follows_whitelist() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(ATTESTATION_HEADING) == 1
    assert (
        0
        <= text.find(WHITELIST_HEADING)
        < text.find(ATTESTATION_HEADING)
        < text.find(LADDER_HEADING)
    )


def test_whitelist_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    start = text.find(WHITELIST_HEADING)
    end = text.find(ATTESTATION_HEADING, start)
    section = text[start:end]
    assert "THIS_SLICE=11.13.5.POST_Z2DS_50110_WHITELIST_ADD_FROM_CAPTURE" in section
    assert "RUNTIME_50110_CLEARANCE=NOT_TESTED" in section
    assert OWNER_GO not in section


def test_attestation_docs_bind_one_get_without_p08() -> None:
    section = _attestation_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION_SINGLE_GET_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        "OWNER_GO_CONSUMED=true",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "AUTHORIZED_ENDPOINT=GET /api/v5/account/config",
        "EXECUTED_ENDPOINT=/api/v5/account/config",
        "EXECUTED_HOST=eea.okx.com",
        "EXECUTED_HTTP_METHOD=GET",
        "REQUEST_TIMESTAMP=2026-09-03T18:17:18Z",
        "HTTP_STATUS=200",
        "OKX_CODE=0",
        "RESULT_CLASS=HTTP_200_OKX_0",
        "OKX_REPORTED_EGRESS_IPV4=NONE",
        "PRIVATE_API_AUTH_SUCCESS=PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME",
        "RUNTIME_50110_CLEARANCE=PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME",
        "PRIVATE_AUTH_BLOCKER_50110=CLEARED_AT_OBSERVATION_TIME",
        "GET_COUNT=1",
        "ACTUAL_NETWORK_REQUEST_COUNT=1",
        "HTTP_EXCHANGE_COUNT=1",
        "SECOND_REQUEST_PERFORMED=false",
        "AUTH_HEADER_SENT=true",
        "REDIRECT_FOLLOWED=false",
        "WHITELIST_MUTATION_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "PREREQUISITE_08_CLOSED=false",
        "TARGET_POSITION_NONZERO_PROVEN=false",
        "POSITION_STATE_OBSERVED=false",
        "G_POSMODE_SUBMIT_BODY_PROVEN=false",
        "ACCOUNT_CONFIG_USED_AS_POSSIDE_PROOF=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_AUTHORITY_BOUNDARY_CASE_A}",
        (
            "EVIDENCE_PACK=evidence/ops/section_11_13_5_post_z2ds_post_whitelist_"
            "private_auth_attestation_v1/20260903T181718Z"
        ),
        "BODY_SHA256=36876f8378c2029823643ac2caf6b2fd24525b7d41afa0a32b6abef46c72d5fb",
        "ATLAS_AUTHORITY=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for token in required:
        assert token in section, token


def test_attestation_docs_forbid_overclaim() -> None:
    section = _attestation_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nTARGET_POSITION_NONZERO_PROVEN=true\n",
        "\nPOSITION_STATE_OBSERVED=true\n",
        "\nG_POSMODE_SUBMIT_BODY_PROVEN=true\n",
        "\nWHITELIST_MUTATION_PERFORMED=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nPOSITIONS_GET_PERFORMED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nP08_CLOSED_INFERRED=true\n",
        "\nACCOUNT_CONFIG_USED_AS_POSSIDE_PROOF=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_attestation_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "POST_Z2DS_POST_WHITELIST_PRIVATE_AUTH_ATTESTATION" not in text
    assert OWNER_GO not in text


def test_atlas_attestation_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:post_z2ds_post_whitelist_private_auth_attestation" in catalog
    assert "id: RUNTIME_COMPONENT:post_z2ds_post_whitelist_private_auth_attestation_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["WHITELIST_MUTATION_PERFORMED"] is False
    assert CLAIMS["P08_CLOSED_INFERRED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["G_POSMODE_SUBMIT_BODY_PROVEN"] is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False


def test_evidence_pack_manifest_and_attestation_fields() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["HTTP_STATUS"] == 200
    assert summary["OKX_CODE"] == "0"
    assert summary["RESULT_CLASS"] == "HTTP_200_OKX_0"
    assert summary["PRIVATE_API_AUTH_SUCCESS"] == ("PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME")
    assert summary["RUNTIME_50110_CLEARANCE"] == ("PROVEN_FOR_THIS_ENDPOINT_AND_OBSERVATION_TIME")
    assert summary["PRIVATE_AUTH_BLOCKER_50110"] == "CLEARED_AT_OBSERVATION_TIME"
    assert summary["OKX_REPORTED_EGRESS_IPV4"] == "NONE"
    assert summary["PREREQUISITE_08_CLOSED"] is False
    assert summary["OWNER_GO_CONSUMED"] is True
    assert summary["GET_REQUEST_COUNT"] == 1
    assert summary["POST_COUNT"] == 0
    snapshot = (EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    assert SECRETREF in snapshot
    assert "acctLv" not in snapshot
    assert "posMode" not in snapshot
    lowered = snapshot.lower()
    assert "plaintext:" not in lowered
    assert "api_secret" not in lowered
    assert '"ok-access-key":' not in lowered


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert "GET_REQUEST_COUNT=1" in text
    assert "HTTP_STATUS=200" in text
    assert "OKX_CODE=0" in text
    assert "PREREQUISITE_08_CLOSED=false" in text
    assert "WHITELIST_MUTATION_PERFORMED=false" in text
    assert NEXT_AUTHORITY_BOUNDARY_CASE_A in text
