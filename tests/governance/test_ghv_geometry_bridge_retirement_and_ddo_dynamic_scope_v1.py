"""GHV geometry bridge retirement + canonical DDO SEAM_DYNAMIC_SCOPE capture proofs."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.governance.ghv_referenced_complete_intelligence_superstructure_offline_cycle_v1 import (
    GHV_AUTHORITY,
    run_ghv_referenced_intelligence_superstructure_offline_cycle_v1,
)
from src.governance.ghv_referenced_intelligence_superstructure_ghv_reference_manifest_v1 import (
    ghv_reference_root_path_v1,
    load_ghv_reference_manifest_config_v1,
    prove_ghv_reference_artifacts_v1,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
    SEAM_DYNAMIC_SCOPE,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.full_core_live_path_composition_root_v1.ghv_intelligence_lineage_forensic_observability_v1 import (
    build_intelligence_lineage_observability_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.types_v1 import (
    NaturalEnterPendingOutcomeRecordV1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    SCOPE_DECISION_TRACE_SCHEMA_VERSION,
)
from tests.governance.test_ghv_referenced_complete_intelligence_superstructure_integration_v1 import (
    _offline_request,
)
from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
    non_productive_test_master_v2_reconciliation_admission_v1,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    DECISION_REF,
    DPO_REF,
    NATIVE,
    _create_pending,
)
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _apply,
    _sixty_one_samples,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_provenance_from_governed_synthetic_close_mark_and_index_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

REPO_ROOT = Path(__file__).resolve().parents[2]
PENDING_INDEX = (
    ghv_reference_root_path_v1(repo_root=REPO_ROOT)
    / "fresh_lane_state_root/LANE_1/natural_enter_pending_outcome_index_v1.json"
)


def test_geometry_bridge_module_absent() -> None:
    path = (
        REPO_ROOT
        / "src/ops/full_core_live_path_composition_root_v1/ghv_decision_time_geometry_evidence_v1.py"
    )
    assert not path.is_file()
    spec = importlib.util.find_spec(
        "src.ops.full_core_live_path_composition_root_v1.ghv_decision_time_geometry_evidence_v1"
    )
    assert spec is None


def test_manifest_has_no_geometry_ledger_basename() -> None:
    manifest = load_ghv_reference_manifest_config_v1()
    assert "geometry_evidence_ledger_basename" not in manifest
    assert manifest["ghv_authority"] == "NONE"


def test_pending_record_has_no_geometry_fields() -> None:
    raw = {
        "schema_version": "natural_enter_pending_outcome.v1",
        "pending_outcome_id": "neo.pending.test",
        "decision_event_ref": "ddo.dec:test",
        "dpo_ref": "ddo.dpo:test",
        "decision_id": "",
        "correlation_id": "ddo.corr.test",
        "cycle_id": "cycle:1",
        "source_run_id": "run",
        "source_session_id": "sess",
        "source_evidence_root": "evidence",
        "canonical_instrument_id": "inst",
        "native_id": "NATIVE",
        "side": "LONG",
        "decision_timestamp_unix": 1.0,
        "decision_reference_price": 1.0,
        "market_context_ref": "",
        "n_bars_required": 2,
        "bars_observed": 0,
        "finalized_bar_identities": [],
        "status": "PENDING",
        "created_at_utc": "2026-01-01T00:00:00Z",
        "updated_at_utc": "2026-01-01T00:00:00Z",
    }
    rec = NaturalEnterPendingOutcomeRecordV1.from_index_dict_v1(raw)
    dumped = rec.to_index_dict_v1()
    assert "geometry_evidence_ref" not in dumped
    assert "geometry_evidence_digest" not in dumped


def test_offline_cycle_lineage_has_no_geometry_slot(tmp_path: Path) -> None:
    out = run_ghv_referenced_intelligence_superstructure_offline_cycle_v1(
        _offline_request(tmp_path)
    )
    lineage = out["intelligence_lineage"]
    assert "geometry_evidence_ref" not in lineage
    assert GHV_AUTHORITY == "NONE"


def test_lineage_observability_no_geometry_fields() -> None:
    replay = type("R", (), {"evidence": type("E", (), {"decision_outcome": "enter_long"})()})()
    record = build_intelligence_lineage_observability_record_v1(
        cycle_id="c:1",
        instrument_id="MINA",
        venue_native_id="MINA-USDT-SWAP",
        ddo_capture_summary={"ok": True},
        ddo_offline_export_handoff=None,
        replay=replay,
    )
    assert "geometry_evidence_ref" not in record
    assert record["scope_ref"]["status"] == "PRESENT"
    assert record["ghv_authority"] == "NONE"


def test_ghv_scope_trace_schema_unchanged_forensic_only() -> None:
    assert SCOPE_DECISION_TRACE_SCHEMA_VERSION == "golden_happy_scope_decision_trace.v1"
    proof = prove_ghv_reference_artifacts_v1()
    assert proof["ghv_authority"] == "NONE"


def test_productive_ddo_capture_emits_dynamic_scope_seam(tmp_path: Path) -> None:
    bound = BoundInstrumentV1(
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="ETH-USDT-SWAP",
        ranking_snapshot_id="rank-ddo-scope",
        ranking_integrity_digest="rank-ddo-scope-digest",
        universe_snapshot_id="uni-ddo-scope",
        selection_id="sel-ddo-scope",
        selection_integrity_digest="sel-ddo-scope-digest",
        selection_state="SELECTED",
    )
    identity = {
        "canonical_instrument_id": bound.instrument_id,
        "venue_instrument_id": bound.venue_native_id,
    }
    samples = tuple(
        sorted(_sixty_one_samples(**identity), key=lambda sample: sample.event_time_unix_seconds)
    )
    created = _apply(tmp_path, samples=samples, **identity)
    assert created.producer is not None
    # The Core feature window also needs older closes from the same price series.
    first = samples[0].mark_price
    closes = tuple(first - offset for offset in range(39, 0, -1)) + tuple(
        sample.mark_price for sample in samples
    )
    last = closes[-1]
    last_event = samples[-1].event_time_unix_seconds
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="ddo-scope-seam-1",
        observed_unix=last_event + 100.0,
        mark_px=last,
        index_px=last * 0.995,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=last_event,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=created.producer,
        ddo_durable_evidence_ledger_path=tmp_path / "ddo_productive_capture.jsonl",
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id),
            mark_px=last,
            index_px=last * 0.995,
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound
        ),
    )
    assert result.input_blocker == "", result.fail_reasons
    assert result.ddo_capture_summary is not None
    assert result.ddo_capture_summary.get("ok") is True
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_productive_capture.jsonl")
    (scope,) = (
        record
        for record in ledger.read_all()
        if record.get("producer_id") == "deterministic_scope_event_generator_v1"
    )
    assert scope["record_id"] in result.ddo_capture_summary["record_ids"]
    assert scope["cycle_id"] == f"{result.cycle_id}:cycle:1"
    assert scope["event_time_utc"] == datetime.fromtimestamp(last_event, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert scope["decision_type"] == "DYNAMIC_SCOPE_NON_TRANSITION"
    assert SEAM_DYNAMIC_SCOPE == "core.dynamic_scope"
    assert CAPTURE_FAILURE_CHANGES_DECISION is False


def test_pending_horizon_is_bound_to_decision_without_evaluated_outcome(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    record = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert record is not None
    assert record.decision_event_ref == DECISION_REF
    assert record.dpo_ref == DPO_REF
    assert record.native_id == NATIVE
    assert record.n_bars_required == 2
    assert record.status == "PENDING"
    assert record.bars_observed == 0
    assert record.finalized_bar_identities == ()
    assert record.closure_refs == {}
    assert "geometry_evidence_ref" not in record.to_index_dict_v1()


@pytest.mark.skipif(not PENDING_INDEX.is_file(), reason="Historical MINA pending index absent")
def test_historical_mina_witness_pending_horizon_contract() -> None:
    pending = json.loads(PENDING_INDEX.read_text(encoding="utf-8"))
    rec = pending["records_by_decision_event_ref"]["ddo.dec:7b6a2f315833f9c3462b0e8d"]
    assert rec["pending_outcome_id"] == "neo.pending.ca567ad2099484912c1e643c973476c1"
    assert rec["n_bars_required"] == 2
    assert rec["bars_observed"] == 0
    assert rec["status"] == "PENDING"
    assert "geometry_evidence_ref" not in rec


@pytest.mark.parametrize(
    "pattern",
    ["ghv_decision_time_geometry_evidence", "ghv.gev.", "geometry_evidence_ref"],
)
def test_repo_src_has_no_bridge_symbols(pattern: str) -> None:
    hits: list[str] = []
    for path in (REPO_ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if pattern in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []
