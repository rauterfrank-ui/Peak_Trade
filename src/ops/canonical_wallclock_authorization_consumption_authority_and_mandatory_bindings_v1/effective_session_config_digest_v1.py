"""Deterministic effective session-config digest (single authority)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    EFFECTIVE_SESSION_CONFIG_DIGEST_VERSION,
    MANDATORY_SAFETY_BOUNDARIES,
    REQUIRED_SESSION_DURATION_SECONDS,
    TARGET_RUNTIME_CAPABILITY,
)


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def normalize_effective_session_config_v1(
    *,
    capability: str = TARGET_RUNTIME_CAPABILITY,
    session_duration_seconds: int = REQUIRED_SESSION_DURATION_SECONDS,
    safety_boundaries: Optional[Mapping[str, bool]] = None,
    runtime_overrides: Optional[Mapping[str, Any]] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    env_overrides: Optional[Mapping[str, Any]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    config_files: Optional[Mapping[str, str]] = None,
    venue: str = AUTHORIZED_VENUE,
    network_scope: str = AUTHORIZED_NETWORK_SCOPE,
) -> dict[str, Any]:
    """Build the full effective config material. Order of merge is versioned and explicit."""
    material: dict[str, Any] = {
        "digest_version": EFFECTIVE_SESSION_CONFIG_DIGEST_VERSION,
        "capability": str(capability),
        "session_duration_seconds": int(session_duration_seconds),
        "venue": str(venue),
        "network_scope": str(network_scope),
        "safety_boundaries": {
            str(k): bool(v)
            for k, v in sorted((safety_boundaries or MANDATORY_SAFETY_BOUNDARIES).items())
        },
        "defaults": {str(k): v for k, v in sorted((defaults or {}).items())},
        "env_overrides": {str(k): v for k, v in sorted((env_overrides or {}).items())},
        "cli_overrides": {str(k): v for k, v in sorted((cli_overrides or {}).items())},
        "runtime_overrides": {str(k): v for k, v in sorted((runtime_overrides or {}).items())},
        "config_files": {str(k): str(v) for k, v in sorted((config_files or {}).items())},
    }
    return material


def compute_effective_session_config_digest_v1(
    *,
    capability: str = TARGET_RUNTIME_CAPABILITY,
    session_duration_seconds: int = REQUIRED_SESSION_DURATION_SECONDS,
    safety_boundaries: Optional[Mapping[str, bool]] = None,
    runtime_overrides: Optional[Mapping[str, Any]] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    env_overrides: Optional[Mapping[str, Any]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    config_files: Optional[Mapping[str, str]] = None,
    venue: str = AUTHORIZED_VENUE,
    network_scope: str = AUTHORIZED_NETWORK_SCOPE,
) -> str:
    material = normalize_effective_session_config_v1(
        capability=capability,
        session_duration_seconds=session_duration_seconds,
        safety_boundaries=safety_boundaries,
        runtime_overrides=runtime_overrides,
        cli_overrides=cli_overrides,
        env_overrides=env_overrides,
        defaults=defaults,
        config_files=config_files,
        venue=venue,
        network_scope=network_scope,
    )
    return hashlib.sha256(_canonical_dumps(material).encode("utf-8")).hexdigest()


def assert_session_config_digest_match_v1(
    *,
    authorization_digest: str,
    live_digest: str,
) -> list[str]:
    if authorization_digest != live_digest:
        return ["CONFIG_DRIFT", "SESSION_CONFIG_DIGEST_MISMATCH"]
    return []
