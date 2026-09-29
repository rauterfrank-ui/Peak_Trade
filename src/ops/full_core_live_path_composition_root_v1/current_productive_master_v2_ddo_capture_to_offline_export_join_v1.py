"""Productive MV2 DDO capture → offline research export handoff (observation-only).

Chains the same-cycle ``DdoCaptureBindingV0`` through wallclock N_BARS hosts into
``export_learning_evidence_from_state_v1`` and
``validate_canonical_optimization_universe_learning_input_v1``. Does not apply
optimization, promote parameters, or authorize external effects.

RUNTIME_AUTHORIZATION_EFFECT=NONE
PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED=false
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

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
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
    export_learning_evidence_from_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
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
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_n_bars_horizon_upstream_from_cycle_capture_v1 import (
    maybe_bind_ddo_n_bars_horizon_decision_from_cycle_capture_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_public_plane_convergence_v1 import (
    maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_o4_n_bars_snapshot_materialization_v1 import (
    _decision_event_unix_v1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_MASTER_V2_DDO_CAPTURE_TO_OFFLINE_EXPORT_JOIN_V1"
HANDOFF_ARTIFACT_BASENAME = "ddo_offline_export_handoff_v1.json"
EXTERNAL_EFFECT_AUTHORIZED = False
_POST_COUNT = 0


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


@dataclass
class _WallclockHandoffState:
    """Minimal carrier for productive wallclock host bindings."""

    ddo_capture_binding: DdoCaptureBindingV0
    ddo_canonical_public_md_bar_producer: CanonicalPublicMdBarProducerV1 | None = None
    ddo_durable_evidence_runtime_state_root: Path | None = None
    ddo_n_bars_horizon_decision_event: dict[str, Any] | None = None
    ddo_o4_n_bars_bar_evidence_snapshot: dict[str, Any] | None = None
    ddo_n_bars_horizon_n_bars: int = 2
    cycle_index: int = 0
    last_ddo_n_bars_horizon_observation: dict[str, Any] | None = None
    last_ddo_n_bars_evaluation_runtime: dict[str, Any] | None = None
    last_ddo_learning_state: dict[str, Any] | None = None


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
    """Seed gapless finalized PT1H bars for productive O4 public-plane convergence."""
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
    """Fail-closed handoff from same-cycle capture binding to offline research ack."""
    binding = request.ddo_capture_binding
    summary = request.ddo_capture_summary
    if not binding.enabled:
        return _fail(("CAPTURE_BINDING_DISABLED",))
    if summary.get("ok") is not True or summary.get("skipped") is True:
        return _fail(("CAPTURE_SUMMARY_NOT_OK",))
    if binding.ledger_path is None:
        return _fail(("CAPTURE_LEDGER_UNBOUND",))

    corr = _correlation_id(request.session_id)
    cycle_ref = _cycle_id(request.session_id, request.cycle_index)
    binding.capture_correlation_id = corr
    binding.capture_cycle_id = cycle_ref

    runtime_root = Path(binding.ledger_path).parent
    state = _WallclockHandoffState(
        ddo_capture_binding=binding,
        ddo_durable_evidence_runtime_state_root=runtime_root,
        ddo_n_bars_horizon_n_bars=int(request.n_bars),
        cycle_index=int(request.cycle_index),
    )

    bind_decision = maybe_bind_ddo_n_bars_horizon_decision_from_cycle_capture_v1(
        state,
        correlation_id=corr,
        cycle_id=cycle_ref,
    )
    decision = state.ddo_n_bars_horizon_decision_event
    if bind_decision is None or decision is None:
        return _fail(("DECISION_EVENT_NOT_RESOLVED_FROM_CAPTURE",))

    producer = build_pt1h_bar_producer_from_finalized_closes_v1(
        session_id=request.session_id,
        repository_sha=request.repository_sha,
        venue=request.venue,
        canonical_instrument_id=request.canonical_instrument_id,
        venue_instrument_id=request.venue_instrument_id,
        finalized_closes=request.finalized_closes,
        last_finalized_event_ts_unix=request.last_finalized_event_ts_unix,
        n_bars=int(request.n_bars),
        decision_event=decision,
    )
    if producer is None:
        return _fail(("O4_BAR_PRODUCER_SEED_FAILED",))
    state.ddo_canonical_public_md_bar_producer = producer

    decision_ref = str(decision.get("record_id") or "")
    o4_materialize = maybe_materialize_ddo_o4_n_bars_snapshot_from_public_plane_convergence_v1(
        state,
        decision_event_ref=decision_ref or None,
        n_bars=int(request.n_bars),
    )
    if o4_materialize is not None and o4_materialize.get("ok") is False:
        return _fail(("O4_SNAPSHOT_MATERIALIZATION_FAILED", str(o4_materialize.get("reason"))))
    if state.ddo_o4_n_bars_bar_evidence_snapshot is None:
        return _fail(("O4_SNAPSHOT_MISSING",))

    horizon = invoke_productive_n_bars_horizon_observation_v1(
        state,
        decision_event=decision,
        o4_snapshot=state.ddo_o4_n_bars_bar_evidence_snapshot,
        event_ts_unix=float(request.event_ts_unix),
    )
    state.last_ddo_n_bars_horizon_observation = horizon
    if horizon.get("ok") is not True:
        return _fail(("HORIZON_OBSERVATION_NOT_OK", str(horizon.get("reason"))))

    eval_rt = invoke_productive_n_bars_evaluation_runtime_v1(
        state,
        decision_event=decision,
        identity=None,
        horizon_result=horizon,
        correlation_id=corr,
    )
    state.last_ddo_n_bars_evaluation_runtime = eval_rt
    if eval_rt.get("ok") is not True:
        return _fail(("EVALUATION_RUNTIME_NOT_OK", str(eval_rt.get("reason"))))

    ingest = invoke_productive_learning_outcome_evidence_ingest_v1(
        state,
        evaluation_runtime=eval_rt,
        session_id=request.session_id,
        correlation_id=corr,
        cycle_id=cycle_ref,
    )
    learning_state = state.last_ddo_learning_state
    if ingest.get("ok") is not True or not isinstance(learning_state, dict):
        return _fail(("LEARNING_STATE_INGEST_NOT_OK", str(ingest.get("reason"))))

    try:
        evidence = export_learning_evidence_from_state_v1(
            learning_state,
            correlation_id=corr,
            cycle_id=cycle_ref,
            code_sha=UNKNOWN,
            config_hash=UNKNOWN,
        )
    except DdoValidationError as exc:
        return _fail(("LEARNING_EVIDENCE_EXPORT_FAILED", str(exc)))
    ack = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=evidence)
    )
    ack_status = str(ack.get("status") or "")
    if ack_status != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        return _fail(("OPTIMIZATION_INPUT_NOT_ACCEPTED", ack_status))

    capture_ids = tuple(str(x) for x in (summary.get("record_ids") or ()) if x)
    artifact_path: str | None = None
    if request.persist_handoff_artifact:
        payload = {
            "join_seam_id": JOIN_SEAM_ID,
            "session_id": request.session_id,
            "cycle_id": cycle_ref,
            "correlation_id": corr,
            "capture_record_ids": list(capture_ids),
            "decision_event_ref": decision_ref,
            "learning_state_record_ref": str(learning_state.get("record_id") or ""),
            "learning_evidence_record_id": str(evidence.get("record_id") or ""),
            "optimization_ack_status": ack_status,
            "optimization_ack_reason": ack.get("reason"),
            "export_id": EXPORT_ID,
            "productive_optimization_join_authorized": PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
            "post_count": _POST_COUNT,
        }
        out = runtime_root / HANDOFF_ARTIFACT_BASENAME
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifact_path = str(out)

    return ProductiveDdoCaptureToOfflineExportHandoffResultV1(
        ok=True,
        join_seam_id=JOIN_SEAM_ID,
        fail_closed=False,
        reason_codes=(),
        capture_summary_ok=True,
        decision_event_ref=decision_ref or None,
        learning_state_record_ref=str(learning_state.get("record_id") or "") or None,
        learning_evidence_record_id=str(evidence.get("record_id") or "") or None,
        optimization_ack_status=ack_status,
        optimization_ack_reason=str(ack.get("reason") or "") or None,
        causal_parent_capture_record_ids=capture_ids,
        handoff_artifact_path=artifact_path,
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
