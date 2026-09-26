"""Bounded Meta → Learning research adaptation input (LEARNING_REPRESENTATION route only).

Typed research-input acknowledgment only. Does not mutate learning state, weights,
thresholds, trading configuration, or productive features.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    UNKNOWN_UNAVAILABLE,
    validate_meta_learning_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_meta_to_learning_research_adaptation_input_v1"
INPUT_DOMAIN: Final[str] = "peak_trade.canonical_meta_to_learning_research_adaptation_input.v1"
DECISION_SCHEMA_VERSION: Final[str] = "bounded_learning_research_adaptation_decision_v1"

DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT: Final[str] = (
    "PROPOSE_REPRESENTATION_RESEARCH_CONTEXT"
)
DISPOSITION_NO_ACTION_FAIL_CLOSED: Final[str] = "NO_ACTION_FAIL_CLOSED"

OUTCOME_APPLICABLE: Final[str] = "APPLICABLE_LEARNING_RESEARCH_INPUT_ONLY"
OUTCOME_FAIL_CLOSED: Final[str] = "FAIL_CLOSED"

REASON_STALE_META_EVIDENCE: Final[str] = "META_LEARNING_EVIDENCE_SCHEMA_STALE"
REASON_LINEAGE_MISMATCH: Final[str] = "META_EVIDENCE_LINEAGE_MISMATCH"
REASON_MISSING_REPRESENTATION_LINEAGE: Final[str] = "LEARNING_REPRESENTATION_LINEAGE_MISSING"

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
NO_SELF_MODIFYING_LEARNING: Final[bool] = True
NO_DIRECT_FEATURE_DROP: Final[bool] = True
NO_DIRECT_PARAMETER_MUTATION: Final[bool] = True
TRADING_SELECTION_EFFECT: Final[str] = "NONE"

_LOGGER = logging.getLogger(__name__)


class MetaToLearningResearchAdaptationInputError(ValueError):
    """Fail-closed meta-to-learning research adaptation input error."""


@dataclass(frozen=True)
class MetaToLearningResearchAdaptationInputRequestV1:
    meta_learning_evidence: Mapping[str, Any] | None
    expected_meta_evidence_id: str | None = None
    expected_meta_learning_evidence_schema_version: str | None = (
        META_LEARNING_EVIDENCE_SCHEMA_VERSION
    )
    requested_learning_state_mutation: bool = False
    requested_parameter_mutation: bool = False
    requested_feature_drop: bool = False
    requested_trading_instrument_selection: bool = False
    requested_promotion: bool = False


def validate_meta_to_learning_research_adaptation_input_v1(
    request: MetaToLearningResearchAdaptationInputRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_learning_state_mutation:
        raise MetaToLearningResearchAdaptationInputError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_parameter_mutation:
        raise MetaToLearningResearchAdaptationInputError("PARAMETER_MUTATION_FORBIDDEN")
    if request.requested_feature_drop:
        raise MetaToLearningResearchAdaptationInputError("FEATURE_DROP_FORBIDDEN")
    if request.requested_trading_instrument_selection:
        raise MetaToLearningResearchAdaptationInputError("TRADING_INSTRUMENT_SELECTION_FORBIDDEN")
    if request.requested_promotion:
        raise MetaToLearningResearchAdaptationInputError("PROMOTION_FORBIDDEN")

    if request.expected_meta_learning_evidence_schema_version not in (
        None,
        META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    ):
        return _decision_payload(
            meta_evidence=None,
            adaptation_items=(),
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason=REASON_STALE_META_EVIDENCE,
        )

    if request.meta_learning_evidence is None:
        return _decision_payload(
            meta_evidence=None,
            adaptation_items=(),
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason="MISSING_META_LEARNING_EVIDENCE",
        )

    try:
        meta = validate_meta_learning_evidence_v1(request.meta_learning_evidence)
    except Exception as exc:
        _LOGGER.debug("meta learning evidence invalid: %s", exc)
        return _decision_payload(
            meta_evidence=None,
            adaptation_items=(),
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason="META_LEARNING_EVIDENCE_MALFORMED",
        )

    if request.expected_meta_evidence_id is not None:
        if str(meta.get("meta_evidence_id")) != request.expected_meta_evidence_id:
            return _decision_payload(
                meta_evidence=meta,
                adaptation_items=(),
                overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
                overall_reason=REASON_LINEAGE_MISMATCH,
            )

    provenance = meta.get("provenance")
    lineage_ref = None
    if isinstance(provenance, Mapping):
        lineage_ref = provenance.get("learning_representation_lineage_ref")
    if not isinstance(lineage_ref, str) or not lineage_ref.strip():
        return _decision_payload(
            meta_evidence=meta,
            adaptation_items=(
                _adaptation_item(
                    disposition=DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
                    outcome=OUTCOME_FAIL_CLOSED,
                    reason=REASON_MISSING_REPRESENTATION_LINEAGE,
                    payload={},
                ),
            ),
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason=REASON_MISSING_REPRESENTATION_LINEAGE,
        )

    pattern = str(meta.get("repeated_success_or_failure_pattern") or UNKNOWN_UNAVAILABLE)
    items = (
        _adaptation_item(
            disposition=DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
            outcome=OUTCOME_APPLICABLE,
            reason="REPRESENTATION_RESEARCH_CONTEXT_ONLY",
            payload={
                "learning_representation_lineage_ref": lineage_ref.strip(),
                "pattern_ref": pattern,
                "learning_state_mutation_authorized": False,
                "productive_apply_authorized": False,
            },
        ),
    )
    return _decision_payload(
        meta_evidence=meta,
        adaptation_items=items,
        overall_disposition=DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
        overall_reason="BOUNDED_LEARNING_RESEARCH_ADAPTATION_INPUT_ONLY",
    )


def derive_learning_adaptation_decision_identity_v1(
    *,
    meta_evidence_id: str,
    adaptation_items: Sequence[Mapping[str, Any]],
) -> str:
    body = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "domain": INPUT_DOMAIN,
        "meta_evidence_id": meta_evidence_id,
        "adaptation_items": tuple(adaptation_items),
    }
    return compute_content_sha256(body)


def _adaptation_item(
    *,
    disposition: str,
    outcome: str,
    reason: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "disposition": disposition,
        "outcome": outcome,
        "reason": reason,
        "payload": dict(payload),
        "proposal_not_authority": True,
        "learning_state_mutation_authorized": False,
        "trading_selection_effect": TRADING_SELECTION_EFFECT,
    }


def _decision_payload(
    *,
    meta_evidence: Mapping[str, Any] | None,
    adaptation_items: Sequence[Mapping[str, Any]],
    overall_disposition: str,
    overall_reason: str,
) -> MappingProxyType[str, Any]:
    meta_id = str(meta_evidence.get("meta_evidence_id")) if meta_evidence else None
    decision_identity = (
        derive_learning_adaptation_decision_identity_v1(
            meta_evidence_id=meta_id,
            adaptation_items=adaptation_items,
        )
        if meta_id and is_valid_sha256_hex(meta_id)
        else None
    )
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_schema_version": DECISION_SCHEMA_VERSION,
        "domain": INPUT_DOMAIN,
        "adaptation_decision_identity": decision_identity,
        "overall_disposition": overall_disposition,
        "overall_reason": overall_reason,
        "adaptation_items": list(adaptation_items),
        "source_meta_evidence_id": meta_id,
        "source_meta_reproducibility_digest": (
            str(meta_evidence.get("reproducibility_digest")) if meta_evidence else None
        ),
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "no_self_modifying_learning": NO_SELF_MODIFYING_LEARNING,
        "no_direct_feature_drop": NO_DIRECT_FEATURE_DROP,
        "no_direct_parameter_mutation": NO_DIRECT_PARAMETER_MUTATION,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return MappingProxyType(body)


__all__ = [
    "INPUT_DOMAIN",
    "MetaToLearningResearchAdaptationInputError",
    "MetaToLearningResearchAdaptationInputRequestV1",
    "NO_DIRECT_FEATURE_DROP",
    "NO_DIRECT_PARAMETER_MUTATION",
    "NO_SELF_MODIFYING_LEARNING",
    "SCHEMA_VERSION",
    "validate_meta_to_learning_research_adaptation_input_v1",
]
