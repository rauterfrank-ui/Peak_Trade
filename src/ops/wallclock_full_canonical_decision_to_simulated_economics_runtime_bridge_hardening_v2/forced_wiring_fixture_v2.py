"""Forced wiring fixture — structurally isolated from wallclock runtime."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.constants_v1 import (
    BRIDGED_CAPABILITY,
    PROBE_TYPE_FORCED_FIXTURE,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.probe_fixture_sha_verifier_v1 import (
    verify_probe_fixture_repository_sha_binding_v1,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.repository_sha_source_v1 import (
    assert_valid_repository_sha_v1,
    resolve_repository_sha_from_git_head_v1,
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


def run_forced_wiring_fixture_v2(
    *,
    evidence_root: Path,
    repo_root: Optional[Path] = None,
    repository_sha: Optional[str] = None,
) -> dict[str, Any]:
    """Deterministic actionable BUY path with fee>0 and observable slippage.

    Never consumes productive authorization. Evidence is excluded from economic metrics.
    """
    if FORCED_FIXTURE_WALLCLOCK_REACHABLE:
        raise RuntimeError("FORCED_FIXTURE_MUST_NOT_BE_WALLCLOCK_REACHABLE")

    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    if repository_sha is None:
        expected_sha = resolve_repository_sha_from_git_head_v1(repo_root=root)
    else:
        expected_sha = assert_valid_repository_sha_v1(repository_sha, field="repository_sha")

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
        repository_sha=expected_sha,
        probe_type=PROBE_TYPE_FORCED_FIXTURE,
    )
    sha_binding = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=Path(evidence_root),
        expected_repository_sha=expected_sha,
        expected_probe_type=PROBE_TYPE_FORCED_FIXTURE,
    )
    pass_ok = bool(
        verification.ok and fee > 0 and slip > 0 and sha_binding.ok and sha_binding.sha_bound
    )
    summary = {
        "ok": pass_ok,
        "capability": BRIDGED_CAPABILITY,
        "capability_id": CAPABILITY_ID,
        "probe_type": PROBE_TYPE_FORCED_FIXTURE,
        "repository_sha": expected_sha,
        "forced_wiring_fixture_pass": pass_ok,
        "forced_wiring_fixture_sha_bound": sha_binding.sha_bound,
        "forced_wiring_fixture_repository_sha": sha_binding.repository_sha,
        "forced_wiring_fixture_expected_sha": sha_binding.expected_sha,
        "forced_fixture_wallclock_reachable": FORCED_FIXTURE_WALLCLOCK_REACHABLE,
        "forced_fixture_economic_metrics_excluded": True,
        "forced_fixture_can_consume_productive_authorization": False,
        "fee": str(fee),
        "slippage": str(slip),
        "fill_id": forced.get("fill_id"),
        "verification": verification.to_dict(),
        "sha_binding": sha_binding.to_dict(),
        "productive_authorization": False,
    }
    Path(evidence_root).mkdir(parents=True, exist_ok=True)
    (Path(evidence_root) / "probe_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sha_binding = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=Path(evidence_root),
        expected_repository_sha=expected_sha,
        expected_probe_type=PROBE_TYPE_FORCED_FIXTURE,
    )
    summary["sha_binding"] = sha_binding.to_dict()
    summary["ok"] = bool(summary["ok"] and sha_binding.ok and sha_binding.sha_bound)
    summary["forced_wiring_fixture_pass"] = summary["ok"]
    summary["forced_wiring_fixture_sha_bound"] = sha_binding.sha_bound
    (Path(evidence_root) / "probe_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary
