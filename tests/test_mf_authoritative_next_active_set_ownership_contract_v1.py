"""Bounded tests for PDF-Step-3 authoritative Next Active Set ownership."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.mf_authoritative_next_active_set_ownership_contract_v1 import (
    ACTIVE_SET_POLICY_ADOPTION,
    ACTIVE_SET_POLICY_RATIFIED,
    ACTIVE_SET_SELECTION_AUTHORITY,
    ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET,
    AS05_D01_DECISION,
    AS05_D01_STATUS,
    AS05_D02_STATUS,
    AS05_D03_STATUS,
    CAP23_REWIRED,
    CAP24_REWIRED,
    CARDINALITY_MODE,
    CENSUS_CLASS,
    COOLDOWN_RATIFIED,
    CURRENT_ENVELOPE_CAN_REPRESENT_ACTIVE_SET,
    EGRESS_ID_REUSED,
    EXECUTING_MODEL_HANDOFF_CONSUMER,
    EXECUTION_AUTHORITY_EFFECT,
    EXECUTION_AUTHORITY_INSIDE_SELECTION_DOMAIN,
    EXECUTION_BECOMES_ACTIVE_SET_OWNER,
    G13_UNLOCK,
    HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO,
    HANDOFF_INTENDED_SEMANTIC_OBJECT,
    LIVE_AUTHORITY_GRANTED,
    MEMBERSHIP_ROTATION_CONTROLLER_OWNER,
    MF_MEMBERSHIP_CONTEXT_SELECTION_AUTHORITY,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_VALUE_POINTER,
    N_VALUE_REOWNED,
    NEXT_ACTIVE_SET_AUTHORITY_CLASS,
    NEXT_ACTIVE_SET_AUTHORITY_OWNER,
    NEXT_ACTIVE_SET_STATUS,
    NEXT_CANONICAL_DECISION,
    NEXT_IMPLEMENTATION_AUTHORIZED,
    NUMERIC_N_CHANGED,
    OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
    OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT,
    OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT,
    ONE_ACTIVE_SET_STATE_OWNER,
    OWNER,
    OWNER_DECISION_SURFACE_STATUS,
    PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP,
    PDF_STEP_4_ANTI_CHURN_CENSUS,
    PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION,
    PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED,
    POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY,
    POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY,
    PRODUCTIVE_SELECTION_AUTHORITY_TRANSFERRED,
    ROTATION_DECISION_AUTHORITY_BOUND,
    ROTATION_POLICY_STATUS,
    RUNTIME_AUTHORITY_GRANTED,
    SECOND_SELECTION_DECISION_DOWNSTREAM,
    SELECTOR_BECOMES_ACTIVE_SET_OWNER,
    TURNOVER_RATIFIED,
    WIRE_SEND_AUTHORITY_GRANTED,
    ActiveSetOwnershipError,
    build_authoritative_next_active_set_declaration_v1,
    classify_mf_single_egress_alignment_v1,
    classify_selection_domain_object_v1,
    reject_rotation_until_step_5_v1,
    validate_authoritative_next_active_set_declaration_v1,
    validate_exactly_one_active_set_owner_v1,
)
from src.ops.mf_canonical_single_egress_authority_handoff_contract_v1 import (
    EGRESS_ID,
    HANDOFF_TO_SINGLE_EXECUTION_SELECTION,
)
from src.ops.mf_membership_context_artifact_contract_v1 import N_VALUE

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src/ops/mf_authoritative_next_active_set_ownership_contract_v1.py"
)
SPEC = (
    Path(__file__).resolve().parents[1]
    / "docs/ops/specs/MF_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_CONTRACT_V1.md"
)


def _declaration_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "active_set_selection_authority": True,
        "authority_class": NEXT_ACTIVE_SET_AUTHORITY_CLASS,
        "cardinality_mode": CARDINALITY_MODE,
        "downstream_execution_must_not_re_rank": True,
        "egress_id": EGRESS_ID_REUSED,
        "executing_model_handoff_consumer": EXECUTING_MODEL_HANDOFF_CONSUMER,
        "execution_authority_inside_selection_domain": False,
        "membership_ids": ["okx_eea:ada", "okx_eea:apt"],
        "n_value_pointer": N_VALUE_POINTER,
        "n_value_reowned": False,
        "no_downstream_selection": True,
        "no_padding": True,
        "object_class": OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
        "one_active_set_state_owner": True,
        "owner": OWNER,
        "policy_a_is_not_automatic_active_set_policy": True,
        "policy_reuse_does_not_transfer_authority": True,
        "rotation_decision_authority_bound": True,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "schema_version": "mf_authoritative_next_active_set_ownership.v1",
    }
    payload.update(overrides)
    return payload


def test_safety_and_ownership_invariants() -> None:
    assert MEMBERSHIP_ROTATION_CONTROLLER_OWNER == OWNER
    assert NEXT_ACTIVE_SET_AUTHORITY_OWNER == OWNER
    assert ROTATION_DECISION_AUTHORITY_BOUND is True
    assert ONE_ACTIVE_SET_STATE_OWNER is True
    assert ACTIVE_SET_SELECTION_AUTHORITY is True
    assert MF_MEMBERSHIP_CONTEXT_SELECTION_AUTHORITY is False
    assert EXECUTION_AUTHORITY_INSIDE_SELECTION_DOMAIN is False
    assert EXECUTION_AUTHORITY_EFFECT == "NONE"
    assert SECOND_SELECTION_DECISION_DOWNSTREAM is False
    assert G13_UNLOCK is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert CAP23_REWIRED is False
    assert CAP24_REWIRED is False
    assert NUMERIC_N_CHANGED is False
    assert N_VALUE_REOWNED is False
    assert N_VALUE_POINTER == N_VALUE == 5
    assert CARDINALITY_MODE == "AT_MOST_N"
    assert POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY is True
    assert POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY is True
    assert ACTIVE_SET_POLICY_ADOPTION == "ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET"
    assert ACTIVE_SET_POLICY_RATIFIED is True
    assert AS05_D01_STATUS == "CLOSED"
    assert AS05_D01_DECISION == "ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET"
    assert AS05_D02_STATUS == "UNRESOLVED"
    assert AS05_D03_STATUS == "UNRESOLVED"
    assert SELECTOR_BECOMES_ACTIVE_SET_OWNER is False
    assert EXECUTION_BECOMES_ACTIVE_SET_OWNER is False
    assert PRODUCTIVE_SELECTION_AUTHORITY_TRANSFERRED is False
    assert RUNTIME_AUTHORITY_GRANTED is False
    assert LIVE_AUTHORITY_GRANTED is False
    assert WIRE_SEND_AUTHORITY_GRANTED is False
    assert CENSUS_CLASS == "INVENTORY_ONLY_NO_POLICY_CHOICE"
    assert ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET == "ADOPTED_POLICY_A_UNCHANGED"
    assert COOLDOWN_RATIFIED is False
    assert TURNOVER_RATIFIED is False
    assert PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP == "CLOSED"
    assert PDF_STEP_4_ANTI_CHURN_CENSUS == "CLOSED"
    assert PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION == "UNRESOLVED"
    assert PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED is False
    assert NEXT_IMPLEMENTATION_AUTHORIZED is False
    assert NEXT_CANONICAL_DECISION == "AS05-D02"
    assert OWNER_DECISION_SURFACE_STATUS == "D01_RATIFIED_D02_D03_UNRESOLVED"
    assert NEXT_ACTIVE_SET_STATUS == ("AUTHORITATIVE_OWNERSHIP_BOUND_ROTATION_FAIL_CLOSED")
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"


def test_object_classes_are_not_equivalent() -> None:
    assert classify_selection_domain_object_v1(OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT) == (
        OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT
    )
    assert (
        classify_selection_domain_object_v1(OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT)
        == OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT
    )
    assert (
        classify_selection_domain_object_v1(OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET)
        == OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET
    )
    assert (
        len(
            {
                OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT,
                OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT,
                OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
            }
        )
        == 3
    )


def test_exactly_one_active_set_owner() -> None:
    assert validate_exactly_one_active_set_owner_v1([OWNER]) == OWNER
    with pytest.raises(ActiveSetOwnershipError) as missing:
        validate_exactly_one_active_set_owner_v1([])
    assert missing.value.failure_code == "ACTIVE_SET_OWNER_MISSING"
    with pytest.raises(ActiveSetOwnershipError) as parallel:
        validate_exactly_one_active_set_owner_v1([OWNER, OWNER])
    assert parallel.value.failure_code == "PARALLEL_ACTIVE_SET_OWNER_FORBIDDEN"
    with pytest.raises(ActiveSetOwnershipError) as cap23:
        validate_exactly_one_active_set_owner_v1(["ops.single_selected_future_policy_v1"])
    assert cap23.value.failure_code == "ACTIVE_SET_OWNER_FORBIDDEN"


def test_valid_declaration_does_not_activate_rotation() -> None:
    declaration = build_authoritative_next_active_set_declaration_v1(
        membership_ids=("okx_eea:ada", "okx_eea:eth")
    )
    assert declaration.owner == OWNER
    assert declaration.object_class == OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET
    assert declaration.rotation_policy_status == ROTATION_POLICY_STATUS
    assert declaration.executing_model_handoff_consumer == "UNBOUND"
    assert declaration.execution_authority_inside_selection_domain is False
    assert len(declaration.membership_ids) == 2


def test_ranking_is_not_active_set() -> None:
    payload = _declaration_payload(object_class=OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT)
    with pytest.raises(ActiveSetOwnershipError) as exc:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert exc.value.failure_code == "RANKING_IS_NOT_ACTIVE_SET"


def test_membership_context_is_not_active_set() -> None:
    payload = _declaration_payload(object_class=OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT)
    with pytest.raises(ActiveSetOwnershipError) as exc:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert exc.value.failure_code == "MEMBERSHIP_CONTEXT_IS_NOT_ACTIVE_SET"


def test_class_collapse_fails_closed() -> None:
    payload = _declaration_payload(equated_to="TOP20")
    with pytest.raises(ActiveSetOwnershipError) as exc:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert exc.value.failure_code == "OBJECT_CLASS_COLLAPSE_FORBIDDEN"


def test_rotation_remains_fail_closed() -> None:
    with pytest.raises(ActiveSetOwnershipError) as exc:
        reject_rotation_until_step_5_v1({"apply_rotation": True})
    assert exc.value.failure_code == "ROTATION_POLICY_UNRATIFIED"
    payload = _declaration_payload(apply_rotation=True)
    with pytest.raises(ActiveSetOwnershipError) as applied:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert applied.value.failure_code == "ROTATION_POLICY_UNRATIFIED"
    assert PDF_STEP_4_ANTI_CHURN_CENSUS == "CLOSED"
    assert ACTIVE_SET_POLICY_ADOPTION == "ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET"
    assert ACTIVE_SET_POLICY_RATIFIED is True
    assert CENSUS_CLASS == "INVENTORY_ONLY_NO_POLICY_CHOICE"
    assert ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET == "ADOPTED_POLICY_A_UNCHANGED"
    assert POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY is True
    assert POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY is True
    assert PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION == "UNRESOLVED"
    assert AS05_D02_STATUS == "UNRESOLVED"


def test_policy_a_adoption_does_not_authorize_runtime_application() -> None:
    payload = _declaration_payload(policy_a_applied_as_active_set_policy=True)
    with pytest.raises(ActiveSetOwnershipError) as exc:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert exc.value.failure_code == "POLICY_A_LEAKAGE"


def test_as05_d01_does_not_transfer_owner_or_close_step_5() -> None:
    payload = _declaration_payload(selector_becomes_active_set_owner=True)
    with pytest.raises(ActiveSetOwnershipError) as selector:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert selector.value.failure_code == "AUTHORITY_LEAKAGE"
    payload = _declaration_payload(execution_becomes_active_set_owner=True)
    with pytest.raises(ActiveSetOwnershipError) as execution:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert execution.value.failure_code == "AUTHORITY_LEAKAGE"
    payload = _declaration_payload(pdf_step_5_closed=True)
    with pytest.raises(ActiveSetOwnershipError) as step5:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert step5.value.failure_code == "STEP_5_STILL_UNRESOLVED"
    payload = _declaration_payload(
        owner="ops.mf_membership_selector_and_rotation_runtime_contract_v1"
    )
    with pytest.raises(ActiveSetOwnershipError) as forbidden:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert forbidden.value.failure_code == "ACTIVE_SET_OWNER_FORBIDDEN"


def test_no_execution_authority_and_no_second_selector() -> None:
    payload = _declaration_payload(execution_authority_inside_selection_domain=True)
    with pytest.raises(ActiveSetOwnershipError) as execution:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert execution.value.failure_code == "AUTHORITY_LEAKAGE"
    payload = _declaration_payload(owner="ops.single_selected_future_policy_v1")
    with pytest.raises(ActiveSetOwnershipError) as second:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert second.value.failure_code == "ACTIVE_SET_OWNER_FORBIDDEN"


def test_at_most_n_and_no_implicit_top5() -> None:
    too_many = [f"id-{index}" for index in range(N_VALUE_POINTER + 1)]
    payload = _declaration_payload(membership_ids=too_many)
    with pytest.raises(ActiveSetOwnershipError) as cardinality:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert cardinality.value.failure_code == "CARDINALITY_EXCEEDS_N"
    payload = _declaration_payload(top5_product=True)
    with pytest.raises(ActiveSetOwnershipError) as top5:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert top5.value.failure_code == "TOP5_PRODUCT_FORBIDDEN"
    payload = _declaration_payload(prefix_selection=True)
    with pytest.raises(ActiveSetOwnershipError) as prefix:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert prefix.value.failure_code == "PREFIX_SELECTION_FORBIDDEN"


def test_malformed_and_ambiguous_fail_closed() -> None:
    with pytest.raises(ActiveSetOwnershipError) as missing:
        validate_authoritative_next_active_set_declaration_v1(None)
    assert missing.value.failure_code == "ACTIVE_SET_DECLARATION_MISSING"
    payload = _declaration_payload()
    del payload["owner"]
    with pytest.raises(ActiveSetOwnershipError) as owner_missing:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert owner_missing.value.failure_code == "ACTIVE_SET_DECLARATION_MISSING"
    payload = _declaration_payload(membership_ids=["okx_eea:ada", "okx_eea:ada"])
    with pytest.raises(ActiveSetOwnershipError) as duplicate:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert duplicate.value.failure_code == "DUPLICATE_INSTRUMENT_ID"


def test_g13_and_consumer_remain_closed() -> None:
    payload = _declaration_payload(g13_unlock=True)
    with pytest.raises(ActiveSetOwnershipError) as g13:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert g13.value.failure_code == "AUTHORITY_LEAKAGE"
    payload = _declaration_payload(
        executing_model_handoff_consumer="ops.single_selected_future_policy_v1"
    )
    with pytest.raises(ActiveSetOwnershipError) as consumer:
        validate_authoritative_next_active_set_declaration_v1(payload)
    assert consumer.value.failure_code == "CONSUMER_IDENTITY_INVENTED"


def test_handoff_alignment_does_not_promote_envelope() -> None:
    alignment = classify_mf_single_egress_alignment_v1()
    assert alignment["egress_id"] == EGRESS_ID
    assert alignment["intended_semantic_object"] == HANDOFF_INTENDED_SEMANTIC_OBJECT
    assert alignment["current_envelope_can_represent_active_set"] is False
    assert alignment["envelope_is_not_yet_active_set_dto"] is True
    assert alignment["executing_model_handoff_consumer"] == "UNBOUND"
    assert alignment["handoff_to_single_execution_selection"] == (
        HANDOFF_TO_SINGLE_EXECUTION_SELECTION
    )
    assert CURRENT_ENVELOPE_CAN_REPRESENT_ACTIVE_SET is False
    assert HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO is True


def test_contract_does_not_import_productive_runtime_owners() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "src.ops.single_selected_future" not in source
    assert "src.execution" not in source
    assert "apply_rotation_runtime" not in source


def test_step_5_d01_closed_without_step_5_close() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert "OWNER_DECISION_SURFACE_STATUS=D01_RATIFIED_D02_D03_UNRESOLVED" in spec
    assert "OWNER_DECISION_COUNT=3" in spec
    assert "DECISION_ID=AS05-D01" in spec
    assert "DECISION_ID=AS05-D02" in spec
    assert "DECISION_ID=AS05-D03" in spec
    assert "AS05_D01_STATUS=CLOSED" in spec
    assert "AS05_D01_DECISION=ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET" in spec
    assert "AS05_D02_STATUS=UNRESOLVED" in spec
    assert "AS05_D03_STATUS=UNRESOLVED" in spec
    assert "POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY=true" in spec
    assert "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=UNRESOLVED" in spec
    assert "ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET=ADOPTED_POLICY_A_UNCHANGED" in spec
    assert "OVERREAD_AS_D01_EQUALS_STEP_5_CLOSE=FORBIDDEN" in spec
    assert "OVERREAD_AS_D01_TRANSFERS_OWNERSHIP_TO_SELECTOR=FORBIDDEN" in spec
    assert "OVERREAD_AS_PDF_FIVE_MECHANISMS_ARE_REQUIRED_FIELDS=FORBIDDEN" in spec
    assert "PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION=CLOSED" not in spec
    assert "PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED=true" not in spec
    assert PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION == "UNRESOLVED"
    assert ACTIVE_SET_POLICY_RATIFIED is True
    assert AS05_D01_STATUS == "CLOSED"
    assert AS05_D02_STATUS == "UNRESOLVED"
    assert AS05_D03_STATUS == "UNRESOLVED"
    assert PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED is False
    assert ROTATION_POLICY_STATUS == "FAIL_CLOSED_UNTIL_PDF_STEP_5"
    assert NEXT_CANONICAL_DECISION == "AS05-D02"
