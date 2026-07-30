"""Canonical strategy probe — real decision graph, HOLD allowed."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.constants_v1 import (
    BRIDGED_CAPABILITY,
    PROBE_TYPE_CANONICAL,
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


def run_canonical_strategy_probe_v2(
    *,
    evidence_root: Path,
    repo_root: Optional[Path] = None,
    repository_sha: Optional[str] = None,
) -> dict[str, Any]:
    """Offline probe using the real Feature→Regime→MasterV2→DoublePlay→Risk→Intent graph.

    Does not force BUY/SELL. Legitimate HOLD is allowed and must carry full provenance.
    """
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    if repository_sha is None:
        expected_sha = resolve_repository_sha_from_git_head_v1(repo_root=root)
    else:
        expected_sha = assert_valid_repository_sha_v1(repository_sha, field="repository_sha")

    # Mild path that typically yields HOLD/observe rather than forced entries.
    mids = [3500.0, 3500.1, 3500.05, 3500.08, 3500.02, 3500.04]
    state, cycles = run_hardened_bridge_cycles_from_mids_v2(
        mids,
        session_id="canonical-strategy-probe",
        start_ts_unix=1_700_000_200.0,
    )
    holds = [c for c in cycles if (c.get("intended_action") or {}).get("intended_side") == "HOLD"]
    if not holds:
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
        repository_sha=expected_sha,
        probe_type=PROBE_TYPE_CANONICAL,
    )
    sha_binding = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=Path(evidence_root),
        expected_repository_sha=expected_sha,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    pass_ok = (
        provenance_ok
        and verification.ok
        and sha_binding.ok
        and sha_binding.sha_bound
        and all(c.get("decision_authority_owner") == DECISION_AUTHORITY_OWNER for c in cycles)
    )
    summary = {
        "ok": pass_ok,
        "capability": BRIDGED_CAPABILITY,
        "capability_id": CAPABILITY_ID,
        "probe_type": PROBE_TYPE_CANONICAL,
        "repository_sha": expected_sha,
        "canonical_strategy_probe_pass": pass_ok,
        "canonical_strategy_probe_sha_bound": sha_binding.sha_bound,
        "canonical_strategy_probe_repository_sha": sha_binding.repository_sha,
        "canonical_strategy_probe_expected_sha": sha_binding.expected_sha,
        "canonical_strategy_probe_uses_real_decision_graph": True,
        "canonical_strategy_probe_forced_action": False,
        "legitimate_hold_present": bool(holds),
        "hold_provenance_complete": provenance_ok,
        "cycles": len(cycles),
        "verification": verification.to_dict(),
        "sha_binding": sha_binding.to_dict(),
    }
    Path(evidence_root).mkdir(parents=True, exist_ok=True)
    (Path(evidence_root) / "probe_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    # Re-verify after summary write so probe_summary SHA field is checked when present.
    sha_binding = verify_probe_fixture_repository_sha_binding_v1(
        evidence_root=Path(evidence_root),
        expected_repository_sha=expected_sha,
        expected_probe_type=PROBE_TYPE_CANONICAL,
    )
    summary["sha_binding"] = sha_binding.to_dict()
    summary["ok"] = bool(summary["ok"] and sha_binding.ok and sha_binding.sha_bound)
    summary["canonical_strategy_probe_pass"] = summary["ok"]
    summary["canonical_strategy_probe_sha_bound"] = sha_binding.sha_bound
    (Path(evidence_root) / "probe_summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary
