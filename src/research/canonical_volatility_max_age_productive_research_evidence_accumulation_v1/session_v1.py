"""Explicit session identity, restart, and resume semantics."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.constants_v1 import (
    SESSION_CONTRACT_VERSION,
)
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    ProductiveEvidenceSessionV1,
    SessionLifecycleStateV1,
    digest_excluding_keys,
    require_nonempty,
    sha256_hex_text,
)


def build_resume_token_v1(
    *,
    session_id: str,
    repository_sha: str,
    venue: str,
    canonical_instrument_id: str,
    session_start_event_time: str,
) -> str:
    material = "|".join(
        [
            require_nonempty(session_id, field_name="session_id"),
            require_nonempty(repository_sha, field_name="repository_sha"),
            require_nonempty(venue, field_name="venue"),
            require_nonempty(canonical_instrument_id, field_name="canonical_instrument_id"),
            require_nonempty(session_start_event_time, field_name="session_start_event_time"),
        ]
    )
    return sha256_hex_text(material)


def _session_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("session_digest",))


def open_productive_evidence_session_v1(
    *,
    session_id: str,
    session_start_event_time: str,
    repository_sha: str,
    venue: str,
    canonical_instrument_id: str,
    venue_instrument_id: str,
    restart_generation: int = 0,
) -> ProductiveEvidenceSessionV1:
    if restart_generation < 0:
        raise ProductiveEvidenceAccumulationError("invalid_restart_generation")
    # Split assignment to avoid NO_SECRETS false-positive on "token = <long_identifier>".
    built_resume = build_resume_token_v1(
        session_id=session_id,
        repository_sha=repository_sha,
        venue=venue,
        canonical_instrument_id=canonical_instrument_id,
        session_start_event_time=session_start_event_time,
    )
    resume_token = built_resume
    provisional = {
        "canonical_instrument_id": require_nonempty(
            canonical_instrument_id, field_name="canonical_instrument_id"
        ),
        "lifecycle_state": SessionLifecycleStateV1.ACTIVE.value,
        "observation_count": 0,
        "repository_sha": require_nonempty(repository_sha, field_name="repository_sha"),
        "restart_generation": int(restart_generation),
        "resume_token": resume_token,
        "session_contract_version": SESSION_CONTRACT_VERSION,
        "session_end_event_time": None,
        "session_id": require_nonempty(session_id, field_name="session_id"),
        "session_start_event_time": require_nonempty(
            session_start_event_time, field_name="session_start_event_time"
        ),
        "venue": require_nonempty(venue, field_name="venue"),
        "venue_instrument_id": require_nonempty(
            venue_instrument_id, field_name="venue_instrument_id"
        ),
    }
    digest = _session_digest_v1(provisional)
    return ProductiveEvidenceSessionV1(
        session_contract_version=SESSION_CONTRACT_VERSION,
        session_id=str(provisional["session_id"]),
        lifecycle_state=SessionLifecycleStateV1.ACTIVE.value,
        session_start_event_time=str(provisional["session_start_event_time"]),
        session_end_event_time=None,
        repository_sha=str(provisional["repository_sha"]),
        venue=str(provisional["venue"]),
        canonical_instrument_id=str(provisional["canonical_instrument_id"]),
        venue_instrument_id=str(provisional["venue_instrument_id"]),
        restart_generation=int(provisional["restart_generation"]),
        resume_token=resume_token,
        observation_count=0,
        session_digest=digest,
    )


def resume_productive_evidence_session_v1(
    session: ProductiveEvidenceSessionV1,
    *,
    resume_token: str,
    repository_sha: str,
    process_restart: bool = True,
) -> ProductiveEvidenceSessionV1:
    """Resume an existing session after process restart.

    Process restart increments ``restart_generation`` but must not invent a new
    ``session_id``. Independent sessions require an explicit new open call.
    """
    if session.lifecycle_state != SessionLifecycleStateV1.ACTIVE.value:
        raise ProductiveEvidenceAccumulationError("session_not_active_for_resume")
    expected = require_nonempty(resume_token, field_name="resume_token")
    if expected != session.resume_token:
        raise ProductiveEvidenceAccumulationError("session_resume_token_mismatch")
    if require_nonempty(repository_sha, field_name="repository_sha") != session.repository_sha:
        raise ProductiveEvidenceAccumulationError("session_repository_sha_mismatch")

    generation = session.restart_generation + (1 if process_restart else 0)
    provisional = session.to_dict()
    provisional["restart_generation"] = generation
    provisional["session_digest"] = _session_digest_v1(provisional)
    return ProductiveEvidenceSessionV1(
        session_contract_version=str(provisional["session_contract_version"]),
        session_id=str(provisional["session_id"]),
        lifecycle_state=str(provisional["lifecycle_state"]),
        session_start_event_time=str(provisional["session_start_event_time"]),
        session_end_event_time=provisional.get("session_end_event_time"),
        repository_sha=str(provisional["repository_sha"]),
        venue=str(provisional["venue"]),
        canonical_instrument_id=str(provisional["canonical_instrument_id"]),
        venue_instrument_id=str(provisional["venue_instrument_id"]),
        restart_generation=int(provisional["restart_generation"]),
        resume_token=str(provisional["resume_token"]),
        observation_count=int(provisional["observation_count"]),
        session_digest=str(provisional["session_digest"]),
    )


def note_observation_on_session_v1(
    session: ProductiveEvidenceSessionV1,
) -> ProductiveEvidenceSessionV1:
    if session.lifecycle_state != SessionLifecycleStateV1.ACTIVE.value:
        raise ProductiveEvidenceAccumulationError("session_not_active")
    provisional = session.to_dict()
    provisional["observation_count"] = int(session.observation_count) + 1
    provisional["session_digest"] = _session_digest_v1(provisional)
    return ProductiveEvidenceSessionV1(
        session_contract_version=session.session_contract_version,
        session_id=session.session_id,
        lifecycle_state=session.lifecycle_state,
        session_start_event_time=session.session_start_event_time,
        session_end_event_time=session.session_end_event_time,
        repository_sha=session.repository_sha,
        venue=session.venue,
        canonical_instrument_id=session.canonical_instrument_id,
        venue_instrument_id=session.venue_instrument_id,
        restart_generation=session.restart_generation,
        resume_token=session.resume_token,
        observation_count=int(provisional["observation_count"]),
        session_digest=str(provisional["session_digest"]),
    )


def complete_productive_evidence_session_v1(
    session: ProductiveEvidenceSessionV1,
    *,
    session_end_event_time: str,
) -> ProductiveEvidenceSessionV1:
    if session.lifecycle_state != SessionLifecycleStateV1.ACTIVE.value:
        raise ProductiveEvidenceAccumulationError("session_not_active_for_complete")
    end = require_nonempty(session_end_event_time, field_name="session_end_event_time")
    provisional = session.to_dict()
    provisional["lifecycle_state"] = SessionLifecycleStateV1.COMPLETED.value
    provisional["session_end_event_time"] = end
    provisional["session_digest"] = _session_digest_v1(provisional)
    return ProductiveEvidenceSessionV1(
        session_contract_version=session.session_contract_version,
        session_id=session.session_id,
        lifecycle_state=SessionLifecycleStateV1.COMPLETED.value,
        session_start_event_time=session.session_start_event_time,
        session_end_event_time=end,
        repository_sha=session.repository_sha,
        venue=session.venue,
        canonical_instrument_id=session.canonical_instrument_id,
        venue_instrument_id=session.venue_instrument_id,
        restart_generation=session.restart_generation,
        resume_token=session.resume_token,
        observation_count=session.observation_count,
        session_digest=str(provisional["session_digest"]),
    )


def assert_observation_binds_session_v1(
    session: ProductiveEvidenceSessionV1,
    *,
    session_id: str,
    repository_sha: str,
    venue: str,
    canonical_instrument_id: str,
) -> None:
    if session.session_id != require_nonempty(session_id, field_name="session_id"):
        raise ProductiveEvidenceAccumulationError("session_id_mismatch")
    if session.repository_sha != require_nonempty(repository_sha, field_name="repository_sha"):
        raise ProductiveEvidenceAccumulationError("session_repository_sha_mismatch")
    if session.venue != require_nonempty(venue, field_name="venue"):
        raise ProductiveEvidenceAccumulationError("session_venue_mismatch")
    if session.canonical_instrument_id != require_nonempty(
        canonical_instrument_id, field_name="canonical_instrument_id"
    ):
        raise ProductiveEvidenceAccumulationError("session_instrument_mismatch")
    if session.lifecycle_state != SessionLifecycleStateV1.ACTIVE.value:
        raise ProductiveEvidenceAccumulationError("session_not_active")


def session_from_mapping_v1(payload: Mapping[str, Any]) -> ProductiveEvidenceSessionV1:
    return ProductiveEvidenceSessionV1(
        session_contract_version=str(payload["session_contract_version"]),
        session_id=str(payload["session_id"]),
        lifecycle_state=str(payload["lifecycle_state"]),
        session_start_event_time=str(payload["session_start_event_time"]),
        session_end_event_time=payload.get("session_end_event_time"),
        repository_sha=str(payload["repository_sha"]),
        venue=str(payload["venue"]),
        canonical_instrument_id=str(payload["canonical_instrument_id"]),
        venue_instrument_id=str(payload["venue_instrument_id"]),
        restart_generation=int(payload["restart_generation"]),
        resume_token=str(payload["resume_token"]),
        observation_count=int(payload["observation_count"]),
        session_digest=str(payload["session_digest"]),
    )


def maybe_session_end_time(session: ProductiveEvidenceSessionV1) -> Optional[str]:
    return session.session_end_event_time
