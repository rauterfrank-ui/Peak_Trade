"""Productive offline: simulated portfolio filled position → MV2/CRS observation truth."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, Optional

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    BACKTEST_POSITION_FEEDBACK_ROLE,
    BacktestEnginePositionFeedbackV1,
)
from src.backtest.mv2_research_wiring_v1 import (
    MV2IntegratedReplayBarSequenceStateV1,
    apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)
from src.trading.master_v2.double_play_composition_matrix_v1 import PositionManagementContext
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    EntryExitDirectionState,
    ExistingPositionSide,
    PositionState,
    ReconciliationState,
)
from src.trading.master_v2.double_play_state import SideState
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
)

PRODUCTIVE_OFFLINE_SIMULATED_PORTFOLIO_POSITION_TRUTH_OWNER = (
    "ops.integrated_offline_economic_evidence_v1."
    "productive_offline_simulated_portfolio_position_truth_v1"
)
POSITION_FEEDBACK_OWNER = (
    "backtest.backtest_engine_position_feedback_adapter_v1."
    "apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1"
)
CRS_POSITION_BINDING_OWNER = (
    "trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0"
)

_ZERO = Decimal("0")


@dataclass(frozen=True)
class ProductiveOfflineSimulatedPortfolioPositionObservationV1:
    """Authoritative filled simulated position snapshot for epoch N+1 inputs."""

    feedback_source_bar_epoch: int
    instrument_id: str
    signed_quantity: Decimal
    reconciled_open_position_quantity: Decimal
    current_reconciled_exposure: Decimal
    existing_position_side: ExistingPositionSide
    position_state: PositionState
    position_management_context: PositionManagementContext
    venue_flat: bool
    current_open_positions_count: int
    current_open_side: Optional[str]


def capture_productive_offline_simulated_portfolio_position_observation_v1(
    *,
    portfolio: SimulatedPortfolioEconomicsModelV1,
    instrument_id: str,
    mark_price: Decimal,
    feedback_source_bar_epoch: int,
) -> ProductiveOfflineSimulatedPortfolioPositionObservationV1:
    pos = portfolio.state.positions.get(instrument_id)
    signed = Decimal(str(pos.quantity)) if pos is not None else _ZERO
    abs_q = signed.copy_abs()
    if signed == 0:
        return ProductiveOfflineSimulatedPortfolioPositionObservationV1(
            feedback_source_bar_epoch=feedback_source_bar_epoch,
            instrument_id=instrument_id,
            signed_quantity=_ZERO,
            reconciled_open_position_quantity=_ZERO,
            current_reconciled_exposure=_ZERO,
            existing_position_side=ExistingPositionSide.NONE,
            position_state=PositionState.FLAT_RECONCILED,
            position_management_context=PositionManagementContext.FLAT,
            venue_flat=True,
            current_open_positions_count=0,
            current_open_side=None,
        )
    exposure = abs_q * mark_price.copy_abs()
    if signed > 0:
        side = ExistingPositionSide.LONG
        pm = PositionManagementContext.LONG_POSITION
        open_side = "LONG"
    else:
        side = ExistingPositionSide.SHORT
        pm = PositionManagementContext.SHORT_POSITION
        open_side = "SHORT"
    return ProductiveOfflineSimulatedPortfolioPositionObservationV1(
        feedback_source_bar_epoch=feedback_source_bar_epoch,
        instrument_id=instrument_id,
        signed_quantity=signed,
        reconciled_open_position_quantity=abs_q,
        current_reconciled_exposure=exposure,
        existing_position_side=side,
        position_state=PositionState.OPEN_FULL,
        position_management_context=pm,
        venue_flat=False,
        current_open_positions_count=1,
        current_open_side=open_side,
    )


def portfolio_observation_to_backtest_position_feedback_v1(
    observation: ProductiveOfflineSimulatedPortfolioPositionObservationV1,
) -> BacktestEnginePositionFeedbackV1:
    return BacktestEnginePositionFeedbackV1(
        feedback_source_bar_epoch=observation.feedback_source_bar_epoch,
        position_state=observation.position_state,
        existing_position_side=observation.existing_position_side,
        venue_flat=observation.venue_flat,
        side_state=SideState.NEUTRAL_OBSERVE,
        direction_state=EntryExitDirectionState.NEUTRAL,
        position_management_context=observation.position_management_context,
        reconciliation_state=ReconciliationState.RECONCILED,
        has_open_trade=observation.reconciled_open_position_quantity > 0,
        authority_role=BACKTEST_POSITION_FEEDBACK_ROLE,
    )


def apply_simulated_portfolio_position_feedback_to_mv2_sequence_state_v1(
    sequence_state: MV2IntegratedReplayBarSequenceStateV1,
    observation: ProductiveOfflineSimulatedPortfolioPositionObservationV1,
) -> MV2IntegratedReplayBarSequenceStateV1:
    if observation.reconciled_open_position_quantity <= 0:
        return sequence_state
    feedback = portfolio_observation_to_backtest_position_feedback_v1(observation)
    return apply_backtest_engine_position_feedback_to_mv2_sequence_state_v1(
        sequence_state,
        feedback,
    )


def overlay_portfolio_observation_on_capital_context_v0(
    capital_context: CanonicalCoreRuntimeCapitalContextV0,
    observation: ProductiveOfflineSimulatedPortfolioPositionObservationV1 | None,
) -> CanonicalCoreRuntimeCapitalContextV0:
    if observation is None or observation.reconciled_open_position_quantity <= 0:
        return capital_context
    return replace(
        capital_context,
        current_reconciled_exposure=observation.current_reconciled_exposure,
        current_open_positions_count=observation.current_open_positions_count,
        current_open_side=observation.current_open_side,
        reconciled_open_position_quantity=observation.reconciled_open_position_quantity,
    )


def extract_crs_open_quantity_from_sizing_input_material_v1(
    sizing_input: Any,
) -> Decimal:
    raw = getattr(sizing_input, "reconciled_open_position_quantity", _ZERO)
    return Decimal(str(raw))
