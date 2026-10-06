"""Advance and close pending Natural-Enter outcomes via real O4 path."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    EXPORT_ID,
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
    BAR_STATE_IN_PROGRESS,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_learning_outcome_evidence_ingest_host_binding_v1 import (
    invoke_productive_learning_outcome_evidence_ingest_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_evaluation_runtime_host_binding_v1 import (
    invoke_productive_n_bars_evaluation_runtime_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_horizon_observation_host_binding_v1 import (
    invoke_productive_n_bars_horizon_observation_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    canonical_bar_envelope_to_o4_bar_element_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_public_plane_convergence_v1 import (
    sync_session_producer_finalized_bars_to_wp_a_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    build_o4_n_bars_bar_evidence_snapshot_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    CLOSURE_EVIDENCE_BASENAME,
    EVENT_BAR_INGESTED,
    EVENT_CLOSED,
    EVENT_FAILED,
    EVIDENCE_CLASS_REAL_PUBLIC,
    EVIDENCE_CLASS_TEST_FIXTURE,
    EXTERNAL_EFFECT_AUTHORIZED,
    O4_STATE_DIRNAME,
    POST_COUNT,
    STATUS_CLOSED,
    STATUS_FAILED_TERMINAL,
    STATUS_IN_PROGRESS,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    _events_path,
    lane_pending_lane_dir_v1,
    persist_record_v1,
    replace_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.types_v1 import (
    NaturalEnterPendingOutcomeRecordV1,
)


@dataclass
class _ResolverWallclockState:
    ddo_capture_binding: DdoCaptureBindingV0
    ddo_durable_evidence_runtime_state_root: Path
    ddo_canonical_public_md_bar_producer: CanonicalPublicMdBarProducerV1 | None = None
    ddo_n_bars_horizon_decision_event: dict[str, Any] | None = None
    ddo_o4_n_bars_bar_evidence_snapshot: dict[str, Any] | None = None
    ddo_n_bars_horizon_n_bars: int = 2
    cycle_index: int = 0
    last_ddo_n_bars_horizon_observation: dict[str, Any] | None = None
    last_ddo_n_bars_evaluation_runtime: dict[str, Any] | None = None
    last_ddo_learning_state: dict[str, Any] | None = None


@dataclass(frozen=True)
class PendingOutcomeBarIngestResultV1:
    ok: bool
    advanced: bool
    duplicate: bool
    reason: str
    record: NaturalEnterPendingOutcomeRecordV1 | None = None
    closed: bool = False


@dataclass(frozen=True)
class PendingOutcomeClosureResultV1:
    ok: bool
    reason: str
    record: NaturalEnterPendingOutcomeRecordV1 | None = None
    closure_refs: Mapping[str, str] | None = None


def _o4_runtime_root_v1(lane_state_root: Path, pending_outcome_id: str) -> Path:
    return lane_pending_lane_dir_v1(lane_state_root) / O4_STATE_DIRNAME / pending_outcome_id


def _normalized_from_ingest_detail_v1(
    pending: NaturalEnterPendingOutcomeRecordV1,
    detail: Mapping[str, Any],
) -> NormalizedPublicMarketDataV1 | None:
    try:
        return NormalizedPublicMarketDataV1(
            canonical_instrument_id=pending.canonical_instrument_id,
            venue_instrument_id=str(detail.get("venue_instrument_id") or pending.native_id),
            venue="okx_eea",
            mark_px=float(detail["mark_px"]),
            event_ts_unix=float(detail["event_ts_unix"]),
            receive_ts_unix=float(detail.get("receive_ts_unix") or detail["event_ts_unix"]) + 1.0,
            mark_price_endpoint=str(detail.get("mark_price_endpoint") or "/pending-outcome/replay"),
            mark_price_field="markPx",
            mapping_digest="natural-enter-pending-outcome-v1",
            mapping_version="v1",
        )
    except (KeyError, TypeError, ValueError):
        return None


def _replay_producer_from_pending_events_v1(
    *,
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    repository_sha: str,
) -> CanonicalPublicMdBarProducerV1:
    producer = CanonicalPublicMdBarProducerV1(
        session_id=pending.pending_outcome_id,
        repository_sha=repository_sha[:40],
        config_digest="natural-enter-pending-outcome-o4-v1",
    )
    events_path = _events_path(lane_pending_lane_dir_v1(lane_state_root))
    if not events_path.is_file():
        return producer
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if str(event.get("pending_outcome_id") or "") != pending.pending_outcome_id:
            continue
        if str(event.get("event_type") or "") != EVENT_BAR_INGESTED:
            continue
        detail = event.get("detail") or {}
        norm = _normalized_from_ingest_detail_v1(pending, detail)
        if norm is None:
            continue
        opened = producer.ingest_normalized_event(norm, runtime_cycle_index=0)
        if opened.get("accepted") is not True:
            continue
        envelope = opened.get("envelope")
        if isinstance(envelope, dict):
            try:
                producer.finalize_bar(
                    canonical_instrument_id=pending.canonical_instrument_id,
                    bar_open_time=float(envelope["bar_open_time"]),
                )
            except (ValueError, TypeError):
                pass
    return producer


def _ensure_producer_v1(
    state: _ResolverWallclockState,
    *,
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    repository_sha: str,
) -> CanonicalPublicMdBarProducerV1:
    if state.ddo_canonical_public_md_bar_producer is not None:
        return state.ddo_canonical_public_md_bar_producer
    producer = _replay_producer_from_pending_events_v1(
        lane_state_root=lane_state_root,
        pending=pending,
        repository_sha=repository_sha,
    )
    state.ddo_canonical_public_md_bar_producer = producer
    return producer


def _bar_identity_v1(envelope: Mapping[str, Any]) -> str:
    return (
        f"{envelope.get('canonical_instrument_id')}:"
        f"{envelope.get('bar_open_time')}:"
        f"{envelope.get('bar_close_time')}"
    )


def _count_post_decision_finalized_bars_v1(
    producer: CanonicalPublicMdBarProducerV1,
    *,
    decision_timestamp_unix: float,
    canonical_instrument_id: str,
) -> tuple[int, tuple[str, ...]]:
    identities: list[str] = []
    for env in producer.list_envelopes():
        if str(env.get("finalization_state") or "") != BAR_STATE_FINALIZED:
            continue
        if str(env.get("canonical_instrument_id") or "") != canonical_instrument_id:
            continue
        close_ts = float(env.get("bar_close_time") or 0.0)
        if close_ts <= float(decision_timestamp_unix):
            continue
        identities.append(_bar_identity_v1(env))
    deduped = tuple(dict.fromkeys(identities))
    return len(deduped), deduped


def _load_decision_event_v1(ddo_ledger_path: Path, decision_event_ref: str) -> dict[str, Any]:
    ledger = AppendOnlyDdoLedgerV0(ddo_ledger_path)
    record = dict(ledger.get(decision_event_ref))
    return record


def ingest_pending_outcome_mark_observation_v1(
    *,
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    normalized: NormalizedPublicMarketDataV1,
    repository_sha: str,
    evidence_root: Path | None = None,
    evidence_class: str = EVIDENCE_CLASS_REAL_PUBLIC,
    allow_test_fixture: bool = False,
) -> PendingOutcomeBarIngestResultV1:
    if pending.status == STATUS_CLOSED:
        return PendingOutcomeBarIngestResultV1(
            ok=False, advanced=False, duplicate=False, reason="ALREADY_CLOSED", record=pending
        )
    if evidence_class == EVIDENCE_CLASS_TEST_FIXTURE and not allow_test_fixture:
        return PendingOutcomeBarIngestResultV1(
            ok=False,
            advanced=False,
            duplicate=False,
            reason="TEST_FIXTURE_FORBIDDEN",
            record=pending,
        )
    if normalized.canonical_instrument_id != pending.canonical_instrument_id:
        return PendingOutcomeBarIngestResultV1(
            ok=False,
            advanced=False,
            duplicate=False,
            reason="INSTRUMENT_MISMATCH",
            record=pending,
        )
    if float(normalized.event_ts_unix) <= float(pending.decision_timestamp_unix):
        return PendingOutcomeBarIngestResultV1(
            ok=False,
            advanced=False,
            duplicate=False,
            reason="OBSERVATION_NOT_AFTER_DECISION",
            record=pending,
        )
    runtime_root = _o4_runtime_root_v1(lane_state_root, pending.pending_outcome_id)
    runtime_root.mkdir(parents=True, exist_ok=True)
    ddo_ledger = lane_pending_lane_dir_v1(lane_state_root) / "ddo_learning_capture_v1.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=ddo_ledger)
    state = _ResolverWallclockState(
        ddo_capture_binding=binding,
        ddo_durable_evidence_runtime_state_root=runtime_root,
        ddo_n_bars_horizon_n_bars=int(pending.n_bars_required),
    )
    producer = _ensure_producer_v1(
        state,
        lane_state_root=lane_state_root,
        pending=pending,
        repository_sha=repository_sha,
    )
    ingest = producer.ingest_normalized_event(normalized, runtime_cycle_index=0)
    if ingest.get("accepted") is not True:
        count, identities = _count_post_decision_finalized_bars_v1(
            producer,
            decision_timestamp_unix=pending.decision_timestamp_unix,
            canonical_instrument_id=pending.canonical_instrument_id,
        )
        if count == pending.bars_observed:
            return PendingOutcomeBarIngestResultV1(
                ok=True,
                advanced=False,
                duplicate=True,
                reason="DUPLICATE_OR_NO_NEW_BAR",
                record=pending,
            )
        return PendingOutcomeBarIngestResultV1(
            ok=False, advanced=False, duplicate=False, reason="O4_INGEST_REJECTED", record=pending
        )
    envelope = ingest.get("envelope")
    if not isinstance(envelope, dict):
        return PendingOutcomeBarIngestResultV1(
            ok=False, advanced=False, duplicate=False, reason="O4_ENVELOPE_MISSING", record=pending
        )
    try:
        producer.finalize_bar(
            canonical_instrument_id=pending.canonical_instrument_id,
            bar_open_time=float(envelope["bar_open_time"]),
        )
    except (ValueError, TypeError):
        pass
    for env in list(producer.list_envelopes()):
        if str(env.get("finalization_state") or "") != BAR_STATE_IN_PROGRESS:
            continue
        if float(normalized.event_ts_unix) >= float(env.get("bar_close_time") or 0.0):
            try:
                producer.finalize_bar(
                    canonical_instrument_id=str(env["canonical_instrument_id"]),
                    bar_open_time=float(env["bar_open_time"]),
                )
            except (ValueError, TypeError):
                pass

    count, identities = _count_post_decision_finalized_bars_v1(
        producer,
        decision_timestamp_unix=pending.decision_timestamp_unix,
        canonical_instrument_id=pending.canonical_instrument_id,
    )
    new_identities = [i for i in identities if i not in pending.finalized_bar_identities]
    if not new_identities and count == pending.bars_observed:
        return PendingOutcomeBarIngestResultV1(
            ok=True,
            advanced=False,
            duplicate=True,
            reason="DUPLICATE_OR_NO_NEW_BAR",
            record=pending,
        )
    status = STATUS_IN_PROGRESS if count > 0 else pending.status
    updated = replace_record_v1(
        pending,
        bars_observed=count,
        finalized_bar_identities=identities,
        status=status,
    )
    persist_record_v1(
        lane_state_root,
        event_type=EVENT_BAR_INGESTED,
        record=updated,
        detail={
            "evidence_class": evidence_class,
            "new_bar_identities": new_identities,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "mark_px": float(normalized.mark_px),
            "event_ts_unix": float(normalized.event_ts_unix),
            "receive_ts_unix": float(normalized.receive_ts_unix),
            "venue_instrument_id": str(normalized.venue_instrument_id),
            "mark_price_endpoint": str(normalized.mark_price_endpoint),
        },
    )
    if evidence_root is not None:
        _append_closure_evidence_v1(
            evidence_root,
            {
                "phase": "BAR_INGESTED",
                "pending_outcome_id": pending.pending_outcome_id,
                "decision_event_ref": pending.decision_event_ref,
                "bars_observed": count,
                "evidence_class": evidence_class,
            },
        )
    if count >= pending.n_bars_required:
        closed = try_close_pending_outcome_v1(
            lane_state_root=lane_state_root,
            pending=updated,
            repository_sha=repository_sha,
            evidence_root=evidence_root,
            resolver_state=state,
        )
        return PendingOutcomeBarIngestResultV1(
            ok=closed.ok,
            advanced=True,
            duplicate=False,
            reason=closed.reason,
            record=closed.record,
            closed=closed.ok,
        )
    return PendingOutcomeBarIngestResultV1(
        ok=True,
        advanced=True,
        duplicate=False,
        reason="HORIZON_INCOMPLETE",
        record=updated,
    )


def _materialize_post_decision_o4_snapshot_v1(
    *,
    producer: CanonicalPublicMdBarProducerV1,
    decision_event_ref: str,
    decision_event: Mapping[str, Any],
    decision_timestamp_unix: float,
    n_bars: int,
) -> dict[str, Any]:
    finalized = [
        canonical_bar_envelope_to_o4_bar_element_v1(item)
        for item in producer.list_envelopes()
        if str(item.get("finalization_state") or "") in {BAR_STATE_FINALIZED, BAR_STATE_CORRECTED}
        and float(item.get("bar_close_time") or 0.0) > float(decision_timestamp_unix)
    ]
    return build_o4_n_bars_bar_evidence_snapshot_v1(
        decision_event_ref=decision_event_ref,
        o4_bars=finalized,
        n_bars=n_bars,
        decision_event=decision_event,
        o4_interval_id=producer.interval,
    )


def try_close_pending_outcome_v1(
    *,
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    repository_sha: str,
    evidence_root: Path | None = None,
    resolver_state: _ResolverWallclockState | None = None,
) -> PendingOutcomeClosureResultV1:
    if pending.status == STATUS_CLOSED:
        return PendingOutcomeClosureResultV1(ok=True, reason="ALREADY_CLOSED", record=pending)
    if pending.bars_observed < pending.n_bars_required:
        return PendingOutcomeClosureResultV1(ok=False, reason="HORIZON_INCOMPLETE", record=pending)
    ddo_ledger = lane_pending_lane_dir_v1(lane_state_root) / "ddo_learning_capture_v1.jsonl"
    try:
        decision = _load_decision_event_v1(ddo_ledger, pending.decision_event_ref)
    except DdoValidationError as exc:
        failed = _mark_failed_v1(lane_state_root, pending, str(exc))
        return PendingOutcomeClosureResultV1(ok=False, reason="DECISION_NOT_FOUND", record=failed)

    runtime_root = _o4_runtime_root_v1(lane_state_root, pending.pending_outcome_id)
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=ddo_ledger)
    state = resolver_state or _ResolverWallclockState(
        ddo_capture_binding=binding,
        ddo_durable_evidence_runtime_state_root=runtime_root,
        ddo_n_bars_horizon_n_bars=int(pending.n_bars_required),
    )
    state.ddo_n_bars_horizon_decision_event = decision
    if state.ddo_canonical_public_md_bar_producer is None:
        _ensure_producer_v1(
            state,
            lane_state_root=lane_state_root,
            pending=pending,
            repository_sha=repository_sha,
        )

    decision_ref = str(decision.get("record_id") or pending.decision_event_ref)
    producer = state.ddo_canonical_public_md_bar_producer
    if not isinstance(producer, CanonicalPublicMdBarProducerV1):
        return PendingOutcomeClosureResultV1(ok=False, reason="O4_PRODUCER_MISSING", record=pending)
    sync_session_producer_finalized_bars_to_wp_a_v1(state)
    try:
        snapshot = _materialize_post_decision_o4_snapshot_v1(
            producer=producer,
            decision_event_ref=decision_ref,
            decision_event=decision,
            decision_timestamp_unix=pending.decision_timestamp_unix,
            n_bars=int(pending.n_bars_required),
        )
    except (ValueError, TypeError, DdoValidationError) as exc:
        return PendingOutcomeClosureResultV1(ok=False, reason=str(exc), record=pending)
    state.ddo_o4_n_bars_bar_evidence_snapshot = snapshot

    horizon = invoke_productive_n_bars_horizon_observation_v1(
        state,
        decision_event=decision,
        o4_snapshot=state.ddo_o4_n_bars_bar_evidence_snapshot,
        event_ts_unix=float(pending.decision_timestamp_unix),
    )
    if horizon.get("ok") is not True:
        return PendingOutcomeClosureResultV1(
            ok=False,
            reason=str(
                horizon.get("reason") or horizon.get("horizon_observation_status") or "HORIZON_FAIL"
            ),
            record=pending,
        )
    eval_rt = invoke_productive_n_bars_evaluation_runtime_v1(
        state,
        decision_event=decision,
        identity=None,
        horizon_result=horizon,
        correlation_id=pending.correlation_id or None,
    )
    if eval_rt.get("ok") is not True:
        return PendingOutcomeClosureResultV1(
            ok=False,
            reason=str(eval_rt.get("reason") or "EVAL_RUNTIME_FAIL"),
            record=pending,
        )
    ingest = invoke_productive_learning_outcome_evidence_ingest_v1(
        state,
        evaluation_runtime=eval_rt,
        session_id=pending.source_session_id,
        correlation_id=pending.correlation_id,
        cycle_id=pending.cycle_id,
    )
    learning_state = state.last_ddo_learning_state
    if ingest.get("ok") is not True or not isinstance(learning_state, dict):
        return PendingOutcomeClosureResultV1(
            ok=False,
            reason=str(ingest.get("reason") or "LEARNING_INGEST_FAIL"),
            record=pending,
        )
    try:
        evidence = export_learning_evidence_from_state_v1(
            learning_state,
            correlation_id=pending.correlation_id,
            cycle_id=pending.cycle_id,
            code_sha=UNKNOWN,
            config_hash=UNKNOWN,
        )
    except DdoValidationError as exc:
        return PendingOutcomeClosureResultV1(ok=False, reason=str(exc), record=pending)
    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    if str(ack.get("status") or "") != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        return PendingOutcomeClosureResultV1(
            ok=False,
            reason=str(ack.get("status") or "OPT_ACK_REJECTED"),
            record=pending,
        )

    observation = horizon.get("evaluation_observation") or {}
    closure_refs = {
        "outcome_record_ref": str(
            observation.get("record_id") or eval_rt.get("outcome_record_ref") or ""
        ),
        "learning_state_record_ref": str(learning_state.get("record_id") or ""),
        "learning_evidence_record_id": str(evidence.get("record_id") or ""),
        "optimization_ack_status": str(ack.get("status") or ""),
        "geometry_evidence_ref": str(pending.geometry_evidence_ref or ""),
        "geometry_evidence_digest": str(pending.geometry_evidence_digest or ""),
    }
    closed = replace_record_v1(
        pending,
        status=STATUS_CLOSED,
        closure_refs=closure_refs,
    )
    persist_record_v1(
        lane_state_root,
        event_type=EVENT_CLOSED,
        record=closed,
        detail={
            "export_id": EXPORT_ID,
            "post_count": POST_COUNT,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "real_o4_closure": True,
        },
    )
    if evidence_root is not None:
        _append_closure_evidence_v1(
            evidence_root,
            {
                "phase": "CLOSED",
                "pending_outcome_id": pending.pending_outcome_id,
                "decision_event_ref": pending.decision_event_ref,
                "dpo_ref": pending.dpo_ref,
                **closure_refs,
            },
        )
    return PendingOutcomeClosureResultV1(
        ok=True,
        reason="CLOSED",
        record=closed,
        closure_refs=closure_refs,
    )


def _mark_failed_v1(
    lane_state_root: Path,
    pending: NaturalEnterPendingOutcomeRecordV1,
    reason: str,
) -> NaturalEnterPendingOutcomeRecordV1:
    failed = replace_record_v1(
        pending,
        status=STATUS_FAILED_TERMINAL,
        failure_reason=reason[:512],
    )
    persist_record_v1(
        lane_state_root,
        event_type=EVENT_FAILED,
        record=failed,
        detail={"reason": reason},
    )
    return failed


def _append_closure_evidence_v1(evidence_root: Path, payload: Mapping[str, Any]) -> None:
    path = Path(evidence_root) / CLOSURE_EVIDENCE_BASENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), sort_keys=True) + "\n")


def advance_all_open_pending_from_mark_v1(
    *,
    lane_state_root: Path,
    canonical_instrument_id: str,
    native_id: str,
    mark_px: float,
    event_ts_unix: float,
    repository_sha: str,
    evidence_root: Path | None = None,
    evidence_class: str = EVIDENCE_CLASS_REAL_PUBLIC,
    allow_test_fixture: bool = False,
) -> tuple[PendingOutcomeBarIngestResultV1, ...]:
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
        list_open_pending_outcomes_v1,
    )

    norm = NormalizedPublicMarketDataV1(
        canonical_instrument_id=canonical_instrument_id,
        venue_instrument_id=native_id,
        venue="okx_eea",
        mark_px=float(mark_px),
        event_ts_unix=float(event_ts_unix),
        receive_ts_unix=float(event_ts_unix) + 1.0,
        mark_price_endpoint="/natural-enter-pending-outcome-advance",
        mark_price_field="markPx",
        mapping_digest="natural-enter-pending-outcome-v1",
        mapping_version="v1",
    )
    results: list[PendingOutcomeBarIngestResultV1] = []
    for pending in list_open_pending_outcomes_v1(lane_state_root):
        if pending.native_id and native_id and pending.native_id != native_id:
            continue
        results.append(
            ingest_pending_outcome_mark_observation_v1(
                lane_state_root=lane_state_root,
                pending=pending,
                normalized=norm,
                repository_sha=repository_sha,
                evidence_root=evidence_root,
                evidence_class=evidence_class,
                allow_test_fixture=allow_test_fixture,
            )
        )
    return tuple(results)
