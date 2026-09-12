"""Typed P01 exact member identity ratification. No productive reconstruction."""

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
    P01_APPLICABILITY_RESOLVED,
    P01_COMBINATION_PRECEDENCE_RESOLVED,
    P01_EXACT_MEMBER_COUNT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT,
    P01_EXACT_MEMBER_IDENTITY_SET,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED,
    P01_RUNTIME_INSTANCE_PRESENT,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    P01_ZERO_ABSENCE_NA_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_exact_member_identity_contract_v1 import (
    IDENTITY_LEVEL_MEANING,
    MEMBER_ID,
    RATIFICATION_SCOPE,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    P01ExactMemberIdentityContractError,
    P01ExactMemberIdentityContractV1,
    build_p01_exact_member_identity_contract_v1,
    reject_p01_identity_as_formula_v1,
    reject_p01_inferred_member_identity_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_EXACT_MEMBER_IDENTITY_CONTRACT_V1.md"
AJ_HEADING = "11.2.1.AJ FULL_CORE_TYPED_P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT"
AK_HEADING = "11.2.1.AK FULL_CORE_TYPED_P01_EXACT_MEMBER_IDENTITY_CONTRACT"
AL_HEADING = "11.2.1.AL FULL_CORE_TYPED_P01_VALUE_UNIT_CLASS_CONTRACT"


def _contract() -> P01ExactMemberIdentityContractV1:
    return build_p01_exact_member_identity_contract_v1(
        p01_exact_member_identity_contract_id="SYNTHETIC_P01_EXACT_MEMBER_IDENTITY_CONTRACT_ID"
    )


def _ak_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ak_start = runbook.index(AK_HEADING)
    return runbook[ak_start : runbook.index(AL_HEADING, ak_start)]


def test_p01_exact_member_identity_contract_constructs() -> None:
    contract = _contract()
    assert isinstance(contract, P01ExactMemberIdentityContractV1)
    assert SCHEMA_CLASS == "P01_EXACT_MEMBER_IDENTITY_CONTRACT_V1"
    assert contract.member_id == MEMBER_ID
    assert (
        contract.p01_exact_member_identity_set
        == "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION"
    )
    assert contract.p01_exact_member_count == "1"
    assert contract.ratification_scope == RATIFICATION_SCOPE
    assert contract.identity_level_meaning == IDENTITY_LEVEL_MEANING
    assert contract.p01_term_set_resolved_status == "true"
    assert contract.p01_runtime_instance_present == "false"
    assert contract.p01_authority_effect == "NONE"
    assert P01_TERM_SET_RESOLVED is True
    assert P01_EXACT_MEMBER_COUNT == 1
    assert P01_EXACT_MEMBER_IDENTITY_SET == MEMBER_ID
    assert P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT is True
    assert P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT == "NONE"
    assert P01_RUNTIME_INSTANCE_PRESENT is False


def test_object_is_immutable() -> None:
    contract = _contract()
    with pytest.raises(FrozenInstanceError):
        contract.p01_term_set_resolved_status = "false"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = _contract()
    second = _contract()
    assert first.provenance_digest == second.provenance_digest


def test_identity_does_not_close_term_semantics_or_algebra() -> None:
    contract = _contract()
    assert contract.identity_does_not_close_p01_term_semantics == "true"
    assert contract.identity_does_not_close_haircut_reserve_depletion_unspecified == "true"
    assert contract.identity_does_not_authorize_arithmetic == "true"
    assert P01_TERM_SEMANTICS_RESOLVED is True
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_APPLICABILITY_RESOLVED is True
    assert P01_MEMBER_ROLE_SIGN_UNIT_RESOLVED is True
    assert P01_ZERO_ABSENCE_NA_RESOLVED is True
    assert P01_COMBINATION_PRECEDENCE_RESOLVED is True
    assert "P01_TERM_SET_UNSPECIFIED" not in contract.remaining_unresolved_semantics
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS


def test_negative_aliases_are_rejected() -> None:
    contract = _contract()
    assert (
        contract.p01m_governed_deployability_conservatism_reduction_is_not_haircut_alias == "true"
    )
    assert contract.p01m_governed_deployability_conservatism_reduction_is_not_u04 == "true"
    assert contract.p01m_governed_deployability_conservatism_reduction_is_not_venue_raw == "true"
    assert contract.p01m_governed_deployability_conservatism_reduction_is_not_availeq == "true"
    assert (
        contract.p01m_governed_deployability_conservatism_reduction_is_not_future_fee_permission
        == ("true")
    )
    for inferred in ("HAIRCUT", "U04", "availEq", "margin reserve", "EMPTY"):
        with pytest.raises(P01ExactMemberIdentityContractError) as raised:
            reject_p01_inferred_member_identity_v1(member_id=inferred)
        assert "P01_MEMBER_IDENTITY_INFERRED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01ExactMemberIdentityContractError) as formula:
        reject_p01_identity_as_formula_v1(formula="EQUITY_BASE_MINUS_RESERVE")
    assert "P01_IDENTITY_IS_NOT_FORMULA" in str(formula.value)
    with pytest.raises(P01ExactMemberIdentityContractError) as extra:
        build_p01_exact_member_identity_contract_v1(
            p01_exact_member_identity_contract_id="SYNTHETIC_P01_EXACT_MEMBER_IDENTITY_CONTRACT_ID",
            member_id="HAIRCUT",
        )
    assert "P01_MEMBER_IDENTITY_INFERRED_FORBIDDEN" in str(
        extra.value
    ) or "P01_MEMBER_ID_MISMATCH" in str(extra.value)


def test_missing_and_malformed_inputs_fail_closed() -> None:
    with pytest.raises(P01ExactMemberIdentityContractError) as missing:
        build_p01_exact_member_identity_contract_v1(
            p01_exact_member_identity_contract_id="SYNTHETIC_P01_EXACT_MEMBER_IDENTITY_CONTRACT_ID",
            member_id=None,
        )
    assert "P01_FIELD_MISSING:member_id" in str(missing.value)
    with pytest.raises(P01ExactMemberIdentityContractError) as malformed:
        build_p01_exact_member_identity_contract_v1(
            p01_exact_member_identity_contract_id="SYNTHETIC_P01_EXACT_MEMBER_IDENTITY_CONTRACT_ID",
            member_id=False,
        )
    assert "P01_FIELD_NOT_STRING:member_id" in str(malformed.value)


def test_gap_dag_and_live_pins_remain_fail_closed() -> None:
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_EXACT_MEMBER_COUNT"] == 1
    assert dag["P01_EXACT_MEMBER_IDENTITY_SET"] == MEMBER_ID
    assert dag["P01_EXACT_MEMBER_IDENTITY_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_EXACT_MEMBER_IDENTITY_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert dag["P01_TERM_SEMANTICS_RESOLVED"] is True
    assert dag["P01_RUNTIME_INSTANCE_PRESENT"] is False
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ak_consumes_go_without_rewriting_aj() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ak_section = _ak_section()
    aj_start = runbook.index(AJ_HEADING)
    aj_section = runbook[aj_start : runbook.index(AK_HEADING, aj_start)]
    assert "P01_HAIRCUT_RESERVE_DEPLETION_SEMANTICS_CONTRACT_SCHEMA_PRESENT=true" in aj_section
    assert "THIS_SLICE=11.2.1.AK" not in aj_section
    assert "P01_TERM_SET_RESOLVED=false" in aj_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_EXACT_MEMBER_IDENTITY_RATIFICATION_V1"
        in ak_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ak_section
    assert "P01_EXACT_MEMBER_IDENTITY_CONTRACT_SCHEMA_PRESENT=true" in ak_section
    assert "P01_TERM_SET_RESOLVED=true" in ak_section
    assert "P01M_GOVERNED_DEPLOYABILITY_CONSERVATISM_REDUCTION" in ak_section
    assert "P01_EXACT_MEMBER_COUNT=1" in ak_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ak_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ak_section
    assert "P01_RUNTIME_INSTANCE_PRESENT=false" in ak_section
    assert "P01_AUTHORITY_EFFECT=NONE" in ak_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ak_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ak_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ak_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ak_section
    )
    assert "EARLIEST_NARROW_P01_DEPENDENCY=P01_VALUE_UNIT_CLASS_UNSPECIFIED" in ak_section
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_EXACT_MEMBER_IDENTITY_CONTRACT_V1" in spec
    assert "P01_TERM_SET_RESOLVED=true" in spec
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in spec
