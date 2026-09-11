"""Isolated PDF-Step-3 authoritative Next Active Set ownership contract V1.

Binds Membership / Rotation Controller ownership of authoritative selected
membership inside the ranking/selection domain. PDF Step 4 census is closed
as inventory only. AS05-D01 adopts isolated POLICY_A unchanged as the Active
Set admission-policy rule set without transferring ownership or granting
runtime. AS05-D02 names evaluate_policy_a_v1 as the pure Active Set
anti-churn evaluator without transferring ownership. Does not close
AS05-D03, does not close PDF Step 5, does not join a host, does not rewire
Cap 2.3 or Cap 2.4, does not unlock G13, and does not name a productive
consumer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.ops.mf_canonical_single_egress_authority_handoff_contract_v1 import (
    EGRESS_ID,
    HANDOFF_PAYLOAD_STATUS,
    HANDOFF_TO_SINGLE_EXECUTION_SELECTION,
    PAYLOAD_CLASS,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    ARTIFACT_TYPE as MEMBERSHIP_CONTEXT_ARTIFACT_TYPE,
    N_VALUE as OD01_N_VALUE,
    MembershipContextArtifactError,
)

OWNER = "ops.mf_membership_rotation_controller_v1"
CONTRACT_ID = "MF_AUTHORITATIVE_NEXT_ACTIVE_SET_OWNERSHIP_CONTRACT_V1"
OBJECT_TYPE = "MF_AUTHORITATIVE_NEXT_ACTIVE_SET_V1"
SCHEMA_VERSION = "mf_authoritative_next_active_set_ownership.v1"

NEXT_ACTIVE_SET_AUTHORITY_CLASS = (
    "AUTHORITATIVE_SELECTED_MEMBERSHIP_INSIDE_RANKING_SELECTION_DOMAIN"
)
OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT = "RANKED_CANDIDATE_CONTEXT"
OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT = "NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT"
OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET = "AUTHORITATIVE_NEXT_ACTIVE_SET"

CARDINALITY_MODE = "AT_MOST_N"
N_VALUE_POINTER = int(OD01_N_VALUE)
N_VALUE_REOWNED = False
NO_PADDING = True
NO_PREFIX_SELECTION = True
NO_DOWNSTREAM_SELECTION = True
ONE_ACTIVE_SET_STATE_OWNER = True

ROTATION_POLICY_STATUS = "FAIL_CLOSED_UNTIL_PDF_STEP_5"
ANTI_CHURN_POLICY_FOR_AUTHORITATIVE_ACTIVE_SET = "ADOPTED_POLICY_A_UNCHANGED"
POLICY_A_IS_NOT_AUTOMATIC_ACTIVE_SET_POLICY = True
POLICY_REUSE_DOES_NOT_TRANSFER_AUTHORITY = True
ACTIVE_SET_POLICY_ADOPTION = "ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET"
ACTIVE_SET_POLICY_RATIFIED = True
AS05_D01_STATUS = "CLOSED"
AS05_D01_DECISION = "ADOPT_POLICY_A_UNCHANGED_FOR_ACTIVE_SET"
AS05_D02_STATUS = "CLOSED"
AS05_D02_DECISION = (
    "NAME_EVALUATE_POLICY_A_V1_AS_PURE_ANTI_CHURN_EVALUATOR_FOR_AUTHORITATIVE_NEXT_ACTIVE_SET"
)
AS05_D03_STATUS = "UNRESOLVED"
EVALUATOR_COMPONENT = (
    "src.ops.mf_membership_selector_and_rotation_runtime_contract_v1.evaluate_policy_a_v1"
)
EVALUATOR_AUTHORITY = "POLICY_A_ADMISSION_OR_NON_ADMISSION_ONLY"
EVALUATOR_IS_NOT_ACTIVE_SET_OWNER = True
EVALUATOR_IS_NOT_RANKING_OWNER = True
EVALUATOR_IS_NOT_PRODUCTIVE_SELECTION_OWNER = True
EVALUATOR_IS_NOT_EXECUTION_OWNER = True
EVALUATOR_IS_NOT_RUNTIME_HOST_OWNER = True
SELECTOR_OWNER_IDENTITY_IS_NOT_ACTIVE_SET_EVALUATOR_AUTHORITY = True
EVALUATOR_REUSE_DOES_NOT_TRANSFER_AUTHORITY = True
ROTATION_IS_NOT_ANTI_CHURN_OWNER = True
ROTATION_ROLE_REMAINS = "MEMBERSHIP_DIFF_ONLY"
SELECTOR_BECOMES_ACTIVE_SET_OWNER = False
EXECUTION_BECOMES_ACTIVE_SET_OWNER = False
PRODUCTIVE_SELECTION_AUTHORITY_TRANSFERRED = False
RUNTIME_AUTHORITY_GRANTED = False
LIVE_AUTHORITY_GRANTED = False
WIRE_SEND_AUTHORITY_GRANTED = False
CENSUS_CLASS = "INVENTORY_ONLY_NO_POLICY_CHOICE"
COOLDOWN_RATIFIED = False
TURNOVER_RATIFIED = False
NUMERIC_N_CHANGED = False

ROTATION_DECISION_AUTHORITY_BOUND = True
MEMBERSHIP_ROTATION_CONTROLLER_OWNER = OWNER
NEXT_ACTIVE_SET_AUTHORITY_OWNER = OWNER
MEMBERSHIP_STATE_OWNER = OWNER
NEXT_ACTIVE_SET_STATUS = "AUTHORITATIVE_OWNERSHIP_BOUND_ROTATION_FAIL_CLOSED"

SELECTION_DOMAIN_AUTHORITY_EFFECT = "ISOLATED_ACTIVE_SET_OWNERSHIP_ONLY"
ACTIVE_SET_SELECTION_AUTHORITY = True
MF_MEMBERSHIP_CONTEXT_SELECTION_AUTHORITY = False
PRODUCTIVE_SELECTION_AUTHORITY = False
CAP23_REMAINS_SOLE_PRODUCTIVE_SELECTION_OWNER = True
CAP23_IMPORTED = False
CAP23_REWIRED = False
CAP24_REWIRED = False
PRODUCTIVE_CONSUMER_CREATED = False
HOST_JOIN = False
G13_UNLOCK = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
RUNTIME_AUTHORIZED = False
EXECUTION_AUTHORITY_INSIDE_SELECTION_DOMAIN = False
EXECUTION_AUTHORITY_EFFECT = "NONE"
FULL_CORE_LIVE_AUTHORITY_EFFECT = "NONE"
CANARY_AUTHORITY_EFFECT = "NONE"
DOWNSTREAM_EXECUTION_MUST_NOT_RE_RANK = True
SECOND_SELECTION_DECISION_DOWNSTREAM = False
SINGLE_EGRESS_REQUIRED = True
NO_DIRECT_TOP20_TO_EXECUTION_BYPASS = True
NO_DIRECT_UNIVERSE_TO_EXECUTION_BYPASS = True

HANDOFF_INTENDED_SEMANTIC_OBJECT = OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET
HANDOFF_CURRENT_ENVELOPE_CLASS = HANDOFF_PAYLOAD_STATUS
HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO = True
CURRENT_ENVELOPE_CAN_REPRESENT_ACTIVE_SET = False
EXECUTING_MODEL_HANDOFF_CONSUMER = "UNBOUND"
EGRESS_ID_REUSED = EGRESS_ID
PARALLEL_HANDOFFS = "FORBIDDEN"

PDF_STEP_3_MEMBERSHIP_ROTATION_OWNERSHIP = "CLOSED"
PDF_STEP_4_ANTI_CHURN_CENSUS = "CLOSED"
PDF_STEP_5_ANTI_CHURN_OWNER_RATIFICATION = "UNRESOLVED"
PDF_STEP_7_RUNTIME_IMPLEMENTATION_ALLOWED = False
NEXT_CANONICAL_DECISION = "AS05-D03"
OWNER_DECISION_SURFACE_STATUS = "D01_D02_RATIFIED_D03_UNRESOLVED"
NEXT_IMPLEMENTATION_AUTHORIZED = False

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "cap23_imported",
    "cap23_rewired",
    "cap24_rewired",
    "cooldown_ratified",
    "execution_authority_inside_selection_domain",
    "g13_unlock",
    "host_join",
    "multi_future_runtime_authorized",
    "n_value_reowned",
    "productive_consumer_created",
    "runtime_authorized",
    "second_selection_decision_downstream",
    "turnover_ratified",
)

TRUE_REQUIRED_FLAGS: tuple[str, ...] = (
    "active_set_selection_authority",
    "downstream_execution_must_not_re_rank",
    "evaluator_is_not_active_set_owner",
    "evaluator_reuse_does_not_transfer_authority",
    "no_downstream_selection",
    "no_padding",
    "one_active_set_state_owner",
    "policy_a_is_not_automatic_active_set_policy",
    "policy_reuse_does_not_transfer_authority",
    "rotation_decision_authority_bound",
    "selector_owner_identity_is_not_active_set_evaluator_authority",
    "single_egress_required",
)

REQUIRED_DECLARATION_KEYS: frozenset[str] = frozenset(
    {
        "authority_class",
        "cardinality_mode",
        "egress_id",
        "executing_model_handoff_consumer",
        "object_class",
        "owner",
        "rotation_policy_status",
    }
)

FORBIDDEN_OBJECT_KEYS: frozenset[str] = frozenset(
    {
        "derived_execution_selection_input",
        "host_adapter",
        "selected_future",
        "single_selected_future",
        "winner",
    }
)

FORBIDDEN_OWNERS: frozenset[str] = frozenset(
    {
        "CAP_7_2_HOST",
        "ops.single_selected_future_policy_v1",
        "ops.single_selected_future_runtime_binding_v1",
        "ops.mf_membership_context_artifact_contract_v1",
        "ops.mf_membership_selector_and_rotation_runtime_contract_v1",
        "ops.productive_futures_ranking_producer_v1",
    }
)


class ActiveSetOwnershipError(MembershipContextArtifactError):
    """Fail-closed Active Set ownership error."""


@dataclass(frozen=True)
class AuthoritativeNextActiveSetDeclarationV1:
    owner: str
    object_type: str
    schema_version: str
    authority_class: str
    object_class: str
    cardinality_mode: str
    n_value_pointer: int
    n_value_reowned: bool
    rotation_policy_status: str
    rotation_decision_authority_bound: bool
    active_set_selection_authority: bool
    execution_authority_inside_selection_domain: bool
    egress_id: str
    executing_model_handoff_consumer: str
    membership_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_set_selection_authority": self.active_set_selection_authority,
            "authority_class": self.authority_class,
            "cardinality_mode": self.cardinality_mode,
            "egress_id": self.egress_id,
            "executing_model_handoff_consumer": self.executing_model_handoff_consumer,
            "execution_authority_inside_selection_domain": (
                self.execution_authority_inside_selection_domain
            ),
            "membership_ids": list(self.membership_ids),
            "n_value_pointer": self.n_value_pointer,
            "n_value_reowned": self.n_value_reowned,
            "object_class": self.object_class,
            "object_type": self.object_type,
            "owner": self.owner,
            "rotation_decision_authority_bound": self.rotation_decision_authority_bound,
            "rotation_policy_status": self.rotation_policy_status,
            "schema_version": self.schema_version,
        }


def classify_selection_domain_object_v1(object_class: str) -> str:
    allowed = {
        OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT,
        OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT,
        OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
    }
    raw = str(object_class or "").strip()
    if raw not in allowed:
        raise ActiveSetOwnershipError("OBJECT_CLASS_UNKNOWN", raw)
    return raw


def _require_mapping(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ActiveSetOwnershipError("ACTIVE_SET_DECLARATION_MISSING", "payload")
    return {str(key): payload[key] for key in payload}


def _reject_forbidden_keys(payload: Mapping[str, Any]) -> None:
    present = sorted(key for key in FORBIDDEN_OBJECT_KEYS if key in payload)
    if present:
        raise ActiveSetOwnershipError("EXECUTION_PAYLOAD_FORBIDDEN", ",".join(present))


def _reject_equated_classes(payload: Mapping[str, Any]) -> None:
    claimed = str(payload.get("object_class") or "").strip()
    if claimed == OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT:
        raise ActiveSetOwnershipError("RANKING_IS_NOT_ACTIVE_SET", claimed)
    if claimed == OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT:
        raise ActiveSetOwnershipError("MEMBERSHIP_CONTEXT_IS_NOT_ACTIVE_SET", claimed)
    alias = str(payload.get("equated_to") or "").strip()
    if alias in {
        OBJECT_CLASS_RANKED_CANDIDATE_CONTEXT,
        OBJECT_CLASS_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT,
        MEMBERSHIP_CONTEXT_ARTIFACT_TYPE,
        "TOP20",
        "TOP5",
    }:
        raise ActiveSetOwnershipError("OBJECT_CLASS_COLLAPSE_FORBIDDEN", alias)


def _require_false_flags(payload: Mapping[str, Any]) -> None:
    for flag in FALSE_REQUIRED_FLAGS:
        if flag not in payload:
            continue
        if payload[flag] is True:
            raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", flag)
        if payload[flag] is not False:
            raise ActiveSetOwnershipError("INVALID_SCHEMA", flag)


def _require_true_flags(payload: Mapping[str, Any]) -> None:
    for flag in TRUE_REQUIRED_FLAGS:
        if flag not in payload:
            continue
        if payload[flag] is not True:
            raise ActiveSetOwnershipError("INVARIANT_MISSING", flag)


def _bind_membership_ids(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, (list, tuple)):
        raise ActiveSetOwnershipError("INVALID_MEMBERSHIP_IDS", "not_sequence")
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        value = str(item).strip()
        if not value:
            raise ActiveSetOwnershipError("MALFORMED_IDENTITY", "empty_instrument_id")
        if value in seen:
            raise ActiveSetOwnershipError("DUPLICATE_INSTRUMENT_ID", value)
        seen.add(value)
        out.append(value)
    if len(out) > N_VALUE_POINTER:
        raise ActiveSetOwnershipError("CARDINALITY_EXCEEDS_N", str(len(out)))
    return tuple(out)


def validate_exactly_one_active_set_owner_v1(owners: Optional[Sequence[str]]) -> str:
    if owners is None:
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_MISSING", "owners")
    if not isinstance(owners, (list, tuple)):
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_AMBIGUOUS", "owners")
    cleaned = [str(item).strip() for item in owners if str(item).strip()]
    if len(cleaned) == 0:
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_MISSING", "empty")
    if len(cleaned) != 1:
        raise ActiveSetOwnershipError("PARALLEL_ACTIVE_SET_OWNER_FORBIDDEN", str(len(cleaned)))
    owner = cleaned[0]
    if owner in FORBIDDEN_OWNERS:
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_FORBIDDEN", owner)
    if owner != OWNER:
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_INVENTED", owner)
    return owner


def reject_rotation_until_step_5_v1(
    payload: Mapping[str, Any] | None = None,
) -> None:
    raw = dict(payload or {})
    if raw.get("apply_rotation") is True:
        raise ActiveSetOwnershipError("ROTATION_POLICY_UNRATIFIED", "apply_rotation")
    if raw.get("policy_a_applied_as_active_set_policy") is True:
        raise ActiveSetOwnershipError("POLICY_A_LEAKAGE", "policy_a_applied")
    if raw.get("selector_becomes_active_set_owner") is True:
        raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", "selector_owner_transfer")
    if raw.get("execution_becomes_active_set_owner") is True:
        raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", "execution_owner_transfer")
    if raw.get("evaluator_becomes_active_set_owner") is True:
        raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", "evaluator_owner_transfer")
    if raw.get("selector_owner_identity_is_active_set_evaluator_authority") is True:
        raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", "selector_evaluator_authority")
    if raw.get("rotation_is_anti_churn_owner") is True:
        raise ActiveSetOwnershipError("AUTHORITY_LEAKAGE", "rotation_anti_churn_owner")
    if raw.get("pdf_step_5_closed") is True:
        raise ActiveSetOwnershipError("STEP_5_STILL_UNRESOLVED", "pdf_step_5_closed")
    if str(raw.get("rotation_policy_status") or ROTATION_POLICY_STATUS) != (ROTATION_POLICY_STATUS):
        raise ActiveSetOwnershipError("ROTATION_POLICY_UNRATIFIED", "status")
    if raw.get("prefix_selection") is True:
        raise ActiveSetOwnershipError("PREFIX_SELECTION_FORBIDDEN", "prefix_selection")
    if raw.get("top5_product") is True:
        raise ActiveSetOwnershipError("TOP5_PRODUCT_FORBIDDEN", "top5_product")


def classify_mf_single_egress_alignment_v1() -> dict[str, Any]:
    return {
        "current_envelope_can_represent_active_set": CURRENT_ENVELOPE_CAN_REPRESENT_ACTIVE_SET,
        "current_envelope_class": HANDOFF_CURRENT_ENVELOPE_CLASS,
        "current_payload_class": PAYLOAD_CLASS,
        "egress_id": EGRESS_ID_REUSED,
        "envelope_is_not_yet_active_set_dto": HANDOFF_ENVELOPE_IS_NOT_YET_ACTIVE_SET_DTO,
        "executing_model_handoff_consumer": EXECUTING_MODEL_HANDOFF_CONSUMER,
        "handoff_to_single_execution_selection": HANDOFF_TO_SINGLE_EXECUTION_SELECTION,
        "intended_semantic_object": HANDOFF_INTENDED_SEMANTIC_OBJECT,
        "parallel_handoffs": PARALLEL_HANDOFFS,
        "smallest_compatible_evolution": (
            "INTENDED_OBJECT_POINTER_WITHOUT_ENVELOPE_SCHEMA_PROMOTION"
        ),
    }


def classify_active_set_anti_churn_evaluator_v1() -> dict[str, Any]:
    return {
        "active_set_owner": OWNER,
        "as05_d02_decision": AS05_D02_DECISION,
        "as05_d02_status": AS05_D02_STATUS,
        "evaluator_authority": EVALUATOR_AUTHORITY,
        "evaluator_component": EVALUATOR_COMPONENT,
        "evaluator_is_not_active_set_owner": EVALUATOR_IS_NOT_ACTIVE_SET_OWNER,
        "evaluator_is_not_execution_owner": EVALUATOR_IS_NOT_EXECUTION_OWNER,
        "evaluator_is_not_productive_selection_owner": (
            EVALUATOR_IS_NOT_PRODUCTIVE_SELECTION_OWNER
        ),
        "evaluator_is_not_ranking_owner": EVALUATOR_IS_NOT_RANKING_OWNER,
        "evaluator_is_not_runtime_host_owner": EVALUATOR_IS_NOT_RUNTIME_HOST_OWNER,
        "evaluator_reuse_does_not_transfer_authority": (
            EVALUATOR_REUSE_DOES_NOT_TRANSFER_AUTHORITY
        ),
        "rotation_is_not_anti_churn_owner": ROTATION_IS_NOT_ANTI_CHURN_OWNER,
        "rotation_role_remains": ROTATION_ROLE_REMAINS,
        "selector_owner_identity_is_not_active_set_evaluator_authority": (
            SELECTOR_OWNER_IDENTITY_IS_NOT_ACTIVE_SET_EVALUATOR_AUTHORITY
        ),
    }


def validate_authoritative_next_active_set_declaration_v1(
    payload: Mapping[str, Any] | None,
) -> AuthoritativeNextActiveSetDeclarationV1:
    raw = _require_mapping(payload)
    missing = sorted(key for key in REQUIRED_DECLARATION_KEYS if key not in raw)
    if missing:
        raise ActiveSetOwnershipError("ACTIVE_SET_DECLARATION_MISSING", ",".join(missing))
    _reject_forbidden_keys(raw)
    _reject_equated_classes(raw)
    _require_false_flags(raw)
    _require_true_flags(raw)
    reject_rotation_until_step_5_v1(raw)
    owner = validate_exactly_one_active_set_owner_v1([str(raw.get("owner") or "")])
    object_class = classify_selection_domain_object_v1(
        str(raw.get("object_class") or OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET)
    )
    if object_class != OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET:
        raise ActiveSetOwnershipError("OBJECT_CLASS_MISMATCH", object_class)
    authority_class = str(raw.get("authority_class") or "").strip()
    if authority_class != NEXT_ACTIVE_SET_AUTHORITY_CLASS:
        raise ActiveSetOwnershipError("AUTHORITY_CLASS_MISMATCH", authority_class)
    cardinality = str(raw.get("cardinality_mode") or "").strip()
    if cardinality != CARDINALITY_MODE:
        raise ActiveSetOwnershipError("CARDINALITY_MODE_MISMATCH", cardinality)
    n_pointer = int(raw.get("n_value_pointer", N_VALUE_POINTER))
    if n_pointer != N_VALUE_POINTER:
        raise ActiveSetOwnershipError("N_VALUE_POINTER_MISMATCH", str(n_pointer))
    if raw.get("n_value_reowned") is True:
        raise ActiveSetOwnershipError("N_VALUE_REOWNED_FORBIDDEN", "n_value_reowned")
    rotation_status = str(raw.get("rotation_policy_status") or "").strip()
    if rotation_status != ROTATION_POLICY_STATUS:
        raise ActiveSetOwnershipError("ROTATION_POLICY_UNRATIFIED", rotation_status)
    consumer = str(
        raw.get("executing_model_handoff_consumer") or EXECUTING_MODEL_HANDOFF_CONSUMER
    ).strip()
    if consumer != EXECUTING_MODEL_HANDOFF_CONSUMER:
        raise ActiveSetOwnershipError("CONSUMER_IDENTITY_INVENTED", consumer)
    egress_id = str(raw.get("egress_id") or EGRESS_ID_REUSED).strip()
    if egress_id != EGRESS_ID_REUSED:
        raise ActiveSetOwnershipError("PARALLEL_HANDOFF_FORBIDDEN", egress_id)
    membership_ids = _bind_membership_ids(raw.get("membership_ids"))
    declaration = AuthoritativeNextActiveSetDeclarationV1(
        owner=owner,
        object_type=OBJECT_TYPE,
        schema_version=SCHEMA_VERSION,
        authority_class=NEXT_ACTIVE_SET_AUTHORITY_CLASS,
        object_class=OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
        cardinality_mode=CARDINALITY_MODE,
        n_value_pointer=N_VALUE_POINTER,
        n_value_reowned=False,
        rotation_policy_status=ROTATION_POLICY_STATUS,
        rotation_decision_authority_bound=True,
        active_set_selection_authority=True,
        execution_authority_inside_selection_domain=False,
        egress_id=EGRESS_ID_REUSED,
        executing_model_handoff_consumer=EXECUTING_MODEL_HANDOFF_CONSUMER,
        membership_ids=membership_ids,
    )
    if declaration.owner != OWNER:
        raise ActiveSetOwnershipError("ACTIVE_SET_OWNER_INVENTED", declaration.owner)
    return declaration


def build_authoritative_next_active_set_declaration_v1(
    *,
    membership_ids: Sequence[str] = (),
) -> AuthoritativeNextActiveSetDeclarationV1:
    payload = {
        "active_set_selection_authority": True,
        "authority_class": NEXT_ACTIVE_SET_AUTHORITY_CLASS,
        "cardinality_mode": CARDINALITY_MODE,
        "downstream_execution_must_not_re_rank": True,
        "egress_id": EGRESS_ID_REUSED,
        "executing_model_handoff_consumer": EXECUTING_MODEL_HANDOFF_CONSUMER,
        "execution_authority_inside_selection_domain": False,
        "membership_ids": list(membership_ids),
        "n_value_pointer": N_VALUE_POINTER,
        "n_value_reowned": False,
        "no_downstream_selection": True,
        "no_padding": True,
        "object_class": OBJECT_CLASS_AUTHORITATIVE_NEXT_ACTIVE_SET,
        "one_active_set_state_owner": True,
        "owner": OWNER,
        "evaluator_is_not_active_set_owner": True,
        "evaluator_reuse_does_not_transfer_authority": True,
        "policy_a_is_not_automatic_active_set_policy": True,
        "policy_reuse_does_not_transfer_authority": True,
        "rotation_decision_authority_bound": True,
        "selector_owner_identity_is_not_active_set_evaluator_authority": True,
        "rotation_policy_status": ROTATION_POLICY_STATUS,
        "schema_version": SCHEMA_VERSION,
    }
    return validate_authoritative_next_active_set_declaration_v1(payload)
