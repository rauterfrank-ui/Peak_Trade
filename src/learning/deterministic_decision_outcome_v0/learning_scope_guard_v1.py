"""Common offline admission before the distinct existing learning consumers.

No pool/target conversion. Scope records are caller-selected and immutable in the
retained Pending capsule; this guard grants no productive application authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.self_learning_provenance_eligibility_v1 import (
    require_self_learning_provenance_eligibility_v1,
)


def require_learning_scope_v1(
    *, outcome: Mapping[str, Any], scope: Mapping[str, Any], target: Mapping[str, Any]
) -> None:
    require_self_learning_provenance_eligibility_v1(outcome)
    p = outcome["outcome_evidence_provenance"]
    expected = {
        "outcome_semantic_class": p["outcome_semantic_class"],
        "market_observation_source": p["market_observation_source"],
        "external_capital_flow_class": p["external_capital_flow_class"],
        "code_sha": outcome["code_sha"],
        "config_hash": outcome["config_hash"],
        "outcome_scalar_kind": p["outcome_scalar_kind"],
        "evaluation_horizon": outcome["evaluation_horizon"],
    }
    if any(scope.get(k) != v for k, v in expected.items()):
        raise DdoValidationError("LEARNING_SCOPE_MISMATCH")
    if (
        p["external_capital_flow_class"] != "NONE"
        or scope.get("target") != dict(target)
        or not scope.get("account_identity")
        or scope.get("metric_version") != "FIRST_LAST_CLOSE_LOG_RETURN_V1"
        or scope.get("evidence_pool_class") != p["outcome_semantic_class"]
        or outcome["code_sha"] == "UNKNOWN"
        or outcome["config_hash"] == "UNKNOWN"
    ):
        raise DdoValidationError("LEARNING_SCOPE_UNBOUND")
