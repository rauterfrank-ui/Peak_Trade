"""Offline GHV + synthetic enter_short → PRE_EXTERNAL contract convergence (no product run)."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    CurrentProductiveGovernedCycleAuthorizationV1,
    EG_OWNER_GO,
    GET_OWNER_GO,
    OCCUPANCY_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
    make_n1_occupied_lane_s5_runner_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1,
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from src.ops.full_core_live_path_composition_root_v1.productive_golden_happy_vector_forensic_observability_v1 import (
    GoldenHappyVectorForensicObservabilitySessionV1,
    bind_golden_happy_vector_forensic_observability_session_v1,
    reset_golden_happy_vector_forensic_observability_session_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
)
from src.ops.single_selected_future_policy_v1.persistence_v1 import (
    load_and_validate_selection_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
    resolve_cap24_runtime_binding_witness_epoch_v1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import _candles
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _productive_instruments_row_for_enter_metadata_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LANE_RUNTIME_REL = (
    "runtime/current_productive/synthetic_enter_ghv_forward_backward_adjudication_v1/"
    "20261002T033614Z"
)
GHV_CAPTURE_REL = (
    "evidence/ops/post_pr7005_current_golden_happy_vector_natural_enter_reproof_v1/"
    "20261002T025205Z/natural_market_data_get_capture_v1.jsonl"
)
ORIGIN_SHA = "c0a1c16f51e2714e5e6df5102f1633b398d6f7f6"
CURSOR_FLOOR = 1790912400.0
NEW_C1_VENUE_TIME = 1790912460.0


def _origin_main_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=REPO_ROOT, text=True
    ).strip()


@pytest.mark.skipif(
    not (REPO_ROOT / LANE_RUNTIME_REL / "lane_state").is_dir(),
    reason="GHV lane runtime snapshot not present",
)
@pytest.mark.skipif(
    not (REPO_ROOT / GHV_CAPTURE_REL).is_file(),
    reason="GHV Real-Venue capture not present for G17 bootstrap",
)
def test_ghv_synthetic_enter_short_offline_reaches_pre_external_terminal() -> None:
    """CURRENT GHV snapshot + synthetic cycle-1 + fresh-pretrade fixtures → PRE_EXTERNAL."""
    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv_witness
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
        productive_auth_free_flat_occupancy_payloads_v1,
    )

    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False

    ws = Path(tempfile.mkdtemp(prefix="ghv_pre_ext_offline_"))
    try:
        runtime_root = REPO_ROOT / LANE_RUNTIME_REL
        shutil.copytree(runtime_root / "lane_state", ws / "lane_state")
        shutil.copytree(runtime_root / "productivity", ws / "productivity")
        product_evidence = ws / "product_evidence"
        product_evidence.mkdir()
        cycle_root = product_evidence / "cycles" / "cycle1inst"
        s5_root = cycle_root / "s5"
        s5_root.mkdir(parents=True)
        (cycle_root / "s5_cycle_authorization_v1.json").write_text(
            json.dumps(
                {
                    "cycle_index": 1,
                    "cycle_instance_id": "cycle1inst",
                    "c1_venue_event_time": NEW_C1_VENUE_TIME,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        capture_rows = ghv_witness._load_jsonl(REPO_ROOT / GHV_CAPTURE_REL)
        candles = _candles(last_ts_ms=int(NEW_C1_VENUE_TIME * 1000))
        prod = ws / "productivity"
        manifest = json.loads(
            (prod / "cap24_selection_state_publish_manifest_v1.json").read_text(encoding="utf-8")
        )
        sel = load_and_validate_selection_v1(
            prod / "runtime_state/selection", require_manifest=True
        )
        binding_epoch = resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-02T03:36:15Z",
        )
        handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=str(manifest.get("repository_sha") or ORIGIN_SHA),
            binding_epoch=binding_epoch,
        )
        native_id = str(handoff.bound_instrument.venue_native_id)
        mark = okx_public_mark_price_payload_v1(native_id=native_id, mark_px=21.035, index_px=21.03)
        index = {
            "code": "0",
            "data": [
                {
                    "instId": native_id,
                    "idxPx": "21.03",
                    "ts": str(int(NEW_C1_VENUE_TIME * 1000)),
                }
            ],
        }

        payloads = dict(_identity_payloads(instrument_id=native_id))
        inst_row = _productive_instruments_row_for_enter_metadata_v1(instrument_id=native_id)
        inst_row.update(
            {
                "ctVal": "0.1",
                "ctValCcy": "RESOL",
                "lotSz": "1",
                "minSz": "1",
                "tickSz": "0.001",
            }
        )
        payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {"code": "0", "data": [inst_row]}
        fresh_transport = ProductiveClassFreshGetTransportV1(payloads=payloads)

        g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
            evidence_store_root=ws / "g17",
            bound_instrument=handoff.bound_instrument,
            mark_candles_payload=capture_rows[0]["payload"],
            receive_or_capture_timestamp=str(int(NEW_C1_VENUE_TIME * 1000)),
        )
        assert g17_join.producer is not None

        pairs = build_s8_occupied_lane_pairs_v1(
            lane_state_root=ws / "lane_state",
            bound=handoff.bound_instrument,
        )

        ghv_reset = bind_golden_happy_vector_forensic_observability_session_v1(
            GoldenHappyVectorForensicObservabilitySessionV1(
                enabled=True,
                product_evidence_root=product_evidence,
                run_id="ghv-pre-ext-offline",
                continuous_run_id="ghv-pre-ext-offline",
                repository_sha=ORIGIN_SHA,
            )
        )
        syn_reset = bind_synthetic_enter_forensic_session_v1(
            build_synthetic_enter_forensic_session_v1(
                enabled=True,
                synthetic_side="enter_short",
                inject_cycle_index=1,
                product_evidence_root=product_evidence,
                continuous_run_id="ghv-pre-ext-offline",
            )
        )
        try:
            runner = make_n1_occupied_lane_s5_runner_v1(
                composed_pairs=pairs,
                g17_producers={"LANE_1": g17_join.producer},
                cycle_id_prefix_base="ghv-pre-ext-offline",
                forensic_observability_enabled=True,
                synthetic_enter_forensic_enabled=True,
                fresh_pretrade_get_transport=fresh_transport,
                cap24_productivity_root=prod,
            )
            auth = CurrentProductiveGovernedCycleAuthorizationV1(
                cycle_owner_go=RUNTIME_OWNER_GO,
                get_owner_go=GET_OWNER_GO,
                eg_owner_go=EG_OWNER_GO,
                t2_owner_go=T2_RUNTIME_OWNER_GO,
                occupancy_owner_go=OCCUPANCY_OWNER_GO,
                native_id=native_id,
                bar="1m",
                expected_cursor_floor=CURSOR_FLOOR,
            )
            result = runner(
                authorization=auth,
                origin_main_sha=_origin_main_sha(),
                cursor_store_root=Path(pairs["LANE_1"][0].lane_state_root),
                lock_root=ws / "lock",
                evidence_root=s5_root,
                candles_payload=candles,
                mark_price_payload=mark,
                index_tickers_payload=index,
                occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
            )
        finally:
            reset_synthetic_enter_forensic_session_v1(syn_reset)
            reset_golden_happy_vector_forensic_observability_session_v1(ghv_reset)

        syn_path = s5_root / "synthetic_enter_forensic_cycle_v1.json"
        assert syn_path.is_file(), "Synthetic overlay evidence required"
        syn_payload = json.loads(syn_path.read_text(encoding="utf-8"))
        assert syn_payload.get("synthetic_enter") is True
        assert syn_payload.get("synthetic_side") == "enter_short"
        assert syn_payload.get("selected_side_after_overlay") == "short"
        assert syn_payload.get("synthetic_injection_point") == INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1

        assert result.t2_consumed is True
        assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
        assert result.decision_result == "EXECUTABLE_VENUE_PLAN_BOUND"
        assert result.decision_execution_eligible == "true"
        assert result.venue_plan_status == "BOUND"
        assert result.post_count == 0
        assert result.permit_created is False
        assert result.final_order_envelope is not None

        safety = getattr(
            getattr(result, "final_order_envelope", None),
            "envelope_id",
            None,
        )
        assert safety

        ledger_path = s5_root / "governed_cycle_orchestrator_ledger_v1.json"
        assert ledger_path.is_file()
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        assert str(ledger.get("K1_PERMIT_CREATED", "false")).lower() == "false"
        assert str(ledger.get("K1_POST_COUNT", "0")) in {"0", ""}

    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_synthetic_overlay_rebinds_stale_observe_safety_for_venue_plan() -> None:
    """After overlay, typed safety must not retain observe-path ENTER blocks."""
    from tests.ops.test_current_productive_synthetic_enter_forensic_v1 import (
        _observe_replay_from_enter_fixture,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
        maybe_apply_synthetic_enter_forensic_overlay_v1,
    )
    from trading.master_v2.replay_execution_safety_contract_v1 import (
        typed_post_29q_consumption_guard_blocks_enter_v1,
        typed_pre_29q_entry_blocked_v1,
    )

    tmp = Path(tempfile.mkdtemp())
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp,
        continuous_run_id="safety-rebind",
    )
    reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            _observe_replay_from_enter_fixture(),
            cycle_index=1,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(reset)
    assert overlay.applied is True
    ts = overlay.replay.replay_execution_safety
    assert ts is not None
    assert typed_pre_29q_entry_blocked_v1(ts) is False
    assert typed_post_29q_consumption_guard_blocks_enter_v1(ts) is False


@pytest.mark.skipif(
    not (REPO_ROOT / LANE_RUNTIME_REL / "lane_state").is_dir(),
    reason="GHV lane runtime snapshot not present",
)
def test_missing_fresh_pretrade_transport_fail_closed_before_pre_external() -> None:
    """Without fresh-pretrade GET carrier, synthetic path must not reach PRE_EXTERNAL."""
    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv_witness
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
        productive_auth_free_flat_occupancy_payloads_v1,
    )

    ws = Path(tempfile.mkdtemp(prefix="ghv_pre_ext_neg_"))
    try:
        runtime_root = REPO_ROOT / LANE_RUNTIME_REL
        shutil.copytree(runtime_root / "lane_state", ws / "lane_state")
        shutil.copytree(runtime_root / "productivity", ws / "productivity")
        product_evidence = ws / "product_evidence"
        product_evidence.mkdir()
        s5_root = product_evidence / "cycles" / "c1" / "s5"
        s5_root.mkdir(parents=True)
        (product_evidence / "cycles" / "c1" / "s5_cycle_authorization_v1.json").write_text(
            json.dumps({"cycle_index": 1}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        capture_rows = ghv_witness._load_jsonl(REPO_ROOT / GHV_CAPTURE_REL)
        candles = _candles(last_ts_ms=int(NEW_C1_VENUE_TIME * 1000))
        prod = ws / "productivity"
        manifest = json.loads(
            (prod / "cap24_selection_state_publish_manifest_v1.json").read_text(encoding="utf-8")
        )
        sel = load_and_validate_selection_v1(
            prod / "runtime_state/selection", require_manifest=True
        )
        binding_epoch = resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-02T03:36:15Z",
        )
        handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=str(manifest.get("repository_sha") or ORIGIN_SHA),
            binding_epoch=binding_epoch,
        )
        native_id = str(handoff.bound_instrument.venue_native_id)
        mark = okx_public_mark_price_payload_v1(native_id=native_id, mark_px=21.035, index_px=21.03)
        g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
            evidence_store_root=ws / "g17",
            bound_instrument=handoff.bound_instrument,
            mark_candles_payload=capture_rows[0]["payload"],
            receive_or_capture_timestamp=str(int(NEW_C1_VENUE_TIME * 1000)),
        )
        pairs = build_s8_occupied_lane_pairs_v1(
            lane_state_root=ws / "lane_state",
            bound=handoff.bound_instrument,
        )
        syn_reset = bind_synthetic_enter_forensic_session_v1(
            build_synthetic_enter_forensic_session_v1(
                enabled=True,
                synthetic_side="enter_short",
                inject_cycle_index=1,
                product_evidence_root=product_evidence,
                continuous_run_id="ghv-pre-ext-neg",
            )
        )
        try:
            runner = make_n1_occupied_lane_s5_runner_v1(
                composed_pairs=pairs,
                g17_producers={"LANE_1": g17_join.producer},
                cycle_id_prefix_base="ghv-pre-ext-neg",
                synthetic_enter_forensic_enabled=True,
                fresh_pretrade_get_transport=None,
            )
            auth = CurrentProductiveGovernedCycleAuthorizationV1(
                cycle_owner_go=RUNTIME_OWNER_GO,
                get_owner_go=GET_OWNER_GO,
                eg_owner_go=EG_OWNER_GO,
                t2_owner_go=T2_RUNTIME_OWNER_GO,
                occupancy_owner_go=OCCUPANCY_OWNER_GO,
                native_id=native_id,
                bar="1m",
                expected_cursor_floor=CURSOR_FLOOR,
            )
            result = runner(
                authorization=auth,
                origin_main_sha=ORIGIN_SHA,
                cursor_store_root=Path(pairs["LANE_1"][0].lane_state_root),
                lock_root=ws / "lock",
                evidence_root=s5_root,
                candles_payload=candles,
                mark_price_payload=mark,
                index_tickers_payload={
                    "code": "0",
                    "data": [{"instId": native_id, "idxPx": "21.03", "ts": "0"}],
                },
                occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
            )
        finally:
            reset_synthetic_enter_forensic_session_v1(syn_reset)

        assert result.disposition != DISPOSITION_PRE_EXTERNAL_EFFECT
        assert result.post_count == 0
    finally:
        shutil.rmtree(ws, ignore_errors=True)
