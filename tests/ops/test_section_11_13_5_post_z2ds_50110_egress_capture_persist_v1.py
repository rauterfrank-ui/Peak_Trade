"""Post-Z2DS 50110 egress-capture persist invariants."""

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
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WHITELIST_GO_NOT_CONSUMED,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
SPEC = REPO_ROOT / "docs/ops/specs/POST_Z2DS_PRIVATE_GET_CURRENT_50110_EGRESS_CAPTURE_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_post_z2ds_private_get_current_50110_egress_capture_v1"
    / "20260903T171133Z"
)

Z2DS_HEADING = "### 11.13.5.Z2DS Post-Z2DR runtime read-only evidence maximum leverage persist"
CAPTURE_HEADING = "### 11.13.5 Post-Z2DS one-shot private GET current 50110 egress capture persist"
WHITELIST_HEADING = "### 11.13.5 Post-Z2DS captured-50110 egress IP whitelist minimum add persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_BOUNDARY = (
    "EXISTING_WHITELIST_GO_MAY_USE_THIS_50110_ONLY_IF_STILL_PROVABLY_CURRENT_AT_MUTATION_TIME"
)
SECRETREF = "secretref://vault/peak-trade/live-canary-minimum-exposure/okx"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _capture_section(text: str) -> str:
    start = text.find(CAPTURE_HEADING)
    assert start >= 0, "missing post-Z2DS 50110 capture heading"
    end = text.find(WHITELIST_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing whitelist persist or §11.14 boundary after capture persist"
    return text[start:end]


def test_capture_heading_is_unique_and_follows_z2ds() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(CAPTURE_HEADING) == 1
    assert 0 <= text.find(Z2DS_HEADING) < text.find(CAPTURE_HEADING) < text.find(LADDER_HEADING)


def test_z2ds_text_was_not_rewritten() -> None:
    text = _read(MASTER_RUNBOOK)
    start = text.find(Z2DS_HEADING)
    end = text.find(CAPTURE_HEADING, start)
    section = text[start:end]
    assert "THIS_SLICE=11.13.5.Z2DS" in section
    assert "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DS" in section
    assert "OWNER_GO=PEAK_TRADE_OWNER_GO_POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_V1" in (
        section
    )
    assert OWNER_GO not in section


def test_capture_docs_bind_one_get_without_whitelist_or_p08() -> None:
    section = _capture_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_POST_Z2DS_PRIVATE_GET_CURRENT_50110_EGRESS_CAPTURE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_POST_Z2DS_50110_EGRESS_CAPTURE",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "AUTHORIZED_ENDPOINT=GET /api/v5/account/config",
        "EXECUTED_ENDPOINT=/api/v5/account/config",
        "EXECUTED_HOST=eea.okx.com",
        "EXECUTED_HTTP_METHOD=GET",
        "REQUEST_TIMESTAMP=2026-09-03T17:11:32Z",
        "HTTP_STATUS=401",
        "OKX_CODE=50110",
        "RESULT_CLASS=HTTP_401_OKX_50110",
        "OKX_REPORTED_EGRESS_IPV4=176.5.200.177",
        "OKX_REPORTED_EGRESS_IPV4_CAPTURED=true",
        "GET_COUNT=1",
        "ACTUAL_NETWORK_REQUEST_COUNT=1",
        "HTTP_EXCHANGE_COUNT=1",
        "SECOND_REQUEST_PERFORMED=false",
        "REDIRECT_FOLLOWED=false",
        "WHITELIST_MUTATION_PERFORMED=false",
        "WHITELIST_GO_CONSUMED=false",
        f"WHITELIST_GO={WHITELIST_GO_NOT_CONSUMED}",
        "HISTORICAL_Z2DS_IP_USED=false",
        "POSITIONS_GET_PERFORMED=false",
        "POST_PERFORMED=false",
        "PREREQUISITE_08_CLOSED=false",
        "P08_CLOSED_INFERRED=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        (
            "EVIDENCE_PACK=evidence/ops/section_11_13_5_post_z2ds_private_get_"
            "current_50110_egress_capture_v1/20260903T171133Z"
        ),
        "BODY_SHA256=7b1f3c3a3152a4ee7e7a8f684e83d61d5f5c13b0dc5c26f3f5da86fd402dd7db",
        "ATLAS_AUTHORITY=NONE",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
    )
    for token in required:
        assert token in section, token


def test_capture_docs_forbid_overclaim() -> None:
    section = _capture_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nWHITELIST_MUTATION_PERFORMED=true\n",
        "\nWHITELIST_GO_CONSUMED=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nPOSITIONS_GET_PERFORMED=true\n",
        "\nHISTORICAL_Z2DS_IP_USED=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nP08_CLOSED_INFERRED=true\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "passphrase" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_has_no_capture_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "POST_Z2DS_50110_EGRESS_CAPTURE" not in text
    assert OWNER_GO not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["WHITELIST_MUTATION_PERFORMED"] is False
    assert CLAIMS["P08_CLOSED_INFERRED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert WHITELIST_GO_NOT_CONSUMED in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_capture_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:post_z2ds_50110_egress_capture" in catalog
    marker = "id: RUNTIME_COMPONENT:post_z2ds_private_get_current_50110_egress_capture_v1"
    assert marker in catalog


def test_evidence_pack_manifest_and_capture_fields() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["HTTP_STATUS"] == 401
    assert summary["OKX_CODE"] == "50110"
    assert summary["OKX_REPORTED_EGRESS_IPV4"] == "176.5.200.177"
    assert summary["WHITELIST_MUTATION_PERFORMED"] is False
    assert summary["HISTORICAL_Z2DS_IP_USED"] is False
    snapshot = (EVIDENCE_PACK / "GET_SNAPSHOT.sanitized.json").read_text(encoding="utf-8")
    assert SECRETREF in snapshot
    assert "<REDACTED_KEY_ID>" in snapshot
    lowered = snapshot.lower()
    assert "plaintext:" not in lowered
    assert "api_secret" not in lowered
    assert '"ok-access-key":' not in lowered


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert "GET_REQUEST_COUNT=1" in text
    assert "OKX_REPORTED_EGRESS_IPV4=176.5.200.177" in text
    assert "WHITELIST_MUTATION_PERFORMED=false" in text
