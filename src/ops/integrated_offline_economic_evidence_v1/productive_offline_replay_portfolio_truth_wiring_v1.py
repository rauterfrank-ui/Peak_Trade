"""Wiring helpers: attach prior-epoch simulated portfolio truth to productive offline replay."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Any, Optional

from src.backtest.mv2_research_wiring_v1 import MV2IntegratedReplayBarSequenceStateV1
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_simulated_portfolio_position_truth_v1 import (
    ProductiveOfflineSimulatedPortfolioPositionObservationV1,
    apply_simulated_portfolio_position_feedback_to_mv2_sequence_state_v1,
    capture_productive_offline_simulated_portfolio_position_observation_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)

PRODUCTIVE_OFFLINE_REPLAY_PORTFOLIO_TRUTH_WIRING_OWNER = (
    "ops.integrated_offline_economic_evidence_v1."
    "productive_offline_replay_portfolio_truth_wiring_v1"
)


def apply_pending_portfolio_observation_to_sequence_state_v1(
    sequence_state: MV2IntegratedReplayBarSequenceStateV1,
    pending_observation: ProductiveOfflineSimulatedPortfolioPositionObservationV1 | None,
) -> MV2IntegratedReplayBarSequenceStateV1:
    if pending_observation is None:
        return sequence_state
    return apply_simulated_portfolio_position_feedback_to_mv2_sequence_state_v1(
        sequence_state,
        pending_observation,
    )


def attach_pending_portfolio_observation_to_replay_input_v1(
    replay_input: Any,
    pending_observation: ProductiveOfflineSimulatedPortfolioPositionObservationV1 | None,
) -> Any:
    if pending_observation is None:
        return replay_input
    return replace(
        replay_input,
        productive_offline_simulated_portfolio_position_observation_v1=pending_observation,
    )


def capture_portfolio_observation_after_epoch_v1(
    *,
    portfolio: SimulatedPortfolioEconomicsModelV1,
    instrument_id: str,
    mark_price: Decimal,
    trading_epoch: int,
) -> ProductiveOfflineSimulatedPortfolioPositionObservationV1:
    return capture_productive_offline_simulated_portfolio_position_observation_v1(
        portfolio=portfolio,
        instrument_id=instrument_id,
        mark_price=mark_price,
        feedback_source_bar_epoch=trading_epoch,
    )
