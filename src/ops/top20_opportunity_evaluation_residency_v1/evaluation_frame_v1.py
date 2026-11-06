"""Build evaluation consumption frames (admission snapshot + ephemeral membership)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    MembershipContextArtifactV1,
    build_membership_context_artifact_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import ResidencyRecordV1
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import (
    load_admission_snapshot_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.residency_engine_v1 import (
    active_residents_v1,
)


@dataclass(frozen=True)
class EvaluationSchedulingFrameV1:
    residency_epoch_ids: tuple[str, ...]
    ordered_instrument_ids: tuple[str, ...]
    evaluation_ranking_snapshot: Mapping[str, Any]
    membership: MembershipContextArtifactV1
    admission_only: bool = True


def _provenance_from_snapshot(
    snapshot: Mapping[str, Any],
    *,
    source_relative_path: str,
) -> Cap22ProvenanceV1:
    return Cap22ProvenanceV1(
        ranking_snapshot_id=str(snapshot.get("ranking_snapshot_id") or ""),
        ranking_schema_version=str(snapshot.get("schema_version") or ""),
        ranking_integrity_digest=str(snapshot.get("integrity_digest") or ""),
        ranking_event_time=str(snapshot.get("event_time") or ""),
        universe_snapshot_id=str(snapshot.get("universe_snapshot_id") or ""),
        ranking_policy_id=str(snapshot.get("ranking_policy_id") or ""),
        ranking_policy_version=str(snapshot.get("ranking_policy_version") or ""),
        source_relative_path=source_relative_path,
        source_file_sha256="",
        snapshot_state=str(snapshot.get("snapshot_state") or ""),
        top20_candidate_context_limit=int(snapshot.get("top20_candidate_context_limit") or 20),
    )


def build_evaluation_frame_for_records_v1(
    *,
    state_root: Path,
    records: Sequence[ResidencyRecordV1],
) -> EvaluationSchedulingFrameV1:
    if not records:
        raise ValueError("empty_active_records")
    ref = records[0].admission.admission_snapshot_ref
    snapshot = load_admission_snapshot_v1(state_root, ref)
    ranking_id = str(snapshot.get("ranking_snapshot_id") or "")
    for rec in records[1:]:
        if rec.admission.ranking_snapshot_id != ranking_id:
            raise ValueError("mixed_admission_snapshot_in_one_frame")
    ordered = tuple(rec.canonical_instrument_id for rec in records)
    provenance = _provenance_from_snapshot(
        snapshot,
        source_relative_path=ref,
    )
    membership = build_membership_context_artifact_v1(
        ordered_instrument_ids=ordered,
        cap22_provenance=provenance,
        bootstrap=True,
        prior_membership_reference=None,
    )
    return EvaluationSchedulingFrameV1(
        residency_epoch_ids=tuple(rec.residency_epoch_id for rec in records),
        ordered_instrument_ids=ordered,
        evaluation_ranking_snapshot=snapshot,
        membership=membership,
        admission_only=True,
    )


def plan_evaluation_frames_v1(
    *,
    state_root: Path,
    store: Any,
) -> tuple[EvaluationSchedulingFrameV1, ...]:
    """Group active residents by admission snapshot (one frame per snapshot id)."""
    actives = list(active_residents_v1(store))
    if not actives:
        return ()
    by_snapshot: dict[str, list[ResidencyRecordV1]] = {}
    for row in actives:
        by_snapshot.setdefault(row.admission.ranking_snapshot_id, []).append(row)
    frames: list[EvaluationSchedulingFrameV1] = []
    for _sid, group in sorted(by_snapshot.items()):
        group_sorted = sorted(
            group, key=lambda r: (r.admission.admission_rank, r.canonical_instrument_id)
        )
        frames.append(
            build_evaluation_frame_for_records_v1(state_root=state_root, records=group_sorted)
        )
    return tuple(frames)


def resolve_staged_evaluation_consumption_v1(
    *,
    state_root: Path,
    store: Any,
) -> Optional[tuple[EvaluationSchedulingFrameV1, ...]]:
    frames = plan_evaluation_frames_v1(state_root=state_root, store=store)
    return frames if frames else None
