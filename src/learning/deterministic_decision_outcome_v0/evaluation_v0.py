"""Fixture-only outcome, attribution, and counterfactual evaluation v0.

Observation is separated from inference. Safety correctness uses the
decision-time information set. A later market path cannot relabel a
safety-correct decision. UNKNOWN/UNAVAILABLE remain first-class.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import freeze_record
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    validate_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.evaluation_records_v0 import (
    validate_attribution_record_v0,
    validate_counterfactual_record_v0,
)
from src.learning.deterministic_decision_outcome_v0.outcome_v0 import validate_outcome_record_v0

EVALUATION_HINDSIGHT_LEAKAGE_ALLOWED: Final[bool] = False
EVALUATION_UNKNOWN_COLLAPSE_ALLOWED: Final[bool] = False


def evaluate_outcome_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    record = validate_outcome_record_v0(payload)
    observation = {
        "actual_outcome_ref": record["actual_outcome_ref"],
        "evaluation_horizon": record["evaluation_horizon"],
        "counterfactual_admissibility": record["counterfactual_admissibility"],
    }
    inference = {
        "safety_score": record["safety_score"],
        "decision_score": record["decision_score"],
        "economic_score": record["economic_score"],
        "root_cause": record["root_cause"],
        "confidence": record["confidence"],
    }
    return freeze_record(
        {
            "record_id": record["record_id"],
            "observation": observation,
            "inference": inference,
            "hindsight_leakage": False,
            "unknown_collapsed": False,
        }
    )


def evaluate_counterfactual_v0(
    payload: Mapping[str, Any], *, decision_event: Mapping[str, Any] | None = None
) -> MappingProxyType[str, Any]:
    record = validate_counterfactual_record_v0(payload)
    if decision_event is not None:
        decision = validate_decision_event_v0(decision_event)
        if decision["record_id"] != record["decision_event_ref"]:
            raise DdoValidationError("COUNTERFACTUAL_DECISION_REF_MISMATCH")
        if (
            record["decision_time_information_set_ref"] is not None
            and decision["decision_time_information_set_ref"] is not None
            and record["decision_time_information_set_ref"]
            != decision["decision_time_information_set_ref"]
        ):
            raise DdoValidationError("COUNTERFACTUAL_DECISION_TIME_SET_MISMATCH")
    if record["counterfactual_admissibility"] == "UNAVAILABLE":
        if record["alternative_result_ref"] is not None:
            raise DdoValidationError("UNAVAILABLE_MUST_REMAIN_UNKNOWN")
    return freeze_record(
        {
            "record_id": record["record_id"],
            "admissibility": record["counterfactual_admissibility"],
            "assumptions": record["assumptions"],
            "confidence": record["confidence"],
            "uses_decision_time_information_set": True,
            "hindsight_leakage": False,
        }
    )


def evaluate_attribution_v0(
    payload: Mapping[str, Any],
    *,
    later_economic_path: Mapping[str, Any] | None = None,
) -> MappingProxyType[str, Any]:
    record = validate_attribution_record_v0(payload)
    if later_economic_path:
        # Later observed economics may be recorded, but cannot rewrite safety labels.
        if "kill_switch_correctness" in later_economic_path:
            if later_economic_path["kill_switch_correctness"] != record["kill_switch_correctness"]:
                raise DdoValidationError("HINDSIGHT_CANNOT_RELABEL_SAFETY_CORRECTNESS")
        if "forced_false_positive" in later_economic_path:
            raise DdoValidationError("HINDSIGHT_CANNOT_RELABEL_SAFETY_CORRECTNESS")
    return freeze_record(
        {
            "record_id": record["record_id"],
            "root_cause": record["root_cause"],
            "kill_switch_correctness": record["kill_switch_correctness"],
            "kill_switch_timing_label": record["kill_switch_timing_label"],
            "stale_root_cause": record["stale_root_cause"],
            "safety_correctness_uses_decision_time_information_set": True,
            "hindsight_leakage": False,
        }
    )
