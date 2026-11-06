"""Productive wiring helpers (default-off)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import SNAPSHOT_STATE_VALID
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.evaluation_frame_v1 import (
    EvaluationSchedulingFrameV1,
    resolve_staged_evaluation_consumption_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
    ResidencyRuntimeConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    apply_evaluation_completion_v1,
    observe_valid_cap22_ranking_snapshot_v1,
    run_scheduler_tick_v1,
)


def _config(config: Optional[ResidencyRuntimeConfigV1]) -> ResidencyRuntimeConfigV1:
    return config if config is not None else ResidencyRuntimeConfigV1()


def is_residency_feature_enabled_v1(
    config: Optional[ResidencyRuntimeConfigV1] = None,
    *,
    scoped_productive_activation: bool = False,
) -> bool:
    cfg = _config(config)
    if scoped_productive_activation and bool(cfg.enabled):
        return True
    if not TOP20_EVALUATION_RESIDENCY_ENABLED:
        return False
    return bool(cfg.enabled)


@dataclass(frozen=True)
class StagedResidencyPrepareResultV1:
    use_residency_frames: bool
    frames: tuple[EvaluationSchedulingFrameV1, ...]
    residency_state_root: Path


def observe_valid_cap22_snapshot_after_persist_v1(
    *,
    state_root: Path,
    ranking_snapshot: Mapping[str, object],
    producer_observed_at_unix: float,
    config: Optional[ResidencyRuntimeConfigV1] = None,
    universe_snapshot: Optional[Mapping[str, object]] = None,
    scoped_productive_activation: bool = False,
) -> None:
    cfg = _config(config)
    if not is_residency_feature_enabled_v1(
        cfg, scoped_productive_activation=scoped_productive_activation
    ):
        return
    if str(ranking_snapshot.get("snapshot_state") or "") != SNAPSHOT_STATE_VALID:
        return
    state_root.mkdir(parents=True, exist_ok=True)
    residency_root = state_root / "top20_evaluation_residency_v1"
    observe_valid_cap22_ranking_snapshot_v1(
        state_root=residency_root,
        ranking_snapshot=ranking_snapshot,
        config=cfg,
        now_unix=float(producer_observed_at_unix),
        universe_snapshot=universe_snapshot,
    )
    run_scheduler_tick_v1(
        state_root=residency_root,
        config=cfg,
        now_unix=float(producer_observed_at_unix),
    )


def prepare_staged_control_plane_residency_v1(
    *,
    productivity_state_root: Path,
    current_ranking_snapshot: Mapping[str, object],
    producer_observed_at_unix: float,
    config: Optional[ResidencyRuntimeConfigV1] = None,
    universe_snapshot: Optional[Mapping[str, object]] = None,
) -> StagedResidencyPrepareResultV1:
    cfg = _config(config)
    residency_root = Path(productivity_state_root) / "top20_evaluation_residency_v1"
    if not is_residency_feature_enabled_v1(cfg):
        return StagedResidencyPrepareResultV1(False, (), residency_root)
    store = observe_valid_cap22_ranking_snapshot_v1(
        state_root=residency_root,
        ranking_snapshot=current_ranking_snapshot,
        config=cfg,
        now_unix=float(producer_observed_at_unix),
        universe_snapshot=universe_snapshot,
    )
    store = run_scheduler_tick_v1(
        state_root=residency_root,
        config=cfg,
        now_unix=float(producer_observed_at_unix),
    )
    frames = resolve_staged_evaluation_consumption_v1(state_root=residency_root, store=store)
    if not frames:
        return StagedResidencyPrepareResultV1(False, (), residency_root)
    return StagedResidencyPrepareResultV1(True, frames, residency_root)


def post_orchestrator_evaluation_feedback_v1(
    *,
    residency_state_root: Path,
    config: Optional[ResidencyRuntimeConfigV1],
    witnesses: Sequence[EvaluationCompletionWitnessV1],
    producer_observed_at_unix: float,
    scoped_productive_activation: bool = False,
) -> None:
    cfg = _config(config)
    if (
        not is_residency_feature_enabled_v1(
            cfg, scoped_productive_activation=scoped_productive_activation
        )
        or not witnesses
    ):
        return
    apply_evaluation_completion_v1(
        state_root=residency_state_root,
        config=cfg,
        witnesses=witnesses,
        now_unix=float(producer_observed_at_unix),
    )
    run_scheduler_tick_v1(
        state_root=residency_state_root,
        config=cfg,
        now_unix=float(producer_observed_at_unix),
    )


def witnesses_from_orchestrator_lane_map_v1(
    *,
    instrument_ids_by_lane: Mapping[str, str],
    residency_epoch_ids_by_instrument: Mapping[str, str],
    replay_executed_by_lane: Mapping[str, bool],
    disposition_by_lane: Mapping[str, str],
) -> tuple[EvaluationCompletionWitnessV1, ...]:
    out: list[EvaluationCompletionWitnessV1] = []
    for lane_id, instrument in instrument_ids_by_lane.items():
        epoch = residency_epoch_ids_by_instrument.get(instrument)
        if not epoch:
            continue
        from src.ops.top20_opportunity_evaluation_residency_v1.lane_evaluation_witness_disposition_v1 import (
            normalize_lane_disposition_to_evaluation_witness_v1,
        )

        raw_disp = str(disposition_by_lane.get(lane_id) or "")
        normalized = normalize_lane_disposition_to_evaluation_witness_v1(raw_disp) or raw_disp
        out.append(
            EvaluationCompletionWitnessV1(
                canonical_instrument_id=instrument,
                residency_epoch_id=epoch,
                integrated_offline_replay_executed=bool(
                    replay_executed_by_lane.get(lane_id, False)
                ),
                governed_cycle_disposition=normalized,
            )
        )
    return tuple(out)
