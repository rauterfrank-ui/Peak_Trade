"""Build archive-sibling payload from post-commit integrated replay facts only.

Does not load or relabel regime_bull_bear_switch_evidence_readmodel artifacts.
Does not recompute transition_state or SideState.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_EVIDENCE_READMODEL_SHORTCUT_FORBIDDEN,
    ERROR_REPLAY_COMMIT_INCOMPLETE,
    ERROR_SOURCE_INVALID,
    ERROR_TRANSITION_IDENTITY_MISMATCH,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1 import (
    coerce_regime_bull_bear_switch_mapping_v1,
)


def _reject_evidence_readmodel_shortcut(source: object) -> tuple[str, ...]:
    if isinstance(source, Mapping):
        schema_name = source.get("schema_name")
        if schema_name == "regime_bull_bear_switch_evidence_readmodel.v1":
            return (ERROR_EVIDENCE_READMODEL_SHORTCUT_FORBIDDEN,)
    if hasattr(source, "schema_name"):
        name = getattr(source, "schema_name", None)
        if name == "regime_bull_bear_switch_evidence_readmodel.v1":
            return (ERROR_EVIDENCE_READMODEL_SHORTCUT_FORBIDDEN,)
    return ()


def build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1(
    *,
    regime_id: str,
    regime_status: str,
    replay_intermediate: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map replay-produced state_switch + transition facts into sibling binder fields."""
    if replay_intermediate is None:
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)

    shortcut_errors = _reject_evidence_readmodel_shortcut(replay_intermediate)
    if shortcut_errors:
        return None, shortcut_errors

    state_switch = getattr(replay_intermediate, "state_switch", None)
    transition = getattr(replay_intermediate, "transition_decision", None)
    if state_switch is None or transition is None:
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)

    if not isinstance(regime_id, str) or not regime_id.strip():
        return None, (ERROR_SOURCE_INVALID,)

    status_raw = regime_status
    if isinstance(status_raw, Enum):
        status_raw = status_raw.value
    if not isinstance(status_raw, str) or not status_raw.strip():
        return None, (ERROR_SOURCE_INVALID,)
    regime_status_str = status_raw.strip()

    previous = getattr(state_switch, "previous_side_state", None)
    next_side = getattr(state_switch, "next_side_state", None)
    scope_event_type = getattr(state_switch, "scope_event_type", None)
    transition_allowed = getattr(state_switch, "transition_allowed", None)
    transition_reason_code = getattr(state_switch, "transition_reason_code", None)

    for label, value in (
        ("previous_side_state", previous),
        ("next_side_state", next_side),
        ("scope_event_type", scope_event_type),
        ("transition_reason_code", transition_reason_code),
    ):
        if not isinstance(value, str) or not value.strip():
            return None, (ERROR_SOURCE_INVALID,)

    if not isinstance(transition_allowed, bool):
        return None, (ERROR_SOURCE_INVALID,)

    trans_allowed = bool(getattr(transition, "allowed", None))
    trans_reason = getattr(transition, "reason_code", None)
    if not isinstance(trans_reason, str) or not trans_reason.strip():
        return None, (ERROR_TRANSITION_IDENTITY_MISMATCH,)
    if (
        trans_allowed != transition_allowed
        or trans_reason.strip() != str(transition_reason_code).strip()
    ):
        return None, (ERROR_TRANSITION_IDENTITY_MISMATCH,)

    semantic_digest = getattr(state_switch, "semantic_digest", None)
    payload: dict[str, Any] = {
        "regime_id": regime_id.strip(),
        "regime_status": regime_status_str,
        "side_state": str(next_side).strip(),
        "previous_side_state": str(previous).strip(),
        "next_side_state": str(next_side).strip(),
        "scope_event_type": str(scope_event_type).strip(),
        "transition_allowed": transition_allowed,
        "transition_reason_code": str(transition_reason_code).strip(),
    }
    if isinstance(semantic_digest, str) and semantic_digest.strip():
        payload["semantic_digest"] = semantic_digest.strip()

    coerced, coerce_errors = coerce_regime_bull_bear_switch_mapping_v1(payload)
    if coerced is None:
        return None, coerce_errors
    return coerced, ()
