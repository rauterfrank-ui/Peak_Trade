"""D6 F12/F13 KIND_SET remaining-unknown pin and reopen-gate tests.

Sealed BH+BI only. No GET. UNKNOWN is durable, not D6 closeout.
GATE_A and GATE_B are named, not executed.
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
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_and_complete_event_stream_acquisition_v1 import (
    CANONICAL_MAPPING_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    CANONICAL_S6_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.eq_identity_and_f12_f13_liability_stock_kind_ratification_v1 import (
    CANONICAL_BH_PACK_RELPATH,
    CANONICAL_PACK_RELPATH as CANONICAL_BI_PACK_RELPATH,
    IDENTITY_NONE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    CANONICAL_PACK_RELPATH,
    CURRENTLY_DECISION_CAPABLE,
    EARLIEST_REMAINING_D6_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    GATE_A_ID,
    GATE_B_ID,
    OWNER_GO,
    SELECTED_BALANCE_SURFACE,
    F12F13KindSetRemainingUnknownPinAndReopenGateError,
    execute_f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1,
    reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    CANONICAL_SEALED_OBSERVATION_PACK_RELPATH,
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BJ_HEADING = "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE"
SEALED_BI = REPO_ROOT / CANONICAL_BI_PACK_RELPATH
SEALED_BH = REPO_ROOT / CANONICAL_BH_PACK_RELPATH
SEALED_PACK = REPO_ROOT / CANONICAL_SEALED_OBSERVATION_PACK_RELPATH
CANONICAL_S6_PACK = REPO_ROOT / CANONICAL_S6_PACK_RELPATH
CANONICAL_MAPPING_PACK = REPO_ROOT / CANONICAL_MAPPING_PACK_RELPATH
CANONICAL_PIN_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-13T23:59:00Z"


def _bj_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BJ_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.BK FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION",
            start,
        )
    ]


def _run(tmp_path: Path):
    return execute_f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bi_pack=SEALED_BI,
        sealed_bh_pack=SEALED_BH,
        sealed_observation_pack=SEALED_PACK,
        sealed_s6_pack=CANONICAL_S6_PACK,
        sealed_mapping_pack=CANONICAL_MAPPING_PACK,
        evidence_root=tmp_path / "pin",
        pin_as_of=_AS_OF,
    )


def test_sealed_input_manifests_verify() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BI) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_BH) == 0
    assert verify_manifest_sha256_v1(store_root=SEALED_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_S6_PACK) == 0
    assert verify_manifest_sha256_v1(store_root=CANONICAL_MAPPING_PACK) == 0


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    with pytest.raises(
        F12F13KindSetRemainingUnknownPinAndReopenGateError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bi_pack=SEALED_BI,
            sealed_bh_pack=SEALED_BH,
            sealed_observation_pack=SEALED_PACK,
            sealed_s6_pack=CANONICAL_S6_PACK,
            sealed_mapping_pack=CANONICAL_MAPPING_PACK,
            evidence_root=tmp_path / "pin",
            pin_as_of=_AS_OF,
        )
    assert not (tmp_path / "pin" / "2026-09-13T235900Z").exists()


def test_claimed_include_gate_execution_or_closeout_fail_closes() -> None:
    with pytest.raises(
        F12F13KindSetRemainingUnknownPinAndReopenGateError,
        match="REMAINING_UNKNOWN_PIN_CANNOT_INCLUDE:",
    ):
        reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
            claimed_proof="INCLUDE",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        F12F13KindSetRemainingUnknownPinAndReopenGateError,
        match="REMAINING_UNKNOWN_PIN_CANNOT_EXECUTE_GATE_A:",
    ):
        reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
            claimed_proof="EXECUTE_GATE_A",
            fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
        )
    with pytest.raises(
        F12F13KindSetRemainingUnknownPinAndReopenGateError,
        match="REMAINING_UNKNOWN_PIN_CANNOT_PATH_C_UNKNOWN_CLOSEOUT:",
    ):
        reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
            claimed_proof="PATH_C_UNKNOWN_CLOSEOUT",
            fact_id="F13_LIABILITY_ALREADY_EMBEDDED_IN_EQ",
        )
    reject_claimed_f12_f13_kind_set_close_or_gate_execution_v1(
        claimed_proof="DURABLE_UNKNOWN_NOT_D6_CLOSEOUT",
        fact_id="F12_LIABILITY_AFFECTS_EQUITY_STOCK",
    )


def test_pin_keeps_unknown_and_does_not_execute_gates(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.genesis_id == EXPECTED_GENESIS_ID
    assert result.genesis_as_of == EXPECTED_GENESIS_AS_OF
    assert result.ratified_eq_identity == IDENTITY_NONE
    assert result.f12_decision == "REMAIN_UNKNOWN"
    assert result.f13_decision == "REMAIN_UNKNOWN"
    assert result.u05_kind_decision == "REMAIN_UNKNOWN"
    assert result.f16_decision == "REMAIN_UNKNOWN"
    assert result.f17_decision == "REMAIN_UNKNOWN"
    assert result.f18_decision == "REMAIN_UNKNOWN"
    assert result.ratified_source_kinds == "NONE"
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.currently_decision_capable_evidence_classes == CURRENTLY_DECISION_CAPABLE
    assert result.unknown_durable_not_closeout == "true"
    assert result.gate_a_persisted == "true"
    assert result.gate_a_executed == "false"
    assert result.gate_b_persisted == "true"
    assert result.gate_b_executed == "false"
    assert result.venue_get_count == "0"
    assert result.post_count == "0"
    assert result.ms2_authorized == "false"
    assert result.d6_fully_closed == "false"
    assert result.d7_authorized == "false"
    assert result.earliest_remaining_d6_blocker == EARLIEST_REMAINING_D6_BLOCKER
    pack = Path(result.store_root)
    pin = json.loads((pack / "remaining_unknown_pin_v1.json").read_text())
    assert pin["layer"] == "ADJUDICATED"
    assert pin["currently_decision_capable_evidence_classes_for_f12_f13"] == "NONE"
    assert pin["unknown_is_durable_but_not_d6_closeout"] == "true"
    assert pin["include_from_unknown_forbidden"] == "true"
    assert pin["exclude_from_unknown_forbidden"] == "true"
    assert pin["further_read_only_slices_on_exhausted_classes_forbidden"] == "true"
    gates = json.loads((pack / "reopen_gates_v1.json").read_text())
    assert gates["gate_a_executed"] == "false"
    assert gates["gate_b_executed"] == "false"
    assert gates["this_workpackage_authorizes_gate_a_get"] == "false"
    gate_a = next(item for item in gates["records"] if item["gate_id"] == GATE_A_ID)
    assert gate_a["authorized_surface_if_later_go"] == SELECTED_BALANCE_SURFACE
    assert gate_a["max_get_count_if_later_go"] == "1"
    assert gate_a["get_alone_may_include"] == "false"
    assert gate_a["get_alone_may_exclude"] == "false"
    gate_b = next(item for item in gates["records"] if item["gate_id"] == GATE_B_ID)
    assert gate_b["no_uniqueness_means"] == "REMAIN_UNKNOWN"
    assert gate_b["vendor_web_repo_archive_search_this_go"] == "FORBIDDEN"
    exhausted = json.loads((pack / "exhausted_or_forbidden_evidence_classes_v1.json").read_text())
    class_ids = {item["class_id"] for item in exhausted["records"]}
    assert "BH_EMPTY_ZERO_ABSENT_BALANCE_SNAPSHOT" in class_ids
    assert "REPEAT_BALANCE_HOPE_GET" in class_ids
    assert "PATH_C_ARCHITECTURAL_UNKNOWN_CLOSEOUT" in class_ids
    layers = json.loads((pack / "layers_v1.json").read_text())
    assert layers["FORENSIC_RAW"] == "NONE_NEW_THIS_GO"
    assert layers["INTERPRETATION"] == "FORBIDDEN"
    assert layers["HYPOTHESIS"] == "FORBIDDEN"
    claims = json.loads((pack / "claims.json").read_text())
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["GATE_A_EXECUTED"] == "false"
    assert claims["GATE_B_EXECUTED"] == "false"
    assert claims["PATH_C"] == "REJECT"
    assert verify_manifest_sha256_v1(store_root=pack) == 0
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert (
        EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY
        == "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_canonical_pack_matches_executor() -> None:
    claims = json.loads((CANONICAL_PIN_PACK / "claims.json").read_text())
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["GENESIS_ID"] == EXPECTED_GENESIS_ID
    assert claims["RATIFIED_EQ_IDENTITY"] == "NONE"
    assert claims["F12_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["F13_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["U05_KIND_DECISION"] == "REMAIN_UNKNOWN"
    assert claims["CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13"] == "NONE"
    assert claims["UNKNOWN_IS_DURABLE_BUT_NOT_D6_CLOSEOUT"] == "true"
    assert claims["GATE_A_EXECUTED"] == "false"
    assert claims["GATE_B_EXECUTED"] == "false"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["D6_FULLY_CLOSED"] == "false"
    assert claims["D7_AUTHORIZED"] == "false"
    assert claims["MS2_AUTHORIZED"] == "false"
    assert claims["EARLIEST_REMAINING_D6_BLOCKER"] == EARLIEST_REMAINING_D6_BLOCKER
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PIN_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_PIN_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_PIN_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_PIN_PACK / name).read_bytes()).hexdigest() == digest


def test_runbook_bj_and_navigation_persist_pin() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bj_section = _bj_section()
    assert OWNER_GO in bj_section
    assert (
        "THIS_SLICE=11.2.1.BJ.FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE"
        in bj_section
    )
    assert "CURRENTLY_DECISION_CAPABLE_EVIDENCE_CLASSES_FOR_F12_F13=NONE" in bj_section
    assert "UNKNOWN_IS_DURABLE_BUT_NOT_D6_CLOSEOUT=true" in bj_section
    assert "GATE_A_EXECUTED=false" in bj_section
    assert "GATE_B_EXECUTED=false" in bj_section
    assert "F12_DECISION=REMAIN_UNKNOWN" in bj_section
    assert "F13_DECISION=REMAIN_UNKNOWN" in bj_section
    assert "KIND_SET_RESOLVED=false" in bj_section
    assert f"EARLIEST_REMAINING_D6_BLOCKER={EARLIEST_REMAINING_D6_BLOCKER}" in bj_section
    assert "VENUE_GET_COUNT=0" in bj_section
    assert "D6_FULLY_CLOSED=false" in bj_section
    assert "D7_AUTHORIZED=false" in bj_section
    assert "MS2_AUTHORIZED=false" in bj_section
    assert (
        "DOCS_TOKEN_FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE_V1" in spec
    )
    assert "FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE_V1.md" in mot
    assert "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE" in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BJ" in atlas
