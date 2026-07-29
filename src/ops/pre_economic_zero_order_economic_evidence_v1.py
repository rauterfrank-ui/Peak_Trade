"""Economic evidence schema + session summary for Pre-Economic Zero-Order v1.

Persists hypothetical (zero-order) decision economics only.
State-switch fields reuse the canonical Master-V2 StateSwitchEvidenceV1 shape
(plus switch freshness / STALE from the landscape projection contract).
Never claims ECONOMIC_VALIDITY_PASS / profitability / Shadow readiness.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.pre_economic_zero_order_wallclock_arming_v1 import TRUTH_CLAIM

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_ECONOMIC_EVIDENCE_V1=true"
SCHEMA_VERSION = "v1"
EVIDENCE_FILE = "economic_decisions.jsonl"
SUMMARY_FILE = "session_economic_summary.json"

# Canonical State Switch field names (StateSwitchEvidenceV1 + landscape freshness).
# Invalid legacy placeholder switch_stay_state must never appear.
CANONICAL_STATE_SWITCH_OWNER = "trading.master_v2.double_play_state"
CANONICAL_STATE_SWITCH_BINDING = (
    "trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0"
)
CANONICAL_SWITCH_FRESHNESS_OWNER = (
    "webui.market_dashboard_landscape_v2.contracts.RegimeBullBearSwitchSnapshotV1"
)

REQUIRED_DECISION_FIELDS = (
    "timestamp",
    "instrument",
    "market_snapshot_identity",
    "regime",
    "bull_bear_state",
    "state_switch",
    "decision",
    "hypothetical_entry",
    "hypothetical_exit",
    "fees",
    "slippage",
    "stop_state",
    "killstate",
    "gross_pnl",
    "net_pnl",
    "mae",
    "mfe",
    "drawdown_contribution",
    "rejection_or_no_trade_reason",
    "provenance",
)

REQUIRED_STATE_SWITCH_FIELDS = (
    "state_switch_id",
    "previous_side_state",
    "next_side_state",
    "scope_event_type",
    "transition_allowed",
    "transition_reason_code",
    "semantic_digest",
    "availability",
)


@dataclass
class StateSwitchEvidenceBindingV1:
    """Read-only binding of canonical StateSwitchEvidenceV1 + freshness.

    ``availability`` uses the landscape contract values (AVAILABLE/STALE/…).
    STALE means aged switch evidence retained without recomputation — not a
    Switch/Stay decision token.
    """

    state_switch_id: str
    previous_side_state: str
    next_side_state: str
    scope_event_type: str
    transition_allowed: bool
    transition_reason_code: str
    semantic_digest: str
    availability: str
    instrument_id: str = ""
    trading_epoch: int = 0
    owner: str = CANONICAL_STATE_SWITCH_OWNER
    binding_adapter: str = CANONICAL_STATE_SWITCH_BINDING

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HypotheticalDecisionRecordV1:
    timestamp: float
    instrument: str
    market_snapshot_identity: str
    regime: str
    bull_bear_state: str
    state_switch: dict[str, Any]
    decision: str
    hypothetical_entry: Optional[float]
    hypothetical_exit: Optional[float]
    fees: float
    slippage: float
    stop_state: str
    killstate: str
    gross_pnl: float
    net_pnl: float
    mae: float
    mfe: float
    drawdown_contribution: float
    rejection_or_no_trade_reason: str
    provenance: dict[str, Any]
    double_play_state: str = "INACTIVE"
    cycle_index: int = 0
    ai_layer_authority: str = "NONE"
    risk_sizing_state: str = "OBSERVED_NON_AUTHORITATIVE"
    orders_attempted: int = 0
    orders_submitted: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate_required_fields(self) -> list[str]:
        payload = self.to_dict()
        missing = [k for k in REQUIRED_DECISION_FIELDS if k not in payload]
        if "switch_stay_state" in payload:
            missing.append("FORBIDDEN_FIELD:switch_stay_state")
        sw = payload.get("state_switch")
        if not isinstance(sw, dict):
            missing.append("MISSING_FIELD:state_switch")
        else:
            for key in REQUIRED_STATE_SWITCH_FIELDS:
                if key not in sw:
                    missing.append(f"MISSING_STATE_SWITCH_FIELD:{key}")
        return missing


@dataclass
class SessionEconomicSummaryV1:
    runtime_duration_seconds: float
    cycles: int
    data_gaps: int
    decision_counts: dict[str, int]
    hypothetical_trade_counts: int
    gross_pnl: float
    net_pnl_after_fees_slippage: float
    profit_factor: float
    max_drawdown: float
    win_rate: float
    average_trade: float
    regime_segmented_pnl: dict[str, float]
    state_switch_transitions: int
    switch_stale_count: int
    killstate_interventions: int
    verifier_result: str
    truth_claim: str = TRUTH_CLAIM
    economic_validity_pass: bool = False
    profitability_proven: bool = False
    shadow_ready: bool = False
    promotion_authorized: bool = False
    orders: bool = False
    canonical_state_switch_owner: str = CANONICAL_STATE_SWITCH_OWNER

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def append_decision_jsonl(*, path: Path, record: HypotheticalDecisionRecordV1) -> None:
    missing = record.validate_required_fields()
    if missing:
        raise ValueError("ECONOMIC_EVIDENCE_FIELDS_MISSING:" + ",".join(missing))
    if int(record.orders_attempted) != 0 or int(record.orders_submitted) != 0:
        raise ValueError("ECONOMIC_EVIDENCE_ORDERS_NONZERO")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")


def load_decision_records(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def validate_decision_record_completeness(record: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if "switch_stay_state" in record:
        blockers.append("FORBIDDEN_FIELD:switch_stay_state")
    for key in REQUIRED_DECISION_FIELDS:
        if key not in record:
            blockers.append(f"MISSING_FIELD:{key}")
    sw = record.get("state_switch")
    if not isinstance(sw, dict):
        blockers.append("STATE_SWITCH_NOT_OBJECT")
    else:
        for key in REQUIRED_STATE_SWITCH_FIELDS:
            if key not in sw:
                blockers.append(f"MISSING_STATE_SWITCH_FIELD:{key}")
        if str(sw.get("availability") or "") not in {
            "AVAILABLE",
            "STALE",
            "UNAVAILABLE",
            "INVALID",
        }:
            blockers.append("STATE_SWITCH_AVAILABILITY_INVALID")
    if int(record.get("orders_attempted", 0)) != 0:
        blockers.append("ORDERS_ATTEMPTED_NONZERO")
    if int(record.get("orders_submitted", 0)) != 0:
        blockers.append("ORDERS_SUBMITTED_NONZERO")
    provenance = record.get("provenance")
    if not isinstance(provenance, dict) or not provenance:
        blockers.append("PROVENANCE_INCOMPLETE")
    return blockers


def build_session_economic_summary_v1(
    *,
    records: Sequence[Mapping[str, Any]],
    runtime_duration_seconds: float,
    cycles: int,
    data_gaps: int,
    state_switch_transitions: int,
    switch_stale_count: int,
    killstate_interventions: int,
    verifier_result: str = "PENDING",
) -> SessionEconomicSummaryV1:
    decision_counts: dict[str, int] = {}
    regime_pnl: dict[str, float] = {}
    trade_pnls: list[float] = []
    equity = 0.0
    peak = 0.0
    max_dd = 0.0
    wins = 0

    for row in records:
        decision = str(row.get("decision") or "UNKNOWN")
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        net = float(row.get("net_pnl") or 0.0)
        regime = str(row.get("regime") or "UNKNOWN")
        regime_pnl[regime] = regime_pnl.get(regime, 0.0) + net
        if decision in {"ENTER_LONG", "ENTER_SHORT", "EXIT", "REVERSE", "HYPOTHETICAL_TRADE"}:
            trade_pnls.append(net)
            equity += net
            peak = max(peak, equity)
            max_dd = max(max_dd, peak - equity)
            if net > 0:
                wins += 1

    gross = sum(float(r.get("gross_pnl") or 0.0) for r in records)
    net_total = sum(float(r.get("net_pnl") or 0.0) for r in records)
    gains = sum(p for p in trade_pnls if p > 0)
    losses = sum(-p for p in trade_pnls if p < 0)
    if losses > 0:
        profit_factor = gains / losses
    elif gains > 0:
        profit_factor = -1.0  # sentinel: infinite PF with zero losses (JSON-safe)
    else:
        profit_factor = 0.0
    trade_count = len(trade_pnls)
    win_rate = (float(wins) / float(trade_count)) if trade_count else 0.0
    average_trade = (net_total / float(trade_count)) if trade_count else 0.0

    return SessionEconomicSummaryV1(
        runtime_duration_seconds=float(runtime_duration_seconds),
        cycles=int(cycles),
        data_gaps=int(data_gaps),
        decision_counts=decision_counts,
        hypothetical_trade_counts=trade_count,
        gross_pnl=float(gross),
        net_pnl_after_fees_slippage=float(net_total),
        profit_factor=float(profit_factor),
        max_drawdown=float(max_dd),
        win_rate=float(win_rate),
        average_trade=float(average_trade),
        regime_segmented_pnl=regime_pnl,
        state_switch_transitions=int(state_switch_transitions),
        switch_stale_count=int(switch_stale_count),
        killstate_interventions=int(killstate_interventions),
        verifier_result=str(verifier_result),
    )


def write_session_economic_summary(*, path: Path, summary: SessionEconomicSummaryV1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
