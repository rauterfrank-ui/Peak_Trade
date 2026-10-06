#!/usr/bin/env python3
"""Bounded productive policy-governed live Fresh-C1 continuous run → PRE_EXTERNAL only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlencode

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_f1_m9_evaluator(
    *,
    ledger_root: Path,
    g17_producers: Mapping[str, object],
    bound: Any,
) -> Any:
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
    from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
        apply_current_productive_g17_typed_vol_cmc_bind_v1,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        BarFinalityStatus,
        CanonicalMarketContextV1,
        ClockTrustStatus,
        DataIntegrityStatus,
        FEATURE_CONTRACT_VERSION,
        WarmupStatus,
        with_computed_input_digest,
    )
    from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
        evaluate_typed_volatility_binding_eligibility_v1,
    )
    from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
        CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    )
    from trading.master_v2.double_play_futures_input import FuturesMarketType

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
    instrument_id = str(bound.instrument_id or "").strip()
    lane_producer = g17_producers.get("LANE_1")
    if lane_producer is not None and not isinstance(
        lane_producer, CanonicalVolatilityTypedRuntimeProducerScaffoldV1
    ):
        raise RuntimeError("F1_M9_G17_PRODUCER_TYPE_INVALID")

    def _gate_market_context_v1(*, cycle_index: int) -> CanonicalMarketContextV1:
        ts = _utc_iso()
        return with_computed_input_digest(
            CanonicalMarketContextV1(
                context_id=(
                    f"ctx-{instrument_id}-f1m9-gate-cycle{cycle_index}-"
                    "current-productive-pre-external-v1"
                ),
                instrument_id=instrument_id,
                market_type=FuturesMarketType.PERPETUAL,
                trading_epoch=1,
                market_event_time=ts,
                decision_time=ts,
                bar_interval="1m",
                bar_finality_status=BarFinalityStatus.FINALIZED,
                mark_price=0.0,
                index_price=0.0,
                best_bid=0.0,
                best_ask=0.0,
                spread=0.0,
                volume=0.0,
                open_interest=0.0,
                funding_rate=0.0,
                volatility_estimate=0.0,
                trend_feature_set={},
                momentum_feature_set={},
                liquidity_feature_set={},
                market_structure_feature_set={},
                data_integrity_status=DataIntegrityStatus.TRUSTED,
                clock_trust_status=ClockTrustStatus.TRUSTED,
                warmup_status=WarmupStatus.WARMUP_COMPLETE,
                feature_contract_version=FEATURE_CONTRACT_VERSION,
                input_digest="",
            )
        )

    def _eval(cycle_index: int):
        base_ctx = _gate_market_context_v1(cycle_index=cycle_index)
        bind_result = apply_current_productive_g17_typed_vol_cmc_bind_v1(
            base_ctx,
            producer=lane_producer,
        )
        ctx = bind_result.context
        elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
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
    parser.add_argument(
        "--enable-natural-market-data-capture-v1",
        action="store_true",
        help="Append-only capture of natural read-only GET payloads under evidence-root",
    )
    parser.add_argument(
        "--enable-golden-happy-vector-forensic-observability-v1",
        action="store_true",
        help=(
            "Forensic Golden Happy Vector observability: entry-state snapshot + "
            "directional signal_strength/threshold evidence (default off)"
        ),
    )
    parser.add_argument(
        "--enable-ghv-pre-external-runtime-flight-recorder-v1",
        action="store_true",
        help=(
            "Observation-only GHV PRE_EXTERNAL runtime flight recorder + continuation "
            "snapshot (default off; no trading authority)"
        ),
    )
    parser.add_argument(
        "--enable-ghv-system-wide-canary-surface-discovery-v1",
        action="store_true",
        help=(
            "Observation-only GHV system-wide Canary correlation + surface discovery "
            "(default off; CANARY_AUTHORITY=NONE)"
        ),
    )
    parser.add_argument(
        "--enable-scoped-top20-evaluation-residency-v1",
        action="store_true",
        help=(
            "Scoped productive Top20 evaluation residency after Cap2.2 persist "
            "(default off; requires --enable-cap23-residency-eligibility-gate-v1 for gate)"
        ),
    )
    parser.add_argument(
        "--enable-cap23-residency-eligibility-gate-v1",
        action="store_true",
        help=(
            "Scoped Cap2.3 read-only eligibility gate on EvaluationCompletionWitnessV1 "
            "(default off; no POST/external effect)"
        ),
    )
    parser.add_argument(
        "--enable-synthetic-enter-forensic-v1",
        action="store_true",
        help=(
            "Forensic-only synthetic ENTER overlay at LIVE-29P join seam (default off). "
            "Does not set NATURAL_ENTER_OBSERVED."
        ),
    )
    parser.add_argument(
        "--synthetic-enter-forensic-side",
        default="enter_short",
        choices=("enter_long", "enter_short"),
        help="Synthetic side when --enable-synthetic-enter-forensic-v1 (default enter_short)",
    )
    parser.add_argument(
        "--synthetic-enter-forensic-cycle-index",
        type=int,
        default=1,
        help="S6 cycle index for one-shot synthetic overlay (default 1)",
    )
    parser.add_argument(
        "--enable-forensic-executable-quantity-override-v1",
        action="store_true",
        help=(
            "Forensic-only: after real LIVE-29P sizing, inject executable quantity when "
            "blocked (requires synthetic + GHV forensic flags; default off)"
        ),
    )
    parser.add_argument(
        "--forensic-executable-quantity",
        default=None,
        help=(
            "Optional explicit positive forensic quantity (no productive default; "
            "requires --enable-forensic-executable-quantity-override-v1)"
        ),
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_continuous_observation_budget_v1 import (
        ContinuousObservationBudgetError,
        PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
        PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
        resolve_continuous_observation_budget_v1,
    )

    parser.add_argument(
        "--max-cycles",
        type=int,
        default=PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN,
        help=(
            f"Bounded S6 cycle cap for this run (default {PRODUCTIVE_DEFAULT_MAX_CYCLES_PER_RUN})"
        ),
    )
    parser.add_argument(
        "--max-run-duration-seconds",
        type=float,
        default=PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS,
        help=(
            "Bounded wall-clock run duration in seconds "
            f"(default {PRODUCTIVE_DEFAULT_MAX_RUN_DURATION_SECONDS})"
        ),
    )
    args = parser.parse_args()
    try:
        observation_budget = resolve_continuous_observation_budget_v1(
            max_cycles=int(args.max_cycles),
            max_run_duration_seconds=float(args.max_run_duration_seconds),
        )
    except ContinuousObservationBudgetError as exc:
        out = {
            "status": "FAIL",
            "blocker": exc.reason_code,
            "detail": exc.detail,
        }
        print(json.dumps(out, sort_keys=True))
        return 2

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

    from src.ops.top20_opportunity_evaluation_residency_v1.scoped_residency_integrated_evaluation_propagation_v1 import (
        build_m01_scoped_residency_cap24_propagation_handoff_v1,
    )

    residency_handoff = build_m01_scoped_residency_cap24_propagation_handoff_v1(
        enable_scoped_top20_evaluation_residency_v1=bool(
            args.enable_scoped_top20_evaluation_residency_v1
        ),
        enable_cap23_residency_eligibility_gate_v1=bool(
            args.enable_cap23_residency_eligibility_gate_v1
        ),
        repository_sha=repository_sha,
        repo_root=REPO_ROOT,
    )
    execute_current_productive_cap24_selection_state_canonical_write_v1(
        owner_go="CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITE_V1",
        origin_main_sha=origin_sha,
        acquisition_result=acq,
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        allow_default_productivity_root=False,
        decision_epoch=decision_epoch,
        execution_integrity_backend=backend,
        residency_runtime_config=residency_handoff.residency_runtime_config,
        cap23_residency_eligibility_gate=residency_handoff.cap23_residency_eligibility_gate,
        scoped_top20_evaluation_residency_v1=residency_handoff.scoped_top20_evaluation_residency_v1,
        scoped_residency_integrated_evaluation=(
            residency_handoff.scoped_residency_integrated_evaluation
        ),
        cap21_coalesce_repo_root=residency_handoff.cap21_coalesce_repo_root,
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

    from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_get_budget_contract_v1 import (
        compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1,
    )

    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane_state_root, bound=bound)
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    floor = _cursor_floor_or_zero(cursor_root)

    auth = CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id=native_id,
        bar="1m",
        expected_cursor_floor=float(floor),
        max_cycles_per_run=observation_budget.effective_max_cycles,
        max_run_duration_seconds=observation_budget.effective_max_run_duration_seconds,
        wait_interval_seconds=5.0,
        max_wait_for_next_c1_seconds=60.0,
        stall_seconds=60.0,
    )
    run_id = mint_continuous_run_id_v1(auth)
    max_request_count = (
        compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1(auth)
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1 import (
        GovernedLiveC1GetOnlyFreshPretradeTransportBindError,
        open_governed_live_c1_get_only_fresh_pretrade_transport_v1,
    )

    try:
        with open_governed_live_c1_get_only_fresh_pretrade_transport_v1(
            max_request_count=max_request_count,
        ) as (transport, credential_bind_proof):
            (evidence_root / "get_only_credential_transport_bind_proof_v1.json").write_text(
                json.dumps(credential_bind_proof, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            if args.enable_natural_market_data_capture_v1:
                from src.ops.full_core_live_path_composition_root_v1.productive_natural_market_data_capture_sink_v1 import (
                    wrap_productive_transport_with_natural_market_data_capture_v1,
                )

                transport = wrap_productive_transport_with_natural_market_data_capture_v1(
                    transport,
                    evidence_root=evidence_root,
                    run_id=run_id,
                    native_id=native_id,
                )
            g17 = _resolve_g17_producer(
                bound=bound,
                transport=transport,
                evidence_store=evidence_root / "g17_hot_path",
                observed_unix=float(datetime.now(timezone.utc).timestamp()),
            )
            obs_source = LiveFreshC1ContinuousObservationSourceV1(
                cursor_store_root=cursor_root,
                evidence_root=evidence_root,
                run_id=run_id,
                native_id=native_id,
                transport=transport,
            )
            from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.session_integration_v1 import (
                wrap_observation_source_for_pending_outcome_advance_v1,
            )

            obs_source = wrap_observation_source_for_pending_outcome_advance_v1(
                obs_source,
                lane_state_root=lane_state_root,
                evidence_root=evidence_root,
                canonical_instrument_id=str(bound.instrument_id or ""),
                native_id=native_id,
                repository_sha=origin_sha,
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
                    f1_m9_cycle_evaluator=_build_f1_m9_evaluator(
                        ledger_root=evidence_root / "f1_m9",
                        g17_producers=g17,
                        bound=bound,
                    ),
                    repo_root=REPO_ROOT,
                    enable_golden_happy_vector_forensic_observability_v1=(
                        args.enable_golden_happy_vector_forensic_observability_v1
                    ),
                    enable_ghv_pre_external_runtime_flight_recorder_v1=bool(
                        args.enable_ghv_pre_external_runtime_flight_recorder_v1
                    ),
                    enable_ghv_system_wide_canary_surface_discovery_v1=bool(
                        args.enable_ghv_system_wide_canary_surface_discovery_v1
                    ),
                    enable_synthetic_enter_forensic_v1=bool(
                        args.enable_synthetic_enter_forensic_v1
                    ),
                    synthetic_enter_forensic_side=str(args.synthetic_enter_forensic_side),
                    synthetic_enter_forensic_cycle_index=int(
                        args.synthetic_enter_forensic_cycle_index
                    ),
                    enable_forensic_executable_quantity_override_v1=bool(
                        args.enable_forensic_executable_quantity_override_v1
                    ),
                    forensic_executable_quantity=str(args.forensic_executable_quantity or ""),
                    selection_id=str(handoff.selection_id or ""),
                    binding_epoch=str(binding_epoch or ""),
                    cap24_reselection_performed=bool(handoff.reselection_performed),
                    fresh_pretrade_get_transport=transport,
                    cap24_productivity_root=productivity_root,
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
    except GovernedLiveC1GetOnlyFreshPretradeTransportBindError as exc:
        out = {
            "status": "FAIL",
            "blocker": "GET_ONLY_CREDENTIAL_TRANSPORT_BIND_FAIL_CLOSED",
            "detail": str(exc),
            "origin_main_sha": origin_sha,
        }
        print(json.dumps(out, sort_keys=True))
        return 2
    except Exception as exc:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1 import (
            CurrentProductiveK1OpaqueSigningHandleError,
        )

        if isinstance(exc, CurrentProductiveK1OpaqueSigningHandleError):
            out = {
                "status": "FAIL",
                "blocker": "K1_CREDENTIAL_ACQUISITION_FAIL_CLOSED",
                "detail": str(exc),
                "origin_main_sha": origin_sha,
            }
            print(json.dumps(out, sort_keys=True))
            return 2
        raise

    from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
        evaluate_natural_enter_reporting_v1,
    )

    orch = result.orchestrator_result
    reporting = evaluate_natural_enter_reporting_v1(
        cycle_records=orch.cycle_records,
        terminal_disposition=str(orch.disposition or ""),
        ddo_jsonl=lane_state_root / "LANE_1/ddo_learning_capture_v1.jsonl",
        lane_state_root=lane_state_root,
    )
    dpo = dict(reporting.dpo)
    outcome = str(dpo.get("decision_outcome") or "").lower()
    natural_pre_external = reporting.natural_pre_external_reached

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
    natural_enter = reporting.natural_enter_observed
    synthetic_summary_path = evidence_root / "synthetic_enter_forensic_summary_v1.json"
    synthetic_enter_observed = False
    synthetic_enter_count = 0
    if synthetic_summary_path.is_file():
        syn = json.loads(synthetic_summary_path.read_text(encoding="utf-8"))
        synthetic_enter_observed = bool(syn.get("synthetic_enter_observed"))
        synthetic_enter_count = int(syn.get("synthetic_enter_count") or 0)
    decision_timestamp_unix = 0.0
    decision_reference_price = 0.0
    if reporting.reporting_s5_cycle_index is not None:
        for rec in orch.cycle_records:
            if int(rec.cycle_index) == int(reporting.reporting_s5_cycle_index):
                decision_timestamp_unix = float(rec.c1_venue_event_time or 0.0)
                break
    trace_path = evidence_root / "golden_happy_scope_decision_trace_v1.jsonl"
    if trace_path.is_file():
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("master_v2_decision_outcome") or "").lower() in {
                "enter_long",
                "enter_short",
            }:
                decision_reference_price = float(row.get("decision_input_mark") or 0.0)
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.session_integration_v1 import (
        finalize_pre_external_session_pending_outcomes_v1,
    )

    pending_session = finalize_pre_external_session_pending_outcomes_v1(
        lane_state_root=lane_state_root,
        reporting=reporting,
        run_id=run_id,
        evidence_root=evidence_root,
        canonical_instrument_id=str(bound.instrument_id or ""),
        native_id=native_id,
        decision_timestamp_unix=decision_timestamp_unix,
        decision_reference_price=decision_reference_price,
        synthetic_enter_observed=synthetic_enter_observed,
        repository_sha=origin_sha,
    )
    report = {
        "BASELINE_SHA": origin_sha,
        "EXECUTION_HEAD_SHA": execution_head_sha,
        "REQUESTED_MAX_CYCLES": observation_budget.requested_max_cycles,
        "EFFECTIVE_MAX_CYCLES": observation_budget.effective_max_cycles,
        "REQUESTED_MAX_RUN_DURATION_SECONDS": (
            observation_budget.requested_max_run_duration_seconds
        ),
        "EFFECTIVE_MAX_RUN_DURATION_SECONDS": (
            observation_budget.effective_max_run_duration_seconds
        ),
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
        "SYNTHETIC_ENTER_OBSERVED": str(synthetic_enter_observed).lower(),
        "SYNTHETIC_ENTER_COUNT": synthetic_enter_count,
        "ENTER_SIDE": reporting.enter_side if natural_enter else "",
        "REPORTING_S5_CYCLE_INDEX": (
            ""
            if reporting.reporting_s5_cycle_index is None
            else str(reporting.reporting_s5_cycle_index)
        ),
        "REPORTING_S5_DISPOSITION": reporting.reporting_s5_disposition,
        "S5_CYCLE_SUMMARIES": cycle_summaries,
        "DPO": dpo,
        "CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN": str(CONTINUOUS_RUN_AUTHORIZED).lower(),
        "POST_COUNT": orch.post_count,
        "PERMIT_CREATED": str(orch.permit_created).lower(),
        "EXTERNAL_EFFECT_COUNT": orch.external_effect_count,
        "GET_REQUEST_COUNT": transport.request_count,
        "PENDING_OUTCOME_CREATED": str(pending_session.pending_created).lower(),
        "PENDING_OUTCOME_CREATION_REASON": pending_session.pending_creation_reason,
        "PENDING_OUTCOME_ID": pending_session.pending_outcome_id or "",
    }
    (evidence_root / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if natural_pre_external else 2


if __name__ == "__main__":
    raise SystemExit(_main())
