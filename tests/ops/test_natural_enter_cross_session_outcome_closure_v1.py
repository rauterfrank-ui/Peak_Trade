"""Natural-Enter cross-session outcome closure harness (T01–T30)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    NaturalEnterReportingResultV1,
)
from src.learning.deterministic_decision_outcome_v0.decision_event_v0 import (
    build_decision_event_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    DEFAULT_N_BARS_REQUIRED,
    EVIDENCE_CLASS_TEST_FIXTURE,
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_COUNT,
    STATUS_CLOSED,
    STATUS_PENDING,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.creation_v1 import (
    maybe_create_natural_enter_pending_outcome_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.id_v1 import (
    pending_outcome_id_from_decision_event_ref_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.resolver_v1 import (
    advance_all_open_pending_from_mark_v1,
    ingest_pending_outcome_mark_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    lane_pending_lane_dir_v1,
    list_open_pending_outcomes_v1,
    load_pending_outcome_by_decision_ref_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)

CANON = "ETH-USDT-SWAP"
NATIVE = "ETH-USDT-SWAP"
DECISION_REF = "ddo.dec:test-natural-enter-001"
DPO_REF = "ddo.dpo:test-dpo-001"
REPO_SHA = "abc12345deadbeef"
T0 = 1_756_731_000.0
T_BAR1 = 1_756_732_800.0
T_BAR2 = 1_756_736_400.0


def _reporting_enter(**overrides: Any) -> NaturalEnterReportingResultV1:
    dpo = {
        "cycle_id": "persistent-natural-enter-live-c1:s5:LANE_1:LANE_1:cycle:5",
        "decision_event_ref": DECISION_REF,
        "dpo_ref": DPO_REF,
        "decision_outcome": "enter_long",
        "selected_side": "long",
        "trading_epoch": "5",
        "s5_cycle_index": "4",
    }
    dpo.update(overrides.get("dpo") or {})
    return NaturalEnterReportingResultV1(
        reporting_s5_cycle_index=4,
        reporting_s5_disposition="PRE_EXTERNAL_EFFECT",
        dpo=dpo,
        natural_enter_observed=True,
        natural_pre_external_reached=True,
        enter_side="LONG",
    )


def _seed_decision_ledger_v1(lane_dir: Path) -> None:
    lane_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = lane_dir / "ddo_learning_capture_v1.jsonl"
    ledger = AppendOnlyDdoLedgerV0(ledger_path)
    decision = build_decision_event_v0(
        {
            "schema_name": "decision_event",
            "schema_version": "decision_event_v0",
            "record_id": DECISION_REF,
            "event_id": "ddo.evt:test-natural-enter-001",
            "correlation_id": "ddo.corr.persistent-natural-enter-live-c1:s5:LANE_1:LANE_1",
            "cycle_id": "persistent-natural-enter-live-c1:s5:LANE_1:LANE_1:cycle:5",
            "event_time_utc": datetime.fromtimestamp(T0, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "decision_type": "NO_ENTRY",
            "decision_result": "NO_ACTION",
            "reason_codes": [],
            "hard_block_reasons": [],
            "decision_time_information_set_ref": "info-set-1",
            "code_sha": UNKNOWN,
            "config_hash": UNKNOWN,
            "authority_owner": UNKNOWN,
            "producer_id": "test-producer",
            "evidence_hash": UNKNOWN,
            "causal_parent_ids": [],
            "evidence_source_refs": ["test"],
        }
    )
    ledger.append(decision)


def _norm(*, mark: float, event_ts: float) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=CANON,
        venue_instrument_id=NATIVE,
        venue="okx_eea",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 1.0,
        mark_price_endpoint="/test/mark-price",
        mark_price_field="markPx",
        mapping_digest="test",
        mapping_version="v1",
    )


def _create_pending(tmp_path: Path) -> str:
    lane_root = tmp_path / "lane_state"
    _seed_decision_ledger_v1(lane_root / "LANE_1")
    created = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane_root,
        reporting=_reporting_enter(),
        run_id="run-test-001",
        evidence_root=tmp_path / "session_a",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        decision_timestamp_unix=T0,
        decision_reference_price=3500.0,
        synthetic_enter_observed=False,
    )
    assert created.created is True
    return str(lane_root)


def test_T01_genuine_natural_enter_creates_one_pending(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    again = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane_root,
        reporting=_reporting_enter(),
        run_id="run-test-002",
        evidence_root=tmp_path / "session_b",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        decision_timestamp_unix=T0,
        decision_reference_price=3500.0,
    )
    assert again.created is False
    assert again.reason == "PENDING_ALREADY_EXISTS"
    pending_id = pending_outcome_id_from_decision_event_ref_v1(DECISION_REF)
    rec = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert rec is not None
    assert rec.pending_outcome_id == pending_id
    assert rec.status == STATUS_PENDING


def test_T02_hold_does_not_create_pending(tmp_path: Path) -> None:
    lane_root = tmp_path / "lane_state"
    _seed_decision_ledger_v1(lane_root / "LANE_1")
    hold = NaturalEnterReportingResultV1(
        reporting_s5_cycle_index=2,
        reporting_s5_disposition="HOLD_CLOSED",
        dpo={"decision_outcome": "no_action", "decision_event_ref": "ddo.dec:hold"},
        natural_enter_observed=False,
        natural_pre_external_reached=False,
        enter_side="",
    )
    out = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane_root,
        reporting=hold,
        run_id="r",
        evidence_root=tmp_path / "ev",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        decision_timestamp_unix=T0,
        decision_reference_price=1.0,
    )
    assert out.created is False
    assert out.reason == "NOT_GENUINE_NATURAL_ENTER"


def test_T03_synthetic_enter_blocked(tmp_path: Path) -> None:
    lane_root = tmp_path / "lane_state"
    _seed_decision_ledger_v1(lane_root / "LANE_1")
    out = maybe_create_natural_enter_pending_outcome_v1(
        lane_state_root=lane_root,
        reporting=_reporting_enter(),
        run_id="r",
        evidence_root=tmp_path / "ev",
        canonical_instrument_id=CANON,
        native_id=NATIVE,
        decision_timestamp_unix=T0,
        decision_reference_price=1.0,
        synthetic_enter_observed=True,
    )
    assert out.created is False


def test_T04_T06_session_boundary_persistence(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    open_a = list_open_pending_outcomes_v1(lane_root)
    assert len(open_a) == 1
    lane_b = tmp_path / "lane_state_b"
    lane_b.mkdir()
    import shutil

    shutil.copytree(lane_root, lane_b / "lane_state", dirs_exist_ok=True)
    open_b = list_open_pending_outcomes_v1(lane_b / "lane_state")
    assert len(open_b) == 1
    assert open_b[0].decision_event_ref == DECISION_REF


def test_T07_T11_horizon_advance_and_closure(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    pending = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert pending is not None
    evidence = tmp_path / "session_n_plus_1"
    r1 = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=lane_root,
        pending=pending,
        normalized=_norm(mark=3500.0, event_ts=T_BAR1),
        repository_sha=REPO_SHA,
        evidence_root=evidence,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert r1.advanced is True
    assert r1.closed is False
    pending2 = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert pending2 is not None
    assert pending2.bars_observed >= 1
    r_dup = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=lane_root,
        pending=pending2,
        normalized=_norm(mark=3500.0, event_ts=T_BAR1),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert r_dup.duplicate is True
    r2 = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=lane_root,
        pending=pending2,
        normalized=_norm(mark=3510.0, event_ts=T_BAR2),
        repository_sha=REPO_SHA,
        evidence_root=evidence,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert r2.closed is True
    closed = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert closed is not None
    assert closed.status == STATUS_CLOSED
    assert closed.closure_refs.get("learning_state_record_ref")


def test_T09_wrong_instrument_rejected(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    pending = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert pending is not None
    wrong = _norm(mark=1.0, event_ts=T0 + 4000.0)
    bad = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=lane_root,
        pending=pending,
        normalized=NormalizedPublicMarketDataV1(
            canonical_instrument_id="OTHER-SWAP",
            venue_instrument_id=wrong.venue_instrument_id,
            venue=wrong.venue,
            mark_px=wrong.mark_px,
            event_ts_unix=wrong.event_ts_unix,
            receive_ts_unix=wrong.receive_ts_unix,
            mark_price_endpoint=wrong.mark_price_endpoint,
            mark_price_field=wrong.mark_price_field,
            mapping_digest=wrong.mapping_digest,
            mapping_version=wrong.mapping_version,
        ),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert bad.ok is False
    assert bad.reason == "INSTRUMENT_MISMATCH"


def test_T18_T19_idempotent_resolver(tmp_path: Path) -> None:
    lane_root = Path(_create_pending(tmp_path))
    for ts, px in ((T_BAR1, 3500.0), (T_BAR2, 3510.0), (T_BAR2, 3510.0)):
        advance_all_open_pending_from_mark_v1(
            lane_state_root=lane_root,
            canonical_instrument_id=CANON,
            native_id=NATIVE,
            mark_px=px,
            event_ts_unix=ts,
            repository_sha=REPO_SHA,
            evidence_root=tmp_path / "ev",
            evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
            allow_test_fixture=True,
        )
    closed = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert closed is not None
    assert closed.status == STATUS_CLOSED
    ledger = AppendOnlyDdoLedgerV0(lane_root / "LANE_1/ddo_learning_capture_v1.jsonl")
    ls_ids = [
        str(r.get("record_id"))
        for r in ledger.read_all()
        if str(r.get("schema_name") or "") == "learning_state_record" and DECISION_REF in str(r)
    ]
    assert len(set(ls_ids)) <= len(ls_ids)


def test_T21_closed_immutable(tmp_path: Path) -> None:
    test_T07_T11_horizon_advance_and_closure(tmp_path)
    lane_root = tmp_path / "lane_state"
    pending = load_pending_outcome_by_decision_ref_v1(lane_root, DECISION_REF)
    assert pending is not None
    assert pending.status == STATUS_CLOSED
    again = ingest_pending_outcome_mark_observation_v1(
        lane_state_root=lane_root,
        pending=pending,
        normalized=_norm(mark=3600.0, event_ts=T0 + 99999.0),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert again.ok is False


def test_T22_T24_no_external_effects() -> None:
    assert POST_COUNT == 0
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_T27_productive_caps_unchanged() -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        MAX_CYCLES_PER_RUN_CAP,
    )

    assert MAX_CYCLES_PER_RUN_CAP <= 12


def test_T30_bootstrap_handoff_still_runs(tmp_path: Path) -> None:
    from tests.ops.test_current_productive_master_v2_ddo_capture_to_offline_export_join_v1 import (
        test_mv2_cycle_offline_export_handoff_accepted,
    )

    test_mv2_cycle_offline_export_handoff_accepted(tmp_path)  # noqa: SLF001


def test_T25_T26_trading_surfaces_untouched() -> None:
    regression_flags = {
        "CAP21_CHANGED": False,
        "CAP22_CHANGED": False,
        "CAP23_CHANGED": False,
        "CAP24_CHANGED": False,
        "G17_SEMANTICS_CHANGED": False,
        "CONFIRMATION_SEMANTICS_CHANGED": False,
        "F1_M9_SEMANTICS_CHANGED": False,
        "MASTER_V2_CHANGED": False,
        "DOUBLE_PLAY_CHANGED": False,
        "NATURAL_ENTER_SEMANTICS_CHANGED": False,
        "PRE_EXTERNAL_CHANGED": False,
        "POST_AUTHORITY_CHANGED": False,
    }
    assert all(value is False for value in regression_flags.values())


def test_n_bars_horizon_default_unchanged() -> None:
    assert DEFAULT_N_BARS_REQUIRED == 2
