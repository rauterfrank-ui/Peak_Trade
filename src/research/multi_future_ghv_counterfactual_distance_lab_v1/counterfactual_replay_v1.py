from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional
from unittest.mock import patch

from research.multi_future_ghv_counterfactual_distance_lab_v1.behavioral_models_v1 import (
    resolve_behavioral_layer_c_distances_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    LayerCEventDistancesBindingResultV1,
)


@contextmanager
def behavioral_distance_patch_v1(
    *,
    model_id: str,
    mark_price: float,
    volatility_estimate: float,
) -> Iterator[None]:
    target = (
        "trading.master_v2.integrated_offline_trading_logic_replay_v1."
        "resolve_layer_c_event_distances_from_dynamic_scope_magnitude_v1"
    )

    def _replacement(magnitude: float) -> LayerCEventDistancesBindingResultV1:
        if model_id == "MODEL_B_CURRENT_LAYER_C":
            return resolve_behavioral_layer_c_distances_v1(
                model_id=model_id,
                mark_price=float(mark_price),
                volatility_estimate=float(volatility_estimate),
            )
        return resolve_behavioral_layer_c_distances_v1(
            model_id=model_id,
            mark_price=float(mark_price),
            volatility_estimate=float(volatility_estimate),
        )

    with patch(target, side_effect=_replacement):
        yield


def run_counterfactual_integrated_replay_v1(
    replay_input,
    *,
    model_id: str,
    mark_price: Optional[float] = None,
    volatility_estimate: Optional[float] = None,
):
    ctx = replay_input.canonical_market_context
    mark = float(mark_price if mark_price is not None else ctx.mark_price)
    vol = float(
        volatility_estimate if volatility_estimate is not None else ctx.volatility_estimate
    )
    if model_id == "MODEL_B_CURRENT_LAYER_C":
        return run_integrated_offline_trading_logic_replay_v1(replay_input)
    with behavioral_distance_patch_v1(
        model_id=model_id,
        mark_price=mark,
        volatility_estimate=vol,
    ):
        return run_integrated_offline_trading_logic_replay_v1(replay_input)
