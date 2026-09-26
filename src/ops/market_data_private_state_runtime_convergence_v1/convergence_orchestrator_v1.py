"""WP-C dual-plane convergence orchestrator (offline/test harness; no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.market_data_private_state_runtime_convergence_v1.consumer_census_v1 import (
    census_summary_v1,
    competing_productive_runtime_truths_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.effective_authorization_readmodel_v1 import (
    ObservationCapabilitySignalsV1,
    build_effective_authorization_readmodel_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.private_handoff_v1 import (
    converged_private_surfaces_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    converged_public_surfaces_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.restart_reconciliation_closure_v1 import (
    run_private_restart_reconciliation_closure_v1,
    run_public_restart_reconciliation_closure_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.safety_boundary_v1 import (
    wp_c_safety_attestation_v1,
)


def run_wp_c_dual_plane_convergence_cycle_v1(
    *,
    public_store_root: Path,
    private_store_root: Path,
    venue_native_id: str,
    canonical_instrument_id: str,
    public_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    private_rest_fetch: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    captured_at: str,
    observation: Optional[ObservationCapabilitySignalsV1] = None,
) -> dict[str, Any]:
    public_closure = run_public_restart_reconciliation_closure_v1(
        store_root=public_store_root,
        venue_native_id=venue_native_id,
        canonical_instrument_id=canonical_instrument_id,
        rest_fetch_json=public_rest_fetch,
        captured_at=captured_at,
    )
    private_closure = run_private_restart_reconciliation_closure_v1(
        store_root=private_store_root,
        rest_fetch_json=private_rest_fetch,
        captured_at=captured_at,
    )

    public_converged = converged_public_surfaces_v1(public_closure["surfaces"])
    private_converged = converged_private_surfaces_v1(
        private_closure["surfaces"],
        trusted_current=private_closure["trusted_current"],
        reconciliation_required=False,
    )

    obs = observation or ObservationCapabilitySignalsV1(
        rest_get_success=True,
        public_ws_connected=False,
        private_ws_connected=False,
    )
    effective_auth = build_effective_authorization_readmodel_v1(observation=obs)
    attestation = wp_c_safety_attestation_v1()

    return {
        "schema_name": "wp_c_dual_plane_convergence_cycle.v1",
        "census_summary": census_summary_v1(),
        "competing_productive_runtime_truths": competing_productive_runtime_truths_v1(),
        "public_closure": public_closure,
        "private_closure": private_closure,
        "converged_public": public_converged,
        "converged_private": private_converged,
        "effective_authorization": effective_auth,
        "safety_attestation": attestation,
    }
