"""The native search spends its next budget on a new measured experiment."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from src.experiments.canonical_advanced_search_v1 import (
    STATUS_ALREADY_MEASURED,
    build_canonical_advanced_search_v1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_native_research_session_v1 import (
    NativeResearchExecutionArchiveV1,
    NativeResearchSessionError,
)
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_research_prepared_execution_v1 import (
    ResearchRecoveryError,
    journal_root_v1,
    publish_v1,
    read_v1,
)
from tests.experiments.test_canonical_native_research_session_v1 import (
    _step,
    measured_session,  # noqa: F401
)
from tests.experiments.test_research_preflight_recovery_v1 import _isolated

ROOT = Path(__file__).resolve().parents[2]


def _next_request(provider, request):
    return (
        replace(provider, context=replace(provider.context, created_at="2026-08-18T20:00:00Z")),
        replace(request, created_at="2026-08-18T19:00:00Z"),
    )


def _reopen(provider, archive):
    context = provider.context
    owners = {
        field: type(store)(store.store_root)
        for field in ("experiment_memory_store", "failure_memory_store", "reality_gap_store")
        if (store := getattr(context, field)) is not None
    }
    return (
        replace(provider, context=replace(context, **owners)),
        NativeResearchExecutionArchiveV1(archive.root),
    )


def _proposed(search):
    (candidate,) = (row for row in search["candidates"] if row["status"] == "PROPOSED")
    return candidate


def test_reopened_measured_history_changes_next_native_trial(measured_session, tmp_path):
    provider, request, archive, seen = _isolated(measured_session, tmp_path, gap=0.01)
    first = _step(provider, request, archive)
    original = first.execution.next_meta_input.research_loop_record
    assert original["comparison_result"]["overall_comparability"] == "COMPARABLE"
    assert not original["failure_records"]
    assert seen[0].receipt["parameters"]["slow_window"] == 50

    provider, archive = _reopen(provider, archive)
    provider, request = _next_request(provider, request)
    unconditioned = build_canonical_advanced_search_v1(request)
    assert _proposed(unconditioned)["experiment_id"] == original["selected_experiment_id"]
    assert any(row["status"] == "BUDGET_EXCLUDED" for row in unconditioned["candidates"])
    assert _step(provider, request, archive).status == "REUSE_ARCHIVED"
    assert len(seen) == 1

    continuation = {"continuation_artifact_ids": (first.artifact_id,)}
    second = _step(provider, request, archive, **continuation)
    assert second.status == "EXECUTED_AND_ARCHIVED"
    assert second.feedback_record is None
    search = second.search_record
    assert search["input_lineage"]["archived_experiment_artifacts"] == {
        original["selected_experiment_id"]: first.artifact_id
    }
    (prior,) = (
        row
        for row in search["candidates"]
        if row["experiment_id"] == original["selected_experiment_id"]
    )
    assert prior["status"] == STATUS_ALREADY_MEASURED
    assert prior["offline_experiment_request"] is None
    assert _proposed(search)["parameter_region"]["slow_window"] == 100
    assert len(seen) == 2
    assert seen[1].receipt["parameters"]["slow_window"] == 100
    assert seen[1].receipt["engine_invocations"] == 4

    replay = _step(provider, request, archive, **continuation)
    assert replay.status == "REUSE_ARCHIVED"
    assert replay.artifact_id == second.artifact_id
    assert canonical_record_payload_v1(replay.search_record) == canonical_record_payload_v1(search)

    exhausted = _step(
        provider,
        replace(request, created_at="2026-08-18T21:00:00Z"),
        archive,
        continuation_artifact_ids=(second.artifact_id, first.artifact_id),
    )
    assert exhausted.status == "NO_PROPOSED_CANDIDATE"
    assert exhausted.execution is None and exhausted.artifact_id is None
    assert exhausted.search_record["search_evidence"]["already_measured_count"] == 2
    assert len(seen) == 2 and len(list(archive.root.glob("*.json"))) == 2

    cold = """
import json
import sys
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
archive = NativeResearchExecutionArchiveV1(sys.argv[1])
first, later = [archive.get(key).next_meta_input for key in sys.argv[2:]]
assert later.search_record["input_lineage"]["archived_experiment_artifacts"] == {
    first.research_loop_record["selected_experiment_id"]: sys.argv[2]
}
print(json.dumps(canonical_record_payload_v1(later.search_record), sort_keys=True))
"""
    reopened = subprocess.run(
        [
            "./scripts/pt",
            "-c",
            cold,
            str(archive.root),
            first.artifact_id,
            second.artifact_id,
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    assert json.loads(reopened.stdout) == canonical_record_payload_v1(search)

    proof_path = tmp_path / "native-continuation-result.json"
    proof = {
        "source_profile": "TEST_ONLY_SYNTHETIC",
        "first_artifact_id": first.artifact_id,
        "second_artifact_id": second.artifact_id,
        "archive_root": str(archive.root),
        "unconditioned_search": canonical_record_payload_v1(unconditioned),
        "executed_continuation": canonical_record_payload_v1(second.execution.evidence),
        "second_measurement": canonical_record_payload_v1(seen[1].receipt),
        "exhausted_search": canonical_record_payload_v1(exhausted.search_record),
        "productive_apply_authorized": False,
    }
    publish_v1(proof_path, proof)
    assert read_v1(proof_path) == proof


def test_measured_failure_retains_its_search_disposition(measured_session, tmp_path):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    first = _step(provider, request, archive)
    loop = first.execution.next_meta_input.research_loop_record
    assert loop["failure_records"]
    provider, archive = _reopen(provider, archive)
    provider, request = _next_request(provider, request)
    second = _step(provider, request, archive, continuation_artifact_ids=(first.artifact_id,))
    (prior,) = (
        row
        for row in second.search_record["candidates"]
        if row["experiment_id"] == loop["selected_experiment_id"]
    )
    assert prior["status"] == "REJECTED_DUPLICATE_WITHOUT_RETEST"
    assert prior["failure_signals"]["matching_failure_record_ids"]
    assert seen[-1].receipt["parameters"]["slow_window"] == 100


def test_native_coverage_is_retained_when_meta_is_explicitly_requested(measured_session, tmp_path):
    provider, request, archive, seen = _isolated(measured_session, tmp_path, gap=0.01)
    first = _step(provider, request, archive)
    provider, request = _next_request(provider, request)
    second = _step(
        provider,
        request,
        archive,
        ids=(first.artifact_id,),
        continuation_artifact_ids=(first.artifact_id,),
        meta_created_at="2026-08-18T18:30:00Z",
        meta_policy=canonical_meta_learning_policy_v1(),
    )
    assert second.feedback_record is not None
    assert second.search_record["search_evidence"]["already_measured_count"] == 1
    assert _proposed(second.search_record)["parameter_region"]["slow_window"] == 100
    assert len(seen) == 2


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("future", "CONTINUATION_ARCHIVE_AFTER_SEARCH"),
        ("foreign-data", "RESEARCH_REUSE_INPUT_CONFLICT"),
        ("foreign-champion", "CONTINUATION_ARCHIVE_CONTEXT_MISMATCH"),
        ("unacknowledged", "CONTINUATION_ORIGINAL_STEP_NOT_ACKNOWLEDGED"),
        ("tampered", "ARCHIVE_BYTE_DIGEST_MISMATCH"),
    ],
)
def test_continuation_rejects_unbound_history_before_engine(
    measured_session, tmp_path, fault, reason
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path, gap=0.01)
    first = _step(provider, request, archive)
    experiment_id = first.execution.next_meta_input.research_loop_record["selected_experiment_id"]
    provider, next_request = _next_request(provider, request)
    if fault == "future":
        next_request = request
    elif fault == "foreign-data":
        bars = provider.bars.copy()
        bars.iloc[-1, bars.columns.get_loc("close")] += 1
        provider = replace(provider, bars=bars)
    elif fault == "foreign-champion":
        champion = provider.context.champion
        identity = {**champion.experiment_identity, "identity_digest": "f" * 64}
        provider = replace(
            provider,
            context=replace(
                provider.context, champion=replace(champion, experiment_identity=identity)
            ),
        )
    elif fault == "unacknowledged":
        (journal_root_v1(provider.context) / experiment_id / "ack.json").unlink()
    elif fault == "tampered":
        packet = archive.root / (first.artifact_id + ".json")
        packet.write_bytes(packet.read_bytes() + b" ")
    with pytest.raises((NativeResearchSessionError, ResearchRecoveryError), match=reason):
        _step(provider, next_request, archive, continuation_artifact_ids=(first.artifact_id,))
    assert len(seen) == 1
