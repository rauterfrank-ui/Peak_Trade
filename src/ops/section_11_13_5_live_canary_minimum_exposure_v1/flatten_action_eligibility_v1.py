"""Flatten-action eligibility from the Z2CM four-way position-state predicate.

Prerequisite 08 (`TARGET_POSITION_NONZERO_PROVEN`) is required only for the
flatten-POST branch. `TARGET_POSITION_NOT_OBSERVED` is a resolved no-candidate
/ no-POST branch. Empty `data[]` is not zero. Completeness is not inferred
from HTTP 200. This module never GETs, never POSTs, and never authorizes live.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    HTTP_OK_DOES_NOT_PROVE_COMPLETENESS,
    QUERY_COMPLETENESS_PROVEN_DEFAULT,
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
    TARGET_POSITION_UNKNOWN,
    TARGET_POSITION_ZERO_PROVEN,
    TargetPositionStateClassificationV1,
    classify_target_position_state_v1,
)

FLATTEN_ACTION_BRANCH_POST = "FLATTEN_POST_BRANCH"
FLATTEN_ACTION_BRANCH_NO_ACTION = "NO_ACTION_BRANCH"
FLATTEN_ACTION_BRANCH_UNKNOWN = "FAIL_CLOSED_UNKNOWN_BRANCH"

PREREQUISITE_08_PASS_NONZERO = "PASS_TARGET_POSITION_NONZERO_PROVEN"
PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY = "FAIL_NOT_NONZERO_POST_BRANCH_ONLY"
PREREQUISITE_08_UNREACHABLE_UNKNOWN = "UNREACHABLE_UNKNOWN"

ABSENCE_TO_ZERO_INFERENCE_ALLOWED = False
EQUIVALENT_UNFILTERED_GET_RESOLVES_NOT_OBSERVED = False
QUERY_COMPLETENESS_PROVEN = False
HTTP_OK_IMPLIES_COMPLETENESS = False
PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY = True
NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER = False
THIS_CLASSIFIER_DOES_NOT_GET = True
THIS_CLASSIFIER_DOES_NOT_POST = True
THIS_CLASSIFIER_DOES_NOT_AUTHORIZE_FLATTEN = True


@dataclass(frozen=True)
class FlattenActionEligibilityV1:
    """Offline eligibility only. Never a flatten, live, or completeness certificate."""

    instrument_id: str
    position_state: str
    branch: str
    execution_prerequisite_08_status: str
    flatten_post_candidate_constructable: bool
    unique_actionable_flatten_candidate: bool
    flatten_post_permitted: bool
    target_position_zero_proven: bool
    target_position_nonzero_proven: bool
    query_completeness_proven: bool
    absence_to_zero_inference_allowed: bool
    equivalent_unfiltered_get_resolves_not_observed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "position_state": self.position_state,
            "branch": self.branch,
            "execution_prerequisite_08_status": self.execution_prerequisite_08_status,
            "flatten_post_candidate_constructable": self.flatten_post_candidate_constructable,
            "unique_actionable_flatten_candidate": self.unique_actionable_flatten_candidate,
            "flatten_post_permitted": self.flatten_post_permitted,
            "target_position_zero_proven": self.target_position_zero_proven,
            "target_position_nonzero_proven": self.target_position_nonzero_proven,
            "query_completeness_proven": self.query_completeness_proven,
            "absence_to_zero_inference_allowed": self.absence_to_zero_inference_allowed,
            "equivalent_unfiltered_get_resolves_not_observed": (
                self.equivalent_unfiltered_get_resolves_not_observed
            ),
            "reason": self.reason,
            "PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY": (
                PREREQUISITE_08_IS_FLATTEN_POST_BRANCH_ONLY
            ),
            "NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER": (NOT_OBSERVED_IS_UNRESOLVED_PHASE_BLOCKER),
            "HTTP_OK_DOES_NOT_PROVE_COMPLETENESS": HTTP_OK_DOES_NOT_PROVE_COMPLETENESS,
            "THIS_CLASSIFIER_DOES_NOT_GET": THIS_CLASSIFIER_DOES_NOT_GET,
            "THIS_CLASSIFIER_DOES_NOT_POST": THIS_CLASSIFIER_DOES_NOT_POST,
            "THIS_CLASSIFIER_DOES_NOT_AUTHORIZE_FLATTEN": (
                THIS_CLASSIFIER_DOES_NOT_AUTHORIZE_FLATTEN
            ),
        }


def _from_classification(
    classified: TargetPositionStateClassificationV1,
) -> FlattenActionEligibilityV1:
    state = classified.state
    zero = state == TARGET_POSITION_ZERO_PROVEN
    nonzero = state == TARGET_POSITION_NONZERO_PROVEN
    if state == TARGET_POSITION_NONZERO_PROVEN:
        branch = FLATTEN_ACTION_BRANCH_POST
        prereq_08 = PREREQUISITE_08_PASS_NONZERO
        candidate = True
        reason = "UNIQUE_ACTIONABLE_FLATTEN_CANDIDATE_NONZERO_POST_STILL_UNAUTHORIZED"
    elif state == TARGET_POSITION_NOT_OBSERVED:
        branch = FLATTEN_ACTION_BRANCH_NO_ACTION
        prereq_08 = PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY
        candidate = False
        reason = "NO_ACTIONABLE_FLATTEN_CANDIDATE_NOT_OBSERVED_NOT_ZERO"
    elif state == TARGET_POSITION_ZERO_PROVEN:
        branch = FLATTEN_ACTION_BRANCH_NO_ACTION
        prereq_08 = PREREQUISITE_08_FAIL_NOT_NONZERO_POST_BRANCH_ONLY
        candidate = False
        reason = "NO_ACTIONABLE_FLATTEN_CANDIDATE_EXPLICIT_ZERO"
    else:
        branch = FLATTEN_ACTION_BRANCH_UNKNOWN
        prereq_08 = PREREQUISITE_08_UNREACHABLE_UNKNOWN
        candidate = False
        reason = classified.reason or TARGET_POSITION_UNKNOWN
    return FlattenActionEligibilityV1(
        instrument_id=classified.instrument_id,
        position_state=state,
        branch=branch,
        execution_prerequisite_08_status=prereq_08,
        flatten_post_candidate_constructable=candidate,
        unique_actionable_flatten_candidate=candidate,
        flatten_post_permitted=False,
        target_position_zero_proven=zero,
        target_position_nonzero_proven=nonzero,
        query_completeness_proven=QUERY_COMPLETENESS_PROVEN_DEFAULT,
        absence_to_zero_inference_allowed=ABSENCE_TO_ZERO_INFERENCE_ALLOWED,
        equivalent_unfiltered_get_resolves_not_observed=(
            EQUIVALENT_UNFILTERED_GET_RESOLVES_NOT_OBSERVED
        ),
        reason=reason,
    )


def classify_flatten_action_eligibility_v1(
    *,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> FlattenActionEligibilityV1:
    """Map the Z2CM four-way predicate onto flatten-POST vs no-action vs unknown.

    Prerequisite 08 FAIL on NOT_OBSERVED is a resolved POST-branch deny. It is
    not an unresolved phase blocker and does not authorize another equivalent
    unfiltered GET. This result does not authorize flatten, live, or POST.
    """
    classified = classify_target_position_state_v1(
        positions_payload=positions_payload,
        instrument_id=instrument_id,
    )
    return _from_classification(classified)


assert HTTP_OK_IMPLIES_COMPLETENESS is False
assert QUERY_COMPLETENESS_PROVEN is False
assert ABSENCE_TO_ZERO_INFERENCE_ALLOWED is False
