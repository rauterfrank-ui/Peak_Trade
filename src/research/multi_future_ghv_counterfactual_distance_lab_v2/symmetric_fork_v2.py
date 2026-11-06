from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Optional

from unittest.mock import patch

from research.multi_future_ghv_counterfactual_distance_lab_v2.constants_v2 import (
    HARD_MAX_ADVERSE_DISTANCE,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    LayerCEventDistancesBindingResultV1,
    resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1,
)

_PATCH_TARGET = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1."
    "resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1"
)

MODEL_B = "MODEL_B_CURRENT_LAYER_C"
MODEL_D = "MODEL_D_POLICY_HARD_MAX"


@dataclass(frozen=True)
class LastDistanceForkSnapshotV2:
    model_id: str
    dynamic_scope_magnitude_input: float
    up_distance_raw: float
    adverse_distance_raw: float
    reversal_distance_raw: float
    up_distance_effective: float
    adverse_distance_effective: float
    reversal_distance_effective: float
    hard_max_applied: bool
    hard_max_value: float


_last_fork: contextvars.ContextVar[Optional[LastDistanceForkSnapshotV2]] = contextvars.ContextVar(
    "mf_ghv_lab_v2_last_fork", default=None
)
_active_model: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "mf_ghv_lab_v2_active_model", default=None
)


def last_distance_fork_snapshot_v2() -> Optional[LastDistanceForkSnapshotV2]:
    return _last_fork.get()


def _apply_hard_max_consumer_v2(
    base: LayerCEventDistancesBindingResultV1,
) -> LayerCEventDistancesBindingResultV1:
    if not base.ok or base.adverse_exit_distance is None:
        return base
    raw_adverse = float(base.adverse_exit_distance)
    cap = float(HARD_MAX_ADVERSE_DISTANCE)
    if raw_adverse <= cap:
        return base
    adverse = cap
    up = adverse / 0.4
    reversal = adverse / 0.4 * 1.5
    return LayerCEventDistancesBindingResultV1(
        ok=True,
        up_distance=up,
        adverse_exit_distance=adverse,
        reversal_distance=reversal,
        dynamic_scope_magnitude=base.dynamic_scope_magnitude,
        failure_codes=(),
    )


def _symmetric_wrapper(magnitude: float) -> LayerCEventDistancesBindingResultV1:
    model_id = _active_model.get() or MODEL_B
    base = resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1(float(magnitude))
    if model_id == MODEL_D:
        effective = _apply_hard_max_consumer_v2(base)
    else:
        effective = base
    if base.ok and effective.ok:
        _last_fork.set(
            LastDistanceForkSnapshotV2(
                model_id=model_id,
                dynamic_scope_magnitude_input=float(magnitude),
                up_distance_raw=float(base.up_distance or 0),
                adverse_distance_raw=float(base.adverse_exit_distance or 0),
                reversal_distance_raw=float(base.reversal_distance or 0),
                up_distance_effective=float(effective.up_distance or 0),
                adverse_distance_effective=float(effective.adverse_exit_distance or 0),
                reversal_distance_effective=float(effective.reversal_distance or 0),
                hard_max_applied=model_id == MODEL_D
                and (base.adverse_exit_distance or 0) > HARD_MAX_ADVERSE_DISTANCE,
                hard_max_value=HARD_MAX_ADVERSE_DISTANCE,
            )
        )
    return effective


@contextmanager
def symmetric_distance_fork_v2(*, model_id: str) -> Iterator[None]:
    token_model = _active_model.set(model_id)
    token_fork = _last_fork.set(None)
    with patch(_PATCH_TARGET, side_effect=_symmetric_wrapper):
        try:
            yield
        finally:
            _active_model.reset(token_model)
            _last_fork.reset(token_fork)


def run_replay_symmetric_v2(replay_input, *, model_id: str):
    with symmetric_distance_fork_v2(model_id=model_id):
        result = run_integrated_offline_trading_logic_replay_v1(replay_input)
        fork = last_distance_fork_snapshot_v2()
    return result, fork


def run_replay_reference_unpatched_v2(replay_input):
    return run_integrated_offline_trading_logic_replay_v1(replay_input)
