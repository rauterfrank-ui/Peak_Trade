"""L10 — sole price-based BULL/BEAR switch (CM_t >= D_t)."""

from __future__ import annotations

from trading.master_v2.naked_mv2_dp_regime_v1 import NakedRegimeV1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    BullBearSwitchInputV1,
    BullBearSwitchOutputV1,
)

L10_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.l10_bull_bear_switch_v1"
SOLE_PRICE_SWITCH_RULE = "CM_t>=D_t"


def _flip_regime(regime: NakedRegimeV1) -> NakedRegimeV1:
    if regime is NakedRegimeV1.BULL:
        return NakedRegimeV1.BEAR
    return NakedRegimeV1.BULL


def apply_l10_bull_bear_switch_v1(inp: BullBearSwitchInputV1) -> BullBearSwitchOutputV1:
    switch_met = float(inp.cm_t) >= float(inp.d_t)
    if switch_met:
        regime_post = _flip_regime(inp.regime_pre)
        return BullBearSwitchOutputV1(
            regime_pre=inp.regime_pre,
            regime_post=regime_post,
            switch_condition_met=True,
            r_t_reset_performed=True,
            persisted_r_t=float(inp.mark_price_m_t),
        )
    return BullBearSwitchOutputV1(
        regime_pre=inp.regime_pre,
        regime_post=inp.regime_pre,
        switch_condition_met=False,
        r_t_reset_performed=False,
        persisted_r_t=float(inp.running_reference_post.reference_price_r_t),
    )


__all__ = [
    "L10_OWNER",
    "SOLE_PRICE_SWITCH_RULE",
    "apply_l10_bull_bear_switch_v1",
]
