"""Bound U05 interest-accrued GET acquisition tests.

Exactly one GET /api/v5/account/interest-accrued?type=2&limit=100.
Empty/zero/absent is not absence. GET alone may not INCLUDE or EXCLUDE.
No retry. No POST. No witness acquisition.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_URL,
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO,
    OWNER_GO,
    PRIMARY_PROOF_STATUS,
    U05PrimaryProofBoundInterestAccruedGetAcquisitionError,
    execute_u05_primary_proof_bound_interest_accrued_get_acquisition_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CD_HEADING = "11.2.1.CD FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u05_primary_proof_bound_interest_accrued_get_acquisition_v1.py"
)
AUTHORIZED_PATH = "/api/v5/account/interest-accrued"


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _empty_body() -> bytes:
    return b'{"code":"0","msg":"","data":[]}'


def _identity_row_body() -> bytes:
    return (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","instId":"","mgnMode":"cross",'
        b'"interest":"0.01","interestRate":"0.0001","liab":"1.25","totalLiab":"1.25",'
        b'"interestFreeLiab":"0","ts":"1726240000000"}]}'
    )


def _run(
    *,
    tmp_path: Path,
    body: bytes,
    status_code: int = 200,
    as_of: str = CANONICAL_PERSIST_AS_OF,
) -> tuple[object, Path, RecordingFakeCanaryTransportV1]:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        status_code=status_code,
        bodies_by_endpoint={AUTHORIZED_PATH: body},
    )
    result = execute_u05_primary_proof_bound_interest_accrued_get_acquisition_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "obs",
        repo_root=REPO_ROOT,
        genesis_store_root=genesis,
        transport=transport,
        persist_as_of=as_of,
    )
    return result, Path(result.store_root), transport


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(
        U05PrimaryProofBoundInterestAccruedGetAcquisitionError, match="OWNER_GO_MISMATCH"
    ):
        execute_u05_primary_proof_bound_interest_accrued_get_acquisition_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            transport=RecordingFakeCanaryTransportV1(body=_empty_body()),
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_empty_data_persists_raw_and_does_not_exclude(tmp_path: Path) -> None:
    result, store, transport = _run(tmp_path=tmp_path, body=_empty_body())
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    capture = json.loads((store / "raw_http_capture_v1.json").read_text(encoding="utf-8"))
    evaluation = json.loads(
        (store / "current_proof_evaluation_v1.json").read_text(encoding="utf-8")
    )
    assert result.actual_get_count == "1"
    assert result.retry_count == "0"
    assert result.post_count == "0"
    assert result.http_status == "200"
    assert result.venue_code == "0"
    assert result.raw_evidence_persisted == "true"
    assert result.qualifying_liability_rows == "0"
    assert result.independent_liability_event_proven == "false"
    assert result.non_algebraic_embedding_identity == "UNKNOWN"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert claims["OWNER_GO_STATUS"] == "CONSUMED"
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert evaluation["get_alone_may_include"] == "false"
    assert evaluation["get_alone_may_exclude"] == "false"
    assert capture["query"] == "type=2&limit=100"
    assert capture["url"] == AUTHORIZED_URL
    assert len(transport.calls) == 1
    assert transport.calls[0].endpoint == AUTHORIZED_ENDPOINT
    assert (store / "raw_interest_accrued_response_body.json").is_file()
    assert verify_manifest_sha256_v1(store_root=store) == 0
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO


def test_identity_row_does_not_prove_embedding_or_include(tmp_path: Path) -> None:
    result, store, _transport = _run(tmp_path=tmp_path, body=_identity_row_body())
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    producer = json.loads((store / "producer_consumption_v1.json").read_text(encoding="utf-8"))
    assert result.qualifying_liability_rows == "1"
    assert result.independent_liability_event_proven == "false"
    assert result.non_algebraic_embedding_identity == "UNKNOWN"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert producer["producer_qualifying_liability_event_count"] == "0"
    assert claims["INDEPENDENT_LIABILITY_EVENT_PROVEN"] == "false"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_http_error_persists_raw_and_consumes_go_without_retry(tmp_path: Path) -> None:
    result, store, transport = _run(tmp_path=tmp_path, body=b'{"code":"50113"}', status_code=401)
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert result.actual_get_count == "1"
    assert result.retry_count == "0"
    assert result.http_status == "401"
    assert result.raw_evidence_persisted == "true"
    assert claims["OWNER_GO_STATUS"] == "CONSUMED"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert len(transport.calls) == 1


def test_source_does_not_retry_or_post() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    assert "max_retries" not in source
    assert "GET_ENDPOINTS_PRIVATE" not in source
    assert 'AUTHORIZED_PATH = "/api/v5/account/interest-accrued"' in source
    assert 'AUTHORIZED_QUERY = "type=2&limit=100"' in source
    assert "TIMEOUT_SECONDS = 15.0" in source
    assert "after=" not in AUTHORIZED_URL
    assert "before=" not in AUTHORIZED_URL


def test_canonical_pack_sealed_and_empty_is_not_exclude() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    capture = json.loads((CANONICAL_PACK / "raw_http_capture_v1.json").read_text(encoding="utf-8"))
    body = json.loads(
        (CANONICAL_PACK / "raw_interest_accrued_response_body.json").read_text(encoding="utf-8")
    )
    assert claims["ACTUAL_GET_COUNT"] == "1"
    assert claims["RETRY_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["HTTP_STATUS"] == "200"
    assert claims["VENUE_CODE"] == "0"
    assert claims["RAW_EVIDENCE_PERSISTED"] == "true"
    assert claims["QUALIFYING_LIABILITY_ROWS"] == "0"
    assert claims["INDEPENDENT_LIABILITY_EVENT_PROVEN"] == "false"
    assert claims["NON_ALGEBRAIC_EMBEDDING_IDENTITY"] == "UNKNOWN"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["SECRET_PERSISTED"] == "false"
    assert capture["url"] == AUTHORIZED_URL
    assert body == {"code": "0", "data": [], "msg": ""}
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cd_persists_consumed_get() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CD_HEADING)
    cd_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cd_section
    assert (
        "THIS_SLICE=11.2.1.CD.FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION"
        in cd_section
    )
    assert "ACTUAL_GET_COUNT=1" in cd_section
    assert "HTTP_STATUS=200" in cd_section
    assert "VENUE_CODE=0" in cd_section
    assert "QUALIFYING_LIABILITY_ROWS=0" in cd_section
    assert "INDEPENDENT_LIABILITY_EVENT_PROVEN=false" in cd_section
    assert "NON_ALGEBRAIC_EMBEDDING_IDENTITY=UNKNOWN" in cd_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in cd_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in cd_section
    assert "GET_ALONE_MAY_INCLUDE=false" in cd_section
    assert "GET_ALONE_MAY_EXCLUDE=false" in cd_section
    assert BLOCKER_ID in cd_section
    assert NEXT_OWNER_GO in cd_section
    assert PRIMARY_PROOF_STATUS in cd_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CD" in cd_section
    assert (
        "DOCS_TOKEN_FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION_V1" in spec
    )
    assert "FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION_V1.md" in mot
    assert CD_HEADING in mot
    assert "11.2.1.CD" in atlas
    assert "u05_primary_proof_bound_interest_accrued_get_acquisition_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
