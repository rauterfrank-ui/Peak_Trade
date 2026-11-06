"""Ephemeral NETWORK_SESSION_GO — parameter-only, never from env/config/persistence."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS,
    NETWORK_SESSION_GO_DEFAULT,
    NETWORK_SESSION_GO_PERSISTED,
)


def reject_network_session_go_env_fallback_v1(
    environ: Mapping[str, str] | None = None,
) -> list[str]:
    blockers: list[str] = []
    if environ is None:
        return blockers
    for key in FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS:
        raw = environ.get(key)
        if raw is None:
            continue
        val = str(raw).strip().lower()
        if val in {"1", "true", "yes", "on"}:
            blockers.append(f"NETWORK_SESSION_GO_ENV_FORBIDDEN:{key}")
    return blockers


def bind_ephemeral_network_session_go_v1(
    *,
    network_session_go: bool | None = None,
    environ: Mapping[str, str] | None = None,
    config_network_session_go: bool | None = None,
    persisted_network_session_go: bool | None = None,
) -> dict[str, Any]:
    """Bind ephemeral GO. Only explicit parameter may be true; default false."""
    blockers = reject_network_session_go_env_fallback_v1(environ)
    if config_network_session_go is True:
        blockers.append("NETWORK_SESSION_GO_FROM_CONFIG_FORBIDDEN")
    if persisted_network_session_go is True:
        blockers.append("NETWORK_SESSION_GO_FROM_PERSISTENCE_FORBIDDEN")
    if NETWORK_SESSION_GO_PERSISTED:
        blockers.append("NETWORK_SESSION_GO_MUST_NOT_BE_PERSISTED_CONSTANT")

    explicit = (
        bool(network_session_go) if network_session_go is not None else NETWORK_SESSION_GO_DEFAULT
    )
    if network_session_go is None:
        explicit = False

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "network_session_go": bool(explicit) and not blockers,
        "network_session_go_default_false": NETWORK_SESSION_GO_DEFAULT is False,
        "network_session_go_persisted": False,
        "network_session_go_from_env": False,
        "network_session_go_from_config": False,
        "ephemeral": True,
        "notes": [
            "EPHEMERAL_NETWORK_SESSION_GO_PARAMETER_ONLY=true",
            "ENV_CONFIG_PERSISTENCE_CANNOT_ENABLE=true",
            f"EXPLICIT_PARAMETER={bool(network_session_go) if network_session_go is not None else False}",
        ],
    }
