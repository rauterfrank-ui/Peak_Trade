"""Persist invariants for authenticated private read / runtime permit issuance."""

from __future__ import annotations

import json
import subprocess
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
    PR_CHANGED_PATHS_FREEZE_BASE_SHA,
    PR_CHANGED_PATHS_FREEZE_COUNT,
    PR_CHANGED_PATHS_FREEZE_DIRNAME,
    PR_CHANGED_PATHS_FREEZE_HEAD_SHA,
    PR_CHANGED_PATHS_FREEZE_SET_HASH,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    execute_authenticated_private_runtime_read_and_permit_issuance_v1,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.pr_changed_paths_freeze_v1 import (
    canonical_pr_changed_paths_freeze_pack_v1,
    changed_paths_set_hash_v1,
    collect_three_dot_changed_paths_v1,
    persist_pr_changed_paths_freeze_v1,
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
FREEZE_PACK = canonical_pr_changed_paths_freeze_pack_v1(REPO_ROOT)

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
        (
            "PR_CHANGED_PATHS_FREEZE_PACK=evidence/ops/"
            f"{EVIDENCE_DIRNAME}/{PR_CHANGED_PATHS_FREEZE_DIRNAME}"
        ),
        f"PR_CHANGED_PATHS_FREEZE_BASE_SHA={PR_CHANGED_PATHS_FREEZE_BASE_SHA}",
        f"PR_CHANGED_PATHS_FREEZE_HEAD_SHA={PR_CHANGED_PATHS_FREEZE_HEAD_SHA}",
        f"PR_CHANGED_PATHS_FREEZE_COUNT={PR_CHANGED_PATHS_FREEZE_COUNT}",
        f"PR_CHANGED_PATHS_FREEZE_SET_HASH={PR_CHANGED_PATHS_FREEZE_SET_HASH}",
        "APRPI_TEMP_ONLY_EVIDENCE_REMAINING=false",
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
    assert "pr_changed_paths_freeze_v1" in catalog


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


def test_pr_changed_paths_freeze_matches_git_three_dot_binding() -> None:
    verified = verify_manifest_v1(FREEZE_PACK)
    assert int(verified["MANIFEST_VERIFY_RC"]) == 0
    freeze = json.loads((FREEZE_PACK / "FREEZE.json").read_text(encoding="utf-8"))
    text_bytes = (FREEZE_PACK / "CHANGED_PATHS.txt").read_bytes()
    persisted = tuple(line for line in text_bytes.decode("utf-8").splitlines() if line.strip())
    reconstructed = collect_three_dot_changed_paths_v1(
        repo_root=REPO_ROOT,
        base_sha=PR_CHANGED_PATHS_FREEZE_BASE_SHA,
        head_sha=PR_CHANGED_PATHS_FREEZE_HEAD_SHA,
    )
    assert freeze["BASE_SHA"] == PR_CHANGED_PATHS_FREEZE_BASE_SHA
    assert freeze["HEAD_SHA"] == PR_CHANGED_PATHS_FREEZE_HEAD_SHA
    assert freeze["CHANGED_FILE_COUNT"] == PR_CHANGED_PATHS_FREEZE_COUNT
    assert freeze["CHANGED_FILE_SET_HASH"] == PR_CHANGED_PATHS_FREEZE_SET_HASH
    assert freeze["TEMP_PATH_IS_AUTHORITY"] is False
    assert freeze["CREATED_AT_UTC_IN_PATH_SET_HASH"] is False
    assert freeze["POST_PERFORMED"] is False
    assert persisted == reconstructed
    assert len(persisted) == PR_CHANGED_PATHS_FREEZE_COUNT
    assert changed_paths_set_hash_v1(persisted) == PR_CHANGED_PATHS_FREEZE_SET_HASH
    assert changed_paths_set_hash_v1(reconstructed) == PR_CHANGED_PATHS_FREEZE_SET_HASH
    assert freeze["CHANGED_PATHS"] == list(reconstructed)
    runtime_manifest = (EVIDENCE_PACK / "MANIFEST.sha256").read_text(encoding="utf-8")
    assert "CHANGED_PATHS.txt" not in runtime_manifest
    assert "pr_changed_paths_freeze_v1" not in runtime_manifest


def test_pr_changed_paths_set_hash_ignores_created_at_utc(tmp_path: Path) -> None:
    first = persist_pr_changed_paths_freeze_v1(
        repo_root=REPO_ROOT,
        pack=tmp_path / "a",
        created_at_utc="2026-09-04T00:00:00Z",
    )
    second = persist_pr_changed_paths_freeze_v1(
        repo_root=REPO_ROOT,
        pack=tmp_path / "b",
        created_at_utc="2026-09-04T23:59:59Z",
    )
    assert first["CHANGED_FILE_SET_HASH"] == second["CHANGED_FILE_SET_HASH"]
    assert first["CHANGED_FILE_SET_HASH"] == PR_CHANGED_PATHS_FREEZE_SET_HASH
    a_paths = (tmp_path / "a" / "CHANGED_PATHS.txt").read_bytes()
    b_paths = (tmp_path / "b" / "CHANGED_PATHS.txt").read_bytes()
    assert a_paths == b_paths
    a_freeze = json.loads((tmp_path / "a" / "FREEZE.json").read_text(encoding="utf-8"))
    b_freeze = json.loads((tmp_path / "b" / "FREEZE.json").read_text(encoding="utf-8"))
    assert a_freeze["CREATED_AT_UTC"] != b_freeze["CREATED_AT_UTC"]
    assert a_freeze["CHANGED_FILE_SET_HASH"] == b_freeze["CHANGED_FILE_SET_HASH"]


def test_frozen_changed_paths_selector_remains_pr_bounded_full() -> None:
    completed = subprocess.run(
        [
            str(REPO_ROOT / "scripts" / "pt"),
            "scripts/ops/ci_test_selection_v1.py",
            "--files-file",
            str(FREEZE_PACK / "CHANGED_PATHS.txt"),
            "--event-name",
            "pull_request",
        ],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "test_selection_mode=PR_BOUNDED_FULL" in completed.stdout
    assert "test_selection_reason=category_central_src_requires_full" in completed.stdout
    assert "tests_execute_pr_bounded_full=true" in completed.stdout
