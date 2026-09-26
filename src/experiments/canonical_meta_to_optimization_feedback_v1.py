"""M7 — Meta-learning evidence to optimization-universe bounded research feedback.

Typed feedback boundary only. Does not execute search, promote, authorize surfaces,
or mutate shared state between universes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_advanced_search_v1 import (
    ADVANCED_SEARCH_DOMAIN,
    SCHEMA_VERSION as ADVANCED_SEARCH_SCHEMA_VERSION,
    SUPPORTED_SEARCH_METHODS,
)
from src.experiments.canonical_optimization_surface_portfolio_registry_v1 import (
    evaluate_meta_optimization_family_portfolio_gate_v1,
)
from src.experiments.canonical_optimization_universe_v1 import (
    build_optimization_universe_capability_registry_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    UNKNOWN_UNAVAILABLE,
    validate_meta_learning_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_meta_to_optimization_feedback_v1"
FEEDBACK_DOMAIN: Final[str] = "peak_trade.canonical_meta_to_optimization_feedback.v1"
DECISION_SCHEMA_VERSION: Final[str] = "bounded_research_feedback_decision_v1"

DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT: Final[str] = "PRIORITIZE_RESEARCH_EXPERIMENT"
DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD: Final[str] = (
    "SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD"
)
DISPOSITION_ALLOCATE_BOUNDED_RESEARCH_BUDGET: Final[str] = "ALLOCATE_BOUNDED_RESEARCH_BUDGET"
DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS: Final[str] = "PROPOSE_RESEARCH_HYPOTHESIS"
DISPOSITION_NO_ACTION_FAIL_CLOSED: Final[str] = "NO_ACTION_FAIL_CLOSED"

OUTCOME_APPLICABLE: Final[str] = "APPLICABLE_RESEARCH_FEEDBACK_ONLY"
OUTCOME_FAIL_CLOSED: Final[str] = "FAIL_CLOSED"

REASON_SEARCH_METHOD_UNKNOWN: Final[str] = "M6_SEARCH_METHOD_TOKEN_UNKNOWN"
REASON_SEARCH_CAPABILITY_NOT_REGISTERED: Final[str] = (
    "ADVANCED_SEARCH_NOT_IN_OPTIMIZATION_UNIVERSE_REGISTRY"
)
REASON_OPTIMIZATION_FAMILY_UNKNOWN: Final[str] = "M6_OPTIMIZATION_FAMILY_UNKNOWN"
REASON_PREDICTIVE_FEATURES_UNKNOWN: Final[str] = "M6_PREDICTIVE_FEATURES_UNKNOWN"
REASON_UNCERTAINTY_UNKNOWN: Final[str] = "M6_UNCERTAINTY_UNKNOWN"
REASON_NO_SOURCE_EXPERIMENTS: Final[str] = "NO_SOURCE_EXPERIMENT_IDS"
REASON_STALE_META_EVIDENCE: Final[str] = "META_LEARNING_EVIDENCE_SCHEMA_STALE"
REASON_LINEAGE_MISMATCH: Final[str] = "META_EVIDENCE_LINEAGE_MISMATCH"

DEFAULT_BOUNDED_RESEARCH_BUDGET_UNITS: Final[int] = 1
ADVANCED_SEARCH_CAPABILITY_ID: Final[str] = ADVANCED_SEARCH_DOMAIN

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True
SEARCH_EXECUTED: Final[bool] = False
TRADING_SELECTION_EFFECT: Final[str] = "NONE"

_LOGGER = logging.getLogger(__name__)


class MetaToOptimizationFeedbackError(ValueError):
    """Fail-closed meta-to-optimization feedback request error."""


@dataclass(frozen=True)
class MetaToOptimizationFeedbackInputRequestV1:
    meta_learning_evidence: Mapping[str, Any] | None
    expected_meta_evidence_id: str | None = None
    expected_meta_learning_evidence_schema_version: str | None = (
        META_LEARNING_EVIDENCE_SCHEMA_VERSION
    )
    requested_search_execution: bool = False
    requested_trading_instrument_selection: bool = False
    requested_promotion: bool = False
    requested_envelope_bypass: bool = False


def _registered_capability_ids() -> frozenset[str]:
    registry = build_optimization_universe_capability_registry_v1()
    entries = registry.get("entries")
    if not isinstance(entries, tuple):
        return frozenset()
    return frozenset(str(entry["capability_id"]) for entry in entries)


def validate_meta_to_optimization_feedback_input_v1(
    request: MetaToOptimizationFeedbackInputRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_search_execution:
        raise MetaToOptimizationFeedbackError("SEARCH_EXECUTION_FORBIDDEN")
    if request.requested_trading_instrument_selection:
        raise MetaToOptimizationFeedbackError("TRADING_INSTRUMENT_SELECTION_FORBIDDEN")
    if request.requested_promotion:
        raise MetaToOptimizationFeedbackError("PROMOTION_FORBIDDEN")
    if request.requested_envelope_bypass:
        raise MetaToOptimizationFeedbackError("ENVELOPE_BYPASS_FORBIDDEN")

    if request.expected_meta_learning_evidence_schema_version not in (
        None,
        META_LEARNING_EVIDENCE_SCHEMA_VERSION,
    ):
        return build_bounded_research_feedback_decision_v1(
            meta_evidence=None,
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason=REASON_STALE_META_EVIDENCE,
            feedback_items=(),
        )

    if request.meta_learning_evidence is None:
        return build_bounded_research_feedback_decision_v1(
            meta_evidence=None,
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason="MISSING_META_LEARNING_EVIDENCE",
            feedback_items=(),
        )

    try:
        meta = validate_meta_learning_evidence_v1(request.meta_learning_evidence)
    except Exception as exc:
        _LOGGER.debug("meta learning evidence invalid: %s", exc)
        return build_bounded_research_feedback_decision_v1(
            meta_evidence=None,
            overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
            overall_reason="META_LEARNING_EVIDENCE_MALFORMED",
            feedback_items=(),
        )

    if request.expected_meta_evidence_id is not None:
        if str(meta.get("meta_evidence_id")) != request.expected_meta_evidence_id:
            return build_bounded_research_feedback_decision_v1(
                meta_evidence=meta,
                overall_disposition=DISPOSITION_NO_ACTION_FAIL_CLOSED,
                overall_reason=REASON_LINEAGE_MISMATCH,
                feedback_items=(),
            )

    return build_bounded_research_feedback_decision_v1(
        meta_evidence=meta,
        overall_disposition=None,
        overall_reason=None,
        feedback_items=None,
    )


def build_bounded_research_feedback_decision_v1(
    *,
    meta_evidence: Mapping[str, Any] | None,
    overall_disposition: str | None,
    overall_reason: str | None,
    feedback_items: Sequence[Mapping[str, Any]] | None,
) -> MappingProxyType[str, Any]:
    if overall_disposition is not None:
        return _decision_payload(
            meta_evidence=meta_evidence,
            feedback_items=tuple(feedback_items or ()),
            overall_disposition=overall_disposition,
            overall_reason=overall_reason or DISPOSITION_NO_ACTION_FAIL_CLOSED,
        )

    assert meta_evidence is not None
    items: list[dict[str, Any]] = []
    registered = _registered_capability_ids()

    source_ids = meta_evidence.get("source_experiment_ids") or ()
    if isinstance(source_ids, (list, tuple)) and source_ids:
        items.append(
            _feedback_item(
                disposition=DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT,
                outcome=OUTCOME_APPLICABLE,
                reason="SOURCE_EXPERIMENT_IDS_PRESENT",
                payload={
                    "experiment_ids": tuple(str(item) for item in source_ids),
                    "proposal_not_authority": True,
                },
            )
        )
    else:
        items.append(
            _feedback_item(
                disposition=DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT,
                outcome=OUTCOME_FAIL_CLOSED,
                reason=REASON_NO_SOURCE_EXPERIMENTS,
                payload={},
            )
        )

    search_method = meta_evidence.get("search_method")
    method_token = UNKNOWN_UNAVAILABLE
    schema_ref = None
    if isinstance(search_method, Mapping):
        method_token = str(search_method.get("method_token") or UNKNOWN_UNAVAILABLE)
        schema_ref = search_method.get("advanced_search_schema_version")

    if method_token != UNKNOWN_UNAVAILABLE and method_token in SUPPORTED_SEARCH_METHODS:
        if ADVANCED_SEARCH_CAPABILITY_ID not in registered:
            items.append(
                _feedback_item(
                    disposition=DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
                    outcome=OUTCOME_FAIL_CLOSED,
                    reason=REASON_SEARCH_CAPABILITY_NOT_REGISTERED,
                    payload={
                        "requested_method": method_token,
                        "advanced_search_schema_version": schema_ref,
                    },
                )
            )
        else:
            items.append(
                _feedback_item(
                    disposition=DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
                    outcome=OUTCOME_APPLICABLE,
                    reason="REGISTERED_RESEARCH_SEARCH_METHOD",
                    payload={
                        "search_method": method_token,
                        "advanced_search_schema_version": schema_ref,
                    },
                )
            )
    else:
        items.append(
            _feedback_item(
                disposition=DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
                outcome=OUTCOME_FAIL_CLOSED,
                reason=REASON_SEARCH_METHOD_UNKNOWN,
                payload={
                    "method_token": method_token,
                    "advanced_search_schema_version": schema_ref,
                    "supported_methods": list(SUPPORTED_SEARCH_METHODS),
                },
            )
        )

    support_count = int(meta_evidence.get("support_count") or 0)
    budget_units = min(DEFAULT_BOUNDED_RESEARCH_BUDGET_UNITS, max(support_count, 1))
    items.append(
        _feedback_item(
            disposition=DISPOSITION_ALLOCATE_BOUNDED_RESEARCH_BUDGET,
            outcome=OUTCOME_APPLICABLE,
            reason="BOUNDED_RESEARCH_BUDGET_ONLY",
            payload={
                "research_budget_units": budget_units,
                "productive_budget_authority": "NONE",
            },
        )
    )

    pattern = str(meta_evidence.get("repeated_success_or_failure_pattern") or "")
    opt_family = meta_evidence.get("optimization_family")
    predictive = meta_evidence.get("predictive_evidence_features")
    uncertainty = meta_evidence.get("uncertainty")
    portfolio_gate = evaluate_meta_optimization_family_portfolio_gate_v1(
        optimization_family=str(opt_family or UNKNOWN_UNAVAILABLE)
    )
    if portfolio_gate.explicit_family_reference:
        outcome = OUTCOME_APPLICABLE if portfolio_gate.research_choice_allowed else OUTCOME_FAIL_CLOSED
        items.append(
            _feedback_item(
                disposition=DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS,
                outcome=outcome,
                reason=portfolio_gate.reason,
                payload={
                    **dict(portfolio_gate.payload),
                    "phase_11_portfolio_gate": True,
                    "predictive_evidence_features": predictive,
                    "uncertainty": uncertainty,
                },
            )
        )
    elif pattern and opt_family == UNKNOWN_UNAVAILABLE:
        items.append(
            _feedback_item(
                disposition=DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS,
                outcome=OUTCOME_APPLICABLE,
                reason="OPAQUE_PATTERN_ONLY_OPTIMIZATION_FAMILY_UNKNOWN",
                payload={
                    "hypothesis_pattern_ref": pattern,
                    "optimization_family": UNKNOWN_UNAVAILABLE,
                    "predictive_evidence_features": predictive,
                    "uncertainty": uncertainty,
                },
            )
        )
    else:
        items.append(
            _feedback_item(
                disposition=DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS,
                outcome=OUTCOME_FAIL_CLOSED,
                reason=REASON_OPTIMIZATION_FAMILY_UNKNOWN,
                payload={},
            )
        )

    applicable = [item for item in items if item["outcome"] == OUTCOME_APPLICABLE]
    overall = DISPOSITION_NO_ACTION_FAIL_CLOSED if not applicable else applicable[0]["disposition"]
    overall_reason = (
        "PARTIAL_RESEARCH_FEEDBACK_WITH_FAIL_CLOSED_ITEMS"
        if len(applicable) < len(items)
        else "BOUNDED_RESEARCH_FEEDBACK_ONLY"
    )

    return _decision_payload(
        meta_evidence=meta_evidence,
        feedback_items=tuple(items),
        overall_disposition=overall,
        overall_reason=overall_reason,
    )


def derive_feedback_decision_identity_v1(
    *,
    meta_evidence_id: str,
    feedback_items: Sequence[Mapping[str, Any]],
) -> str:
    body = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "domain": FEEDBACK_DOMAIN,
        "meta_evidence_id": meta_evidence_id,
        "feedback_items": tuple(feedback_items),
    }
    return compute_content_sha256(body)


def _feedback_item(
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
        "search_execution_authorized": False,
        "trading_selection_effect": TRADING_SELECTION_EFFECT,
    }


def _decision_payload(
    *,
    meta_evidence: Mapping[str, Any] | None,
    feedback_items: Sequence[Mapping[str, Any]],
    overall_disposition: str,
    overall_reason: str,
) -> MappingProxyType[str, Any]:
    meta_id = str(meta_evidence.get("meta_evidence_id")) if meta_evidence else None
    decision_identity = (
        derive_feedback_decision_identity_v1(
            meta_evidence_id=meta_id,
            feedback_items=feedback_items,
        )
        if meta_id and is_valid_sha256_hex(meta_id)
        else None
    )
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "decision_schema_version": DECISION_SCHEMA_VERSION,
        "domain": FEEDBACK_DOMAIN,
        "feedback_decision_identity": decision_identity,
        "overall_disposition": overall_disposition,
        "overall_reason": overall_reason,
        "feedback_items": feedback_items,
        "source_meta_evidence_id": meta_id,
        "source_meta_reproducibility_digest": (
            str(meta_evidence.get("reproducibility_digest")) if meta_evidence else None
        ),
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
        "search_executed": SEARCH_EXECUTED,
        "trading_selection_effect": TRADING_SELECTION_EFFECT,
        "advanced_search_schema_version": ADVANCED_SEARCH_SCHEMA_VERSION,
        "optimization_universe_registry_digest": build_optimization_universe_capability_registry_v1()[
            "registry_digest"
        ],
    }
    body["result_digest"] = compute_content_sha256(
        _json_safe({key: value for key, value in body.items() if key != "result_digest"})
    )
    return MappingProxyType(body)


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
