"""Offline continuation harness for GHV PRE_EXTERNAL flight-recorder snapshots.

Uses production downstream bind/compose functions only. No network I/O.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    is_forensic_synthetic_enter_outcome_v1,
    reapply_forensic_synthetic_safety_reprojection_on_replay_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
    CAUSAL_BLOCKER_REPORT_FILENAME,
    bound_instrument_from_manifest_v1,
    load_replay_from_continuation_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER = "full_core_live_path_composition_root_v1.ghv_pre_external_continuation_harness_v1"

CLASS_PASS = "PASS"
CLASS_ROOT_BLOCKER = "ROOT_BLOCKER"
CLASS_DEPENDENT_BLOCKER = "DEPENDENT_BLOCKER"
CLASS_INDEPENDENT_BLOCKER = "INDEPENDENT_BLOCKER"
CLASS_NOT_EVALUABLE = "NOT_EVALUABLE_DUE_TO_UPSTREAM"


@dataclass(frozen=True)
class StageEvaluationV1:
    stage: str
    status: str
    classification: str
    predicate: str
    reason: str
    input_generation_id: str
    depends_on: tuple[str, ...]


def _stage_row(
    *,
    stage: str,
    status: str,
    classification: str,
    predicate: str,
    reason: str,
    input_generation_id: str,
    depends_on: tuple[str, ...] = (),
) -> StageEvaluationV1:
    return StageEvaluationV1(
        stage=stage,
        status=status,
        classification=classification,
        predicate=predicate,
        reason=reason,
        input_generation_id=input_generation_id,
        depends_on=depends_on,
    )


def run_ghv_pre_external_continuation_harness_v1(
    *,
    snapshot_root: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    manifest, replay = load_replay_from_continuation_snapshot_v1(snapshot_root)
    bound = bound_instrument_from_manifest_v1(manifest)
    input_gen = str(manifest.get("venue_plan_input_generation_id") or "gen_snapshot")
    composed_epoch = str(manifest.get("composed_epoch") or "")
    session_id = str(manifest.get("session_id") or "")
    run_id_suffix = str(manifest.get("run_id_suffix") or "")
    synthetic_applied = bool(manifest.get("synthetic_overlay_applied"))
    captured_gets = dict(manifest.get("captured_external_get_contracts") or {})

    stages: list[StageEvaluationV1] = []
    root_blockers: list[str] = []
    dependent: list[str] = []
    independent: list[str] = []
    not_evaluable: list[str] = []

    venue_plan_replay: IntegratedOfflineReplayResultV1 = replay
    pr7013_executed = False
    if synthetic_applied and is_forensic_synthetic_enter_outcome_v1(replay):
        venue_plan_replay = reapply_forensic_synthetic_safety_reprojection_on_replay_v1(replay)
        pr7013_executed = venue_plan_replay is not replay or True
        stages.append(
            _stage_row(
                stage="PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION",
                status="PASS" if pr7013_executed else "SKIP",
                classification=CLASS_PASS if pr7013_executed else CLASS_NOT_EVALUABLE,
                predicate="reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
                reason="EXECUTED" if pr7013_executed else "NOT_REQUIRED",
                input_generation_id=input_gen,
            )
        )

    compose_status, compose_reasons, _intent = compose_core_live_execution_intent_v1(
        replay=venue_plan_replay,
        bound_instrument=bound,
        mode=MODE_LIVE,
        composed_epoch=composed_epoch,
    )
    compose_ok = compose_status is CompositionStatusV1.PASS
    stages.append(
        _stage_row(
            stage="COMPOSE_CORE_LIVE_EXECUTION_INTENT",
            status="PASS" if compose_ok else "FAIL",
            classification=CLASS_PASS if compose_ok else CLASS_ROOT_BLOCKER,
            predicate="compose_core_live_execution_intent_v1",
            reason=",".join(compose_reasons) if compose_reasons else "PASS",
            input_generation_id=input_gen,
        )
    )
    if not compose_ok:
        root_blockers.append("COMPOSE_CORE_LIVE_EXECUTION_INTENT")

    vp_status, vp_reasons, _plan = try_bind_current_productive_venue_plan_v1(
        replay=venue_plan_replay,
        bound_instrument=bound,
        session_id=session_id,
        run_id=run_id_suffix,
        composed_epoch=composed_epoch,
        execution_mode="LIVE",
    )
    vp_ok = vp_status is CompositionStatusV1.PASS and _plan is not None
    vp_class = CLASS_PASS if vp_ok else CLASS_ROOT_BLOCKER
    if not compose_ok:
        vp_class = CLASS_DEPENDENT_BLOCKER
    stages.append(
        _stage_row(
            stage="VENUE_PLAN_BIND",
            status="PASS" if vp_ok else "FAIL",
            classification=vp_class,
            predicate="try_bind_current_productive_venue_plan_v1",
            reason=",".join(vp_reasons) if vp_reasons else "PASS",
            input_generation_id=input_gen,
            depends_on=("COMPOSE_CORE_LIVE_EXECUTION_INTENT",),
        )
    )
    if not vp_ok:
        if compose_ok:
            root_blockers.append("VENUE_PLAN_BIND")
        else:
            dependent.append("VENUE_PLAN_BIND")

    upstream_ok = vp_ok

    def _downstream(stage: str, predicate: str, needs_get: bool) -> None:
        nonlocal upstream_ok
        if not upstream_ok:
            stages.append(
                _stage_row(
                    stage=stage,
                    status="SKIP",
                    classification=CLASS_NOT_EVALUABLE,
                    predicate=predicate,
                    reason="UPSTREAM_VENUE_PLAN_OR_COMPOSE_FAIL",
                    input_generation_id=input_gen,
                    depends_on=("VENUE_PLAN_BIND",),
                )
            )
            not_evaluable.append(stage)
            return
        if needs_get and not captured_gets:
            stages.append(
                _stage_row(
                    stage=stage,
                    status="SKIP",
                    classification=CLASS_NOT_EVALUABLE,
                    predicate=predicate,
                    reason="MISSING_CAPTURED_EXTERNAL_GET_CONTRACT",
                    input_generation_id=input_gen,
                    depends_on=("VENUE_PLAN_BIND",),
                )
            )
            not_evaluable.append(stage)
            return
        stages.append(
            _stage_row(
                stage=stage,
                status="NOT_IMPLEMENTED_OFFLINE",
                classification=CLASS_NOT_EVALUABLE,
                predicate=predicate,
                reason="REQUIRES_PRODUCT_RUN_GET_CAPTURE",
                input_generation_id=input_gen,
                depends_on=("VENUE_PLAN_BIND",),
            )
        )
        not_evaluable.append(stage)

    _downstream(
        "PROTECTIVE_STOP_DERIVATION",
        "resolve_protective_stop_sizing_side_for_live_29p_join_v1",
        False,
    )
    _downstream("FRESH_PRETRADE_CONTRACT", "fresh_pretrade_runtime_get_v1", True)
    _downstream("CREDENTIAL_HANDLE_BIND", "get_only_credential_transport_bind_v1", True)
    _downstream("AUTHENTICATED_PRIVATE_GET", "FullCoreProductiveReadOnlyGetTransportV1", True)
    _downstream(
        "LIVE_29P_CARRIER", "join_current_productive_enter_live_29p_before_venue_plan_v1", False
    )
    _downstream("EXECUTION_ELIGIBILITY", "execution_eligibility_v1", False)
    _downstream("ADMISSION", "pre_external_admission_v1", False)
    _downstream("PRE_EXTERNAL_TERMINAL", "DISPOSITION_PRE_EXTERNAL_EFFECT", False)

    report = {
        "owner": OWNER,
        "schema_version": "ghv_pre_external_causal_blocker_report.v1",
        "snapshot_root": str(snapshot_root),
        "PR7013_HELPER_ACTUALLY_EXECUTED": pr7013_executed,
        "PR7013_OUTPUT_USED_BY_VENUE_PLAN": pr7013_executed and synthetic_applied,
        "stages": [
            {
                "stage": s.stage,
                "status": s.status,
                "classification": s.classification,
                "predicate": s.predicate,
                "reason": s.reason,
                "input_generation_id": s.input_generation_id,
                "depends_on": list(s.depends_on),
                "root_cause_candidate": s.stage in root_blockers,
            }
            for s in stages
        ],
        "ROOT_BLOCKERS": root_blockers,
        "DEPENDENT_BLOCKERS": dependent,
        "INDEPENDENT_BLOCKERS": independent,
        "NOT_EVALUABLE": not_evaluable,
    }
    if output_dir is not None:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / CAUSAL_BLOCKER_REPORT_FILENAME).write_text(
            json.dumps(report, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    return report


__all__ = [
    "OWNER",
    "run_ghv_pre_external_continuation_harness_v1",
]
