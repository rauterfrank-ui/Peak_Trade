"""Forced wiring fixture — structurally isolated from wallclock runtime."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CAPABILITY_ID,
    FORCED_FIXTURE_WALLCLOCK_REACHABLE,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.evidence_streams_v2 import (
    persist_hardening_evidence_bundle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
    verify_full_economic_reconstruction_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotentPortfolioV2,
)

# Marker used by structural wallclock reachability tests.
FORCED_WIRING_FIXTURE_MODULE = (
    "src.ops.wallclock_full_canonical_decision_to_simulated_economics_"
    "runtime_bridge_hardening_v2.forced_wiring_fixture_v2"
)


def run_forced_wiring_fixture_v2(*, evidence_root: Path) -> dict[str, Any]:
    """Deterministic actionable BUY path with fee>0 and observable slippage.

    Never consumes productive authorization. Evidence is excluded from economic metrics.
    """
    if FORCED_FIXTURE_WALLCLOCK_REACHABLE:
        raise RuntimeError("FORCED_FIXTURE_MUST_NOT_BE_WALLCLOCK_REACHABLE")

    params = PortfolioEconomicsModelParamsV1(
        fee_rate_bps=Decimal("2.0"),
        slippage_bps=Decimal("1.0"),
        initial_equity=Decimal("100000"),
    )
    state = HardenedBridgeSessionStateV2(
        portfolio=IdempotentPortfolioV2.from_params(params),
    )
    # Warmup mids then forced actionable.
    mids = [3500.0, 3510.0, 3520.0, 3550.0]
    cycles: list[dict[str, Any]] = []
    session_id = "forced-wiring-fixture-not-a-productive-session"
    for i, mid in enumerate(mids[:-1]):
        cycles.append(
            run_hardened_bridge_cycle_v2(
                state,
                mid_price=mid,
                event_ts_unix=1_700_000_100.0 + i,
                session_id=session_id,
            )
        )
    forced = run_hardened_bridge_cycle_v2(
        state,
        mid_price=mids[-1],
        event_ts_unix=1_700_000_100.0 + len(mids),
        session_id=session_id,
        forced_actionable={"intended_side": "BUY", "intended_quantity": "0.14"},
    )
    cycles.append(forced)
    if forced.get("fill") is None:
        raise RuntimeError("FORCED_WIRING_FILL_REQUIRED")
    fee = Decimal(str(forced["fill"].get("fee") or forced["fill"].get("fee_amount") or "0"))
    slip = Decimal(
        str(forced["fill"].get("slippage_cost") or forced["fill"].get("slippage_amount") or "0")
    )
    if fee <= 0:
        raise RuntimeError("FORCED_WIRING_FEE_MUST_BE_POSITIVE")
    if slip <= 0:
        raise RuntimeError("FORCED_WIRING_SLIPPAGE_MUST_BE_POSITIVE")

    verification = verify_full_economic_reconstruction_v2(
        cycle_ledger=cycles,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
        economic_metrics={"excluded": True},
        forced_fixture_excluded=True,
    )
    persist_hardening_evidence_bundle_v2(
        evidence_root=evidence_root,
        session_id=session_id,
        cycles=cycles,
        fill_ledger=state.fill_ledger,
        portfolio_snapshot=state.portfolio.snapshot(),
        economic_metrics=state.portfolio.economic_metrics().to_dict(),
        verification=verification.to_dict(),
        authorization_status="NOT_APPLICABLE",
        mode="forced_wiring_fixture",
        exclude_from_economic_metrics=True,
    )
    return {
        "ok": verification.ok,
        "capability_id": CAPABILITY_ID,
        "forced_wiring_fixture_pass": verification.ok and fee > 0 and slip > 0,
        "forced_fixture_wallclock_reachable": FORCED_FIXTURE_WALLCLOCK_REACHABLE,
        "forced_fixture_economic_metrics_excluded": True,
        "fee": str(fee),
        "slippage": str(slip),
        "fill_id": forced.get("fill_id"),
        "verification": verification.to_dict(),
        "productive_authorization": False,
    }
