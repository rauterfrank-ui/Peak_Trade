"""GATE_A independently attested productive nonzero liability-stock tests.

Exactly one GET /api/v5/account/balance. Empty/zero/absent is not
absence. Nonzero does not INCLUDE. No bills. No POST. No retry.
"""

from __future__ import annotations

import hashlib
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
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    GATE_A_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.gate_a_independently_attested_productive_nonzero_liability_stock_v1 import (
    AUTHORIZED_SURFACE,
    BASIS_NONQUALIFYING,
    BASIS_NONZERO_REOPEN,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREREQUISITE,
    STATUS_EXECUTED_NONQUALIFYING,
    STATUS_EXECUTED_QUALIFYING,
    GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError,
    execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
BX_HEADING = (
    "11.2.1.BX FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK"
)
_AS_OF = "2026-09-14T20:05:00Z"


def _bx_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BX_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _balance_body(*, liab: str | None, include_liab: bool = True) -> bytes:
    liab_json = ""
    if include_liab:
        liab_json = f',"liab":"{liab}"'
    return (
        '{"code":"0","msg":"","data":[{"borrowFroz":"","details":'
        '[{"ccy":"USDC","eq":"1.25","cashBal":"1.25"'
        + liab_json
        + ',"crossLiab":"","isoLiab":"","interest":"0","upl":"0",'
        '"uplLiab":"0","uTime":"1726240000000"},'
        '{"ccy":"EUR","eq":"2","cashBal":"2","liab":"0","crossLiab":"0",'
        '"isoLiab":"0","interest":"0","upl":"0","uplLiab":"0",'
        '"uTime":"1726240000000"}]}]}'
    ).encode("utf-8")


def _run(
    *,
    tmp_path: Path,
    body: bytes,
    as_of: str = _AS_OF,
    status_code: int = 200,
) -> tuple[object, Path, RecordingFakeCanaryTransportV1]:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        status_code=status_code,
        bodies_by_endpoint={ENDPOINT_ACCOUNT_BALANCE: body},
    )
    result = execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1(
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
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={ENDPOINT_ACCOUNT_BALANCE: _balance_body(liab="")}
    )
    with pytest.raises(
        GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            transport=transport,
            persist_as_of=_AS_OF,
        )
    assert not (tmp_path / "obs").exists()
    assert transport.calls == []


def test_missing_vault_on_productive_path_does_not_get(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(
        GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError,
        match="VAULT_UNAVAILABLE",
    ):
        execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            vault_file=tmp_path / "missing_vault.json",
            transport=None,
            persist_as_of=_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_empty_liab_is_executed_nonqualifying_not_exclude(tmp_path: Path) -> None:
    result, pack, transport = _run(tmp_path=tmp_path, body=_balance_body(liab=""))
    assert result.gate_a_execution_status == STATUS_EXECUTED_NONQUALIFYING
    assert result.gate_a_productive_nonzero_liability_proven == "false"
    assert result.u05_reopened_decision_capable == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.u05_decision_basis == BASIS_NONQUALIFYING
    assert result.u06_decision == DECISION_REMAIN_UNKNOWN
    assert result.actual_get_count == "1"
    assert result.post_count == "0"
    assert result.http_status == "200"
    assert result.venue_code == "0"
    assert [call.endpoint for call in transport.calls] == [ENDPOINT_ACCOUNT_BALANCE]
    assert all(call.method == "GET" for call in transport.calls)
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["GATE_A_EXECUTED"] == "true"
    assert claims["GATE_B_EXECUTED"] == "false"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0


def test_zero_string_liab_is_executed_nonqualifying(tmp_path: Path) -> None:
    result, _pack, _transport = _run(tmp_path=tmp_path, body=_balance_body(liab="0"))
    assert result.gate_a_execution_status == STATUS_EXECUTED_NONQUALIFYING
    assert result.u05_reopened_decision_capable == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN


def test_missing_liab_key_is_executed_nonqualifying(tmp_path: Path) -> None:
    result, _pack, _transport = _run(
        tmp_path=tmp_path, body=_balance_body(liab=None, include_liab=False)
    )
    assert result.gate_a_execution_status == STATUS_EXECUTED_NONQUALIFYING
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN


def test_nonzero_liab_reopens_u05_but_does_not_include(tmp_path: Path) -> None:
    result, pack, _transport = _run(tmp_path=tmp_path, body=_balance_body(liab="1.5"))
    assert result.gate_a_execution_status == STATUS_EXECUTED_QUALIFYING
    assert result.gate_a_productive_nonzero_liability_proven == "true"
    assert result.u05_reopened_decision_capable == "true"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.u05_decision_basis == BASIS_NONZERO_REOPEN
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["U05_REOPENED_DECISION_CAPABLE"] == "true"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert "INCLUDE" not in claims["U05_DECISION_AFTER"]
    qualification = json.loads((pack / "gate_a_qualification_v1.json").read_text(encoding="utf-8"))
    assert qualification["get_alone_may_include"] == "false"
    assert qualification["get_alone_may_exclude"] == "false"
    assert qualification["source_semantics_proven"] == "false"
    assert qualification["embedding_proven"] == "false"
    assert qualification["prerequisite"] == PREREQUISITE
    assert qualification["gate_a_id"] == GATE_A_ID


def test_bills_get_is_not_performed(tmp_path: Path) -> None:
    _result, _pack, transport = _run(tmp_path=tmp_path, body=_balance_body(liab=""))
    endpoints = [call.endpoint for call in transport.calls]
    assert ENDPOINT_ACCOUNT_BILLS not in endpoints
    assert endpoints == [ENDPOINT_ACCOUNT_BALANCE]


def test_http_error_hard_stops_without_persist_or_retry(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        status_code=401,
        bodies_by_endpoint={ENDPOINT_ACCOUNT_BALANCE: b'{"code":"50111","msg":"Invalid"}'},
    )
    with pytest.raises(
        GateAIndependentlyAttestedProductiveNonzeroLiabilityStockError,
        match="GATE_A_BALANCE_GET_FAILED:HTTP_STATUS:401",
    ):
        execute_gate_a_independently_attested_productive_nonzero_liability_stock_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            transport=transport,
            persist_as_of=_AS_OF,
        )
    assert not (tmp_path / "obs").exists()
    assert len(transport.calls) == 1


def test_raw_body_sealed_without_secrets(tmp_path: Path) -> None:
    body = _balance_body(liab="")
    _result, pack, _transport = _run(tmp_path=tmp_path, body=body)
    assert (pack / "raw_account_balance_response_body.json").read_bytes() == body
    capture = json.loads((pack / "raw_http_capture_v1.json").read_text(encoding="utf-8"))
    blob = json.dumps(capture).lower()
    assert capture["layer"] == "RAW_PRIMARY_EVIDENCE"
    assert capture["secrets_or_signatures_persisted"] == "false"
    assert "ok-access" not in blob
    assert "api_secret" not in blob
    assert "passphrase" not in blob


def test_canonical_pack_matches_executor() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["AUTHORIZED_GET_SURFACES"] == AUTHORIZED_SURFACE
    assert claims["AUTHORIZED_GET_COUNT"] == "1"
    assert claims["ACTUAL_GET_COUNT"] == "1"
    assert claims["POST_COUNT"] == "0"
    assert claims["GATE_A_EXECUTED"] == "true"
    assert claims["GATE_B_EXECUTED"] == "false"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_CLASS_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["RATIFIED_CLASSIFIED_EVENT_KIND_SET_STATUS"] == "EMPTY_FAIL_CLOSED"
    assert claims["ACCOUNT_BILLS_CURRENT_NONCANONICAL"] == "true"
    assert claims["MS2_AUTHORIZED"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["RECONSTRUCTION_IMPLEMENTED"] == "false"
    assert claims["STANDING_FULL_CORE_DAG_PIN"] == EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
    assert claims["HTTP_STATUS"] == "200"
    assert claims["VENUE_CODE"] == "0"
    assert claims["GATE_A_EXECUTION_STATUS"] in {
        STATUS_EXECUTED_QUALIFYING,
        STATUS_EXECUTED_NONQUALIFYING,
    }
    if claims["GATE_A_EXECUTION_STATUS"] == STATUS_EXECUTED_QUALIFYING:
        assert claims["GATE_A_PRODUCTIVE_NONZERO_LIABILITY_PROVEN"] == "true"
        assert claims["U05_REOPENED_DECISION_CAPABLE"] == "true"
        assert claims["U05_DECISION_BASIS"] == BASIS_NONZERO_REOPEN
    else:
        assert claims["GATE_A_PRODUCTIVE_NONZERO_LIABILITY_PROVEN"] == "false"
        assert claims["U05_REOPENED_DECISION_CAPABLE"] == "false"
        assert claims["U05_DECISION_BASIS"] == BASIS_NONQUALIFYING
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
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
    raw_body = CANONICAL_PACK / "raw_account_balance_response_body.json"
    capture = json.loads((CANONICAL_PACK / "raw_http_capture_v1.json").read_text(encoding="utf-8"))
    assert capture["payload_sha256"] == hashlib.sha256(raw_body.read_bytes()).hexdigest()
    assert capture["secrets_or_signatures_persisted"] == "false"


def test_runbook_bx_persists_gate_a_execution() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bx_section = _bx_section()
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert OWNER_GO in bx_section
    assert (
        "THIS_SLICE=11.2.1.BX.FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK"
        in bx_section
    )
    assert "AUTHORIZED_GET_COUNT=1" in bx_section
    assert "ACTUAL_GET_COUNT=1" in bx_section
    assert "POST_COUNT=0" in bx_section
    assert f"GATE_A_EXECUTION_STATUS={claims['GATE_A_EXECUTION_STATUS']}" in bx_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in bx_section
    assert "U06_DECISION=REMAIN_UNKNOWN" in bx_section
    assert "GATE_B_EXECUTED=false" in bx_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bx_section
    assert "MS2_AUTHORIZED=false" in bx_section
    assert "D6_FULLY_CLOSED=false" in bx_section
    assert "RECONSTRUCTION_IMPLEMENTED=false" in bx_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in bx_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BX" in bx_section
    assert (
        "DOCS_TOKEN_FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK_V1"
        in spec
    )
    assert (
        "FULL_CORE_OPTION_D_GATE_A_INDEPENDENTLY_ATTESTED_PRODUCTIVE_NONZERO_LIABILITY_STOCK_V1.md"
        in mot
    )
    assert BX_HEADING in mot
    assert "11.2.1.BX" in atlas
    assert "gate_a_independently_attested_productive_nonzero_liability_stock_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False


def test_standing_pins_unchanged() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
