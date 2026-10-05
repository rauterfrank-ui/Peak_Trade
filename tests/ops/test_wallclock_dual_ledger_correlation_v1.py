"""Passive dual-ledger forensic correlation (Run003 observability)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.paper_shadow_bounded_orchestrator_v1.shadow_routing_v1 import (
    PreExternalProductiveEventV1,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.wallclock_forensic_cycle_record_v1 import (
    apply_dual_ledger_passive_correlation_v1,
    build_wallclock_forensic_cycle_record_v1,
)


@dataclass
class _RouteStub:
    ok: bool
    shadow_evidence: dict[str, Any] | None
    fail_reason: str = ""


def test_no_natural_enter_bridge_only_correlation() -> None:
    record = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle={
            "cycle_id": "cycle:session:1",
            "decision_outcome": "observe",
            "reason_codes": [],
        },
        cycle_sequence=1,
        timestamp_unix=1.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=False,
    )
    assert record is not None
    apply_dual_ledger_passive_correlation_v1(record, run_id="PAPER_SHADOW_RUN_001")
    assert record["dual_ledger_correlation_key"] == "PAPER_SHADOW_RUN_001:cycle:session:1"
    assert record["pre_external_event_key"] is None
    assert record["bridge_domain_effect_present"] is False
    assert record["shadow_domain_effect_present"] is False
    assert record["shadow_fill_present"] is False


def test_pre_external_and_shadow_both_correlated() -> None:
    record = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle={
            "cycle_id": "cycle:session:2",
            "decision_outcome": "enter_long",
            "reason_codes": [],
            "fill": {"qty": "1"},
        },
        cycle_sequence=2,
        timestamp_unix=2.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=True,
    )
    assert record is not None
    event = PreExternalProductiveEventV1(
        event_key="paper-shadow-run:cycle:session:2",
        flight_id="paper-shadow-run",
        cycle_id=2,
        instrument_id="ETH-USD_UM_XPERP-310404",
        side="long",
        quantity="1",
        mark_price="2500",
        terminal_disposition="PRE_EXTERNAL_EFFECT",
    )
    route = _RouteStub(ok=True, shadow_evidence={"simulated_fill_present": True})
    apply_dual_ledger_passive_correlation_v1(
        record, run_id="PAPER_SHADOW_RUN_001", pre_external_event=event, shadow_route=route
    )
    assert record["dual_ledger_correlation_key"] == event.event_key
    assert record["bridge_domain_effect_present"] is True
    assert record["shadow_domain_effect_present"] is True
    assert record["shadow_fill_present"] is True
    assert record["paper_shadow_consumed"] is True
    assert record["causal_chain_terminator"] is None


def test_pre_external_shadow_missing_records_terminator() -> None:
    record = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle={
            "cycle_id": "cycle:session:3",
            "decision_outcome": "enter_long",
            "reason_codes": [],
        },
        cycle_sequence=3,
        timestamp_unix=3.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=True,
    )
    assert record is not None
    event = PreExternalProductiveEventV1(
        event_key="k:3",
        flight_id="f",
        cycle_id=3,
        instrument_id="ETH-USD_UM_XPERP-310404",
        side="long",
        quantity="1",
        mark_price="2500",
        terminal_disposition="PRE_EXTERNAL_EFFECT",
    )
    route = _RouteStub(
        ok=False, shadow_evidence=None, fail_reason="MAX_SIMULATED_OPEN_POSITION_COUNT"
    )
    apply_dual_ledger_passive_correlation_v1(
        record, run_id="RUN", pre_external_event=event, shadow_route=route
    )
    assert record["shadow_domain_effect_present"] is False
    assert record["causal_chain_terminator"] == "MAX_SIMULATED_OPEN_POSITION_COUNT"
