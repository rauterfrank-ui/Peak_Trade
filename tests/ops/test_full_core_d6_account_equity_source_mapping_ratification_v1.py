"""D6 account-equity source-mapping ratification tests. Sealed input only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    STATUS_RATIFIED_NON_SOURCE,
    STATUS_RATIFIED_OTHER_DOMAIN,
    STATUS_RATIFIED_SOURCE_KIND,
    STATUS_UNRESOLVED_AMBIGUOUS,
    STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY,
    AccountEquitySourceMappingRatificationError,
    assert_eq_is_not_source_authority_v1,
    execute_account_equity_source_mapping_ratification_v1,
    reject_unratified_equity_stock_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION_WORKPACKAGE_V1.md"
)
BE_HEADING = "11.2.1.BE FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION"
BD_HEADING = "11.2.1.BD FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION"
SEALED_PACK = REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
CANONICAL_S6_PACK = REPO_ROOT / CANONICAL_S6_PACK_RELPATH
CANONICAL_MAPPING_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_d6_account_equity_source_mapping_ratification_v1/2026-09-13T192000Z"
)
_AS_OF = "2026-09-13T19:20:00Z"


def _be_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BE_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BF FULL_CORE_D6_SOURCE_MAPPING_AND_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION",
            start,
        )
    ]


def test_sealed_input_manifests_verify() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_S6_PACK) == 0


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(AccountEquitySourceMappingRatificationError, match="OWNER_GO_MISMATCH"):
        execute_account_equity_source_mapping_ratification_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_s6_pack=CANONICAL_S6_PACK,
            sealed_observation_pack=SEALED_PACK,
            evidence_root=tmp_path / "mapping",
            ratification_as_of=_AS_OF,
        )
    assert not (tmp_path / "mapping" / "2026-09-13T192000Z").exists()


def test_unratified_source_kind_guard_fail_closes() -> None:
    with pytest.raises(
        AccountEquitySourceMappingRatificationError, match="UNRATIFIED_SOURCE_KIND_FORBIDDEN"
    ):
        reject_unratified_equity_stock_source_kind_v1(
            event_kind="U05_LIABILITY",
            mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
        )
    with pytest.raises(AccountEquitySourceMappingRatificationError, match="EQ_CANNOT_BE"):
        assert_eq_is_not_source_authority_v1(
            field_name="eq",
            ratification_status=STATUS_RATIFIED_SOURCE_KIND,
        )
    reject_unratified_equity_stock_source_kind_v1(
        event_kind="NONE",
        mapped_numeric_effect="NOT_MAPPED_FAIL_CLOSED",
    )
    assert_eq_is_not_source_authority_v1(
        field_name="eq",
        ratification_status=STATUS_RATIFIED_NON_SOURCE,
    )


def test_ratifies_unique_non_source_and_other_domain_without_kind_set(
    tmp_path: Path,
) -> None:
    result = execute_account_equity_source_mapping_ratification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_s6_pack=CANONICAL_S6_PACK,
        sealed_observation_pack=SEALED_PACK,
        evidence_root=tmp_path / "mapping",
        ratification_as_of=_AS_OF,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.ratification_candidate_count == "136"
    assert result.ratified_source_kinds == "NONE"
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.mapping_persisted == "true"
    assert result.mapping_coverage_status == "PARTIAL_FAIL_CLOSED_NO_RATIFIED_SOURCE_KIND"
    assert result.raw_eq_source_authority == "false"
    assert result.retention_coverage_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.ordering_completeness_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.complete_classified_event_stream_proven == "false"
    assert result.u05_kind_decision == "REMAIN_UNKNOWN"
    assert result.u06_kind_decision == "REMAIN_UNKNOWN"
    assert result.residual_kind_decision == "REMAIN_UNKNOWN"
    assert result.f12_f13_f16_f17_f18_status == "UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN"
    assert result.new_network_get_count == "0"
    assert result.network_post_performed == "false"
    assert result.ms2_authorized == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert "details.eq" in result.ratified_non_source_fields
    assert "account.imr" in result.ratified_non_source_fields
    assert "account.ordFroz" in result.ratified_other_domain_fields
    assert "details.ordFrozen" in result.ratified_other_domain_fields
    assert "details.liab" in result.unresolved_fields
    assert "bills.fee" in result.unresolved_fields
    assert "bills.type" in result.unresolved_fields
    pack = Path(result.store_root)
    records = json.loads((pack / "source_mapping_records_v1.json").read_text())
    by_path = {row["field_path"]: row for row in records["records"]}
    assert by_path["details.eq"]["ratification_status"] == STATUS_RATIFIED_NON_SOURCE
    assert by_path["details.eq"]["source_role"] == "FRESH_EQ_RECONCILIATION_TARGET_NOT_SOURCE"
    assert by_path["details.eq"]["event_kind"] == "NONE"
    assert by_path["account.availEq"]["ratification_status"] == STATUS_RATIFIED_NON_SOURCE
    assert by_path["account.imr"]["ratification_status"] == STATUS_RATIFIED_NON_SOURCE
    assert "NOT_EQUITY_STOCK_SOURCE" in by_path["account.imr"]["economic_semantic"]
    assert by_path["account.ordFroz"]["ratification_status"] == STATUS_RATIFIED_OTHER_DOMAIN
    assert by_path["details.upl"]["ratification_status"] == STATUS_RATIFIED_NON_SOURCE
    assert by_path["details.liab"]["ratification_status"] == STATUS_UNRESOLVED_AMBIGUOUS
    assert by_path["bills.fee"]["ratification_status"] == STATUS_UNRESOLVED_AMBIGUOUS
    assert by_path["bills.type"]["ratification_status"] == STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY
    assert by_path["details.interest"]["ratification_status"] == (
        STATUS_UNRESOLVED_INSUFFICIENT_AUTHORITY
    )
    statuses = {row["ratification_status"] for row in records["records"]}
    assert STATUS_RATIFIED_SOURCE_KIND not in statuses
    assert all(row["event_kind"] == "NONE" for row in records["records"])
    assert all(
        row["mapped_numeric_effect"] == "NOT_MAPPED_FAIL_CLOSED" for row in records["records"]
    )
    assert verify_manifest_sha256_v1(store_root=pack) == 0
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True


def test_canonical_mapping_pack_matches_ratification() -> None:
    claims = json.loads((CANONICAL_MAPPING_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["GENESIS_AS_OF"] == EXPECTED_GENESIS_AS_OF
    assert claims["RATIFICATION_AS_OF"] == _AS_OF
    assert claims["RATIFICATION_CANDIDATE_COUNT"] == "136"
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["MAPPING_PERSISTED"] == "true"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["U05_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["U06_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["RESIDUAL_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F12_STATUS"] == "UNKNOWN"
    assert claims["F18_STATUS"] == "UNKNOWN"
    assert claims["RETENTION_COVERAGE_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["ORDERING_COMPLETENESS_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["MS2_AUTHORIZED"] == "false"
    assert claims["D6_FULLY_CLOSED"] == "false"
    assert claims["D7_AUTHORIZED"] == "false"
    assert claims["NEW_NETWORK_GET_COUNT"] == "0"
    assert "details.eq" in claims["RATIFIED_NON_SOURCE_FIELDS"]
    assert "account.ordFroz" in claims["RATIFIED_OTHER_DOMAIN_FIELDS"]
    assert "details.liab" in claims["UNRESOLVED_FIELDS"]
    assert verify_manifest_sha256_v1(store_root=CANONICAL_MAPPING_PACK) == 0
    expected: dict[str, str] = {}
    for line in (
        (CANONICAL_MAPPING_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_MAPPING_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_MAPPING_PACK / name).read_bytes()).hexdigest() == digest


def test_runbook_be_persists_partial_mapping() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    be_section = _be_section()
    assert "OWNER_GO=OWNER_GO_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION_WORKPACKAGE_V1" in (
        be_section
    )
    assert "THIS_SLICE=11.2.1.BE.FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION" in (
        be_section
    )
    assert "MAPPING_PERSISTED=true" in be_section
    assert "KIND_SET_RESOLVED=false" in be_section
    assert "RATIFIED_SOURCE_KINDS=NONE" in be_section
    assert "U05_KIND_DECISION=REMAIN_UNKNOWN" in be_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in be_section
    assert "MS2_AUTHORIZED=false" in be_section
    assert "D6_FULLY_CLOSED=false" in be_section
    assert "D7_AUTHORIZED=false" in be_section
    assert "RETENTION_COVERAGE_STATUS=FAIL_CLOSED_NOT_PROVEN" in be_section
    assert "DOCS_TOKEN_FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION_WORKPACKAGE_V1" in (
        spec
    )
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION_WORKPACKAGE_V1.md" in mot
    assert "§11.2.1.BE FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION" in mot
    runbook = RUNBOOK.read_text(encoding="utf-8")
    bd_start = runbook.index(BD_HEADING)
    bd_only = runbook[bd_start : runbook.index(BE_HEADING, bd_start)]
    assert "MAPPING_PERSISTED=false" in bd_only
    assert "MASTER_V2_UNCHANGED=true" in be_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in be_section
    assert "BULL_BEAR_STATE_SWITCH_UNCHANGED=true" in be_section
    assert "CONSTRUCT_LIVE_EXECUTION_PORT_V1=FORBIDDEN_IN_CAP_11_1" in be_section
