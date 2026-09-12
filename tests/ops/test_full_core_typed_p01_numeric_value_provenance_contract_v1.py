"""Typed P01 numeric value provenance adjudication. No productive reconstruction."""

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
    P01_EMBEDDED_STATE_RESOLVED,
    P01_EQUITY_BASE_INCLUSION_RESOLVED,
    P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT,
    P01_NUMERIC_VALUE_PROVENANCE_RESOLVED,
    P01_TERM_SEMANTICS_RESOLVED,
    P01_TERM_SET_RESOLVED,
    P01_U04_OVERLAP_RESOLVED,
    P01_U05_OVERLAP_RESOLVED,
    P01_VALUE_UNIT_CLASS_RESOLVED,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SOURCE_SELECTED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_DECOMPOSED_CONTRACT_GAP,
    live_admission_gap_dag_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_numeric_value_provenance_contract_v1 import (
    CANDIDATE_SOURCES_CLASSIFICATION,
    EVIDENCE_CLASSIFICATION,
    P01_NUMERIC_VALUE_PROVENANCE_STATUS,
    P01_NUMERIC_VALUE_SOURCE,
    P01_NUMERIC_VALUE_TRANSFORMATION,
    PRODUCER_STATE,
    REJECTED_PROVENANCE_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    TYPED_PROVENANCE_CLASS,
    TYPED_PROVENANCE_CLASS_ACCOUNTING_DERIVED,
    TYPED_PROVENANCE_CLASS_COMPOSITE,
    TYPED_PROVENANCE_CLASS_CONFIGURATION_DERIVED,
    TYPED_PROVENANCE_CLASS_INTERNALLY_RECONSTRUCTED,
    TYPED_PROVENANCE_CLASS_LEDGER_DERIVED,
    TYPED_PROVENANCE_CLASS_POLICY_DERIVED,
    TYPED_PROVENANCE_CLASS_RISK_MODEL_DERIVED,
    TYPED_PROVENANCE_CLASS_UNKNOWN,
    TYPED_PROVENANCE_CLASS_VENUE_NATIVE,
    P01NumericValueProvenanceContractError,
    P01NumericValueProvenanceContractV1,
    build_p01_numeric_value_provenance_contract_v1,
    reject_p01_haircut_unspecified_as_numeric_construction_v1,
    reject_p01_name_similarity_or_equality_as_source_v1,
    reject_p01_unspecified_provenance_as_arithmetic_v1,
    reject_p01_unspecified_provenance_as_numeric_authorization_v1,
    reject_p01_venue_field_as_numeric_source_v1,
    reject_p01_zero_as_numeric_value_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    NUMERIC_NOT_COMPUTED,
    NUMERIC_PRESENT_ZERO,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1.md"
AG_HEADING = "11.2.1.AG FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT"
AH_HEADING = "11.2.1.AH FULL_CORE_TYPED_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT"
AI_HEADING = "11.2.1.AI FULL_CORE_TYPED_P01_MEMBER_FRESHNESS_INHERITANCE_CONTRACT"


def _ah_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ah_start = runbook.index(AH_HEADING)
    return runbook[ah_start : runbook.index(AI_HEADING, ah_start)]


def test_p01_numeric_provenance_contract_constructs() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert isinstance(contract, P01NumericValueProvenanceContractV1)
    assert SCHEMA_CLASS == "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1"
    assert contract.p01_numeric_value_provenance_status == P01_NUMERIC_VALUE_PROVENANCE_STATUS
    assert contract.p01_numeric_value_provenance_status == "UNSPECIFIED"
    assert contract.p01_numeric_value_source == P01_NUMERIC_VALUE_SOURCE
    assert contract.p01_numeric_value_source == "UNSPECIFIED"
    assert contract.p01_numeric_value_transformation == P01_NUMERIC_VALUE_TRANSFORMATION
    assert contract.p01_numeric_value_transformation == "UNSPECIFIED"
    assert contract.typed_provenance_class == TYPED_PROVENANCE_CLASS
    assert contract.typed_provenance_class == TYPED_PROVENANCE_CLASS_UNKNOWN
    assert contract.p01_numeric_value_provenance_resolved_status == "false"
    assert contract.producer_state == PRODUCER_STATE
    assert P01_NUMERIC_VALUE_PROVENANCE_RESOLVED is False
    assert P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT is True
    assert P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_numeric_value_provenance_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    second = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_unspecified_provenance_is_not_numeric_authorization() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.unknown_is_not_numeric_authorization == "true"
    assert contract.unspecified_is_not_numeric_authorization == "true"
    assert contract.typed_provenance_class != TYPED_PROVENANCE_CLASS_VENUE_NATIVE
    with pytest.raises(P01NumericValueProvenanceContractError) as raised:
        build_p01_numeric_value_provenance_contract_v1(
            p01_numeric_value_provenance_contract_id=(
                "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
            ),
            p01_numeric_value_provenance_resolved_status="true",
        )
    assert "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01NumericValueProvenanceContractError) as helper:
        reject_p01_unspecified_provenance_as_numeric_authorization_v1(
            provenance_status="UNSPECIFIED"
        )
    assert "P01_UNSPECIFIED_NUMERIC_AUTHORIZATION_FORBIDDEN" in str(helper.value)


def test_missing_input_cannot_become_a_p01_value() -> None:
    with pytest.raises(P01NumericValueProvenanceContractError) as missing:
        build_p01_numeric_value_provenance_contract_v1(
            p01_numeric_value_provenance_contract_id=(
                "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
            ),
            p01_numeric_value_source=None,
        )
    assert "P01_FIELD_MISSING:p01_numeric_value_source" in str(missing.value)
    with pytest.raises(P01NumericValueProvenanceContractError) as empty:
        build_p01_numeric_value_provenance_contract_v1(
            p01_numeric_value_provenance_contract_id=(
                "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
            ),
            p01_numeric_value_source="",
        )
    assert "P01_FIELD_MISSING:p01_numeric_value_source" in str(empty.value)


def test_malformed_input_cannot_become_a_p01_value() -> None:
    with pytest.raises(P01NumericValueProvenanceContractError) as not_string:
        build_p01_numeric_value_provenance_contract_v1(
            p01_numeric_value_provenance_contract_id=(
                "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
            ),
            p01_numeric_value_source=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_numeric_value_source" in str(not_string.value)
    with pytest.raises(P01NumericValueProvenanceContractError) as numeric:
        build_p01_numeric_value_provenance_contract_v1(
            p01_numeric_value_provenance_contract_id=(
                "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
            ),
            p01_numeric_value_source=0,
        )
    assert "P01_FIELD_NOT_STRING:p01_numeric_value_source" in str(numeric.value)


def test_zero_is_not_a_p01_value() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.zero_is_not_p01_value == "true"
    assert contract.absence_is_not_p01_value == "true"
    for inferred in ("0", "ZERO", NUMERIC_PRESENT_ZERO):
        with pytest.raises(P01NumericValueProvenanceContractError) as raised:
            build_p01_numeric_value_provenance_contract_v1(
                p01_numeric_value_provenance_contract_id=(
                    "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
                ),
                p01_numeric_value_source=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_VALUE_FORBIDDEN" in str(
            raised.value
        ) or "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01NumericValueProvenanceContractError) as helper:
        reject_p01_zero_as_numeric_value_v1(numeric_state="0")
    assert "P01_ZERO_OR_ABSENCE_VALUE_FORBIDDEN" in str(helper.value)


def test_venue_fields_are_not_p01_numeric_sources() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.venue_field_is_not_p01_value == "true"
    for inferred in (
        "availEq",
        "details.availEq",
        "totalEq",
        "eq",
        "adjEq",
        "cashBal",
        "upl",
        NUMERIC_NOT_COMPUTED,
    ):
        with pytest.raises(P01NumericValueProvenanceContractError) as raised:
            build_p01_numeric_value_provenance_contract_v1(
                p01_numeric_value_provenance_contract_id=(
                    "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
                ),
                p01_numeric_value_source=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in message
            or "P01_NUMERIC_VALUE_SOURCE_MISMATCH" in message
            or "P01_ZERO_OR_ABSENCE_VALUE_FORBIDDEN" in message
        )
    with pytest.raises(P01NumericValueProvenanceContractError) as helper:
        reject_p01_venue_field_as_numeric_source_v1(source="availEq")
    assert "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in str(helper.value)


def test_name_similarity_and_equality_do_not_prove_source() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.name_similarity_does_not_prove_source == "true"
    assert contract.numeric_equality_does_not_prove_source == "true"
    assert contract.policy_slot_is_not_numeric_source == "true"
    assert contract.algebra_slot_is_not_numeric_source == "true"
    for inferred in ("EQUAL_VALUE", "SHARED_SOURCE", "P01_STATUS_DECIDED"):
        with pytest.raises(P01NumericValueProvenanceContractError) as raised:
            build_p01_numeric_value_provenance_contract_v1(
                p01_numeric_value_provenance_contract_id=(
                    "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
                ),
                p01_numeric_value_source=inferred,
            )
        assert "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in str(
            raised.value
        ) or "P01_NUMERIC_VALUE_SOURCE_MISMATCH" in str(raised.value)
    with pytest.raises(P01NumericValueProvenanceContractError) as helper:
        reject_p01_name_similarity_or_equality_as_source_v1(source_rule="EQUAL_VALUE")
    assert "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in str(
        helper.value
    ) or "P01_NUMERIC_VALUE_SOURCE_MISMATCH" in str(helper.value)


def test_candidate_provenance_classes_remain_unproven() -> None:
    for inferred in (
        TYPED_PROVENANCE_CLASS_VENUE_NATIVE,
        TYPED_PROVENANCE_CLASS_INTERNALLY_RECONSTRUCTED,
        TYPED_PROVENANCE_CLASS_POLICY_DERIVED,
        TYPED_PROVENANCE_CLASS_CONFIGURATION_DERIVED,
        TYPED_PROVENANCE_CLASS_RISK_MODEL_DERIVED,
        TYPED_PROVENANCE_CLASS_LEDGER_DERIVED,
        TYPED_PROVENANCE_CLASS_ACCOUNTING_DERIVED,
        TYPED_PROVENANCE_CLASS_COMPOSITE,
    ):
        with pytest.raises(P01NumericValueProvenanceContractError) as raised:
            build_p01_numeric_value_provenance_contract_v1(
                p01_numeric_value_provenance_contract_id=(
                    "SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
                ),
                typed_provenance_class=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_NUMERIC_SOURCE_INFERRED_FORBIDDEN" in message
            or "P01_TYPED_PROVENANCE_CLASS_UNPROVEN" in message
        )


def test_unspecified_haircut_cannot_construct_p01() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.unspecified_haircut_cannot_construct_p01 == "true"
    assert (
        contract.haircut_reserve_depletion_construction_state
        == "NOT_ANTICIPATED_UNSPECIFIED_FAIL_CLOSED"
    )
    with pytest.raises(P01NumericValueProvenanceContractError) as helper:
        reject_p01_haircut_unspecified_as_numeric_construction_v1(
            construction_state="NOT_ANTICIPATED_UNSPECIFIED_FAIL_CLOSED"
        )
    assert "P01_UNSPECIFIED_HAIRCUT_CONSTRUCTION_FORBIDDEN" in str(helper.value)


def test_unspecified_provenance_cannot_authorize_arithmetic() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.unspecified_cannot_authorize_subtraction == "true"
    assert contract.unspecified_cannot_authorize_addition == "true"
    assert contract.unspecified_cannot_authorize_netting == "true"
    assert contract.unspecified_cannot_authorize_omission == "true"
    assert contract.unspecified_cannot_authorize_ignore == "true"
    for action in ("ADD", "SUBTRACT", "NET", "OMIT", "IGNORE"):
        with pytest.raises(P01NumericValueProvenanceContractError) as raised:
            reject_p01_unspecified_provenance_as_arithmetic_v1(
                provenance_status="UNSPECIFIED",
                requested_action=action,
            )
        assert "P01_UNSPECIFIED_PROVENANCE_ARITHMETIC_FORBIDDEN" in str(raised.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_numeric_value_provenance_contract_v1(
        p01_numeric_value_provenance_contract_id="SYNTHETIC_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_provenance_inferences == REJECTED_PROVENANCE_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    assert "NO_WINNER_RATIFIED=true" in CANDIDATE_SOURCES_CLASSIFICATION
    assert "REJECTED" in contract.candidate_sources_classification
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_NUMERIC_VALUE_PROVENANCE_RESOLVED"] is False
    assert dag["P01_U04_OVERLAP_RESOLVED"] is False
    assert dag["P01_U05_OVERLAP_RESOLVED"] is False
    assert dag["P01_EMBEDDED_STATE_RESOLVED"] is False
    assert dag["P01_EQUITY_BASE_INCLUSION_RESOLVED"] is False
    assert dag["P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ah_consumes_go_without_rewriting_ag() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ah_section = _ah_section()
    ag_start = runbook.index(AG_HEADING)
    ag_section = runbook[ag_start : runbook.index(AH_HEADING, ag_start)]
    assert "P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT=true" in ag_section
    assert "THIS_SLICE=11.2.1.AH" not in ag_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1"
        in ah_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ah_section
    assert "P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_SCHEMA_PRESENT=true" in ah_section
    assert "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED=false" in ah_section
    assert "P01_NUMERIC_VALUE_PROVENANCE_STATUS=UNSPECIFIED" in ah_section
    assert "P01_NUMERIC_VALUE_SOURCE=UNSPECIFIED" in ah_section
    assert "P01_NUMERIC_VALUE_TRANSFORMATION=UNSPECIFIED" in ah_section
    assert "P01_U04_OVERLAP_RESOLVED=false" in ah_section
    assert "P01_U05_OVERLAP_RESOLVED=false" in ah_section
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in ah_section
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in ah_section
    assert "P01_APPLICABILITY_RESOLVED=false" in ah_section
    assert "P01_TERM_SET_RESOLVED=false" in ah_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ah_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ah_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ah_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ah_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ah_section
    assert "SOURCE_SELECTED=false" in ah_section
    assert "MAPPING_PROVEN=false" in ah_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ah_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_NUMERIC_VALUE_PROVENANCE_CONTRACT_V1" in spec
    assert "P01_NUMERIC_VALUE_PROVENANCE_RESOLVED=false" in spec
    assert "P01_NUMERIC_VALUE_SOURCE=UNSPECIFIED" in spec
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_EQUITY_BASE_INCLUSION_RESOLVED is False
    assert P01_EMBEDDED_STATE_RESOLVED is False
    assert P01_U04_OVERLAP_RESOLVED is False
    assert P01_U05_OVERLAP_RESOLVED is False
