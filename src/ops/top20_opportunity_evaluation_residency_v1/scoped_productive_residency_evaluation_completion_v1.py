"""Scoped productive residency evaluation → witness feedback (default-off).

Runs integrated offline evaluation for active residency records, then invokes
``post_orchestrator_evaluation_feedback_v1`` — same seam as N5 control plane.
No harness witness injection; witnesses are derived from evaluation dispositions.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    STATE_ACTIVE_RESIDENT,
    STATE_ADMITTED_PENDING,
    STATE_COMPLETED,
)
from src.ops.top20_opportunity_evaluation_residency_v1.lane_evaluation_witness_disposition_v1 import (
    evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    EvaluationCompletionWitnessV1,
    ResidencyRuntimeConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.orchestration_v1 import (
    post_orchestrator_evaluation_feedback_v1,
    witnesses_from_orchestrator_lane_map_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    active_residents_v1,
    is_canonical_evaluation_complete_v1,
    run_scheduler_tick_v1,
)


@dataclass(frozen=True)
class ScopedResidencyIntegratedEvaluationConfigV1:
    """Offline integrated evaluation inputs (recorded GET only)."""

    dataset_root: Path
    repository_sha: str
    max_cycles: int = 4
    max_duration_seconds: float = 180.0
    g17_provision: str = "natural_checkpoint"


@dataclass(frozen=True)
class ScopedResidencyEvaluationCompletionResultV1:
    ok: bool
    witnesses_applied: int
    witnesses_canonical: int
    failure_codes: tuple[str, ...] = ()


EvaluationDispositionFnV1 = Callable[
    [
        str,
        str,
        ScopedResidencyIntegratedEvaluationConfigV1,
        Path,
    ],
    tuple[bool, str],
]


def venue_native_for_canonical_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    canonical_instrument_id: str,
) -> str:
    cid = str(canonical_instrument_id or "").strip()
    for key in ("instruments", "eligible_instruments"):
        for row in universe_snapshot.get(key) or ():
            if not isinstance(row, Mapping):
                continue
            if str(row.get("canonical_instrument_id") or "").strip() == cid:
                native = str(row.get("venue_native_inst_id") or "").strip()
                if native:
                    return native
    return ""


def _load_ghv_adjudication_module_v1():
    repo = Path(__file__).resolve().parents[3].resolve()
    path = repo / "scripts/ops/run_golden_happy_natural_data_offline_witness_adjudication_v1.py"
    spec = importlib.util.spec_from_file_location("ghv_adj", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _disposition_from_integrated_replay_v1(
    replay: Mapping[str, Any],
) -> tuple[bool, str]:
    ok, witness_disp, _meta = (
        evaluation_witness_disposition_from_n5_compatible_integrated_replay_v1(replay)
    )
    return ok, witness_disp


def default_integrated_residency_evaluation_disposition_v1(
    *,
    venue_native_id: str,
    instrument_id: str,
    config: ScopedResidencyIntegratedEvaluationConfigV1,
    workspace: Path,
) -> tuple[bool, str]:
    adj = _load_ghv_adjudication_module_v1()
    root = Path(config.dataset_root)
    rows = adj._load_jsonl(root / "natural_market_data_get_capture_v1.jsonl")
    report_path = root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    if not report_path.is_file():
        return False, "DATASET_REPORT_MISSING"
    run_id = json.loads(report_path.read_text(encoding="utf-8")).get("RUN_ID")
    if not run_id:
        return False, "DATASET_RUN_ID_MISSING"
    injections = adj._build_injections(adj._bundle_polls(rows, run_id), venue_native_id)
    replay = adj._run_stateful_replay(
        injections=injections,
        native=venue_native_id,
        max_cycles=int(config.max_cycles),
        max_duration=float(config.max_duration_seconds),
        workspace=workspace,
        mode="SCOPED_RESIDENCY_PRODUCTIVE_EVALUATION",
        g17_provision=config.g17_provision,
        dataset_root=root,
        instrument_id=instrument_id,
    )
    return _disposition_from_integrated_replay_v1(replay)


def run_scoped_productive_residency_evaluation_completion_v1(
    *,
    residency_state_root: Path,
    residency_config: ResidencyRuntimeConfigV1,
    universe_snapshot: Mapping[str, Any],
    producer_observed_at_unix: float,
    integrated_evaluation: ScopedResidencyIntegratedEvaluationConfigV1 | None,
    evaluation_disposition_fn: EvaluationDispositionFnV1 | None = None,
    scheduler_tick_unix: float | None = None,
) -> ScopedResidencyEvaluationCompletionResultV1:
    if integrated_evaluation is None:
        return ScopedResidencyEvaluationCompletionResultV1(
            ok=False,
            witnesses_applied=0,
            witnesses_canonical=0,
            failure_codes=("INTEGRATED_EVALUATION_CONFIG_MISSING",),
        )
    residency_state_root.mkdir(parents=True, exist_ok=True)
    tick_unix = float(scheduler_tick_unix or (producer_observed_at_unix + 1.0))
    run_scheduler_tick_v1(
        state_root=residency_state_root,
        config=residency_config,
        now_unix=tick_unix,
    )
    store = load_store_v1(residency_state_root)
    actives = list(active_residents_v1(store))
    if not actives:
        pending = [r for r in store.records if r.state == STATE_ADMITTED_PENDING]
        if pending:
            return ScopedResidencyEvaluationCompletionResultV1(
                ok=False,
                witnesses_applied=0,
                witnesses_canonical=0,
                failure_codes=("ACTIVE_RESIDENT_PROMOTION_MISSING",),
            )
        return ScopedResidencyEvaluationCompletionResultV1(
            ok=False,
            witnesses_applied=0,
            witnesses_canonical=0,
            failure_codes=("NO_RESIDENCY_RECORDS_FOR_EVALUATION",),
        )

    resolve = evaluation_disposition_fn or (
        lambda native, iid, cfg, ws: default_integrated_residency_evaluation_disposition_v1(
            venue_native_id=native,
            instrument_id=iid,
            config=cfg,
            workspace=ws,
        )
    )
    witnesses: list[EvaluationCompletionWitnessV1] = []
    workspace_base = residency_state_root / "_scoped_integrated_evaluation_workspace_v1"
    workspace_base.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for idx, rec in enumerate(actives):
        if rec.state not in {STATE_ACTIVE_RESIDENT}:
            continue
        native = venue_native_for_canonical_v1(
            universe_snapshot=universe_snapshot,
            canonical_instrument_id=rec.canonical_instrument_id,
        )
        if not native:
            failures.append("VENUE_NATIVE_LOOKUP_FAIL")
            continue
        ws = workspace_base / f"eval_{idx}"
        ok, disposition = resolve(
            native,
            rec.canonical_instrument_id,
            integrated_evaluation,
            ws,
        )
        if not ok:
            failures.append(f"EVAL_NOT_COMPLETE:{disposition}")
            continue
        witnesses.append(
            EvaluationCompletionWitnessV1(
                canonical_instrument_id=rec.canonical_instrument_id,
                residency_epoch_id=rec.residency_epoch_id,
                integrated_offline_replay_executed=True,
                governed_cycle_disposition=disposition,
            )
        )

    if not witnesses:
        return ScopedResidencyEvaluationCompletionResultV1(
            ok=False,
            witnesses_applied=0,
            witnesses_canonical=0,
            failure_codes=tuple(failures or ("NO_CANONICAL_WITNESSES",)),
        )

    completion_unix = tick_unix + 1.0
    post_orchestrator_evaluation_feedback_v1(
        residency_state_root=residency_state_root,
        config=residency_config,
        witnesses=witnesses,
        producer_observed_at_unix=completion_unix,
        scoped_productive_activation=True,
    )
    canonical = sum(1 for w in witnesses if is_canonical_evaluation_complete_v1(w))
    completed_store = load_store_v1(residency_state_root)
    completed_count = sum(1 for r in completed_store.records if r.state == STATE_COMPLETED)
    return ScopedResidencyEvaluationCompletionResultV1(
        ok=completed_count > 0 and canonical > 0,
        witnesses_applied=len(witnesses),
        witnesses_canonical=canonical,
        failure_codes=tuple(failures),
    )


def witnesses_from_residency_evaluation_results_v1(
    *,
    instrument_ids_by_lane: Mapping[str, str],
    residency_epoch_ids_by_instrument: Mapping[str, str],
    replay_executed_by_lane: Mapping[str, bool],
    disposition_by_lane: Mapping[str, str],
) -> tuple[EvaluationCompletionWitnessV1, ...]:
    """Alias for N5-compatible witness construction (reuse surface)."""

    return witnesses_from_orchestrator_lane_map_v1(
        instrument_ids_by_lane=instrument_ids_by_lane,
        residency_epoch_ids_by_instrument=residency_epoch_ids_by_instrument,
        replay_executed_by_lane=replay_executed_by_lane,
        disposition_by_lane=disposition_by_lane,
    )
