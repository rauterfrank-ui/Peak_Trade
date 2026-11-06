"""Session hooks for PRE_EXTERNAL launcher (harness only)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    NaturalEnterReportingResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    ContinuousObservationSourceV1,
    InjectedContinuousObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    extract_mark_and_index_from_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    EVIDENCE_CLASS_REAL_PUBLIC,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import (
    maybe_create_natural_enter_pending_outcome_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.resolver_v1 import (
    advance_all_open_pending_from_mark_v1,
)


@dataclass(frozen=True)
class PreExternalPendingOutcomeSessionResultV1:
    pending_created: bool
    pending_creation_reason: str
    pending_outcome_id: str | None


def finalize_pre_external_session_pending_outcomes_v1(
    *,
    lane_state_root: Path,
    reporting: NaturalEnterReportingResultV1,
    run_id: str,
    evidence_root: Path,
    canonical_instrument_id: str,
    native_id: str,
    decision_timestamp_unix: float,
    decision_reference_price: float,
    market_context_ref: str = "",
    synthetic_enter_observed: bool = False,
    repository_sha: str = "",
) -> PreExternalPendingOutcomeSessionResultV1:
    created = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane_state_root,
        reporting=reporting,
        run_id=run_id,
        evidence_root=evidence_root,
        canonical_instrument_id=canonical_instrument_id,
        native_id=native_id,
        decision_timestamp_unix=decision_timestamp_unix,
        decision_reference_price=decision_reference_price,
        market_context_ref=market_context_ref,
        synthetic_enter_observed=synthetic_enter_observed,
    )
    return PreExternalPendingOutcomeSessionResultV1(
        pending_created=created.created,
        pending_creation_reason=created.reason,
        pending_outcome_id=created.pending_outcome_id,
    )


class _ObservationSourceLike(Protocol):
    def poll(self) -> InjectedContinuousObservationV1 | None: ...


@dataclass
class PendingOutcomeAdvanceObservationSourceV1:
    """Delegates poll; advances open pending outcomes from accepted mark observations."""

    inner: _ObservationSourceLike
    lane_state_root: Path
    evidence_root: Path
    canonical_instrument_id: str
    native_id: str
    repository_sha: str

    def poll(self) -> InjectedContinuousObservationV1 | None:
        observation = self.inner.poll()
        if observation is None:
            return None
        mark_payload = observation.mark_price_payload
        if not isinstance(mark_payload, dict):
            return observation
        mark_px, _idx = extract_mark_and_index_from_payload_v1(
            mark_payload, native_id=self.native_id
        )
        if mark_px is None:
            return observation
        candles = observation.candles_payload
        event_ts = _extract_latest_candle_ts_v1(candles)
        if event_ts is None:
            return observation
        advance_all_open_pending_from_mark_v1(
            lane_state_root=self.lane_state_root,
            canonical_instrument_id=self.canonical_instrument_id,
            native_id=self.native_id,
            mark_px=float(mark_px),
            event_ts_unix=float(event_ts),
            repository_sha=self.repository_sha,
            evidence_root=self.evidence_root,
            evidence_class=EVIDENCE_CLASS_REAL_PUBLIC,
            allow_test_fixture=False,
        )
        return observation


def _extract_latest_candle_ts_v1(candles_payload: Any) -> float | None:
    data = candles_payload.get("data") if isinstance(candles_payload, dict) else None
    if not isinstance(data, list) or not data:
        return None
    row = data[0]
    if isinstance(row, (list, tuple)) and row:
        try:
            return float(row[0]) / 1000.0 if float(row[0]) > 1e12 else float(row[0])
        except (TypeError, ValueError):
            return None
    return None


def wrap_observation_source_for_pending_outcome_advance_v1(
    source: ContinuousObservationSourceV1,
    *,
    lane_state_root: Path,
    evidence_root: Path,
    canonical_instrument_id: str,
    native_id: str,
    repository_sha: str,
) -> ContinuousObservationSourceV1:
    return PendingOutcomeAdvanceObservationSourceV1(
        inner=source,
        lane_state_root=lane_state_root,
        evidence_root=evidence_root,
        canonical_instrument_id=canonical_instrument_id,
        native_id=native_id,
        repository_sha=repository_sha,
    )
