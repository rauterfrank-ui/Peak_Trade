"""Regression: S5 persistent natural-enter runner must wire LIVE-29P fresh GET evidence."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_MISSING,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    EG_OWNER_GO,
    GET_OWNER_GO,
    OCCUPANCY_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    productive_auth_free_flat_occupancy_payloads_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    build_s8_occupied_lane_pairs_v1,
    make_n1_occupied_lane_s5_runner_v1,
    resolve_live_29p_injected_for_productive_s5_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
    prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    reset_synthetic_enter_forensic_session_v1,
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
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    STATE_SELECTED_ACTIVE,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _EPOCH,
    _identity_payloads,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _productive_instruments_row_for_enter_metadata_v1,
)
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import _candles
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FAILING_LANE_RUNTIME_REL = (
    "runtime/current_productive/synthetic_enter_ghv_forward_backward_adjudication_v1/"
    "20261002T033614Z"
)
WORKING_GHV_CAPTURE_REL = (
    "evidence/ops/post_pr7005_current_golden_happy_vector_natural_enter_reproof_v1/"
    "20261002T025205Z/natural_market_data_get_capture_v1.jsonl"
)
ORIGIN_SHA = "95b0c7ad37027dfcb652239e26f8c14cc4c13db5"
NATIVE_ID = "KSTR-USDT-SWAP"
CURSOR_FLOOR = 1790912400.0
NEW_C1_VENUE_TIME = 1790912460.0


def _bound_kstr() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id="cap24-KSTR-USDT-SWAP",
        venue_native_id=NATIVE_ID,
        ranking_snapshot_id="rank-live29p-1",
        ranking_integrity_digest="rank-digest-live29p-1",
        universe_snapshot_id="uni-live29p-1",
        selection_id="sel-live29p-1",
        selection_integrity_digest="sel-digest-live29p-1",
        selection_state=STATE_SELECTED_ACTIVE,
        selected_future_count=1,
        max_positions_effective=MAX_POSITIONS_EFFECTIVE,
    )


class ProductiveClassFreshGetTransportV1(CountingInjectedFreshGetTransportV1):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.transport_class = TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET
        self.venue_live_contact = True


def _productive_transport(*, instrument_id: str = NATIVE_ID) -> ProductiveClassFreshGetTransportV1:
    payloads = dict(_identity_payloads(instrument_id=instrument_id))
    payloads[ENDPOINT_PUBLIC_INSTRUMENTS] = {
        "code": "0",
        "data": [_productive_instruments_row_for_enter_metadata_v1(instrument_id=instrument_id)],
    }
    return ProductiveClassFreshGetTransportV1(payloads=payloads)


def test_resolve_live_29p_injected_performs_get_and_trusted_present(tmp_path: Path) -> None:
    prod = write_cap21_productivity_root_for_inst_v1(tmp_path, venue_native_id=NATIVE_ID)
    transport = _productive_transport()
    injected = resolve_live_29p_injected_for_productive_s5_cycle_v1(
        bound=_bound_kstr(),
        fresh_pretrade_get_transport=transport,
        productivity_root=prod,
        decision_epoch=_EPOCH,
    )
    assert injected is not None
    assert injected.get_performed is True
    assert transport.get_call_count >= 1
    assert injected.fresh_pretrade_get_status == "TRUSTED_PRESENT"


def test_join_enter_without_injected_still_get_missing() -> None:
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
        EPOCH,
        _bound,
        _enter_replay,
    )
    from tests.ops.test_current_productive_synthetic_enter_forensic_v1 import (
        _host_enter_cycle,
    )

    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    join = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        injected=None,
        decision_epoch=EPOCH,
    )
    assert join.called is True
    assert join.get_count == 0
    assert join.status == STATUS_MISSING


@pytest.mark.skipif(
    not (REPO_ROOT / FAILING_LANE_RUNTIME_REL / "lane_state").is_dir(),
    reason="GHV+synthetic lane snapshot not present",
)
@pytest.mark.skipif(
    not (REPO_ROOT / WORKING_GHV_CAPTURE_REL).is_file(),
    reason="Working GHV capture not present",
)
def test_s5_runner_ghv_synthetic_wires_live_29p_get_evidence() -> None:
    """GHV + synthetic cycle-1: LIVE-29P join must receive injected GET (not GET_MISSING)."""
    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv_witness

    capture_rows = ghv_witness._load_jsonl(REPO_ROOT / WORKING_GHV_CAPTURE_REL)
    candles = _candles(last_ts_ms=int(NEW_C1_VENUE_TIME * 1000))
    mark = okx_public_mark_price_payload_v1(native_id=NATIVE_ID, mark_px=21.035, index_px=21.03)
    index = {
        "code": "0",
        "data": [
            {
                "instId": NATIVE_ID,
                "idxPx": "21.03",
                "ts": str(int(NEW_C1_VENUE_TIME * 1000)),
            }
        ],
    }
    ws = Path(tempfile.mkdtemp(prefix="live29p_get_wiring_"))
    try:
        runtime_root = REPO_ROOT / FAILING_LANE_RUNTIME_REL
        shutil.copytree(runtime_root / "lane_state", ws / "lane_state")
        shutil.copytree(runtime_root / "productivity", ws / "productivity")
        product_evidence = ws / "product_evidence"
        s5_root = product_evidence / "cycles" / "cycle1inst" / "s5"
        s5_root.mkdir(parents=True)
        (product_evidence / "cycles" / "cycle1inst" / "s5_cycle_authorization_v1.json").write_text(
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
        bound = handoff.bound_instrument
        pairs = build_s8_occupied_lane_pairs_v1(
            lane_state_root=ws / "lane_state",
            bound=bound,
        )
        g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
            evidence_store_root=ws / "g17",
            bound_instrument=bound,
            mark_candles_payload=capture_rows[0]["payload"],
            receive_or_capture_timestamp=str(int(NEW_C1_VENUE_TIME * 1000)),
        )
        assert g17_join.producer is not None
        transport = _productive_transport(instrument_id=str(bound.venue_native_id or NATIVE_ID))
        syn_reset = bind_synthetic_enter_forensic_session_v1(
            build_synthetic_enter_forensic_session_v1(
                enabled=True,
                synthetic_side="enter_short",
                inject_cycle_index=1,
                product_evidence_root=product_evidence,
                continuous_run_id="live29p-wiring-regression",
            )
        )
        try:
            runner = make_n1_occupied_lane_s5_runner_v1(
                composed_pairs=pairs,
                g17_producers={"LANE_1": g17_join.producer},
                cycle_id_prefix_base="live29p-wiring",
                forensic_observability_enabled=False,
                synthetic_enter_forensic_enabled=True,
                fresh_pretrade_get_transport=transport,
                cap24_productivity_root=prod,
            )
            auth = CurrentProductiveGovernedCycleAuthorizationV1(
                cycle_owner_go=RUNTIME_OWNER_GO,
                get_owner_go=GET_OWNER_GO,
                eg_owner_go=EG_OWNER_GO,
                t2_owner_go=T2_RUNTIME_OWNER_GO,
                occupancy_owner_go=OCCUPANCY_OWNER_GO,
                native_id=str(bound.venue_native_id or NATIVE_ID),
                bar="1m",
                expected_cursor_floor=CURSOR_FLOOR,
            )
            cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
            result = runner(
                authorization=auth,
                origin_main_sha=ORIGIN_SHA,
                cursor_store_root=cursor_root,
                lock_root=ws / "lock",
                evidence_root=s5_root,
                candles_payload=candles,
                mark_price_payload=mark,
                index_tickers_payload=index,
                occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
            )
        finally:
            reset_synthetic_enter_forensic_session_v1(syn_reset)

        assert result.t2_consumed is True
        assert result.reason_code != "T2_CYCLE_EXCEPTION"
        assert transport.get_call_count >= 1
        assert result.first_genuine_blocker != "LIVE_29P_GET_MISSING"
        assert (s5_root / "synthetic_enter_forensic_cycle_v1.json").is_file()
    finally:
        shutil.rmtree(ws, ignore_errors=True)
