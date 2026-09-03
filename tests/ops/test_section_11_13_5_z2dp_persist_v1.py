"""§11.13.5.Z2DP fresh create-readiness evidence persist invariants."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.route_c_submit_composition_constants_v1 import (
    POSITION_MODE_FAIL_CLOSED,
    POSITION_MODE_SUBMIT_BODY_SEMANTICS,
    PREREQUISITE_08_CLOSED as ROUTE_C_PREREQUISITE_08_CLOSED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md"
SPEC = REPO_ROOT / "docs" / "ops" / "specs" / "POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1.md"
EVIDENCE_PACK = (
    REPO_ROOT
    / "evidence"
    / "ops"
    / "section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1"
    / "20260903T114921Z"
)

Z2DO_HEADING = "### 11.13.5.Z2DO Route-C offline gated productive submit composition persist"
Z2DP_HEADING = "### 11.13.5.Z2DP Post-Z2DO fresh Route-C create-readiness GET evidence persist"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
NEXT_BOUNDARY = (
    "SEPARATE_OWNER_GO_REQUIRED_BEFORE_ANY_POST_OR_POSITION_CREATION_OR_FLATTEN_OR_LIVE_OR_CANARY"
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _z2dp_section(text: str) -> str:
    start = text.find(Z2DP_HEADING)
    assert start >= 0, "missing §11.13.5.Z2DP heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after Z2DP"
    return text[start:end]


def test_z2dp_heading_is_unique_and_follows_z2do() -> None:
    text = _read(MASTER_RUNBOOK)
    assert text.count(Z2DP_HEADING) == 1
    assert 0 <= text.find(Z2DO_HEADING) < text.find(Z2DP_HEADING) < text.find(LADDER_HEADING)


def test_z2dp_docs_bind_get_evidence_without_post_or_08_close() -> None:
    section = _z2dp_section(_read(MASTER_RUNBOOK))
    required = (
        "AUTHORIZED_SCOPE=A_Z2DP_POST_Z2DO_FRESH_CREATE_READINESS_GET_EVIDENCE_ONLY",
        f"OWNER_GO={OWNER_GO}",
        "OWNER_GO_STATUS=CONSUMED",
        f"CURRENT_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}",
        "EXPECTED_ORIGIN_MAIN_SHA_MATCH=true",
        f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}",
        f"THIS_SLICE={THIS_SLICE}",
        "LAST_CANONICALLY_CLOSED_STEP=SECTION_11_13_5_Z2DP",
        "CURRENT_CANONICAL_SECTION=11.13.5.Z2DP",
        "CURRENT_CANONICAL_SECTION_REPLACED=false",
        "Z2DO_TEXT_REWRITTEN=false",
        "Z2DN_TEXT_REWRITTEN=false",
        "Z2DM_TEXT_REWRITTEN=false",
        f"WORKPACKAGE_ID={WORKPACKAGE_ID}",
        "GET_REQUEST_COUNT=12",
        "FUNDING_GET_PERFORMED=false",
        "POSITIONS_GET_PERFORMED=true",
        "POST_PERFORMED=false",
        "CREATE_ACCOUNT_IDENTITY_READY=true",
        "POSITION_MODE_SUBMIT_BODY_SEMANTICS=UNPROVEN",
        "POSITION_MODE_FAIL_CLOSED=true",
        "POSITION_MODE_READY=false",
        "PRETRADE_GATES_READY=false",
        "FUNDING_EXPOSURE_READY=false",
        "VENUE_NONZERO_CAPACITY=PROVEN_ZERO",
        "CURRENT_ROUTE_C_QUANTITY_ADMISSIBILITY=BLOCKED_BY_VENUE_CAPACITY",
        "PREREQUISITE_08_CLOSED=false",
        "CREATE_READINESS_AFTER_FRESH_EVIDENCE=BLOCKED_BY_MULTIPLE_GAPS",
        "CREATE_PATH_ARCHITECTURALLY_COMPLETE=true",
        "CREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=false",
        "CURRENT_PRODUCTIVE_WIRE_REACHABLE=false",
        "CREATE_PATH_CURRENTLY_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "ATLAS_MUTATION=false",
        "ATLAS_IMPACT=UPDATED",
        "LANDSCAPE_MUTATION=false",
        "NO_MAP_OF_TRUTH_MUTATION=true",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        f"NEXT_AUTHORITY_BOUNDARY={NEXT_BOUNDARY}",
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY="
        "EXECUTION_PREREQUISITE_08_TARGET_POSITION_NONZERO_PROVEN",
    )
    for token in required:
        assert token in section, token


def test_z2dp_docs_forbid_overclaim() -> None:
    section = _z2dp_section(_read(MASTER_RUNBOOK))
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nSUBMIT_UNLOCKED=true\n",
        "\nPREREQUISITE_08_CLOSED=true\n",
        "\nCREATE_PATH_CURRENTLY_AUTHORIZED=true\n",
        "\nCURRENT_PRODUCTIVE_WIRE_REACHABLE=true\n",
        "\nCREATE_PATH_PRODUCTIVE_WIRE_CAPABLE=true\n",
        "\nPOST_PERFORMED=true\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_OMIT_POSSIDE\n",
        "\nPOSITION_MODE_SUBMIT_BODY_SEMANTICS=PROVEN_EMIT_POSSIDE_NET\n",
        "\nCREATE_READINESS_AFTER_FRESH_EVIDENCE=READY_FOR_SEPARATE_RISK_BEARING_OWNER_GO\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
        "\nLANDSCAPE_AUTHORITY=SSOT\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()


def test_map_of_truth_has_no_z2dp_semantic_entry() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert "Z2DP" not in text
    assert "11.13.5.Z2DP" not in text


def test_code_claims_remain_fail_closed() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
    assert CLAIMS["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    assert CLAIMS["POST_ALLOWED"] is False
    assert POSITION_MODE_SUBMIT_BODY_SEMANTICS == "UNPROVEN"
    assert POSITION_MODE_FAIL_CLOSED is True
    assert ROUTE_C_PREREQUISITE_08_CLOSED is False
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_atlas_z2dp_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(ATLAS_AUTHORITY)
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:z2dp" in catalog
    marker = "id: RUNTIME_COMPONENT:post_z2do_fresh_create_readiness_evidence_v1"
    assert marker in catalog
    start = catalog.find(marker)
    end = catalog.find("\n  - id:", start + 1)
    block = catalog[start:] if end < 0 else catalog[start:end]
    assert "current_canonical: false" in block
    assert "ATLAS_AUTHORITY=NONE" in block
    assert "execute_v1.py" in block
    assert (
        "src/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/__init__.py"
        in block
    )
    assert (
        "src/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/persist_claims_v1.py"
        in block
    )
    assert (
        "src/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/persist_v1.py"
        in block
    )
    assert (
        "src/ops/section_11_13_5_z2dp_post_z2do_fresh_create_readiness_evidence_v1/redaction_v1.py"
        in block
    )


def test_evidence_pack_manifest_verifies_and_matches_adjudication() -> None:
    assert EVIDENCE_PACK.is_dir()
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert adjudication["CREATE_ACCOUNT_IDENTITY_READY"] is True
    assert adjudication["POSITION_MODE_SUBMIT_BODY_SEMANTICS"] == "UNPROVEN"
    assert adjudication["PREREQUISITE_08_CLOSED"] is False
    assert adjudication["VENUE_NONZERO_CAPACITY"] == "PROVEN_ZERO"
    assert adjudication["CREATE_READINESS_AFTER_FRESH_EVIDENCE"] == "BLOCKED_BY_MULTIPLE_GAPS"
    assert adjudication["CURRENT_PRODUCTIVE_WIRE_REACHABLE"] is False
    assert adjudication["CREATE_PATH_CURRENTLY_AUTHORIZED"] is False
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["POST_COUNT"] == 0
    assert summary["FUNDING_GET_PERFORMED"] is False
    spec = _read(SPEC)
    assert "CREATE_READINESS_AFTER_FRESH_EVIDENCE=BLOCKED_BY_MULTIPLE_GAPS" in spec
    assert "docs_token: DOCS_TOKEN_POST_Z2DO_FRESH_CREATE_READINESS_EVIDENCE_V1" in spec
