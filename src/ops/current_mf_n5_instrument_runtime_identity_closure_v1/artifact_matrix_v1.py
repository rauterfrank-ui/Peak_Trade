"""Lane-local artifact lifecycle adjudication matrix (D4)."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.constants_v1 import (
    CURSOR_FILENAME,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.constants_v1 import (
    DDO_LEARNING_CAPTURE_LEDGER_BASENAME_V1,
    GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME,
    GOVERNED_CYCLE_LOCK_ROOT_DIRNAME,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    LANE_IDENTITY_MANIFEST_BASENAME,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
    InstrumentSensitiveStateClass,
    StateCarryDisposition,
    adjudicate_instrument_sensitive_state_v1,
)


class LaneArtifactDisposition(str, Enum):
    SAFE_TO_RETAIN = "SAFE_TO_RETAIN"
    IDENTITY_VALIDATED = "IDENTITY_VALIDATED"
    GENERATION_KEYED = "GENERATION_KEYED"
    PURGED_ON_RELEASE_REKEY = "PURGED_ON_RELEASE_REKEY"
    NOT_LANE_LOCAL = "NOT_LANE_LOCAL"


@dataclass(frozen=True)
class LaneArtifactAdjudicationRowV1:
    artifact: str
    disposition: LaneArtifactDisposition
    relative_path: str | None


_ARTIFACT_STATE_CLASS: dict[str, InstrumentSensitiveStateClass] = {
    "cap23_hysteresis": InstrumentSensitiveStateClass.CAP23_HYSTERESIS,
    "cap24_binding": InstrumentSensitiveStateClass.CAP24_BINDING,
    "mv2_cursor": InstrumentSensitiveStateClass.CONFIRMATION_CURSOR,
    "dynamic_scope": InstrumentSensitiveStateClass.RUNTIME_SCOPE,
    "side_state": InstrumentSensitiveStateClass.SIDE_STATE,
    "confirmation_epochs": InstrumentSensitiveStateClass.CONFIRMATION_CURSOR,
    "cooldown_switch": InstrumentSensitiveStateClass.MV2_DP_STATE,
    "ddo_lane_ledger": InstrumentSensitiveStateClass.MV2_DP_STATE,
    "observation_cursor": InstrumentSensitiveStateClass.CONFIRMATION_CURSOR,
    "governed_cycle_lock": InstrumentSensitiveStateClass.MV2_DP_STATE,
    "governed_cycle_evidence": InstrumentSensitiveStateClass.EVIDENCE_REPLAY,
    "lane_identity_manifest": InstrumentSensitiveStateClass.MV2_DP_STATE,
    "reconciliation_lane_cache": InstrumentSensitiveStateClass.RECONCILIATION,
}


def lane_artifact_adjudication_matrix_v1() -> tuple[LaneArtifactAdjudicationRowV1, ...]:
    return (
        LaneArtifactAdjudicationRowV1(
            "cap23_hysteresis", LaneArtifactDisposition.NOT_LANE_LOCAL, None
        ),
        LaneArtifactAdjudicationRowV1(
            "cap24_binding", LaneArtifactDisposition.NOT_LANE_LOCAL, None
        ),
        LaneArtifactAdjudicationRowV1(
            "mv2_cursor",
            LaneArtifactDisposition.IDENTITY_VALIDATED,
            CURSOR_FILENAME,
        ),
        LaneArtifactAdjudicationRowV1(
            "dynamic_scope",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            "dynamic_scope_v1.json",
        ),
        LaneArtifactAdjudicationRowV1(
            "side_state",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            "side_state_v1.json",
        ),
        LaneArtifactAdjudicationRowV1(
            "confirmation_epochs",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            "confirmation_v1.json",
        ),
        LaneArtifactAdjudicationRowV1(
            "cooldown_switch",
            LaneArtifactDisposition.GENERATION_KEYED,
            "cooldown_switch_v1.json",
        ),
        LaneArtifactAdjudicationRowV1(
            "ddo_lane_ledger",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            DDO_LEARNING_CAPTURE_LEDGER_BASENAME_V1,
        ),
        LaneArtifactAdjudicationRowV1(
            "observation_cursor",
            LaneArtifactDisposition.IDENTITY_VALIDATED,
            CURSOR_FILENAME,
        ),
        LaneArtifactAdjudicationRowV1(
            "governed_cycle_lock",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            GOVERNED_CYCLE_LOCK_ROOT_DIRNAME,
        ),
        LaneArtifactAdjudicationRowV1(
            "governed_cycle_evidence",
            LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY,
            GOVERNED_CYCLE_EVIDENCE_ROOT_DIRNAME,
        ),
        LaneArtifactAdjudicationRowV1(
            "lane_identity_manifest",
            LaneArtifactDisposition.GENERATION_KEYED,
            LANE_IDENTITY_MANIFEST_BASENAME,
        ),
        LaneArtifactAdjudicationRowV1(
            "reconciliation_lane_cache",
            LaneArtifactDisposition.NOT_LANE_LOCAL,
            None,
        ),
    )


def _purge_path(lane_state_root: Path, relative: str) -> None:
    target = lane_state_root / relative
    if target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target, ignore_errors=True)


def purge_lane_local_artifacts_for_release_v1(lane_state_root: Path | str) -> None:
    """Remove lane-local mutable artifacts that must not cross instrument generations."""
    root = Path(lane_state_root)
    matrix = lane_artifact_adjudication_matrix_v1()
    for row in matrix:
        if row.disposition != LaneArtifactDisposition.PURGED_ON_RELEASE_REKEY:
            continue
        if not row.relative_path:
            continue
        _purge_path(root, row.relative_path)
    _purge_path(root, CURSOR_FILENAME)


def adjudicate_lane_release_disposition_v1(
    *,
    prior_identity: BoundInstrumentLaneIdentityV1 | None,
    current_identity: OccupiedLaneRuntimeInstrumentIdentityV1,
) -> StateCarryDisposition:
    return adjudicate_instrument_sensitive_state_v1(
        state_class=InstrumentSensitiveStateClass.MV2_DP_STATE,
        prior_identity=prior_identity,
        current_identity=current_identity.lane_identity,
    )


def execute_lane_generation_transition_v1(
    *,
    lane_state_root: Path | str,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    prior_identity: BoundInstrumentLaneIdentityV1 | None,
) -> StateCarryDisposition:
    disposition = adjudicate_lane_release_disposition_v1(
        prior_identity=prior_identity,
        current_identity=identity,
    )
    if prior_identity is not None and disposition in {
        StateCarryDisposition.RESET,
        StateCarryDisposition.REKEY,
    }:
        purge_lane_local_artifacts_for_release_v1(lane_state_root)
    manifest = Path(lane_state_root) / LANE_IDENTITY_MANIFEST_BASENAME
    manifest.parent.mkdir(parents=True, exist_ok=True)
    import json

    manifest.write_text(
        json.dumps(identity.to_manifest_dict(), sort_keys=True, ensure_ascii=True),
        encoding="utf-8",
    )
    return disposition
