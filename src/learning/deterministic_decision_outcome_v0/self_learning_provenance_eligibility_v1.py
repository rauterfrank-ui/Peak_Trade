"""Self-Learning provenance eligibility gate v1 — semantic admissibility, not trading authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.outcome_evidence_provenance_v1 import (
    ExternalCapitalFlowClassV1,
    OutcomeSemanticClassV1,
    extract_outcome_provenance_from_record_v1,
    provenance_implies_productive_truth_v1,
    validate_outcome_evidence_provenance_v1,
)

GATE_ID: Final[str] = "peak_trade.learning.ddo.self_learning_provenance_eligibility_v1"
SELF_LEARNING_TRADING_AUTHORITY: Final[str] = "NONE"

_ADMITTED_CLASSES: Final[frozenset[str]] = frozenset(
    {
        OutcomeSemanticClassV1.OBSERVED_PRODUCTIVE_PRE_EXTERNAL.value,
        OutcomeSemanticClassV1.INTERNAL_SIMULATED_OUTCOME.value,
        OutcomeSemanticClassV1.I67_PAPER_SIM_OUTCOME.value,
        OutcomeSemanticClassV1.SHADOW_COUNTERFACTUAL.value,
        OutcomeSemanticClassV1.TESTNET_VENUE_EVIDENCE.value,
        OutcomeSemanticClassV1.REPLAY_HISTORICAL.value,
        OutcomeSemanticClassV1.DDO_OBSERVATION_ONLY.value,
        OutcomeSemanticClassV1.CANARY_EVIDENCE.value,
    }
)

_REJECTED_EXTERNAL_CAPITAL: Final[frozenset[str]] = frozenset(
    {
        ExternalCapitalFlowClassV1.DEPOSIT.value,
        ExternalCapitalFlowClassV1.WITHDRAWAL.value,
        ExternalCapitalFlowClassV1.INTERNAL_TRANSFER.value,
        ExternalCapitalFlowClassV1.AMBIGUOUS.value,
    }
)


@dataclass(frozen=True)
class SelfLearningEligibilityResultV1:
    admitted: bool
    reason_code: str
    outcome_semantic_class: str
    provenance_digest: str | None


def evaluate_self_learning_provenance_eligibility_v1(
    outcome_record: Mapping[str, Any],
    *,
    prior_outcome_semantic_class: str | None = None,
) -> SelfLearningEligibilityResultV1:
    block = outcome_record.get("outcome_evidence_provenance")
    if block is None:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code="LEGACY_OUTCOME_MISSING_PROVENANCE",
            outcome_semantic_class=OutcomeSemanticClassV1.UNKNOWN.value,
            provenance_digest=None,
        )
    provenance = validate_outcome_evidence_provenance_v1(block)
    status = str(provenance["provenance_status"])
    oclass = str(provenance["outcome_semantic_class"])
    digest = str(provenance["provenance_digest"])
    if status in {"UNKNOWN", "AMBIGUOUS"}:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code=f"PROVENANCE_STATUS_{status}",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
        )
    if oclass in {OutcomeSemanticClassV1.UNKNOWN.value, OutcomeSemanticClassV1.AMBIGUOUS.value}:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code=f"OUTCOME_SEMANTIC_CLASS_{oclass}",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
        )
    ext = str(provenance["external_capital_flow_class"])
    if ext in _REJECTED_EXTERNAL_CAPITAL:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code="EXTERNAL_CAPITAL_FLOW_NOT_TRADING_OUTCOME",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
        )
    if oclass not in _ADMITTED_CLASSES:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code="OUTCOME_CLASS_NOT_ADMITTED",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
        )
    if prior_outcome_semantic_class is not None and prior_outcome_semantic_class != oclass:
        return SelfLearningEligibilityResultV1(
            admitted=False,
            reason_code="INCOMPATIBLE_OUTCOME_CLASS_IN_SCOPE",
            outcome_semantic_class=oclass,
            provenance_digest=digest,
        )
    _ = provenance_implies_productive_truth_v1(provenance)
    return SelfLearningEligibilityResultV1(
        admitted=True,
        reason_code="ADMITTED",
        outcome_semantic_class=oclass,
        provenance_digest=digest,
    )


def require_self_learning_provenance_eligibility_v1(
    outcome_record: Mapping[str, Any],
    *,
    prior_outcome_semantic_class: str | None = None,
) -> SelfLearningEligibilityResultV1:
    result = evaluate_self_learning_provenance_eligibility_v1(
        outcome_record, prior_outcome_semantic_class=prior_outcome_semantic_class
    )
    if not result.admitted:
        raise DdoValidationError(result.reason_code)
    return result


def outcome_semantic_class_from_record_v1(outcome_record: Mapping[str, Any]) -> str:
    prov = extract_outcome_provenance_from_record_v1(outcome_record)
    if prov is None:
        return OutcomeSemanticClassV1.UNKNOWN.value
    return str(prov["outcome_semantic_class"])
