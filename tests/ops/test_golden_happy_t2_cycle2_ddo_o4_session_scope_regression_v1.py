"""Regression: Real-Venue GHV cycle-2 T2_CYCLE_EXCEPTION (O4 session mix in WP-A store)."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_REL = (
    "evidence/ops/golden_happy_vector_extended_natural_observation_budget_and_verification_v1/"
    "20261002T105800Z"
)
LANE_RUNTIME_REL = "runtime/current_productive/golden_happy_extended_obs_budget_v1/lane_state"
PRODUCTIVITY_RUNTIME_REL = (
    "runtime/current_productive/golden_happy_extended_obs_budget_v1/productivity"
)


@pytest.mark.skipif(
    not (REPO_ROOT / EVIDENCE_REL / "natural_market_data_get_capture_v1.jsonl").is_file(),
    reason="Captured Real-Venue evidence package not present in workspace",
)
@pytest.mark.skipif(
    not (REPO_ROOT / LANE_RUNTIME_REL).is_dir(),
    reason="Post-run lane persistence snapshot not present",
)
def test_cycle2_productive_s5_no_t2_cycle_exception_after_o4_session_scope() -> None:
    """Reproduce cycle-2 CAP-USDT-SWAP path offline; must not fail with T2_CYCLE_EXCEPTION."""
    import scripts.ops.run_golden_happy_natural_data_offline_witness_adjudication_v1 as ghv
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
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )

    evid = REPO_ROOT / EVIDENCE_REL
    rows = ghv._load_jsonl(evid / "natural_market_data_get_capture_v1.jsonl")
    by_poll = ghv._bundle_polls(rows, "c1b3e3574a023949")
    bundle = by_poll[14]
    candles, mark, index = (
        bundle["poll"]["payload"],
        bundle["mark"]["payload"],
        bundle["index"]["payload"],
    )

    ws = Path(tempfile.mkdtemp(prefix="ghv_t2_cycle2_regression_"))
    try:
        shutil.copytree(REPO_ROOT / LANE_RUNTIME_REL, ws / "lane_state")
        shutil.copytree(REPO_ROOT / PRODUCTIVITY_RUNTIME_REL, ws / "productivity")
        cursor_path = (
            ws / "lane_state/LANE_1/current_productive_sidestate_confirmation_cursor_v1.json"
        )
        cur = json.loads(cursor_path.read_text(encoding="utf-8"))

        def _set_venue_event_time(obj: object, val: float) -> None:
            if isinstance(obj, dict):
                for key, child in list(obj.items()):
                    if key == "venue_event_time":
                        obj[key] = val
                    else:
                        _set_venue_event_time(child, val)

        _set_venue_event_time(cur, 1790895600.0)
        cursor_path.write_text(json.dumps(cur, indent=2) + "\n", encoding="utf-8")

        prod = ws / "productivity"
        manifest_path = prod / "cap24_selection_state_publish_manifest_v1.json"
        prod_repo_sha = json.loads(manifest_path.read_text(encoding="utf-8")).get("repository_sha")
        sel = load_and_validate_selection_v1(
            prod / "runtime_state/selection", require_manifest=True
        )
        binding_epoch = resolve_cap24_runtime_binding_witness_epoch_v1(
            selection=sel.selection,
            decision_epoch="2026-10-01T21:33:35Z",
        )
        handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
            productivity_root=prod,
            repository_sha=str(prod_repo_sha),
            binding_epoch=binding_epoch,
        )
        pairs = build_s8_occupied_lane_pairs_v1(
            lane_state_root=ws / "lane_state",
            bound=handoff.bound_instrument,
        )
        g17_store = ws / "g17_hot_path"
        g17_store.mkdir()
        g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
            evidence_store_root=g17_store,
            bound_instrument=handoff.bound_instrument,
            mark_candles_payload=rows[0]["payload"],
            receive_or_capture_timestamp="1790895666368",
        )
        assert g17_join.producer is not None
        g17 = {"LANE_1": g17_join.producer}
        runner = make_n1_occupied_lane_s5_runner_v1(
            composed_pairs=pairs,
            g17_producers=g17,
            cycle_id_prefix_base="ghv-t2-cycle2-regression",
            forensic_observability_enabled=False,
        )
        cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
        ev_root = ws / "s5_evidence"
        ev_root.mkdir()
        auth = CurrentProductiveGovernedCycleAuthorizationV1(
            cycle_owner_go=RUNTIME_OWNER_GO,
            get_owner_go=GET_OWNER_GO,
            eg_owner_go=EG_OWNER_GO,
            t2_owner_go=T2_RUNTIME_OWNER_GO,
            occupancy_owner_go=OCCUPANCY_OWNER_GO,
            native_id="CAP-USDT-SWAP",
            bar="1m",
            expected_cursor_floor=1790895600.0,
        )
        result = runner(
            authorization=auth,
            origin_main_sha=str(prod_repo_sha),
            cursor_store_root=cursor_root,
            lock_root=cursor_root / ".governed_cycle_lock",
            evidence_root=ev_root,
            candles_payload=candles,
            mark_price_payload=mark,
            index_tickers_payload=index,
            occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
        )
        assert result.reason_code != "T2_CYCLE_EXCEPTION", result.first_genuine_blocker
        assert result.t2_consumed is True
    finally:
        shutil.rmtree(ws, ignore_errors=True)
