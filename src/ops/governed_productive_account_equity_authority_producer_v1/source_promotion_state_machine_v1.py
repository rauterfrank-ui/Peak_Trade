"""SOURCE_PROMOTION_STATE_MACHINE_V1.

Typed promotion states for C17+ account-equity source candidates.
No state skip. No self-authorization. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import FrozenSet, Mapping, Tuple

SCHEMA_CLASS = "SOURCE_PROMOTION_STATE_MACHINE_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
OWNER_RATIFICATION_REQUIRED = True
AUTOMATIC_PROMOTION_ALLOWED = False

STATE_GENERATED = "GENERATED"
STATE_EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
STATE_EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
STATE_ACCEPTANCE_FAILED = "ACCEPTANCE_FAILED"
STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION = "ACCEPTABLE_FOR_OWNER_RATIFICATION"
STATE_OWNER_RATIFIED = "OWNER_RATIFIED"
STATE_MAPPING_PROVEN = "MAPPING_PROVEN"
STATE_PRODUCER_AUTHORIZED = "PRODUCER_AUTHORIZED"
STATE_RUNTIME_BINDING_AUTHORIZED = "RUNTIME_BINDING_AUTHORIZED"

PROMOTION_STATES: Tuple[str, ...] = (
    STATE_GENERATED,
    STATE_EVIDENCE_INCOMPLETE,
    STATE_EVIDENCE_COMPLETE,
    STATE_ACCEPTANCE_FAILED,
    STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
    STATE_OWNER_RATIFIED,
    STATE_MAPPING_PROVEN,
    STATE_PRODUCER_AUTHORIZED,
    STATE_RUNTIME_BINDING_AUTHORIZED,
)

PR1_ALLOWED_STATES: FrozenSet[str] = frozenset(
    {
        STATE_GENERATED,
        STATE_EVIDENCE_INCOMPLETE,
        STATE_EVIDENCE_COMPLETE,
        STATE_ACCEPTANCE_FAILED,
        STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION,
    }
)

PR1_FORBIDDEN_STATES: FrozenSet[str] = frozenset(
    {
        STATE_OWNER_RATIFIED,
        STATE_MAPPING_PROVEN,
        STATE_PRODUCER_AUTHORIZED,
        STATE_RUNTIME_BINDING_AUTHORIZED,
    }
)

LEGAL_TRANSITIONS: Mapping[str, FrozenSet[str]] = {
    STATE_GENERATED: frozenset({STATE_EVIDENCE_INCOMPLETE, STATE_EVIDENCE_COMPLETE}),
    STATE_EVIDENCE_INCOMPLETE: frozenset({STATE_EVIDENCE_COMPLETE, STATE_ACCEPTANCE_FAILED}),
    STATE_EVIDENCE_COMPLETE: frozenset(
        {STATE_ACCEPTANCE_FAILED, STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION}
    ),
    STATE_ACCEPTANCE_FAILED: frozenset(),
    STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION: frozenset({STATE_OWNER_RATIFIED}),
    STATE_OWNER_RATIFIED: frozenset({STATE_MAPPING_PROVEN}),
    STATE_MAPPING_PROVEN: frozenset({STATE_PRODUCER_AUTHORIZED}),
    STATE_PRODUCER_AUTHORIZED: frozenset({STATE_RUNTIME_BINDING_AUTHORIZED}),
    STATE_RUNTIME_BINDING_AUTHORIZED: frozenset(),
}

OWNER_GATE_TRANSITIONS: FrozenSet[Tuple[str, str]] = frozenset(
    {(STATE_ACCEPTABLE_FOR_OWNER_RATIFICATION, STATE_OWNER_RATIFIED)}
)


class SourcePromotionStateMachineError(ValueError):
    """Fail-closed promotion state-machine violation."""


def assert_known_promotion_state_v1(state: str) -> str:
    text = str(state or "").strip()
    if text not in PROMOTION_STATES:
        raise SourcePromotionStateMachineError(f"UNKNOWN_PROMOTION_STATE:{state}")
    return text


def assert_pr1_candidate_status_allowed_v1(state: str) -> str:
    text = assert_known_promotion_state_v1(state)
    if text in PR1_FORBIDDEN_STATES:
        raise SourcePromotionStateMachineError(f"PR1_FORBIDDEN_PROMOTION_STATE:{text}")
    if text not in PR1_ALLOWED_STATES:
        raise SourcePromotionStateMachineError(f"PR1_STATUS_NOT_ALLOWED:{text}")
    return text


def assert_legal_promotion_transition_v1(*, current: str, nxt: str) -> None:
    current_state = assert_known_promotion_state_v1(current)
    next_state = assert_known_promotion_state_v1(nxt)
    if current_state == next_state:
        raise SourcePromotionStateMachineError(
            f"PROMOTION_STATE_SKIP_OR_NOOP_FORBIDDEN:{current_state}->{next_state}"
        )
    allowed = LEGAL_TRANSITIONS.get(current_state, frozenset())
    if next_state not in allowed:
        raise SourcePromotionStateMachineError(
            f"PROMOTION_STATE_SKIP_FORBIDDEN:{current_state}->{next_state}"
        )


def assert_owner_ratification_gate_v1(
    *,
    current: str,
    nxt: str,
    owner_explicitly_ratifies_exact_candidate_id: bool,
) -> None:
    assert_legal_promotion_transition_v1(current=current, nxt=nxt)
    if (current, nxt) not in OWNER_GATE_TRANSITIONS:
        return
    if owner_explicitly_ratifies_exact_candidate_id is not True:
        raise SourcePromotionStateMachineError(
            "OWNER_RATIFICATION_GATE_REQUIRED_FOR_OWNER_RATIFIED"
        )


def candidate_cannot_self_authorize_v1(*, claimed_status: str) -> None:
    status = assert_known_promotion_state_v1(claimed_status)
    if status in PR1_FORBIDDEN_STATES:
        raise SourcePromotionStateMachineError(f"CANDIDATE_SELF_AUTHORIZATION_FORBIDDEN:{status}")
