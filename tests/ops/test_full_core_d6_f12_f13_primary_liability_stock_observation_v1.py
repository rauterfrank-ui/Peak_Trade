"""D6 F12/F13 primary liability-stock observation tests.

One authorized GET /api/v5/account/balance. Empty/zero/missing cannot
INCLUDE or EXCLUDE. Non-zero tokens do not automatically INCLUDE.
No bills GET. No POST.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_primary_liability_stock_observation_v1 import (
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_SURFACE,
    BLOCKER_EMPTY_OR_ZERO,
    BLOCKER_NONZERO_UNPROVEN,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    F12F13PrimaryLiabilityStockObservationError,
    assert_f12_f13_balance_surface_already_selected_v1,
    execute_f12_f13_primary_liability_stock_observation_v1,
    reject_claimed_f12_f13_proof_from_token_shape_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
    GET_ENDPOINTS_PRIVATE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    RecordingFakeCanaryTransportV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1.md"
)
BH_HEADING = "11.2.1.BH FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-13T22:15:00Z"


def _bh_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BH_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BI FULL_CORE_D6_EQ_IDENTITY_AND_F12_F13_LIABILITY_STOCK_KIND_RATIFICATION",
            start,
        )
    ]


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
) -> tuple[object, Path, RecordingFakeCanaryTransportV1]:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(bodies_by_endpoint={ENDPOINT_ACCOUNT_BALANCE: body})
    result = execute_f12_f13_primary_liability_stock_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "obs",
        genesis_store_root=genesis,
        transport=transport,
        observation_as_of=as_of,
    )
    return result, Path(result.store_root), transport


def test_canary_private_allowlist_includes_balance_surface() -> None:
    assert_f12_f13_balance_surface_already_selected_v1()
    assert AUTHORIZED_ENDPOINT in GET_ENDPOINTS_PRIVATE
    assert AUTHORIZED_ENDPOINT == ENDPOINT_ACCOUNT_BALANCE
    assert AUTHORIZED_SURFACE == "GET_/api/v5/account/balance"


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    transport = RecordingFakeCanaryTransportV1(
        bodies_by_endpoint={ENDPOINT_ACCOUNT_BALANCE: _balance_body(liab="")}
    )
    with pytest.raises(F12F13PrimaryLiabilityStockObservationError, match="OWNER_GO_MISMATCH"):
        execute_f12_f13_primary_liability_stock_observation_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            genesis_store_root=genesis,
            transport=transport,
            observation_as_of=_AS_OF,
        )
    assert not (tmp_path / "obs").exists()
    assert transport.calls == []


def test_missing_vault_on_productive_path_does_not_get(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(F12F13PrimaryLiabilityStockObservationError, match="VAULT_FILE_REQUIRED"):
        execute_f12_f13_primary_liability_stock_observation_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            genesis_store_root=genesis,
            vault_file=None,
            transport=None,
            observation_as_of=_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_empty_liab_cannot_include_or_exclude(tmp_path: Path) -> None:
    result, pack, transport = _run(tmp_path=tmp_path, body=_balance_body(liab=""))
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.f13_decision == "REMAIN_UNKNOWN"
    assert result.nonzero_liability_observed == "false"
    assert result.earliest_remaining_d6_blocker == BLOCKER_EMPTY_OR_ZERO
    assert result.get_count == "1"
    assert result.post_count == "0"
    assert len(transport.calls) == 1
    assert transport.calls[0].method == "GET"
    assert transport.calls[0].endpoint == ENDPOINT_ACCOUNT_BALANCE
    forensic = json.loads((pack / "forensic_liability_tokens_v1.json").read_text())
    usdc = forensic["details"][0]["tokens"]
    liab = next(item for item in usdc if item["field"] == "liab")
    assert liab["presence"] == "STRING"
    assert liab["raw_token"] == ""
    assert liab["exact_empty_string"] == "true"
    assert liab["nonzero_string_token"] == "false"
    claims = json.loads((pack / "claims.json").read_text())
    assert claims["F16_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert verify_manifest_sha256_v1(store_root=pack) == 0


def test_zero_string_liab_cannot_include_or_exclude(tmp_path: Path) -> None:
    result, pack, _transport = _run(tmp_path=tmp_path, body=_balance_body(liab="0"))
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.f13_decision == "REMAIN_UNKNOWN"
    assert result.nonzero_liability_observed == "false"
    forensic = json.loads((pack / "forensic_liability_tokens_v1.json").read_text())
    usdc = forensic["details"][0]["tokens"]
    liab = next(item for item in usdc if item["field"] == "liab")
    assert liab["raw_token"] == "0"
    assert liab["exact_zero_string"] == "true"
    assert liab["exact_empty_string"] == "false"


def test_missing_liab_key_is_absent_not_empty(tmp_path: Path) -> None:
    result, pack, _transport = _run(
        tmp_path=tmp_path, body=_balance_body(liab=None, include_liab=False)
    )
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.nonzero_liability_observed == "false"
    forensic = json.loads((pack / "forensic_liability_tokens_v1.json").read_text())
    usdc = forensic["details"][0]["tokens"]
    liab = next(item for item in usdc if item["field"] == "liab")
    assert liab["presence"] == "ABSENT"
    assert liab["raw_token"] == ""
    assert liab["exact_empty_string"] == "false"


def test_nonzero_liab_does_not_include_as_source_kind(tmp_path: Path) -> None:
    result, pack, _transport = _run(tmp_path=tmp_path, body=_balance_body(liab="12.5"))
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.f13_decision == "REMAIN_UNKNOWN"
    assert result.nonzero_liability_observed == "true"
    assert result.earliest_remaining_d6_blocker == BLOCKER_NONZERO_UNPROVEN
    assert result.ratified_source_kinds == "NONE"
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    forensic = json.loads((pack / "forensic_liability_tokens_v1.json").read_text())
    usdc = forensic["details"][0]["tokens"]
    liab = next(item for item in usdc if item["field"] == "liab")
    assert liab["raw_token"] == "12.5"
    assert liab["nonzero_string_token"] == "true"
    claims = json.loads((pack / "claims.json").read_text())
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN"] == "false"
    assert claims["D6_FULLY_CLOSED"] == "false"
    assert claims["D7_AUTHORIZED"] == "false"
    assert claims["MS2_AUTHORIZED"] == "false"


def test_bills_get_is_not_performed(tmp_path: Path) -> None:
    _result, _pack, transport = _run(tmp_path=tmp_path, body=_balance_body(liab=""))
    endpoints = [call.endpoint for call in transport.calls]
    assert endpoints == [ENDPOINT_ACCOUNT_BALANCE]
    assert ENDPOINT_ACCOUNT_BILLS not in endpoints
    assert all(call.method == "GET" for call in transport.calls)


def test_claimed_include_exclude_or_algebra_fail_closes() -> None:
    with pytest.raises(
        F12F13PrimaryLiabilityStockObservationError,
        match="F12_F13_CANNOT_INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND",
    ):
        reject_claimed_f12_f13_proof_from_token_shape_v1(
            claimed_proof="INCLUDE_AS_NECESSARY_EQUITY_STOCK_KIND",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        F12F13PrimaryLiabilityStockObservationError,
        match="F12_F13_CANNOT_EMPTY_LIAB_MEANS_F12_FALSE",
    ):
        reject_claimed_f12_f13_proof_from_token_shape_v1(
            claimed_proof="EMPTY_LIAB_MEANS_F12_FALSE",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        F12F13PrimaryLiabilityStockObservationError,
        match="F12_F13_CANNOT_NONZERO_LIAB_MEANS_EQUITY_STOCK_SOURCE",
    ):
        reject_claimed_f12_f13_proof_from_token_shape_v1(
            claimed_proof="NONZERO_LIAB_MEANS_EQUITY_STOCK_SOURCE",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    reject_claimed_f12_f13_proof_from_token_shape_v1(
        claimed_proof="REMAIN_UNKNOWN_PRIMARY_EVIDENCE_DOES_NOT_CARRY_DECISION",
        fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
    )


def test_canonical_pack_matches_executor() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text())
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["AUTHORIZED_GET_SURFACES"] == AUTHORIZED_SURFACE
    assert claims["GET_COUNT"] == "1"
    assert claims["POST_COUNT"] == "0"
    assert claims["ACCOUNT_MUTATION_PERFORMED"] == "false"
    assert claims["NONZERO_LIABILITY_OBSERVED"] == "false"
    assert claims["RAW_EVIDENCE_SEALED"] == "true"
    assert claims["F12_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F13_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F16_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F17_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F18_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["EARLIEST_REMAINING_D6_BLOCKER"] == BLOCKER_EMPTY_OR_ZERO
    assert claims["HTTP_STATUS"] == "200"
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
    capture = json.loads((CANONICAL_PACK / "raw_http_capture_v1.json").read_text())
    assert capture["payload_sha256"] == hashlib.sha256(raw_body.read_bytes()).hexdigest()
    assert capture["secrets_or_signatures_persisted"] == "false"


def test_runbook_bh_persists_typed_fail_closed_observation() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bh_section = _bh_section()
    assert OWNER_GO in bh_section
    assert (
        "THIS_SLICE=11.2.1.BH.FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION"
        in bh_section
    )
    assert "GET_COUNT=1" in bh_section
    assert "POST_COUNT=0" in bh_section
    assert "NONZERO_LIABILITY_OBSERVED=false" in bh_section
    assert "F12_DECISION=REMAIN_UNKNOWN" in bh_section
    assert "F13_DECISION=REMAIN_UNKNOWN" in bh_section
    assert "F16_DECISION=REMAIN_UNKNOWN" in bh_section
    assert "RATIFIED_SOURCE_KINDS=NONE" in bh_section
    assert "KIND_SET_RESOLVED=false" in bh_section
    assert f"EARLIEST_REMAINING_D6_BLOCKER={BLOCKER_EMPTY_OR_ZERO}" in bh_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in bh_section
    assert "MS2_AUTHORIZED=false" in bh_section
    assert "D6_FULLY_CLOSED=false" in bh_section
    assert "D7_AUTHORIZED=false" in bh_section
    assert "REPEAT_GET_HOPING_FOR_NONZERO_FORBIDDEN=true" in bh_section
    assert "DOCS_TOKEN_FULL_CORE_D6_F12_F13_PRIMARY_LIABILITY_STOCK_OBSERVATION_V1" in spec


def test_raw_body_sealed_before_interpretation(tmp_path: Path) -> None:
    body = _balance_body(liab="")
    _result, pack, _transport = _run(tmp_path=tmp_path, body=body)
    assert (pack / "raw_account_balance_response_body.json").read_bytes() == body
    capture = json.loads((pack / "raw_http_capture_v1.json").read_text())
    assert capture["layer"] == "RAW_PRIMARY_EVIDENCE"
    assert capture["secrets_or_signatures_persisted"] == "false"
    assert "ok-access" not in json.dumps(capture).lower()
    assert "api_secret" not in json.dumps(capture).lower()


def test_standing_pins_and_live_path_dag_unchanged() -> None:
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
        == "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
