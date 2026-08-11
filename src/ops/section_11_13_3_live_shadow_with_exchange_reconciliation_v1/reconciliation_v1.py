"""§11.5 Live shadow exchange reconciliation evaluation (GET-snapshot only).

Preparation/execute of this package never submits Live orders, never mutates
accounts, and never unlocks Cap 11.7. Exchange truth adoption requires an
explicit policy id. Silent local history overwrite is forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY,
    NO_ACCOUNT_MUTATION_FROM_SHADOW_RECONCILIATION,
    NO_AUTOMATIC_STAGE_PROMOTION,
    NO_LIVE_ORDER_FROM_SHADOW_RECONCILIATION,
    RECONCILIATION_BEFORE_ALPHA,
    RECONCILIATION_CONTINUOUS,
    RECONCILIATION_LAYERS,
    RECONCILIATION_OUTCOMES,
    SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)


class LiveShadowReconReconciliationError(RuntimeError):
    """Fail-closed reconciliation contract violation."""


_BLOCKING_OUTCOMES = frozenset(
    {
        "EXIT_ONLY",
        "REDUCE_ONLY",
        "CANCEL_ALL_AND_HALT",
        "HARD_STOP_OWNER_REVIEW",
        "CANCEL_UNKNOWN_ORDERS",
    }
)


@dataclass(frozen=True)
class LiveShadowReconLayerResultV1:
    layer: str
    outcome: str
    divergence_detected: bool
    blocks_new_entry: bool
    exchange_truth_adoption_policy_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer,
            "outcome": self.outcome,
            "divergence_detected": self.divergence_detected,
            "blocks_new_entry": self.blocks_new_entry,
            "exchange_truth_adoption_policy_id": self.exchange_truth_adoption_policy_id,
        }


@dataclass(frozen=True)
class LiveShadowReconEvaluationV1:
    layers: tuple[LiveShadowReconLayerResultV1, ...]
    all_layers_match: bool
    unresolved_economic_divergence: bool
    blocks_new_entry: bool
    order_effect: str = "NONE"
    account_mutation_effect: str = "NONE"
    automatic_stage_promotion: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "DOCUMENT_CLASS": "BOUNDED_LIVE_SHADOW_EXCHANGE_RECONCILIATION_LAYER_EVAL_V1",
            "ALL_LAYERS_MATCH": self.all_layers_match,
            "UNRESOLVED_ECONOMIC_DIVERGENCE": self.unresolved_economic_divergence,
            "BLOCKS_NEW_ENTRY": self.blocks_new_entry,
            "ORDER_EFFECT": self.order_effect,
            "ACCOUNT_MUTATION_EFFECT": self.account_mutation_effect,
            "AUTOMATIC_STAGE_PROMOTION": self.automatic_stage_promotion,
            "RECONCILIATION_BEFORE_ALPHA": RECONCILIATION_BEFORE_ALPHA,
            "RECONCILIATION_CONTINUOUS": RECONCILIATION_CONTINUOUS,
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": (
                UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY
            ),
            "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY": (
                EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY
            ),
            "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN": (SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN),
            "NO_LIVE_ORDER_FROM_SHADOW_RECONCILIATION": (NO_LIVE_ORDER_FROM_SHADOW_RECONCILIATION),
            "NO_ACCOUNT_MUTATION_FROM_SHADOW_RECONCILIATION": (
                NO_ACCOUNT_MUTATION_FROM_SHADOW_RECONCILIATION
            ),
            "NO_AUTOMATIC_STAGE_PROMOTION": NO_AUTOMATIC_STAGE_PROMOTION,
            "layers": [layer.to_dict() for layer in self.layers],
        }


def refuse_silent_local_history_overwrite_v1(*, attempted_overwrite_of: str) -> None:
    raise LiveShadowReconReconciliationError(
        f"SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN:{attempted_overwrite_of}"
    )


def refuse_automatic_stage_promotion_v1(*, claimed_target_stage: str) -> None:
    raise LiveShadowReconReconciliationError(
        f"AUTOMATIC_STAGE_PROMOTION_FORBIDDEN:{claimed_target_stage}"
    )


def refuse_live_order_side_effect_v1(*, claimed_action: str) -> None:
    raise LiveShadowReconReconciliationError(
        f"LIVE_ORDER_SIDE_EFFECT_FORBIDDEN_IN_SHADOW_RECON:{claimed_action}"
    )


def _normalize_layer_value(payload: Mapping[str, Any] | None, key: str) -> Any:
    if not payload:
        return None
    return payload.get(key)


def _layer_outcome(
    *,
    layer: str,
    local_value: Any,
    exchange_value: Any,
    exchange_truth_adoption_policy_id: str | None,
) -> LiveShadowReconLayerResultV1:
    if layer not in RECONCILIATION_LAYERS:
        raise LiveShadowReconReconciliationError(f"UNKNOWN_RECONCILIATION_LAYER:{layer}")

    divergence = local_value != exchange_value
    if not divergence:
        outcome = "MATCH"
        policy_id = None
    else:
        if exchange_truth_adoption_policy_id:
            if not EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY:
                raise LiveShadowReconReconciliationError(
                    "EXCHANGE_TRUTH_ADOPTION_POLICY_FLAG_DRIFT"
                )
            outcome = "SAFE_ADOPT_EXCHANGE_TRUTH"
            policy_id = exchange_truth_adoption_policy_id
        else:
            outcome = "HARD_STOP_OWNER_REVIEW"
            policy_id = None

    if outcome not in RECONCILIATION_OUTCOMES:
        raise LiveShadowReconReconciliationError(f"UNKNOWN_RECONCILIATION_OUTCOME:{outcome}")
    if outcome == "SAFE_ADOPT_EXCHANGE_TRUTH" and not policy_id:
        raise LiveShadowReconReconciliationError("EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY")

    blocks = bool(divergence and outcome in _BLOCKING_OUTCOMES)
    return LiveShadowReconLayerResultV1(
        layer=layer,
        outcome=outcome,
        divergence_detected=divergence,
        blocks_new_entry=blocks,
        exchange_truth_adoption_policy_id=policy_id,
    )


def evaluate_live_shadow_exchange_reconciliation_v1(
    *,
    local_expected_state: Mapping[str, Any],
    exchange_snapshot: Mapping[str, Any],
    exchange_truth_adoption_policy_id: str | None = None,
) -> LiveShadowReconEvaluationV1:
    """Compare local shadow expected state vs exchange snapshot across §11.5 layers."""
    if not isinstance(local_expected_state, Mapping):
        raise LiveShadowReconReconciliationError("LOCAL_EXPECTED_STATE_REQUIRED")
    if not isinstance(exchange_snapshot, Mapping):
        raise LiveShadowReconReconciliationError("EXCHANGE_SNAPSHOT_REQUIRED")

    # Decision / evidence history must never be silently overwritten.
    if bool(local_expected_state.get("overwrite_decision_history")) or bool(
        exchange_snapshot.get("overwrite_decision_history")
    ):
        refuse_silent_local_history_overwrite_v1(attempted_overwrite_of="decision_history")

    results: list[LiveShadowReconLayerResultV1] = []
    for layer in RECONCILIATION_LAYERS:
        results.append(
            _layer_outcome(
                layer=layer,
                local_value=_normalize_layer_value(local_expected_state, layer),
                exchange_value=_normalize_layer_value(exchange_snapshot, layer),
                exchange_truth_adoption_policy_id=exchange_truth_adoption_policy_id,
            )
        )

    all_match = all(r.outcome == "MATCH" and not r.divergence_detected for r in results)
    unresolved = any(
        r.divergence_detected and r.outcome == "HARD_STOP_OWNER_REVIEW" for r in results
    )
    blocks = any(r.blocks_new_entry for r in results) or (
        unresolved and UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY
    )

    if not NO_LIVE_ORDER_FROM_SHADOW_RECONCILIATION:
        raise LiveShadowReconReconciliationError("ORDER_SIDE_EFFECT_FLAG_DRIFT")
    if not NO_ACCOUNT_MUTATION_FROM_SHADOW_RECONCILIATION:
        raise LiveShadowReconReconciliationError("ACCOUNT_MUTATION_FLAG_DRIFT")
    if not NO_AUTOMATIC_STAGE_PROMOTION:
        raise LiveShadowReconReconciliationError("AUTOMATIC_PROMOTION_FLAG_DRIFT")

    return LiveShadowReconEvaluationV1(
        layers=tuple(results),
        all_layers_match=all_match,
        unresolved_economic_divergence=unresolved,
        blocks_new_entry=blocks,
        order_effect="NONE",
        account_mutation_effect="NONE",
        automatic_stage_promotion=False,
    )


def build_matched_local_and_exchange_fixture_v1() -> tuple[dict[str, Any], dict[str, Any]]:
    """Deterministic MATCH fixture pair for unit tests (never productive proven)."""
    state = {
        layer: {"status": "flat_or_empty", "digest": f"fixture-{layer}"}
        for layer in RECONCILIATION_LAYERS
    }
    return dict(state), dict(state)
