"""Offline reproof for CURRENT → GHOSV read-only execution evidence binding."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.ghosv_bounded_context_v1.constants_v1 import ADAPTER_MODE, TRAFFIC_RED, TRAFFIC_YELLOW
from src.ops.ghosv_bounded_context_v1.current_execution_evidence_reader_v1 import (
    READER_AUTHORITY,
    CurrentExecutionEvidenceSourcesV1,
    observe_current_execution_via_ghosv_v1,
    read_current_execution_evidence_v1,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import GhosvCompleteness, GhosvEvidenceKind
from src.ops.ghosv_bounded_context_v1.s02_identity_correlation_v1 import correlate_evidence_v1
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)

REPO = Path(__file__).resolve().parents[2]
CAP11_FIXTURE = (
    REPO
    / "docs/evidence/capability_1_1_productive_reconciliation_runtime_binding_v1/clean_start_match"
)
PRE_EXTERNAL_FIXTURE = (
    REPO
    / "tests/fixtures/current_productive_golden_happy_vector_post_7065_reference_v1/PRE_EXTERNAL_CONVERGENCE_REPORT.json"
)


def test_reader_authority_none():
    assert READER_AUTHORITY == "NONE"
    assert ADAPTER_MODE == "DISABLED"


def test_cap11_recon_bundle_maps_to_ghosv_records():
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id="cap11-clean-start",
        recon_dir=CAP11_FIXTURE,
    )
    records = read_current_execution_evidence_v1(sources)
    kinds = {r.kind for r in records}
    assert GhosvEvidenceKind.RECONCILIATION_GATE.value in kinds


def test_pre_external_fixture_maps_execution_attempt_and_report():
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id="pre-ext-fixture",
        pre_external_convergence_report_json=PRE_EXTERNAL_FIXTURE,
    )
    records = read_current_execution_evidence_v1(sources)
    kinds = {r.kind for r in records}
    assert GhosvEvidenceKind.PRE_EXTERNAL_REPORT.value in kinds
    assert GhosvEvidenceKind.EXECUTION_ATTEMPT.value in kinds
    attempt = next(r for r in records if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value)
    assert attempt.payload.get("post_count_known") is True
    assert attempt.payload.get("post_occurred") is False
    assert attempt.completeness == GhosvCompleteness.COMPLETE.value


def test_combined_fixture_observe_yellow_or_green_not_unbounded(tmp_path: Path):
    envelope = build_final_order_envelope_v1(
        instrument_id="BTC-USDT-SWAP",
        side="buy",
        order_type="limit",
        quantity="1",
        quantity_unit="contract",
        td_mode="cross",
        reduce_only=False,
        client_order_id="ghosv-bind-test-1",
        path_kind="test",
        venue_plan_clordid="ghosv-bind-test-1",
        quantity_source="test",
        side_source="test",
        instrument_source="test",
        admission_ref="test-admission",
        provenance_ref="test-prov",
        creation_epoch="2026-01-01T00:00:00+00:00",
        price="100",
        pos_side="long",
    )
    env_path = tmp_path / "final_order_envelope.json"
    env_path.write_text(
        __import__("json").dumps(envelope.to_runtime_json_v1(), sort_keys=True),
        encoding="utf-8",
    )
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id="combined-offline",
        recon_dir=CAP11_FIXTURE,
        final_order_envelope_json=env_path,
        pre_external_convergence_report_json=PRE_EXTERNAL_FIXTURE,
    )
    result = observe_current_execution_via_ghosv_v1(sources)
    assert result.adapter_decision.adapter_mode == "DISABLED"
    assert result.traffic_overall in {TRAFFIC_YELLOW, TRAFFIC_RED}


def test_recon_hard_stop_fixture_red(tmp_path: Path):
    import json

    recon_dir = tmp_path / "recon"
    recon_dir.mkdir()
    (recon_dir / "productive_reconciliation_evidence_v1.json").write_text(
        json.dumps(
            {
                "classification": "MISSING_TRUTH",
                "hard_stop": True,
                "config_digest": "d",
                "single_writer_identity": "productive_portfolio_position_state_writer_v1",
                "observed_state_digest": "o",
                "event_time_unix": 1.0,
                "wall_time_unix": 2.0,
            }
        ),
        encoding="utf-8",
    )
    sources = CurrentExecutionEvidenceSourcesV1(trade_id="recon-hs", recon_dir=recon_dir)
    result = observe_current_execution_via_ghosv_v1(sources)
    assert result.traffic_overall == TRAFFIC_RED


def test_cap11_recon_uses_binding_trade_id_and_preserves_writer_identity():
    binding = "operator-bound-trade-xyz"
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id=binding,
        recon_dir=CAP11_FIXTURE,
    )
    records = read_current_execution_evidence_v1(sources)
    recon = next(r for r in records if r.kind == GhosvEvidenceKind.RECONCILIATION_GATE.value)
    assert recon.trade_id == binding
    assert recon.payload.get("single_writer_identity") == (
        "productive_portfolio_position_state_writer_v1"
    )
    assert recon.payload.get("ghosv_binding_trade_id") == binding
    assert recon.payload.get("ghosv_file_writer_identity") == (
        "productive_portfolio_position_state_writer_v1"
    )


def test_combined_cap11_sources_single_s02_correlation_group():
    binding = "single-group-trade"
    sources = CurrentExecutionEvidenceSourcesV1(
        trade_id=binding,
        recon_dir=CAP11_FIXTURE,
    )
    records = read_current_execution_evidence_v1(sources)
    groups = correlate_evidence_v1(records)
    trade_ids = {g.trade_id for g in groups}
    assert trade_ids == {binding}


def test_pre_external_missing_post_count_unknown_not_zero(tmp_path: Path):
    import json

    report = {
        "NATIVE_ID": "BTC-USDT-SWAP",
        "TERMINAL_DISPOSITION": "HOLD",
        "PRE_EXTERNAL_REACHED": "true",
        "RUN_ID": "run-missing-post",
    }
    path = tmp_path / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    records = read_current_execution_evidence_v1(
        CurrentExecutionEvidenceSourcesV1(
            trade_id="missing-post-count",
            pre_external_convergence_report_json=path,
        )
    )
    attempt = next(r for r in records if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value)
    assert attempt.payload.get("post_count_known") is False
    assert "post_occurred" not in attempt.payload
    assert "post_count" not in attempt.payload
    assert attempt.completeness == GhosvCompleteness.UNKNOWN.value


def test_pre_external_invalid_post_count_unknown(tmp_path: Path):
    import json

    report = {
        "NATIVE_ID": "BTC-USDT-SWAP",
        "POST_COUNT": "not-a-number",
        "RUN_ID": "run-bad-post",
    }
    path = tmp_path / "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    records = read_current_execution_evidence_v1(
        CurrentExecutionEvidenceSourcesV1(
            trade_id="invalid-post-count",
            pre_external_convergence_report_json=path,
        )
    )
    attempt = next(r for r in records if r.kind == GhosvEvidenceKind.EXECUTION_ATTEMPT.value)
    assert attempt.payload.get("post_count_known") is False
    assert attempt.completeness == GhosvCompleteness.UNKNOWN.value


@pytest.mark.parametrize("missing_trade_id", ["", "   "])
def test_missing_trade_id_fail_closed(missing_trade_id: str):
    with pytest.raises(Exception):
        read_current_execution_evidence_v1(
            CurrentExecutionEvidenceSourcesV1(trade_id=missing_trade_id)
        )
