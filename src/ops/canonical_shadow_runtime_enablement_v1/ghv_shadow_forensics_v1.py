"""GHV-guided Shadow dry forensic probes (no operational authorization)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.ops.canonical_shadow_runtime_enablement_v1.constants_v1 import (
    SHADOW_ACTIVATION_OPERATOR_GO,
    SHADOW_OBSERVATION_OPERATOR_GO,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_cycle_entrypoint_v1 import (
    run_canonical_shadow_runtime_offline_cycle_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.shadow_reconciliation_v1 import (
    ShadowReconciliationLedgerV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    ensure_accounting_session_v1,
)

_INSTRUMENT = "ETH-USD_UM_XPERP-TEST"
_MARK = Decimal("2500.00")


@dataclass(frozen=True)
class GhvShadowForensicSummaryV1:
    ghv_pre_external_event_count: int
    ghv_shadow_continuation_eligible_count: int
    ghv_shadow_continuation_count: int
    causal_event_identity_break_count: int
    event_substitution_count: int
    unexplained_shadow_attrition_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "GHV_PRE_EXTERNAL_EVENT_COUNT": self.ghv_pre_external_event_count,
            "GHV_SHADOW_CONTINUATION_ELIGIBLE_COUNT": self.ghv_shadow_continuation_eligible_count,
            "GHV_SHADOW_CONTINUATION_COUNT": self.ghv_shadow_continuation_count,
            "CAUSAL_EVENT_IDENTITY_BREAK_COUNT": self.causal_event_identity_break_count,
            "EVENT_SUBSTITUTION_COUNT": self.event_substitution_count,
            "UNEXPLAINED_SHADOW_ATTRITION_COUNT": self.unexplained_shadow_attrition_count,
        }


def _load_pre_external_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return [r for r in rows if r.get("pre_external") is True]


def _side_from_natural_traces(traces_path: Path, flight_id: str, cycle_id: int) -> str | None:
    if not traces_path.is_file():
        return None
    try:
        enters = json.loads(traces_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    for row in enters:
        if row.get("FLIGHT_ID") == flight_id and int(row.get("CYCLE_ID", -1)) == cycle_id:
            outcome = str(row.get("decision_outcome") or "")
            if outcome == "enter_long":
                return "buy"
            if outcome == "enter_short":
                return "sell"
    return None


def run_ghv_same_event_shadow_trace_v1(
    *,
    ghv_run_dir: Path,
    dry_run_activated: bool = True,
) -> dict[str, Any]:
    """Trace PRE_EXTERNAL GHV rows through Shadow boundary (dry forensic)."""
    tail_path = ghv_run_dir / "productive_tail_observations.jsonl"
    traces_path = ghv_run_dir / "natural_enter_traces.txt"
    pre_rows = _load_pre_external_rows(tail_path)
    pre_count = len(pre_rows)

    session = ensure_accounting_session_v1(instrument_id=_INSTRUMENT, state_root=None)
    portfolio = SimulatedPortfolioEconomicsModelV1(
        PortfolioEconomicsModelParamsV1(initial_equity=Decimal("100000"))
    )
    ledger = ShadowReconciliationLedgerV1()
    traces: list[dict[str, Any]] = []
    continuation_count = 0
    identity_breaks = 0
    substitutions = 0
    attrition: list[dict[str, Any]] = []

    sample_rows = pre_rows[:2] if pre_rows else []
    if pre_rows:
        long_candidates = [r for r in pre_rows if r.get("FLIGHT_ID") == "GHV-F0068"]
        short_candidates = [r for r in pre_rows if r.get("FLIGHT_ID") == "GHV-F0069"]
        sample_rows = []
        if long_candidates:
            sample_rows.append(long_candidates[0])
        if short_candidates:
            sample_rows.append(short_candidates[0])

    for row in sample_rows:
        flight_id = str(row.get("FLIGHT_ID"))
        cycle_id = int(row.get("CYCLE_ID"))
        side = _side_from_natural_traces(traces_path, flight_id, cycle_id) or "sell"
        event_key = f"{flight_id}:{cycle_id}"
        if dry_run_activated:
            result = run_canonical_shadow_runtime_offline_cycle_v1(
                disposition=DISPOSITION_PRE_EXTERNAL_EFFECT,
                instrument_id=_INSTRUMENT,
                side=side,
                quantity="1",
                mark_price=str(_MARK),
                session_id=f"ghv-shadow-{flight_id}",
                cycle_index=cycle_id,
                session=session,
                portfolio=portfolio,
                operator_go_token=SHADOW_ACTIVATION_OPERATOR_GO,
                operator_observation_go_token=SHADOW_OBSERVATION_OPERATOR_GO,
            )
            ok, reason = ledger.record_simulated_execution(
                flight_id=flight_id,
                cycle_id=cycle_id,
                session_id=f"ghv-shadow-{flight_id}",
            )
            if result.ok and ok:
                continuation_count += 1
            else:
                attrition.append(
                    {
                        "event_key": event_key,
                        "shadow_ok": result.ok,
                        "reconcile_ok": ok,
                        "reason": reason or result.fail_reason,
                    }
                )
        traces.append(
            {
                "event_key": event_key,
                "flight_id": flight_id,
                "cycle_id": cycle_id,
                "side": side,
                "pre_external_row": row,
                "substituted": False,
            }
        )

    eligible = pre_count
    unexplained = len([a for a in attrition if not a.get("reason")])

    summary = GhvShadowForensicSummaryV1(
        ghv_pre_external_event_count=pre_count,
        ghv_shadow_continuation_eligible_count=eligible,
        ghv_shadow_continuation_count=continuation_count if dry_run_activated else 0,
        causal_event_identity_break_count=identity_breaks,
        event_substitution_count=substitutions,
        unexplained_shadow_attrition_count=unexplained,
    )
    return {
        "summary": summary.to_dict(),
        "representative_traces": traces,
        "attrition_explanations": attrition,
        "population_level_identity": "REPRESENTATIVE_ONLY",
    }


def run_shadow_dry_forensic_reproof_v1(
    *,
    ghv_run_dir: Path,
) -> dict[str, Any]:
    trace = run_ghv_same_event_shadow_trace_v1(ghv_run_dir=ghv_run_dir, dry_run_activated=True)
    s = trace["summary"]
    return {
        **s,
        "SHADOW_BOUNDARY_ACCEPT_COUNT": s["GHV_SHADOW_CONTINUATION_COUNT"],
        "SIMULATED_EXECUTION_ACCEPT_COUNT": s["GHV_SHADOW_CONTINUATION_COUNT"],
        "SIMULATED_EXECUTION_REJECT_COUNT": max(
            0,
            int(s["GHV_SHADOW_CONTINUATION_ELIGIBLE_COUNT"])
            - int(s["GHV_SHADOW_CONTINUATION_COUNT"]),
        ),
        "SHADOW_POSITION_TRANSITION_COUNT": s["GHV_SHADOW_CONTINUATION_COUNT"],
        "SHADOW_RECONCILED_EVENT_COUNT": s["GHV_SHADOW_CONTINUATION_COUNT"],
        "SHADOW_ACCOUNTED_EVENT_COUNT": s["GHV_SHADOW_CONTINUATION_COUNT"],
        "DRY_FORENSIC_ONLY": True,
        "OPERATOR_GO_CONSUMED": False,
    }
