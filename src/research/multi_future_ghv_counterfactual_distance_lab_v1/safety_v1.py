from __future__ import annotations

from dataclasses import dataclass

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)


@dataclass(frozen=True)
class LabSafetySnapshotV1:
    post_allowed: bool
    real_venue_post_allowed: bool
    external_effect_authorized: bool
    live_enabled: bool
    live_armed: bool
    real_post_count: int
    safety_abort: bool


def assert_lab_safety_v1(*, real_post_count: int = 0) -> LabSafetySnapshotV1:
    violations: list[str] = []
    if POST_ALLOWED:
        violations.append("POST_ALLOWED")
    if REAL_VENUE_POST_ALLOWED:
        violations.append("REAL_VENUE_POST_ALLOWED")
    if EXTERNAL_EFFECT_AUTHORIZED:
        violations.append("EXTERNAL_EFFECT_AUTHORIZED")
    if real_post_count != 0:
        violations.append(f"REAL_POST_COUNT={real_post_count}")
    abort = bool(violations)
    if abort:
        raise RuntimeError(f"SAFETY_ABORT=true violations={violations}")
    return LabSafetySnapshotV1(
        post_allowed=False,
        real_venue_post_allowed=False,
        external_effect_authorized=False,
        live_enabled=False,
        live_armed=False,
        # Lab runtime: no live arm path entered; standing LIVE_* predicates not consulted.
        real_post_count=real_post_count,
        safety_abort=False,
    )
