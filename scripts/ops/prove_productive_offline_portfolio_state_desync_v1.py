#!/usr/bin/env python3
"""Prove portfolio vs MV2/CRS state desync on bounded productive offline path (read-only)."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.ops import run_current_historical_productive_offline_economic_qualification_v1 as qual
from scripts.ops import stage_okx_economic_research_dataset_from_raw_staging_v1 as research_staging
from scripts.ops.productive_historical_replay_adapter_v1 import (
    apply_g17_typed_volatility_to_context_v1,
    build_strategy_agreement_signal_binding_v1,
    precompute_economic_research_g17_typed_estimates_v1,
    restore_productive_bindings_after_coerce_v1,
)
from src.backtest.mv2_research_wiring_v1 import (
    ObservationClassification,
    WarmupStatus,
    accept_mv2_research_bar_market_observation_v1,
    bind_bar_for_mv2_wiring_v1,
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1,
    _coerce_replay_input_enums_for_integrated_replay_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.productive_offline_economic_completion_v1 import (
    build_productive_replay_baseline_input_v1,
    invoke_current_authoritative_replay_v1,
)
from src.ops.integrated_offline_economic_evidence_v1.replay_simulated_economics_bridge_v1 import (
    apply_replay_result_to_simulated_portfolio_v1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.research.longer_chronological_pit_acquisition_v1 import ENV_ARCHIVE_ROOT
from src.research.longer_chronological_pit_acquisition_v1.archive_root import resolve_archive_root
from src.trading.master_v2.double_play_entry_exit_policy_v0 import PositionState
from trading.master_v2.single_lane_confirmation_activation_v1 import (
    initial_directional_confirmation_side_state_carrier_v1,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Peak_Trade_data_archive")
MAX_EPOCH = 72_000
RT2_ENTRY_EPOCH = 40_808


def _portfolio_qty(portfolio: SimulatedPortfolioEconomicsModelV1, instrument_id: str) -> Decimal:
    pos = portfolio.state.positions.get(instrument_id)
    return Decimal(str(pos.quantity)) if pos else Decimal("0")


def main() -> int:
    os.environ[ENV_ARCHIVE_ROOT] = str(ARCHIVE_ROOT.resolve())
    resolve_archive_root(explicit=ARCHIVE_ROOT.resolve(), require_for_write=False)
    root = _REPO.resolve()
    bars, _, _ = qual._load_governed_dataset(ARCHIVE_ROOT, dataset_version="v3")
    cost_binding = research_staging.build_cost_model_binding()
    profile_binding = research_staging.build_profile_binding(cost_binding)
    research_execution_cost = qual._research_execution_cost_from_binding(cost_binding)
    template = build_productive_replay_baseline_input_v1(trading_epoch=0, current_price=3000.0)
    agreement_binding = build_strategy_agreement_signal_binding_v1(
        qual._strategy_bars_for_agreement_v1(bars)
    )
    typed_g17 = precompute_economic_research_g17_typed_estimates_v1(bars.iloc[:MAX_EPOCH])

    portfolio = SimulatedPortfolioEconomicsModelV1(params=PortfolioEconomicsModelParamsV1())
    sequence_state = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    session_id = "desync-prove-v1"
    witness = None

    for i, (_, bar) in enumerate(bars.iterrows()):
        if i >= MAX_EPOCH:
            break
        if str(bar.get("warmup_status", "warmup_complete")).lower() != "warmup_complete":
            continue
        context, _, _ = bind_bar_for_mv2_wiring_v1(
            bar=bar,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            trading_epoch=i,
            profile_binding=profile_binding,
            research_execution_cost=research_execution_cost,
        )
        context = apply_g17_typed_volatility_to_context_v1(context, typed_estimate=typed_g17.get(i))
        if context.warmup_status != WarmupStatus.WARMUP_COMPLETE:
            continue
        obs = accept_mv2_research_bar_market_observation_v1(
            prior_state=sequence_state.observation_acceptance_state,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            market_event_time=context.market_event_time,
            mark_price=float(context.mark_price),
            session_id=session_id,
            venue="okx_eea",
            input_digest=context.input_digest,
            reset_session=False,
        )
        if obs.result.fail_closed:
            raise RuntimeError(obs.result.reason_code)
        confirmation = sequence_state.directional_confirmation_progress
        if confirmation is None:
            confirmation = initial_directional_confirmation_side_state_carrier_v1(
                session_id=obs.session_id,
                venue=obs.venue,
                instrument=obs.instrument,
            )
        sequence_state = replace(
            sequence_state,
            observation_acceptance_state=obs.state_after,
            last_observation_acceptance_result=obs.result,
            directional_confirmation_progress=confirmation,
            confirmation_progress_session_id=obs.session_id,
            confirmation_progress_venue=obs.venue,
            confirmation_progress_instrument=obs.instrument,
        )
        if obs.result.classification is not ObservationClassification.DISTINCT:
            continue

        pq_before = _portfolio_qty(portfolio, qual.REPLAY_INSTRUMENT_ID)
        mv2_ps = sequence_state.position_state
        built = qual._build_replay_input_from_bar(
            template=template,
            context=context,
            sequence_state=sequence_state,
            trading_epoch=i,
            observation_acceptance_result=obs.result,
        )
        wired, _ = qual._wire_historical_productive_replay_input_v1(
            repo_root=root,
            replay_input=built,
            context=context,
            agreement_binding=agreement_binding,
            trading_epoch=i,
        )
        replay_input = restore_productive_bindings_after_coerce_v1(
            _coerce_replay_input_enums_for_integrated_replay_v1(wired),
            wired=wired,
        )
        result = invoke_current_authoritative_replay_v1(replay_input=replay_input)
        crs_qty = Decimal("0")
        crs_exposure = Decimal("0")
        if result.intermediate and result.intermediate.capital_risk_sizing_decision:
            # sizing input defaults when boundary static
            boundary = replay_input.current_instrument_capital_risk_sizing_boundary_state_file
            if boundary is not None:
                crs_exposure = Decimal(str(getattr(boundary, "current_reconciled_exposure", "0")))

        outcome = str(result.evidence.decision_outcome or "")
        if (
            pq_before != 0
            and mv2_ps is PositionState.FLAT_RECONCILED
            and crs_qty == 0
            and outcome == "enter_short"
            and i >= RT2_ENTRY_EPOCH
        ):
            witness = {
                "epoch": i,
                "portfolio_quantity": str(pq_before),
                "mv2_position_state": mv2_ps.value,
                "crs_open_qty": str(crs_qty),
                "crs_exposure": str(crs_exposure),
                "decision_outcome": outcome,
                "reason_codes": list(result.evidence.reason_codes or ()),
            }
            break

        if result.intermediate is not None:
            sequence_state = project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1(
                intermediate=result.intermediate,
                previous=sequence_state,
                next_trading_epoch=i + 1,
            )
        sequence_state = replace(
            sequence_state,
            prior_mark_price=float(context.mark_price),
            observation_acceptance_state=obs.state_after,
            last_observation_acceptance_result=obs.result,
        )
        apply_replay_result_to_simulated_portfolio_v1(
            portfolio,
            result=result,
            instrument_id=qual.REPLAY_INSTRUMENT_ID,
            mark_price=Decimal(str(context.mark_price)),
        )

    report = {
        "pre_fix_desync_proven": witness is not None,
        "witness": witness,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if witness else 1


if __name__ == "__main__":
    raise SystemExit(main())
