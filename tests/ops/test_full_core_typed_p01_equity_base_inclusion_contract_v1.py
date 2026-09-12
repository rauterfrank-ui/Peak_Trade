"""Typed P01 equity-base inclusion adjudication contract. No productive reconstruction."""

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
    P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_equity_base_inclusion_contract_v1 import (
    EVIDENCE_CLASSIFICATION,
    P01_EQUITY_BASE_INCLUSION_ADJUDICATION,
    P01_EQUITY_BASE_INCLUSION_RULE,
    P01_EQUITY_BASE_INCLUSION_STATUS,
    REJECTED_INCLUSION_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    TYPED_INCLUSION_STATE,
    TYPED_INCLUSION_STATE_CONDITIONAL,
    TYPED_INCLUSION_STATE_EXCLUDED,
    TYPED_INCLUSION_STATE_INCLUDED,
    TYPED_INCLUSION_STATE_INDEPENDENT,
    TYPED_INCLUSION_STATE_PARTIAL,
    TYPED_INCLUSION_STATE_UNKNOWN,
    P01EquityBaseInclusionContractError,
    P01EquityBaseInclusionContractV1,
    build_p01_equity_base_inclusion_contract_v1,
    reject_p01_inclusion_inferred_from_u04_u05_u06_schema_or_venue_v1,
    reject_p01_unknown_inclusion_as_excluded_v1,
    reject_p01_unknown_inclusion_as_subtraction_or_omission_v1,
    reject_p01_zero_or_absence_as_embedded_or_excluded_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    EMBEDDED_STATE,
    INCLUSION_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    INCLUSION_IN_BASE,
    INCLUSION_NOT_APPLICABLE,
    INCLUSION_NOT_IN_BASE,
    INCLUSION_UNRESOLVED,
    NUMERIC_PRESENT_ZERO,
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_PENDING_ORDER_RESERVATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_EQUITY_BASE_INCLUSION_CONTRACT_V1.md"
AD_HEADING = "11.2.1.AD FULL_CORE_TYPED_P01_APPLICABILITY_CONTRACT"
AE_HEADING = "11.2.1.AE FULL_CORE_TYPED_P01_EQUITY_BASE_INCLUSION_CONTRACT"
AF_HEADING = "11.2.1.AF FULL_CORE_TYPED_P01_EMBEDDING_STATE_CONTRACT"


def _ae_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ae_start = runbook.index(AE_HEADING)
    return runbook[ae_start : runbook.index(AF_HEADING, ae_start)]


def test_p01_equity_base_inclusion_contract_constructs() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert isinstance(contract, P01EquityBaseInclusionContractV1)
    assert SCHEMA_CLASS == "P01_EQUITY_BASE_INCLUSION_CONTRACT_V1"
    assert contract.p01_equity_base_inclusion_status == INCLUSION_STATE
    assert contract.p01_equity_base_inclusion_status == P01_EQUITY_BASE_INCLUSION_STATUS
    assert contract.p01_equity_base_inclusion_status == INCLUSION_UNRESOLVED
    assert contract.p01_equity_base_inclusion_rule == P01_EQUITY_BASE_INCLUSION_RULE
    assert contract.p01_equity_base_inclusion_adjudication == P01_EQUITY_BASE_INCLUSION_ADJUDICATION
    assert contract.p01_equity_base_inclusion_resolved_status == "false"
    assert contract.typed_inclusion_state == TYPED_INCLUSION_STATE_UNKNOWN
    assert P01_EQUITY_BASE_INCLUSION_RESOLVED is False
    assert P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT is True
    assert P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_equity_base_inclusion_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    second = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_unknown_inclusion_remains_unresolved_not_excluded() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.p01_equity_base_inclusion_status == "UNRESOLVED"
    assert contract.typed_inclusion_state == TYPED_INCLUSION_STATE
    assert contract.typed_inclusion_state != TYPED_INCLUSION_STATE_INCLUDED
    assert contract.typed_inclusion_state != TYPED_INCLUSION_STATE_EXCLUDED
    assert contract.typed_inclusion_state != TYPED_INCLUSION_STATE_INDEPENDENT
    assert contract.unknown_is_not_excluded == "true"
    with pytest.raises(P01EquityBaseInclusionContractError) as raised:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_status=INCLUSION_NOT_IN_BASE,
        )
    assert "P01_UNKNOWN_INCLUSION_AUTO_EXCLUDED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as helper:
        reject_p01_unknown_inclusion_as_excluded_v1(inclusion_status=INCLUSION_NOT_IN_BASE)
    assert "P01_UNKNOWN_INCLUSION_AUTO_EXCLUDED_FORBIDDEN" in str(helper.value)


def test_missing_input_cannot_become_excluded() -> None:
    with pytest.raises(P01EquityBaseInclusionContractError) as missing:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_status=None,
        )
    assert "P01_FIELD_MISSING:p01_equity_base_inclusion_status" in str(missing.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as empty:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_status="",
        )
    assert "P01_FIELD_MISSING:p01_equity_base_inclusion_status" in str(empty.value)


def test_malformed_input_cannot_become_excluded() -> None:
    with pytest.raises(P01EquityBaseInclusionContractError) as not_string:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_status=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_equity_base_inclusion_status" in str(not_string.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as numeric:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_status=0,
        )
    assert "P01_FIELD_NOT_STRING:p01_equity_base_inclusion_status" in str(numeric.value)


def test_zero_cannot_imply_embedded_or_excluded() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.zero_is_not_embedded_or_excluded == "true"
    for inferred in ("0", "ZERO", NUMERIC_PRESENT_ZERO):
        with pytest.raises(P01EquityBaseInclusionContractError) as raised:
            build_p01_equity_base_inclusion_contract_v1(
                p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
                p01_equity_base_inclusion_status=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_INCLUSION_FORBIDDEN" in str(
            raised.value
        ) or "P01_INCLUSION_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as helper:
        reject_p01_zero_or_absence_as_embedded_or_excluded_v1(inclusion_status="0")
    assert "P01_ZERO_OR_ABSENCE_INCLUSION_FORBIDDEN" in str(helper.value)


def test_absence_cannot_imply_not_embedded() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.absence_is_not_not_embedded == "true"
    for inferred in ("ABSENT", "MISSING", "NONE"):
        with pytest.raises(P01EquityBaseInclusionContractError) as raised:
            build_p01_equity_base_inclusion_contract_v1(
                p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
                p01_equity_base_inclusion_status=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_INCLUSION_FORBIDDEN" in str(raised.value)


def test_term_set_applicability_and_unit_unresolved_do_not_decide_inclusion() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_APPLICABILITY_RESOLVED is False
    assert contract.term_set_unresolved_does_not_decide_inclusion == "true"
    assert contract.applicability_unresolved_does_not_decide_inclusion == "true"
    assert contract.unit_unresolved_does_not_decide_inclusion == "true"
    assert contract.p01_equity_base_inclusion_resolved_status == "false"
    with pytest.raises(P01EquityBaseInclusionContractError) as resolved:
        build_p01_equity_base_inclusion_contract_v1(
            p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
            p01_equity_base_inclusion_resolved_status="true",
        )
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED_FORBIDDEN" in str(resolved.value)


def test_u04_u05_u06_schema_and_venue_raw_cannot_decide_inclusion() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.separate_schema_does_not_prove_independent_deduction == "true"
    for inferred in (
        "U04",
        "U05",
        "U06",
        TERM_PENDING_ORDER_RESERVATION,
        TERM_LIABILITY,
        TERM_FEE,
        TERM_EQUITY_BASE,
        "SEPARATE_SCHEMA_FIELD",
        "frozenBal",
        "ordFrozen",
        "availEq",
        "totalEq",
    ):
        with pytest.raises(P01EquityBaseInclusionContractError) as raised:
            build_p01_equity_base_inclusion_contract_v1(
                p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
                p01_equity_base_inclusion_rule=inferred,
            )
        assert "P01_INCLUSION_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as helper:
        reject_p01_inclusion_inferred_from_u04_u05_u06_schema_or_venue_v1(inclusion_rule="U04")
    assert "P01_INCLUSION_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_candidate_inclusion_states_remain_unproven() -> None:
    for inferred in (
        TYPED_INCLUSION_STATE_INCLUDED,
        TYPED_INCLUSION_STATE_EXCLUDED,
        TYPED_INCLUSION_STATE_CONDITIONAL,
        TYPED_INCLUSION_STATE_PARTIAL,
        TYPED_INCLUSION_STATE_INDEPENDENT,
        INCLUSION_IN_BASE,
        INCLUSION_NOT_IN_BASE,
        INCLUSION_NOT_APPLICABLE,
        "REDUCTION_ONLY",
        "SAFE",
    ):
        with pytest.raises(P01EquityBaseInclusionContractError) as raised:
            build_p01_equity_base_inclusion_contract_v1(
                p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID",
                p01_equity_base_inclusion_rule=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_INCLUSION_INFERRED_FROM_LABEL_FORBIDDEN" in message
            or "P01_UNKNOWN_INCLUSION_AUTO_EXCLUDED_FORBIDDEN" in message
            or "P01_EQUITY_BASE_INCLUSION_CANDIDATE_UNPROVEN" in message
        )


def test_unknown_inclusion_cannot_authorize_subtraction_or_omission() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.unknown_inclusion_cannot_authorize_subtraction == "true"
    assert contract.unknown_inclusion_cannot_authorize_omission == "true"
    assert contract.no_double_counting_permission == "true"
    with pytest.raises(P01EquityBaseInclusionContractError) as subtract:
        reject_p01_unknown_inclusion_as_subtraction_or_omission_v1(
            inclusion_status=INCLUSION_UNRESOLVED,
            requested_action="SUBTRACT",
        )
    assert "P01_UNKNOWN_INCLUSION_SUBTRACTION_OR_OMISSION_FORBIDDEN" in str(subtract.value)
    with pytest.raises(P01EquityBaseInclusionContractError) as omit:
        reject_p01_unknown_inclusion_as_subtraction_or_omission_v1(
            inclusion_status=INCLUSION_UNRESOLVED,
            requested_action="OMIT",
        )
    assert "P01_UNKNOWN_INCLUSION_SUBTRACTION_OR_OMISSION_FORBIDDEN" in str(omit.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_equity_base_inclusion_contract_v1(
        p01_equity_base_inclusion_contract_id="SYNTHETIC_P01_EQUITY_BASE_INCLUSION_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_EQUITY_BASE_INCLUSION_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert "P01_APPLICABILITY_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_TERM_SET_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert EMBEDDED_STATE == "UNRESOLVED"
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_inclusion_inferences == REJECTED_INCLUSION_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_EQUITY_BASE_INCLUSION_RESOLVED"] is False
    assert dag["P01_APPLICABILITY_RESOLVED"] is False
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is True
    assert dag["P01_EQUITY_BASE_INCLUSION_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_EQUITY_BASE_INCLUSION_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ae_consumes_go_without_rewriting_ad() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ae_section = _ae_section()
    ad_start = runbook.index(AD_HEADING)
    ad_section = runbook[ad_start : runbook.index(AE_HEADING, ad_start)]
    assert "P01_APPLICABILITY_CONTRACT_SCHEMA_PRESENT=true" in ad_section
    assert "THIS_SLICE=11.2.1.AE" not in ad_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_EQUITY_BASE_INCLUSION_CONTRACT_V1" in ae_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ae_section
    assert "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT=true" in ae_section
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in ae_section
    assert "P01_EQUITY_BASE_INCLUSION_STATUS=UNRESOLVED" in ae_section
    assert "P01_APPLICABILITY_RESOLVED=false" in ae_section
    assert "P01_TERM_SET_RESOLVED=false" in ae_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ae_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ae_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ae_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ae_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ae_section
    assert "SOURCE_SELECTED=false" in ae_section
    assert "MAPPING_PROVEN=false" in ae_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ae_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_EQUITY_BASE_INCLUSION_CONTRACT_V1" in spec
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in spec
    assert "P01_APPLICABILITY_RESOLVED=false" in spec
    assert "P01_TERM_SET_RESOLVED=false" in spec
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in spec
