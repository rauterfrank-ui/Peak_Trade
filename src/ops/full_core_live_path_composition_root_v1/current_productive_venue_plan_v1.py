"""Bind a CURRENT_PRODUCTIVE venue plan from Master-V2 replay + Cap-24 binding.

Does not fabricate ENTER, size, or plan. Missing replay is a truthful deny.
STEP-29Q remains PLAN_ONLY at composition. No POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import Optional

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    VenuePlanCandidateV1,
)
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    translate_core_live_intent_to_venue_plan_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT = "CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT"


def try_bind_current_productive_venue_plan_v1(
    *,
    replay: Optional[IntegratedOfflineReplayResultV1],
    bound_instrument: BoundInstrumentV1,
    session_id: str,
    run_id: str,
    composed_epoch: str,
    td_mode: str = "cross",
) -> tuple[CompositionStatusV1, tuple[str, ...], VenuePlanCandidateV1 | None]:
    if replay is None:
        return CompositionStatusV1.DENY, (CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,), None
    status, reasons, intent = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=bound_instrument,
        mode=MODE_LIVE,
        composed_epoch=composed_epoch,
    )
    if status is not CompositionStatusV1.PASS or intent is None:
        return status, reasons, None
    return translate_core_live_intent_to_venue_plan_v1(
        intent,
        session_id=session_id,
        run_id=run_id,
        td_mode=td_mode,
    )
