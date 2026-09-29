"""Productive MV2 DDO capture → offline export handoff."""

from __future__ import annotations

from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)

from pathlib import Path

import pytest

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    CanonicalOptimizationUniverseLearningInputRequestV1,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
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


def test_mv2_cycle_offline_export_handoff_accepted(tmp_path: Path) -> None:
    result = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs(cycle_id="ddo-export-1", tmp_path=tmp_path),
    )
    handoff = result.ddo_offline_export_handoff
    assert handoff is not None
    assert handoff.get("ok") is True
    assert handoff.get("optimization_ack_status") == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
    assert handoff.get("decision_event_ref")
    assert handoff.get("learning_evidence_record_id")
    assert handoff.get("causal_parent_capture_record_ids")
    artifact = tmp_path / HANDOFF_ARTIFACT_BASENAME
    assert artifact.is_file()


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
