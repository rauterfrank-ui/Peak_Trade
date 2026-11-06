"""Ephemeral NETWORK_SESSION_GO — Step-5 pattern; Step-7 Real-TTY campaign keys."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    FORBIDDEN_NETWORK_SESSION_GO_ENV_KEYS,
    NETWORK_SESSION_GO_DEFAULT,
    NETWORK_SESSION_GO_PERSISTED,
    STEP5_NETWORK_SESSION_GO_PATTERN_OWNER,
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

    if network_session_go is None:
        explicit = False
    else:
        explicit = bool(network_session_go)

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "network_session_go": bool(explicit) and not blockers,
        "network_session_go_default_false": NETWORK_SESSION_GO_DEFAULT is False,
        "network_session_go_persisted": False,
        "network_session_go_from_env": False,
        "network_session_go_from_config": False,
        "ephemeral": True,
        "pattern_owner": STEP5_NETWORK_SESSION_GO_PATTERN_OWNER,
        "notes": [
            "EPHEMERAL_NETWORK_SESSION_GO_PARAMETER_ONLY=true",
            "ENV_CONFIG_PERSISTENCE_CANNOT_ENABLE=true",
            "REUSES_STEP5_NETWORK_SESSION_GO_PATTERN=true",
            f"EXPLICIT_PARAMETER={bool(network_session_go) if network_session_go is not None else False}",
        ],
    }
