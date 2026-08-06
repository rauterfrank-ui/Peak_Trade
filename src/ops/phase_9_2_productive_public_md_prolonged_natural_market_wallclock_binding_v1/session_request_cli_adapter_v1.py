"""Session-request CLI adapter for Step-5 prolonged natural-market binding.

Assembles a canonical session_request dict for later governed execution.
Does not mint authorization, consume tokens, or open network sockets.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    DEFAULT_WALLCLOCK_DURATION_SECONDS,
    GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
    GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE,
    MAX_WALLCLOCK_DURATION_SECONDS,
    MIN_WALLCLOCK_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
    RUNTIME_SESSION_ID,
    SESSION_LADDER_STEP,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (
    planned_max_cycles_v1,
    validate_planned_duration_v1,
)


class SessionRequestAdapterError(ValueError):
    """Fail-closed session-request adapter error."""


def build_step5_session_request_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    planned_session_duration_seconds: int = DEFAULT_WALLCLOCK_DURATION_SECONDS,
    authorization_id: str = "",
    authorization_digest: str = "",
    confirm_token_binding_sha256: str = "",
    predecessor_step4_evidence_ref: str = "",
    minimum_interval_seconds: float = 2.0,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    gaps = validate_planned_duration_v1(int(planned_session_duration_seconds))
    if gaps:
        raise SessionRequestAdapterError("SESSION_REQUEST_DURATION_INVALID:" + ",".join(gaps))
    max_cycles = planned_max_cycles_v1(
        int(planned_session_duration_seconds), float(minimum_interval_seconds)
    )
    request = {
        "schema_version": "phase_9_2_prolonged_natural_market_session_request.v1",
        "capability_id": CAPABILITY_ID,
        "session_id": TARGET_SESSION_ID,
        "runtime_session_id": RUNTIME_SESSION_ID,
        "confirmation_session_id": CONFIRMATION_SESSION_ID,
        "session_ladder_step": SESSION_LADDER_STEP,
        "session_scope": SESSION_SCOPE,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "expected_repository_sha": str(expected_repository_sha).strip(),
        "expected_config_digest": str(expected_config_digest).strip(),
        "entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "min_session_duration_seconds": MIN_WALLCLOCK_DURATION_SECONDS,
        "planned_session_duration_seconds": int(planned_session_duration_seconds),
        "max_session_duration_seconds": MAX_WALLCLOCK_DURATION_SECONDS,
        "clock_authority_duration": "MONOTONIC",
        "max_cycles": max_cycles,
        "max_requests_per_session": max_cycles,
        "minimum_interval_seconds": float(minimum_interval_seconds),
        "network_scope": GOVERNED_PUBLIC_MD_NETWORK_SCOPE,
        "session_execution_scope": GOVERNED_PUBLIC_MD_SESSION_EXECUTION_SCOPE,
        "artifact_network_scope": PRODUCTIVE_V2_ARTIFACT_NETWORK_SCOPE,
        "http_get_only": True,
        "public_md_only": True,
        "authorization_id": str(authorization_id or "").strip(),
        "authorization_digest": str(authorization_digest or "").strip(),
        "confirm_token_binding_sha256": str(confirm_token_binding_sha256 or "").strip(),
        "predecessor_step4_evidence_ref": str(predecessor_step4_evidence_ref or "").strip(),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "notes": [
            "ADAPTER_ASSEMBLES_REQUEST_ONLY=true",
            "NO_AUTH_ISSUANCE=true",
            "NO_TOKEN_CONSUMPTION=true",
            "NO_NETWORK_SESSION=true",
        ],
    }
    if extra:
        for key, value in extra.items():
            if key in request:
                raise SessionRequestAdapterError(f"SESSION_REQUEST_EXTRA_OVERWRITE_FORBIDDEN:{key}")
            request[key] = value
    request["session_request_digest"] = sha256_canonical_v1(request)
    return request


def bind_session_request_to_runner_kwargs_v1(session_request: Mapping[str, Any]) -> dict[str, Any]:
    """Map session_request fields to wallclock runner kwargs (no invoke)."""
    required = (
        "expected_repository_sha",
        "expected_config_digest",
        "session_id",
        "planned_session_duration_seconds",
        "canonical_instrument_id",
    )
    missing = [k for k in required if not session_request.get(k)]
    if missing:
        raise SessionRequestAdapterError("SESSION_REQUEST_INCOMPLETE:" + ",".join(missing))
    return {
        "repository_sha": session_request["expected_repository_sha"],
        "config_digest": session_request["expected_config_digest"],
        "session_id": session_request["session_id"],
        "runtime_session_id": session_request.get("runtime_session_id", RUNTIME_SESSION_ID),
        "confirmation_session_id": session_request.get(
            "confirmation_session_id", CONFIRMATION_SESSION_ID
        ),
        "instrument_id": session_request["canonical_instrument_id"],
        "duration_seconds": int(session_request["planned_session_duration_seconds"]),
        "max_cycles": int(session_request.get("max_cycles") or 0),
        "network_session_allowed": False,
        "invoke_runner": False,
        "notes": [
            "RUNNER_KWARGS_BOUND_WITHOUT_INVOKE=true",
            "NETWORK_SESSION_ALLOWED_DEFAULT_FALSE=true",
        ],
    }
