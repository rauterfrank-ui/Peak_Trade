"""Typed P01 applicability adjudication contract. No productive reconstruction."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    GOVERNED_PRODUCER_CREATED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT,
    P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT,
    P01_APPLICABILITY_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_applicability_contract_v1 import (
    EVIDENCE_CLASSIFICATION,
    P01_APPLICABILITY_RULE,
    P01_APPLICABILITY_STATUS,
    REJECTED_APPLICABILITY_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    TYPED_APPLICABILITY_STATE,
    TYPED_APPLICABILITY_STATE_APPLIES,
    TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY,
    TYPED_APPLICABILITY_STATE_UNKNOWN,
    P01ApplicabilityContractError,
    P01ApplicabilityContractV1,
    build_p01_applicability_contract_v1,
    reject_p01_applicability_inferred_from_u04_u05_u06_or_venue_v1,
    reject_p01_unknown_applicability_as_not_applicable_v1,
    reject_p01_zero_or_absence_as_not_applicable_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    APPLICABILITY_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    INCLUSION_NOT_APPLICABLE,
    NUMERIC_PRESENT_ZERO,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_PENDING_ORDER_RESERVATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT_V1.md"
AC_HEADING = "11.2.1.AC FULL_CORE_TYPED_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT"
AD_HEADING = "11.2.1.AD FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT"
AE_HEADING = "11.2.1.AE FULL_CORE_TYPED_P01_EQUITY_BASE_INCLUSION_CONTRACT"


def _ad_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ad_start = runbook.index(AD_HEADING)
    return runbook[ad_start : runbook.index(AE_HEADING, ad_start)]


def test_p01_applicability_contract_constructs() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert isinstance(contract, P01ApplicabilityContractV1)
    assert SCHEMA_CLASS == "P01_APPLICABILITY_CONTRACT_V1"
    assert contract.p01_applicability_status == APPLICABILITY_STATE
    assert contract.p01_applicability_status == P01_APPLICABILITY_STATUS
    assert contract.p01_applicability_rule == P01_APPLICABILITY_RULE
    assert contract.p01_applicability_resolved_status == "false"
    assert contract.typed_applicability_state == TYPED_APPLICABILITY_STATE_UNKNOWN
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT is True
    assert P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_applicability_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    second = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_unknown_applicability_remains_fail_closed_not_not_applicable() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert contract.p01_applicability_status == "UNSPECIFIED_FAIL_CLOSED"
    assert contract.typed_applicability_state == TYPED_APPLICABILITY_STATE
    assert contract.typed_applicability_state != TYPED_APPLICABILITY_STATE_APPLIES
    assert contract.typed_applicability_state != TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY
    assert contract.typed_applicability_state != INCLUSION_NOT_APPLICABLE
    assert contract.unknown_is_not_not_applicable == "true"
    with pytest.raises(P01ApplicabilityContractError) as raised:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_status=INCLUSION_NOT_APPLICABLE,
        )
    assert "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01ApplicabilityContractError) as helper:
        reject_p01_unknown_applicability_as_not_applicable_v1(
            applicability_status=INCLUSION_NOT_APPLICABLE
        )
    assert "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in str(helper.value)


def test_missing_input_cannot_become_not_applicable() -> None:
    with pytest.raises(P01ApplicabilityContractError) as missing:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_status=None,
        )
    assert "P01_FIELD_MISSING:p01_applicability_status" in str(missing.value)
    with pytest.raises(P01ApplicabilityContractError) as empty:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_status="",
        )
    assert "P01_FIELD_MISSING:p01_applicability_status" in str(empty.value)


def test_malformed_input_cannot_become_not_applicable() -> None:
    with pytest.raises(P01ApplicabilityContractError) as not_string:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_status=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_applicability_status" in str(not_string.value)
    with pytest.raises(P01ApplicabilityContractError) as numeric:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_status=0,
        )
    assert "P01_FIELD_NOT_STRING:p01_applicability_status" in str(numeric.value)


def test_zero_cannot_imply_not_applicable() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert contract.zero_is_not_not_applicable == "true"
    for inferred in ("0", "ZERO", NUMERIC_PRESENT_ZERO):
        with pytest.raises(P01ApplicabilityContractError) as raised:
            build_p01_applicability_contract_v1(
                p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
                p01_applicability_status=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_NOT_APPLICABLE_FORBIDDEN" in str(
            raised.value
        ) or "P01_APPLICABILITY_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01ApplicabilityContractError) as helper:
        reject_p01_zero_or_absence_as_not_applicable_v1(applicability_status="0")
    assert "P01_ZERO_OR_ABSENCE_NOT_APPLICABLE_FORBIDDEN" in str(helper.value)


def test_absence_cannot_imply_not_applicable() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert contract.absence_is_not_not_applicable == "true"
    for inferred in ("ABSENT", "MISSING", "NONE"):
        with pytest.raises(P01ApplicabilityContractError) as raised:
            build_p01_applicability_contract_v1(
                p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
                p01_applicability_status=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_NOT_APPLICABLE_FORBIDDEN" in str(raised.value)


def test_term_set_and_unit_unresolved_do_not_decide_applicability() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert contract.term_set_unresolved_does_not_decide_applicability == "true"
    assert contract.unit_unresolved_does_not_decide_applicability == "true"
    assert contract.p01_applicability_resolved_status == "false"
    with pytest.raises(P01ApplicabilityContractError) as resolved:
        build_p01_applicability_contract_v1(
            p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
            p01_applicability_resolved_status="true",
        )
    assert "P01_APPLICABILITY_RESOLVED_FORBIDDEN" in str(resolved.value)


def test_u04_u05_u06_and_venue_raw_cannot_decide_applicability() -> None:
    for inferred in (
        "U04",
        "U05",
        "U06",
        TERM_PENDING_ORDER_RESERVATION,
        TERM_LIABILITY,
        TERM_FEE,
        "WHEN_PENDING_ORDERS_EXIST",
        "WHEN_FEES_EXIST",
        "frozenBal",
        "ordFrozen",
        "availEq",
    ):
        with pytest.raises(P01ApplicabilityContractError) as raised:
            build_p01_applicability_contract_v1(
                p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
                p01_applicability_rule=inferred,
            )
        assert "P01_APPLICABILITY_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01ApplicabilityContractError) as helper:
        reject_p01_applicability_inferred_from_u04_u05_u06_or_venue_v1(applicability_rule="U04")
    assert "P01_APPLICABILITY_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_candidate_applicability_rules_remain_unproven() -> None:
    for inferred in (
        "ALWAYS_APPLIES",
        "NEVER_APPLIES",
        "POLICY_SELECTED",
        "WHEN_RESERVE_CONFIGURED",
        "VENUE_DEPENDENT",
        TYPED_APPLICABILITY_STATE_APPLIES,
        TYPED_APPLICABILITY_STATE_DOES_NOT_APPLY,
        "OPTIONAL",
        "DISABLED",
    ):
        with pytest.raises(P01ApplicabilityContractError) as raised:
            build_p01_applicability_contract_v1(
                p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID",
                p01_applicability_rule=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_APPLICABILITY_INFERRED_FROM_LABEL_FORBIDDEN" in message
            or "P01_UNKNOWN_APPLICABILITY_AUTO_NA_FORBIDDEN" in message
        )


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_applicability_contract_v1(
        p01_applicability_contract_id="SYNTHETIC_P01_APPLICABILITY_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_APPLICABILITY_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_TERM_SET_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_applicability_inferences == REJECTED_APPLICABILITY_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_APPLICABILITY_RESOLVED"] is False
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is False
    assert dag["P01_APPLICABILITY_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_APPLICABILITY_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ad_consumes_go_without_rewriting_ac() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ad_section = _ad_section()
    ac_start = runbook.index(AC_HEADING)
    ac_section = runbook[ac_start : runbook.index(AD_HEADING, ac_start)]
    assert "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT=true" in ac_section
    assert "THIS_SLICE=11.2.1.AD" not in ac_section
    assert "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_APPLICABILITY_CONTRACT_V1" in ad_section
    assert "OWNER_GO_STATUS=CONSUMED" in ad_section
    assert "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT=true" in ad_section
    assert "P01_APPLICABILITY_RESOLVED=false" in ad_section
    assert "P01_APPLICABILITY=UNSPECIFIED_FAIL_CLOSED" in ad_section
    assert "P01_TERM_SET_RESOLVED=false" in ad_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ad_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ad_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ad_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ad_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ad_section
    assert "SOURCE_SELECTED=false" in ad_section
    assert "MAPPING_PROVEN=false" in ad_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ad_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT_V1" in spec
    assert "P01_APPLICABILITY_RESOLVED=false" in spec
    assert "P01_TERM_SET_RESOLVED=false" in spec
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in spec
