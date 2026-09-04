"""Offline and recording-transport tests for delayed-zero persist and P7/P9."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    EMPTY_DATA_IS_ZERO,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL,
    OWNER_GO,
    POST_ALLOWED,
    PROVEN_POS_ID,
    RECORDED_ZERO_OBSERVATION_IDENTITY,
    SECTION_11_14_AUTHORIZED,
    TARGET_INSTRUMENT_ID_VALUE,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.contract_v1 import (
    G12CanonicalDelayedZeroPersistError,
    assert_contract_invariants_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.execute_v1 import (
    run_g12_canonical_delayed_zero_persist_and_observations_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.lineage_bind_v1 import (
    bind_flatten_lineage_v1,
)
from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.verify_local_capture_v1 import (
    verify_local_delayed_zero_capture_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EMPTY_BODY = b'{"code":"0","msg":"","data":[]}'
PENDING_NONEMPTY = (
    b'{"code":"0","msg":"","data":[{"instId":"SUI-USD_UM_XPERP-310404",'
    b'"clOrdId":"ptokxeprod508b7b41508b7b4101","ordType":"limit","state":"live"}]}'
)
RELATED_NONEMPTY = b'{"code":"0","msg":"","data":[{"instId":"BTC-USD_UM_XPERP-999999","pos":"2"}]}'


def test_contract_invariants_remain_fail_closed() -> None:
    assert_contract_invariants_v1()
    assert EMPTY_DATA_IS_ZERO is False
    assert FORENSIC_LOCAL_OPS_LOCAL_IS_NOT_CANONICAL is True
    assert POST_ALLOWED is False
    assert SECTION_11_14_AUTHORIZED is False


def test_local_capture_verifies_against_recorded_identities() -> None:
    verified = verify_local_delayed_zero_capture_v1(repo_root=REPO_ROOT)
    assert verified["P5_SOURCE_LOCAL_CAPTURE_VERIFIED"] is True
    assert verified["P5_POSID"] == PROVEN_POS_ID
    assert verified["DELAYED_ZERO"]["OBSERVATION_IDENTITY"] == RECORDED_ZERO_OBSERVATION_IDENTITY
    assert verified["DELAYED_ZERO"]["TARGET_POSITION_ZERO_WINDOW_PROVEN"] is True
    assert verified["DELAYED_ZERO"]["CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN"] is False
    assert verified["HISTORY"]["HISTORY_IS_NOT_TARGET_POSITION_ZERO_PROVEN"] is True
    assert verified["FORENSIC_LOCAL_IS_NOT_CANONICAL"] is True


def test_flatten_lineage_binds_from_persisted_evidence() -> None:
    lineage = bind_flatten_lineage_v1(repo_root=REPO_ROOT)
    assert lineage.authorized is True
    assert lineage.reduce_only is True
    assert lineage.cl_ord_id.startswith("ptokxeprod")
    assert lineage.instrument_id == TARGET_INSTRUMENT_ID_VALUE
    assert lineage.proven_pos_id == PROVEN_POS_ID
    assert lineage.fill_cl_ord_id == lineage.cl_ord_id
    assert lineage.venue_accepted is True


def test_full_conjunction_empty_p7_p9_does_not_rewrite_from_p5_alone(
    tmp_path: Path,
) -> None:
    transport = RecordingFakeCanaryTransportV1(
        body=EMPTY_BODY,
        bodies_by_endpoint={
            "/api/v5/trade/orders-pending": EMPTY_BODY,
            "/api/v5/account/positions": EMPTY_BODY,
        },
    )
    summary = run_g12_canonical_delayed_zero_persist_and_observations_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path,
        transport=transport,
        persist=True,
    )
    assert summary["P5_CANONICAL_PERSIST"] == "PASS"
    assert summary["P5_DELAYED_TARGET_ZERO"] == "PASS"
    assert summary["P7_PENDING_EMPTY"] == "PASS"
    assert summary["P9_NO_UNEXPECTED_RELATED_NONZERO"] == "PASS"
    assert summary["FULL_G12_CONJUNCTION_CURRENTLY_PROVEN"] is True
    assert summary["CANONICAL_SSOT_TARGET_POSITION_ZERO_PROVEN_FROM_P5_ALONE"] is False
    assert summary["TOTAL_NEW_HTTP_GET_COUNT"] == 2
    assert summary["TOTAL_WRITE_COUNT"] == 0
    assert summary["POST_USED"] is False
    assert len(transport.calls) == 2
    assert transport.calls[0].endpoint == "/api/v5/trade/orders-pending"
    assert transport.calls[1].endpoint == "/api/v5/account/positions"
    assert transport.calls[0].method == "GET"
    pack = Path(summary["EVIDENCE_PACK"])
    assert (pack / "GET_HISTORY_POSID.sanitized.json").is_file()
    assert (pack / "GET_DELAYED_POSID_ZERO.sanitized.json").is_file()
    assert (pack / "GET_ORDERS_PENDING.sanitized.json").is_file()
    assert (pack / "GET_ACCOUNT_POSITIONS_UNFILTERED.sanitized.json").is_file()
    assert (pack / "MANIFEST.sha256").is_file()


def test_pending_nonempty_fails_p7_and_keeps_g12_open(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        body=EMPTY_BODY,
        bodies_by_endpoint={
            "/api/v5/trade/orders-pending": PENDING_NONEMPTY,
            "/api/v5/account/positions": EMPTY_BODY,
        },
    )
    summary = run_g12_canonical_delayed_zero_persist_and_observations_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path,
        transport=transport,
        persist=False,
    )
    assert summary["P7_PENDING_EMPTY"] == "FAIL"
    assert summary["FULL_G12_CONJUNCTION_CURRENTLY_PROVEN"] is False
    assert summary["LIVE_FLATTEN_PROVABILITY_PROVEN"] is False
    assert summary["G12_STATUS"] == "OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN"
    assert summary["EXACT_REMAINING_G12_BLOCKER"] == "P7_PENDING_EMPTY"


def test_related_nonzero_fails_p9(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        body=EMPTY_BODY,
        bodies_by_endpoint={
            "/api/v5/trade/orders-pending": EMPTY_BODY,
            "/api/v5/account/positions": RELATED_NONEMPTY,
        },
    )
    summary = run_g12_canonical_delayed_zero_persist_and_observations_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path,
        transport=transport,
        persist=False,
    )
    assert summary["P9_NO_UNEXPECTED_RELATED_NONZERO"] == "FAIL"
    assert summary["FULL_G12_CONJUNCTION_CURRENTLY_PROVEN"] is False


def test_wrong_owner_go_rejected(tmp_path: Path) -> None:
    with pytest.raises(G12CanonicalDelayedZeroPersistError, match="OWNER_GO_MISMATCH"):
        run_g12_canonical_delayed_zero_persist_and_observations_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            transport=RecordingFakeCanaryTransportV1(),
            persist=False,
        )


def test_auth_failure_hard_stops_without_p9(tmp_path: Path) -> None:
    transport = RecordingFakeCanaryTransportV1(
        status_code=401,
        body=b'{"code":"50110","msg":"ip","data":[]}',
    )
    with pytest.raises(G12CanonicalDelayedZeroPersistError, match="AUTH_OR_TRANSPORT_FAILURE"):
        run_g12_canonical_delayed_zero_persist_and_observations_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path,
            transport=transport,
            persist=False,
        )
    assert len(transport.calls) == 1
