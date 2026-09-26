"""Deterministic restart/replay/reconciliation closure for public + private planes."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.market_data_private_state_runtime_convergence_v1.private_handoff_v1 import (
    assert_baseline_before_delta_trusted_v1,
    stale_gap_fail_closed_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    forbid_direct_transport_as_consumer_truth_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.runtime_orchestrator_v1 import (
    OkxEeaPrivateAccountStateRuntimeV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)


def run_public_restart_reconciliation_closure_v1(
    *,
    store_root: Path,
    venue_native_id: str,
    canonical_instrument_id: str,
    rest_fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    captured_at: str,
    mark_age_seconds: float = 1.0,
    bba_age_seconds: float = 1.0,
) -> dict[str, Any]:
    """durable → gap/recovery path → publish without WS consumer truth."""
    runtime = PublicMarketDataRuntimeV1(
        store_root=store_root,
        venue_native_id=venue_native_id,
        canonical_instrument_id=canonical_instrument_id,
        rest_fetch_json=rest_fetch_json,
    )
    runtime.bootstrap(captured_at=captured_at)
    forbid_direct_transport_as_consumer_truth_v1(
        consumer_id="public_restart_closure", transport_session_as_truth=False
    )
    surfaces = runtime.publish_consumer_surfaces(
        mark_age_seconds=mark_age_seconds,
        bba_age_seconds=bba_age_seconds,
        captured_at=captured_at,
    )
    return {
        "phase": "public_restart_reconciliation_closure",
        "lifecycle_events": list(runtime.lifecycle_events),
        "historical_live_ws_required": surfaces.get("research_optimizer", {}).get(
            "live_ws_required", True
        ),
        "surfaces": surfaces,
    }


def run_private_restart_reconciliation_closure_v1(
    *,
    store_root: Path,
    rest_fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    captured_at: str,
    ws_delta_applied: bool = False,
    quality_state: Optional[str] = None,
) -> dict[str, Any]:
    """durable restore → REST baseline → reconcile → trusted boundary before deltas."""
    runtime = OkxEeaPrivateAccountStateRuntimeV1(
        store_root=store_root,
        rest_fetch_json=rest_fetch_json,
    )
    runtime.restore_durable_state_v1()
    baseline = runtime.run_rest_baseline_v1(captured_at=captured_at, recovery=True)
    snap = baseline["snapshot"]
    reconciled = runtime.reconcile_after_restore_or_ws_v1(
        reconciliation_id="wp_c_restart_closure",
        rest_snapshot=snap,
        restored_from_durable=True,
    )
    baseline_established = True
    assert_baseline_before_delta_trusted_v1(
        baseline_established=baseline_established,
        ws_delta_applied=ws_delta_applied,
    )
    stale_gap_fail_closed_v1(
        trusted_current=runtime.trusted_current,
        quality_state=quality_state,
    )
    surfaces = runtime.publish_consumer_surfaces_v1()
    return {
        "phase": "private_restart_reconciliation_closure",
        "baseline_established": baseline_established,
        "trusted_current": runtime.trusted_current,
        "lifecycle_events": list(runtime.lifecycle_events),
        "reconciled_quality": reconciled.get("quality", {}),
        "surfaces": surfaces,
    }
