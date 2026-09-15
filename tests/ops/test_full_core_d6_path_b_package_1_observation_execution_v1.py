"""PACKAGE_1 Observation S1-S5 execution tests. No mapping. No POST."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXECUTION_READY,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    OBSERVATION_EXECUTED,
    OBSERVATION_EXECUTION_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_execution_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    Package1ObservationExecutionError,
    execute_package_1_observation_s1_s5_v1,
    preflight_package_1_observation_s0_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
    ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_SUBTYPES,
    GET_ENDPOINTS_PRIVATE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_PATH_B_PACKAGE_1_OBSERVATION_EXECUTION_V1.md"
BC_HEADING = "11.2.1.BC FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
_OBS_AS_OF = "2026-09-13T18:15:00Z"
CANONICAL_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_d6_path_b_package_1_observation_execution_v1/2026-09-13T182521Z"
)


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _config_body(uid: str, settle: str) -> bytes:
    return (
        '{"code":"0","msg":"","data":[{"uid":"'
        + uid
        + '","mainUid":"'
        + uid
        + '","acctLv":"2","settleCcy":"'
        + settle
        + '","posMode":"net_mode"}]}'
    ).encode("utf-8")


def _bodies(uid: str, settle: str) -> dict[str, bytes]:
    return {
        ENDPOINT_ACCOUNT_CONFIG: _config_body(uid, settle),
        ENDPOINT_ACCOUNT_BALANCE: (
            b'{"code":"0","msg":"","data":[{"adjEq":"1","details":'
            b'[{"ccy":"USDC","eq":"1.25","cashBal":"1.25","liab":"0",'
            b'"crossLiab":"0","isoLiab":"0","interest":"0","upl":"0",'
            b'"uplLiab":"0","uTime":"1726240000000"}]}]}'
        ),
        ENDPOINT_ACCOUNT_SUBTYPES: b'{"code":"0","msg":"","data":[]}',
        ENDPOINT_ACCOUNT_BILLS: (
            b'{"code":"0","msg":"","data":[{"billId":"b1","ts":"1","type":"2"},'
            b'{"billId":"b2","ts":"2","type":"2"}]}'
        ),
        ENDPOINT_ACCOUNT_BILLS_ARCHIVE: (
            b'{"code":"0","msg":"","data":[{"billId":"b2","ts":"2","type":"2"},'
            b'{"billId":"b3","ts":"3","type":"2"}]}'
        ),
    }


def _transport_for(genesis: Path) -> RecordingFakeCanaryTransportV1:
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis)
    return RecordingFakeCanaryTransportV1(
        bodies_by_endpoint=_bodies(d4.bound_account_identity, d4.settlement_currency)
    )


def _bc_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BC_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BD FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION", start
        )
    ]


def test_canary_private_allowlist_includes_package_1_surfaces() -> None:
    assert ENDPOINT_ACCOUNT_CONFIG in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ACCOUNT_BALANCE in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ACCOUNT_SUBTYPES in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ACCOUNT_BILLS in GET_ENDPOINTS_PRIVATE
    assert ENDPOINT_ACCOUNT_BILLS_ARCHIVE in GET_ENDPOINTS_PRIVATE


def test_preflight_accepts_canonical_genesis_store() -> None:
    root = preflight_package_1_observation_s0_v1(origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA)
    assert root.resolve() == GENESIS_STORE.resolve()


def test_wrong_owner_go_fail_closes_before_network(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    transport = _transport_for(genesis)
    with pytest.raises(Package1ObservationExecutionError, match="OWNER_GO_MISMATCH"):
        execute_package_1_observation_s1_s5_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            genesis_store_root=genesis,
            transport=transport,
            observation_as_of=_OBS_AS_OF,
        )
    assert transport.calls == []


def test_uid_mismatch_fail_closes_without_minting(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint=_bodies("900199001990019900", "USDC")
    )
    with pytest.raises(Package1ObservationExecutionError) as err:
        execute_package_1_observation_s1_s5_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            genesis_store_root=genesis,
            transport=transport,
            observation_as_of=_OBS_AS_OF,
        )
    assert "D4_OBSERVATION_MISMATCH_FAIL_CLOSED" in str(err.value) or "D4_CORROBORATION" in str(
        err.value
    )
    assert [call.method for call in transport.calls] == ["GET"]
    assert [call.endpoint for call in transport.calls] == [ENDPOINT_ACCOUNT_CONFIG]
    assert not (tmp_path / "pack" / "2026-09-13T181500Z").exists()


def test_s1_s5_persists_raw_pack_without_mapping_or_post(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    transport = _transport_for(genesis)
    result = execute_package_1_observation_s1_s5_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        genesis_store_root=genesis,
        transport=transport,
        observation_as_of=_OBS_AS_OF,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.s1_account_config_get == "true"
    assert result.s2_account_balance_get == "true"
    assert result.s3_account_subtypes_get == "true"
    assert result.s4_account_bills_get == "true"
    assert result.s4_account_bills_archive_get == "true"
    assert result.authorized_get_surface_count == "5"
    assert result.unauthorized_get_surface_count == "0"
    assert result.network_post_performed == "false"
    assert result.d4_identity_minted == "false"
    assert result.raw_eq_source_authority == "false"
    assert result.d4_corroboration_result == (
        "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"
    )
    assert result.bills_archive_overlap_status == "PARTIAL_BILL_ID_OVERLAP"
    assert result.retention_coverage_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.ordering_completeness_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.raw_evidence_sealed == "true"
    assert result.kind_set_resolved == "false"
    assert result.mapping_persisted == "false"
    assert result.mapping_s6_executed == "false"
    assert result.ms2_authorized == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    pack = Path(result.store_root)
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["S6_EXECUTED"] == "false"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["D4_IDENTITY_MINTED"] == "false"
    subtypes = json.loads((pack / "s3_account_subtypes_observation_v1.json").read_text())
    assert subtypes["row_count"] == "0"
    assert subtypes["empty_result_proves_zero_events"] == "false"
    balance = json.loads((pack / "s2_account_balance_observation_v1.json").read_text())
    assert balance["raw_eq_source_authority"] == "false"
    assert [call.method for call in transport.calls] == ["GET"] * 5
    assert [call.endpoint for call in transport.calls] == [
        ENDPOINT_ACCOUNT_CONFIG,
        ENDPOINT_ACCOUNT_BALANCE,
        ENDPOINT_ACCOUNT_SUBTYPES,
        ENDPOINT_ACCOUNT_BILLS,
        ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
    ]
    assert not any(call.method == "POST" for call in transport.calls)
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert EXECUTION_READY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is False


def test_canonical_productive_pack_sealed_without_s6() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["GENESIS_AS_OF"] == EXPECTED_GENESIS_AS_OF
    assert claims["OBSERVATION_AS_OF"] == "2026-09-13T18:25:21Z"
    assert claims["AUTHORIZED_GET_SURFACE_COUNT"] == "5"
    assert claims["UNAUTHORIZED_GET_SURFACE_COUNT"] == "0"
    assert claims["NETWORK_POST_PERFORMED"] == "false"
    assert claims["D4_IDENTITY_MINTED"] == "false"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["S6_EXECUTED"] == "false"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["MAPPING_PERSISTED"] == "false"
    assert claims["MS2_AUTHORIZED"] == "false"
    assert claims["D6_FULLY_CLOSED"] == "false"
    assert claims["D7_AUTHORIZED"] == "false"
    assert claims["RAW_EVIDENCE_SEALED"] == "true"
    assert claims["RETENTION_COVERAGE_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["ORDERING_COMPLETENESS_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["EMPTY_RESULT_PROVES_ZERO_EVENTS"] == "false"
    assert claims["PAGINATION_EXHAUSTION_PROVES_COMPLETENESS"] == "false"
    manifest = CANONICAL_PACK / "MANIFEST.sha256"
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_PACK / name).read_bytes()).hexdigest() == digest


def test_runbook_bc_persists_observation_without_s6() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bc_section = _bc_section()
    assert "OWNER_GO=OWNER_GO_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION_WORKPACKAGE_V1" in (
        bc_section
    )
    assert "THIS_SLICE=11.2.1.BC.FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION" in (
        bc_section
    )
    assert "AUTHORIZED_GET_SURFACE_COUNT=5" in bc_section
    assert "NETWORK_POST_PERFORMED=false" in bc_section
    assert "D4_IDENTITY_MINTED=false" in bc_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in bc_section
    assert "S6_EXECUTED=false" in bc_section
    assert "KIND_SET_RESOLVED=false" in bc_section
    assert "MS2_AUTHORIZED=false" in bc_section
    assert "D7_AUTHORIZED=false" in bc_section
    assert "DOCS_TOKEN_FULL_CORE_D6_PATH_B_PACKAGE_1_OBSERVATION_EXECUTION_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_PACKAGE_1_OBSERVATION_EXECUTION_V1.md" in mot
    assert "§11.2.1.BC FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION" in mot
