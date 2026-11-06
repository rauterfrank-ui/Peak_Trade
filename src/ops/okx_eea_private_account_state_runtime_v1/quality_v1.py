"""WP-B quality/freshness vocabulary (no global private-state TTL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    FRESH_PRETRADE_FRESHNESS_POLICY,
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    PRIVATE_STATE_GLOBAL_TTL_SECONDS,
    QUALITY_CURRENT,
    QUALITY_INVALID,
    QUALITY_RECONCILIATION_REQUIRED,
    QUALITY_STALE,
    QUALITY_UNKNOWN,
)


class PrivateQualityError(ValueError):
    pass


@dataclass(frozen=True)
class QualityVerdictV1:
    quality: str
    publishable: bool
    fresh_pretrade_substitute: bool
    running_equity_mint: bool


def assert_no_global_private_state_ttl_v1() -> None:
    if PRIVATE_STATE_GLOBAL_TTL_SECONDS is not None:
        raise PrivateQualityError("GLOBAL_PRIVATE_STATE_TTL_FORBIDDEN")


def quality_from_ws_health_v1(*, connected: bool, auth_ok: bool) -> str:
    if not connected:
        return QUALITY_STALE
    if not auth_ok:
        return QUALITY_INVALID
    return QUALITY_CURRENT


def quality_after_disconnect_v1() -> str:
    return QUALITY_RECONCILIATION_REQUIRED


def quality_for_fresh_pretrade_surface_v1(*, cached_only: bool) -> QualityVerdictV1:
    return QualityVerdictV1(
        quality=QUALITY_UNKNOWN if cached_only else QUALITY_CURRENT,
        publishable=not cached_only,
        fresh_pretrade_substitute=False,
        running_equity_mint=False,
    )


def quality_for_position_observation_v1(*, age_ms: int, ws_trusted: bool) -> QualityVerdictV1:
    if not ws_trusted:
        return QualityVerdictV1(
            quality=QUALITY_RECONCILIATION_REQUIRED,
            publishable=False,
            fresh_pretrade_substitute=False,
            running_equity_mint=False,
        )
    stale = age_ms > POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS
    return QualityVerdictV1(
        quality=QUALITY_STALE if stale else QUALITY_CURRENT,
        publishable=not stale,
        fresh_pretrade_substitute=False,
        running_equity_mint=False,
    )


def preserve_fresh_pretrade_policy_pin_v1() -> str:
    return FRESH_PRETRADE_FRESHNESS_POLICY


def transition_on_ambiguity_v1(current: str) -> str:
    if current == QUALITY_INVALID:
        return QUALITY_INVALID
    return QUALITY_RECONCILIATION_REQUIRED


def restored_state_quality_before_reconcile_v1() -> str:
    return QUALITY_UNKNOWN
