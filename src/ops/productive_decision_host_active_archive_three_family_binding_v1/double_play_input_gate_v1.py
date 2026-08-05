"""Double-Play productive input gate — fail-closed without new mapping semantics."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    DOUBLE_PLAY_BLOCK_REASON,
    FAMILY_DOUBLE_PLAY,
    HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    FamilyExportResultV1,
)
from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
)
from trading.master_v2.double_play_composition import DoublePlayCompositionDecision
from trading.master_v2.double_play_dashboard_display import build_dashboard_display_snapshot
from trading.master_v2.double_play_futures_input import FuturesInputReadinessDecision
from trading.master_v2.double_play_state import TransitionDecision
from trading.master_v2.double_play_suitability import SuitabilityProjectionDecision
from trading.master_v2.double_play_survival import SurvivalEnvelopeDecision


_REQUIRED_DECISION_TYPES: tuple[tuple[str, type], ...] = (
    ("futures_input", FuturesInputReadinessDecision),
    ("transition", TransitionDecision),
    ("survival", SurvivalEnvelopeDecision),
    ("suitability", SuitabilityProjectionDecision),
    ("capital_slot_ratchet", CapitalSlotRatchetDecision),
    ("capital_slot_release", CapitalSlotReleaseDecision),
    ("composition", DoublePlayCompositionDecision),
)


def classify_double_play_canonical_inputs_v1(
    cycle_outputs: Mapping[str, Any] | None,
) -> FamilyExportResultV1:
    """Return fail-closed family result unless all Decision-typed inputs are present.

    Productive ``IntegratedOfflineReplayIntermediateV1`` does not carry these types.
    Inventing ResultV1→Decision mapping is forbidden (NEW_SEMANTICS).
    """
    if HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH and not _has_complete_inputs(
        cycle_outputs
    ):
        return FamilyExportResultV1(
            family_id=FAMILY_DOUBLE_PLAY,
            exportable=False,
            exported=False,
            materialized=False,
            loader_ok=False,
            error_code="HARD_STOP_DOUBLE_PLAY_CANONICAL_INPUT_CONTRACT_MISMATCH",
            detail=DOUBLE_PLAY_BLOCK_REASON,
            skipped_reason="canonical_display_inputs_incomplete",
        )
    assert cycle_outputs is not None
    snap = build_dashboard_display_snapshot(
        futures_input=cycle_outputs["futures_input"],
        transition=cycle_outputs["transition"],
        survival=cycle_outputs["survival"],
        suitability=cycle_outputs["suitability"],
        capital_slot_ratchet=cycle_outputs["capital_slot_ratchet"],
        capital_slot_release=cycle_outputs["capital_slot_release"],
        composition=cycle_outputs["composition"],
    )
    return FamilyExportResultV1(
        family_id=FAMILY_DOUBLE_PLAY,
        exportable=True,
        exported=False,
        materialized=False,
        loader_ok=False,
        detail="snapshot_ready",
        skipped_reason="",
    )


def _has_complete_inputs(cycle_outputs: Mapping[str, Any] | None) -> bool:
    if not isinstance(cycle_outputs, Mapping):
        return False
    for key, typ in _REQUIRED_DECISION_TYPES:
        value = cycle_outputs.get(key)
        if value is None or not isinstance(value, typ):
            return False
    return True


def try_extract_double_play_decision_inputs_from_replay_intermediate_v1(
    intermediate: object | None,
) -> Optional[dict[str, Any]]:
    """Return Decision-typed inputs only when already present — never invent mapping.

    Supports:
    - attributes named exactly as required keys on the intermediate, or
    - a complete ``display_decision_bundle`` / ``pure_stack_display_decision_bundle``
      exposing ``as_decision_mapping()``.

    TransitionDecision may appear as ``transition_decision`` (passthrough) but a
    partial set still fail-closes — no partial composition / no ResultV1 rebuild.
    """
    if intermediate is None:
        return None

    bundle = getattr(intermediate, "display_decision_bundle", None)
    if bundle is None:
        bundle = getattr(intermediate, "pure_stack_display_decision_bundle", None)
    if bundle is not None and hasattr(bundle, "as_decision_mapping"):
        mapping = bundle.as_decision_mapping()
        if isinstance(mapping, Mapping):
            candidate_from_bundle: dict[str, Any] = {}
            for key, typ in _REQUIRED_DECISION_TYPES:
                value = mapping.get(key)
                if value is None or not isinstance(value, typ):
                    return None
                candidate_from_bundle[key] = value
            return candidate_from_bundle

    candidate: dict[str, Any] = {}
    for key, typ in _REQUIRED_DECISION_TYPES:
        value = getattr(intermediate, key, None)
        if key == "transition" and value is None:
            value = getattr(intermediate, "transition_decision", None)
        if value is None or not isinstance(value, typ):
            return None
        candidate[key] = value
    return candidate
