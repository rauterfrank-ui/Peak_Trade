"""D6 Mini-Slice 1 EQUITY_STOCK necessary kind-set fail-closed closeout."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ACCOUNT_EQUITY_AUTHORITY_OWNER,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_COMPLETENESS_PRECONDITIONS_PROVEN,
    EARLIEST_D6_COMPLETENESS_DEPENDENCY,
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    KIND_SET_CLOSEOUT_CREATED,
    KIND_SET_CLOSEOUT_STATUS,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    SOURCE_SELECTED,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_C01_C16_FORBIDDEN,
    DISPOSITION_EXCLUDED,
    DISPOSITION_NOT_EQUITY_STOCK,
    DISPOSITION_NOT_EVENT_KIND,
    DISPOSITION_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_necessary_kind_set_closeout_contract_v1 import (
    CLOSEOUT_STATUS_FAIL_CLOSED,
    EXCLUDED_CANDIDATE_IDS,
    REQUIRED_UNKNOWN_CANDIDATE_IDS,
    build_equity_stock_necessary_kind_set_closeout_v1,
    build_necessary_kind_disposition_records_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT_V1.md"
AV_HEADING = "11.2.1.AV FULL_CORE_D6_CLASSIFIED_KIND_SET_AND_EVENT_SOURCE_SEAM"
AW_HEADING = "11.2.1.AW FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT"
_NEW_CONTRACT_FILE = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "equity_stock_necessary_kind_set_closeout_contract_v1.py"
)
_FORBIDDEN_ENGINE_MARKERS = (
    "reconstruct_equity_stock_from_events",
    "acquire_equity_events",
    "requests.",
    "httpx.",
    "urllib.request",
)


def _aw_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    aw_start = runbook.index(AW_HEADING)
    return runbook[
        aw_start : runbook.index(
            "11.2.1.AX FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST", aw_start
        )
    ]


def _av_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    av_start = runbook.index(AV_HEADING)
    return runbook[av_start : runbook.index(AW_HEADING, av_start)]


def test_named_include_exclude_unknown_kind_set_closeout() -> None:
    closeout = build_equity_stock_necessary_kind_set_closeout_v1(closeout_id="KIND_SET_CLOSEOUT_A")
    records = build_necessary_kind_disposition_records_v1()
    by_id = {record.candidate_id: record for record in records}
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is False
    assert KIND_SET_RESOLVED is False
    assert closeout.included_classified_kinds == "NONE_RATIFIED"
    assert closeout.kind_set_resolved == "false"
    assert closeout.unknown_necessary_class_remains == "true"
    assert closeout.absence_is_not_zero_events == "true"
    assert closeout.ms1_kind_set_fully_closed == "false"
    assert closeout.ms2_authorized == "false"
    assert closeout.closeout_status == CLOSEOUT_STATUS_FAIL_CLOSED
    assert closeout.named_remaining_unknown_necessary_classes == ",".join(
        REQUIRED_UNKNOWN_CANDIDATE_IDS
    )
    assert closeout.excluded_candidate_ids == ",".join(EXCLUDED_CANDIDATE_IDS)
    assert by_id["FILL"].disposition == DISPOSITION_EXCLUDED
    assert by_id["U02_REALIZED_PNL"].disposition == DISPOSITION_NOT_EVENT_KIND
    assert by_id["U03_UNREALIZED_PNL_MTM"].disposition == DISPOSITION_NOT_EVENT_KIND
    assert by_id["U04_PENDING_ORDER_RESERVATION"].disposition == (DISPOSITION_NOT_EQUITY_STOCK)
    assert by_id["P01_GOVERNED_RISK_CAPITAL_REDUCTION"].disposition == (
        DISPOSITION_NOT_EQUITY_STOCK
    )
    assert by_id["C01_THROUGH_C16"].disposition == DISPOSITION_C01_C16_FORBIDDEN
    assert by_id["U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND"].disposition == (
        DISPOSITION_UNKNOWN
    )
    assert by_id["U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND"].disposition == (DISPOSITION_UNKNOWN)
    assert by_id["RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS"].disposition == (
        DISPOSITION_UNKNOWN
    )
    assert "FILL" not in RATIFIED_CLASSIFIED_KIND_SET
    assert "U04_PENDING_ORDER_RESERVATION" not in RATIFIED_CLASSIFIED_KIND_SET


def test_ms1_does_not_release_ms2_or_equity_authority() -> None:
    closeout = build_equity_stock_necessary_kind_set_closeout_v1(
        closeout_id="KIND_SET_CLOSEOUT_PINS"
    )
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert KIND_SET_CLOSEOUT_CREATED is True
    assert KIND_SET_CLOSEOUT_STATUS == CLOSEOUT_STATUS_FAIL_CLOSED
    assert UNKNOWN_NECESSARY_CLASS_REMAINS is True
    assert MS1_KIND_SET_FULLY_CLOSED is False
    assert MS2_AUTHORIZED is False
    assert NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES == REQUIRED_UNKNOWN_CANDIDATE_IDS
    assert AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT is False
    assert EVENT_KIND_SOURCE_SEAM_SELECTED is False
    assert SOURCE_SELECTED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert COMPLETE_EVENT_STREAM_PROVEN is False
    assert D6_COMPLETENESS_PRECONDITIONS_PROVEN is False
    assert C17_CREATED is False
    assert RECONSTRUCTION_ENGINE_CREATED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert closeout.authorized_productive_event_source_seam_present == "false"
    assert closeout.event_kind_source_seam_selected == "false"
    assert closeout.source_selected == "false"
    assert closeout.raw_eq_source_authority == "false"
    assert EARLIEST_D6_COMPLETENESS_DEPENDENCY == (
        "RATIFIED_CLASSIFIED_EVENT_KIND_SET_AND_AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM"
    )
    assert EARLIEST_D6_KIND_SET_DEPENDENCY == (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert dag["KIND_SET_RESOLVED"] is False
    assert dag["MS1_KIND_SET_FULLY_CLOSED"] is False
    assert dag["MS2_AUTHORIZED"] is False
    assert dag["UNKNOWN_NECESSARY_CLASS_REMAINS"] is True
    assert dag["KIND_SET_CLOSEOUT_STATUS"] == CLOSEOUT_STATUS_FAIL_CLOSED
    assert dag["EARLIEST_D6_KIND_SET_DEPENDENCY"] == EARLIEST_D6_KIND_SET_DEPENDENCY
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    text = (REPO_ROOT / _NEW_CONTRACT_FILE).read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in _FORBIDDEN_ENGINE_MARKERS:
        assert marker not in lowered
    assert "def reconstruct_equity_stock" not in text
    assert "def acquire_events" not in text


def test_runbook_aw_consumes_owner_go_without_rewriting_av_or_releasing_ms2() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    aw_section = _aw_section()
    av_section = _av_section()
    assert "THIS_SLICE=11.2.1.AV" in av_section
    assert "THIS_SLICE=11.2.1.AW" not in av_section
    assert (
        "OWNER_GO=OWNER_GO_D6_KIND_SET_AND_AUTHORIZED_EVENT_SOURCE_SEAM_CLOSEOUT_WP_V1"
        in aw_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in aw_section
    assert "THIS_SLICE=11.2.1.AW.FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT" in (
        aw_section
    )
    assert "KIND_SET_RESOLVED=false" in aw_section
    assert "MS1_KIND_SET_FULLY_CLOSED=false" in aw_section
    assert "MS2_AUTHORIZED=false" in aw_section
    assert "MINI_SLICE_3_AUTHORIZED=false" in aw_section
    assert "MINI_SLICE_4_AUTHORIZED=false" in aw_section
    assert "UNKNOWN_NECESSARY_CLASS_REMAINS=true" in aw_section
    assert "NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES=" in aw_section
    assert "U05_LIABILITY_AS_CLASSIFIED_EQUITY_STOCK_KIND" in aw_section
    assert "U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND" in aw_section
    assert "RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS" in aw_section
    assert "KIND_SET_CLOSEOUT_STATUS=FAIL_CLOSED_NAMED_REMAINING_UNKNOWN" in aw_section
    assert "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT=false" in aw_section
    assert "EVENT_KIND_SOURCE_SEAM_SELECTED=false" in aw_section
    assert "SOURCE_SELECTED=false" in aw_section
    assert "RAW_EQ_SOURCE_AUTHORITY=false" in aw_section
    assert "NETWORK_GET_PERFORMED=false" in aw_section
    assert "NETWORK_POST_PERFORMED=false" in aw_section
    assert "NEW_TRANSPORT_CREATED=false" in aw_section
    assert "C17_CREATED=false" in aw_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in aw_section
    assert "LIVE_ENABLED=false" in aw_section
    assert "MASTER_V2_UNCHANGED=true" in aw_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in aw_section
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in aw_section
    assert (
        "EARLIEST_D6_KIND_SET_DEPENDENCY="
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET" in aw_section
    )
    assert (
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE="
        "D6_REMAINS_BLOCKED_ON_NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
        in aw_section
    )
    assert "KIND_SET_RESOLVED=false" in spec
    assert "MS2_AUTHORIZED=false" in spec
    assert "DOCS_TOKEN_FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT_V1.md" in mot
    assert "§11.2.1.AW FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT" in mot
