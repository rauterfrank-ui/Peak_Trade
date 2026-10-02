"""Residency lifecycle engine: admission, scheduling, expiry, completion."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.top20_opportunity_evaluation_residency_v1.admission_v1 import (
    admission_events_from_valid_snapshot_v1,
    current_rank_observation_for_instrument_v1,
    validate_cap22_integrity_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    EARLY_RELEASE_ALLOWED,
    GOVERNED_CYCLE_SUCCESS_DISPOSITIONS,
    MAX_ACTIVE_EVALUATION_RESIDENTS,
    REASON_CAPACITY_QUEUE_FULL,
    REASON_CLOCK_ROLLBACK,
    REASON_REENTRY_OUTSIDE_TOP20_REQUIRED,
    STATE_ACTIVE_RESIDENT,
    STATE_ADMITTED_PENDING,
    STATE_CAPACITY_REJECTED,
    STATE_COMPLETED,
    STATE_EVALUATION_OBSERVED,
    STATE_EXPIRED_ACTIVE,
    STATE_EXPIRED_PENDING,
    STATE_INVALIDATED,
    TERMINAL_STATES,
)
from src.ops.top20_opportunity_evaluation_residency_v1.hard_invalidation_v1 import (
    hard_invalidation_reason_v1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    AdmissionProvenanceV1,
    CurrentRankObservationV1,
    EvaluationCompletionWitnessV1,
    ResidencyMetricsV1,
    ResidencyRecordV1,
    ResidencyRuntimeConfigV1,
    ResidencyStoreSnapshotV1,
    new_residency_epoch_id,
    residency_identity_key,
)
from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import (
    persist_admission_snapshot_v1,
    persist_bundle_v1,
)


def is_canonical_evaluation_complete_v1(witness: EvaluationCompletionWitnessV1) -> bool:
    if not witness.integrated_offline_replay_executed:
        return False
    return str(witness.governed_cycle_disposition or "") in GOVERNED_CYCLE_SUCCESS_DISPOSITIONS


def _non_terminal_records(store: ResidencyStoreSnapshotV1) -> list[ResidencyRecordV1]:
    return [row for row in store.records if row.state not in TERMINAL_STATES]


def _active_keys(store: ResidencyStoreSnapshotV1) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in _non_terminal_records(store):
        keys.add(
            residency_identity_key(
                universe_snapshot_id=row.universe_snapshot_id,
                canonical_instrument_id=row.canonical_instrument_id,
            )
        )
    return keys


def _append_event(
    *,
    event_type: str,
    record: ResidencyRecordV1,
    extra: Optional[Mapping[str, Any]] = None,
) -> str:
    payload = {
        "event_type": event_type,
        "canonical_instrument_id": record.canonical_instrument_id,
        "residency_epoch_id": record.residency_epoch_id,
        "state": record.state,
    }
    if extra:
        payload.update(dict(extra))
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _apply_clock_guard(
    store: ResidencyStoreSnapshotV1,
    *,
    now_unix: float,
) -> None:
    if store.last_observed_clock_unix and now_unix < store.last_observed_clock_unix:
        raise ValueError(REASON_CLOCK_ROLLBACK)


def _expire_due_records(
    records: list[ResidencyRecordV1],
    *,
    now_unix: float,
    metrics: ResidencyMetricsV1,
) -> tuple[list[ResidencyRecordV1], ResidencyMetricsV1]:
    updated: list[ResidencyRecordV1] = []
    m = metrics
    for row in records:
        if row.state in TERMINAL_STATES:
            updated.append(row)
            continue
        if now_unix >= row.residency_deadline_unix:
            if row.state == STATE_ADMITTED_PENDING:
                row.state = STATE_EXPIRED_PENDING
                row.terminal_reason = "deadline"
                row.active_slot = None
                m = replace(m, expired_pending_total=m.expired_pending_total + 1)
            elif row.state in {STATE_ACTIVE_RESIDENT, STATE_EVALUATION_OBSERVED}:
                row.state = STATE_EXPIRED_ACTIVE
                row.terminal_reason = "deadline"
                row.active_slot = None
                m = replace(m, expired_active_total=m.expired_active_total + 1)
            else:
                row.active_slot = None
        updated.append(row)
    return updated, m


def observe_valid_cap22_ranking_snapshot_v1(
    *,
    state_root: Path,
    ranking_snapshot: Mapping[str, Any],
    config: ResidencyRuntimeConfigV1,
    now_unix: float,
    universe_snapshot: Optional[Mapping[str, Any]] = None,
) -> ResidencyStoreSnapshotV1:
    config.validate_v1()
    integrity_failures = validate_cap22_integrity_v1(ranking_snapshot)
    if integrity_failures:
        return load_only(state_root)
    store = load_only(state_root)
    metrics = _load_metrics(state_root)
    _apply_clock_guard(store, now_unix=now_unix)
    records = list(store.records)
    records, metrics = _expire_due_records(records, now_unix=now_unix, metrics=metrics)

    universe_id = str(ranking_snapshot.get("universe_snapshot_id") or "")
    ref = persist_admission_snapshot_v1(state_root, ranking_snapshot)

    for row in records:
        if row.state in TERMINAL_STATES:
            rank, in_top20 = current_rank_observation_for_instrument_v1(
                ranking_snapshot,
                canonical_instrument_id=row.canonical_instrument_id,
                observed_at_unix=now_unix,
            )
            if not in_top20:
                row.post_terminal_outside_top20_observed = True
            continue
        rank, in_top20 = current_rank_observation_for_instrument_v1(
            ranking_snapshot,
            canonical_instrument_id=row.canonical_instrument_id,
            observed_at_unix=now_unix,
        )
        row.current_rank_observations.append(
            CurrentRankObservationV1(
                ranking_snapshot_id=str(ranking_snapshot.get("ranking_snapshot_id") or ""),
                rank=rank,
                in_current_top20=in_top20,
                observed_at_unix=now_unix,
            )
        )
        row.last_observed_clock_unix = now_unix
        inv = hard_invalidation_reason_v1(
            record_instrument_id=row.canonical_instrument_id,
            universe_snapshot=universe_snapshot,
            admission_universe_snapshot_id=row.universe_snapshot_id,
        )
        if inv:
            row.state = STATE_INVALIDATED
            row.terminal_reason = inv
            row.active_slot = None

    active_keys = _active_keys(
        ResidencyStoreSnapshotV1(
            schema_version=store.schema_version,
            next_first_admission_sequence=store.next_first_admission_sequence,
            records=tuple(records),
            last_observed_clock_unix=store.last_observed_clock_unix,
        )
    )
    pending_count = sum(1 for r in records if r.state == STATE_ADMITTED_PENDING)
    events = sorted(
        admission_events_from_valid_snapshot_v1(
            ranking_snapshot, already_admitted=list(active_keys)
        ),
        key=lambda item: (item[1], item[0]),
    )
    seq = store.next_first_admission_sequence
    for canonical, rank, _row in events:
        key = residency_identity_key(
            universe_snapshot_id=universe_id, canonical_instrument_id=canonical
        )
        if key in active_keys:
            continue
        prior = [r for r in records if r.canonical_instrument_id == canonical]
        if prior:
            last = prior[-1]
            if last.state in TERMINAL_STATES and not last.post_terminal_outside_top20_observed:
                continue
        if pending_count >= int(config.max_pending):
            rec = ResidencyRecordV1(
                canonical_instrument_id=canonical,
                universe_snapshot_id=universe_id,
                residency_epoch_id=new_residency_epoch_id(
                    instrument_id=canonical,
                    sequence=seq,
                    admission_ranking_snapshot_id=str(
                        ranking_snapshot.get("ranking_snapshot_id") or ""
                    ),
                ),
                state=STATE_CAPACITY_REJECTED,
                admission=AdmissionProvenanceV1(
                    ranking_snapshot_id=str(ranking_snapshot.get("ranking_snapshot_id") or ""),
                    ranking_integrity_digest=str(ranking_snapshot.get("integrity_digest") or ""),
                    universe_snapshot_id=universe_id,
                    admission_rank=rank,
                    admission_event_time=str(ranking_snapshot.get("event_time") or ""),
                    admission_snapshot_ref=ref,
                ),
                residency_started_at_unix=now_unix,
                residency_deadline_unix=now_unix,
                first_admission_sequence=seq,
                queue_order_key=(seq, canonical),
                terminal_reason=REASON_CAPACITY_QUEUE_FULL,
                last_observed_clock_unix=now_unix,
            )
            records.append(rec)
            metrics = replace(metrics, capacity_rejected_total=metrics.capacity_rejected_total + 1)
            persist_bundle_v1(
                state_root,
                store=_store_from_records(store, records, now_unix),
                metrics=metrics,
                event_line=_append_event(event_type="CAPACITY_REJECTED", record=rec),
            )
            seq += 1
            continue
        deadline = now_unix + float(config.duration_seconds)
        rec = ResidencyRecordV1(
            canonical_instrument_id=canonical,
            universe_snapshot_id=universe_id,
            residency_epoch_id=new_residency_epoch_id(
                instrument_id=canonical,
                sequence=seq,
                admission_ranking_snapshot_id=str(
                    ranking_snapshot.get("ranking_snapshot_id") or ""
                ),
            ),
            state=STATE_ADMITTED_PENDING,
            admission=AdmissionProvenanceV1(
                ranking_snapshot_id=str(ranking_snapshot.get("ranking_snapshot_id") or ""),
                ranking_integrity_digest=str(ranking_snapshot.get("integrity_digest") or ""),
                universe_snapshot_id=universe_id,
                admission_rank=rank,
                admission_event_time=str(ranking_snapshot.get("event_time") or ""),
                admission_snapshot_ref=ref,
            ),
            residency_started_at_unix=now_unix,
            residency_deadline_unix=deadline,
            first_admission_sequence=seq,
            queue_order_key=(seq, canonical),
            last_observed_clock_unix=now_unix,
        )
        records.append(rec)
        pending_count += 1
        metrics = replace(metrics, admissions_total=metrics.admissions_total + 1)
        persist_bundle_v1(
            state_root,
            store=_store_from_records(store, records, now_unix, next_seq=seq + 1),
            metrics=metrics,
            event_line=_append_event(event_type="ADMITTED_PENDING", record=rec),
        )
        active_keys.add(key)
        seq += 1

    final_store = _store_from_records(store, records, now_unix, next_seq=seq)
    persist_bundle_v1(state_root, store=final_store, metrics=metrics)
    return final_store


def run_scheduler_tick_v1(
    *,
    state_root: Path,
    config: ResidencyRuntimeConfigV1,
    now_unix: float,
) -> ResidencyStoreSnapshotV1:
    config.validate_v1()
    store = load_only(state_root)
    metrics = _load_metrics(state_root)
    _apply_clock_guard(store, now_unix=now_unix)
    records = list(store.records)
    records, metrics = _expire_due_records(records, now_unix=now_unix, metrics=metrics)
    active = [r for r in records if r.state == STATE_ACTIVE_RESIDENT]
    slots_used = {r.active_slot for r in active if r.active_slot is not None}
    pending = sorted(
        [r for r in records if r.state == STATE_ADMITTED_PENDING],
        key=lambda r: (r.queue_order_key[0], r.queue_order_key[1]),
    )
    slot = 1
    while len(active) < MAX_ACTIVE_EVALUATION_RESIDENTS and pending:
        rec = pending.pop(0)
        while slot in slots_used and slot <= MAX_ACTIVE_EVALUATION_RESIDENTS:
            slot += 1
        if slot > MAX_ACTIVE_EVALUATION_RESIDENTS:
            break
        rec.state = STATE_ACTIVE_RESIDENT
        rec.active_slot = slot
        slots_used.add(slot)
        active.append(rec)
        latency = now_unix - rec.residency_started_at_unix
        samples = metrics.first_admission_to_active_latency_samples + (latency,)
        metrics = replace(
            metrics,
            promotions_total=metrics.promotions_total + 1,
            first_admission_to_active_latency_samples=samples,
        )
        persist_bundle_v1(
            state_root,
            store=_store_from_records(store, records, now_unix),
            metrics=metrics,
            event_line=_append_event(
                event_type="ACTIVE_RESIDENT", record=rec, extra={"slot": slot}
            ),
        )
        slot += 1
    final = _store_from_records(store, records, now_unix)
    persist_bundle_v1(state_root, store=final, metrics=metrics)
    return final


def apply_evaluation_completion_v1(
    *,
    state_root: Path,
    config: ResidencyRuntimeConfigV1,
    witnesses: Sequence[EvaluationCompletionWitnessV1],
    now_unix: float,
) -> ResidencyStoreSnapshotV1:
    store = load_only(state_root)
    metrics = _load_metrics(state_root)
    records = list(store.records)
    for witness in witnesses:
        if not is_canonical_evaluation_complete_v1(witness):
            continue
        for idx, row in enumerate(records):
            if row.residency_epoch_id != witness.residency_epoch_id:
                continue
            if row.state not in {STATE_ACTIVE_RESIDENT, STATE_EVALUATION_OBSERVED}:
                continue
            row.state = STATE_EVALUATION_OBSERVED
            latency = now_unix - row.residency_started_at_unix
            samples = metrics.active_to_evaluation_observed_latency_samples + (latency,)
            metrics = replace(
                metrics,
                evaluation_observed_total=metrics.evaluation_observed_total + 1,
                active_to_evaluation_observed_latency_samples=samples,
            )
            if config.early_release_allowed and EARLY_RELEASE_ALLOWED:
                row.state = STATE_COMPLETED
                row.active_slot = None
                row.terminal_reason = "evaluation_observed"
            records[idx] = row
            persist_bundle_v1(
                state_root,
                store=_store_from_records(store, records, now_unix),
                metrics=metrics,
                event_line=_append_event(
                    event_type="EVALUATION_OBSERVED",
                    record=row,
                    extra=witness.to_dict(),
                ),
            )
            break
    final = _store_from_records(store, records, now_unix)
    persist_bundle_v1(state_root, store=final, metrics=metrics)
    return final


def active_residents_v1(store: ResidencyStoreSnapshotV1) -> tuple[ResidencyRecordV1, ...]:
    rows = [r for r in store.records if r.state == STATE_ACTIVE_RESIDENT]
    return tuple(sorted(rows, key=lambda r: (r.active_slot or 999, r.queue_order_key)))


def load_only(state_root: Path) -> ResidencyStoreSnapshotV1:
    from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_store_v1

    return load_store_v1(state_root)


def _load_metrics(state_root: Path) -> ResidencyMetricsV1:
    from src.ops.top20_opportunity_evaluation_residency_v1.persistence_v1 import load_metrics_v1

    return load_metrics_v1(state_root)


def _store_from_records(
    prior: ResidencyStoreSnapshotV1,
    records: list[ResidencyRecordV1],
    now_unix: float,
    *,
    next_seq: Optional[int] = None,
) -> ResidencyStoreSnapshotV1:
    return ResidencyStoreSnapshotV1(
        schema_version=prior.schema_version,
        next_first_admission_sequence=int(
            next_seq if next_seq is not None else prior.next_first_admission_sequence
        ),
        records=tuple(records),
        last_observed_clock_unix=max(prior.last_observed_clock_unix, now_unix),
    )
