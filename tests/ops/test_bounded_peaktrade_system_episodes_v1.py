"""Combined actual offline owners, declared synthetic ports and no new authority."""

from dataclasses import replace
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path

import pytest

from tests.ops._bounded_system_episode_fixture_v1 import (
    five_lane_episode,
    entry_episode,
    outcome_episode,
    research_episode,
    evaluate_current_episode_numbers,
    dump,
)


@pytest.fixture
def combined_episode(tmp_path):
    root = tmp_path / "e6-combined-episode"
    root.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        selection = root / "selection"
        selection.mkdir()
        n5, facts = five_lane_episode(selection, mp)
    bound = n5.readiness_projections["LANE_1"].bound_instrument
    assert bound.venue_native_id == "ETH-USDT-SWAP"
    entry = entry_episode(root / "entry", bound)
    job, source, context, done = outcome_episode(root / "learning", entry)
    return root, n5, facts, entry, job, source, context, done


def test_selected_cap24_identity_reaches_actual_core_risk_envelope_fill_and_learning(
    combined_episode,
):
    root, n5, facts, e, job, source, context, done = combined_episode
    assert n5.readiness_projections["LANE_1"].bound_instrument is e.bound
    assert e.bound.instrument_id == context.instrument_id == e.episode.identity.instrument_id
    assert e.bound.venue_native_id == context.native_id == e.envelope.instrument_id
    assert D(e.envelope.quantity) == e.accounting.position.qty
    assert D(e.active_sum) > 0
    assert done["numeric_readback"]["realized_return"] == math.log(120 / 110)
    assert done["numeric_readback"]["error"] == math.log(120 / 110) - 0.02
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
        read_explicit_offline_pending_v1,
    )

    assert read_explicit_offline_pending_v1(job) == done
    capsule = json.loads((job / "capsule_v1.json").read_text())
    assert capsule["context"]["producer_payload_json"] == context.producer_payload_json
    assert capsule["scope"]["account_identity"] == e.episode.identity.account_scope.account_identity
    dump(
        root / "combined-witness.json",
        {
            "data_class": "EXPLICIT_SYNTHETIC_OFFLINE",
            "actual_n5_lanes": len(n5.lane_rollups),
            "canonical_instrument_id": e.bound.instrument_id,
            "native_id": context.native_id,
            "decision_context": capsule["context"],
            "episode_identity": json.loads(json.dumps(e.episode.identity, default=vars)),
            "envelope": e.envelope.to_runtime_json_v1(),
            "reservation_id": e.reservation_id,
            "active_reserved_notional": e.active_sum,
            "opening_fill": e.fills[0].to_dict(),
            "job_root": str(job),
            "numeric_readback": done["numeric_readback"],
            "source_profile": source.profile_v1(),
            "economic_quality": "BLOCKED",
            "operational_authority": "NONE",
            "ports": [
                "explicit synthetic instrument metadata/account/facts",
                "N5 fixture G17/reconciliation",
                "separate explicit Core entry price path",
                "injected account GET response",
                "internal simulated fills",
                "explicit synthetic forecast and later O4 bars",
            ],
            "limits": [
                "No natural source or venue execution",
                "No claim that the N5 HOLD became ENTER from identical price inputs",
                "Research market data is separately declared; outcome values do not replace research returns",
            ],
        },
    )


def test_entry_partial_progress_reload_flat_preserves_retained_learning(combined_episode):
    root, _, _, e, job, _, _, done = combined_episode
    from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
        build_simulated_fill_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_progress_v1 import (
        advance_position_episode_from_simulated_accounting_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
        recover_position_episode_from_simulated_accounting_v1,
    )
    from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
        seal_simulated_accounting_episode_flat_v1,
        inspect_sealed_simulated_episode_v1,
    )
    from tests.ops.test_simulated_accounting_episode_close_v1 import _observation
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import (
        read_explicit_offline_pending_v1,
    )

    entry_source = Path(e.episode.entry_source_ref.split(":", 2)[2])
    original = entry_source.read_bytes()
    job_before = {str(p): p.read_bytes() for p in job.rglob("*") if p.is_file()}
    qty = e.accounting.position.qty
    for i in range(2):
        fill = build_simulated_fill_v1(
            fill_id=f"e6-reduce-{i}",
            instrument_id=e.bound.venue_native_id,
            side="SELL",
            quantity=qty / 2,
            mark_price="2100",
            contract=e.accounting.contract,
            reduce_only=True,
            event_time_unix=e.now + 60 + i * 60,
        )
        e.accounting.apply_fill(fill)
        e.fills.append(fill)
        if i == 0:
            advance_position_episode_from_simulated_accounting_v1(
                episode=e.episode,
                session=e.accounting,
                fills=tuple(e.fills),
                source_archive_root=e.args["source_archive_root"],
                cursor_store_root=e.cursor_root,
                expected_scope=e.episode.identity.account_scope,
                writer_session_id="e6-progress",
            )
            restored = recover_position_episode_from_simulated_accounting_v1(
                identity=e.episode.identity,
                source_path=entry_source,
                state_root=e.args["state_root"],
                repository_sha=e.args["repository_sha"],
                config_digest=e.args["config_digest"],
                writer_session_id="e6-reload",
            )
            assert (
                restored.binding.entry_event_time == e.episode.binding.entry_event_time == e.now + 1
            )
            assert e.accounting.position.qty == qty / 2
    observation = _observation(e.episode.identity)
    observation.update(
        observed_portfolio=replace(
            observation["observed_portfolio"],
            event_time_unix=e.now + 121,
            wall_time_unix=e.now + 121,
        ),
        observed_unix=e.now + 122,
    )
    sealed = seal_simulated_accounting_episode_flat_v1(
        episode=e.episode,
        accounting_session=e.accounting,
        fills=tuple(e.fills),
        bound=e.bound,
        expected_scope=e.episode.identity.account_scope,
        source_archive_root=e.args["source_archive_root"],
        cursor_store_root=e.cursor_root,
        writer_session_id="e6-flat",
        **observation,
    )
    assert sealed["status"] == "SEALED" and e.accounting.position is None
    inspected = inspect_sealed_simulated_episode_v1(
        identity=e.episode.identity,
        state_root=e.args["state_root"],
        repository_sha=e.args["repository_sha"],
        config_digest=e.args["config_digest"],
        expected_initial_source_ref=e.episode.entry_source_ref,
    )
    assert inspected["closure_ref"] == sealed["closure_ref"]
    assert entry_source.read_bytes() == original
    assert read_explicit_offline_pending_v1(job) == done
    assert job_before == {str(p): p.read_bytes() for p in job.rglob("*") if p.is_file()}
    from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch

    account = e.episode.identity.account_scope.account_identity
    reopened = _host(
        root / "entry" / "budget",
        _fetch(uid=account),
        clock=lambda: e.now + 122,
        expected_account=account,
    )
    try:
        reopened.observe_v1({"LANE_1": e.bound})
        # A locally flat Accounting episode is not a settled capital source.
        # Reopening the same original owner retains its exact hold and plan.
        assert reopened.owner.active_sum_v1() == D(e.active_sum)
        link = reopened.owner.execution_links_v1()[str(e.reservation_id)]
        assert link["envelope"] == e.envelope.to_runtime_json_v1()
    finally:
        reopened.close()
    dump(
        root / "flat-witness.json",
        {
            "closure": sealed,
            "opening_source_sha256": hashlib.sha256(original).hexdigest(),
            "learning_unchanged": True,
            "accounting_checkpoint": e.accounting.to_durable_dict(),
            "reservation_release_claimed": False,
            "external_submit_claimed": False,
        },
    )


def test_acceptance_inventory_rejects_unexecuted_missing_and_ambiguous_requirements(tmp_path):
    from src.ops.bounded_peaktrade_system_composition_v1.acceptance_v1 import (
        project_bounded_offline_acceptance_v1,
    )
    from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
        repository_source_digest_v1,
    )

    receipt = tmp_path / "run.xml"
    receipt.write_text(
        '<testsuites><testsuite><testcase classname="actual" name="case"/></testsuite></testsuites>'
    )
    case = {
        "case_id": "AC38",
        "status": "PASS_SELECTED_OFFLINE_PROFILE",
        "data_class": "EXPLICIT_SYNTHETIC_OFFLINE",
        "actual_owners": ["Core"],
        "scope_limit": "synthetic owner mechanism only",
        "tests": [{"class": "actual", "name": "case"}],
    }
    args = dict(
        expected_source_digest=repository_source_digest_v1(),
        junit_path=receipt,
        expected_junit_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
        required_case_ids=("AC38", "AC39"),
        case_evidence=[case],
    )
    result = project_bounded_offline_acceptance_v1(**args)
    assert result["inventory_status"] == "INCOMPLETE" and result["missing_cases"] == ["AC39"]
    assert result["full_system_accepted"] is False and result["operational_authority"] == "NONE"
    assert (
        project_bounded_offline_acceptance_v1(**{**args, "required_case_ids": ("AC38",)})[
            "inventory_status"
        ]
        == "COMPLETE"
    )
    blocked = project_bounded_offline_acceptance_v1(
        **{**args, "required_case_ids": ("AC38",), "case_evidence": [{**case, "status": "BLOCKED"}]}
    )
    assert blocked["inventory_status"] == "BLOCKED" and blocked["blocked_or_incomplete_cases"] == [
        "AC38"
    ]
    for changed, match in [
        (
            {"case_evidence": [{**case, "tests": [{"class": "historical", "name": "not_run"}]}]},
            "NOT_EXECUTED",
        ),
        ({"case_evidence": [case, case]}, "DUPLICATE"),
        ({"case_evidence": [{**case, "data_class": "NATURAL"}]}, "DATA_CLASS"),
        ({"expected_source_digest": "0" * 64}, "SOURCE_GENERATION"),
        ({"expected_junit_sha256": "0" * 64}, "RECEIPT_CHANGED"),
    ]:
        with pytest.raises(ValueError, match=match):
            project_bounded_offline_acceptance_v1(**{**args, **changed})


def test_closed_actual_consumer_admits_native_research_and_next_measured_candidate(
    combined_episode, monkeypatch
):
    root, _, _, _, job, _, _, done = combined_episode
    result, archive, first, second, step, provider, request = research_episode(
        root / "research", job
    )
    from src.experiments.canonical_research_result_to_meta_input_v1 import (
        build_meta_learning_from_research_results_v1,
    )
    from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
    from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1

    loaded = archive.get(second.artifact_id)
    original = build_meta_learning_from_research_results_v1(
        [second.execution.next_meta_input],
        created_at="2026-09-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    reloaded = build_meta_learning_from_research_results_v1(
        [loaded.next_meta_input],
        created_at="2026-09-18T19:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert canonical_record_payload_v1(original) == canonical_record_payload_v1(reloaded)
    assert result["actual_measured_slow_windows"] == [50, 100]
    assert result["outcome_scalar_used_as_research_score"] is False
    assert all(
        m["instrument_id"] == result["instrument_id"]
        and m["instrument_admission_mode"] == "current_selected_instrument_v1"
        for m in result["measurements"]
    )
    key, evaluation_archive, evaluation_plan = evaluate_current_episode_numbers(
        root / "evaluation", job, archive, second.artifact_id
    )
    for native_key in (first.artifact_id, second.artifact_id):
        assert archive.get(native_key).next_meta_input.research_loop_record[
            "selected_experiment_id"
        ]
    # An unsupported mode is rejected before opening any new research owner.
    from src.experiments.canonical_native_research_session_v1 import (
        run_native_research_session_step_v1,
    )
    from src.experiments.canonical_experiment_memory_store_v1 import (
        CanonicalExperimentMemoryStoreV1,
    )
    from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
    from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1

    invalid_root = root / "invalid-research-mode"
    invalid_provider = replace(
        provider,
        context=replace(
            provider.context,
            instrument_admission_mode="unsupported",
            experiment_memory_store=CanonicalExperimentMemoryStoreV1(invalid_root / "memory"),
            failure_memory_store=CanonicalFailureMemoryStoreV1(invalid_root / "failures"),
            reality_gap_store=CanonicalRealityGapStoreV1(invalid_root / "gaps"),
        ),
    )
    with pytest.raises(ValueError, match="mode_unsupported"):
        run_native_research_session_step_v1(
            search_request=request,
            provider=invalid_provider,
            archive=archive,
            prior_artifact_ids=(),
            provider_ref="EXPLICIT_E6_OFFLINE",
            evidence_source_class="TEST_ONLY_SYNTHETIC",
        )
    assert not invalid_root.exists()
    # A changed original numerical consumer must prevent any later research call.
    ack = job / "consumer_ack_v1.json"
    original_bytes = ack.read_bytes()
    changed = json.loads(original_bytes)
    changed["numeric_readback"]["error"] += 1
    ack.write_text(json.dumps(changed))

    def forbidden(*a, **kw):
        raise AssertionError("No engine after changed consumer")

    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        forbidden,
    )
    with pytest.raises(ValueError, match="ACK_MISMATCH"):
        step(provider, replace(request, created_at="2026-09-18T20:00:00Z"))
    ack.write_bytes(original_bytes)
    dump(root / "research" / "meta-reload-witness.json", canonical_record_payload_v1(reloaded))
    import subprocess
    from tests.ops._bounded_system_episode_fixture_v1 import ROOT

    code = f"""
import json
from pathlib import Path
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.offline_v1 import read_explicit_offline_pending_v1
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.evaluation.golden_vectors.integration.domain_result_binding_v1 import EvaluationPlanV1,DomainRequirementV1,DomainExclusionV1
from src.evaluation.golden_vectors.integration.evaluation_receipt_v1 import EvaluationReceiptArchiveV1
from src.evaluation.golden_vectors.integration.bounded_required_domain_fanout_v1 import read_system_evaluation_v1
import src.experiments.canonical_native_research_measurements_v1 as engine
def forbidden(*a,**k):raise AssertionError("No engine on readback")
engine.measure_native_research_candidate_v1=forbidden
done=read_explicit_offline_pending_v1(Path({str(job)!r}))
native=NativeResearchExecutionArchiveV1(Path({str(archive.root)!r})).get({second.artifact_id!r})
p=json.loads({json.dumps(evaluation_plan.to_dict_v1())!r})
p["required"]=tuple(DomainRequirementV1(**r) for r in p["required"])
p["not_required"]=tuple(DomainExclusionV1(**r) for r in p["not_required"])
r=read_system_evaluation_v1(EvaluationReceiptArchiveV1(Path({str(evaluation_archive.root)!r})),{key!r},expected_plan=EvaluationPlanV1(**p))
assert done["stage"]=="INGESTED" and r["mechanism_status"]=="PASS" and r["economic_quality"]["status"]=="BLOCKED"
print(json.dumps({{"numeric":done["numeric_readback"],"native_id":native.next_meta_input.research_loop_record["selected_experiment_id"],"evaluation":r["mechanism_status"]}}))
"""
    readback = subprocess.run(
        [str(ROOT / "scripts/pt"), "-"],
        input=code,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    assert readback.returncode == 0, readback.stderr
    loaded = json.loads(readback.stdout.splitlines()[-1])
    assert loaded["numeric"] == done["numeric_readback"]
    dump(root / "fresh-process-readback.json", loaded)


def test_current_research_instrument_mode_and_dirty_provenance_fail_closed(combined_episode):
    _, _, _, e, _, _, _, _ = combined_episode
    from tests.backtest.test_parameter_sensitivity_split_observation_v1 import _inputs
    from src.experiments.canonical_native_research_measurements_v1 import (
        native_research_identity_sources_v1,
    )
    from src.backtest.mv2_research_wiring_v1 import (
        STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1 as mode,
    )

    bars, cfg = _inputs()
    with pytest.raises(ValueError, match="instrument_not_supported"):
        native_research_identity_sources_v1(cfg, instrument_id=e.bound.instrument_id, bars=bars)
    with pytest.raises(ValueError, match="instrument_not_okx"):
        native_research_identity_sources_v1(
            cfg, instrument_id="inst-eth-usdt-perp", bars=bars, instrument_admission_mode=mode
        )
    with pytest.raises(ValueError, match="mode_unsupported"):
        native_research_identity_sources_v1(
            cfg,
            instrument_id=e.bound.instrument_id,
            bars=bars,
            instrument_admission_mode="anything",
        )
    from tests.experiments.test_canonical_advanced_search_v1 import _identity_request
    from src.experiments.canonical_experiment_identity_v1 import (
        build_canonical_experiment_identity_v1,
    )

    with pytest.raises(ValueError, match="DIRTY_TREE_PROVENANCE_FAIL_CLOSED"):
        build_canonical_experiment_identity_v1(
            _identity_request(working_tree_status="DIRTY", dirty_paths_digest="a" * 64)
        )
