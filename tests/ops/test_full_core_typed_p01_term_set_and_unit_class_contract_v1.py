"""Typed P01 term-set and unit-class adjudication contract. No productive reconstruction."""

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
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_term_set_and_unit_class_contract_v1 import (
    EVIDENCE_CLASSIFICATION,
    FAMILY_CLASS_LABELS,
    FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET,
    P01_TERM_SET,
    P01_VALUE_UNIT_CLASS,
    REJECTED_TERM_SET_INFERENCES,
    REJECTED_UNIT_CLASS_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    P01TermSetAndUnitClassContractError,
    P01TermSetAndUnitClassContractV1,
    build_p01_term_set_and_unit_class_contract_v1,
    reject_p01_term_membership_inferred_from_u04_u05_u06_v1,
    reject_p01_unit_inherited_from_settlement_currency_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    TERM_FEE,
    TERM_LIABILITY,
    TERM_PENDING_ORDER_RESERVATION,
    TERM_SET_UNSPECIFIED,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1.md"
AB_HEADING = "11.2.1.AB FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_TERM_CONTRACT"
AC_HEADING = "11.2.1.AC FULL_CORE_TYPED_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT"
AD_HEADING = "11.2.1.AD FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT"


def _ac_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ac_start = runbook.index(AC_HEADING)
    return runbook[ac_start : runbook.index(AD_HEADING, ac_start)]


def test_p01_term_set_and_unit_class_contract_constructs() -> None:
    contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    assert isinstance(contract, P01TermSetAndUnitClassContractV1)
    assert SCHEMA_CLASS == "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1"
    assert contract.p01_term_set == TERM_SET_UNSPECIFIED
    assert contract.p01_term_set == P01_TERM_SET
    assert contract.p01_value_unit_class == P01_VALUE_UNIT_CLASS
    assert contract.p01_term_set_resolved_status == "false"
    assert contract.p01_value_unit_class_resolved_status == "false"
    assert P01_TERM_SET_RESOLVED is False
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT is True
    assert P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_term_set_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    second = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_family_labels_are_not_an_exact_term_set() -> None:
    contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    assert contract.family_class_labels == FAMILY_CLASS_LABELS
    assert contract.family_labels_are_not_exact_term_set == FAMILY_LABELS_ARE_NOT_EXACT_TERM_SET
    assert contract.p01_term_set != FAMILY_CLASS_LABELS
    with pytest.raises(P01TermSetAndUnitClassContractError) as raised:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            p01_term_set=FAMILY_CLASS_LABELS,
        )
    assert "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)


def test_u04_u05_u06_labels_cannot_become_p01_members() -> None:
    for inferred in (
        "U04",
        "U05",
        "U06",
        TERM_PENDING_ORDER_RESERVATION,
        TERM_LIABILITY,
        TERM_FEE,
    ):
        with pytest.raises(P01TermSetAndUnitClassContractError) as raised:
            build_p01_term_set_and_unit_class_contract_v1(
                p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
                p01_term_set=inferred,
            )
        assert "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as helper:
        reject_p01_term_membership_inferred_from_u04_u05_u06_v1(term_set="U04")
    assert "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_empty_or_zero_term_set_is_not_canonical_zero() -> None:
    with pytest.raises(P01TermSetAndUnitClassContractError) as empty:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            p01_term_set="EMPTY",
        )
    assert "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN" in str(empty.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as zero:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            p01_term_set="ZERO",
        )
    assert "P01_TERM_MEMBERSHIP_INFERRED_FROM_LABEL_FORBIDDEN" in str(zero.value)


def test_unknown_unit_cannot_inherit_settlement_usdc() -> None:
    contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    assert contract.p01_value_unit_class == "UNSPECIFIED"
    for inferred in ("USDC", "USD", "AMOUNT", "RATIO", "PERCENT", "BPS", "CONTRACTS"):
        with pytest.raises(P01TermSetAndUnitClassContractError) as raised:
            build_p01_term_set_and_unit_class_contract_v1(
                p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
                p01_value_unit_class=inferred,
            )
        assert "P01_UNIT_INFERRED_CURRENCY_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as helper:
        reject_p01_unit_inherited_from_settlement_currency_v1(value_unit_class="USDC")
    assert "P01_UNIT_INFERRED_CURRENCY_FORBIDDEN" in str(helper.value)


def test_negative_p01_and_resolved_closure_remain_forbidden() -> None:
    with pytest.raises(P01TermSetAndUnitClassContractError) as negative:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            negative_allowed="true",
        )
    assert "P01_NEGATIVE_FORBIDDEN" in str(negative.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as resolved:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            p01_term_set_resolved_status="true",
        )
    assert "P01_TERM_SET_RESOLVED_FORBIDDEN" in str(resolved.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as unit_resolved:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            p01_value_unit_class_resolved_status="true",
        )
    assert "P01_VALUE_UNIT_CLASS_RESOLVED_FORBIDDEN" in str(unit_resolved.value)
    with pytest.raises(P01TermSetAndUnitClassContractError) as closed:
        build_p01_term_set_and_unit_class_contract_v1(
            p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID",
            unspecified_closed_status="true",
        )
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED_FORBIDDEN" in str(closed.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_term_set_and_unit_class_contract_v1(
        p01_term_set_and_unit_class_contract_id="SYNTHETIC_P01_TERM_SET_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_TERM_SET_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_term_set_inferences == REJECTED_TERM_SET_INFERENCES
    assert contract.rejected_unit_class_inferences == REJECTED_UNIT_CLASS_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_TERM_SET_RESOLVED"] is False
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ac_consumes_go_without_rewriting_ab() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ac_section = _ac_section()
    ab_start = runbook.index(AB_HEADING)
    ab_section = runbook[ab_start : runbook.index(AC_HEADING, ab_start)]
    assert "P01_TERM_CONTRACT_SCHEMA_PRESENT=true" in ab_section
    assert "THIS_SLICE=11.2.1.AC" not in ab_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1"
        in ac_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ac_section
    assert "P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_SCHEMA_PRESENT=true" in ac_section
    assert "P01_TERM_SET_RESOLVED=false" in ac_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ac_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ac_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ac_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ac_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ac_section
    assert "SOURCE_SELECTED=false" in ac_section
    assert "MAPPING_PROVEN=false" in ac_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ac_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_TERM_SET_AND_UNIT_CLASS_CONTRACT_V1" in spec
    assert "P01_TERM_SET_RESOLVED=false" in spec
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in spec
