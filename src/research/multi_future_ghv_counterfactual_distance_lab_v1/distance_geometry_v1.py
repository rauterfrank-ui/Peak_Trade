from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
from typing import Mapping

from research.multi_future_ghv_counterfactual_distance_lab_v1.behavioral_models_v1 import (
    HARD_MAX_ADVERSE_DISTANCE,
    resolve_behavioral_layer_c_distances_v1,
)
from research.multi_future_ghv_counterfactual_distance_lab_v1.contract_profiles_v1 import (
    ContractProfileV1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)


def _round_to_tick(price: Decimal, tick: Decimal) -> Decimal:
    if tick <= 0:
        return price
    q = (price / tick).quantize(Decimal("1"), rounding=ROUND_DOWN)
    return q * tick


def evaluate_distance_geometry_v1(
    *,
    model_id: str,
    mark_price: float,
    volatility_estimate: float,
    contract: ContractProfileV1,
) -> Mapping[str, object]:
    binding = resolve_behavioral_layer_c_distances_v1(
        model_id=model_id,
        mark_price=mark_price,
        volatility_estimate=volatility_estimate,
    )
    mark = float(mark_price)
    sigma_p = float(volatility_estimate) * mark
    out: dict[str, object] = {
        "model_id": model_id,
        "mark_price": mark,
        "volatility_estimate": float(volatility_estimate),
        "DISTANCE_BINDING_OK": binding.ok,
        "DISTANCE_ABSOLUTE": binding.adverse_exit_distance,
        "DISTANCE_RELATIVE_TO_PRICE": (
            None if not binding.adverse_exit_distance else float(binding.adverse_exit_distance) / mark
        ),
        "DISTANCE_RELATIVE_TO_SIGMA_P": (
            None
            if not binding.adverse_exit_distance or sigma_p <= 0
            else float(binding.adverse_exit_distance) / sigma_p
        ),
        "POLICY_HARD_MAX_FAILURE": False,
        "SYMBOL_OVERRIDE_REQUIRED": False,
        "PRICE_BUCKET_REQUIRED": False,
    }
    if not binding.ok or binding.adverse_exit_distance is None:
        out.update(
            {
                "STOP_VALID_LONG": False,
                "STOP_VALID_SHORT": False,
                "NONPOSITIVE_STOP_COUNT": 1,
                "CONTRACT_FAILURE": True,
            }
        )
        return out
    adverse = float(binding.adverse_exit_distance)
    if adverse > HARD_MAX_ADVERSE_DISTANCE and model_id != "MODEL_D_POLICY_HARD_MAX":
        out["POLICY_HARD_MAX_FAILURE"] = True
    stop_long = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side="LONG",
        reference_price=Decimal(str(mark)),
        adverse_exit_distance=adverse,
    )
    stop_short = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side="SHORT",
        reference_price=Decimal(str(mark)),
        adverse_exit_distance=adverse,
    )
    stop_long_f = float(stop_long) if stop_long is not None else None
    stop_short_f = float(stop_short) if stop_short is not None else None
    tick = contract.tick_size
    rounded_long = (
        _round_to_tick(Decimal(str(stop_long_f)), tick) if stop_long_f is not None else None
    )
    rounded_short = (
        _round_to_tick(Decimal(str(stop_short_f)), tick) if stop_short_f is not None else None
    )
    nonpos = int(
        (stop_long_f is None or stop_long_f <= 0) + (stop_short_f is None or stop_short_f <= 0)
    )
    tick_fail = int(
        (rounded_long is not None and rounded_long <= 0)
        + (rounded_short is not None and rounded_short <= 0)
    )
    precision_fail = 0
    if stop_long_f is not None:
        prec = contract.price_precision
        s = f"{stop_long_f:.{prec}f}"
        if float(s) <= 0:
            precision_fail += 1
    out.update(
        {
            "STOP_PRICE_LONG": stop_long_f,
            "STOP_PRICE_SHORT": stop_short_f,
            "STOP_VALID_LONG": stop_long_f is not None and stop_long_f > 0,
            "STOP_VALID_SHORT": stop_short_f is not None and stop_short_f > 0,
            "NONPOSITIVE_STOP_COUNT": nonpos,
            "TICK_FAILURE": tick_fail > 0,
            "PRECISION_FAILURE": precision_fail > 0,
            "CONTRACT_FAILURE": tick_fail > 0 or precision_fail > 0,
            "PRICE_SCALE_FAILURE": nonpos > 0 and model_id == "MODEL_A_LEGACY_FIXED_80",
            "GENERALIZATION_FAILURE": nonpos > 0 or not binding.ok,
        }
    )
    return out
