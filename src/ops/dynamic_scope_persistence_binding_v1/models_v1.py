"""Durable dynamic-scope models derived from RuntimeScopeState + CanonicalScopeSnapshotV1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    ALLOWED_RESET_REASONS,
    CAPABILITY_ID,
    SCHEMA_VERSION,
    STATE_VERSION,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
)
from trading.master_v2.double_play_state import RuntimeScopeState


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body)


def runtime_scope_state_to_dict(state: RuntimeScopeState) -> dict[str, Any]:
    return asdict(state)


def runtime_scope_state_from_dict(payload: Mapping[str, Any]) -> RuntimeScopeState:
    return RuntimeScopeState(
        anchor_price=float(payload.get("anchor_price") or 0.0),
        current_upscope_boundary=float(payload.get("current_upscope_boundary") or 0.0),
        current_downscope_boundary=float(payload.get("current_downscope_boundary") or 0.0),
        current_hysteresis_band=float(payload.get("current_hysteresis_band") or 0.0),
        last_switch_tick=int(payload.get("last_switch_tick") or -1_000_000),
        now_tick=int(payload.get("now_tick") or 0),
        scope_stability_ticks=int(payload.get("scope_stability_ticks") or 0),
        switches_in_window=int(payload.get("switches_in_window") or 0),
        window_start_tick=int(payload.get("window_start_tick") or 0),
        last_completed_side_switch_tick=int(
            payload.get("last_completed_side_switch_tick") or -1_000_000
        ),
        chop_latched=bool(payload.get("chop_latched")),
    )


def canonical_scope_snapshot_to_dict(scope: CanonicalScopeSnapshotV1) -> dict[str, Any]:
    return {
        "scope_id": scope.scope_id,
        "instrument_id": scope.instrument_id,
        "initialized_at_trading_epoch": int(scope.initialized_at_trading_epoch),
        "source_market_context_id": scope.source_market_context_id,
        "source_input_digest": scope.source_input_digest,
        "lifecycle_state": scope.lifecycle_state.value,
        "reference_price": float(scope.reference_price),
        "volatility_estimate": float(scope.volatility_estimate),
        "initial_volatility_distance": float(scope.initial_volatility_distance),
        "scope_band": float(scope.scope_band),
        "neutral_upper_boundary": float(scope.neutral_upper_boundary),
        "neutral_lower_boundary": float(scope.neutral_lower_boundary),
        "trailing_anchor": float(scope.trailing_anchor),
        "min_scope_band": float(scope.min_scope_band),
        "max_scope_band": float(scope.max_scope_band),
        "policy_version": scope.policy_version,
        "semantic_digest": scope.semantic_digest,
        "reason_codes": list(scope.reason_codes),
    }


def canonical_scope_snapshot_from_dict(payload: Mapping[str, Any]) -> CanonicalScopeSnapshotV1:
    return CanonicalScopeSnapshotV1(
        scope_id=str(payload["scope_id"]),
        instrument_id=str(payload["instrument_id"]),
        initialized_at_trading_epoch=int(payload["initialized_at_trading_epoch"]),
        source_market_context_id=str(payload["source_market_context_id"]),
        source_input_digest=str(payload["source_input_digest"]),
        lifecycle_state=CanonicalScopeLifecycleState(str(payload["lifecycle_state"])),
        reference_price=float(payload["reference_price"]),
        volatility_estimate=float(payload["volatility_estimate"]),
        initial_volatility_distance=float(payload["initial_volatility_distance"]),
        scope_band=float(payload["scope_band"]),
        neutral_upper_boundary=float(payload["neutral_upper_boundary"]),
        neutral_lower_boundary=float(payload["neutral_lower_boundary"]),
        trailing_anchor=float(payload["trailing_anchor"]),
        min_scope_band=float(payload["min_scope_band"]),
        max_scope_band=float(payload["max_scope_band"]),
        policy_version=str(payload["policy_version"]),
        semantic_digest=str(payload.get("semantic_digest") or ""),
        reason_codes=tuple(str(x) for x in (payload.get("reason_codes") or ())),
    )


@dataclass(frozen=True)
class ScopeResetRecordV1:
    reason: str
    authority: str
    previous_state_digest: str
    new_state_digest: str
    instrument_identity: str
    event_time_context: str

    def __post_init__(self) -> None:
        if self.reason not in ALLOWED_RESET_REASONS:
            raise ValueError(f"INVALID_RESET_REASON:{self.reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason": self.reason,
            "authority": self.authority,
            "previous_state_digest": self.previous_state_digest,
            "new_state_digest": self.new_state_digest,
            "instrument_identity": self.instrument_identity,
            "event_time_context": self.event_time_context,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ScopeResetRecordV1":
        return cls(
            reason=str(payload["reason"]),
            authority=str(payload["authority"]),
            previous_state_digest=str(payload.get("previous_state_digest") or ""),
            new_state_digest=str(payload.get("new_state_digest") or ""),
            instrument_identity=str(payload["instrument_identity"]),
            event_time_context=str(payload.get("event_time_context") or ""),
        )


@dataclass(frozen=True)
class CanonicalDynamicScopeStateV1:
    """Minimal durable Dynamic Scope state — serialization has no decision authority."""

    scope_session_id: str
    instrument_id: str
    venue: str
    existing_scope: Optional[CanonicalScopeSnapshotV1]
    runtime_scope_state: Optional[RuntimeScopeState]
    runtime_scope_bound_instrument_id: str
    confirmation_session_id: str
    market_observation_epoch: Optional[int]
    last_market_event_time: Optional[float]
    last_accepted_observation_identity_digest: Optional[str]
    position_context: Mapping[str, Any]
    scope_direction_state: str
    side_state: str
    host_trading_epoch: int
    price_path_tail: tuple[float, ...]
    repository_sha: str
    config_digest: str
    previous_state_digest: str = ""
    last_reset: Optional[ScopeResetRecordV1] = None
    state_version: str = STATE_VERSION
    commit_identity: str = ""
    commit_sequence: int = 0
    prior_commit_seen: bool = False

    def __post_init__(self) -> None:
        if not self.scope_session_id.strip():
            raise ValueError("INVALID_SCOPE_SESSION_ID")
        if not self.instrument_id.strip():
            raise ValueError("INVALID_INSTRUMENT_ID")
        if self.state_version != STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_DYNAMIC_SCOPE_STATE_VERSION:{self.state_version}")
        if (
            self.existing_scope is not None
            and self.existing_scope.instrument_id != self.instrument_id
        ):
            raise ValueError("INSTRUMENT_SCOPE_SNAPSHOT_MISMATCH")
        if (
            self.runtime_scope_bound_instrument_id
            and self.runtime_scope_bound_instrument_id != self.instrument_id
        ):
            raise ValueError("INSTRUMENT_RUNTIME_SCOPE_MISMATCH")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "state_version": self.state_version,
            "scope_session_id": self.scope_session_id,
            "instrument_id": self.instrument_id,
            "venue": self.venue,
            "existing_scope": (
                None
                if self.existing_scope is None
                else canonical_scope_snapshot_to_dict(self.existing_scope)
            ),
            "runtime_scope_state": (
                None
                if self.runtime_scope_state is None
                else runtime_scope_state_to_dict(self.runtime_scope_state)
            ),
            "runtime_scope_bound_instrument_id": self.runtime_scope_bound_instrument_id,
            "confirmation_session_id": self.confirmation_session_id,
            "market_observation_epoch": self.market_observation_epoch,
            "last_market_event_time": self.last_market_event_time,
            "last_accepted_observation_identity_digest": (
                self.last_accepted_observation_identity_digest
            ),
            "position_context": dict(self.position_context),
            "scope_direction_state": self.scope_direction_state,
            "side_state": self.side_state,
            "host_trading_epoch": int(self.host_trading_epoch),
            "price_path_tail": [float(x) for x in self.price_path_tail],
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "previous_state_digest": self.previous_state_digest,
            "last_reset": None if self.last_reset is None else self.last_reset.to_dict(),
            "commit_identity": self.commit_identity,
            "commit_sequence": int(self.commit_sequence),
            "prior_commit_seen": bool(self.prior_commit_seen),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CanonicalDynamicScopeStateV1":
        version = str(payload.get("state_version") or "")
        if version != STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_DYNAMIC_SCOPE_STATE_VERSION:{version}")
        existing_raw = payload.get("existing_scope")
        runtime_raw = payload.get("runtime_scope_state")
        reset_raw = payload.get("last_reset")
        return cls(
            scope_session_id=str(payload["scope_session_id"]),
            instrument_id=str(payload["instrument_id"]),
            venue=str(payload["venue"]),
            existing_scope=(
                None if existing_raw is None else canonical_scope_snapshot_from_dict(existing_raw)
            ),
            runtime_scope_state=(
                None if runtime_raw is None else runtime_scope_state_from_dict(runtime_raw)
            ),
            runtime_scope_bound_instrument_id=str(
                payload.get("runtime_scope_bound_instrument_id") or payload["instrument_id"]
            ),
            confirmation_session_id=str(payload.get("confirmation_session_id") or ""),
            market_observation_epoch=(
                None
                if payload.get("market_observation_epoch") is None
                else int(payload["market_observation_epoch"])
            ),
            last_market_event_time=(
                None
                if payload.get("last_market_event_time") is None
                else float(payload["last_market_event_time"])
            ),
            last_accepted_observation_identity_digest=(
                None
                if payload.get("last_accepted_observation_identity_digest") is None
                else str(payload["last_accepted_observation_identity_digest"])
            ),
            position_context=dict(payload.get("position_context") or {}),
            scope_direction_state=str(payload.get("scope_direction_state") or "LONG"),
            side_state=str(payload.get("side_state") or "neutral_observe"),
            host_trading_epoch=int(payload.get("host_trading_epoch") or 0),
            price_path_tail=tuple(float(x) for x in (payload.get("price_path_tail") or ())),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            previous_state_digest=str(payload.get("previous_state_digest") or ""),
            last_reset=(None if reset_raw is None else ScopeResetRecordV1.from_dict(reset_raw)),
            state_version=version,
            commit_identity=str(payload.get("commit_identity") or ""),
            commit_sequence=int(payload.get("commit_sequence") or 0),
            prior_commit_seen=bool(payload.get("prior_commit_seen")),
        )

    def state_digest(self) -> str:
        material = dict(self.to_dict())
        # Commit-chain metadata is not part of the semantic scope digest.
        material.pop("commit_identity", None)
        material.pop("commit_sequence", None)
        material.pop("prior_commit_seen", None)
        material.pop("previous_state_digest", None)
        return canonical_digest_v1(material)

    def with_commit(
        self, *, commit_identity: str, commit_sequence: int
    ) -> "CanonicalDynamicScopeStateV1":
        return CanonicalDynamicScopeStateV1(
            scope_session_id=self.scope_session_id,
            instrument_id=self.instrument_id,
            venue=self.venue,
            existing_scope=self.existing_scope,
            runtime_scope_state=self.runtime_scope_state,
            runtime_scope_bound_instrument_id=self.runtime_scope_bound_instrument_id,
            confirmation_session_id=self.confirmation_session_id,
            market_observation_epoch=self.market_observation_epoch,
            last_market_event_time=self.last_market_event_time,
            last_accepted_observation_identity_digest=(
                self.last_accepted_observation_identity_digest
            ),
            position_context=dict(self.position_context),
            scope_direction_state=self.scope_direction_state,
            side_state=self.side_state,
            host_trading_epoch=self.host_trading_epoch,
            price_path_tail=tuple(self.price_path_tail),
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            previous_state_digest=self.previous_state_digest,
            last_reset=self.last_reset,
            state_version=self.state_version,
            commit_identity=commit_identity,
            commit_sequence=commit_sequence,
            prior_commit_seen=True,
        )


@dataclass(frozen=True)
class DynamicScopeBindingEvidenceV1:
    capability_id: str
    ok: bool
    claims: Mapping[str, Any]
    cycle_telemetry: Mapping[str, Any]
    failure_injection_results: Mapping[str, Any]
    parity_results: Mapping[str, Any]
    restart_results: Mapping[str, Any]
    domain_to_persistence_matrix: tuple[Mapping[str, Any], ...]
    call_graph_before: tuple[str, ...]
    call_graph_after: tuple[str, ...]
    preexisting_evidence_fingerprint: Mapping[str, Any]
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "capability_id": self.capability_id,
            "ok": self.ok,
            "claims": dict(self.claims),
            "cycle_telemetry": dict(self.cycle_telemetry),
            "failure_injection_results": dict(self.failure_injection_results),
            "parity_results": dict(self.parity_results),
            "restart_results": dict(self.restart_results),
            "domain_to_persistence_matrix": [dict(x) for x in self.domain_to_persistence_matrix],
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "preexisting_evidence_fingerprint": dict(self.preexisting_evidence_fingerprint),
        }
        digest = self.evidence_digest or canonical_digest_v1(payload)
        payload["evidence_digest"] = digest
        return payload
