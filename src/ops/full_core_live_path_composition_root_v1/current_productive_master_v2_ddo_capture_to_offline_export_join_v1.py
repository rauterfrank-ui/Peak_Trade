"""Contain the unverified same-cycle DDO outcome source (observation-only).

Capture remains enabled, but prior closes cannot supply future observed N_BARS
evidence. Until a verified horizon source is bound, this seam returns an explicit
blocked disposition without evaluation, learning, export, or artifact writes.
The legacy bar seed below remains available only for forensic reproduction.

RUNTIME_AUTHORIZATION_EFFECT=NONE
PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED=false
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_horizon_upstream_from_cycle_capture_v1 import (
    resolve_decision_event_from_capture_binding_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    _decision_event_unix_v1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_MASTER_V2_DDO_CAPTURE_TO_OFFLINE_EXPORT_JOIN_V1"
HANDOFF_ARTIFACT_BASENAME = "ddo_offline_export_handoff_v1.json"
EXTERNAL_EFFECT_AUTHORIZED = False
STATUS_BLOCKED_UNVERIFIED_SOURCE = "BLOCKED_UNVERIFIED_OUTCOME_SOURCE"
STATUS_REJECTED_CAPTURE_INPUT = "REJECTED_CAPTURE_INPUT"


@dataclass
class ProductiveDdoCaptureToOfflineExportHandoffRequestV1:
    ddo_capture_binding: DdoCaptureBindingV0
    ddo_capture_summary: Mapping[str, Any]
    session_id: str
    cycle_index: int
    event_ts_unix: float
    repository_sha: str
    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    finalized_closes: Sequence[float]
    last_finalized_event_ts_unix: float
    n_bars: int = 2
    persist_handoff_artifact: bool = True


@dataclass(frozen=True)
class ProductiveDdoCaptureToOfflineExportHandoffResultV1:
    ok: bool
    join_seam_id: str
    fail_closed: bool
    reason_codes: tuple[str, ...]
    capture_summary_ok: bool
    decision_event_ref: str | None
    learning_state_record_ref: str | None
    learning_evidence_record_id: str | None
    optimization_ack_status: str | None
    optimization_ack_reason: str | None
    causal_parent_capture_record_ids: tuple[str, ...]
    handoff_artifact_path: str | None
    status: str = STATUS_REJECTED_CAPTURE_INPUT


def _correlation_id(session_id: str) -> str:
    return f"ddo.corr.{session_id}"[:128]


def _cycle_id(session_id: str, cycle_index: int) -> str:
    return f"{session_id}:cycle:{cycle_index}"


def build_pt1h_bar_producer_from_finalized_closes_v1(
    *,
    session_id: str,
    repository_sha: str,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    finalized_closes: Sequence[float],
    last_finalized_event_ts_unix: float,
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
) -> CanonicalPublicMdBarProducerV1 | None:
    """Reproduce the historical seed for offline forensics, never observed evidence."""
    if n_bars < 2:
        return None
    if len(finalized_closes) < n_bars:
        return None
    producer = CanonicalPublicMdBarProducerV1(
        session_id=session_id[:128],
        repository_sha=repository_sha[:40],
        config_digest="ddo-handoff-o4-seed-v1",
    )
    closes_tail = [float(x) for x in finalized_closes[-n_bars:]]
    hour = 3600.0
    if decision_event is not None:
        try:
            anchor = _decision_event_unix_v1(decision_event)
        except Exception:  # noqa: BLE001
            anchor = float(last_finalized_event_ts_unix)
    else:
        anchor = float(last_finalized_event_ts_unix)
    for bar_index in range(n_bars):
        mark = closes_tail[bar_index]
        event_ts = anchor + (bar_index + 1) * hour
        norm = NormalizedPublicMarketDataV1(
            canonical_instrument_id=canonical_instrument_id,
            venue_instrument_id=venue_instrument_id,
            venue=venue,
            mark_px=mark,
            event_ts_unix=event_ts,
            receive_ts_unix=event_ts + 1.0,
            mark_price_endpoint="/api/v5/public/mark-price",
            mark_price_field="markPx",
            mapping_digest="ddo-handoff-mapping-v1",
            mapping_version="v1",
        )
        opened = producer.ingest_normalized_event(norm)
        if opened.get("accepted") is not True:
            return None
        envelope = opened.get("envelope")
        if not isinstance(envelope, dict):
            return None
        producer.finalize_bar(
            canonical_instrument_id=canonical_instrument_id,
            bar_open_time=float(envelope["bar_open_time"]),
        )
    return producer


def run_productive_ddo_capture_to_offline_export_handoff_v1(
    request: ProductiveDdoCaptureToOfflineExportHandoffRequestV1,
) -> ProductiveDdoCaptureToOfflineExportHandoffResultV1:
    """Reject the unverified source without changing capture or producer results.

    The request shape is retained for existing callers. ``finalized_closes``
    and ``persist_handoff_artifact`` cannot enable the retired seed path.
    Blocked does not mean that a durable pending job has been created.
    """
    binding = request.ddo_capture_binding
    summary = request.ddo_capture_summary
    if not binding.enabled:
        return _fail(("CAPTURE_BINDING_DISABLED",))
    if summary.get("ok") is not True or summary.get("skipped") is True:
        return _fail(("CAPTURE_SUMMARY_NOT_OK",))
    if binding.ledger_path is None:
        return _fail(("CAPTURE_LEDGER_UNBOUND",))
    if summary.get("durable_ok") is False:
        return _fail(("CAPTURE_DURABILITY_FAILED",))

    corr = _correlation_id(request.session_id)
    cycle_ref = _cycle_id(request.session_id, request.cycle_index)
    decision = resolve_decision_event_from_capture_binding_v1(
        binding, correlation_id=corr, cycle_id=cycle_ref
    )
    if decision is None:
        return _fail(("DECISION_EVENT_NOT_RESOLVED_FROM_CAPTURE",))
    # The legacy resolver can fall back to a correlation-only candidate. That
    # fallback is not enough to bind even this cycle's diagnostic decision ref.
    if decision.get("cycle_id") != cycle_ref:
        return _fail(("CAPTURE_DECISION_CYCLE_MISMATCH",))
    return ProductiveDdoCaptureToOfflineExportHandoffResultV1(
        ok=False,
        join_seam_id=JOIN_SEAM_ID,
        fail_closed=True,
        reason_codes=("VERIFIED_N_BARS_SOURCE_NOT_BOUND",),
        capture_summary_ok=True,
        decision_event_ref=str(decision["record_id"]),
        learning_state_record_ref=None,
        learning_evidence_record_id=None,
        optimization_ack_status=None,
        optimization_ack_reason=None,
        causal_parent_capture_record_ids=tuple(str(x) for x in summary.get("record_ids", ()) if x),
        handoff_artifact_path=None,
        status=STATUS_BLOCKED_UNVERIFIED_SOURCE,
    )


def _fail(codes: Sequence[str]) -> ProductiveDdoCaptureToOfflineExportHandoffResultV1:
    return ProductiveDdoCaptureToOfflineExportHandoffResultV1(
        ok=False,
        join_seam_id=JOIN_SEAM_ID,
        fail_closed=True,
        reason_codes=tuple(str(c) for c in codes if c),
        capture_summary_ok=False,
        decision_event_ref=None,
        learning_state_record_ref=None,
        learning_evidence_record_id=None,
        optimization_ack_status=None,
        optimization_ack_reason=None,
        causal_parent_capture_record_ids=(),
        handoff_artifact_path=None,
    )
