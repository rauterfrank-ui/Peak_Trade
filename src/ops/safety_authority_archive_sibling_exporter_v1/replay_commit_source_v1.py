"""Build archive-sibling Safety Authority fields from replay commit artifacts only.

Maps already-produced ReplayExecutionSafetyV1 and KillSwitch boundary binding
refs from cycle commit. Does not call evaluate_offline_killswitch_boundary_v0,
derive_replay_execution_safety_v1, or instantiate KillSwitch.

Presentation mapping (family-specific adapter, R4_SAFETY_ADAPTER):
- ``veto_active`` ← ``typed_enter_hold_required_v1(replay_execution_safety)``
- ``kill_switch_state`` ← ``KillSwitchState.KILLED.name`` when veto else ``ACTIVE.name``
- ``reason_codes`` ← replay_execution_safety.reason_codes (copy only)
- ``evidence_digest`` ← decision evidence ``killswitch_boundary_ref`` when bound
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.safety_authority_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_DECISION_EVIDENCE_ABSENT,
    ERROR_KILLSWITCH_BOUNDARY_NOT_BOUND,
    ERROR_TYPED_REPLAY_SAFETY_ABSENT,
)
from src.risk_layer.kill_switch.state import KillSwitchState
from src.webui.workflow_dashboard_readmodel_v1.safety_authority_presentation_projection_materializer_v1 import (
    coerce_safety_authority_fields_mapping_v1,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    ReplayExecutionSafetyV1,
    typed_enter_hold_required_v1,
)


def _read_str_field(source: object, key: str) -> str | None:
    if isinstance(source, Mapping):
        raw = source.get(key)
    elif hasattr(source, key):
        raw = getattr(source, key)
    else:
        return None
    if not isinstance(raw, str) or not raw.strip():
        return None
    return raw.strip()


def build_safety_authority_sibling_payload_from_replay_commit_v1(
    *,
    replay_execution_safety: object | None,
    decision_evidence: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map replay-attached typed safety contract into sibling export shape."""
    if decision_evidence is None:
        return None, (ERROR_DECISION_EVIDENCE_ABSENT,)

    if replay_execution_safety is None or not isinstance(
        replay_execution_safety, ReplayExecutionSafetyV1
    ):
        return None, (ERROR_TYPED_REPLAY_SAFETY_ABSENT,)

    ks_effect = _read_str_field(decision_evidence, "killswitch_boundary_effect")
    if ks_effect != KILLSWITCH_BOUNDARY_EFFECT_BOUND_OFFLINE:
        return None, (ERROR_KILLSWITCH_BOUNDARY_NOT_BOUND,)

    ks_ref = _read_str_field(decision_evidence, "killswitch_boundary_ref") or ""

    veto_active = bool(typed_enter_hold_required_v1(replay_execution_safety))
    kill_switch_state = KillSwitchState.KILLED.name if veto_active else KillSwitchState.ACTIVE.name

    raw_fields: dict[str, Any] = {
        "kill_switch_state": kill_switch_state,
        "veto_active": veto_active,
        "reason_codes": list(replay_execution_safety.reason_codes),
        "schema_version": "v1",
    }
    if ks_ref:
        raw_fields["evidence_digest"] = ks_ref
        raw_fields["semantic_digest"] = ks_ref

    coerced, errors = coerce_safety_authority_fields_mapping_v1(raw_fields)
    if coerced is None:
        return None, errors
    return dict(coerced), ()
