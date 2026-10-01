"""Lane generation / release safety (D4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_LANE_GENERATION_STALE,
    LANE_IDENTITY_MANIFEST_BASENAME,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    CURSOR_FILENAME,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.artifact_matrix_v1 import (
    execute_lane_generation_transition_v1,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    StateCarryDisposition,
)


class LaneGenerationError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _manifest_path(lane_state_root: Path) -> Path:
    return lane_state_root / LANE_IDENTITY_MANIFEST_BASENAME


def _load_manifest(path: Path) -> Mapping[str, Any] | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        return None
    return raw


def _prior_identity_from_manifest(raw: Mapping[str, Any]) -> BoundInstrumentLaneIdentityV1 | None:
    lane_id = str(raw.get("lane_id") or "").strip()
    bound_id = str(raw.get("bound_instrument_identity") or "").strip()
    epoch = str(raw.get("instrument_epoch") or "").strip()
    if not lane_id or not bound_id or not epoch:
        return None
    return BoundInstrumentLaneIdentityV1(
        lane_id=lane_id,
        bound_instrument_identity=bound_id,
        instrument_epoch=epoch,
    )


def ensure_lane_generation_safe_v1(
    *,
    lane_state_root: Path | str,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    purge_on_reset: bool = True,
) -> StateCarryDisposition:
    """Adjudicate persisted lane-local state vs current bound identity; purge on RESET."""
    root = Path(lane_state_root)
    root.mkdir(parents=True, exist_ok=True)
    manifest_path = _manifest_path(root)
    prior_raw = _load_manifest(manifest_path)
    prior = _prior_identity_from_manifest(prior_raw) if prior_raw is not None else None
    if not purge_on_reset and prior is not None:
        if prior.bound_instrument_identity == identity.lane_identity.bound_instrument_identity:
            return execute_lane_generation_transition_v1(
                lane_state_root=root,
                identity=identity,
                prior_identity=prior,
            )
    return execute_lane_generation_transition_v1(
        lane_state_root=root,
        identity=identity,
        prior_identity=prior,
    )


def assert_cursor_matches_identity_or_absent_v1(
    *,
    cursor_store_root: Path,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        load_current_productive_sidestate_confirmation_cursor_v1,
    )

    cursor_path = cursor_store_root / CURSOR_FILENAME
    if not cursor_path.is_file():
        return
    loaded = load_current_productive_sidestate_confirmation_cursor_v1(cursor_store_root)
    if loaded is None:
        return
    inst = str(getattr(loaded, "instrument_id", None) or "")
    if isinstance(loaded, Mapping):
        inst = str(loaded.get("instrument_id") or inst or "")
    native = str(getattr(loaded, "venue_native_id", None) or "")
    if isinstance(loaded, Mapping):
        native = str(loaded.get("venue_native_id") or native or "")
    if inst and inst != identity.canonical_instrument_id:
        raise LaneGenerationError(FAILURE_LANE_GENERATION_STALE, f"{identity.lane_id}:inst")
    if native and native != identity.venue_native_id:
        raise LaneGenerationError(FAILURE_LANE_GENERATION_STALE, f"{identity.lane_id}:native")
