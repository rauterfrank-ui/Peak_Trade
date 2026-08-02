"""Productive C1/C2/C3 confirmation binding for the single-future host.

SERIALIZATION_ADAPTER_HAS_NO_DECISION_AUTHORITY=true
CORE_LOGIC_CHANGE=false
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    DEFAULT_VENUE,
    OWNER,
    STATE_VERSION,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.models_v1 import (
    CanonicalConfirmationStateV1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.persistence_v1 import (
    ConfirmationPersistenceError,
    assert_no_silent_reinitialization_v1,
    load_confirmation_state_v1,
    persist_confirmation_state_atomic_v1,
    prior_commit_exists,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.reason_codes_v1 import (
    ConfirmationBindingFailureCodeV1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.single_writer_v1 import (
    ConfirmationStateSingleWriterV1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
    ObservationAcceptanceStateV1,
    ObservationCandidateV1,
    ObservationClassification,
    ObservationReasonCode,
    ObservationTransportMetadataV1,
    commit_observation_acceptance_v1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
    initial_directional_confirmation_side_state_carrier_v1,
    non_advancing_observation_acceptance_result_v1,
)


class ObservationCycleKindV1(str, Enum):
    MARKET_SAMPLE = "market_sample"
    DUPLICATE_SAMPLE = "duplicate_sample"
    NO_SAMPLE = "no_sample"
    MISSING = "missing"
    OUT_OF_ORDER = "out_of_order"
    DECISION_CYCLE_ONLY = "decision_cycle_only"


def confirmation_config_digest_v1(
    *,
    confirmation_epochs: int = 2,
    confirmation_signal_threshold: float = 0.01,
    candidate_signal_threshold: float = 0.005,
) -> str:
    material = (
        f"cap61-config:epochs={confirmation_epochs}:"
        f"conf_thr={confirmation_signal_threshold}:"
        f"cand_thr={candidate_signal_threshold}:owner={OWNER}:sv={STATE_VERSION}"
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def stable_confirmation_session_id_v1(
    *,
    instrument_id: str,
    venue: str = DEFAULT_VENUE,
    repository_sha: str,
    config_digest: str,
) -> str:
    """Stable across cycles/restarts for one instrument confirmation lifecycle."""
    material = f"confirmation-session:{venue}:{instrument_id}:{repository_sha}:{config_digest}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"cfsess-{venue.lower()}-{instrument_id}-{digest}"


def instrument_key_v1(
    *,
    instrument_id: str,
    venue: str = DEFAULT_VENUE,
    venue_instrument_id: str | None = None,
) -> InstrumentObservationKeyV1:
    return InstrumentObservationKeyV1(
        venue=venue,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_instrument_id or instrument_id,
    )


@dataclass
class HostConfirmationBindingV1:
    """Caller-owned confirmation binding surface carried by BridgeSessionStateV1."""

    enabled: bool = True
    confirmation_session_id: str = ""
    venue: str = DEFAULT_VENUE
    instrument_id: str = ""
    venue_instrument_id: str = ""
    repository_sha: str = ""
    config_digest: str = ""
    observation_acceptance_state: Optional[ObservationAcceptanceStateV1] = None
    confirmation_side_carrier: Optional[DirectionalConfirmationSideStateCarrierV1] = None
    last_observation_acceptance_result: Optional[ObservationAcceptanceResultV1] = None
    state_root: Optional[str] = None
    commit_sequence: int = 0
    prior_commit_seen: bool = False
    initialized: bool = False

    def instrument_key(self) -> InstrumentObservationKeyV1:
        return instrument_key_v1(
            instrument_id=self.instrument_id,
            venue=self.venue,
            venue_instrument_id=self.venue_instrument_id or self.instrument_id,
        )

    def to_canonical_state(self) -> CanonicalConfirmationStateV1:
        if self.observation_acceptance_state is None or self.confirmation_side_carrier is None:
            raise RuntimeError("CONFIRMATION_BINDING_NOT_INITIALIZED")
        return CanonicalConfirmationStateV1(
            confirmation_session_id=self.confirmation_session_id,
            instrument_id=self.instrument_id,
            venue=self.venue,
            observation_acceptance_state=self.observation_acceptance_state,
            confirmation_side_carrier=self.confirmation_side_carrier,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            commit_identity="",
            commit_sequence=self.commit_sequence,
            prior_commit_seen=self.prior_commit_seen,
        )


def ensure_host_confirmation_binding_v1(
    binding: HostConfirmationBindingV1,
    *,
    instrument_id: str,
    venue: str = DEFAULT_VENUE,
    venue_instrument_id: str | None = None,
    repository_sha: str,
    config_digest: str | None = None,
    state_root: Path | None = None,
    require_load_if_prior_commit: bool = True,
) -> HostConfirmationBindingV1:
    """Initialize or restart-load confirmation binding. No silent reinitialization."""
    digest = config_digest or confirmation_config_digest_v1()
    root = (
        Path(state_root)
        if state_root is not None
        else (Path(binding.state_root) if binding.state_root else None)
    )
    if binding.initialized and binding.confirmation_session_id:
        if binding.instrument_id != instrument_id:
            raise ConfirmationPersistenceError(
                ConfirmationBindingFailureCodeV1.INSTRUMENT_ISOLATION_VIOLATION,
                f"{binding.instrument_id}!={instrument_id}",
            )
        if binding.repository_sha != repository_sha:
            raise ConfirmationPersistenceError(
                ConfirmationBindingFailureCodeV1.REPOSITORY_SHA_MISMATCH,
                f"{binding.repository_sha}!={repository_sha}",
            )
        if binding.config_digest != digest:
            raise ConfirmationPersistenceError(
                ConfirmationBindingFailureCodeV1.CONFIG_DIGEST_MISMATCH,
                f"{binding.config_digest}!={digest}",
            )
        return binding

    session_id = stable_confirmation_session_id_v1(
        instrument_id=instrument_id,
        venue=venue,
        repository_sha=repository_sha,
        config_digest=digest,
    )
    key = instrument_key_v1(
        instrument_id=instrument_id,
        venue=venue,
        venue_instrument_id=venue_instrument_id,
    )
    loaded: Optional[CanonicalConfirmationStateV1] = None
    if root is not None:
        binding.state_root = str(root)
        loaded = load_confirmation_state_v1(
            root,
            require_present=bool(require_load_if_prior_commit and prior_commit_exists(root)),
            expected_repository_sha=repository_sha,
            expected_config_digest=digest,
            expected_instrument_id=instrument_id,
            allow_missing_before_first_state=not prior_commit_exists(root),
        )
        assert_no_silent_reinitialization_v1(
            state_root=root,
            loaded=loaded,
            initializing_fresh=loaded is None,
        )

    if loaded is not None:
        if loaded.confirmation_session_id != session_id:
            # Session id is a pure function of bindings; mismatch is integrity failure.
            raise ConfirmationPersistenceError(
                ConfirmationBindingFailureCodeV1.SESSION_ID_UNSTABLE,
                f"{loaded.confirmation_session_id}!={session_id}",
            )
        binding.confirmation_session_id = loaded.confirmation_session_id
        binding.observation_acceptance_state = loaded.observation_acceptance_state
        binding.confirmation_side_carrier = loaded.confirmation_side_carrier
        binding.commit_sequence = loaded.commit_sequence
        binding.prior_commit_seen = True
    else:
        if root is not None and prior_commit_exists(root):
            raise ConfirmationPersistenceError(
                ConfirmationBindingFailureCodeV1.SILENT_REINITIALIZATION_BLOCKED,
                str(root),
            )
        binding.confirmation_session_id = session_id
        binding.observation_acceptance_state = initial_observation_acceptance_state_v1(
            bound_instrument_key=key
        )
        binding.confirmation_side_carrier = initial_directional_confirmation_side_state_carrier_v1(
            session_id=session_id,
            venue=venue,
            instrument=key,
        )
        binding.commit_sequence = 0
        binding.prior_commit_seen = False

    binding.enabled = True
    binding.venue = venue
    binding.instrument_id = instrument_id
    binding.venue_instrument_id = venue_instrument_id or instrument_id
    binding.repository_sha = repository_sha
    binding.config_digest = digest
    binding.initialized = True
    return binding


def _no_sample_result(binding: HostConfirmationBindingV1) -> ObservationAcceptanceResultV1:
    state = binding.observation_acceptance_state
    assert state is not None
    return ObservationAcceptanceResultV1(
        classification=ObservationClassification.DUPLICATE,
        strategy_advance_allowed=False,
        state_before=state,
        state_after=state,
        observation_identity=None,
        reason_code=ObservationReasonCode.DUPLICATE.value,
    )


def evaluate_host_observation_acceptance_v1(
    binding: HostConfirmationBindingV1,
    *,
    mid_price: float | None,
    event_ts_unix: float,
    cycle_index: int,
    kind: ObservationCycleKindV1 = ObservationCycleKindV1.MARKET_SAMPLE,
    force_event_time: float | None = None,
) -> ObservationAcceptanceResultV1:
    """Evaluate C1 for one host cycle. Decision-only / missing / no-sample never advance."""
    if not binding.initialized or binding.observation_acceptance_state is None:
        raise RuntimeError("CONFIRMATION_BINDING_NOT_INITIALIZED")

    if kind in {
        ObservationCycleKindV1.NO_SAMPLE,
        ObservationCycleKindV1.MISSING,
        ObservationCycleKindV1.DECISION_CYCLE_ONLY,
    }:
        result = _no_sample_result(binding)
        binding.last_observation_acceptance_result = result
        return result

    if mid_price is None:
        raise ConfirmationPersistenceError(
            ConfirmationBindingFailureCodeV1.INVALID_OBSERVATION_CYCLE,
            kind.value,
        )

    event_time = float(force_event_time if force_event_time is not None else event_ts_unix)
    if kind is ObservationCycleKindV1.OUT_OF_ORDER:
        last = binding.observation_acceptance_state.last_accepted_observation_identity
        if last is not None:
            event_time = float(last.venue_event_time) - 1.0
        else:
            event_time = 0.0  # invalid / non-positive → fail-closed classification

    transport = ObservationTransportMetadataV1(
        receive_time=float(event_ts_unix),
        runtime_cycle_index=int(cycle_index),
        wallclock_now=float(event_ts_unix),
    )
    if kind is ObservationCycleKindV1.DUPLICATE_SAMPLE:
        last = binding.observation_acceptance_state.last_accepted_observation_identity
        if last is not None:
            event_time = float(last.venue_event_time)
            mid_price = float(last.mark_price)
            # Exact duplicate (not transport-only): reuse last transport fingerprint.
            transport = binding.observation_acceptance_state.last_accepted_transport

    candidate = ObservationCandidateV1(
        venue=binding.venue,
        canonical_instrument_id=binding.instrument_id,
        venue_instrument_id=binding.venue_instrument_id or binding.instrument_id,
        venue_event_time=event_time,
        mark_price=float(mid_price),
        transport=transport,
    )
    result = evaluate_distinct_market_observation_v1(
        binding.observation_acceptance_state,
        candidate,
    )
    binding.last_observation_acceptance_result = result
    return result


def commit_host_confirmation_after_replay_v1(
    binding: HostConfirmationBindingV1,
    *,
    observation_acceptance_result: ObservationAcceptanceResultV1,
    confirmation_side_carrier_after: DirectionalConfirmationSideStateCarrierV1 | None,
    persist: bool = True,
    writer_session_id: str | None = None,
) -> Mapping[str, Any]:
    """Commit C1 acceptance state + C3 carrier; optionally persist durably."""
    if binding.observation_acceptance_state is None:
        raise RuntimeError("CONFIRMATION_BINDING_NOT_INITIALIZED")
    committed = commit_observation_acceptance_v1(
        current_state=binding.observation_acceptance_state,
        result=observation_acceptance_result,
    )
    binding.observation_acceptance_state = committed
    if confirmation_side_carrier_after is not None:
        binding.confirmation_side_carrier = confirmation_side_carrier_after
    persist_result: dict[str, Any] = {"persisted": False}
    if persist and binding.state_root:
        root = Path(binding.state_root)
        writer = ConfirmationStateSingleWriterV1(
            state_root=root,
            session_id=writer_session_id or binding.confirmation_session_id,
            instrument_id=binding.instrument_id,
        )
        writer.acquire()
        try:
            canonical = binding.to_canonical_state()
            out = persist_confirmation_state_atomic_v1(
                state_root=root,
                state=canonical,
                writer=writer,
            )
            committed_state: CanonicalConfirmationStateV1 = out["state"]
            binding.commit_sequence = committed_state.commit_sequence
            binding.prior_commit_seen = True
            persist_result = {
                "persisted": True,
                "commit_identity": committed_state.commit_identity,
                "commit_sequence": committed_state.commit_sequence,
                "state_digest": committed_state.state_digest(),
            }
        finally:
            writer.release()
    return persist_result


def non_advancing_for_binding_v1(
    binding: HostConfirmationBindingV1,
) -> ObservationAcceptanceResultV1:
    return non_advancing_observation_acceptance_result_v1(
        bound_instrument_key=binding.instrument_key(),
        market_observation_epoch=(
            binding.observation_acceptance_state.market_observation_epoch
            if binding.observation_acceptance_state is not None
            else None
        ),
    )
