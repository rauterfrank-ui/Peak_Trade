"""Evidence captured from the existing F1/M9 decision inside integrated replay."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
    )
    from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
        DoublePlayTypedVolatilityPresenceGateResultV1,
    )
    from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
        IntegratedOfflineReplayInputV1,
    )


@dataclass(frozen=True, slots=True)
class F1M9ReplayHostObservationV1:
    replay_id: str
    instrument_id: str
    trading_epoch: int
    replay_input_digest: str
    market_context_ref: str
    submitted_market_context_digest: str
    submitted_market_event_time: str
    submitted_decision_time: str
    configuration_digest: str | None
    seam_digest: str | None
    owner_apply_record_digest: str | None
    owner_threshold_record_digest: str | None
    configuration_runtime_applied: bool
    threshold_seconds: float | None
    typed_estimate_present: bool
    reference_event_time: str | None
    estimate_as_of_event_time: str | None
    estimate_age_seconds: float | None
    presence_alpha_allowed: bool
    local_enforcement_applied: bool
    local_alpha_allowed: bool
    local_reason_codes: tuple[str, ...]
    host_uses_presence_alpha: bool
    effective_host_alpha_allowed: bool
    host_compatibility_reasons: tuple[str, ...]


@dataclass(slots=True)
class _ReplayObservationCapture:
    replay_input: IntegratedOfflineReplayInputV1
    observations: list[F1M9ReplayHostObservationV1]


_CAPTURE: ContextVar[_ReplayObservationCapture | None] = ContextVar(
    "f1_m9_replay_host_observation_capture", default=None
)


@contextmanager
def capture_f1_m9_replay_host_observations_v1(
    replay_input: IntegratedOfflineReplayInputV1,
) -> Iterator[list[F1M9ReplayHostObservationV1]]:
    """Keep this observation local to one explicit offline replay."""
    observations: list[F1M9ReplayHostObservationV1] = []
    token = _CAPTURE.set(_ReplayObservationCapture(replay_input, observations))
    try:
        yield observations
    finally:
        _CAPTURE.reset(token)


def record_f1_m9_replay_host_observation_v1(
    *,
    presence: DoublePlayTypedVolatilityPresenceGateResultV1,
    consumer_path: F1M9ProductiveRuntimeThresholdConsumerPathResultV1,
    use_presence_alpha: bool,
    effective_alpha: bool,
    compatibility_reasons: tuple[str, ...],
) -> None:
    """Project the observed inputs and return value without reevaluating any gate."""
    capture = _CAPTURE.get()
    if capture is None:
        return
    replay_input = capture.replay_input
    context = replay_input.canonical_market_context
    age = presence.max_age_policy_evidence
    seam = replay_input.governed_authorized_productive_parameter_seam_record
    config_digest = None
    owner_apply_digest = None
    if consumer_path.seam_digest is not None and seam is not None:
        if seam.get("seam_digest") == consumer_path.seam_digest:
            config_digest = seam.get("configuration_digest")
            owner_apply_digest = seam.get("owner_apply_authorization_record_digest")
    observation = F1M9ReplayHostObservationV1(
        replay_id=replay_input.replay_id,
        instrument_id=replay_input.instrument_id,
        trading_epoch=replay_input.trading_epoch,
        replay_input_digest=replay_input.input_digest,
        market_context_ref=context.context_id,
        submitted_market_context_digest=context.input_digest,
        submitted_market_event_time=context.market_event_time,
        submitted_decision_time=context.decision_time,
        configuration_digest=config_digest,
        seam_digest=consumer_path.seam_digest,
        owner_apply_record_digest=owner_apply_digest,
        owner_threshold_record_digest=consumer_path.owner_threshold_record_digest,
        configuration_runtime_applied=consumer_path.configuration_runtime_applied,
        threshold_seconds=consumer_path.threshold_numeric_max_age_seconds,
        typed_estimate_present=presence.typed_estimate_present,
        reference_event_time=age.reference_event_time if age is not None else None,
        estimate_as_of_event_time=age.estimate_as_of_event_time if age is not None else None,
        estimate_age_seconds=age.computed_age_seconds if age is not None else None,
        presence_alpha_allowed=presence.alpha_scope_entry_authority_allowed,
        local_enforcement_applied=consumer_path.enforcement_applied,
        local_alpha_allowed=consumer_path.alpha_scope_entry_authority_allowed,
        local_reason_codes=consumer_path.reason_codes,
        host_uses_presence_alpha=use_presence_alpha,
        effective_host_alpha_allowed=effective_alpha,
        host_compatibility_reasons=compatibility_reasons,
    )
    capture.observations.append(observation)
