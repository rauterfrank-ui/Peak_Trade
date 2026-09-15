"""PACKAGE_1 S6 mapping/classification tests. Sealed input only. No GET/POST."""

from __future__ import annotations

import hashlib
import json
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
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    CLASSIFICATION_STATUS_CLASSIFIED,
    CLASSIFICATION_STATUS_UNCLASSIFIED,
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    Package1S6MappingClassificationError,
    execute_package_1_s6_mapping_classification_v1,
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION_V1.md"
)
BD_HEADING = "11.2.1.BD FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION"
BC_HEADING = "11.2.1.BC FULL_CORE_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
SEALED_PACK = REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
CANONICAL_S6_PACK = (
    REPO_ROOT
    / "evidence/ops/full_core_d6_path_b_package_1_s6_mapping_classification_v1/2026-09-13T184000Z"
)
_S6_AS_OF = "2026-09-13T18:40:00Z"


def _bd_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BD_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BE FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION", start
        )
    ]


def test_sealed_observation_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=GENESIS_STORE) == 0


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(Package1S6MappingClassificationError, match="OWNER_GO_MISMATCH"):
        execute_package_1_s6_mapping_classification_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_observation_pack=SEALED_PACK,
            genesis_store_root=GENESIS_STORE,
            evidence_root=tmp_path / "s6",
            mapping_as_of=_S6_AS_OF,
        )
    assert not (tmp_path / "s6" / "2026-09-13T184000Z").exists()


def test_tampered_manifest_fail_closes(tmp_path: Path) -> None:
    cloned = tmp_path / "tampered"
    cloned.mkdir()
    for path in SEALED_PACK.iterdir():
        if path.is_file():
            (cloned / path.name).write_bytes(path.read_bytes())
    claims = cloned / "claims.json"
    claims.write_text(
        claims.read_text(encoding="utf-8").replace("false", "true", 1), encoding="utf-8"
    )
    with pytest.raises(Package1S6MappingClassificationError, match="MANIFEST_DIGEST_MISMATCH"):
        execute_package_1_s6_mapping_classification_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_observation_pack=cloned,
            genesis_store_root=GENESIS_STORE,
            evidence_root=tmp_path / "s6",
            mapping_as_of=_S6_AS_OF,
        )


def test_s6_classifies_sealed_pack_fail_closed_without_kind_resolution(
    tmp_path: Path,
) -> None:
    result = execute_package_1_s6_mapping_classification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_observation_pack=SEALED_PACK,
        genesis_store_root=GENESIS_STORE,
        evidence_root=tmp_path / "s6",
        mapping_as_of=_S6_AS_OF,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.s6_executed == "true"
    assert result.sealed_input_only == "true"
    assert result.manifest_verify_rc == "0"
    assert result.observed_kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.mapping_persisted == "false"
    assert result.mapping_coverage_status == "FAIL_CLOSED_NO_RATIFIED_KIND"
    assert result.classified_bill_row_count == "58"
    assert result.retention_coverage_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.ordering_completeness_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.d4_identity_minted == "false"
    assert result.raw_eq_source_authority == "false"
    assert result.new_network_get_count == "0"
    assert result.network_post_performed == "false"
    assert result.ms2_authorized == "false"
    assert result.ms2_executed == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND" in result.unresolved_kinds_or_ambiguities
    pack = Path(result.store_root)
    claims = json.loads((pack / "claims.json").read_text(encoding="utf-8"))
    assert claims["S6_EXECUTED"] == "true"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["MAPPING_PERSISTED"] == "false"
    assert claims["D4_IDENTITY_MINTED"] == "false"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["NEW_NETWORK_GET_COUNT"] == "0"
    assert claims["OBSERVED_VENUE_TYPE_TOKEN_SET"] == "1,2,27,8"
    assert claims["PARTIAL_OVERLAP_IS_NOT_RETENTION_COMPLETENESS"] == "true"
    records = json.loads((pack / "s6_classification_records_v1.json").read_text())
    assert records["classified_bill_row_count"] == "58"
    statuses = {row["classification_status"] for row in records["records"]}
    assert CLASSIFICATION_STATUS_CLASSIFIED not in statuses
    assert statuses <= {CLASSIFICATION_STATUS_UNCLASSIFIED}
    effects = {row["mapped_numeric_effect"] for row in records["records"]}
    assert effects == {"NOT_MAPPED_FAIL_CLOSED"}
    assert all(
        row["reconstruction_eligibility"] == "INVALID_FAIL_CLOSED" for row in records["records"]
    )
    assert all(
        row["kind_ratification"] == "FORBIDDEN_NO_RATIFIED_KIND" for row in records["records"]
    )
    subtypes = json.loads((pack / "s6_surface_mapping_v1.json").read_text())["subtypes"]
    assert subtypes["observed_catalog_type_count"] == "32"
    assert subtypes["query_result_is_not_kind_completeness"] == "true"
    balance = json.loads((pack / "s6_surface_mapping_v1.json").read_text())["balance"]
    assert balance["raw_eq_source_authority"] == "false"
    assert balance["eq_role"] == "RECONCILIATION_OR_EMBEDDING_TARGET_ONLY"
    embedding = json.loads((pack / "s6_embedding_facts_v1.json").read_text())
    fact_ids = [fact["fact_id"] for fact in embedding["facts"]]
    assert fact_ids == [
        "F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        "F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
        "F16_FEE_ALREADY_EMBEDDED_IN_EQ",
        "F17_FEE_SEPARATE_ACCOUNT_DELTA",
        "F18_FEE_RECONCILIATION_ONLY",
    ]
    assert all(fact["status"] == "UNKNOWN" for fact in embedding["facts"])
    fields = json.loads((pack / "s6_observed_field_classification_v1.json").read_text())
    by_path = {row["field_path"]: row for row in fields["records"]}
    required = (
        "account.adjEq",
        "account.availEq",
        "account.imr",
        "account.mmr",
        "account.mgnRatio",
        "account.totalEq",
        "account.upl",
        "details.eq",
        "details.upl",
        "details.liab",
        "details.imr",
        "details.mmr",
        "details.mgnRatio",
        "bills.fee",
        "bills.type",
        "bills.subType",
    )
    for path in required:
        assert path in by_path, path
    assert by_path["details.eq"]["classification_status"] == "MAPPED_RATIFIED"
    assert by_path["details.eq"]["peak_trade_target_kind"] == "NONE"
    assert by_path["account.availEq"]["classification_status"] == "NOT_APPLICABLE"
    assert by_path["account.adjEq"]["classification_status"] == "NOT_APPLICABLE"
    assert by_path["account.totalEq"]["classification_status"] == "NOT_APPLICABLE"
    assert by_path["account.imr"]["classification_status"] == "AMBIGUOUS"
    assert by_path["account.mmr"]["classification_status"] == "AMBIGUOUS"
    assert by_path["account.mgnRatio"]["classification_status"] == "AMBIGUOUS"
    assert by_path["account.upl"]["classification_status"] == "AMBIGUOUS"
    assert by_path["details.liab"]["classification_status"] == "AMBIGUOUS"
    assert by_path["bills.fee"]["classification_status"] == "AMBIGUOUS"
    assert by_path["bills.type"]["classification_status"] == "OBSERVED_UNRATIFIED"
    assert int(result.observed_relevant_field_count) == len(fields["records"])
    assert int(result.observed_relevant_field_count) >= len(required)
    assert "account.imr" in result.high_value_unratified_candidates
    assert "details.liab" in result.high_value_unratified_candidates
    assert "bills.type" in result.ratification_candidates
    assert "U05_KIND_DECISION=REMAIN_UNKNOWN" in result.kind_set_resolution_blockers
    assert by_path["config.uid"]["observed_value"] == "REDACTED_IDENTITY_OR_ACCOUNT_MEMBER"
    assert by_path["config.mainUid"]["observed_value"] == "REDACTED_IDENTITY_OR_ACCOUNT_MEMBER"
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert OBSERVATION_EXECUTED is False
    assert OBSERVATION_EXECUTION_AUTHORIZED is False
    assert OBSERVATION_NETWORK_GET_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EXECUTION_READY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert verify_manifest_sha256_v1(store_root=pack) == 0


def test_canonical_s6_pack_matches_fail_closed_classification() -> None:
    claims = json.loads((CANONICAL_S6_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["GENESIS_AS_OF"] == EXPECTED_GENESIS_AS_OF
    assert claims["MAPPING_AS_OF"] == _S6_AS_OF
    assert claims["S6_EXECUTED"] == "true"
    assert claims["SEALED_INPUT_ONLY"] == "true"
    assert claims["MANIFEST_VERIFY_RC"] == "0"
    assert claims["OBSERVED_KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["MAPPING_PERSISTED"] == "false"
    assert claims["MAPPING_COVERAGE_STATUS"] == "FAIL_CLOSED_NO_RATIFIED_KIND"
    assert claims["CLASSIFIED_BILL_ROW_COUNT"] == "58"
    assert claims["RETENTION_COVERAGE_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["ORDERING_COMPLETENESS_STATUS"] == "FAIL_CLOSED_NOT_PROVEN"
    assert claims["D4_IDENTITY_MINTED"] == "false"
    assert claims["RAW_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["NEW_NETWORK_GET_COUNT"] == "0"
    assert claims["NETWORK_POST_PERFORMED"] == "false"
    assert claims["MS2_AUTHORIZED"] == "false"
    assert claims["D6_FULLY_CLOSED"] == "false"
    assert claims["D7_AUTHORIZED"] == "false"
    assert claims["FIELD_SEMANTIC_TRACE_PERSISTED"] == "true"
    assert int(claims["OBSERVED_RELEVANT_FIELD_COUNT"]) > 0
    assert "account.imr" in claims["AMBIGUOUS_FIELDS"]
    assert "account.availEq" in claims["NOT_APPLICABLE_FIELDS"]
    assert "details.eq" in claims["MAPPED_RATIFIED_FIELDS"]
    assert verify_manifest_sha256_v1(store_root=CANONICAL_S6_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_S6_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_S6_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_S6_PACK / name).read_bytes()).hexdigest() == digest


def test_runbook_bd_persists_fail_closed_s6() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bd_section = _bd_section()
    assert "OWNER_GO=OWNER_GO_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION_V1" in bd_section
    assert "THIS_SLICE=11.2.1.BD.FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION" in (
        bd_section
    )
    assert "S6_EXECUTED=true" in bd_section
    assert "KIND_SET_RESOLVED=false" in bd_section
    assert "MAPPING_PERSISTED=false" in bd_section
    assert "MAPPING_COVERAGE_STATUS=FAIL_CLOSED_NO_RATIFIED_KIND" in bd_section
    assert "D4_IDENTITY_MINTED=false" in bd_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in bd_section
    assert "NEW_NETWORK_GET_COUNT=0" in bd_section
    assert "NETWORK_POST_PERFORMED=false" in bd_section
    assert "MS2_AUTHORIZED=false" in bd_section
    assert "D6_FULLY_CLOSED=false" in bd_section
    assert "D7_AUTHORIZED=false" in bd_section
    assert "FIELD_SEMANTIC_TRACE_PERSISTED=true" in bd_section
    assert "DOCS_TOKEN_FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION_V1.md" in mot
    assert "§11.2.1.BD FULL_CORE_D6_PATH_B_PACKAGE_1_S6_MAPPING_CLASSIFICATION" in mot
    runbook = RUNBOOK.read_text(encoding="utf-8")
    bc_start = runbook.index(BC_HEADING)
    bc_only = runbook[bc_start : runbook.index(BD_HEADING, bc_start)]
    assert "S6_EXECUTED=false" in bc_only
