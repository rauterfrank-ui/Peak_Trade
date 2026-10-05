"""Prove wallclock operational path records passive forensic cycle telemetry."""

from __future__ import annotations

from src.ops.paper_shadow_bounded_orchestrator_v1.run_evidence_v1 import RunEvidenceAccumulatorV1
from src.ops.paper_shadow_bounded_orchestrator_v1.wallclock_forensic_cycle_record_v1 import (
    build_wallclock_forensic_cycle_record_v1,
)


def test_operational_run_evidence_path_stores_forensic_record() -> None:
    ev = RunEvidenceAccumulatorV1(
        run_id="wire-test",
        fixpoint_sha="x",
        fixpoint_tree="y",
        settings_digest="z",
    )
    bridge = {
        "cycle_id": "c1",
        "instrument_id": "ETH-USD_UM_XPERP-310404",
        "decision_outcome": "observe",
        "reason_codes": ["hold"],
        "feature_digest": "fd",
        "market_data_reference": {"mid": 1.0},
    }
    record = build_wallclock_forensic_cycle_record_v1(
        bridge_cycle=bridge,
        cycle_sequence=1,
        timestamp_unix=100.0,
        instrument_id="ETH-USD_UM_XPERP-310404",
        pre_external_emitted=False,
    )
    ev.record_productive_cycle(bridge_cycle=bridge, forensic_record=record)
    assert ev.forensic_cycle_records
    assert ev.forensic_cycle_records[0]["record_digest"]
    assert ev.to_dict()["forensic_cycle_record_count"] == 1
