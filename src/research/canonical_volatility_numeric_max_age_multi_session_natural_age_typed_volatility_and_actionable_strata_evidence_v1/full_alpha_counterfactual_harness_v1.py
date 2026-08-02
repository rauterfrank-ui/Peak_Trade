"""Read-only Full-Alpha counterfactual harness (volatility DI only)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Mapping, Optional

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    SCHEMA_FULL_ALPHA_COUNTERFACTUAL,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    AlphaComponentSnapshotV1,
    MultiSessionTypedVolEvidenceError,
    classify_first_divergence_v1,
    sha256_hex_canonical,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.typed_volatility_comparison_v1 import (
    assert_estimates_contract_compatible_v1,
    clone_aged_estimate_immutable_v1,
)
from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextV1,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CanonicalVolatilityEstimateV1,
)

AlphaEvaluator = Callable[[CanonicalMarketContextV1], AlphaComponentSnapshotV1]


def _assert_no_side_effects_v1(snapshot: AlphaComponentSnapshotV1) -> None:
    if snapshot.order_intents:
        raise MultiSessionTypedVolEvidenceError("counterfactual_order_activity_forbidden")
    if snapshot.state_mutations:
        raise MultiSessionTypedVolEvidenceError("counterfactual_state_mutation_forbidden")


def build_frozen_market_context_shell_v1(
    *,
    base_context: CanonicalMarketContextV1,
    market_context_digest: str,
) -> CanonicalMarketContextV1:
    """Freeze non-volatility inputs; clear typed/legacy vol before DI."""
    cleared = replace(
        base_context,
        canonical_volatility_estimate=None,
        volatility_estimate=0.0,
        input_digest="",
    )
    frozen = with_computed_input_digest(cleared)
    # Digests over non-vol shell are caller-owned; retain explicit digest binding.
    if market_context_digest and not str(market_context_digest).strip():
        raise MultiSessionTypedVolEvidenceError("market_context_digest_invalid")
    return frozen


def evaluate_with_injected_volatility_v1(
    *,
    frozen_context: CanonicalMarketContextV1,
    estimate: CanonicalVolatilityEstimateV1,
    evaluator: AlphaEvaluator,
) -> tuple[CanonicalMarketContextV1, AlphaComponentSnapshotV1]:
    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        frozen_context,
        estimate,
    )
    snapshot = evaluator(bound)
    _assert_no_side_effects_v1(snapshot)
    return bound, snapshot


def default_digest_alpha_evaluator_v1(
    context: CanonicalMarketContextV1,
) -> AlphaComponentSnapshotV1:
    """Default read-only evaluator: digest-stable component projection from CMC.

    Does not invent Bull/Bear/Double-Play thresholds. Uses bound volatility
    presence/value as the sole injected variable and leaves other components
    as frozen placeholders derived from context digests — suitable for DI
    confounder tests and for production adapters that replace this evaluator.
    """
    estimate = context.canonical_volatility_estimate
    if estimate is None:
        raise MultiSessionTypedVolEvidenceError("typed_estimate_required_for_evaluation")
    vol_token = f"{estimate.value:.12g}|{estimate.source_digest}"
    base = context.input_digest or "no_input_digest"
    # Components identical except those that legitimately depend on injected vol.
    directional = f"directional_bound:{base}"
    survival = f"survival_bound:{base}"
    suitability = f"suitability_bound:{base}"
    composition = f"composition_bound:{base}"
    switch_state = f"switch_bound:{base}"
    # Entry permission / outcome / final may diverge with volatility injection.
    entry_permission = f"entry_permission:{vol_token}"
    entry_outcome = f"entry_outcome:{vol_token}"
    hold_reduce_exit = f"hold_reduce_exit_bound:{base}"
    final_outcome = f"final:{entry_outcome}|{hold_reduce_exit}"
    payload = {
        "composition": composition,
        "directional_assessment": directional,
        "entry_outcome": entry_outcome,
        "entry_permission": entry_permission,
        "final_outcome": final_outcome,
        "hold_reduce_exit": hold_reduce_exit,
        "suitability": suitability,
        "survival": survival,
        "switch_state": switch_state,
        "volatility_source_digest": estimate.source_digest,
        "volatility_value": float(estimate.value),
    }
    return AlphaComponentSnapshotV1(
        directional_assessment=directional,
        survival=survival,
        suitability=suitability,
        composition=composition,
        switch_state=switch_state,
        entry_permission=entry_permission,
        entry_outcome=entry_outcome,
        hold_reduce_exit=hold_reduce_exit,
        final_outcome=final_outcome,
        evaluation_digest=sha256_hex_canonical(payload),
        order_intents=(),
        state_mutations=(),
    )


def run_full_alpha_counterfactual_comparison_v1(
    *,
    session_id: str,
    market_sample_id: str,
    market_context_digest: str,
    prior_state_digest: str,
    frozen_context: CanonicalMarketContextV1,
    aged_estimate: CanonicalVolatilityEstimateV1,
    fresh_estimate: Optional[CanonicalVolatilityEstimateV1],
    age_seconds: float,
    aged_volatility_record_id: str,
    fresh_volatility_record_id: str,
    evaluator: AlphaEvaluator | None = None,
    non_volatility_input_digest: str | None = None,
    expected_non_volatility_input_digest: str | None = None,
) -> dict[str, Any]:
    """Compare aged vs fresh evaluations with identical non-vol inputs."""
    eval_fn = evaluator or default_digest_alpha_evaluator_v1
    if (
        expected_non_volatility_input_digest is not None
        and non_volatility_input_digest is not None
        and non_volatility_input_digest != expected_non_volatility_input_digest
    ):
        return {
            "schema": SCHEMA_FULL_ALPHA_COUNTERFACTUAL,
            "COUNTERFACTUAL_COMPARISON_ID": sha256_hex_canonical(
                {
                    "session_id": session_id,
                    "market_sample_id": market_sample_id,
                    "age_seconds": age_seconds,
                }
            ),
            "SESSION_ID": session_id,
            "MARKET_SAMPLE_ID": market_sample_id,
            "MARKET_CONTEXT_DIGEST": market_context_digest,
            "classification": "NOT_COMPARABLE",
            "FIRST_DIVERGENCE_COMPONENT": "NON_VOLATILITY_INPUT",
            "AGE_ONLY_CAUSALITY_SUPPORTED": False,
            "CONFOUNDERS": ["NON_VOLATILITY_INPUT_DIGEST_MISMATCH"],
            "NON_PERSISTING_READ_ONLY": True,
            "COUNTERFACTUAL_STATE_MUTATION_OCCURRED": False,
            "COUNTERFACTUAL_ORDER_ACTIVITY_OCCURRED": False,
        }

    aged = clone_aged_estimate_immutable_v1(aged_estimate)
    shell = build_frozen_market_context_shell_v1(
        base_context=frozen_context,
        market_context_digest=market_context_digest,
    )
    if fresh_estimate is None:
        return {
            "schema": SCHEMA_FULL_ALPHA_COUNTERFACTUAL,
            "COUNTERFACTUAL_COMPARISON_ID": sha256_hex_canonical(
                {
                    "session_id": session_id,
                    "market_sample_id": market_sample_id,
                    "age_seconds": age_seconds,
                    "status": "FRESH_ESTIMATE_UNAVAILABLE",
                }
            ),
            "SESSION_ID": session_id,
            "MARKET_SAMPLE_ID": market_sample_id,
            "MARKET_CONTEXT_DIGEST": market_context_digest,
            "AGED_VOLATILITY_RECORD_ID": aged_volatility_record_id,
            "FRESH_VOLATILITY_RECORD_ID": fresh_volatility_record_id,
            "VOLATILITY_AGE_SECONDS": float(age_seconds),
            "PRIOR_STATE_DIGEST": prior_state_digest,
            "classification": "FRESH_ESTIMATE_UNAVAILABLE",
            "FIRST_DIVERGENCE_COMPONENT": "NONE",
            "AGE_ONLY_CAUSALITY_SUPPORTED": False,
            "CONFOUNDERS": ["FRESH_ESTIMATE_UNAVAILABLE"],
            "NON_PERSISTING_READ_ONLY": True,
            "COUNTERFACTUAL_STATE_MUTATION_OCCURRED": False,
            "COUNTERFACTUAL_ORDER_ACTIVITY_OCCURRED": False,
        }

    try:
        assert_estimates_contract_compatible_v1(aged, fresh_estimate)
    except MultiSessionTypedVolEvidenceError as exc:
        return {
            "schema": SCHEMA_FULL_ALPHA_COUNTERFACTUAL,
            "COUNTERFACTUAL_COMPARISON_ID": sha256_hex_canonical(
                {"session_id": session_id, "err": str(exc)}
            ),
            "SESSION_ID": session_id,
            "MARKET_SAMPLE_ID": market_sample_id,
            "MARKET_CONTEXT_DIGEST": market_context_digest,
            "classification": "NOT_COMPARABLE",
            "FIRST_DIVERGENCE_COMPONENT": "CONTRACT_COMPATIBILITY",
            "AGE_ONLY_CAUSALITY_SUPPORTED": False,
            "CONFOUNDERS": [str(exc)],
            "NON_PERSISTING_READ_ONLY": True,
            "COUNTERFACTUAL_STATE_MUTATION_OCCURRED": False,
            "COUNTERFACTUAL_ORDER_ACTIVITY_OCCURRED": False,
        }

    _bound_aged, aged_snap = evaluate_with_injected_volatility_v1(
        frozen_context=shell,
        estimate=aged,
        evaluator=eval_fn,
    )
    _bound_fresh, fresh_snap = evaluate_with_injected_volatility_v1(
        frozen_context=shell,
        estimate=fresh_estimate,
        evaluator=eval_fn,
    )
    classification, first = classify_first_divergence_v1(aged_snap, fresh_snap)
    aged_d = aged_snap.to_dict()
    fresh_d = fresh_snap.to_dict()
    payload = {
        "schema": SCHEMA_FULL_ALPHA_COUNTERFACTUAL,
        "schema_version": "v1",
        "COUNTERFACTUAL_COMPARISON_ID": sha256_hex_canonical(
            {
                "aged_eval": aged_snap.evaluation_digest,
                "fresh_eval": fresh_snap.evaluation_digest,
                "market_sample_id": market_sample_id,
                "session_id": session_id,
            }
        ),
        "SESSION_ID": session_id,
        "MARKET_SAMPLE_ID": market_sample_id,
        "MARKET_CONTEXT_DIGEST": market_context_digest,
        "AGED_VOLATILITY_RECORD_ID": aged_volatility_record_id,
        "FRESH_VOLATILITY_RECORD_ID": fresh_volatility_record_id,
        "VOLATILITY_AGE_SECONDS": float(age_seconds),
        "PRIOR_STATE_DIGEST": prior_state_digest,
        "AGED_EVALUATION_DIGEST": aged_snap.evaluation_digest,
        "FRESH_EVALUATION_DIGEST": fresh_snap.evaluation_digest,
        "FIRST_DIVERGENCE_COMPONENT": first,
        "classification": classification,
        "DIRECTIONAL_ASSESSMENT_CHANGED": (
            aged_d["directional_assessment"] != fresh_d["directional_assessment"]
        ),
        "SURVIVAL_CHANGED": aged_d["survival"] != fresh_d["survival"],
        "SUITABILITY_CHANGED": aged_d["suitability"] != fresh_d["suitability"],
        "COMPOSITION_CHANGED": aged_d["composition"] != fresh_d["composition"],
        "SWITCH_STATE_CHANGED": aged_d["switch_state"] != fresh_d["switch_state"],
        "ENTRY_PERMISSION_CHANGED": (aged_d["entry_permission"] != fresh_d["entry_permission"]),
        "ENTRY_OUTCOME_CHANGED": aged_d["entry_outcome"] != fresh_d["entry_outcome"],
        "HOLD_REDUCE_EXIT_CHANGED": (aged_d["hold_reduce_exit"] != fresh_d["hold_reduce_exit"]),
        "FINAL_OUTCOME_CHANGED": aged_d["final_outcome"] != fresh_d["final_outcome"],
        "AGE_ONLY_CAUSALITY_SUPPORTED": classification
        not in {"NOT_COMPARABLE", "FRESH_ESTIMATE_UNAVAILABLE", "UNKNOWN"},
        "CONFOUNDERS": [],
        "NON_PERSISTING_READ_ONLY": True,
        "COUNTERFACTUAL_STATE_MUTATION_OCCURRED": False,
        "COUNTERFACTUAL_ORDER_ACTIVITY_OCCURRED": False,
        "HARDCODED_AGE_DECISION_PROBE": False,
        "aged_snapshot": aged_d,
        "fresh_snapshot": fresh_d,
    }
    payload["record_digest"] = sha256_hex_canonical(
        {k: v for k, v in payload.items() if k not in {"aged_snapshot", "fresh_snapshot"}}
    )
    return payload
