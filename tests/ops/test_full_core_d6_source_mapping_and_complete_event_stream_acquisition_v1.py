"""D6 source-mapping and classified event-stream acquisition tests.

Sealed S1-S6 plus #6452 mapping input only. No new GET.
"""

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
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
    EARLIEST_REMAINING_D6_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY,
    OWNER_GO,
    AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError,
    execute_account_equity_source_mapping_and_complete_event_stream_acquisition_v1,
    reject_observed_value_as_kind_absence_or_embedding_decision_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
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
    / "docs/ops/specs/FULL_CORE_D6_SOURCE_MAPPING_AND_COMPLETE_EVENT_STREAM_ACQUISITION_V1.md"
)
BF_HEADING = (
    "11.2.1.BF FULL_CORE_D6_SOURCE_MAPPING_AND_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
)
BE_HEADING = "11.2.1.BE FULL_CORE_D6_ACCOUNT_EQUITY_SOURCE_MAPPING_RATIFICATION"
SEALED_PACK = REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
CANONICAL_S6_PACK = REPO_ROOT / CANONICAL_S6_PACK_RELPATH
CANONICAL_MAPPING_PACK = REPO_ROOT / CANONICAL_MAPPING_PACK_RELPATH
CANONICAL_ACQUISITION_PACK = (
    REPO_ROOT / "evidence/ops/full_core_d6_source_mapping_and_complete_event_stream_acquisition_v1/"
    "2026-09-13T194000Z"
)
_AS_OF = "2026-09-13T19:40:00Z"


def _bf_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BF_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BG FULL_CORE_D6_F12_F13_F16_F17_F18_NECESSARY_EQUITY_STOCK_KIND_RESOLUTION",
            start,
        )
    ]


def test_sealed_input_manifests_verify() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_S6_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_MAPPING_PACK) == 0


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(
        AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_account_equity_source_mapping_and_complete_event_stream_acquisition_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_observation_pack=SEALED_PACK,
            sealed_s6_pack=CANONICAL_S6_PACK,
            sealed_mapping_pack=CANONICAL_MAPPING_PACK,
            evidence_root=tmp_path / "acq",
            acquisition_as_of=_AS_OF,
        )
    assert not (tmp_path / "acq" / "2026-09-13T194000Z").exists()


def test_forensic_value_cannot_decide_embedding_or_kind() -> None:
    with pytest.raises(
        AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError,
        match="FORENSIC_VALUE_CANNOT_INCLUDE",
    ):
        reject_observed_value_as_kind_absence_or_embedding_decision_v1(
            claimed_proof="INCLUDE",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        AccountEquitySourceMappingAndCompleteEventStreamAcquisitionError,
        match="FORENSIC_VALUE_CANNOT_KIND_ABSENCE",
    ):
        reject_observed_value_as_kind_absence_or_embedding_decision_v1(
            claimed_proof="KIND_ABSENCE",
            fact_id="KIND_ABSENCE",
        )
    reject_observed_value_as_kind_absence_or_embedding_decision_v1(
        claimed_proof="NO_UNIQUE_EMBEDDING_OR_KIND_DECISION",
        fact_id="F16_FEE_ALREADY_EMBEDDED_IN_EQ",
    )


def test_acquisition_ranks_remaining_blocker_without_source_kinds(
    tmp_path: Path,
) -> None:
    result = execute_account_equity_source_mapping_and_complete_event_stream_acquisition_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_observation_pack=SEALED_PACK,
        sealed_s6_pack=CANONICAL_S6_PACK,
        sealed_mapping_pack=CANONICAL_MAPPING_PACK,
        evidence_root=tmp_path / "acq",
        acquisition_as_of=_AS_OF,
    )
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.ratified_source_kinds == "NONE"
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.mapping_persisted == "true"
    assert result.raw_eq_source_authority == "false"
    assert result.u05_kind_decision == "REMAIN_UNKNOWN"
    assert result.u06_kind_decision == "REMAIN_UNKNOWN"
    assert result.residual_kind_decision == "REMAIN_UNKNOWN"
    assert result.f12_f13_f16_f17_f18_status == "UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN"
    assert result.retention_coverage_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.ordering_completeness_status == "FAIL_CLOSED_NOT_PROVEN"
    assert result.authorized_productive_event_source_seam == "false"
    assert result.complete_classified_event_stream_proven == "false"
    assert result.earliest_remaining_d6_blocker == EARLIEST_REMAINING_D6_BLOCKER
    assert result.new_network_get_count == "0"
    assert result.network_post_performed == "false"
    assert result.ms2_authorized == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    pack = Path(result.store_root)
    ranked = json.loads((pack / "ranked_remaining_d6_blockers_v1.json").read_text())
    assert ranked["earliest_remaining_d6_blocker"] == EARLIEST_REMAINING_D6_BLOCKER
    assert ranked["kind_set_include_exclude_blocked_by"] == KIND_SET_INCLUDE_EXCLUDE_BLOCKED_BY
    assert ranked["narrower_than_be_bag"] == "true"
    assert ranked["records"][0]["rank"] == "1"
    forensic_bills = json.loads((pack / "forensic_bills_raw_v1.json").read_text())
    assert forensic_bills["interpretation_status"] == "FORBIDDEN"
    assert forensic_bills["partial_overlap_does_not_prove_retention"] == "true"
    forensic_balance = json.loads((pack / "forensic_balance_raw_v1.json").read_text())
    assert forensic_balance["eq_remains_reconciliation_target_only"] == "true"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False


def test_canonical_acquisition_pack_matches_executor() -> None:
    claims = json.loads((CANONICAL_ACQUISITION_PACK / "claims.json").read_text())
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["EARLIEST_REMAINING_D6_BLOCKER"] == EARLIEST_REMAINING_D6_BLOCKER
    assert claims["NEW_NETWORK_GET_COUNT"] == "0"
    assert verify_manifest_sha256_v1(store_root=CANONICAL_ACQUISITION_PACK) == 0
    expected: dict[str, str] = {}
    for line in (
        (CANONICAL_ACQUISITION_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    ):
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_ACQUISITION_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert (
            hashlib.sha256((CANONICAL_ACQUISITION_PACK / name).read_bytes()).hexdigest() == digest
        )


def test_runbook_bf_persists_ranked_fail_closed_acquisition() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    bf_section = _bf_section()
    assert OWNER_GO in bf_section
    assert (
        "THIS_SLICE=11.2.1.BF.FULL_CORE_D6_SOURCE_MAPPING_AND_COMPLETE_CLASSIFIED_EVENT_STREAM_ACQUISITION"
        in bf_section
    )
    assert "RATIFIED_SOURCE_KINDS=NONE" in bf_section
    assert "KIND_SET_RESOLVED=false" in bf_section
    assert f"EARLIEST_REMAINING_D6_BLOCKER={EARLIEST_REMAINING_D6_BLOCKER}" in bf_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in bf_section
    assert "MS2_AUTHORIZED=false" in bf_section
    assert "D6_FULLY_CLOSED=false" in bf_section
    assert "D7_AUTHORIZED=false" in bf_section
    assert "COMPLETE_CLASSIFIED_EVENT_STREAM_PROVEN=false" in bf_section
    assert "DOCS_TOKEN_FULL_CORE_D6_SOURCE_MAPPING_AND_COMPLETE_EVENT_STREAM_ACQUISITION_V1" in spec
