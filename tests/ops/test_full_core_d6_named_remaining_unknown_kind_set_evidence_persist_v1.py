"""D6 named remaining-unknown kind-set evidence persist."""

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
    EARLIEST_D6_KIND_SET_DEPENDENCY,
    EVENT_KIND_SOURCE_SEAM_SELECTED,
    HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES,
    KIND_SET_EVIDENCE_PERSIST_CREATED,
    KIND_SET_EVIDENCE_PERSIST_STATUS,
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS1_KIND_SET_FULLY_CLOSED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ENGINE_CREATED,
    RESIDUAL_COMPLETENESS_PROVEN,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_NO_REMAINDER_NORMALIZED,
    SOURCE_SELECTED,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    UNKNOWN_NECESSARY_CLASS_REMAINS,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    OWNER,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
    RATIFIED_CLASSIFIED_KIND_SET_RESOLVED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    CANDIDATE_RESIDUAL,
    CANDIDATE_U05,
    CANDIDATE_U06,
    DECISION_REMAIN_UNKNOWN,
    EVIDENCE_STATUS_FAIL_CLOSED,
    HYPOTHESIS_ONLY_TOKEN,
    NamedRemainingUnknownKindSetEvidencePersistContractError,
    build_named_remaining_unknown_kind_evidence_records_v1,
    build_named_remaining_unknown_kind_set_evidence_persist_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_ADJUDICATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST_V1.md"
)
AW_HEADING = "11.2.1.AW FULL_CORE_D6_EQUITY_STOCK_NECESSARY_KIND_SET_CLOSEOUT"
AX_HEADING = "11.2.1.AX FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST"
AY_HEADING = "11.2.1.AY FULL_CORE_D6_SCOPED_READ_ONLY_OBSERVATION_BOUNDARY"
_NEW_CONTRACT_FILE = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "named_remaining_unknown_kind_set_evidence_persist_contract_v1.py"
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
    return runbook[aw_start : runbook.index(AX_HEADING, aw_start)]


def _ax_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ax_start = runbook.index(AX_HEADING)
    return runbook[ax_start : runbook.index(AY_HEADING, ax_start)]


def test_three_candidates_remain_unknown_and_kind_set_stays_empty() -> None:
    persist = build_named_remaining_unknown_kind_set_evidence_persist_v1(
        persist_id="KIND_SET_EVIDENCE_A"
    )
    records = {
        record.candidate_id: record
        for record in build_named_remaining_unknown_kind_evidence_records_v1()
    }
    assert RATIFIED_CLASSIFIED_KIND_SET == ()
    assert RATIFIED_CLASSIFIED_KIND_SET_RESOLVED is False
    assert KIND_SET_RESOLVED is False
    assert persist.ratified_classified_event_kind_set == "EMPTY_FAIL_CLOSED"
    assert persist.kind_set_resolved == "false"
    assert persist.unknown_necessary_class_remains == "true"
    assert persist.ms1_kind_set_fully_closed == "false"
    assert persist.ms2_authorized == "false"
    assert persist.u05_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.u06_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.residual_kind_decision == DECISION_REMAIN_UNKNOWN
    assert persist.residual_completeness_proven == "false"
    assert persist.residual_no_remainder_normalized == "false"
    assert persist.hypothesis_only_classes == HYPOTHESIS_ONLY_TOKEN
    assert persist.p01_u05_overlap_adjudication == "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
    assert persist.evidence_persist_status == EVIDENCE_STATUS_FAIL_CLOSED
    assert records[CANDIDATE_U05].decision == DECISION_REMAIN_UNKNOWN
    assert records[CANDIDATE_U06].decision == DECISION_REMAIN_UNKNOWN
    assert records[CANDIDATE_RESIDUAL].decision == DECISION_REMAIN_UNKNOWN
    assert "INCLUDE" not in records[CANDIDATE_U05].decision
    assert "EXCLUDE" not in records[CANDIDATE_RESIDUAL].decision
    assert "NO_REMAINDER" not in records[CANDIDATE_RESIDUAL].embedding_status


def test_evidence_persist_does_not_release_ms2_or_equity_authority() -> None:
    persist = build_named_remaining_unknown_kind_set_evidence_persist_v1(
        persist_id="KIND_SET_EVIDENCE_PINS"
    )
    dag = live_admission_gap_dag_v1()
    assert OWNER == "ops.governed_productive_account_equity_authority_producer_v1"
    assert ACCOUNT_EQUITY_AUTHORITY_OWNER == OWNER
    assert KIND_SET_EVIDENCE_PERSIST_CREATED is True
    assert KIND_SET_EVIDENCE_PERSIST_STATUS == EVIDENCE_STATUS_FAIL_CLOSED
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_COMPLETENESS_PROVEN is False
    assert RESIDUAL_NO_REMAINDER_NORMALIZED is False
    assert UNKNOWN_NECESSARY_CLASS_REMAINS is True
    assert MS1_KIND_SET_FULLY_CLOSED is False
    assert MS2_AUTHORIZED is False
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
    assert P01_U05_OVERLAP_ADJUDICATION == "UNKNOWN_RELATIONSHIP_FAIL_CLOSED"
    assert HYPOTHESIS_ONLY_EQUITY_STOCK_EVENT_CLASSES == (
        "DEPOSIT",
        "WITHDRAWAL",
        "TRANSFER",
        "FUNDING",
        "INTEREST",
        "LIQUIDATION",
        "CONVERT",
    )
    assert EARLIEST_D6_KIND_SET_DEPENDENCY == (
        "NAMED_REMAINING_UNKNOWN_NECESSARY_EQUITY_STOCK_KIND_SET"
    )
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"
    )
    assert dag["U05_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert dag["U06_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert dag["RESIDUAL_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert dag["KIND_SET_EVIDENCE_PERSIST_STATUS"] == EVIDENCE_STATUS_FAIL_CLOSED
    assert dag["RESIDUAL_NO_REMAINDER_NORMALIZED"] is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()
    with pytest.raises(NamedRemainingUnknownKindSetEvidencePersistContractError):
        build_named_remaining_unknown_kind_set_evidence_persist_v1(persist_id=" ")
    text = (REPO_ROOT / _NEW_CONTRACT_FILE).read_text(encoding="utf-8")
    lowered = text.lower()
    for marker in _FORBIDDEN_ENGINE_MARKERS:
        assert marker not in lowered
    assert "def reconstruct_equity_stock" not in text
    assert persist.authority_effect == "NONE"


def test_runbook_ax_consumes_owner_go_without_rewriting_aw_or_releasing_ms2() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    aw_section = _aw_section()
    ax_section = _ax_section()
    assert "THIS_SLICE=11.2.1.AW" in aw_section
    assert "THIS_SLICE=11.2.1.AX" not in aw_section
    assert "OWNER_GO=OWNER_GO_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST_V1" in ax_section
    assert "OWNER_GO_STATUS=CONSUMED" in ax_section
    assert (
        "THIS_SLICE=11.2.1.AX.FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST"
        in ax_section
    )
    assert "U05_KIND_DECISION=REMAIN_UNKNOWN" in ax_section
    assert "U06_KIND_DECISION=REMAIN_UNKNOWN" in ax_section
    assert "RESIDUAL_KIND_DECISION=REMAIN_UNKNOWN" in ax_section
    assert "KIND_SET_RESOLVED=false" in ax_section
    assert "MS1_KIND_SET_FULLY_CLOSED=false" in ax_section
    assert "MS2_AUTHORIZED=false" in ax_section
    assert "MINI_SLICE_3_AUTHORIZED=false" in ax_section
    assert "MINI_SLICE_4_AUTHORIZED=false" in ax_section
    assert "UNKNOWN_NECESSARY_CLASS_REMAINS=true" in ax_section
    assert "RESIDUAL_COMPLETENESS_PROVEN=false" in ax_section
    assert "RESIDUAL_NO_REMAINDER_NORMALIZED=false" in ax_section
    assert "P01_U05_OVERLAP_ADJUDICATION=UNKNOWN_RELATIONSHIP_FAIL_CLOSED" in ax_section
    assert "HYPOTHESIS_ONLY=DEPOSIT,WITHDRAWAL,TRANSFER,FUNDING,INTEREST,LIQUIDATION,CONVERT" in (
        ax_section
    )
    assert "AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT=false" in ax_section
    assert "NETWORK_GET_PERFORMED=false" in ax_section
    assert "NETWORK_POST_PERFORMED=false" in ax_section
    assert "C17_CREATED=false" in ax_section
    assert "RECONSTRUCTION_ENGINE_CREATED=false" in ax_section
    assert "LIVE_ENABLED=false" in ax_section
    assert "MASTER_V2_UNCHANGED=true" in ax_section
    assert "DOUBLE_PLAY_UNCHANGED=true" in ax_section
    assert "D7_DETERMINISTIC_STOCK_RECONSTRUCTION=NOT_BUILT" in ax_section
    assert (
        "MAX_SAFE_REPO_INTERNAL_NEXT_SLICE="
        "D6_REMAINS_BLOCKED_ON_NAMED_REMAINING_UNKNOWN_KIND_SET_INCLUDE_OR_EXCLUDE_EVIDENCE_REQUIREMENTS"
        in ax_section
    )
    assert "KIND_SET_RESOLVED=false" in spec
    assert "MS2_AUTHORIZED=false" in spec
    assert "DOCS_TOKEN_FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST_V1" in spec
    mot = (REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md").read_text(encoding="utf-8")
    assert "FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST_V1.md" in mot
    assert "§11.2.1.AX FULL_CORE_D6_NAMED_REMAINING_UNKNOWN_KIND_SET_EVIDENCE_PERSIST" in mot
