"""Regression: GHV + synthetic forensic cycle-1 T2 must consume (no compose kwarg leak)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FAILING_LANE_RUNTIME_REL = (
    "runtime/current_productive/synthetic_enter_ghv_forward_backward_adjudication_v1/"
    "20261002T033614Z"
)
WORKING_GHV_CAPTURE_REL = (
    "evidence/ops/post_pr7005_current_golden_happy_vector_natural_enter_reproof_v1/"
    "20261002T025205Z/natural_market_data_get_capture_v1.jsonl"
)
ORIGIN_SHA = "9e6c2b31862fb3bc4e3b302cdaee979d1941ca8e"
CURSOR_FLOOR = 1790912400.0
NEW_C1_VENUE_TIME = 1790912460.0


@pytest.mark.skipif(
    not (REPO_ROOT / FAILING_LANE_RUNTIME_REL / "lane_state").is_dir(),
    reason="Failing GHV+synthetic product lane snapshot not present",
)
@pytest.mark.skipif(
    not (REPO_ROOT / WORKING_GHV_CAPTURE_REL).is_file(),
    reason="Working GHV Real-Venue capture not present for G17 bootstrap",
)
def test_cycle1_ghv_and_synthetic_forensic_t2_consumed(tmp_path: Path) -> None:
    """Reproduce product GHV+synthetic cycle-1 path; T2 must not fail with T2_CYCLE_EXCEPTION."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        STATUS_MISSING,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        CurrentProductiveGovernedCycleAuthorizationV1,
        EG_OWNER_GO,
        GET_OWNER_GO,
        OCCUPANCY_OWNER_GO,
        RUNTIME_OWNER_GO,
        T2_RUNTIME_OWNER_GO,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
        productive_auth_free_flat_occupancy_payloads_v1,
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

    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv_witness

    capture_rows = ghv_witness._load_jsonl(REPO_ROOT / WORKING_GHV_CAPTURE_REL)
    assert capture_rows, "capture must not be empty"
    candles = _candles(last_ts_ms=int(NEW_C1_VENUE_TIME * 1000))
    mark = okx_public_mark_price_payload_v1(
        native_id="KSTR-USDT-SWAP", mark_px=21.035, index_px=21.03
    )
    index = {
        "code": "0",
        "data": [
            {
                "instId": "KSTR-USDT-SWAP",
                "idxPx": "21.03",
                "ts": str(int(NEW_C1_VENUE_TIME * 1000)),
            }
        ],
    }

    def _run_s5(
        *, synthetic_enabled: bool, evidence_suffix: str
    ) -> tuple[object, dict[str, object] | None]:
        ws = Path(tempfile.mkdtemp(prefix=f"ghv_t2_cycle1_{evidence_suffix}_"))
        synthetic_payload: dict[str, object] | None = None
        try:
            runtime_root = REPO_ROOT / FAILING_LANE_RUNTIME_REL
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
            prod = ws / "productivity"
            manifest = json.loads(
                (prod / "cap24_selection_state_publish_manifest_v1.json").read_text(
                    encoding="utf-8"
                )
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
            pairs = build_s8_occupied_lane_pairs_v1(
                lane_state_root=ws / "lane_state",
                bound=handoff.bound_instrument,
            )
            g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
                evidence_store_root=ws / "g17",
                bound_instrument=handoff.bound_instrument,
                mark_candles_payload=capture_rows[0]["payload"],
                receive_or_capture_timestamp=str(int(NEW_C1_VENUE_TIME * 1000)),
            )
            assert g17_join.producer is not None
            ghv_reset = bind_golden_happy_vector_forensic_observability_session_v1(
                GoldenHappyVectorForensicObservabilitySessionV1(
                    enabled=True,
                    product_evidence_root=product_evidence,
                    run_id=f"ghv-t2-cycle1-{evidence_suffix}",
                    continuous_run_id=f"ghv-t2-cycle1-{evidence_suffix}",
                    repository_sha=ORIGIN_SHA,
                )
            )
            syn_reset = None
            if synthetic_enabled:
                syn_reset = bind_synthetic_enter_forensic_session_v1(
                    build_synthetic_enter_forensic_session_v1(
                        enabled=True,
                        synthetic_side="enter_short",
                        inject_cycle_index=1,
                        product_evidence_root=product_evidence,
                        continuous_run_id=f"ghv-t2-cycle1-{evidence_suffix}",
                    )
                )
            try:
                runner = make_n1_occupied_lane_s5_runner_v1(
                    composed_pairs=pairs,
                    g17_producers={"LANE_1": g17_join.producer},
                    cycle_id_prefix_base=f"ghv-t2-cycle1-{evidence_suffix}",
                    forensic_observability_enabled=True,
                    synthetic_enter_forensic_enabled=synthetic_enabled,
                )
                cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
                auth = CurrentProductiveGovernedCycleAuthorizationV1(
                    cycle_owner_go=RUNTIME_OWNER_GO,
                    get_owner_go=GET_OWNER_GO,
                    eg_owner_go=EG_OWNER_GO,
                    t2_owner_go=T2_RUNTIME_OWNER_GO,
                    occupancy_owner_go=OCCUPANCY_OWNER_GO,
                    native_id="KSTR-USDT-SWAP",
                    bar="1m",
                    expected_cursor_floor=CURSOR_FLOOR,
                )
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
                syn_path = s5_root / "synthetic_enter_forensic_cycle_v1.json"
                if syn_path.is_file():
                    synthetic_payload = json.loads(syn_path.read_text(encoding="utf-8"))
                return result, synthetic_payload
            finally:
                if syn_reset is not None:
                    reset_synthetic_enter_forensic_session_v1(syn_reset)
                reset_golden_happy_vector_forensic_observability_session_v1(ghv_reset)
        finally:
            shutil.rmtree(ws, ignore_errors=True)

    ghv_only_result, _ = _run_s5(synthetic_enabled=False, evidence_suffix="ghv_only")
    assert ghv_only_result.reason_code != "T2_CYCLE_EXCEPTION", (
        ghv_only_result.first_genuine_blocker
    )
    assert ghv_only_result.t2_consumed is True

    result, syn_payload = _run_s5(synthetic_enabled=True, evidence_suffix="ghv_synthetic")
    assert result.reason_code != "T2_CYCLE_EXCEPTION", result.first_genuine_blocker
    assert result.t2_consumed is True

    assert syn_payload is not None, "Synthetic overlay must persist cycle evidence"
    assert syn_payload.get("synthetic_enter") is True
    assert syn_payload.get("synthetic_side") == "enter_short"
    assert syn_payload.get("synthetic_injection_point") == INJECTION_POINT_LIVE_29P_JOIN_SEAM_V1
    assert syn_payload.get("natural_enter") is False

    assert result.first_genuine_blocker is not None
    assert "LIVE_29P" in str(result.first_genuine_blocker or "")
    assert result.first_genuine_blocker != "T2_CYCLE_EXCEPTION"
    assert str(result.first_genuine_blocker or "") != "HOLD"
    assert str(result.reason_code or "") != "HOLD"
    assert syn_payload.get("selected_side_after_overlay") == "short"
    _ = STATUS_MISSING
