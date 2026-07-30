"""Canonical strategy probe — real decision graph, HOLD allowed."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    CAPABILITY_ID,
    DECISION_AUTHORITY_OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.evidence_streams_v2 import (
    persist_hardening_evidence_bundle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.full_economic_reconstruction_verifier_v2 import (
    verify_full_economic_reconstruction_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    run_hardened_bridge_cycles_from_mids_v2,
)


def run_canonical_strategy_probe_v2(*, evidence_root: Path) -> dict[str, Any]:
    """Offline probe using the real Feature→Regime→MasterV2→DoublePlay→Risk→Intent graph.

    Does not force BUY/SELL. Legitimate HOLD is allowed and must carry full provenance.
    """
    # Mild path that typically yields HOLD/observe rather than forced entries.
    mids = [3500.0, 3500.1, 3500.05, 3500.08, 3500.02, 3500.04]
    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        mids,
        session_id="canonical-strategy-probe",
        start_ts_unix=1_700_000_200.0,
    )
    holds = [c for c in cycles if (c.get("intended_action") or {}).get("intended_side") == "HOLD"]
    if not holds:
        # Still acceptable if strategy acted; require provenance either way.
        sample = cycles[-1]
    else:
        sample = holds[-1]
    action = sample.get("intended_action") or {}
    provenance_ok = all(
        [
            bool(sample.get("decision_id")),
            bool(sample.get("risk_decision_id")),
            bool(sample.get("intent_id")),
            bool(sample.get("feature_digest")),
            bool(sample.get("regime_digest")),
            bool(action.get("decision_producer") == DECISION_AUTHORITY_OWNER),
            bool(sample.get("safety_evaluation")),
            sample.get("forced_wiring") is False,
        ]
    )
    verification = verify_full_economic_reconstruction_v2(
        cycle_ledger=cycles,
        fill_ledger=state.fill_ledger,
        final_portfolio_snapshot=state.portfolio.snapshot(),
        economic_metrics=state.portfolio.economic_metrics().to_dict(),
    )
    persist_hardening_evidence_bundle_v2(
        evidence_root=evidence_root,
        session_id="canonical-strategy-probe",
        cycles=cycles,
        fill_ledger=state.fill_ledger,
        portfolio_snapshot=state.portfolio.snapshot(),
        economic_metrics=state.portfolio.economic_metrics().to_dict(),
        verification=verification.to_dict(),
        authorization_status="NOT_APPLICABLE",
        mode="canonical_strategy_probe",
        exclude_from_economic_metrics=False,
    )
    pass_ok = (
        provenance_ok
        and verification.ok
        and all(c.get("decision_authority_owner") == DECISION_AUTHORITY_OWNER for c in cycles)
    )
    return {
        "ok": pass_ok,
        "capability_id": CAPABILITY_ID,
        "canonical_strategy_probe_pass": pass_ok,
        "canonical_strategy_probe_uses_real_decision_graph": True,
        "canonical_strategy_probe_forced_action": False,
        "legitimate_hold_present": bool(holds),
        "hold_provenance_complete": provenance_ok,
        "cycles": len(cycles),
        "verification": verification.to_dict(),
    }
