"""Versioned execution baseline for CURRENT productive actual-venue POST slice.

Records a merge-stable **recorded** baseline SHA for API/decision alignment while
binding live execution identity to trusted ``origin/main`` plus fail-closed
protected-surface drift checks (PL-TF-002 pattern; mirrors 29P chain contract).

A recorded pin update alone must not require ``live origin/main == pin``: that
equality would self-invalidate on every squash merge that changes the pin file.
Unexpected POST-slice code drift is blocked via ``git diff origin/main`` on
protected paths instead.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    CurrentProductive29PChainBaselineError,
    CurrentProductive29PRuntimeIntegrityBackendV1,
    GitCurrentProductive29PRuntimeIntegrityBackendV1,
)

if TYPE_CHECKING:
    from pathlib import Path

# Post-#6946 PRE-LIVE fresh-root isolation merge (recorded rebind; live integrity separate).
EXPECTED_BASELINE_ORIGIN_MAIN_SHA = "fca07afa1fa74a94cdecde3876c9c30ad79ba828"
PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA = "1e859eaa79f48308cf7037656c6465191ed9993b"
BASELINE_AUTHORITY_CLASS = (
    "VERSIONED_POST_SLICE_RECORDED_BASELINE_WITH_LIVE_INTEGRITY_AND_PROTECTED_SURFACE_DRIFT_GATE"
)

PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS: tuple[str, ...] = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_actual_venue_post_baseline_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_actual_venue_post_owner_go_durable_consume_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/envelope_bound_external_effect_send_seam_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/external_effect_permit_durable_consume_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/gated_productive_wire_transport_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/full_core_productive_http_post_transport_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py",
    "src/governance/current_productive_real_venue_post_admission_v1.py",
    "src/governance/current_productive_actual_venue_post_admission_policy_v1.py",
)


class CurrentProductiveActualVenuePostBaselineError(RuntimeError):
    """Fail-closed actual-venue POST baseline violation."""


def assert_declared_baseline_matches_slice_pin_v1(
    *, declared_baseline_origin_main_sha: str
) -> None:
    declared = str(declared_baseline_origin_main_sha or "").strip().lower()
    expected = EXPECTED_BASELINE_ORIGIN_MAIN_SHA.lower()
    if declared != expected:
        raise CurrentProductiveActualVenuePostBaselineError("BASELINE_SHA_MISMATCH")


def resolve_and_assert_live_post_execution_baseline_v1(
    *,
    declared_baseline_origin_main_sha: str,
    integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
    repo_root: Path | None = None,
    verify_protected_surfaces: bool = True,
) -> str:
    """Validate recorded pin alignment, live origin/main, HEAD sync, and POST-slice drift."""

    assert_declared_baseline_matches_slice_pin_v1(
        declared_baseline_origin_main_sha=declared_baseline_origin_main_sha
    )
    backend = integrity_backend
    if backend is None:
        from pathlib import Path as _Path

        root = repo_root or _Path(__file__).resolve().parents[3]
        backend = GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=root)
    live = str(backend.resolve_origin_main_sha_v1() or "").strip().lower()
    head = str(backend.resolve_head_sha_v1() or "").strip().lower()
    if head != live:
        raise CurrentProductiveActualVenuePostBaselineError(
            "HEAD_NOT_SYNCHRONIZED_WITH_ORIGIN_MAIN"
        )
    if verify_protected_surfaces:
        drift = backend.diff_origin_main_for_paths_v1(
            PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS
        )
        if drift.strip():
            raise CurrentProductiveActualVenuePostBaselineError(
                "PROTECTED_POST_SLICE_SURFACE_DRIFT"
            )
    return live


__all__ = [
    "BASELINE_AUTHORITY_CLASS",
    "EXPECTED_BASELINE_ORIGIN_MAIN_SHA",
    "PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA",
    "PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS",
    "CurrentProductiveActualVenuePostBaselineError",
    "assert_declared_baseline_matches_slice_pin_v1",
    "resolve_and_assert_live_post_execution_baseline_v1",
]
