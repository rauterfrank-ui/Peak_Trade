"""Typed P01 broader embedding-state adjudication contract. No productive reconstruction."""

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
    P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT,
    P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT,
    P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_embedding_state_contract_v1 import (
    EVIDENCE_CLASSIFICATION,
    P01_EMBEDDED_STATE,
    P01_EMBEDDING_ADJUDICATION,
    P01_EMBEDDING_RULE,
    P01_OVERLAP_STATE,
    REJECTED_EMBEDDING_INFERENCES,
    REMAINING_UNRESOLVED_SEMANTICS,
    SCHEMA_CLASS,
    TYPED_EMBEDDING_STATE,
    TYPED_EMBEDDING_STATE_DEPENDS_ON_APPLICABILITY,
    TYPED_EMBEDDING_STATE_DEPENDS_ON_MEMBER_CLASS,
    TYPED_EMBEDDING_STATE_EMBEDDED_IN_ANOTHER_TERM,
    TYPED_EMBEDDING_STATE_EMBEDDED_IN_EQUITY_BASE,
    TYPED_EMBEDDING_STATE_EMBEDDED_IN_U04,
    TYPED_EMBEDDING_STATE_EMBEDDED_IN_U05,
    TYPED_EMBEDDING_STATE_EMBEDDED_IN_U06,
    TYPED_EMBEDDING_STATE_FULLY_EMBEDDED,
    TYPED_EMBEDDING_STATE_NOT_EMBEDDED,
    TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED,
    TYPED_EMBEDDING_STATE_UNKNOWN,
    P01EmbeddingStateContractError,
    P01EmbeddingStateContractV1,
    build_p01_embedding_state_contract_v1,
    reject_p01_embedding_inferred_from_u04_u05_u06_schema_or_venue_v1,
    reject_p01_equal_values_or_shared_source_as_embedding_v1,
    reject_p01_u06_distinctness_as_non_embedding_v1,
    reject_p01_unknown_embedding_as_not_embedded_v1,
    reject_p01_unknown_embedding_as_subtraction_omission_or_netting_v1,
    reject_p01_zero_or_absence_as_embedding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_haircut_reserve_depletion_term_contract_v1 import (
    EMBEDDED_STATE,
    INCLUSION_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EMBEDDED_NO,
    EMBEDDED_YES,
    NUMERIC_PRESENT_ZERO,
    TERM_EQUITY_BASE,
    TERM_FEE,
    TERM_LIABILITY,
    TERM_PENDING_ORDER_RESERVATION,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / "docs/ops/specs/FULL_CORE_TYPED_P01_EMBEDDING_STATE_CONTRACT_V1.md"
AE_HEADING = "11.2.1.AE FULL_CORE_TYPED_P01_EQUITY_BASE_INCLUSION_CONTRACT"
AF_HEADING = "11.2.1.AF FULL_CORE_TYPED_P01_EMBEDDING_STATE_CONTRACT"
AG_HEADING = "11.2.1.AG FULL_CORE_TYPED_P01_OVERLAP_WITH_U04_U05_CONTRACT"


def _af_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    af_start = runbook.index(AF_HEADING)
    return runbook[af_start : runbook.index(AG_HEADING, af_start)]


def test_p01_embedding_state_contract_constructs() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert isinstance(contract, P01EmbeddingStateContractV1)
    assert SCHEMA_CLASS == "P01_EMBEDDING_STATE_CONTRACT_V1"
    assert contract.p01_embedded_state == EMBEDDED_STATE
    assert contract.p01_embedded_state == P01_EMBEDDED_STATE
    assert contract.p01_embedded_state == "UNRESOLVED"
    assert contract.p01_embedding_rule == P01_EMBEDDING_RULE
    assert contract.p01_embedding_adjudication == P01_EMBEDDING_ADJUDICATION
    assert contract.p01_embedded_state_resolved_status == "false"
    assert contract.typed_embedding_state == TYPED_EMBEDDING_STATE_UNKNOWN
    assert P01_EMBEDDED_STATE_RESOLVED is True
    assert P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT is True
    assert P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT is False
    assert P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT == "NONE"


def test_object_is_immutable() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    with pytest.raises(FrozenInstanceError):
        contract.p01_embedded_state_resolved_status = "true"  # type: ignore[misc]


def test_digest_is_deterministic() -> None:
    first = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    second = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert first.provenance_digest == second.provenance_digest


def test_unknown_embedding_remains_unresolved_not_not_embedded() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.p01_embedded_state == "UNRESOLVED"
    assert contract.typed_embedding_state == TYPED_EMBEDDING_STATE
    assert contract.typed_embedding_state != TYPED_EMBEDDING_STATE_NOT_EMBEDDED
    assert contract.typed_embedding_state != TYPED_EMBEDDING_STATE_FULLY_EMBEDDED
    assert contract.typed_embedding_state != TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED
    assert contract.unknown_is_not_not_embedded == "true"
    assert contract.unknown_is_not_embedded == "true"
    with pytest.raises(P01EmbeddingStateContractError) as raised:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state=EMBEDDED_NO,
        )
    assert "P01_UNKNOWN_EMBEDDING_AUTO_NOT_EMBEDDED_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EmbeddingStateContractError) as helper:
        reject_p01_unknown_embedding_as_not_embedded_v1(embedded_state=EMBEDDED_NO)
    assert "P01_UNKNOWN_EMBEDDING_AUTO_NOT_EMBEDDED_FORBIDDEN" in str(helper.value)


def test_missing_input_cannot_become_not_embedded() -> None:
    with pytest.raises(P01EmbeddingStateContractError) as missing:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state=None,
        )
    assert "P01_FIELD_MISSING:p01_embedded_state" in str(missing.value)
    with pytest.raises(P01EmbeddingStateContractError) as empty:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state="",
        )
    assert "P01_FIELD_MISSING:p01_embedded_state" in str(empty.value)


def test_malformed_input_cannot_become_not_embedded() -> None:
    with pytest.raises(P01EmbeddingStateContractError) as not_string:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state=False,
        )
    assert "P01_FIELD_NOT_STRING:p01_embedded_state" in str(not_string.value)
    with pytest.raises(P01EmbeddingStateContractError) as numeric:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state=0,
        )
    assert "P01_FIELD_NOT_STRING:p01_embedded_state" in str(numeric.value)


def test_zero_cannot_imply_embedding_or_non_embedding() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.zero_does_not_prove_embedding == "true"
    for inferred in ("0", "ZERO", NUMERIC_PRESENT_ZERO):
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            build_p01_embedding_state_contract_v1(
                p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
                p01_embedded_state=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_EMBEDDING_FORBIDDEN" in str(
            raised.value
        ) or "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EmbeddingStateContractError) as helper:
        reject_p01_zero_or_absence_as_embedding_v1(embedded_state="0")
    assert "P01_ZERO_OR_ABSENCE_EMBEDDING_FORBIDDEN" in str(helper.value)


def test_absence_cannot_imply_embedding_or_non_embedding() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.absence_does_not_prove_embedding == "true"
    for inferred in ("ABSENT", "MISSING", "NONE"):
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            build_p01_embedding_state_contract_v1(
                p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
                p01_embedded_state=inferred,
            )
        assert "P01_ZERO_OR_ABSENCE_EMBEDDING_FORBIDDEN" in str(raised.value)


def test_unresolved_term_set_applicability_unit_and_inclusion_do_not_decide_embedding() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert P01_TERM_SET_RESOLVED is True
    assert P01_VALUE_UNIT_CLASS_RESOLVED is True
    assert P01_APPLICABILITY_RESOLVED is True
    assert P01_EQUITY_BASE_INCLUSION_RESOLVED is True
    assert INCLUSION_STATE == "UNRESOLVED"
    assert contract.term_set_unresolved_does_not_decide_embedding == "true"
    assert contract.applicability_unresolved_does_not_decide_embedding == "true"
    assert contract.unit_unresolved_does_not_decide_embedding == "true"
    assert contract.equity_base_inclusion_unresolved_does_not_decide_broader_embedding == "true"
    assert contract.p01_embedded_state_resolved_status == "false"
    with pytest.raises(P01EmbeddingStateContractError) as resolved:
        build_p01_embedding_state_contract_v1(
            p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
            p01_embedded_state_resolved_status="true",
        )
    assert "P01_EMBEDDED_STATE_RESOLVED_FORBIDDEN" in str(resolved.value)


def test_u04_u05_u06_schema_and_venue_raw_cannot_decide_embedding() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.u04_u05_u06_labels_do_not_decide_embedding == "true"
    assert contract.separate_schema_does_not_prove_independence == "true"
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
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            build_p01_embedding_state_contract_v1(
                p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
                p01_embedding_rule=inferred,
            )
        assert "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EmbeddingStateContractError) as helper:
        reject_p01_embedding_inferred_from_u04_u05_u06_schema_or_venue_v1(embedding_rule="U04")
    assert "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_equal_values_and_shared_source_do_not_prove_embedding() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.equal_values_do_not_prove_embedding == "true"
    assert contract.shared_source_does_not_prove_embedding == "true"
    for inferred in ("EQUAL_VALUE", "SHARED_SOURCE", "SHARED_PROVENANCE"):
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            build_p01_embedding_state_contract_v1(
                p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
                p01_embedding_rule=inferred,
            )
        assert "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(raised.value)
    with pytest.raises(P01EmbeddingStateContractError) as helper:
        reject_p01_equal_values_or_shared_source_as_embedding_v1(embedding_rule="EQUAL_VALUE")
    assert "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_candidate_embedding_states_remain_unproven() -> None:
    for inferred in (
        TYPED_EMBEDDING_STATE_NOT_EMBEDDED,
        TYPED_EMBEDDING_STATE_FULLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_PARTIALLY_EMBEDDED,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_EQUITY_BASE,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U04,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U05,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_U06,
        TYPED_EMBEDDING_STATE_EMBEDDED_IN_ANOTHER_TERM,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_MEMBER_CLASS,
        TYPED_EMBEDDING_STATE_DEPENDS_ON_APPLICABILITY,
        EMBEDDED_YES,
        EMBEDDED_NO,
        "INDEPENDENT",
        "SEPARATE",
        "SAFE",
    ):
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            build_p01_embedding_state_contract_v1(
                p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID",
                p01_embedding_rule=inferred,
            )
        message = str(raised.value)
        assert (
            "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in message
            or "P01_UNKNOWN_EMBEDDING_AUTO_NOT_EMBEDDED_FORBIDDEN" in message
            or "P01_EMBEDDING_CANDIDATE_UNPROVEN" in message
        )


def test_embedding_dimensions_remain_distinct_and_unresolved() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.family_level_embedding_state == "UNRESOLVED"
    assert contract.member_level_embedding_state == "UNRESOLVED"
    assert contract.economic_overlap_state == "UNRESOLVED"
    assert contract.representational_nesting_state == "UNRESOLVED"
    assert contract.arithmetic_inclusion_state == "UNRESOLVED"
    assert contract.semantic_equivalence_state == "UNRESOLVED"
    assert contract.p01_overlap_state == P01_OVERLAP_STATE
    assert "U06_ACCRUED_FEES_DISTINCT" in contract.p01_overlap_state
    with pytest.raises(P01EmbeddingStateContractError) as helper:
        reject_p01_u06_distinctness_as_non_embedding_v1(embedding_rule="U06_ACCRUED_FEES_DISTINCT")
    assert "P01_EMBEDDING_INFERRED_FROM_LABEL_FORBIDDEN" in str(helper.value)


def test_unknown_embedding_cannot_authorize_subtraction_omission_or_netting() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.unknown_embedding_cannot_authorize_subtraction == "true"
    assert contract.unknown_embedding_cannot_authorize_omission == "true"
    assert contract.unknown_embedding_cannot_authorize_netting == "true"
    assert contract.no_double_counting_permission == "true"
    for action in ("SUBTRACT", "OMIT", "NET", "COMBINE"):
        with pytest.raises(P01EmbeddingStateContractError) as raised:
            reject_p01_unknown_embedding_as_subtraction_omission_or_netting_v1(
                embedded_state="UNRESOLVED",
                requested_action=action,
            )
        assert "P01_UNKNOWN_EMBEDDING_SUBTRACTION_OMISSION_OR_NETTING_FORBIDDEN" in str(
            raised.value
        )


def test_p01_global_semantics_and_algebra_remain_unresolved() -> None:
    contract = build_p01_embedding_state_contract_v1(
        p01_embedding_state_contract_id="SYNTHETIC_P01_EMBEDDING_STATE_CONTRACT_ID"
    )
    assert contract.remaining_unresolved_semantics == REMAINING_UNRESOLVED_SEMANTICS
    assert "P01_EMBEDDING_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert "P01_EQUITY_BASE_INCLUSION_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert "P01_APPLICABILITY_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_TERM_SET_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_VALUE_UNIT_CLASS_UNSPECIFIED" in contract.remaining_unresolved_semantics
    assert "P01_OVERLAP_WITH_U04_U05_UNRESOLVED" in contract.remaining_unresolved_semantics
    assert EMBEDDED_STATE == "UNRESOLVED"
    assert P01_TERM_SEMANTICS_RESOLVED is True
    assert P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED is True
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert contract.rejected_embedding_inferences == REJECTED_EMBEDDING_INFERENCES
    assert "CANONICAL_AUTHORITY" in EVIDENCE_CLASSIFICATION
    dag = live_admission_gap_dag_v1()
    assert EARLIEST_DECOMPOSED_CONTRACT_GAP == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    assert dag["P01_EMBEDDED_STATE_RESOLVED"] is True
    assert dag["P01_EQUITY_BASE_INCLUSION_RESOLVED"] is True
    assert dag["P01_APPLICABILITY_RESOLVED"] is True
    assert dag["P01_TERM_SET_RESOLVED"] is True
    assert dag["P01_VALUE_UNIT_CLASS_RESOLVED"] is True
    assert dag["P01_EMBEDDING_STATE_CONTRACT_RUNTIME_INSTANCE_PRESENT"] is False
    assert dag["P01_EMBEDDING_STATE_CONTRACT_AUTHORITY_EFFECT"] == "NONE"
    assert SOURCE_SELECTED is False
    assert MAPPING_PROVEN is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    with pytest.raises(ExecutionPortConstructionForbiddenError):
        construct_live_execution_port_v1()


def test_runbook_af_consumes_go_without_rewriting_ae() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    af_section = _af_section()
    ae_start = runbook.index(AE_HEADING)
    ae_section = runbook[ae_start : runbook.index(AF_HEADING, ae_start)]
    assert "P01_EQUITY_BASE_INCLUSION_CONTRACT_SCHEMA_PRESENT=true" in ae_section
    assert "THIS_SLICE=11.2.1.AF" not in ae_section
    assert (
        "OWNER_GO=OWNER_GO_PEAK_TRADE_FULL_CORE_P01_BROADER_EMBEDDING_STATE_CONTRACT_V1"
        in af_section
    )
    assert "OWNER_GO_STATUS=CONSUMED" in af_section
    assert "P01_EMBEDDING_STATE_CONTRACT_SCHEMA_PRESENT=true" in af_section
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in af_section
    assert "P01_EMBEDDED_STATE=UNRESOLVED" in af_section
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in af_section
    assert "P01_APPLICABILITY_RESOLVED=false" in af_section
    assert "P01_TERM_SET_RESOLVED=false" in af_section
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in af_section
    assert "P01_TERM_SEMANTICS_RESOLVED=false" in af_section
    assert "P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED_CLOSED=false" in af_section
    assert "RECONSTRUCTION_ALGEBRA_COMPLETE=false" in af_section
    assert "CANONICAL_FORMULA_PROVEN=false" in af_section
    assert "SOURCE_SELECTED=false" in af_section
    assert "MAPPING_PROVEN=false" in af_section
    assert (
        "EARLIEST_DECOMPOSED_CONTRACT_GAP=P01_HAIRCUT_RESERVE_DEPLETION_UNSPECIFIED" in af_section
    )
    assert "DOCS_TOKEN_FULL_CORE_TYPED_P01_EMBEDDING_STATE_CONTRACT_V1" in spec
    assert "P01_EMBEDDED_STATE_RESOLVED=false" in spec
    assert "P01_EMBEDDED_STATE=UNRESOLVED" in spec
    assert "P01_EQUITY_BASE_INCLUSION_RESOLVED=false" in spec
    assert "P01_APPLICABILITY_RESOLVED=false" in spec
    assert "P01_TERM_SET_RESOLVED=false" in spec
    assert "P01_VALUE_UNIT_CLASS_RESOLVED=false" in spec
