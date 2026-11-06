"""Actual measured comparison, durable restart and failure-informed next research."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from src.experiments.canonical_advanced_search_v1 import (
    build_canonical_advanced_search_v1,
    canonical_record_payload_v1,
    SearchSpaceV1,
    SearchAxisV1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_reality_gap_store_v1 import RealityGapDimensionV1
from src.experiments.canonical_native_research_measurements_v1 import (
    NativeResearchExecutionContextV1,
    NativeResearchExperimentProviderV1,
)
from src.experiments.canonical_native_research_session_v1 import (
    NativeResearchExecutionArchiveV1,
    NativeResearchSessionError,
    measure_native_research_champion_v1,
    run_native_research_session_step_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    canonical_robustness_policy_v1,
    derive_robustness_policy_digest_v1,
)
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    build_meta_learning_from_research_results_v1,
)
from tests.experiments.test_canonical_advanced_search_v1 import _request
from tests.experiments.test_canonical_native_research_measurements_v1 import _case

AT = "2026-08-18T18:00:00Z"


def _step(provider, request, archive, ids=(), **kwargs):
    return run_native_research_session_step_v1(
        search_request=request,
        provider=provider,
        archive=archive,
        prior_artifact_ids=ids,
        provider_ref="NativeResearchExperimentProviderV1.TEST_ONLY_MEASURED_SESSION",
        evidence_source_class="TEST_ONLY_SYNTHETIC",
        **kwargs,
    )


@pytest.fixture(scope="module")
def measured_session(tmp_path_factory):
    output = tmp_path_factory.mktemp("native_durable_session")
    bars, cfg, _, template, _ = _case()
    policy = canonical_robustness_policy_v1()
    initial_search = build_canonical_advanced_search_v1(
        _request(
            identity_template=template,
            seed=template.seed,
            budget=1,
            created_at="2026-08-18T13:00:00Z",
            robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
            search_space=SearchSpaceV1(
                "native.session.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50,))),
            ),
        )
    )
    horizon = {
        "start": bars.index[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": bars.index[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    universe = ("TEST_ONLY_NATIVE_MEASURED",)
    candidate = next(row for row in initial_search["candidates"] if row["status"] == "PROPOSED")
    champion = measure_native_research_champion_v1(
        candidate=candidate,
        bars=bars,
        cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        instrument_id="inst-eth-usdt-perp",
        time_horizon=horizon,
        market_universe=universe,
        robustness_policy=policy,
        created_at="2026-08-18T14:00:00Z",
    )
    template = replace(template, seed=55)
    context = NativeResearchExecutionContextV1(
        identity_template=template,
        champion=champion.candidate,
        champion_measurements=champion.measurements,
        created_at=AT,
        time_horizon=horizon,
        market_universe=universe,
        gap_dimensions=(RealityGapDimensionV1("fee", 0.01, 0.02, 0.005, "ratio"),),
        observed_surface="SHADOW",
        threshold_policy_digest=hashlib.sha256(b"TEST_ONLY_SYNTHETIC_GAP_POLICY").hexdigest(),
        robustness_policy=policy,
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(output / "memory"),
        failure_memory_store=CanonicalFailureMemoryStoreV1(output / "failures"),
        reality_gap_store=CanonicalRealityGapStoreV1(output / "gaps"),
    )
    seen = []
    provider = NativeResearchExperimentProviderV1(
        bars=bars,
        base_cfg=cfg,
        strategy_id="ma_crossover",
        strategy_version="v1",
        instrument_id="inst-eth-usdt-perp",
        context=context,
        measurement_observer=seen.append,
    )
    request = _request(
        identity_template=template,
        seed=55,
        budget=1,
        robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
        search_space=SearchSpaceV1(
            "native.session.v1",
            (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (50, 100))),
        ),
    )
    archive = NativeResearchExecutionArchiveV1(output / "archive")
    result = _step(provider, request, archive)
    for name, value in (
        ("champion_robustness.json", champion.robustness_evidence),
        ("champion_measurement.json", champion.measurements.receipt),
        ("session_execution.json", result.execution.evidence),
        ("session_measurement.json", seen[0].receipt),
    ):
        (output / name).write_text(json.dumps(canonical_record_payload_v1(value), indent=2) + "\n")
    (output / "session_artifact_id.txt").write_text(result.artifact_id + "\n")
    return provider, request, archive, result, champion, seen, output


def test_actual_champion_comparison_and_owner_persistence(measured_session):
    provider, _, archive, result, champion, seen, _ = measured_session
    assert result.status == "EXECUTED_AND_ARCHIVED"
    assert len(seen) == 1
    loop = result.execution.next_meta_input.research_loop_record
    assert loop["comparison_result"]["overall_comparability"] == "COMPARABLE"
    assert all(
        row["status"] == "IDENTICAL" for row in loop["comparison_result"]["dimension_results"]
    )
    assert loop["challenger_report"]["champion_state"]["mutated"] is False
    assert loop["robustness_evidence"]["aggregate_status"] != "PASS"
    assert champion.robustness_evidence["aggregate_status"] != "PASS"
    assert not any(
        row["failure_class"] == "REJECTED_COMPARABILITY" for row in loop["failure_records"]
    )
    assert provider.context.experiment_memory_store.exists(loop["selected_experiment_id"])
    assert len(provider.context.failure_memory_store.list_records()) == len(loop["failure_records"])
    assert len(provider.context.reality_gap_store.list_records()) == 1
    assert archive.get(result.artifact_id).evidence == result.execution.evidence


def test_real_failure_memory_changes_next_search_before_engine(measured_session, monkeypatch):
    provider, request, archive, _, _, _, output = measured_session
    unconditioned = build_canonical_advanced_search_v1(request)
    assert (
        next(row for row in unconditioned["candidates"] if row["status"] == "PROPOSED")[
            "parameter_region"
        ]["slow_window"]
        == 50
    )
    measured_next = []
    next_provider = replace(
        provider,
        measurement_observer=measured_next.append,
        context=replace(provider.context, created_at="2026-08-18T20:00:00Z"),
    )
    result = _step(next_provider, replace(request, created_at="2026-08-18T19:00:00Z"), archive)
    assert result.status == "EXECUTED_AND_ARCHIVED"
    assert measured_next[0].receipt["parameters"]["slow_window"] == 100
    assert any(
        row["status"] == "REJECTED_DUPLICATE_WITHOUT_RETEST"
        for row in result.search_record["candidates"]
    )
    (output / "failure_informed_next_execution.json").write_text(
        json.dumps(canonical_record_payload_v1(result.execution.evidence), indent=2) + "\n"
    )
    exhausted = _step(next_provider, replace(request, created_at="2026-08-18T21:00:00Z"), archive)
    assert exhausted.status == "NO_PROPOSED_CANDIDATE"
    assert exhausted.execution is None and exhausted.artifact_id is None
    assert len(measured_next) == 1


def test_archive_idempotence_and_exact_meta_in_new_process(measured_session):
    _, _, archive, result, _, seen, output = measured_session
    assert archive.append(result.execution, seen[0].receipt) == result.artifact_id
    later = build_meta_learning_from_research_results_v1(
        [result.execution.next_meta_input],
        created_at="2026-08-18T22:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    code = f"""
import json
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_research_result_to_meta_input_v1 import build_meta_learning_from_research_results_v1
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
loaded=NativeResearchExecutionArchiveV1({str(archive.root)!r}).get({result.artifact_id!r})
meta=build_meta_learning_from_research_results_v1([loaded.next_meta_input],created_at="2026-08-18T22:00:00Z",policy=canonical_meta_learning_policy_v1())
print(json.dumps(canonical_record_payload_v1(meta),sort_keys=True))
"""
    root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [str(root / "scripts/pt"), "-"],
        input=code,
        text=True,
        capture_output=True,
        cwd=root,
        check=True,
    )
    replay = json.loads(completed.stdout.splitlines()[-1])
    assert replay == canonical_record_payload_v1(later)
    (output / "later_meta_fresh_process.json").write_text(json.dumps(replay, indent=2) + "\n")


def test_resume_reads_archived_numerical_evidence(measured_session):
    provider, request, archive, previous, _, _, output = measured_session
    template = replace(provider.context.identity_template, seed=56)
    resumed = replace(
        provider,
        context=replace(
            provider.context, identity_template=template, created_at="2026-08-18T23:00:00Z"
        ),
    )
    result = _step(
        resumed,
        replace(
            request,
            identity_template=template,
            seed=56,
            created_at="2026-08-18T22:30:00Z",
            search_space=SearchSpaceV1(
                "native.session.v1",
                (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (75,))),
            ),
        ),
        archive,
        ids=(previous.artifact_id,),
        meta_created_at="2026-08-18T22:00:00Z",
        meta_policy=canonical_meta_learning_policy_v1(),
    )
    assert (
        result.feedback_record["meta_input_binding"]["source_bindings"][0]["experiment_id"]
        == previous.execution.next_meta_input.research_loop_record["selected_experiment_id"]
    )
    assert result.execution is not None
    (output / "resumed_feedback_execution.json").write_text(
        json.dumps(canonical_record_payload_v1(result.execution.evidence), indent=2) + "\n"
    )
    (output / "resumed_meta_feedback.json").write_text(
        json.dumps(canonical_record_payload_v1(result.feedback_record), indent=2) + "\n"
    )


@pytest.mark.parametrize(
    "mode", ["missing_stores", "wrong_template", "missing_meta", "duplicate_prior", "unbounded"]
)
def test_session_rejects_incomplete_or_conflicting_context_before_execution(measured_session, mode):
    provider, request, archive, previous, _, _, _ = measured_session
    ids = ()
    if mode == "missing_stores":
        provider = replace(provider, context=replace(provider.context, failure_memory_store=None))
    elif mode == "wrong_template":
        request = replace(request, identity_template=replace(request.identity_template, seed=99))
    elif mode == "missing_meta":
        ids = (previous.artifact_id,)
    elif mode == "duplicate_prior":
        ids = (previous.artifact_id, previous.artifact_id)
    elif mode == "unbounded":
        request = replace(request, budget=2)
    with pytest.raises(NativeResearchSessionError):
        _step(provider, request, archive, ids=ids)


def test_archive_rejects_tampered_bytes_and_path_escape(measured_session, tmp_path):
    _, _, archive, result, _, _, _ = measured_session
    copy = NativeResearchExecutionArchiveV1(tmp_path)
    (tmp_path / (result.artifact_id + ".json")).write_bytes(
        (archive.root / (result.artifact_id + ".json")).read_bytes() + b" "
    )
    with pytest.raises(NativeResearchSessionError, match="BYTE_DIGEST"):
        copy.get(result.artifact_id)
    with pytest.raises(NativeResearchSessionError, match="CONTENT_ADDRESS"):
        copy.get("../escape")


def test_archive_rejects_rehashed_wrong_numeric_receipt(measured_session):
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    _, _, archive, result, _, seen, _ = measured_session
    receipt = canonical_record_payload_v1(seen[0].receipt)
    full = next(row for row in receipt["runs"] if row["split"] == "full")
    full["statistics"]["sharpe"]["value"] = 999
    receipt["content_digest"] = compute_content_sha256(
        {k: v for k, v in receipt.items() if k != "content_digest"}
    )
    with pytest.raises(NativeResearchSessionError, match="METRIC_BINDING"):
        archive.append(result.execution, receipt)


def test_baseline_policy_conflict_rejected_before_measurement(measured_session, monkeypatch):
    import src.experiments.canonical_native_research_session_v1 as session

    provider, request, _, _, _, _, _ = measured_session
    search = build_canonical_advanced_search_v1(request)
    candidate = next(row for row in search["candidates"] if row["status"] == "PROPOSED")
    policy = canonical_robustness_policy_v1()
    policy["crash_window"] += 1

    def forbidden_measurement(**kwargs):
        raise AssertionError("must reject before engine")

    monkeypatch.setattr(session, "measure_native_research_candidate_v1", forbidden_measurement)
    with pytest.raises(NativeResearchSessionError, match="POLICY_FINGERPRINT"):
        measure_native_research_champion_v1(
            candidate=candidate,
            bars=provider.bars,
            cfg=provider.base_cfg,
            strategy_id=provider.strategy_id,
            strategy_version=provider.strategy_version,
            instrument_id=provider.instrument_id,
            time_horizon=provider.context.time_horizon,
            market_universe=provider.context.market_universe,
            robustness_policy=policy,
            created_at=AT,
        )
