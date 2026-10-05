"""Wallclock forensic cycle record builder (passive telemetry contract)."""

from __future__ import annotations

from src.ops.paper_shadow_bounded_orchestrator_v1.wallclock_forensic_cycle_record_v1 import (
    FIELD_MANIFEST,
    SCHEMA_VERSION,
    build_wallclock_forensic_cycle_record_v1,
)


def test_build_record_deterministic_digest() -> None:
    bridge = {
        "cycle_id": "s-c1",
        "instrument_id": "ETH-USD_UM_XPERP-310404",
        "decision_outcome": "enter_long",
        "reason_codes": ["ok"],
        "feature_digest": "abc",
        "market_data_reference": {"mid": 1.0},
        "fill": {"side": "BUY"},
        "portfolio_state_after_hash": "h2",
    }
    r1 = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle=bridge,
        cycle_sequence=1,
        timestamp_unix=100.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=True,
    )
    r2 = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle=bridge,
        cycle_sequence=1,
        timestamp_unix=100.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=True,
    )
    assert r1 is not None
    assert r1["schema_version"] == SCHEMA_VERSION
    assert r1["record_digest"] == r2["record_digest"]
    assert r1["natural_enter"] is True
    assert r1["fill_present"] is True
    assert len(FIELD_MANIFEST) >= 10
