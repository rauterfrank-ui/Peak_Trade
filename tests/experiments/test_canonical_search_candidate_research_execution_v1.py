"""Bound next research execution, denial before persistence and downstream proof."""

from dataclasses import replace
import math
import hashlib

import pytest

from src.experiments.canonical_advanced_search_v1 import (
    SearchAxisV1,
    SearchSpaceV1,
    build_canonical_advanced_search_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_experiment_identity_v1 import build_canonical_experiment_identity_v1
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    ResearchResultMetaInputV1,
    build_meta_learning_from_research_results_v1,
)
from src.experiments.canonical_search_candidate_research_execution_v1 import (
    SearchResearchExecutionError,
    run_search_candidate_research_execution_v1,
    run_research_feedback_next_execution_v1,
    build_research_execution_gvef_reference_v1,
    read_research_execution_gvef_reference_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_advanced_search_v1 import _request as search_request
from tests.experiments.test_canonical_automated_offline_research_loop_v1 import (
    _candidate,
    _hypothesis,
    _observations,
    _request,
)
from tests.experiments.test_canonical_research_result_to_meta_input_v1 import (
    _source,
    _stats,
    _HORIZON,
    _UNIVERSE,
)

AT = "2026-08-18T18:00:00Z"


def _proposed(search):
    return next(row for row in search["candidates"] if row["status"] == "PROPOSED")


def _provider(template, *, observations=None, horizon=_HORIZON, universe=_UNIVERSE, seen=None):
    def execute(candidate):
        if seen is not None:
            seen.append(candidate["experiment_id"])
        hypothesis = _hypothesis(
            hypothesis_id=candidate["hypothesis_id"],
            identity_request=replace(
                template,
                strategy_params={**template.strategy_params, **candidate["parameter_region"]},
            ),
            parameter_region=candidate["parameter_region"],
            strategy_family=candidate["strategy_family"],
            regime=candidate["offline_experiment_request"]["regime"],
            candidate_ref=candidate["candidate_ref"],
            time_horizon=horizon,
            market_universe=universe,
        )
        return _request(
            hypotheses=(hypothesis,),
            selected_hypothesis_id=hypothesis.hypothesis_id,
            created_at=AT,
            experiment_observations=observations or _observations(),
            champion=_candidate(
                identity=build_canonical_experiment_identity_v1(replace(template, seed=1000)),
                time_horizon=horizon,
                market_universe=universe,
            ),
        )

    return execute


def _run(search, provider, **kwargs):
    return run_search_candidate_research_execution_v1(
        search_record=search,
        experiment_id=_proposed(search)["experiment_id"],
        created_at=AT,
        experiment_provider=provider,
        provider_ref="test_only.explicit_provider",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
        **kwargs,
    )


def test_provider_once_exact_identity_and_immutable_source_then_actual_meta():
    req = search_request(budget=1)
    search = build_canonical_advanced_search_v1(req)
    seen = []
    result = _run(search, _provider(req.identity_template, seen=seen))
    assert seen == [_proposed(search)["experiment_id"]]
    assert result.evidence["provider_invocations"] == 1
    assert result.next_meta_input.research_loop_record["selected_experiment_id"] == seen[0]
    assert not result.evidence["source_class_authenticated"]
    with pytest.raises(TypeError):
        result.evidence["research_loop_record"]["experiment_record"]["metrics"]["sharpe"] = 999
    meta = build_meta_learning_from_research_results_v1(
        [result.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert meta["source_bindings"][0]["experiment_id"] == seen[0]


@pytest.mark.parametrize(
    "field",
    ["identity", "parameter_region", "regime", "candidate_ref", "hypothesis_id", "created_at"],
)
def test_request_mismatch_does_not_invoke_loop_or_persist(monkeypatch, field):
    req = search_request(budget=1)
    search = build_canonical_advanced_search_v1(req)
    provider = _provider(req.identity_template)

    def divergent(candidate):
        request = provider(candidate)
        h = request.hypotheses[0]
        if field == "identity":
            h = replace(h, identity_request=replace(h.identity_request, seed=999))
        elif field in {"parameter_region", "regime", "candidate_ref", "hypothesis_id"}:
            h = replace(h, **{field: {"other": 1} if field == "parameter_region" else "other"})
        if field == "created_at":
            return replace(request, created_at="2026-08-18T19:00:00Z")
        return replace(request, hypotheses=(h,))

    def forbidden(_):
        pytest.fail("Phase10 must not be called for a divergent request")

    monkeypatch.setattr(
        "src.experiments.canonical_search_candidate_research_execution_v1.run_canonical_automated_offline_research_loop_v1",
        forbidden,
    )
    with pytest.raises(SearchResearchExecutionError, match="MISMATCH"):
        _run(search, divergent)


@pytest.mark.parametrize(
    "created_at",
    ["2026-02-30T00:00:00Z", "2026-08-18T14:00:00Z", "2026-08-18", "2026-08-18T18:00:00+00:00"],
)
def test_bad_time_rejected_before_provider(created_at):
    search = build_canonical_advanced_search_v1(search_request(budget=1))
    with pytest.raises(SearchResearchExecutionError):
        run_search_candidate_research_execution_v1(
            search_record=search,
            experiment_id=_proposed(search)["experiment_id"],
            created_at=created_at,
            experiment_provider=lambda _: pytest.fail("provider must not execute"),
            provider_ref="test_only",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
        )


def test_excluded_candidate_and_stale_integrity_rejected_before_provider():
    search = build_canonical_advanced_search_v1(search_request(budget=1))
    excluded = next(x for x in search["candidates"] if x["status"] != "PROPOSED")
    with pytest.raises(SearchResearchExecutionError, match="PROPOSED"):
        run_search_candidate_research_execution_v1(
            search_record=search,
            experiment_id=excluded["experiment_id"],
            created_at=AT,
            experiment_provider=lambda _: pytest.fail("must not execute"),
            provider_ref="test",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
        )
    tampered = canonical_record_payload_v1(search)
    tampered["candidates"][0]["parameter_region"]["fast"] = 999
    with pytest.raises(ValueError):
        _run(tampered, lambda _: pytest.fail("must not execute"))


def test_provider_failure_does_not_emit_success_or_run_phase10(monkeypatch):
    search = build_canonical_advanced_search_v1(search_request(budget=1))
    monkeypatch.setattr(
        "src.experiments.canonical_search_candidate_research_execution_v1.run_canonical_automated_offline_research_loop_v1",
        lambda _: pytest.fail("must not run"),
    )

    def failed(_):
        raise RuntimeError("measurement failed")

    with pytest.raises(RuntimeError, match="measurement failed"):
        _run(search, failed)


def _native_sources():
    """New native-name controlled case, not renaming any historical candidate."""
    from src.experiments.canonical_automated_offline_research_loop_v1 import (
        run_canonical_automated_offline_research_loop_v1,
    )

    sources = []
    for seed in (12, 13, 14):
        _, generic = _source(seed)
        template = replace(
            generic.identity_template, strategy_params={"fast_window": 10, "slow_window": 50}
        )
        request = replace(
            generic,
            identity_template=template,
            search_space=SearchSpaceV1(
                search_space_id="test_only.native_windows.v1",
                axes=(SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
            ),
        )
        search = build_canonical_advanced_search_v1(request)
        chosen = _proposed(search)
        # Reuse the existing computed control's observations, not its identities.
        original, _ = _source(seed)
        observations = _observations(
            metrics=dict(original.research_loop_record["experiment_record"]["metrics"]),
            robustness_results={},
            regime_results={},
            robustness_observations={
                "returns": [0.002, -0.001, 0.003, 0.001] * 8 + [-0.003, 0.001, -0.002, -0.001] * 16,
                "split_metrics": {
                    "train": {
                        "sharpe": _stats([0.002, -0.001, 0.003, 0.001] * 8)["sharpe"],
                        "sample_size": 32,
                    },
                    "validation": {
                        "sharpe": _stats([-0.003, 0.001, -0.002, -0.001] * 8)["sharpe"],
                        "sample_size": 32,
                    },
                    "holdout": {
                        "sharpe": _stats([-0.003, 0.001, -0.002, -0.001] * 8)["sharpe"],
                        "sample_size": 32,
                    },
                },
            },
        )
        loop_request = replace(
            _provider(template, observations=observations)(chosen),
            created_at="2026-08-18T15:30:00Z",
        )
        loop = run_canonical_automated_offline_research_loop_v1(loop_request)
        sources.append(ResearchResultMetaInputV1(search, loop, _HORIZON, _UNIVERSE))
    return sources, request


def _native_measured_case(artifact_root):
    """Computed controls -> Meta -> native Search ->3 actual split engines -> Meta."""
    from copy import deepcopy
    import json
    from src.backtest.mv2_research_wiring_v1 import run_mv2_research_backtest_wiring_v1
    from src.backtest.parameter_sensitivity_v1 import split_bars_train_validation_oos_v1
    from src.backtest.stats import compute_backtest_stats
    from tests.backtest.test_parameter_sensitivity_split_observation_v1 import _inputs

    sources, request = _native_sources()
    bars, cfg = _inputs()
    dataset_digest = hashlib.sha256(bars.to_csv(float_format="%.17g").encode()).hexdigest()
    template = replace(request.identity_template, dataset_digest=dataset_digest)
    request = replace(request, identity_template=template, created_at="2026-08-18T17:00:00Z")
    before = build_canonical_advanced_search_v1(request)
    (artifact_root / "before_search.json").write_text(
        json.dumps(canonical_record_payload_v1(before), indent=2) + "\n"
    )
    (artifact_root / "source_inputs.json").write_text(
        json.dumps(
            [
                {
                    "search_record": canonical_record_payload_v1(item.search_record),
                    "research_loop_record": canonical_record_payload_v1(item.research_loop_record),
                    "time_horizon": dict(item.time_horizon),
                    "market_universe": list(item.market_universe),
                }
                for item in sources
            ],
            indent=2,
        )
        + "\n"
    )
    (artifact_root / "native_bars.csv").write_bytes(bars.to_csv(float_format="%.17g").encode())
    (artifact_root / "native_cfg.json").write_text(json.dumps(cfg, indent=2) + "\n")
    observations = []
    horizon = {
        "start": bars.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": bars.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    universe = ("TEST_ONLY_SYNTHETIC_NATIVE_BARS",)

    def measured(candidate):
        point_cfg = deepcopy(cfg)
        point_cfg["economic_evaluation_v1"]["strategy_params"] = dict(candidate["parameter_region"])
        split_metrics = {}
        for name, split in zip(
            ("train", "validation", "holdout"), split_bars_train_validation_oos_v1(bars)
        ):
            wiring = run_mv2_research_backtest_wiring_v1(
                split, strategy_id="ma_crossover", cfg=point_cfg
            )
            trades = wiring.backtest_result.trades.to_dict(orient="records")
            stats = compute_backtest_stats(
                trades=trades, equity_curve=wiring.backtest_result.equity_curve, periods_per_year=1
            )
            split_metrics[name] = {
                "sharpe": stats["sharpe"],
                "sample_size": len(wiring.backtest_result.equity_curve.pct_change().dropna()),
            }
            equity_bytes = wiring.backtest_result.equity_curve.to_csv(float_format="%.17g").encode()
            equity_ref = f"{name}_equity.csv"
            (artifact_root / equity_ref).write_bytes(equity_bytes)
            observations.append(
                {
                    "split": name,
                    "experiment_id": candidate["experiment_id"],
                    "period_start": str(split.index[0]),
                    "period_end": str(split.index[-1]),
                    "return_observations": split_metrics[name]["sample_size"],
                    "equity_ref": equity_ref,
                    "equity_sha256": hashlib.sha256(equity_bytes).hexdigest(),
                    "strategy_provenance": wiring.strategy_signal_provenance.to_dict(),
                    "engine_signal_digest": wiring.backtest_engine_signal_digest,
                    "mv2_signal_digest": wiring.mv2_replay_signal_digest,
                    "cost_binding": wiring.effective_cost_config.to_dict(),
                    "nonfinite_metric_names": sorted(
                        key for key, value in stats.items() if not math.isfinite(value)
                    ),
                    "parameters": dict(candidate["parameter_region"]),
                    "sharpe_nonannual": stats["sharpe"],
                    "return": stats["total_return"],
                    "trades": len(trades),
                    "funding_model_ref": wiring.effective_cost_config.funding_model_version,
                }
            )
        split_bytes = json.dumps(
            observations, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        (artifact_root / "observed_splits.canonical.json").write_bytes(split_bytes)
        obs = _observations(
            artifacts=(
                {
                    "kind": "STORE_RELATIVE",
                    "ref": "observed_splits.canonical.json",
                    "digest": hashlib.sha256(split_bytes).hexdigest(),
                    "media_type": "application/json",
                },
            ),
            metrics={"oos_sharpe": split_metrics["holdout"]["sharpe"]},
            robustness_results={},
            regime_results={},
            robustness_observations={"split_metrics": split_metrics},
        )
        return _provider(template, observations=obs, horizon=horizon, universe=universe)(candidate)

    executed = run_research_feedback_next_execution_v1(
        sources,
        created_at="2026-08-18T16:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
        next_search_request=request,
        execution_created_at=AT,
        experiment_provider=measured,
        provider_ref="TEST_ONLY_SYNTHETIC.actual_mv2_split_engine",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
    )
    later = build_meta_learning_from_research_results_v1(
        [executed.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    return executed, observations, later


@pytest.fixture(scope="module")
def measured_case(tmp_path_factory):
    import json

    output = tmp_path_factory.mktemp("measured_native_execution")
    executed, observations, later = _native_measured_case(output)
    for name, value in (
        ("execution_packet.json", executed.evidence),
        ("observed_splits.json", observations),
        ("later_meta.json", later),
    ):
        plain = canonical_record_payload_v1(value) if not isinstance(value, list) else value
        (output / name).write_text(json.dumps(plain, indent=2, allow_nan=False) + "\n")
    reference = build_research_execution_gvef_reference_v1(
        executed, artifact_ref="executed_research.canonical.json"
    )
    (output / "executed_research.canonical.json").write_bytes(reference.artifact_bytes)
    (output / "gvef_reference.json").write_text(
        json.dumps(canonical_record_payload_v1(reference.learning_artifact), indent=2) + "\n"
    )
    return executed, observations, later, output


def test_native_next_candidate_actually_measured_and_seen_by_later_meta(measured_case):
    executed, observations, later, output = measured_case
    assert len(observations) == 3
    assert {tuple(sorted(row["parameters"].items())) for row in observations} == {
        (("fast_window", 10), ("slow_window", 100))
    }
    loop = executed.next_meta_input.research_loop_record
    assert (
        loop["experiment_record"]["metrics"]["oos_sharpe"] == observations[-1]["sharpe_nonannual"]
    )
    assert later["source_bindings"][0]["experiment_id"] == loop["selected_experiment_id"]
    assert later["source_bindings"][0]["research_loop_identity"] == loop["loop_identity"]
    assert executed.evidence["executed_research"]["phase10_invocations"] == 1
    assert not executed.evidence["productive_apply_authorized"]
    # Controlled identity/gap scaffolding, funding and economic boundaries stay open.
    assert {row["funding_model_ref"] for row in observations} == {"NOT_BOUND"}
    assert loop["robustness_evidence"]["aggregate_status"] != "PASS"
    for row in observations:
        assert row["engine_signal_digest"] == row["mv2_signal_digest"]
        assert row["strategy_provenance"]["configured_strategy_params"] == row["parameters"]
        assert row["cost_binding"]["economic_interpretation_allowed"] is False
        assert (
            hashlib.sha256((output / row["equity_ref"]).read_bytes()).hexdigest()
            == row["equity_sha256"]
        )
    from src.experiments.canonical_experiment_identity_v1 import domain_separated_digest

    raw_dataset_digest = hashlib.sha256((output / "native_bars.csv").read_bytes()).hexdigest()
    assert loop["experiment_record"]["experiment_identity"][
        "dataset_digest"
    ] == domain_separated_digest("dataset", {"source_digest": raw_dataset_digest})
    artifact = loop["experiment_record"]["artifacts"][0]
    assert hashlib.sha256((output / artifact["ref"]).read_bytes()).hexdigest() == artifact["digest"]
    assert compute_content_sha256(canonical_record_payload_v1(executed.evidence))


def test_exact_measured_packet_reaches_existing_gvef_without_learning_quality_claim(measured_case):
    import json
    from src.evaluation.golden_vectors.evaluators.self_learning_v1 import SelfLearningEvaluatorV1
    from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
    from src.evaluation.golden_vectors.contracts.enums import DomainVerdict
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import sl_context

    executed, _, _, output = measured_case
    reference = build_research_execution_gvef_reference_v1(
        executed, artifact_ref="executed_research.canonical.json"
    )
    artifact = canonical_record_payload_v1(reference.learning_artifact)
    assert hashlib.sha256(reference.artifact_bytes).hexdigest() == artifact["payload_sha256"]
    assert json.loads(reference.artifact_bytes) == canonical_record_payload_v1(executed.evidence)
    assert (output / artifact["artifact_ref"]).read_bytes() == reference.artifact_bytes
    assert json.loads((output / "gvef_reference.json").read_text()) == artifact
    ctx = sl_context(baseline=artifact, candidate=artifact)
    evaluator = SelfLearningEvaluatorV1()
    baseline = evaluator.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
    candidate = evaluator.evaluate_candidate(context=ctx, replay=ctx.replay_trace)
    assert baseline.verdict is candidate.verdict is DomainVerdict.PASS
    assert candidate.metrics[0].metric_id == "sl.artifact_digest"
    assert candidate.metrics[0].value == sha256_hex(artifact)
    assert candidate.semantic_digest_deltas["evidence_source_class"] == "MECHANISM_TEST_EVIDENCE"
    (output / "gvef_packet_evaluation.json").write_text(
        json.dumps(candidate.model_dump(mode="json"), indent=2) + "\n"
    )


def test_feedback_budget_above_one_never_executes_provider():
    with pytest.raises(SearchResearchExecutionError, match="SINGLE_CANDIDATE_BUDGET"):
        run_research_feedback_next_execution_v1(
            [],
            created_at="2026-08-18T16:00:00Z",
            policy=canonical_meta_learning_policy_v1(),
            next_search_request=search_request(budget=2),
            execution_created_at=AT,
            experiment_provider=lambda _: pytest.fail("must not execute"),
            provider_ref="test",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
        )


def test_provider_cannot_edit_candidate_or_nested_lists():
    request = search_request(budget=1)
    search = build_canonical_advanced_search_v1(request)
    delegate = _provider(request.identity_template)

    def provider(candidate):
        with pytest.raises(TypeError):
            candidate["parameter_region"]["fast"] = 99
        with pytest.raises(TypeError):
            candidate["matched_meta_learning_proposal_ids"].append("forged")
        return delegate(candidate)

    result = _run(search, provider)
    with pytest.raises(TypeError):
        result.next_meta_input.search_record["candidates"].clear()


def test_nanosecond_precedence_checked_before_provider():
    request = search_request(budget=1, created_at="2026-08-18T18:00:00.000000002Z")
    search = build_canonical_advanced_search_v1(request)
    with pytest.raises(SearchResearchExecutionError, match="PRECEDES_SEARCH"):
        run_search_candidate_research_execution_v1(
            search_record=search,
            experiment_id=_proposed(search)["experiment_id"],
            created_at="2026-08-18T18:00:00.000000001Z",
            experiment_provider=lambda _: pytest.fail("must not execute"),
            provider_ref="test",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
        )


@pytest.mark.parametrize(
    "ref", ["../x.json", "/x.json", "x//y.json", "x\\y.json", "x:bad.json", "./x.json", "x.txt"]
)
def test_gvef_reference_rejects_non_artifact_paths(measured_case, ref):
    with pytest.raises(SearchResearchExecutionError, match="RELATIVE_JSON"):
        build_research_execution_gvef_reference_v1(measured_case[0], artifact_ref=ref)


def test_gvef_reference_rejects_stale_numeric_packet(measured_case):
    executed = measured_case[0]
    payload = canonical_record_payload_v1(executed.evidence)
    payload["executed_research"]["research_loop_record"]["experiment_record"]["metrics"][
        "oos_sharpe"
    ] = 999
    with pytest.raises(SearchResearchExecutionError, match="DIGEST_MISMATCH"):
        build_research_execution_gvef_reference_v1(
            replace(executed, evidence=payload), artifact_ref="x.json"
        )


def test_existing_stores_persist_then_reload_without_new_memory_owner(tmp_path):
    from src.experiments.canonical_experiment_memory_store_v1 import (
        CanonicalExperimentMemoryStoreV1,
    )
    from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
    from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
    from tests.experiments.test_canonical_automated_offline_research_loop_v1 import _dimension

    request = search_request(budget=1)
    search = build_canonical_advanced_search_v1(request)
    delegate = _provider(request.identity_template)
    stores = dict(
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(tmp_path / "memory"),
        failure_memory_store=CanonicalFailureMemoryStoreV1(tmp_path / "failures"),
        reality_gap_store=CanonicalRealityGapStoreV1(tmp_path / "gaps"),
    )

    def provider(candidate):
        return replace(
            delegate(candidate),
            gap_dimensions=(_dimension(observed=0.1, threshold=0.001),),
            **stores,
        )

    result = _run(search, provider)
    loop = result.next_meta_input.research_loop_record
    memory = CanonicalExperimentMemoryStoreV1(tmp_path / "memory").get(
        loop["selected_experiment_id"]
    )
    assert canonical_record_payload_v1(memory) == canonical_record_payload_v1(
        loop["experiment_record"]
    )
    gap = loop["reality_gap_record"]
    reloaded_gap = CanonicalRealityGapStoreV1(tmp_path / "gaps").get(gap["reality_gap_record_id"])
    assert canonical_record_payload_v1(reloaded_gap) == canonical_record_payload_v1(gap)
    assert loop["failure_records"]
    for failure in loop["failure_records"]:
        reloaded = CanonicalFailureMemoryStoreV1(tmp_path / "failures").get(
            failure["failure_record_id"]
        )
        assert canonical_record_payload_v1(reloaded) == canonical_record_payload_v1(failure)


def test_divergent_candidate_leaves_actual_stores_unwritten(tmp_path):
    from src.experiments.canonical_experiment_memory_store_v1 import (
        CanonicalExperimentMemoryStoreV1,
    )

    request = search_request(budget=1)
    search = build_canonical_advanced_search_v1(request)
    delegate = _provider(request.identity_template)

    def provider(candidate):
        request = delegate(candidate)
        h = request.hypotheses[0]
        return replace(
            request,
            hypotheses=(replace(h, regime="WRONG"),),
            experiment_memory_store=CanonicalExperimentMemoryStoreV1(tmp_path / "memory"),
        )

    with pytest.raises(SearchResearchExecutionError, match="regime"):
        _run(search, provider)
    assert list(tmp_path.iterdir()) == []


def test_gvef_reference_cannot_point_to_a_different_meta_input(measured_case):
    result = measured_case[0]
    wrong = replace(result.next_meta_input, time_horizon={"start": "other", "end": "other"})
    with pytest.raises(SearchResearchExecutionError, match="time_horizon"):
        build_research_execution_gvef_reference_v1(
            replace(result, next_meta_input=wrong), artifact_ref="x.json"
        )


def test_exact_gvef_bound_bytes_reload_into_same_later_meta_result(measured_case):
    import json

    executed, _, later, output = measured_case
    reference = json.loads((output / "gvef_reference.json").read_text())
    reloaded = read_research_execution_gvef_reference_v1(
        reference, artifact_bytes=(output / "executed_research.canonical.json").read_bytes()
    )
    actual = build_meta_learning_from_research_results_v1(
        [reloaded.next_meta_input],
        created_at="2026-08-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert canonical_record_payload_v1(actual) == canonical_record_payload_v1(later)
    assert reloaded.evidence == executed.evidence
    (output / "later_meta_after_gvef_reference_reload.json").write_text(
        json.dumps(canonical_record_payload_v1(actual), indent=2) + "\n"
    )


def test_gvef_bound_numeric_bytes_and_reference_identity_cannot_diverge(measured_case):
    import json

    _, _, _, output = measured_case
    reference = json.loads((output / "gvef_reference.json").read_text())
    raw = (output / "executed_research.canonical.json").read_bytes()
    with pytest.raises(SearchResearchExecutionError, match="BYTE_DIGEST"):
        read_research_execution_gvef_reference_v1(reference, artifact_bytes=raw + b" ")
    reference["experiment_id"] = "0" * 64
    with pytest.raises(SearchResearchExecutionError, match="gvef_reference"):
        read_research_execution_gvef_reference_v1(reference, artifact_bytes=raw)


def test_original_gvef_numeric_float_boundary_is_preserved(measured_case):
    from src.evaluation.golden_vectors.contracts.errors import GvefSchemaError
    from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import sl_context

    payload = canonical_record_payload_v1(measured_case[0].evidence)
    with pytest.raises(GvefSchemaError, match="float forbidden"):
        sl_context(baseline=payload, candidate=payload)
