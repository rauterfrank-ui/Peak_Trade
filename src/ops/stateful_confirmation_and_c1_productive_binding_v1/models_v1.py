"""Durable confirmation binding models derived from C1/C2/C3 domain contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    SCHEMA_VERSION,
    STATE_VERSION,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceStateV1,
)
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_digest_v1(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256_hex(body)


@dataclass(frozen=True)
class CanonicalConfirmationStateV1:
    """Minimal durable confirmation state — no parallel Master V2 / Double Play model."""

    confirmation_session_id: str
    instrument_id: str
    venue: str
    observation_acceptance_state: ObservationAcceptanceStateV1
    confirmation_side_carrier: DirectionalConfirmationSideStateCarrierV1
    repository_sha: str
    config_digest: str
    state_version: str = STATE_VERSION
    commit_identity: str = ""
    commit_sequence: int = 0
    prior_commit_seen: bool = False

    def __post_init__(self) -> None:
        if not self.confirmation_session_id.strip():
            raise ValueError("INVALID_CONFIRMATION_SESSION_ID")
        if not self.instrument_id.strip():
            raise ValueError("INVALID_INSTRUMENT_ID")
        if not self.venue.strip():
            raise ValueError("INVALID_VENUE")
        if self.state_version != STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_CONFIRMATION_STATE_VERSION:{self.state_version}")
        bull = self.confirmation_side_carrier.bull_confirmation_state
        bear = self.confirmation_side_carrier.bear_confirmation_state
        if bull.session_id != self.confirmation_session_id:
            raise ValueError("SESSION_ID_CARRIER_MISMATCH")
        if bear.session_id != self.confirmation_session_id:
            raise ValueError("SESSION_ID_CARRIER_MISMATCH")
        if bull.instrument.canonical_instrument_id != self.instrument_id:
            raise ValueError("INSTRUMENT_CARRIER_MISMATCH")
        if bear.instrument.canonical_instrument_id != self.instrument_id:
            raise ValueError("INSTRUMENT_CARRIER_MISMATCH")

    def _durable_observation_state_dict(self) -> dict[str, Any]:
        """Persist C1 cursor without ephemeral transport metadata."""
        payload = self.observation_acceptance_state.to_dict()
        # EPHEMERAL: transport never distinctness authority and must not affect restart digests.
        payload["last_accepted_transport"] = None
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "state_version": self.state_version,
            "confirmation_session_id": self.confirmation_session_id,
            "instrument_id": self.instrument_id,
            "venue": self.venue,
            "observation_acceptance_state": self._durable_observation_state_dict(),
            "confirmation_side_carrier": self.confirmation_side_carrier.to_dict(),
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "commit_identity": self.commit_identity,
            "commit_sequence": int(self.commit_sequence),
            "prior_commit_seen": bool(self.prior_commit_seen),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CanonicalConfirmationStateV1":
        version = str(payload.get("state_version") or "")
        if version != STATE_VERSION:
            raise ValueError(f"UNSUPPORTED_CONFIRMATION_STATE_VERSION:{version}")
        obs_payload = dict(payload["observation_acceptance_state"])
        obs_payload["last_accepted_transport"] = None
        return cls(
            confirmation_session_id=str(payload["confirmation_session_id"]),
            instrument_id=str(payload["instrument_id"]),
            venue=str(payload["venue"]),
            observation_acceptance_state=ObservationAcceptanceStateV1.from_dict(obs_payload),
            confirmation_side_carrier=DirectionalConfirmationSideStateCarrierV1.from_dict(
                payload["confirmation_side_carrier"]
            ),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            state_version=version,
            commit_identity=str(payload.get("commit_identity") or ""),
            commit_sequence=int(payload.get("commit_sequence") or 0),
            prior_commit_seen=bool(payload.get("prior_commit_seen")),
        )

    def state_digest(self) -> str:
        material = dict(self.to_dict())
        material.pop("commit_identity", None)
        material.pop("commit_sequence", None)
        material.pop("prior_commit_seen", None)
        return canonical_digest_v1(material)

    def with_commit(
        self, *, commit_identity: str, commit_sequence: int
    ) -> "CanonicalConfirmationStateV1":
        return CanonicalConfirmationStateV1(
            confirmation_session_id=self.confirmation_session_id,
            instrument_id=self.instrument_id,
            venue=self.venue,
            observation_acceptance_state=self.observation_acceptance_state,
            confirmation_side_carrier=self.confirmation_side_carrier,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            state_version=self.state_version,
            commit_identity=commit_identity,
            commit_sequence=commit_sequence,
            prior_commit_seen=True,
        )


@dataclass(frozen=True)
class ConfirmationBindingEvidenceV1:
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
        }
        digest = self.evidence_digest or canonical_digest_v1(payload)
        payload["evidence_digest"] = digest
        return payload
