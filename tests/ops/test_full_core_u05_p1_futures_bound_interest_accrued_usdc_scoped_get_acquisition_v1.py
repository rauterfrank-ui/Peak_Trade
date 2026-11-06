"""P1 FUTURES USDC-scoped interest-accrued GET acquisition tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1 import (
    AUTHORIZED_PATH,
    AUTHORIZED_QUERY,
    BOUND_SETTLEMENT_CCY,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAX_GET_COUNT,
    OWNER_GO,
    U05P1FuturesBoundInterestAccruedGetAcquisitionError,
    execute_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_QUERY as CD_QUERY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1.py"
)
PERSIST_AS_OF = "2026-09-20T22:30:00Z"


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _run(*, tmp_path: Path, body: bytes) -> tuple[object, Path, RecordingFakeCanaryTransportV1]:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        status_code=200,
        bodies_by_endpoint={AUTHORIZED_PATH: body},
    )
    result = execute_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "obs",
        repo_root=REPO_ROOT,
        genesis_store_root=genesis,
        transport=transport,
        persist_as_of=PERSIST_AS_OF,
    )
    return result, Path(result.store_root), transport


def test_query_differs_from_cd_and_binding_constants() -> None:
    assert "ccy=" in AUTHORIZED_QUERY
    assert AUTHORIZED_QUERY != CD_QUERY
    assert f"ccy={BOUND_SETTLEMENT_CCY}" in AUTHORIZED_QUERY
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    assert "MAX_GET_COUNT = 1" in source
    assert "RETRY_COUNT = 0" in source
    assert "spot-borrow-repay-history" in source


def test_empty_body_p1_unknown_single_get(tmp_path: Path) -> None:
    result, store, transport = _run(tmp_path=tmp_path, body=b'{"code":"0","msg":"","data":[]}')
    assert result.actual_get_count == "1"
    assert result.p1_status == "UNKNOWN"
    assert result.row_count == "0"
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert f"ccy={BOUND_SETTLEMENT_CCY}" in transport.calls[0].endpoint
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["P4_STATUS"] == "UNKNOWN"
    assert claims["PRIMARY_PROOF_CREATED"] == "false"
    assert claims["U05_PRIMARY_PROOF_UNCHANGED"] == "true"
    assert claims["RETRY_COUNT"] == "0"
    adjudication = json.loads((store / "p1_adjudication_v1.json").read_text(encoding="utf-8"))
    assert adjudication["U05_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert verify_manifest_sha256_v1(store_root=store) == 0


def test_nonzero_row_still_p1_unknown_kind_set_empty(tmp_path: Path) -> None:
    body = (
        b'{"code":"0","msg":"","data":[{"ccy":"USDC","interest":"0.01","liab":"1.0",'
        b'"totalLiab":"1.0","ts":"1726240000000"}]}'
    )
    result, store, _transport = _run(tmp_path=tmp_path, body=body)
    assert result.p1_status == "UNKNOWN"
    qual = json.loads((store / "p1_offline_qualification_v1.json").read_text(encoding="utf-8"))
    assert int(qual["qualifying_p1_count"]) == 0


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(U05P1FuturesBoundInterestAccruedGetAcquisitionError, match="OWNER_GO"):
        execute_u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            transport=RecordingFakeCanaryTransportV1(),
            persist_as_of=PERSIST_AS_OF,
        )


def test_canonical_pack_relpath_prefix() -> None:
    assert CANONICAL_PACK_RELPATH.startswith("evidence/ops/full_core_u05_p1_futures")
