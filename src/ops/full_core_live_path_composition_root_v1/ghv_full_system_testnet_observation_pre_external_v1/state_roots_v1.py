"""Isolated state roots for GHV Full-System Testnet Observation campaigns."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.constants_v1 import (
    FORBIDDEN_CROSS_ENV_ROOT_MARKERS,
    STATE_ROOT_MARKER,
)


class GhvTestnetStateIsolationError(RuntimeError):
    """Fail-closed cross-environment state reuse violation."""


@dataclass(frozen=True)
class GhvTestnetObservationStateRootsV1:
    evidence_root: Path
    lane_state_root: Path
    productivity_root: Path
    account_observation_state_root: Path
    pending_outcome_state_root: Path
    o4_state_root: Path


def derive_ghv_testnet_observation_state_roots_v1(
    base_root: Path,
) -> GhvTestnetObservationStateRootsV1:
    root = Path(base_root).resolve()
    marker = STATE_ROOT_MARKER
    evidence = root / marker / "evidence"
    lane = root / marker / "lane_state"
    productivity = root / marker / "productivity"
    account_obs = root / marker / "account_observation_state"
    pending = lane / "LANE_1" / "natural_enter_pending_outcome_v1"
    o4 = pending / "natural_enter_pending_outcome_o4_v1"
    for path in (evidence, lane, productivity, account_obs, pending, o4):
        path.mkdir(parents=True, exist_ok=True)
    return GhvTestnetObservationStateRootsV1(
        evidence_root=evidence,
        lane_state_root=lane,
        productivity_root=productivity,
        account_observation_state_root=account_obs,
        pending_outcome_state_root=pending,
        o4_state_root=o4,
    )


def assert_ghv_testnet_observation_state_roots_isolated_v1(
    *,
    evidence_root: Path,
    lane_state_root: Path,
    productivity_root: Path,
) -> dict[str, str]:
    paths = (
        Path(evidence_root),
        Path(lane_state_root),
        Path(productivity_root),
    )
    joined = " ".join(str(p).lower() for p in paths)
    if STATE_ROOT_MARKER not in joined:
        raise GhvTestnetStateIsolationError("TESTNET_STATE_ROOT_MARKER_REQUIRED")
    for marker in FORBIDDEN_CROSS_ENV_ROOT_MARKERS:
        if marker in joined:
            raise GhvTestnetStateIsolationError("CROSS_ENV_STATE_REUSE_REJECTED")
    return {
        "STATE_ROOT_MARKER": STATE_ROOT_MARKER,
        "CROSS_ENV_STATE_REUSE": "false",
        "TESTNET_STATE_ISOLATION": "true",
    }
