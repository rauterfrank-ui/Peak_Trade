"""Explicit synthetic inputs; functions invoke existing owners, never test functions."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.ops.test_bounded_offline_all_purpose_consumers_v1 import _profiles

HEAD = "1814ca5b24d1d3ab537683e340b3ab045ea51e62"
ROOT = Path(__file__).resolve().parents[2]


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def five_lane_episode(root, monkeypatch):
    from tests.ops import test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as f
    from tests.ops.test_current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        _g17_for_instruments,
    )
    from src.ops.economic_md_input_producer_v1.purpose_gateway_v1 import (
        PurposeBoundEconomicMdGatewayV1,
    )
    from src.ops.economic_md_input_producer_v1.producer_v1 import (
        produce_economic_md_input_snapshot_v1,
    )
    from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
        produce_ranking_feature_production_snapshot_v1,
    )

    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
    from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        _market_kwargs,
    )
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        ProductiveFullAutonomyCap24BindContextV1,
        run_productive_full_autonomy_n5_runtime_orchestrator_v1,
    )

    at = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp() - 600
    monkeypatch.setattr(f, "OBSERVED_UNIX", at)
    monkeypatch.setattr(f, "SOURCE_EVENT", str(round(at * 1000)))
    monkeypatch.setattr(f, "REPO_SHA", HEAD)
    observed = {}

    def features(universe):
        routes = {}
        now = int(f.OBSERVED_UNIX * 1000)
        for inst in universe["instruments"]:
            if inst["eligibility"]:
                routes[inst["venue_native_inst_id"]] = _profiles(
                    root / "facts",
                    canonical=inst["canonical_instrument_id"],
                    native=inst["venue_native_inst_id"],
                    now_ms=now,
                    last_ms=now // 60000 * 60000,
                )
        gateway = PurposeBoundEconomicMdGatewayV1(routes, now)
        economic = produce_economic_md_input_snapshot_v1(
            universe_snapshot=universe,
            public_md_source=gateway,
            collection_started_at_unix=f.OBSERVED_UNIX - 1,
            collection_completed_at_unix=f.OBSERVED_UNIX,
        )
        result = produce_ranking_feature_production_snapshot_v1(
            economic.snapshot, observed_age_seconds=0
        )
        assert result.instrument_count_feature_ready == 5
        observed.update(gateway=gateway, routes=routes, economic=economic, features=result)
        return result

    monkeypatch.setattr(f, "synthesize_ready_feature_production_snapshot_v1", features)
    natives = ["ETH-USDT-SWAP", "SOL-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    chain = f._persist_universe_and_ranking(root, f._five_rows())
    topology = root / "topology"
    topology.mkdir()
    membership = f._membership(chain["ranking"], [f._cid(chain["ranking"], n) for n in natives])
    payloads = {
        f"LANE_{i + 1}": observed["routes"][n]["TRADING"].trading_c1_v1(native_id=n)
        for i, n in enumerate(natives)
    }
    marks = {
        n: observed["routes"][n]["TRADING"].trading_c1_v1(native_id=n)["data"][-1][4]
        for n in natives
    }
    cap24 = ProductiveFullAutonomyCap24BindContextV1(
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=f._empty_portfolio(at),
        mark_price_by_native_id=marks,
        session_id="e6-five-lane",
        now_unix=at,
    )
    cycle = _market_kwargs(cycle_id_prefix="e6-five-lane", last_ts=at - 60)
    cycle.pop("origin_main_sha")
    cycle.update(
        observed_unix=at,
        mark_px=1020.0,
        index_px=1014.9,
        bid_px=1019.9,
        ask_px=1020.1,
        last_finalized_event_ts_unix=at - 60,
        candles_payload=None,
        candles_payload_by_lane=payloads,
        g17_typed_vol_producers=_g17_for_instruments(chain, natives, 5),
    )
    writer = f._held_writer(topology)
    try:
        result = run_productive_full_autonomy_n5_runtime_orchestrator_v1(
            membership=membership,
            ranking_snapshot=chain["ranking"],
            topology_state_root_base=topology,
            lane_assignment_writer=writer,
            cap24_bind=cap24,
            repository_sha=HEAD,
            producer_observed_at_unix=at,
            origin_main_sha="5d1c838c15369507c5247834db4dd0df25592169",
            target_cardinality=5,
            include_host_completion_rollup=True,
            **cycle,
        )
    finally:
        writer.release()
    assert len(result.lane_rollups) == 5
    assert result.completion_result.productive_runtime_cardinality == "5_JOINED"
    assert all(r.post_count == 0 and not r.permit_created for r in result.lane_rollups)
    assert len({r.cursor_store_root for r in result.lane_rollups}) == 5
    # Both ranking and C1 come from this shared fact store at this replay clock.
    # G17 and reconciliation remain separately declared explicit fixture ports.
    return result, observed


def entry_episode(root, bound):
    """Actual original Core ENTER with the selected Cap24 identity, then real owners."""
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _cycle,
        _produced_g17_producer,
    )
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        strong_uptrend_closes_v1,
        natural_enter_long_closes_v1,
    )
    from tests.ops.test_bounded_offline_original_entry_risk_join_v1 import _host_request
    from tests.ops.test_outer_entry_budget_policy_v1 import _injected, _balance_payload, Slot, join
    from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REUSED_BINDING_ACCOUNT_SCOPE as ACCOUNT,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import lane_bindings_v1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
        ProductiveFuturesAccountingSessionV1,
    )
    from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
        build_simulated_fill_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
        PositionEpisodeIdentityV1,
        PositionEpisodeScopeV1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        bind_simulated_accounting_episode_identity_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.risk_bound_simulated_entry_v1 import (
        create_risk_bound_simulated_episode_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        persist_current_productive_sidestate_confirmation_cursor_v1,
    )
    from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
    from tests.ops.test_simulated_accounting_entry_source_v1 import _args

    now = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
    producer = _produced_g17_producer(
        instrument_id=bound.instrument_id, venue_native_id=bound.venue_native_id
    )
    # Two native contracts fit the unchanged 25-USDC entry ceiling, allowing
    # two valid one-contract reductions without inventing fractional venue lots.
    path = strong_uptrend_closes_v1(base=100.0)
    origin = _cycle(
        cycle_id="e6-origin",
        bound_instrument=bound,
        g17_typed_vol_producer=producer,
        closes=path,
        mark_px=path[0],
        event_ts_unix=now - 180,
    )
    candidate = _cycle(
        cycle_id="e6-candidate",
        bound_instrument=bound,
        g17_typed_vol_producer=producer,
        incoming_cursor=origin.outgoing_cursor,
        closes=path,
        mark_px=path[-1],
        event_ts_unix=now - 120,
    )
    closes = natural_enter_long_closes_v1(path)
    cycle = _cycle(
        cycle_id="e6-enter",
        bound_instrument=bound,
        g17_typed_vol_producer=producer,
        incoming_cursor=candidate.outgoing_cursor,
        closes=closes,
        mark_px=closes[-1],
        event_ts_unix=now - 100,
    )
    assert cycle.decision_outcome == "enter_long" and cycle.replay.replay_pass
    host = _host(root / "budget", _fetch(uid=ACCOUNT), clock=lambda: now, expected_account=ACCOUNT)
    try:
        context = host.observe_v1({"LANE_1": bound})
        risk = _host_request(context, cycle.replay)
        epoch = lane_bindings_v1({"LANE_1": bound})["LANE_1"]["instrument_epoch"]
        inst = replace(
            risk.data.instruments[0],
            canonical_id=bound.instrument_id,
            native_id=bound.venue_native_id,
            instrument_epoch=epoch,
        )
        risk = replace(
            risk,
            canonical_id=bound.instrument_id,
            native_id=bound.venue_native_id,
            instrument_epoch=epoch,
            data=replace(risk.data, instruments=(inst,)),
        )
        joined = join(
            replay=cycle.replay,
            bound_instrument=bound,
            decision_epoch=EPOCH,
            injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
            portfolio_budget_owner=host.owner,
            portfolio_slot=Slot("LANE_1", str(cycle.replay.evidence.decision_id), "risk-entry"),
            host_budget_recovery=context,
            restrictive_risk=risk,
        )
        assert joined.status == "PASS", joined.reason_codes
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=joined.replay,
            bound_instrument=bound,
            session_id="e6",
            run_id="e6",
            composed_epoch=EPOCH,
            execution_mode="SHADOW",
        )
        assert status.value == "PASS", reasons
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan, admission_ref="e6-offline", provenance_ref="e6-offline", creation_epoch=EPOCH
        )
        rid = joined.portfolio_reservation_id
        host.owner.bind_execution_plan_v1(rid, envelope)
        accounting = ProductiveFuturesAccountingSessionV1(
            contract=_contract(bound.venue_native_id), initial_equity=D("999.676")
        )
        fill = build_simulated_fill_v1(
            fill_id="offline-envelope:" + envelope.envelope_digest,
            instrument_id=bound.venue_native_id,
            side=envelope.side.upper(),
            quantity=envelope.quantity,
            mark_price=str(cycle.replay.intermediate.market_context.mark_price),
            contract=accounting.contract,
            reduce_only=False,
            event_time_unix=now + 1,
        )
        accounting.apply_fill(fill)
        identity = PositionEpisodeIdentityV1(
            "LANE_1",
            bound.instrument_id,
            bound.venue_native_id,
            "unbound-opening",
            "long",
            PositionEpisodeScopeV1(ACCOUNT, "INTERNAL_SIMULATED_EXECUTION"),
        )
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=identity, opening_fill=fill
        )
        args = _args(root / "position", identity)
        args["repository_sha"] = HEAD
        episode, receipt = create_risk_bound_simulated_episode_v1(
            owner=host.owner,
            reservation_id=rid,
            envelope=envelope,
            session=accounting,
            fills=(fill,),
            **args,
        )
        cursor_root = root / "core"
        persist_current_productive_sidestate_confirmation_cursor_v1(
            cycle.outgoing_cursor, store_root=cursor_root
        )
        snapshot = host.owner.risk_snapshot_v1()
        return SimpleNamespace(
            cycle=cycle,
            bound=bound,
            episode=episode,
            receipt=receipt,
            accounting=accounting,
            fills=[fill],
            cursor_root=cursor_root,
            envelope=envelope,
            reservation_id=rid,
            risk_snapshot=snapshot,
            active_sum=str(host.owner.active_sum_v1()),
            now=now,
            args=args,
        )
    finally:
        host.close()


def outcome_episode(root, entry, *, interrupt=None):
    from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
        DdoCaptureBindingV0,
        SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        observe_producer_result_v0,
    )
    from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
    from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
        pending_decision_context_from_invocation_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
        create_explicit_offline_pending_v1,
        advance_explicit_offline_pending_v1,
        offline_return_target_v1,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_evidence_v1 import (
        mint_forecast_evidence_v1,
    )

    invocation = SimpleNamespace(bound_instrument=entry.bound, cycle_result=entry.cycle)
    context = pending_decision_context_from_invocation_v1(invocation)
    assert context is not None
    stamp = (
        datetime.fromtimestamp(context.decision_timestamp_unix, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    ledger = entry.cursor_root / "ddo_learning_capture_v1.jsonl"
    config_digest = hashlib.sha256(
        (ROOT / "config/ops/canonical_decision_runtime_config_v1.toml").read_bytes()
    ).hexdigest()
    captured = observe_producer_result_v0(
        DdoCaptureBindingV0(
            enabled=True, ledger_path=ledger, capture_scope_config_hash=config_digest
        ),
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=entry.cycle.replay.intermediate.entry_exit_decision,
        event_time_utc=stamp,
        correlation_id="ddo.corr.e6",
        cycle_id=context.cycle_id,
        repository_sha=HEAD,
    )
    assert captured["ok"]
    row = next(
        r
        for r in AppendOnlyDdoLedgerV0(ledger).read_all()
        if r["schema_name"] == "double_play_entry_exit_observation"
    )
    dpo = {
        k: str(v).lower() if isinstance(v, bool) else str(v)
        for k, v in row["producer_canonical_payload"].items()
    }
    dpo.update(
        dpo_ref=row["record_id"],
        decision_event_ref=row["decision_event_ref"],
        cycle_id=context.cycle_id,
    )
    target = offline_return_target_v1(context=context, n_bars=2, venue="okx")
    end = datetime.fromisoformat(
        target["return_end_close_time_utc"].replace("Z", "+00:00")
    ).timestamp()
    asof = end + 3602
    source = _profiles(
        root / "outcome-facts",
        canonical=context.instrument_id,
        native=context.native_id,
        now_ms=round(asof * 1000),
        last_ms=round((asof - 2) * 1000),
    )["OUTCOME"]
    forecast = mint_forecast_evidence_v1(
        information_set_ref="info.e6.synthetic",
        forecast_created_at_utc=stamp,
        outcome_horizon_end_utc=target["return_end_close_time_utc"],
        n_bars=2,
        bar_spec_ref=target["bar_spec_ref"],
        forecast_kind="RETURN_DISTRIBUTION_SUMMARY",
        probabilistic_payload={"mean_return": 0.02, "std_return": 0.1},
        market_state_refs=[entry.cycle.replay.intermediate.market_context.context_id],
        forecast_model_ref="model.e6.synthetic",
        support_disposition="SUFFICIENT_EVIDENCE",
        provenance={"source_class": "SYNTHETIC_OFFLINE", "measured_return_target_v1": target},
        selected_instrument_ref=target["instrument_ref"],
        decision_event_ref=dpo["decision_event_ref"],
    )
    job = create_explicit_offline_pending_v1(
        retention_root=root / "retained",
        source_lane_root=entry.cursor_root,
        source_ledger=ledger,
        context=context,
        dpo=dpo,
        source=source,
        source_class="SYNTHETIC_OFFLINE",
        forecast=forecast,
        account_identity=entry.episode.identity.account_scope.account_identity,
        venue="okx",
        n_bars=2,
        expires_at_unix=asof + 7200,
        retry_interval_seconds=1,
        max_attempts=10,
        max_retained_jobs=10,
        retained_bytes_backpressure_threshold=10000000,
    )
    early = advance_explicit_offline_pending_v1(
        root=job,
        as_of_unix=context.decision_timestamp_unix + 2,
        source=source.at_v1(round((context.decision_timestamp_unix + 2) * 1000)),
    )
    assert early["stage"] == "WAITING_HORIZON"
    if interrupt is not None:
        interrupt(job)
    done = advance_explicit_offline_pending_v1(root=job, as_of_unix=asof, source=source)
    assert done["stage"] == "INGESTED"
    return job, source, context, done


def research_episode(root, job):
    """Verified closed consumer admission + lineage, then actual native research.

    The outcome is an admission dependency. It is never relabeled as the research
    engine's return, fee gap, OOS result or a profitable learning signal.
    """
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
        read_explicit_offline_pending_v1,
    )
    from tests.backtest.test_parameter_sensitivity_split_observation_v1 import _inputs
    from tests.experiments.test_canonical_advanced_search_v1 import _identity_request, _request
    from src.experiments.canonical_advanced_search_v1 import (
        SearchSpaceV1,
        SearchAxisV1,
        build_canonical_advanced_search_v1,
        canonical_record_payload_v1,
    )
    from src.experiments.canonical_native_research_measurements_v1 import (
        native_research_input_hashes_v1,
        native_research_identity_sources_v1,
        NativeResearchExecutionContextV1,
        NativeResearchExperimentProviderV1,
    )
    from src.experiments.canonical_native_research_session_v1 import (
        NativeResearchExecutionArchiveV1,
        measure_native_research_champion_v1,
        run_native_research_session_step_v1,
    )
    from src.experiments.canonical_robustness_suite_v1 import (
        canonical_robustness_policy_v1,
        derive_robustness_policy_digest_v1,
    )
    from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
    from src.experiments.canonical_experiment_memory_store_v1 import (
        CanonicalExperimentMemoryStoreV1,
    )
    from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
    from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
    import platform
    from src.backtest.mv2_research_wiring_v1 import (
        STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1 as admission,
    )

    closed = read_explicit_offline_pending_v1(job)
    if closed["stage"] != "INGESTED" or closed["independent_sample_count"] != 1:
        raise ValueError("E6_RESEARCH_CLOSED_NUMERIC_CONSUMER_REQUIRED")
    capsule = json.loads((job / "capsule_v1.json").read_text())
    ack_sha = hashlib.sha256((job / "consumer_ack_v1.json").read_bytes()).hexdigest()
    lineage = "explicit-offline-consumer-ack:sha256:" + ack_sha
    instrument = capsule["context"]["instrument_id"]
    bars, cfg = _inputs()  # separately declared synthetic research dataset
    hashes = native_research_input_hashes_v1(bars, cfg)
    template = _identity_request(
        strategy_params=cfg["economic_evaluation_v1"]["strategy_params"],
        dataset_digest=hashes["dataset_sha256"],
        parent_lineage_ref=lineage,
        environment={
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        },
        **native_research_identity_sources_v1(
            cfg, instrument_id=instrument, bars=bars, instrument_admission_mode=admission
        ),
    )
    policy = dict(canonical_robustness_policy_v1())
    policy["oos_sharpe_collapse_ratio"] = 100.0  # explicit stricter study policy
    space = SearchSpaceV1(
        "e6-explicit-native",
        (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
    )
    initial = build_canonical_advanced_search_v1(
        _request(
            identity_template=template,
            budget=1,
            seed=template.seed,
            created_at="2026-09-18T12:00:00Z",
            search_space=space,
            robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
        )
    )
    horizon = {
        "start": bars.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": bars.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    champion = measure_native_research_champion_v1(
        candidate=next(c for c in initial["candidates"] if c["status"] == "PROPOSED"),
        bars=bars,
        cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        instrument_id=instrument,
        time_horizon=horizon,
        market_universe=("EXPLICIT_SYNTHETIC_OFFLINE",),
        robustness_policy=policy,
        created_at="2026-09-18T13:00:00Z",
        instrument_admission_mode=admission,
    )
    template = replace(template, seed=55)
    context = NativeResearchExecutionContextV1(
        identity_template=template,
        champion=champion.candidate,
        champion_measurements=champion.measurements,
        created_at="2026-09-18T15:00:00Z",
        time_horizon=horizon,
        market_universe=("EXPLICIT_SYNTHETIC_OFFLINE",),
        gap_dimensions=(RealityGapDimensionV1("fee", 0.01, 0.01, 0.005, "ratio"),),
        observed_surface="SHADOW",
        threshold_policy_digest=hashlib.sha256(
            b"EXPLICIT_SYNTHETIC_OFFLINE_E6_GAP_STUDY_POLICY"
        ).hexdigest(),
        robustness_policy=policy,
        instrument_admission_mode=admission,
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(root / "memory"),
        failure_memory_store=CanonicalFailureMemoryStoreV1(root / "failures"),
        reality_gap_store=CanonicalRealityGapStoreV1(root / "gaps"),
    )
    seen = []
    provider = NativeResearchExperimentProviderV1(
        bars, cfg, "ma_crossover", "v1", instrument, context, seen.append
    )
    request = _request(
        identity_template=template,
        budget=1,
        seed=55,
        created_at="2026-09-18T14:00:00Z",
        search_space=space,
        robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
    )
    archive = NativeResearchExecutionArchiveV1(root / "archive")

    def step(p, r, ids=()):
        # This check is deliberately before every provider/engine call and before
        # native original-memory preflight; the original job remains its owner.
        if (
            read_explicit_offline_pending_v1(job) != closed
            or hashlib.sha256((job / "consumer_ack_v1.json").read_bytes()).hexdigest() != ack_sha
        ):
            raise ValueError("E6_RESEARCH_ORIGINAL_CONSUMER_CHANGED")
        from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1

        return run_native_research_session_step_v1(
            search_request=r,
            provider=p,
            archive=archive,
            prior_artifact_ids=ids,
            provider_ref="NativeResearchExperimentProviderV1.EXPLICIT_E6_OFFLINE",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
            meta_created_at="2026-09-18T15:30:00Z" if ids else None,
            meta_policy=canonical_meta_learning_policy_v1() if ids else None,
        )

    first = step(provider, request)
    later_provider = replace(provider, context=replace(context, created_at="2026-09-18T17:00:00Z"))
    second = step(
        later_provider, replace(request, created_at="2026-09-18T16:00:00Z"), (first.artifact_id,)
    )
    assert len(seen) == 2 and all(x.receipt["engine_invocations"] == 4 for x in seen)
    assert [x.receipt["parameters"]["slow_window"] for x in seen] == [50, 100]
    result = {
        "outcome_job_id": closed["job_id"],
        "original_consumer_ack_sha256": ack_sha,
        "lineage_ref": lineage,
        "instrument_id": instrument,
        "admission_dependency": "VERIFIED_CLOSED_NUMERIC_CONSUMER",
        "first_artifact_id": first.artifact_id,
        "second_artifact_id": second.artifact_id,
        "archive_root": str(archive.root),
        "actual_measured_slow_windows": [50, 100],
        "native_candidate_engine_invocations": 8,
        "separate_champion_engine_invocations": 4,
        "measurements": [canonical_record_payload_v1(x.receipt) for x in seen],
        "gap_data_class": "EXPLICIT_SYNTHETIC_OFFLINE_NOT_OBSERVED_FEES",
        "outcome_scalar_used_as_research_score": False,
        "source_authenticated": False,
        "economic_quality": "BLOCKED",
        "productive_apply_authorized": False,
        "identity_provenance": "UNVERIFIED_EXPLICIT_FIXTURE_DECLARATIONS_NOT_CURRENT_TREE_CLEAN_PROOF",
    }
    dump(root / "research-witness.json", result)
    return result, archive, first, second, step, later_provider, request


def evaluate_current_episode_numbers(root, job, native_archive, artifact_id):
    """Rebind E5's explicit replay corpus to this episode's *actual* numeric owners."""
    from tests.evaluation.golden_vectors.test_bounded_required_domain_fanout_v1 import _inputs
    from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import (
        retain_native_research_packet_v1,
        retain_mi_packet_v1,
    )
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        build_research_execution_gvef_reference_v1,
    )
    from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
    from src.evaluation.golden_vectors.contracts.models import (
        DomainEvaluationContextV1,
        VectorManifestV1,
        contract_digest_hex,
    )
    from src.evaluation.golden_vectors.corpus.digest_v1 import (
        corpus_identity_digest_hex,
        vector_identity_digest_hex,
    )
    from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import (
        BoundContextEvidenceBuilderV1,
        DomainExecutionInputV1,
        requirement_for_input_v1,
        run_required_domain_fanout_v1,
    )

    plan, inputs, archive = _inputs(root)
    native = retain_native_research_packet_v1(
        archive, owner_root=native_archive.root, artifact_id=artifact_id
    )
    ack = json.loads((job / "consumer_ack_v1.json").read_text())
    mi = retain_mi_packet_v1(
        archive, owner_root=job / "mi_consumer", durable_evidence_id=ack["mi_durable_id"]
    )
    artifact = canonical_record_payload_v1(
        build_research_execution_gvef_reference_v1(
            native_archive.get(artifact_id), artifact_ref="execution.json"
        ).learning_artifact
    )
    for domain, numeric in (("self_learning", native), ("market_intelligence", mi)):
        entry = inputs[domain]
        raw = entry.context.model_dump(mode="json", by_alias=True)
        for row in raw["replay_trace"]["entries"]:
            if domain == "self_learning":
                row["learning_artifact"] = artifact
            else:
                row["mi_context_bundle"]["measured_calibration_artifact"] = numeric
        context = DomainEvaluationContextV1.model_validate(raw)
        folder = Path(context.run_manifest.corpus_manifest_ref)
        manifest = context.corpus_identity
        vector_path = folder / "vectors" / (manifest.vector_ids[0] + ".json")
        vector = VectorManifestV1.model_validate_json(vector_path.read_text())
        vector = vector.model_copy(
            update={
                "population_selector": vector.population_selector.model_copy(
                    update={"binding_digest": contract_digest_hex(context.replay_trace)}
                )
            }
        )
        manifest = manifest.model_copy(
            update={
                "corpus_digest": corpus_identity_digest_hex(
                    manifest,
                    vector_digests_by_id={vector.vector_id: vector_identity_digest_hex(vector)},
                )
            }
        )
        vector_path.write_text(vector.model_dump_json(by_alias=True))
        (folder / "corpus_manifest.json").write_text(manifest.model_dump_json(by_alias=True))
        context = context.model_copy(update={"corpus_identity": manifest})
        deps = replace(entry.dependencies, evidence_builder=BoundContextEvidenceBuilderV1(context))
        inputs[domain] = DomainExecutionInputV1(context, deps, (numeric,))
    requirements = tuple(
        requirement_for_input_v1(r.domain, r.vector_id, inputs[r.domain]) for r in plan.required
    )
    plan = replace(
        plan,
        change_id="E6-actual-closed-consumer-native-research-numeric-receipts",
        required=requirements,
    )
    key, result = run_required_domain_fanout_v1(
        plan=plan, inputs=inputs, archive=archive, economic_request={"claim": "natural usefulness"}
    )
    assert (
        result["mechanism_status"] == "PASS" and result["economic_quality"]["status"] == "BLOCKED"
    )
    dump(
        root / "e6-evaluation-witness.json",
        {
            "receipt_id": key,
            "archive_root": str(archive.root),
            "expected_plan": plan.to_dict_v1(),
            "native_artifact_id": artifact_id,
            "mi_artifact_id": ack["mi_durable_id"],
            "mechanism_status": result["mechanism_status"],
            "economic_quality": result["economic_quality"],
            "other_domain_replay_scope": "EXPLICIT_E5_FIXTURE_REPLAY_CONTRACTS_ONLY_NOT_FULL_EPISODE_EXECUTION",
        },
    )
    return key, archive, plan
