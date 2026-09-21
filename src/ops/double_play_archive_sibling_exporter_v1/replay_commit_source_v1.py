"""Build archive-sibling payload from post-commit Pure-Stack display Decisions only.

Does not load or relabel DDO / entry-exit observation artifacts.
Does not map SurvivalResultV1 / SuitabilityResultV1 / DoublePlayCompositionResultV1
to Pure-Stack Decisions (ResultV1→Decision mapping unauthorized).
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.double_play_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_REPLAY_COMMIT_INCOMPLETE,
    ERROR_RESULTV1_SHORTCUT_FORBIDDEN,
)
from src.ops.double_play_archive_sibling_exporter_v1.exporter_v1 import (
    coerce_double_play_display_export_payload_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.double_play_input_gate_v1 import (
    try_extract_double_play_decision_inputs_from_replay_intermediate_v1,
)
from trading.master_v2.double_play_dashboard_display import (
    build_dashboard_display_snapshot,
    snapshot_to_jsonable,
)


def _reject_resultv1_shortcut(intermediate: object) -> tuple[str, ...]:
    """Fail-closed when replay intermediate exposes ResultV1 carriers without Decisions."""
    if intermediate is None:
        return ()
    for attr in ("composition_result", "bull_survival", "bear_survival"):
        if hasattr(intermediate, attr) and getattr(intermediate, attr) is not None:
            bundle = getattr(intermediate, "display_decision_bundle", None)
            if bundle is None:
                bundle = getattr(intermediate, "pure_stack_display_decision_bundle", None)
            if bundle is None:
                return (ERROR_RESULTV1_SHORTCUT_FORBIDDEN,)
    return ()


def build_double_play_dashboard_display_sibling_payload_from_replay_commit_v1(
    *,
    replay_intermediate: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map already-produced Pure-Stack Decisions into sibling export shape."""
    if replay_intermediate is None:
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)

    shortcut_errors = _reject_resultv1_shortcut(replay_intermediate)
    if shortcut_errors:
        return None, shortcut_errors

    mapping = try_extract_double_play_decision_inputs_from_replay_intermediate_v1(
        replay_intermediate
    )
    if mapping is None:
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)

    snap = build_dashboard_display_snapshot(
        futures_input=mapping["futures_input"],
        transition=mapping["transition"],
        survival=mapping["survival"],
        suitability=mapping["suitability"],
        capital_slot_ratchet=mapping["capital_slot_ratchet"],
        capital_slot_release=mapping["capital_slot_release"],
        composition=mapping["composition"],
    )
    raw = snapshot_to_jsonable(snap)
    coerced, error = coerce_double_play_display_export_payload_v1(raw)
    if coerced is None:
        return None, (error or ERROR_REPLAY_COMMIT_INCOMPLETE,)
    return coerced, ()


def build_double_play_dashboard_display_sibling_payload_from_mapping_v1(
    decision_mapping: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Build sibling payload from an already-extracted Decision mapping (tests/helpers)."""
    if not isinstance(decision_mapping, Mapping):
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)
    required = (
        "futures_input",
        "transition",
        "survival",
        "suitability",
        "capital_slot_ratchet",
        "capital_slot_release",
        "composition",
    )
    for key in required:
        if decision_mapping.get(key) is None:
            return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)
    snap = build_dashboard_display_snapshot(
        futures_input=decision_mapping["futures_input"],
        transition=decision_mapping["transition"],
        survival=decision_mapping["survival"],
        suitability=decision_mapping["suitability"],
        capital_slot_ratchet=decision_mapping["capital_slot_ratchet"],
        capital_slot_release=decision_mapping["capital_slot_release"],
        composition=decision_mapping["composition"],
    )
    raw = snapshot_to_jsonable(snap)
    coerced, error = coerce_double_play_display_export_payload_v1(raw)
    if coerced is None:
        return None, (error or ERROR_REPLAY_COMMIT_INCOMPLETE,)
    return coerced, ()
