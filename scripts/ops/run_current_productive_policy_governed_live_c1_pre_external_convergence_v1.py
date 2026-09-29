#!/usr/bin/env python3
"""Bounded productive policy-governed live Fresh-C1 continuous run → PRE_EXTERNAL only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _extract_latest_dpo_cycle2(lane: Path) -> dict[str, str]:
    ddo = lane / "LANE_1/ddo_learning_capture_v1.jsonl"
    out: dict[str, str] = {}
    if not ddo.is_file():
        return out
    for line in ddo.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("record_type") != "double_play_entry_exit_observation":
            continue
        p = row.get("payload") or {}
        if ":cycle:2" not in str(p.get("cycle_id") or ""):
            continue
        canon = p.get("producer_canonical_payload") or {}
        out = {
            "decision_event_ref": str(p.get("decision_event_ref") or ""),
            "dpo_ref": str(p.get("record_id") or ""),
            "decision_outcome": str(canon.get("decision_outcome") or ""),
            "selected_side": str(canon.get("selected_side") or ""),
            "execution_eligible": str(canon.get("execution_eligible") or "").lower(),
        }
    return out


def _build_f1_m9_evaluator(*, ledger_root: Path) -> Any:
    from src.governance.current_productive_activation_policy_v1 import (
        RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    )
    from src.governance.f1_m9_productive_apply_ledger_v1 import (
        F1M9ProductiveApplyLedgerPathsV1,
        initialize_empty_revocation_ledger_v1,
    )
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
    )
    from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
        F1M9ThresholdValueAuthorizationLedgerPathsV1,
        initialize_empty_threshold_revocation_ledger_v1,
    )
    from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
        GovernedF1M9ThresholdConsumerWiringRequestV1,
        run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1,
    )
    from tests.governance.test_governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
        _bound_context,
    )
    from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
        _valid_estimate,
    )

    ledger_root.mkdir(parents=True, exist_ok=True)
    apply_rev = ledger_root / "apply_rev.jsonl"
    threshold_rev = ledger_root / "threshold_rev.jsonl"
    initialize_empty_revocation_ledger_v1(apply_rev)
    initialize_empty_threshold_revocation_ledger_v1(threshold_rev)
    continuation = run_governed_f1_m9_productive_runtime_threshold_consumer_wiring_continuation_v1(
        GovernedF1M9ThresholdConsumerWiringRequestV1(
            apply_ledger_paths=F1M9ProductiveApplyLedgerPathsV1(
                apply_ledger_path=ledger_root / "apply.jsonl",
                revocation_ledger_path=apply_rev,
            ),
            threshold_ledger_paths=F1M9ThresholdValueAuthorizationLedgerPathsV1(
                threshold_ledger_path=ledger_root / "threshold.jsonl",
                threshold_revocation_ledger_path=threshold_rev,
            ),
            repo_root=REPO_ROOT,
        )
    )
    if continuation.bound_seam_record is None:
        raise RuntimeError("F1_M9_BOUND_SEAM_MISSING")
    ctx, elig = _bound_context(_valid_estimate())

    def _eval(_cycle_index: int):
        return evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
            market_context=ctx,
            eligibility=elig,
            governed_seam_record=continuation.bound_seam_record,
            require_governed_seam=True,
            runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
            repo_root=REPO_ROOT,
        )

    return _eval


def _resolve_g17_producer(
    *,
    bound: Any,
    transport: Any,
    evidence_store: Path,
    observed_unix: float,
) -> dict[str, object]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1 import (
        prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_pt1m_mark_sample_adapter_v1 import (
        ENDPOINT_HISTORY_MARK_PRICE_CANDLES,
        mark_history_get_query_v1,
    )

    mark_history_endpoint = (
        f"{ENDPOINT_HISTORY_MARK_PRICE_CANDLES}?"
        f"{urlencode(mark_history_get_query_v1(venue_native_id=str(bound.venue_native_id or '')))}"
    )
    mark_history_result = transport.get(
        endpoint=mark_history_endpoint,
        auth_required=False,
        pretrade_decision_id=f"pre-external-wp-g17-{int(observed_unix)}",
    )
    if mark_history_result.get_performed is not True or mark_history_result.payload is None:
        raise RuntimeError("G17_MARK_HISTORY_GET_FAIL_CLOSED")
    g17_join = prepare_current_productive_g17_dk_mv2_typed_vol_hot_path_v1(
        evidence_store_root=evidence_store,
        bound_instrument=bound,
        mark_candles_payload=mark_history_result.payload,
        receive_or_capture_timestamp=str(int(float(observed_unix) * 1000)),
    )
    if g17_join.fail_closed or not g17_join.estimate_present or g17_join.producer is None:
        raise RuntimeError(
            "G17_TYPED_VOL_HOT_PATH_FAIL_CLOSED:" + (g17_join.reason_code or "ESTIMATE_ABSENT")
        )
    return {"LANE_1": g17_join.producer}


def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Policy-governed live Fresh-C1 continuous run (PRE_EXTERNAL terminal only)"
    )
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--lane-state-root", type=Path, required=True)
    parser.add_argument("--productivity-root", type=Path, required=True)
    parser.add_argument("--binding-epoch", default=None)
    parser.add_argument(
        "--wp-branch-evidence-run",
        action="store_true",
        help="Record execution at current HEAD while Owner-GO baseline stays origin/main",
    )
    args = parser.parse_args()

    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _cursor_floor_or_zero,
    )
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
        acquire_eea_universe_inventory_v1,
    )
    from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
        UrllibEeaPublicUniverseGetTransportV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        CONTINUOUS_RUN_AUTHORIZED,
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        HARD_CAP_MAX_CYCLES_PER_RUN,
        HARD_CAP_MAX_RUN_DURATION_SECONDS,
        RUNTIME_OWNER_GO,
        CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        PersistentNaturalEnterConvergenceError,
        build_s8_occupied_lane_pairs_v1,
        preflight_current_productive_persistent_natural_enter_v1,
        run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
        LiveFreshC1ContinuousObservationSourceV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
        FullCoreProductiveReadOnlyGetTransportV1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
        PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS,
        GitCurrentProductive29PRuntimeIntegrityBackendV1,
        assert_current_productive_29p_execution_identity_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
        execute_current_productive_cap24_selection_state_canonical_write_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
        mint_continuous_run_id_v1,
    )

    evidence_root = Path(args.evidence_root)
    lane_state_root = Path(args.lane_state_root)
    productivity_root = Path(args.productivity_root)
    for p in (evidence_root, lane_state_root, productivity_root):
        p.mkdir(parents=True, exist_ok=True)

    backend = GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=REPO_ROOT)
    baseline_sha = backend.resolve_origin_main_sha_v1()
    execution_head_sha = backend.resolve_head_sha_v1()
    if args.wp_branch_evidence_run:
        drift = backend.diff_origin_main_for_paths_v1(
            PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS
        )
        if drift.strip():
            out = {"status": "FAIL", "blocker": "PROTECTED_CHAIN_SURFACE_DRIFT"}
            print(json.dumps(out, sort_keys=True))
            return 2
    else:
        baseline_sha = assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=baseline_sha,
            integrity_backend=backend,
        )
        execution_head_sha = baseline_sha
    origin_sha = baseline_sha
    repository_sha = execution_head_sha
    decision_epoch = args.binding_epoch or _utc_iso()

    acq = acquire_eea_universe_inventory_v1(transport=UrllibEeaPublicUniverseGetTransportV1())
    if acq.ok is not True:
        out = {"status": "FAIL", "blocker": "EEA_UNIVERSE_ACQUISITION_FAIL"}
        print(json.dumps(out, sort_keys=True))
        return 2

    execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go="CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1",
        origin_main_sha=origin_sha,
        acquisition_result=acq,
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        allow_default_productivity_root=False,
        decision_epoch=decision_epoch,
        execution_integrity_backend=backend,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.cap24_runtime_binding_witness_epoch_v1 import (
        resolve_cap24_runtime_binding_witness_epoch_v1,
    )

    sel_root = productivity_root / "runtime_state" / "selection"
    sel_load = load_and_validate_selection_v1(sel_root, require_manifest=True)
    if sel_load.ok is not True or sel_load.selection is None:
        out = {"status": "FAIL", "blocker": "CAP23_SELECTION_LOAD_FAIL_CLOSED"}
        print(json.dumps(out, sort_keys=True))
        return 2
    binding_epoch = resolve_cap24_runtime_binding_witness_epoch_v1(
        selection=sel_load.selection,
        decision_epoch=decision_epoch,
    )
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
    )
    bound = handoff.bound_instrument
    native_id = str(bound.venue_native_id or "").strip()
    pre = preflight_current_productive_persistent_natural_enter_v1(
        productivity_root=productivity_root,
        lane_state_root=lane_state_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
        authorization_native_id=native_id,
    )
    if not pre.ok:
        out = {"status": "FAIL", "blocker": pre.reason_code, "preflight": pre.reason_code}
        print(json.dumps(out, sort_keys=True))
        return 2

    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=32)
    g17 = _resolve_g17_producer(
        bound=bound,
        transport=transport,
        evidence_store=evidence_root / "g17_hot_path",
        observed_unix=float(datetime.now(timezone.utc).timestamp()),
    )
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_state_root, bound=bound)
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    floor = _cursor_floor_or_zero(cursor_root)

    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id=native_id,
        bar="1m",
        expected_cursor_floor=float(floor),
        max_cycles_per_run=HARD_CAP_MAX_CYCLES_PER_RUN,
        max_run_duration_seconds=HARD_CAP_MAX_RUN_DURATION_SECONDS,
        wait_interval_seconds=5.0,
        max_wait_for_next_c1_seconds=60.0,
        stall_seconds=60.0,
    )
    run_id = mint_continuous_run_id_v1(auth)
    obs_source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor_root,
        evidence_root=evidence_root,
        run_id=run_id,
        native_id=native_id,
        transport=transport,
    )

    try:
        result = run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1(
            authorization=auth,
            origin_main_sha=origin_sha,
            lane_state_root=lane_state_root,
            bound=bound,
            g17_producers=g17,
            observation_source=obs_source,
            evidence_root=evidence_root,
            f1_m9_cycle_evaluator=_build_f1_m9_evaluator(ledger_root=evidence_root / "f1_m9"),
            repo_root=REPO_ROOT,
        )
    except PersistentNaturalEnterConvergenceError as exc:
        out = {
            "status": "FAIL",
            "blocker": exc.reason_code,
            "detail": exc.detail,
            "origin_main_sha": origin_sha,
        }
        print(json.dumps(out, sort_keys=True))
        return 2

    orch = result.orchestrator_result
    dpo = _extract_latest_dpo_cycle2(lane_state_root)
    outcome = str(dpo.get("decision_outcome") or "").lower()
    natural_pre_external = (
        orch.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
        and outcome in {"enter_long", "enter_short"}
        and str(dpo.get("execution_eligible") or "").lower() == "true"
    )

    fresh_c1_ledger = evidence_root / "fresh_c1_get_owner_go_consumptions_v1.jsonl"
    fresh_c1_count = 0
    if fresh_c1_ledger.is_file():
        fresh_c1_count = sum(
            1 for line in fresh_c1_ledger.read_text(encoding="utf-8").splitlines() if line.strip()
        )

    cycle_summaries = [
        {
            "cycle_index": rec.cycle_index,
            "s5_disposition": rec.s5_disposition,
            "c1_venue_event_time": rec.c1_venue_event_time,
        }
        for rec in orch.cycle_records
    ]
    pre_external_reached = orch.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    natural_enter = outcome in {"enter_long", "enter_short"}
    report = {
        "BASELINE_SHA": origin_sha,
        "EXECUTION_HEAD_SHA": execution_head_sha,
        "RUN_ID": run_id,
        "EVIDENCE_ROOT": str(evidence_root),
        "NATIVE_ID": native_id,
        "LIVE_PUBLIC_C1_GET_EXECUTED": str(obs_source.get_count > 0).lower(),
        "OWNER_GO_FRESH_C1_GET_CONSUMPTION_COUNT": fresh_c1_count,
        "CYCLE_COUNT": orch.cycles_completed,
        "TERMINAL_DISPOSITION": orch.disposition,
        "S5_TERMINAL_CLASS": orch.terminal_class,
        "FIRST_GENUINE_BLOCKER": orch.first_genuine_blocker,
        "NATURAL_PRE_EXTERNAL_REACHED": str(natural_pre_external).lower(),
        "PRE_EXTERNAL_REACHED": str(pre_external_reached).lower(),
        "NATURAL_ENTER_OBSERVED": str(natural_enter).lower(),
        "ENTER_SIDE": outcome if natural_enter else "",
        "S5_CYCLE_SUMMARIES": cycle_summaries,
        "DPO": dpo,
        "CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN": str(CONTINUOUS_RUN_AUTHORIZED).lower(),
        "POST_COUNT": orch.post_count,
        "PERMIT_CREATED": str(orch.permit_created).lower(),
        "EXTERNAL_EFFECT_COUNT": orch.external_effect_count,
        "GET_REQUEST_COUNT": transport.request_count,
    }
    (evidence_root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if natural_pre_external else 2


if __name__ == "__main__":
    raise SystemExit(_main())
