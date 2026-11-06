"""Production observation supplier: real engines and downstream robustness consumers."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.experiments.canonical_advanced_search_v1 import (
    build_canonical_advanced_search_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_native_research_measurements_v1 import (
    NativeResearchMeasurementError,
    native_research_input_hashes_v1,
    native_research_identity_sources_v1,
    measure_native_research_candidate_v1,
)
from src.experiments.canonical_search_candidate_research_execution_v1 import (
    run_search_candidate_research_execution_v1,
)
from tests.backtest.test_parameter_sensitivity_split_observation_v1 import _inputs
from tests.experiments.test_canonical_advanced_search_v1 import (
    _request,
    _identity_request,
    SearchSpaceV1,
    SearchAxisV1,
)
from tests.experiments.test_canonical_search_candidate_research_execution_v1 import (
    _provider,
    _proposed,
    AT,
)


def _case():
    bars, cfg = _inputs()
    hashes = native_research_input_hashes_v1(bars, cfg)
    template = _identity_request(
        strategy_params=dict(cfg["economic_evaluation_v1"]["strategy_params"]),
        dataset_digest=hashes["dataset_sha256"],
        **native_research_identity_sources_v1(cfg, instrument_id="inst-eth-usdt-perp", bars=bars),
    )
    request = _request(
        identity_template=template,
        budget=1,
        search_space=SearchSpaceV1(
            "native.measured.v1",
            (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
        ),
    )
    search = build_canonical_advanced_search_v1(request)
    return bars, cfg, hashes, template, search


def _measure(bars, cfg, hashes, candidate):
    return measure_native_research_candidate_v1(
        candidate=candidate,
        bars=bars,
        cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        expected_dataset_sha256=hashes["dataset_sha256"],
        expected_config_sha256=hashes["config_sha256"],
        instrument_id="inst-eth-usdt-perp",
    )


@pytest.fixture(scope="module")
def measured(tmp_path_factory):
    bars, cfg, hashes, template, search = _case()
    observed = _measure(bars, cfg, hashes, _proposed(search))
    horizon = {
        "start": bars.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": bars.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    provider = _provider(
        template,
        observations=observed.observations,
        horizon=horizon,
        universe=("TEST_ONLY_NATIVE_MEASURED",),
    )
    executed = run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=_proposed(search)["experiment_id"],
        created_at=AT,
        experiment_provider=provider,
        provider_ref="TEST_ONLY_NATIVE.production_measurement_supplier",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
    )
    from src.experiments.canonical_research_result_to_meta_input_v1 import (
        build_meta_learning_from_research_results_v1,
    )
    from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1

    later = build_meta_learning_from_research_results_v1(
        [executed.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    output = tmp_path_factory.mktemp("native_production_measurements")
    (output / "measurement_receipt.json").write_text(
        json.dumps(canonical_record_payload_v1(observed.receipt), indent=2, allow_nan=False) + "\n"
    )
    (output / "execution.json").write_text(
        json.dumps(canonical_record_payload_v1(executed.evidence), indent=2, allow_nan=False) + "\n"
    )
    (output / "later_meta.json").write_text(
        json.dumps(canonical_record_payload_v1(later), indent=2) + "\n"
    )
    (output / "bars.csv").write_bytes(bars.to_csv(float_format="%.17g").encode())
    (output / "cfg.canonical.json").write_text(
        json.dumps(cfg, sort_keys=True, separators=(",", ":"), allow_nan=False)
    )
    return observed, executed, bars, cfg, output


def test_four_actual_runs_use_full_path_returns_not_joined_split_resets(measured):
    result, _, bars, _, _ = measured
    assert result.receipt["engine_invocations"] == 4
    assert [x["split"] for x in result.receipt["runs"]] == [
        "full",
        "train",
        "validation",
        "holdout",
    ]
    full = result.receipt["runs"][0]
    assert (
        len(result.observations.robustness_observations["returns"]) == full["return_observations"]
    )
    assert len(full["equity"]) == len(bars) + 1
    assert (
        result.observations.metrics["engine_pre_funding_sharpe"]
        == full["statistics"]["sharpe"]["value"]
    )
    assert (
        result.observations.robustness_observations["split_metrics"]["holdout"]["sample_size"]
        == result.receipt["runs"][-1]["return_observations"]
    )


def test_actual_returns_reach_mc_bootstrap_rolling_and_crash_owners(measured):
    result, execution, _, _, _ = measured
    evidence = execution.next_meta_input.research_loop_record["robustness_evidence"]
    statuses = {x["test_id"]: x["status"] for x in evidence["test_results"]}
    for key in ("MONTE_CARLO", "BLOCK_BOOTSTRAP", "ROLLING_OOS", "CRASH_SCENARIOS"):
        assert statuses[key] in {"PASS", "FAIL"}, (key, statuses[key])
    assert evidence["aggregate_status"] != "PASS"
    assert (
        result.receipt["funding_effect_in_equity"] == "NOT_ESTABLISHED_BY_SIGNAL_OR_MODEL_BINDING"
    )
    assert result.receipt["funding_unit_signal_is_actual_quantity"] is False


def test_nonfinite_measurements_are_retained_as_missing_not_fake_numbers(measured):
    result = measured[0]
    assert any(
        m["status"] == "NONFINITE"
        for row in result.receipt["runs"]
        for m in row["statistics"].values()
    )
    for row in result.receipt["runs"]:
        for metric in row["statistics"].values():
            if metric["status"] == "NONFINITE":
                assert metric["value"] is None
    assert "parameter_stability" not in result.observations.metrics
    assert "funding_sensitivity" not in result.observations.metrics


@pytest.mark.parametrize("changed", ["data", "config", "params", "strategy", "dataset_identity"])
def test_binding_divergence_rejected_before_engine(monkeypatch, changed):
    bars, cfg, hashes, template, search = _case()
    candidate = canonical_record_payload_v1(_proposed(search))
    if changed == "data":
        bars.iloc[0, bars.columns.get_loc("close")] += 1
    if changed == "config":
        cfg["risk"]["risk_per_trade"] = 0.001
    if changed == "params":
        cfg["economic_evaluation_v1"]["strategy_params"]["slow_window"] = 100
        hashes = native_research_input_hashes_v1(bars, cfg)
    if changed == "strategy":
        template = replace(template, strategy_identity="other.v1")
        search = build_canonical_advanced_search_v1(
            _request(
                identity_template=template,
                budget=1,
                search_space=SearchSpaceV1(
                    "native.measured.v1",
                    (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
                ),
            )
        )
        candidate = _proposed(search)
    if changed == "dataset_identity":
        template = replace(template, dataset_digest="0" * 64)
        search = build_canonical_advanced_search_v1(
            _request(
                identity_template=template,
                budget=1,
                search_space=SearchSpaceV1(
                    "native.measured.v1",
                    (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
                ),
            )
        )
        candidate = _proposed(search)
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.run_mv2_research_backtest_wiring_v1",
        lambda *a, **kw: pytest.fail("no engine call permitted"),
    )
    with pytest.raises(NativeResearchMeasurementError):
        _measure(bars, cfg, hashes, candidate)


@pytest.mark.parametrize("bad_index", ["duplicate", "unsorted", "naive"])
def test_bad_time_axes_rejected_before_measurement(bad_index):
    bars, cfg, _, _, search = _case()
    if bad_index == "duplicate":
        bars = bars.iloc[[0, 0, *range(2, len(bars))]]
    elif bad_index == "unsorted":
        bars = bars.iloc[::-1]
    else:
        bars.index = bars.index.tz_localize(None)
    hashes = native_research_input_hashes_v1(bars, cfg)
    with pytest.raises(NativeResearchMeasurementError, match="ORDERED_UNIQUE"):
        _measure(bars, cfg, hashes, _proposed(search))


def test_input_frames_and_config_not_mutated(measured):
    _, _, bars, cfg, _ = measured
    original_bars, original_cfg = _inputs()
    assert bars.equals(original_bars)
    assert cfg == original_cfg


@pytest.mark.parametrize("field", ["fee", "risk", "funding", "cash"])
def test_changed_cost_risk_or_equity_cannot_keep_same_canonical_candidate(monkeypatch, field):
    bars, cfg, _, _, search = _case()
    if field == "fee":
        cfg["backtest"]["fee_bps"] += 1
    elif field == "risk":
        cfg["risk"]["risk_per_trade"] = 0.001
    elif field == "cash":
        cfg["backtest"]["initial_cash"] *= 2
    else:
        cfg["backtest"]["funding"] = {
            "bind": True,
            "model_version": "backtest_funding_perpetual_interval_v1",
        }
    hashes = native_research_input_hashes_v1(bars, cfg)
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.run_mv2_research_backtest_wiring_v1",
        lambda *a, **kw: pytest.fail("no engine call permitted"),
    )
    with pytest.raises(NativeResearchMeasurementError, match="CONFIG_SOURCE_MISMATCH"):
        _measure(bars, cfg, hashes, _proposed(search))


def test_model_binding_is_distinct_from_applied_quantity_cashflow(measured):
    import pandas as pd
    from src.backtest.funding_model_v1 import (
        compute_funding_drag_v1,
        default_funding_model_config_v1,
    )

    baseline, _, bars, cfg, output = measured
    bound_cfg = deepcopy(cfg)
    bound_cfg["backtest"]["funding"] = {
        "bind": True,
        "model_version": "backtest_funding_perpetual_interval_v1",
    }
    bindings = native_research_input_hashes_v1(bars, bound_cfg)
    template = _identity_request(
        strategy_params=bound_cfg["economic_evaluation_v1"]["strategy_params"],
        dataset_digest=bindings["dataset_sha256"],
        **native_research_identity_sources_v1(
            bound_cfg, instrument_id="inst-eth-usdt-perp", bars=bars
        ),
    )
    search = build_canonical_advanced_search_v1(
        _request(
            identity_template=template,
            budget=1,
            search_space=SearchSpaceV1(
                "native.measured.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
            ),
        )
    )
    bound = _measure(bars, bound_cfg, bindings, _proposed(search))
    old, new = baseline.receipt["runs"][0], bound.receipt["runs"][0]
    assert new["cost_binding"]["funding_model_version"] == "backtest_funding_perpetual_interval_v1"
    assert old["equity"] == new["equity"]
    assert old["mapped_signal_values"] == new["mapped_signal_values"]
    assert any(abs(q) != 1 for q in new["closed_trade_quantities"])
    proxy = compute_funding_drag_v1(
        bars=bars,
        position_series=pd.Series(new["mapped_signal_values"], index=bars.index),
        initial_equity=cfg["backtest"]["initial_cash"],
        config=default_funding_model_config_v1(),
        data_digest=bindings["dataset_sha256"],
    )
    held_at_payment = []
    for event in proxy.payment_events:
        for trade in new["closed_trade_intervals"]:
            if (
                pd.Timestamp(trade["entry_time"])
                < pd.Timestamp(event.timestamp)
                < pd.Timestamp(trade["exit_time"])
            ):
                held_at_payment.append(
                    {
                        "timestamp": event.timestamp,
                        "actual_quantity": trade["quantity"],
                        "mapped_signal_proxy": event.position_sign,
                        "funding_rate": event.funding_rate,
                    }
                )
    assert held_at_payment
    assert any(
        row["actual_quantity"] != 0 and row["mapped_signal_proxy"] == 0 and row["funding_rate"] != 0
        for row in held_at_payment
    )
    (output / "funding_binding_effect_probe.json").write_text(
        json.dumps(
            {
                "method": "Only funding config bound/unbound changed; same bars/params/risk/cash, distinct source-bound experiment identities",
                "model_status_when_bound": new["cost_binding"]["funding_model_version"],
                "full_equity_identical": True,
                "signals_identical": True,
                "actual_closed_trade_quantities": new["closed_trade_quantities"],
                "strictly_held_at_funding_timestamps": held_at_payment,
                "unit_signal_proxy_only": proxy.to_dict(),
                "actual_quantity_cashflow_applied_to_engine_equity_proven": False,
            },
            indent=2,
        )
        + "\n"
    )


def test_measured_supplier_later_meta_survives_gvef_reference_reload(measured):
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        build_research_execution_gvef_reference_v1,
        read_research_execution_gvef_reference_v1,
    )
    from src.experiments.canonical_research_result_to_meta_input_v1 import (
        build_meta_learning_from_research_results_v1,
    )
    from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1

    _, executed, _, _, output = measured
    reference = build_research_execution_gvef_reference_v1(
        executed, artifact_ref="measured_execution.canonical.json"
    )
    raw = reference.artifact_bytes
    (output / "measured_execution.canonical.json").write_bytes(raw)
    (output / "gvef_reference.json").write_text(
        json.dumps(canonical_record_payload_v1(reference.learning_artifact), indent=2) + "\n"
    )
    loaded = read_research_execution_gvef_reference_v1(
        reference.learning_artifact, artifact_bytes=raw
    )
    later = build_meta_learning_from_research_results_v1(
        [loaded.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert canonical_record_payload_v1(later) == json.loads(
        (output / "later_meta.json").read_text()
    )
    (output / "later_meta_after_reference_reload.json").write_text(
        json.dumps(canonical_record_payload_v1(later), indent=2) + "\n"
    )


@pytest.fixture(scope="module")
def regular_provider_case(measured):
    from src.experiments.canonical_native_research_measurements_v1 import (
        NativeResearchExecutionContextV1,
        NativeResearchExperimentProviderV1,
    )
    from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
    from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
    from src.experiments.canonical_robustness_suite_v1 import (
        canonical_robustness_policy_v1,
        derive_robustness_policy_digest_v1,
    )

    champion_measurements, _, bars, cfg, output = measured
    _, _, _, template, champion_search = _case()
    horizon = {
        "start": bars.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": bars.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    universe = ("TEST_ONLY_NATIVE_MEASURED",)
    champion = ComparisonCandidateV1(
        experiment_identity=_proposed(champion_search)["experiment_identity"],
        time_horizon=horizon,
        market_universe=universe,
    )
    template = replace(template, seed=55)
    policy = canonical_robustness_policy_v1()
    search = build_canonical_advanced_search_v1(
        _request(
            identity_template=template,
            budget=1,
            robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
            search_space=SearchSpaceV1(
                "native.measured.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
            ),
        )
    )
    # Explicit controlled context input; the provider never fabricates missing Shadow values.
    context = NativeResearchExecutionContextV1(
        identity_template=template,
        champion=champion,
        champion_measurements=champion_measurements,
        created_at=AT,
        time_horizon=horizon,
        market_universe=universe,
        gap_dimensions=(
            RealityGapDimensionV1(
                name="fee",
                expected=0.01,
                observed=0.02,
                threshold=0.005,
                unit="ratio",
            ),
        ),
        observed_surface="SHADOW",
        threshold_policy_digest="1" * 64,
        robustness_policy=policy,
    )
    observed = []
    provider = NativeResearchExperimentProviderV1(
        bars=bars,
        base_cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        instrument_id="inst-eth-usdt-perp",
        context=context,
        measurement_observer=observed.append,
    )
    executed = run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=_proposed(search)["experiment_id"],
        created_at=AT,
        experiment_provider=provider,
        provider_ref="NativeResearchExperimentProviderV1.TEST_ONLY_CONTEXT",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
    )
    (output / "regular_provider_execution.json").write_text(
        json.dumps(canonical_record_payload_v1(executed.evidence), indent=2) + "\n"
    )
    (output / "regular_provider_measurement.json").write_text(
        json.dumps(canonical_record_payload_v1(observed[0].receipt), indent=2) + "\n"
    )
    return provider, search, executed, observed


def test_regular_provider_executes_without_fixture_request_or_fixed_scores(
    regular_provider_case, measured
):
    _, search, executed, observed = regular_provider_case
    assert len(observed) == 1
    loop = executed.next_meta_input.research_loop_record
    scores = loop["challenger_report"]["scores"]
    assert (
        scores[loop["selected_experiment_id"]]
        == observed[0].observations.metrics["engine_pre_funding_sharpe"]
    )
    champion_score = measured[0].receipt["runs"][0]["statistics"]["sharpe"]["value"]
    assert scores[loop["champion_experiment_id"]] == champion_score
    assert (
        loop["experiment_record"]["hypothesis_fingerprint"]
        == _proposed(search)["hypothesis_fingerprint"]
    )


def test_regular_provider_does_not_invent_unavailable_gap_context(
    regular_provider_case, monkeypatch
):
    provider, search, _, _ = regular_provider_case
    broken = replace(provider, context=replace(provider.context, gap_dimensions=()))
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        lambda **kw: pytest.fail("no measurement before context admission"),
    )
    with pytest.raises(NativeResearchMeasurementError, match="REALITY_GAP_CONTEXT"):
        broken(_proposed(search))


def test_regular_provider_binds_search_and_actual_robustness_policy(
    regular_provider_case, monkeypatch
):
    provider, _, _, _ = regular_provider_case
    bad = build_canonical_advanced_search_v1(
        _request(
            identity_template=provider.context.identity_template,
            budget=1,
            search_space=SearchSpaceV1(
                "native.measured.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
            ),
        )
    )
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        lambda **kw: pytest.fail("policy mismatch must reject before measurement"),
    )
    with pytest.raises(NativeResearchMeasurementError, match="POLICY_FINGERPRINT"):
        provider(_proposed(bad))


def test_regular_provider_rejects_stale_champion_measurement(regular_provider_case):
    provider, search, _, _ = regular_provider_case
    receipt = canonical_record_payload_v1(provider.context.champion_measurements.receipt)
    receipt["runs"][0]["statistics"]["sharpe"]["value"] = 999
    wrong = replace(provider.context.champion_measurements, receipt=receipt)
    provider = replace(provider, context=replace(provider.context, champion_measurements=wrong))
    with pytest.raises(NativeResearchMeasurementError, match="CHAMPION_MEASUREMENT_DIGEST"):
        provider(_proposed(search))


def test_regular_provider_rejects_conflicting_fixed_config_before_measurement(
    regular_provider_case, monkeypatch
):
    provider, search, _, _ = regular_provider_case
    cfg = deepcopy(provider.base_cfg)
    cfg["economic_evaluation_v1"]["strategy_params"]["slow_window"] = 99
    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        lambda **kw: pytest.fail("fixed config conflict must reject before measurement"),
    )
    with pytest.raises(NativeResearchMeasurementError, match="BASE_TEMPLATE_CONFIG_PARAMETER"):
        replace(provider, base_cfg=cfg)(_proposed(search))


def test_meta_selected_next_region_runs_through_regular_provider_and_later_meta(
    regular_provider_case, measured
):
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        run_research_feedback_next_execution_v1,
    )
    from src.experiments.canonical_research_result_to_meta_input_v1 import (
        ResearchResultMetaInputV1,
        build_meta_learning_from_research_results_v1,
    )
    from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
    from src.experiments.canonical_automated_offline_research_loop_v1 import (
        run_canonical_automated_offline_research_loop_v1,
        OfflineExperimentObservationsV1,
    )
    from src.experiments.canonical_robustness_suite_v1 import (
        canonical_robustness_policy_v1,
        derive_robustness_policy_digest_v1,
    )
    from tests.experiments.test_canonical_research_result_to_meta_input_v1 import (
        _source,
        _stats,
        _HORIZON,
        _UNIVERSE,
    )

    policy = canonical_robustness_policy_v1()
    train = [0.002, -0.001, 0.003, 0.001] * 8
    holdout = [-0.003, 0.001, -0.002, -0.001] * 8
    inputs = []
    for seed in (12, 13, 14):
        _, old_request = _source(seed)
        template = replace(
            old_request.identity_template, strategy_params={"fast_window": 10, "slow_window": 50}
        )
        request = replace(
            old_request,
            identity_template=template,
            robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
            search_space=SearchSpaceV1(
                "controlled.native.source.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
            ),
        )
        search = build_canonical_advanced_search_v1(request)
        observations = OfflineExperimentObservationsV1(
            metrics={"sharpe": _stats(train + holdout + holdout)["sharpe"]},
            robustness_results={},
            regime_results={},
            artifacts=(),
            robustness_policy=policy,
            robustness_observations={
                "returns": train + holdout + holdout,
                "split_metrics": {
                    "train": {"sharpe": _stats(train)["sharpe"], "sample_size": len(train)},
                    "validation": {
                        "sharpe": _stats(holdout)["sharpe"],
                        "sample_size": len(holdout),
                    },
                    "holdout": {"sharpe": _stats(holdout)["sharpe"], "sample_size": len(holdout)},
                },
            },
        )
        # Controlled historical input setup; the next actual attempt uses the regular provider below.
        loop_request = replace(
            _provider(template, observations=observations)(_proposed(search)),
            created_at="2026-08-18T15:30:00Z",
        )
        loop = run_canonical_automated_offline_research_loop_v1(loop_request)
        assert (
            loop["experiment_record"]["hypothesis_fingerprint"]
            == _proposed(search)["hypothesis_fingerprint"]
        )
        inputs.append(ResearchResultMetaInputV1(search, loop, _HORIZON, _UNIVERSE))
    provider, _, _, _ = regular_provider_case
    seen = []
    provider = replace(provider, measurement_observer=seen.append)
    next_request = _request(
        identity_template=provider.context.identity_template,
        budget=1,
        created_at="2026-08-18T17:00:00Z",
        robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
        search_space=SearchSpaceV1(
            "native.measured.v1",
            (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
        ),
    )
    executed = run_research_feedback_next_execution_v1(
        inputs,
        created_at="2026-08-18T16:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
        next_search_request=next_request,
        execution_created_at=AT,
        experiment_provider=provider,
        provider_ref="NativeResearchExperimentProviderV1.TEST_ONLY_CONTEXT",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
    )
    assert len(seen) == 1
    assert seen[0].receipt["parameters"] == {"fast_window": 10, "slow_window": 100}
    later = build_meta_learning_from_research_results_v1(
        [executed.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert later["source_bindings"][0]["experiment_id"] == seen[0].receipt["experiment_id"]
    output = measured[-1]
    (output / "regular_provider_feedback_execution.json").write_text(
        json.dumps(canonical_record_payload_v1(executed.evidence), indent=2) + "\n"
    )
    (output / "regular_provider_feedback_measurement.json").write_text(
        json.dumps(canonical_record_payload_v1(seen[0].receipt), indent=2) + "\n"
    )
    (output / "regular_provider_feedback_later_meta.json").write_text(
        json.dumps(canonical_record_payload_v1(later), indent=2) + "\n"
    )
    from src.experiments.canonical_search_candidate_research_execution_v1 import (
        build_research_execution_gvef_reference_v1,
        read_research_execution_gvef_reference_v1,
    )

    reference = build_research_execution_gvef_reference_v1(
        executed, artifact_ref="regular_provider_feedback_execution.canonical.json"
    )
    (output / "regular_provider_feedback_execution.canonical.json").write_bytes(
        reference.artifact_bytes
    )
    (output / "regular_provider_feedback_gvef_reference.json").write_text(
        json.dumps(canonical_record_payload_v1(reference.learning_artifact), indent=2) + "\n"
    )
    loaded = read_research_execution_gvef_reference_v1(
        reference.learning_artifact, artifact_bytes=reference.artifact_bytes
    )
    reloaded_meta = build_meta_learning_from_research_results_v1(
        [loaded.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert canonical_record_payload_v1(reloaded_meta) == canonical_record_payload_v1(later)
    (output / "regular_provider_feedback_later_meta_after_reload.json").write_text(
        json.dumps(canonical_record_payload_v1(reloaded_meta), indent=2) + "\n"
    )


def test_observational_callback_cannot_mutate_metrics_scores_or_robustness(regular_provider_case):
    provider, search, _, observed = regular_provider_case
    provider = replace(
        provider,
        context=replace(
            provider.context,
            robustness_policy=canonical_record_payload_v1(provider.context.robustness_policy),
        ),
    )
    expected = observed[0].observations.metrics["engine_pre_funding_sharpe"]

    def mutate_snapshot(snapshot):
        snapshot.observations.metrics["engine_pre_funding_sharpe"] = 999
        snapshot.observations.robustness_observations["returns"][0] = 0.99
        snapshot.receipt["runs"][0]["statistics"]["sharpe"]["value"] = 999
        provider.context.robustness_policy.clear()

    provider = replace(provider, measurement_observer=mutate_snapshot)
    result = run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=_proposed(search)["experiment_id"],
        created_at=AT,
        experiment_provider=provider,
        provider_ref="isolated_observer.TEST_ONLY",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
    )
    loop = result.next_meta_input.research_loop_record
    assert loop["experiment_record"]["metrics"]["engine_pre_funding_sharpe"] == expected
    assert loop["challenger_report"]["scores"][loop["selected_experiment_id"]] == expected
    assert canonical_record_payload_v1(loop) == canonical_record_payload_v1(
        regular_provider_case[2].next_meta_input.research_loop_record
    )
