"""Typed P01 overlap/equivalence adjudication versus U04 and U05. No productive reconstruction."""

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
    P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_embedding_state_contract_v1 import (
    P01_OVERLAP_STATE as PARENT_AF_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    EVIDENCE_CLASSIFICATION,
    P01_OVERLAP_STATE,
    P01_U04_OVERLAP_ADJUDICATION,
    P01_U04_OVERLAP_STATE,
    P01_U05_OVERLAP_ADJUDICATION,
    P01_U05_OVERLAP_STATE,
    REJECTED_OVERLAP_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    TYPED_OVERLAP_STATE_APPLICABILITY_DEPENDENT,
    TYPED_OVERLAP_STATE_DISJOINT,
    TYPED_OVERLAP_STATE_EQUIVALENT,
    TYPED_OVERLAP_STATE_FULLY_OVERLAPPING,
    TYPED_OVERLAP_STATE_MEMBER_DEPENDENT,
    TYPED_OVERLAP_STATE_P01_CONTAINS_U04,
    TYPED_OVERLAP_STATE_P01_CONTAINS_U05,
    TYPED_OVERLAP_STATE_PARTIALLY_OVERLAPPING,
    TYPED_OVERLAP_STATE_U04_CONTAINS_P01,
    TYPED_OVERLAP_STATE_U05_CONTAINS_P01,
    TYPED_OVERLAP_STATE_UNKNOWN,
    P01OverlapWithU04U05ContractError,
    P01OverlapWithU04U05ContractV1,
    build_p01_overlap_with_u04_u05_contract_v1,
    reject_p01_equal_values_or_shared_source_as_equivalence_v1,
    reject_p01_u04_u05_labels_as_overlap_v1,
    reject_p01_u06_distinctness_as_p01_u06_relation_v1,
    reject_p01_unknown_overlap_as_arithmetic_v1,
    reject_p01_unknown_overlap_as_disjoint_v1,
    reject_p01_zero_or_absence_as_non_overlap_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    NUMERIC_PRESENT_ZERO,
    TERM_LIABILITY,
    TERM_PENDING_ORDER_RESERVATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT_V1.md"
AF_HEADING = "11.2.1.AF FULL_CORE_TYPED_P01_EMBEDDING_STATE_CONTRACT"
AG_HEADING = "11.2.1.AG FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT"


def _ag_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    ag_start = runbook.index(AG_HEADING)
    return runbook[ag_start : runbook.index("## 11.3 Autonomy state model", ag_start)]


def test_p01_overlap_contract_constructs() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert isinstance(contract, P01OverlapWithU04U05ContractV1)
    assert SCHEMA_CLASS == "P01_OVERLAP_WITH_U04_U05_CONTRACT_V1"
    assert contract.p01_u04_overlap_state == P01_U04_OVERLAP_STATE
    assert contract.p01_u04_overlap_state == "UNRESOLVED"
    assert contract.p01_u04_overlap_adjudication == P01_U04_OVERLAP_ADJUDICATION
    assert contract.p01_u05_overlap_state == P01_U05_OVERLAP_STATE
    assert contract.p01_u05_overlap_state == "UNRESOLVED"
    assert contract.p01_u05_overlap_adjudication == P01_U05_OVERLAP_ADJUDICATION
    assert contract.typed_u04_overlap_state == TYPED_OVERLAP_STATE_UNKNOWN
    assert contract.typed_u05_overlap_state == TYPED_OVERLAP_STATE_UNKNOWN
    assert contract.p01_u04_overlap_resolved_status == "false"
    assert contract.p01_u05_overlap_resolved_status == "false"
    assert P01_U04_OVERLAP_RESOLVED is False
    assert P01_U05_OVERLAP_RESOLVED is False
    assert P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT is True
    assert P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_u04_overlap_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    second = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_unknown_u04_and_u05_overlap_remain_unresolved() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.unknown_is_not_disjoint == "true"
    assert contract.unknown_is_not_equivalent == "true"
    assert contract.unknown_is_not_non_overlapping == "true"
    assert contract.typed_u04_overlap_state != TYPED_OVERLAP_STATE_DISJOINT
    assert contract.typed_u04_overlap_state != TYPED_OVERLAP_STATE_EQUIVALENT
    assert contract.typed_u05_overlap_state != TYPED_OVERLAP_STATE_DISJOINT
    assert contract.typed_u05_overlap_state != TYPED_OVERLAP_STATE_EQUIVALENT
    with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u04_overlap_state=TYPED_OVERLAP_STATE_DISJOINT,
        )
    assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(
        raised.value
    ) or "P01_U04_OVERLAP_CANDIDATE_UNPROVEN" in str(raised.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as helper:
        reject_p01_unknown_overlap_as_disjoint_v1(overlap_state=TYPED_OVERLAP_STATE_DISJOINT)
    assert "P01_UNKNOWN_OVERLAP_AUTO_DISJOINT_FORBIDDEN" in str(
        helper.value
    ) or "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_missing_input_cannot_become_disjoint() -> None:
    with pytest.raises(P01OverlapWithU04U05ContractError) as missing:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u04_overlap_state=None,
        )
    assert "P01_FIELD_MISSING:p01_u04_overlap_state" in str(missing.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as empty:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u05_overlap_state="",
        )
    assert "P01_FIELD_MISSING:p01_u05_overlap_state" in str(empty.value)


def test_malformed_input_cannot_become_disjoint() -> None:
    with pytest.raises(P01OverlapWithU04U05ContractError) as not_string:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u04_overlap_state=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_u04_overlap_state" in str(not_string.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as numeric:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u05_overlap_state=0,
        )
    assert "P01_FIELD_NOT_STRING:p01_u05_overlap_state" in str(numeric.value)


def test_zero_does_not_prove_non_overlap() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.zero_does_not_prove_non_overlap == "true"
    for inferred in ("0", "ZERO", NUMERIC_PRESENT_ZERO):
        with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
            build_p01_overlap_with_u04_u05_contract_v1(
                p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
                p01_u04_overlap_state=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_OVERLAP_FORBIDDEN" in str(
            raised.value
        ) or "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as helper:
        reject_p01_zero_or_absence_as_non_overlap_v1(overlap_state="0")
    assert "P01_ZERO_OR_ABSENCE_OVERLAP_FORBIDDEN" in str(helper.value)


def test_equal_values_and_shared_source_or_unit_do_not_prove_equivalence() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.equal_values_do_not_prove_equivalence == "true"
    assert contract.shared_source_does_not_prove_equivalence == "true"
    assert contract.shared_unit_does_not_prove_equivalence == "true"
    for inferred in ("EQUAL_VALUE", "SHARED_SOURCE", "SHARED_UNIT"):
        with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
            build_p01_overlap_with_u04_u05_contract_v1(
                p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
                p01_u04_overlap_adjudication=inferred,
            )
        assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as helper:
        reject_p01_equal_values_or_shared_source_as_equivalence_v1(overlap_rule="EQUAL_VALUE")
    assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_unresolved_term_set_applicability_and_embedding_do_not_decide_overlap() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert P01_TERM_SET_RESOLVED is False
    assert P01_VALUE_UNIT_CLASS_RESOLVED is False
    assert P01_APPLICABILITY_RESOLVED is False
    assert P01_EMBEDDED_STATE_RESOLVED is False
    assert contract.term_set_unresolved_does_not_decide_overlap == "true"
    assert contract.applicability_unresolved_does_not_decide_overlap == "true"
    assert contract.embedding_unresolved_does_not_decide_overlap == "true"
    with pytest.raises(P01OverlapWithU04U05ContractError) as resolved:
        build_p01_overlap_with_u04_u05_contract_v1(
            p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
            p01_u04_overlap_resolved_status="true",
        )
    assert "P01_U04_OVERLAP_RESOLVED_FORBIDDEN" in str(resolved.value)


def test_u04_u05_labels_do_not_decide_overlap() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.u04_u05_labels_do_not_decide_overlap == "true"
    for inferred in (
        "U04",
        "U05",
        TERM_PENDING_ORDER_RESERVATION,
        TERM_LIABILITY,
        "SEPARATE_SCHEMA_FIELD",
        "ordFrozen",
    ):
        with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
            build_p01_overlap_with_u04_u05_contract_v1(
                p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
                p01_u05_overlap_adjudication=inferred,
            )
        assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01OverlapWithU04U05ContractError) as helper:
        reject_p01_u04_u05_labels_as_overlap_v1(overlap_rule="U04")
    assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_candidate_overlap_states_remain_unproven() -> None:
    for inferred in (
        TYPED_OVERLAP_STATE_EQUIVALENT,
        TYPED_OVERLAP_STATE_PARTIALLY_OVERLAPPING,
        TYPED_OVERLAP_STATE_FULLY_OVERLAPPING,
        TYPED_OVERLAP_STATE_DISJOINT,
        TYPED_OVERLAP_STATE_P01_CONTAINS_U04,
        TYPED_OVERLAP_STATE_U04_CONTAINS_P01,
        TYPED_OVERLAP_STATE_P01_CONTAINS_U05,
        TYPED_OVERLAP_STATE_U05_CONTAINS_P01,
        TYPED_OVERLAP_STATE_MEMBER_DEPENDENT,
        TYPED_OVERLAP_STATE_APPLICABILITY_DEPENDENT,
        "NON_OVERLAPPING",
        "SAFE_TO_SUM",
        "SAFE_TO_NET",
        "SAFE_TO_DEDUPLICATE",
    ):
        with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
            build_p01_overlap_with_u04_u05_contract_v1(
                p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID",
                p01_u05_overlap_state=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in message
            or "P01_U05_OVERLAP_CANDIDATE_UNPROVEN" in message
            or "P01_ZERO_OR_ABSENCE_OVERLAP_FORBIDDEN" in message
        )


def test_overlap_dimensions_remain_distinct_and_unresolved() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.semantic_equivalence_state == "UNRESOLVED"
    assert contract.economic_overlap_state == "UNRESOLVED"
    assert contract.representational_nesting_state == "UNRESOLVED"
    assert contract.shared_provenance_state == "UNRESOLVED"
    assert contract.shared_numeric_value_state == "UNRESOLVED"
    assert contract.shared_unit_state == "UNRESOLVED"
    assert contract.simultaneous_applicability_state == "UNRESOLVED"
    assert contract.arithmetic_interaction_state == "UNRESOLVED"
    assert contract.p01_overlap_state == P01_OVERLAP_STATE
    assert "U06_ACCRUED_FEES_DISTINCT" in contract.p01_overlap_state
    assert "P01_U04_OVERLAP_UNRESOLVED" in contract.p01_overlap_state
    assert "P01_U05_OVERLAP_UNRESOLVED" in contract.p01_overlap_state
    assert PARENT_AF_OVERLAP_STATE != contract.p01_overlap_state
    with pytest.raises(P01OverlapWithU04U05ContractError) as helper:
        reject_p01_u06_distinctness_as_p01_u06_relation_v1(overlap_rule="U06_ACCRUED_FEES_DISTINCT")
    assert "P01_OVERLAP_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_unknown_overlap_cannot_authorize_summation_or_deduplication() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.unknown_overlap_cannot_authorize_summation == "true"
    assert contract.unknown_overlap_cannot_authorize_deduplication == "true"
    assert contract.unknown_overlap_cannot_authorize_netting == "true"
    assert contract.unknown_overlap_cannot_authorize_subtraction == "true"
    assert contract.unknown_overlap_cannot_authorize_omission == "true"
    assert contract.no_double_counting_permission == "true"
    for action in ("SUM", "DEDUPLICATE", "NET", "SUBTRACT", "OMIT"):
        with pytest.raises(P01OverlapWithU04U05ContractError) as raised:
            reject_p01_unknown_overlap_as_arithmetic_v1(
                overlap_state="UNRESOLVED",
                requested_action=action,
            )
        assert "P01_UNKNOWN_OVERLAP_ARITHMETIC_FORBIDDEN" in str(raised.value)


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_overlap_with_u04_u05_contract_v1(
        p01_overlap_with_u04_u05_contract_id="SYNTHETIC_P01_OVERLAP_WITH_U04_U05_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert "P01_EMBEDDING_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert "P01_NUMERIC_VALUE_PROVENANCE_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert P01_TERM_SEMANTICS_RESOLVED is False
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_overlap_inferences == REJECTED_OVERLAP_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED"
    assert dag["P01_U04_OVERLAP_RESOLVED"] is False
    assert dag["P01_U05_OVERLAP_RESOLVED"] is False
    assert dag["P01_EMBEDDED_STATE_RESOLVED"] is False
    assert dag["P01_EQUITY_BASE_INCLUSION_RESOLVED"] is False
    assert dag["P01_OVERLAP_WITH_U04_U05_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_OVERLAP_WITH_U04_U05_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_ag_consumes_go_without_rewriting_af() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    ag_section = _ag_section()
    af_start = runbook.index(AF_HEADING)
    af_section = runbook[af_start : runbook.index(AG_HEADING, af_start)]
    assert "P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT=true" in af_section
    assert "THIS_SLICE=11.2.1.AG" not in af_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_OVERLAP_WITH_U04_U05_CONTRACT_V1" in ag_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in ag_section
    assert "P01_OVERLAP_WITH_U04_U05_CONTRACT_SCHEMA_PRESENT=true" in ag_section
    assert "P01_U04_OVERLAP_RESOLVED=false" in ag_section
    assert "P01_U04_OVERLAP_STATE=UNRESOLVED" in ag_section
    assert "P01_U05_OVERLAP_RESOLVED=false" in ag_section
    assert "P01_U05_OVERLAP_STATE=UNRESOLVED" in ag_section
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in ag_section
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in ag_section
    assert "P01_APPLICABILITY_RESOLVED=false" in ag_section
    assert "P01_TERM_SET_RESOLVED=false" in ag_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in ag_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in ag_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in ag_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in ag_section
    assert "CANONICAL_FORMULA_PROVEN=false" in ag_section
    assert "SOURCE_SELECTED=false" in ag_section
    assert "MAPPING_PROVEN=false" in ag_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in ag_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT_V1" in spec
    assert "P01_U04_OVERLAP_RESOLVED=false" in spec
    assert "P01_U05_OVERLAP_RESOLVED=false" in spec
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in spec
    assert "P01_TERM_SET_RESOLVED=false" in spec
