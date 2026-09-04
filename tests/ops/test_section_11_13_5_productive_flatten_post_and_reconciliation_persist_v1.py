"""Persist invariants for productive flatten POST and reconciliation."""

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
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    CANONICAL_RECOVERY_EVIDENCE_RUN_ID,
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
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.persist_claims_v1 import (
    CLAIMS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs" / "system_atlas" / "entities" / "catalog.yaml"
SPEC = REPO_ROOT / "docs/ops/specs/PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_V1.md"
EVIDENCE_PACK = REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / CANONICAL_EVIDENCE_RUN_ID
RECOVERY_PACK = (
    REPO_ROOT / "evidence" / "ops" / EVIDENCE_DIRNAME / CANONICAL_RECOVERY_EVIDENCE_RUN_ID
)

APRPI_HEADING = "### 11.13.5 AUTHENTICATED_PRIVATE_RUNTIME_READ_AND_RUNTIME_PERMIT_ISSUANCE"
FLATTEN_HEADING = "### 11.13.5 PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _flatten_section(text: str) -> str:
    start = text.find(FLATTEN_HEADING)
    assert start >= 0, "missing PRODUCTIVE_FLATTEN persist heading"
    end = text.find(LADDER_HEADING, start)
    assert end > start, "missing §11.14 boundary after flatten persist"
    return text[start:end]


def test_flatten_persist_is_additive_after_aprpi() -> None:
    text = _read(MASTER_RUNBOOK)
    aprpi_start = text.find(APRPI_HEADING)
    flatten_start = text.find(FLATTEN_HEADING)
    ladder = text.find(LADDER_HEADING)
    assert 0 <= aprpi_start < flatten_start < ladder
    aprpi = text[aprpi_start:flatten_start]
    assert "CENSUS_TEXT_REWRITTEN=true" not in aprpi
    assert "PRODUCTIVE_FLATTEN_POST_AUTHORIZED=false" in aprpi


def test_flatten_runbook_persist_tokens() -> None:
    section = _flatten_section(_read(MASTER_RUNBOOK))
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
        "POST_PERFORMED=true",
        "POST_RESULT=POST_ACCEPTED",
        "LIVE_AUTHORIZED=false",
        "CANARY_AUTHORIZED=false",
        "SUBMIT_UNLOCKED=false",
        "LIVE_ENABLED=false",
        "LIVE_ARMED=false",
        "EMPTY_DATA_IS_ZERO=false",
        "CENSUS_TEXT_REWRITTEN=false",
        "MERGE_AUTHORIZED_BY_THIS_PERSIST=false",
        "EXECUTION_READY=false",
        "THIS_GO_DOES_NOT_SET_LIVE_AUTHORIZED=true",
        "TARGET_POSITION_ZERO_PROVEN=false",
        "LIVE_FLATTEN_PROVABILITY_PROVEN=false",
        "RETRY_USED=false",
        "FUNDING_USED=false",
        "G10_STATUS=CLOSED_PRODUCTIVE_FLATTEN_POST_PERFORMED",
        "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN",
        f"EVIDENCE_PACK=evidence/ops/{EVIDENCE_DIRNAME}/{CANONICAL_EVIDENCE_RUN_ID}",
        (
            f"RECOVERY_EVIDENCE_PACK=evidence/ops/{EVIDENCE_DIRNAME}/"
            f"{CANONICAL_RECOVERY_EVIDENCE_RUN_ID}"
        ),
        "ATLAS_AUTHORITY=NONE",
        "LANDSCAPE_AUTHORITY=NONE",
    )
    for token in required:
        assert token in section, token
    forbidden = (
        "\nLIVE_AUTHORIZED=true\n",
        "\nCANARY_AUTHORIZED=true\n",
        "\nEMPTY_DATA_IS_ZERO=true\n",
        "\nMERGE_AUTHORIZED_BY_THIS_PERSIST=true\n",
        "\nEXECUTION_READY=true\n",
        "\nCENSUS_TEXT_REWRITTEN=true\n",
        "\nLIVE_FLATTEN_PROVABILITY_PROVEN=true\n",
        "\nTARGET_POSITION_ZERO_PROVEN=true\n",
        "\nRETRY_USED=true\n",
        "\nFUNDING_USED=true\n",
        "\nATLAS_AUTHORITY=CANONICAL\n",
    )
    for token in forbidden:
        assert token not in section, token
    assert "api_secret" not in section.lower()
    assert "ok-access-" not in section.lower()


def test_map_of_truth_is_navigation_only() -> None:
    text = _read(MAP_OF_TRUTH)
    assert "DOCUMENT_ROLE=NAVIGATION_ONLY_NO_SEMANTICS" in text
    assert OWNER_GO not in text
    assert "PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION" in text


def test_atlas_flatten_is_navigation_only() -> None:
    catalog = _read(ATLAS_CATALOG)
    authority = _read(REPO_ROOT / "docs" / "system_atlas" / "ATLAS_AUTHORITY_AND_USAGE.md")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:productive_flatten_post_and_reconciliation" in catalog
    assert "id: RUNTIME_COMPONENT:productive_flatten_post_and_reconciliation_v1" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog


def test_code_claims_remain_fail_closed_for_standing_flags() -> None:
    assert CLAIMS["OWNER_GO"] == OWNER_GO
    assert CLAIMS["THIS_SLICE"] == THIS_SLICE
    assert CLAIMS["PRODUCTIVE_FLATTEN_POST_AUTHORIZED"] is True
    assert CLAIMS["STANDING_LIVE_AUTHORIZED"] is False
    assert CLAIMS["RETRY_ALLOWED"] is False
    assert CLAIMS["EMPTY_DATA_IS_ZERO"] is False
    assert CLAIMS["NEXT_AUTHORITY_BOUNDARY"] == NEXT_AUTHORITY_BOUNDARY
    assert OWNER_GO in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False


def test_spec_token_and_no_live_unlock() -> None:
    text = _read(SPEC)
    assert "docs_token: DOCS_TOKEN_PRODUCTIVE_FLATTEN_POST_AND_RECONCILIATION_V1" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "EMPTY_DATA_IS_ZERO=false" in text
    assert "LIVE_FLATTEN_PROVABILITY_PROVEN=false" in text
    assert "NEXT_AUTHORITY_BOUNDARY=OWNER_MERGE_GO" in text


def test_evidence_pack_manifest_and_claims() -> None:
    verified = verify_manifest_v1(EVIDENCE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    claims = json.loads((EVIDENCE_PACK / "claims.json").read_text(encoding="utf-8"))
    summary = json.loads((EVIDENCE_PACK / "SUMMARY.json").read_text(encoding="utf-8"))
    adjudication = json.loads((EVIDENCE_PACK / "ADJUDICATION.json").read_text(encoding="utf-8"))
    assert claims["POST_PERFORMED"] is True
    assert summary["POST_RESULT"] == "POST_ACCEPTED"
    assert summary["LIVE_AUTHORIZED"] is False
    assert summary["CANARY_AUTHORIZED"] is False
    assert summary["TARGET_POSITION_ZERO_PROVEN"] is False
    assert summary["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert summary["RETRY_USED"] is False
    assert adjudication["G10_STATUS"] == "CLOSED_PRODUCTIVE_FLATTEN_POST_PERFORMED"
    assert adjudication["G12_STATUS"] == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert (EVIDENCE_PACK / "OBSERVATIONS.sanitized.json").is_file()
    assert (EVIDENCE_PACK / "RUNTIME_PERMIT.json").is_file()
    assert (EVIDENCE_PACK / "POST_ACTION.sanitized.json").is_file()


def test_recovery_pack_empty_data_is_not_zero_and_fill_is_bound() -> None:
    verified = verify_manifest_v1(RECOVERY_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    recovery = json.loads(
        (RECOVERY_PACK / "RECOVERY_RECON.sanitized.json").read_text(encoding="utf-8")
    )
    assert recovery["OBSERVATION"]["POSITION_OBSERVATION_CLASS"] == "CASE_C_EMPTY_DATA_NOT_ZERO"
    assert recovery["OBSERVATION"]["TARGET_POSITION_ZERO_PROVEN"] is False
    fills = recovery["OBSERVATIONS"]["GET_TRADE_FILLS_RECOVERY"]["REDACTED_PAYLOAD"]["data"]
    bound = [
        row
        for row in fills
        if str(row.get("clOrdId") or "") == "ptokxeprod508b7b41508b7b4101"
        and str(row.get("side") or "") == "sell"
        and str(row.get("fillSz") or "") == "1"
    ]
    assert len(bound) == 1
    assert recovery["PENDING_ROW_COUNT"] == 0
    assert recovery["POST_USED"] is False
    assert recovery["RETRY_USED"] is False
    assert recovery["LIVE_AUTHORIZED"] is False
