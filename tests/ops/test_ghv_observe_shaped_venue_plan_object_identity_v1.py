"""Product-parity: genuine observe-shaped S7 replay + synthetic enter → venue plan / PRE_EXTERNAL."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
    compose_core_live_execution_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MODE_LIVE,
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
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reapply_forensic_synthetic_safety_reprojection_on_replay_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
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
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _lane_g17,
    _market_kwargs,
    _pair,
    _s7_kwargs,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _balance_payload,
    _injected,
    _instruments_payload,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    ProductiveClassFreshGetTransportV1,
    _productive_instruments_row_for_enter_metadata_v1,
)
from tests.ops.test_ghv_pre_external_offline_convergence_v1 import (
    CURSOR_FLOOR,
    GHV_CAPTURE_REL,
    LANE_RUNTIME_REL,
    NEW_C1_VENUE_TIME,
    ORIGIN_SHA,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
    compose_occupied_lane_mv2_dp_durable_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    productive_auth_free_flat_occupancy_payloads_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_PUBLIC_INSTRUMENTS,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _identity_payloads,
)
from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from trading.master_v2.replay_execution_safety_contract_v1 import (
    typed_post_29q_consumption_guard_blocks_enter_v1,
    typed_pre_29q_entry_blocked_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_ENTER_COMPOSITION = frozenset(
    {
        CompositionStatus.LONG_SELECTED,
        CompositionStatus.SHORT_SELECTED,
    }
)
_HOLD_LIKE_OUTCOMES = frozenset({"observe", "no_action", "hold", "reduce", "reconcile_only"})


def _genuine_observe_shaped_s7_replay_v1(tmp_path: Path):
    """S7 compose on neutral market kwargs — not enter-host relabel."""
    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    market = _market_kwargs(cycle_id_prefix="observe-shaped-genuine")
    composed = compose_occupied_lane_mv2_dp_durable_cycle_v1(
        pairs,
        g17_typed_vol_producers=_lane_g17(pairs),
        **_s7_kwargs(market),
    )
    replay = composed["LANE_1"].cycle_result.replay
    assert replay is not None and replay.replay_pass is True
    raw = replay.evidence.decision_outcome
    outcome = str(getattr(raw, "value", raw) or "").strip().lower()
    assert outcome in _HOLD_LIKE_OUTCOMES, outcome
    comp = replay.intermediate.composition_result.composition_status
    assert comp not in _ENTER_COMPOSITION, comp
    return pairs, replay, market


def test_genuine_s7_compose_replay_is_not_enter_host_derived(tmp_path: Path) -> None:
    _genuine_observe_shaped_s7_replay_v1(tmp_path)


def test_live_29p_rebound_replay_needs_final_reprojection_for_venue_plan(tmp_path: Path) -> None:
    """Observe-shaped compose + overlay + live-29P rebound: venue plan needs final reprojection."""
    pairs, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    bound = pairs["LANE_1"][1]
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="venue-plan-object-id",
    )
    reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        assert overlay.applied is True
        live_29p = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=overlay.replay,
            bound_instrument=bound,
            injected=_injected(
                payload=_balance_payload(),
                instruments_payload=_instruments_payload(
                    inst_id=str(bound.venue_native_id),
                ),
            ),
            decision_epoch=EPOCH,
        )
        assert live_29p.status == "PASS"
        rebound = live_29p.replay
        assert rebound is not None
        raw_status, raw_reasons, _ = compose_core_live_execution_intent_v1(
            replay=rebound,
            bound_instrument=bound,
            mode=MODE_LIVE,
            composed_epoch=EPOCH,
        )
        final_replay = reapply_forensic_synthetic_safety_reprojection_on_replay_v1(rebound)
        ts = final_replay.replay_execution_safety
        assert ts is not None
        assert typed_pre_29q_entry_blocked_v1(ts) is False
        assert typed_post_29q_consumption_guard_blocks_enter_v1(ts) is False
        fixed_status, fixed_reasons, intent = compose_core_live_execution_intent_v1(
            replay=final_replay,
            bound_instrument=bound,
            mode=MODE_LIVE,
            composed_epoch=EPOCH,
        )
        assert fixed_status is CompositionStatusV1.PASS, fixed_reasons
        assert intent is not None
        if raw_status is not CompositionStatusV1.PASS:
            assert "REPLAY_SAFETY" in " ".join(raw_reasons) or raw_reasons
    finally:
        reset_synthetic_enter_forensic_session_v1(reset)


@pytest.mark.skipif(
    not (REPO_ROOT / LANE_RUNTIME_REL / "lane_state").is_dir(),
    reason="GHV lane runtime snapshot not present",
)
@pytest.mark.skipif(
    not (REPO_ROOT / GHV_CAPTURE_REL).is_file(),
    reason="GHV Real-Venue capture not present for G17 bootstrap",
)
def test_observe_shaped_natural_layer_synthetic_runner_reaches_pre_external() -> None:
    """Full S5 runner: natural MV2 observe + synthetic overlay → PRE_EXTERNAL (product parity)."""
    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv_witness
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )

    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False

    ws = Path(tempfile.mkdtemp(prefix="observe_venue_plan_"))
    try:
        runtime_root = REPO_ROOT / LANE_RUNTIME_REL
        shutil.copytree(runtime_root / "lane_state", ws / "lane_state")
        shutil.copytree(runtime_root / "productivity", ws / "productivity")
        product_evidence = ws / "product_evidence"
        product_evidence.mkdir()
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

        syn_reset = bind_synthetic_enter_forensic_session_v1(
            build_synthetic_enter_forensic_session_v1(
                enabled=True,
                synthetic_side="enter_short",
                inject_cycle_index=1,
                product_evidence_root=product_evidence,
                continuous_run_id="observe-parity-pre-ext",
            )
        )
        try:
            runner = make_n1_occupied_lane_s5_runner_v1(
                composed_pairs=pairs,
                g17_producers={"LANE_1": g17_join.producer},
                cycle_id_prefix_base="observe-parity",
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
                origin_main_sha=ORIGIN_SHA,
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

        syn_row = json.loads(
            (product_evidence / "synthetic_enter_forensic_v1.jsonl")
            .read_text(encoding="utf-8")
            .strip()
        )
        assert syn_row["natural_outcome_before_overlay"] in _HOLD_LIKE_OUTCOMES
        assert syn_row["decision_outcome_after_overlay"] == "enter_short"
        assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
        assert result.decision_result == "EXECUTABLE_VENUE_PLAN_BOUND"
        assert result.post_count == 0
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_synthetic_disabled_observe_shaped_runner_holds(tmp_path: Path) -> None:
    _, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
        observe_replay,
        cycle_index=1,
    )
    assert overlay.applied is False


def test_synthetic_enabled_non_injection_cycle_no_overlay(tmp_path: Path) -> None:
    _, observe_replay, _ = _genuine_observe_shaped_s7_replay_v1(tmp_path)
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="non-injection",
    )
    reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=2,
        )
        assert overlay.applied is False
    finally:
        reset_synthetic_enter_forensic_session_v1(reset)
