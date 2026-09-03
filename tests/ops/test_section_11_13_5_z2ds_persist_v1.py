"""§11.13.5.Z2DS post-Z2DR runtime read-only evidence persist invariants."""

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
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    PREREQUISITE_08_CLOSED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
SPEC = REPO_ROOT / "docs/ops/specs/POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2ds_post_z2dr_runtime_read_only_evidence_max_leverage_v1"
    / "20260903T155946Z"
)

Z2DR_HEADING = "### 11.13.5.Z2DR Post-Z2DQ Route-C create-path blocker census SSOT persist"
Z2DS_HEADING = "### 11.13.5.Z2DS Post-Z2DR runtime read-only evidence maximum leverage persist"
CAPTURE_HEADING = "### 11.13.5 Post-Z2DS one-shot private GET current 50110 egress capture persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_POST_OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2ds_section(text: str) -> str:
    start = text.find(Z2DS_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DS heading"
    end = text.find(CAPTURE_HEADING, start)
    if end < 0:
        end = text.find(LADDER_HEADING, start)
    assert end > start, "missing capture persist or §11.14 boundary after Z2DS"
    return text[start:end]


def test_z2ds_heading_is_unique_and_follows_z2dr() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DS_HEADING) == 1
    assert 0 <= text.find(Z2DR_HEADING) < text.find(Z2DS_HEADING) < text.find(LADDER_HEADING)


def test_z2ds_docs_bind_get_evidence_without_post_or_08_close() -> None:
    section = _z2ds_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DS_POST_Z2DR_RUNTIME_READ_ONLY_EVIDENCE_MAX_LEVERAGE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DS",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DS",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "GET_REQUEST_COUNT=10",
        "PUBLIC_GET_COUNT=3",
        "PRIVATE_GET_COUNT=7",
        "FUNDING_GET_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=true",
        "POST_PERFORMED=false",
        "NETWORK_CALL_PERFORMED=true",
        "VENUE_NETWORK_ACCESS=true",
        "PRIVATE_AUTH_FAILURE_CLASS=HTTP_401_OKX_50110",
        "TARGET_POSITION_OBSERVATION=AUTH_FAILED",
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        "MAX_SAFE_READ_ONLY_RUNTIME_BUNDLE_REMAINING=0",
        "PREREQUISITE_08_CLOSED=false",
        "CREATE_PATH_CURRENTLY_AUTHORIZED=false",
        "THIS_GO_AUTHORIZES_GET=true",
        "THIS_GO_AUTHORIZES_POST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
    )
    for token in required:
        assert token in section, token


def test_z2ds_docs_forbid_overclaim() -> None:
    section = _z2ds_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCREATE_PATH_CURRENTLY_AUTHORIZED=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_OMIT_POSSIDE\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
    )
    for token in forbidden:
        assert token not in section, token


def test_map_of_truth_has_no_z2ds_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DS" not in text
    assert "11.13.5.Z2DS" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert CLAIMS["POST_PERFORMED"] is False
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert POSITION_MODE_FAIL_CLOSED is True
    assert PREREQUISITE_08_CLOSED is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2ds_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:z2ds" in catalog


def test_evidence_pack_manifest_and_claims() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SECRET_VALUES_INCLUDED"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["MAX_SAFE_READ_ONLY_RUNTIME_BUNDLE_REMAINING"] == 0
    assert summary["TARGET_POSITION_OBSERVATION"] == "AUTH_FAILED"


def test_spec_exists() -> None:
    assert SPEC.is_file()
    text = _read(SPEC)
    assert f"OWNER_GO" in text or OWNER_GO.split("_")[-1] in text
    assert "GET_REQUEST_COUNT=10" in text
