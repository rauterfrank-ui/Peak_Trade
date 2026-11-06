"""Productive MV2 DDO capture → offline export handoff."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.learning.deterministic_decision_outcome_v0.double_play_input_evidence_v1 import (
    SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_capture_to_offline_export_join_v1 import (
    HANDOFF_ARTIFACT_BASENAME,
    ProductiveDdoCaptureToOfflineExportHandoffRequestV1,
    run_productive_ddo_capture_to_offline_export_handoff_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from tests.ops.test_current_productive_master_v2_ddo_learning_capture_join_v1 import _cycle_kwargs


def test_mv2_cycle_blocks_unverified_outcome_source(tmp_path: Path) -> None:
    result = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs(cycle_id="ddo-export-1", tmp_path=tmp_path),
    )
    handoff = result.ddo_offline_export_handoff
    assert handoff is not None
    assert handoff.get("ok") is False
    assert handoff.get("status") == "BLOCKED_UNVERIFIED_OUTCOME_SOURCE"
    assert handoff.get("reason_codes") == ["VERIFIED_N_BARS_SOURCE_NOT_BOUND"]
    assert handoff.get("optimization_ack_status") is None
    assert handoff.get("decision_event_ref")
    assert handoff.get("learning_evidence_record_id") is None
    assert handoff.get("learning_state_record_ref") is None
    assert handoff.get("pending_outcome_created") is False
    assert handoff.get("causal_parent_capture_record_ids")
    artifact = tmp_path / HANDOFF_ARTIFACT_BASENAME
    assert not artifact.exists()
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_productive_capture.jsonl")
    ledger.verify_integrity()
    records = ledger.read_all()
    assert records
    assert all(
        row.get("schema_name")
        in {
            "decision_event",
            "double_play_entry_exit_observation",
            SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE,
        }
        for row in records
    )
    decision_ids = {row["record_id"] for row in records if row["schema_name"] == "decision_event"}
    input_evidence = [
        row
        for row in records
        if row["schema_name"] == SCHEMA_NAME_DOUBLE_PLAY_ENTRY_EXIT_POLICY_INPUT_EVIDENCE
    ]
    assert input_evidence
    assert all(row["decision_event_ref"] in decision_ids for row in input_evidence)
    from src.ops.full_core_live_path_composition_root_v1.ghv_intelligence_lineage_forensic_observability_v1 import (
        build_intelligence_lineage_observability_record_v1,
    )

    diagnostic = build_intelligence_lineage_observability_record_v1(
        cycle_id="ddo-export-1",
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        ddo_capture_summary=result.ddo_capture_summary,
        ddo_offline_export_handoff=handoff,
        replay=SimpleNamespace(
            replay_pass=True, evidence=SimpleNamespace(decision_outcome="enter_long")
        ),
    )
    assert diagnostic["ddo_handoff_status"] == "BLOCKED_UNVERIFIED_OUTCOME_SOURCE"
    assert diagnostic["structural_outcome_completeness"] == "UNAVAILABLE"
    assert diagnostic["pending_outcome_created_by_handoff"] is False
    assert diagnostic["learning_evidence_ref"]["status"] == "NOT_REACHED"


@pytest.mark.parametrize("capture_failure", [False, True])
def test_capture_does_not_change_trading_result(tmp_path: Path, capture_failure: bool) -> None:
    kwargs = _cycle_kwargs(cycle_id="same-decision", tmp_path=tmp_path)
    ledger = kwargs.pop("ddo_durable_evidence_ledger_path")
    baseline = run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    if capture_failure:
        parent = tmp_path / "parent-is-file"
        parent.write_text("preserve")
        ledger = parent / "capture.jsonl"
    actual = run_current_productive_master_v2_runtime_cycle_v1(
        **kwargs, ddo_durable_evidence_ledger_path=ledger
    )
    assert replace(actual, ddo_capture_summary=None, ddo_offline_export_handoff=None) == baseline
    assert actual.ddo_capture_summary is not None
    if capture_failure:
        assert actual.ddo_capture_summary.get("durable_ok") is False
        assert (
            actual.ddo_offline_export_handoff is None
            or actual.ddo_offline_export_handoff["ok"] is False
        )


def test_retired_seed_not_called_and_historical_artifact_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_master_v2_ddo_capture_to_offline_export_join_v1 as seam,
    )

    def forbidden(**kwargs):
        raise AssertionError("retired seed called")

    monkeypatch.setattr(seam, "build_pt1h_bar_producer_from_finalized_closes_v1", forbidden)
    artifact = tmp_path / HANDOFF_ARTIFACT_BASENAME
    artifact.write_bytes(b"historical artifact, not current evidence")
    result = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs(cycle_id="no-seed", tmp_path=tmp_path)
    )
    assert result.ddo_offline_export_handoff["ok"] is False
    assert artifact.read_bytes() == b"historical artifact, not current evidence"


@pytest.mark.parametrize(
    "durable_ok,decision_cycle,reason",
    [
        (False, "session:cycle:1", "CAPTURE_DURABILITY_FAILED"),
        (True, "session:cycle:2", "CAPTURE_DECISION_CYCLE_MISMATCH"),
    ],
)
def test_rejects_failed_durability_and_correlation_only_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    durable_ok: bool,
    decision_cycle: str,
    reason: str,
) -> None:
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_master_v2_ddo_capture_to_offline_export_join_v1 as seam,
    )

    monkeypatch.setattr(
        seam,
        "resolve_decision_event_from_capture_binding_v1",
        lambda *args, **kwargs: {"record_id": "ddo.dec:test", "cycle_id": decision_cycle},
    )
    result = run_productive_ddo_capture_to_offline_export_handoff_v1(
        ProductiveDdoCaptureToOfflineExportHandoffRequestV1(
            ddo_capture_binding=DdoCaptureBindingV0(
                enabled=True, ledger_path=tmp_path / "capture.jsonl"
            ),
            ddo_capture_summary={"ok": True, "durable_ok": durable_ok},
            session_id="session",
            cycle_index=1,
            event_ts_unix=1_700_000_000,
            repository_sha="abc12345",
            venue="okx_eea",
            canonical_instrument_id="inst-1",
            venue_instrument_id="ETH-USDT-SWAP",
            finalized_closes=[100, 101],
            last_finalized_event_ts_unix=1_700_000_000,
        )
    )
    assert result.reason_codes == (reason,)
    assert result.ok is False
    assert not list(tmp_path.iterdir())


def test_handoff_fail_closed_without_capture_summary(tmp_path: Path) -> None:
    binding = DdoCaptureBindingV0(
        enabled=True, ledger_path=tmp_path / "ddo_productive_capture.jsonl"
    )
    out = run_productive_ddo_capture_to_offline_export_handoff_v1(
        ProductiveDdoCaptureToOfflineExportHandoffRequestV1(
            ddo_capture_binding=binding,
            ddo_capture_summary={"ok": False},
            session_id="sess-missing",
            cycle_index=1,
            event_ts_unix=1_700_000_000.0,
            repository_sha="abc12345deadbeef",
            venue="okx_eea",
            canonical_instrument_id="inst-1",
            venue_instrument_id="ETH-USDT-SWAP",
            finalized_closes=[100.0, 101.0],
            last_finalized_event_ts_unix=1_700_000_000.0,
        )
    )
    assert out.ok is False
    assert "CAPTURE_SUMMARY_NOT_OK" in out.reason_codes


def test_handoff_fail_closed_without_in_memory_capture_records(tmp_path: Path) -> None:
    cycle = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs(cycle_id="ddo-export-2", tmp_path=tmp_path),
    )
    summary = cycle.ddo_capture_summary
    assert summary is not None
    binding = DdoCaptureBindingV0(
        enabled=True, ledger_path=tmp_path / "ddo_productive_capture.jsonl"
    )
    out = run_productive_ddo_capture_to_offline_export_handoff_v1(
        ProductiveDdoCaptureToOfflineExportHandoffRequestV1(
            ddo_capture_binding=binding,
            ddo_capture_summary=summary,
            session_id="sess-empty-ledger",
            cycle_index=1,
            event_ts_unix=1_700_000_000.0,
            repository_sha="abc12345deadbeef",
            venue="okx_eea",
            canonical_instrument_id="inst-1",
            venue_instrument_id="ETH-USDT-SWAP",
            finalized_closes=[100.0, 101.0],
            last_finalized_event_ts_unix=1_700_000_000.0,
        )
    )
    assert out.ok is False
    assert out.reason_codes
    assert out.reason_codes[0] in {
        "CAPTURE_RECORDS_MISSING",
        "DECISION_EVENT_NOT_RESOLVED_FROM_CAPTURE",
    }


def test_productive_optimization_join_authorization_guard() -> None:
    assert PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED is False


def test_canonical_optimization_input_rejects_missing_fields() -> None:
    result = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(learning_evidence=None)
    )
    assert result["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
