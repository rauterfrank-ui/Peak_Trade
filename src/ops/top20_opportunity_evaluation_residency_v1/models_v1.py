"""DTOs for Top20 evaluation residency lifecycle and scheduling."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    DEFAULT_MAX_PENDING,
    DEFAULT_RESIDENCY_DURATION_SECONDS,
    IMPLEMENTATION_SAFETY_MAX_PENDING,
    SCHEMA_VERSION,
    STATE_ABSENT,
    TOP20_EVALUATION_RESIDENCY_ENABLED,
)


def canonical_json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class ResidencyRuntimeConfigV1:
    enabled: bool = TOP20_EVALUATION_RESIDENCY_ENABLED
    max_pending: int = DEFAULT_MAX_PENDING
    duration_seconds: float = DEFAULT_RESIDENCY_DURATION_SECONDS
    early_release_allowed: bool = True

    def validate_v1(self) -> None:
        if int(self.max_pending) <= 0:
            raise ValueError("max_pending_must_be_positive")
        if int(self.max_pending) > IMPLEMENTATION_SAFETY_MAX_PENDING:
            raise ValueError("max_pending_exceeds_safety_bound")
        if float(self.duration_seconds) <= 0:
            raise ValueError("duration_seconds_must_be_positive")


@dataclass(frozen=True)
class CurrentRankObservationV1:
    ranking_snapshot_id: str
    rank: Optional[int]
    in_current_top20: bool
    observed_at_unix: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "in_current_top20": bool(self.in_current_top20),
            "observed_at_unix": float(self.observed_at_unix),
            "rank": self.rank,
            "ranking_snapshot_id": self.ranking_snapshot_id,
        }


@dataclass(frozen=True)
class AdmissionProvenanceV1:
    ranking_snapshot_id: str
    ranking_integrity_digest: str
    universe_snapshot_id: str
    admission_rank: int
    admission_event_time: str
    admission_snapshot_ref: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "admission_event_time": self.admission_event_time,
            "admission_rank": int(self.admission_rank),
            "admission_snapshot_ref": self.admission_snapshot_ref,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "universe_snapshot_id": self.universe_snapshot_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "AdmissionProvenanceV1":
        return AdmissionProvenanceV1(
            ranking_snapshot_id=str(payload["ranking_snapshot_id"]),
            ranking_integrity_digest=str(payload["ranking_integrity_digest"]),
            universe_snapshot_id=str(payload["universe_snapshot_id"]),
            admission_rank=int(payload["admission_rank"]),
            admission_event_time=str(payload["admission_event_time"]),
            admission_snapshot_ref=str(payload["admission_snapshot_ref"]),
        )


@dataclass
class ResidencyRecordV1:
    canonical_instrument_id: str
    universe_snapshot_id: str
    residency_epoch_id: str
    state: str
    admission: AdmissionProvenanceV1
    residency_started_at_unix: float
    residency_deadline_unix: float
    first_admission_sequence: int
    queue_order_key: tuple[int, str]
    active_slot: Optional[int] = None
    post_terminal_outside_top20_observed: bool = False
    current_rank_observations: list[CurrentRankObservationV1] = field(default_factory=list)
    terminal_reason: str = ""
    last_observed_clock_unix: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_slot": self.active_slot,
            "admission": self.admission.to_dict(),
            "canonical_instrument_id": self.canonical_instrument_id,
            "current_rank_observations": [row.to_dict() for row in self.current_rank_observations],
            "first_admission_sequence": int(self.first_admission_sequence),
            "last_observed_clock_unix": float(self.last_observed_clock_unix),
            "post_terminal_outside_top20_observed": bool(self.post_terminal_outside_top20_observed),
            "queue_order_key": [int(self.queue_order_key[0]), str(self.queue_order_key[1])],
            "residency_deadline_unix": float(self.residency_deadline_unix),
            "residency_epoch_id": self.residency_epoch_id,
            "residency_started_at_unix": float(self.residency_started_at_unix),
            "state": self.state,
            "terminal_reason": self.terminal_reason,
            "universe_snapshot_id": self.universe_snapshot_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "ResidencyRecordV1":
        qk = payload.get("queue_order_key") or [0, ""]
        obs = [
            CurrentRankObservationV1(
                ranking_snapshot_id=str(row["ranking_snapshot_id"]),
                rank=(None if row.get("rank") is None else int(row["rank"])),
                in_current_top20=bool(row["in_current_top20"]),
                observed_at_unix=float(row["observed_at_unix"]),
            )
            for row in (payload.get("current_rank_observations") or [])
        ]
        return ResidencyRecordV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            universe_snapshot_id=str(payload["universe_snapshot_id"]),
            residency_epoch_id=str(payload["residency_epoch_id"]),
            state=str(payload["state"]),
            admission=AdmissionProvenanceV1.from_dict(payload.get("admission") or {}),
            residency_started_at_unix=float(payload["residency_started_at_unix"]),
            residency_deadline_unix=float(payload["residency_deadline_unix"]),
            first_admission_sequence=int(payload["first_admission_sequence"]),
            queue_order_key=(int(qk[0]), str(qk[1])),
            active_slot=(
                None if payload.get("active_slot") is None else int(payload["active_slot"])
            ),
            post_terminal_outside_top20_observed=bool(
                payload.get("post_terminal_outside_top20_observed", False)
            ),
            current_rank_observations=obs,
            terminal_reason=str(payload.get("terminal_reason") or ""),
            last_observed_clock_unix=float(payload.get("last_observed_clock_unix") or 0.0),
        )


@dataclass(frozen=True)
class ResidencyStoreSnapshotV1:
    schema_version: str
    next_first_admission_sequence: int
    records: tuple[ResidencyRecordV1, ...]
    last_observed_clock_unix: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_observed_clock_unix": float(self.last_observed_clock_unix),
            "next_first_admission_sequence": int(self.next_first_admission_sequence),
            "records": [row.to_dict() for row in self.records],
            "schema_version": self.schema_version,
        }

    @staticmethod
    def empty() -> "ResidencyStoreSnapshotV1":
        return ResidencyStoreSnapshotV1(
            schema_version=SCHEMA_VERSION,
            next_first_admission_sequence=1,
            records=(),
            last_observed_clock_unix=0.0,
        )


@dataclass(frozen=True)
class EvaluationCompletionWitnessV1:
    canonical_instrument_id: str
    residency_epoch_id: str
    integrated_offline_replay_executed: bool
    governed_cycle_disposition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "governed_cycle_disposition": self.governed_cycle_disposition,
            "integrated_offline_replay_executed": bool(self.integrated_offline_replay_executed),
            "residency_epoch_id": self.residency_epoch_id,
        }


@dataclass(frozen=True)
class ResidencyMetricsV1:
    admissions_total: int = 0
    promotions_total: int = 0
    evaluation_observed_total: int = 0
    expired_pending_total: int = 0
    expired_active_total: int = 0
    capacity_rejected_total: int = 0
    first_admission_to_active_latency_samples: tuple[float, ...] = ()
    active_to_evaluation_observed_latency_samples: tuple[float, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_to_evaluation_observed_latency_samples": list(
                self.active_to_evaluation_observed_latency_samples
            ),
            "admissions_total": int(self.admissions_total),
            "capacity_rejected_total": int(self.capacity_rejected_total),
            "evaluation_observed_total": int(self.evaluation_observed_total),
            "expired_active_total": int(self.expired_active_total),
            "expired_pending_total": int(self.expired_pending_total),
            "first_admission_to_active_latency_samples": list(
                self.first_admission_to_active_latency_samples
            ),
            "promotions_total": int(self.promotions_total),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "ResidencyMetricsV1":
        return ResidencyMetricsV1(
            admissions_total=int(payload.get("admissions_total") or 0),
            promotions_total=int(payload.get("promotions_total") or 0),
            evaluation_observed_total=int(payload.get("evaluation_observed_total") or 0),
            expired_pending_total=int(payload.get("expired_pending_total") or 0),
            expired_active_total=int(payload.get("expired_active_total") or 0),
            capacity_rejected_total=int(payload.get("capacity_rejected_total") or 0),
            first_admission_to_active_latency_samples=tuple(
                float(x) for x in (payload.get("first_admission_to_active_latency_samples") or ())
            ),
            active_to_evaluation_observed_latency_samples=tuple(
                float(x)
                for x in (payload.get("active_to_evaluation_observed_latency_samples") or ())
            ),
        )


def residency_identity_key(
    *, universe_snapshot_id: str, canonical_instrument_id: str
) -> tuple[str, str]:
    return (str(universe_snapshot_id), str(canonical_instrument_id))


def new_residency_epoch_id(
    *, instrument_id: str, sequence: int, admission_ranking_snapshot_id: str
) -> str:
    raw = f"{instrument_id}:{sequence}:{admission_ranking_snapshot_id}"
    return f"re_{sha256_hex(raw)[:16]}"
