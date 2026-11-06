"""Actual native measured trial; preflight and original Phase10 crash recovery."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from tests.experiments.test_canonical_native_research_session_v1 import measured_session, _step  # noqa: F401 - pytest fixture
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_research_prepared_execution_v1 import (
    ResearchRecoveryError,
    journal_root_v1,
    finish_prepared_v1,
    research_step_lease_v1,
)


def _isolated(measured_session, tmp_path, *, gap=0.02):
    provider, request, _, _, _, _, _ = measured_session
    ctx = replace(
        provider.context,
        existing_failure_records=(),
        gap_dimensions=tuple(replace(g, observed=gap) for g in provider.context.gap_dimensions),
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(tmp_path / "memory"),
        failure_memory_store=CanonicalFailureMemoryStoreV1(tmp_path / "failures"),
        reality_gap_store=CanonicalRealityGapStoreV1(tmp_path / "gaps"),
    )
    seen = []
    return (
        replace(provider, context=ctx, measurement_observer=seen.append),
        request,
        NativeResearchExecutionArchiveV1(tmp_path / "archive"),
        seen,
    )


@pytest.mark.parametrize("boundary", ["prepared", "experiment", "failure", "gap", "archive", "ack"])
def test_partial_owner_writes_resume_exact_createdat_without_engine(
    measured_session, tmp_path, monkeypatch, boundary
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    actual = None
    if boundary in {"prepared", "ack"}:
        import src.experiments.canonical_research_prepared_execution_v1 as persistence

        actual = persistence.publish_v1

        def fail(path, body):
            actual(path, body)
            if path.name == boundary + ".json":
                raise RuntimeError("after durable write")

        monkeypatch.setattr(persistence, "publish_v1", fail)
    else:
        owner = {
            "experiment": provider.context.experiment_memory_store,
            "failure": provider.context.failure_memory_store,
            "gap": provider.context.reality_gap_store,
            "archive": archive,
        }[boundary]
        actual = owner.append

        def fail(*a, **kw):
            actual(*a, **kw)
            raise RuntimeError("after durable write")

        monkeypatch.setattr(owner, "append", fail)
    with pytest.raises(RuntimeError, match="after durable write"):
        _step(provider, request, archive)
    assert len(seen) == 1
    original = next(journal_root_v1(provider.context).glob("*/prepared.json"))
    original_bytes = original.read_bytes()
    monkeypatch.undo()

    def forbidden(*a, **kw):
        raise AssertionError("recovery must never call the engine")

    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        forbidden,
    )
    if boundary == "ack":
        with research_step_lease_v1(provider.context):
            resumed = finish_prepared_v1(original.parent, archive, provider.context)
    else:
        resumed = _step(
            replace(provider, context=replace(provider.context, created_at="2026-08-19T18:00:00Z")),
            replace(request, created_at="2026-08-19T17:00:00Z"),
            archive,
        )
    assert resumed.status in {"RESUMED_AND_ARCHIVED", "REUSE_ARCHIVED", "EXECUTED_AND_ARCHIVED"}
    # A completed ACK lets normal Search move on instead of resuming; at the ACK
    # boundary call exact prepared recovery explicitly to distinguish that case.
    assert (
        resumed.execution.next_meta_input.research_loop_record["created_at"]
        == "2026-08-18T18:00:00Z"
    )
    assert original.read_bytes() == original_bytes
    assert len(seen) == 1
    assert len(list(archive.root.glob("*.json"))) == 1


def test_uncertain_measurement_and_existing_unarchived_identity_block_new_engine(
    measured_session, tmp_path, monkeypatch
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)

    def failed_observer(m):
        raise RuntimeError("measurement lost before prepared request")

    provider = replace(provider, measurement_observer=failed_observer)
    with pytest.raises(RuntimeError):
        _step(provider, request, archive)
    with pytest.raises(ResearchRecoveryError, match="UNCERTAIN"):
        _step(provider, request, archive)
    assert not list(archive.root.glob("*.json"))


def test_reuse_and_replication_policy_before_provider(measured_session, tmp_path, monkeypatch):
    # Nonfailing explicit gap + retest suppresses duplicate Search rejection;
    # reuse is tested with its exact original single selected search directly.
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    first = _step(provider, request, archive)
    from src.experiments.canonical_research_preflight_v1 import research_preflight_v1

    c = next(c for c in first.search_record["candidates"] if c["status"] == "PROPOSED")
    path = journal_root_v1(provider.context) / c["experiment_id"]
    status, reused = research_preflight_v1(
        candidate=c, context=provider.context, archive=archive, step_path=path, retest_reason=None
    )
    assert status == "REUSE_ARCHIVED" and reused[0] == first.artifact_id
    with pytest.raises(ResearchRecoveryError, match="REPLICATION_NOT_SUPPORTED"):
        research_preflight_v1(
            candidate=c,
            context=provider.context,
            archive=archive,
            step_path=path,
            retest_reason="explicit-replication",
        )
    assert len(seen) == 1


def test_original_memory_without_prepared_packet_and_lease_contention_block(
    measured_session, tmp_path
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    with research_step_lease_v1(provider.context):
        with pytest.raises(ResearchRecoveryError, match="BUSY"):
            _step(provider, request, archive)
    from src.experiments.canonical_advanced_search_v1 import build_canonical_advanced_search_v1

    c = next(
        c
        for c in build_canonical_advanced_search_v1(request)["candidates"]
        if c["status"] == "PROPOSED"
    )
    path = provider.context.experiment_memory_store.store_root / c["experiment_id"]
    path.mkdir(parents=True)
    (path / "retained-partial-original").write_text("must remain")
    with pytest.raises(ResearchRecoveryError, match="ORIGINAL_MEASUREMENT"):
        _step(provider, request, archive)
    assert len(seen) == 0 and (path / "retained-partial-original").read_text() == "must remain"


def test_fresh_process_recovery_never_imports_engine_trial(measured_session, tmp_path, monkeypatch):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    actual = archive.append

    def failed(*a, **kw):
        raise RuntimeError("late archive failure")

    monkeypatch.setattr(archive, "append", failed)
    with pytest.raises(RuntimeError):
        _step(provider, request, archive)
    monkeypatch.setattr(archive, "append", actual)
    packet = next(journal_root_v1(provider.context).glob("*/prepared.json"))
    code = """
from pathlib import Path
from types import SimpleNamespace
import sys,json
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_research_prepared_execution_v1 import finish_prepared_v1,research_step_lease_v1
import src.experiments.canonical_native_research_measurements_v1 as native
def forbidden(*a,**k):raise AssertionError('engine forbidden')
native.measure_native_research_candidate_v1=forbidden
p=Path(sys.argv[1]);ctx=SimpleNamespace(experiment_memory_store=CanonicalExperimentMemoryStoreV1(p/'memory'),failure_memory_store=CanonicalFailureMemoryStoreV1(p/'failures'),reality_gap_store=CanonicalRealityGapStoreV1(p/'gaps'))
with research_step_lease_v1(ctx):r=finish_prepared_v1(Path(sys.argv[2]),NativeResearchExecutionArchiveV1(p/'archive'),ctx)
print('RESULT='+json.dumps({'artifact':r.artifact_id,'created_at':r.execution.next_meta_input.research_loop_record['created_at']}))
"""
    repo = Path(__file__).resolve().parents[2]
    r = subprocess.run(
        [str(repo / "scripts/pt"), "-c", code, str(tmp_path), str(packet.parent)],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(next(l[7:] for l in r.stdout.splitlines() if l.startswith("RESULT=")))
    assert data["created_at"] == "2026-08-18T18:00:00Z"
    assert (
        archive.get(data["artifact"]).next_meta_input.research_loop_record["created_at"]
        == data["created_at"]
    )
    assert len(seen) == 1


def test_actual_session_reuses_without_provider_and_rejects_input_drift(
    measured_session, tmp_path, monkeypatch
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path, gap=0.01)
    first = _step(provider, request, archive)
    assert not first.execution.next_meta_input.research_loop_record["failure_records"]

    def forbidden(*a, **kw):
        raise AssertionError("reuse must not measure")

    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        forbidden,
    )
    second = _step(
        replace(provider, context=replace(provider.context, created_at="2026-08-19T18:00:00Z")),
        replace(request, created_at="2026-08-19T17:00:00Z"),
        archive,
    )
    assert second.status == "REUSE_ARCHIVED" and second.artifact_id == first.artifact_id
    assert second.execution.evidence == first.execution.evidence and len(seen) == 1
    bars = provider.bars.copy()
    bars.iloc[-1, bars.columns.get_loc("close")] += 1
    with pytest.raises(ResearchRecoveryError, match="INPUT_CONFLICT"):
        _step(replace(provider, bars=bars), request, archive)


@pytest.mark.parametrize("mode", ["receipt", "prepared", "owner", "archive_locator"])
def test_prepared_drift_blocks_recovery_without_remeasure(
    measured_session, tmp_path, monkeypatch, mode
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)

    def fail(*a, **k):
        raise RuntimeError("archive unavailable")

    monkeypatch.setattr(archive, "append", fail)
    with pytest.raises(RuntimeError):
        _step(provider, request, archive)
    monkeypatch.undo()
    packet = next(journal_root_v1(provider.context).glob("*/prepared.json"))
    if mode in {"receipt", "prepared"}:
        data = json.loads(packet.read_text())
        data["body"]["receipt"]["engine_invocations"] = 0
        if mode == "prepared":
            data["body"]["request"]["fields"]["created_at"] = "2026-08-19T18:00:00Z"
        packet.write_text(json.dumps(data))
    ctx = provider.context
    if mode == "owner":
        ctx = replace(
            ctx, experiment_memory_store=CanonicalExperimentMemoryStoreV1(tmp_path / "foreign")
        )
    if mode == "archive_locator":
        archive = NativeResearchExecutionArchiveV1(tmp_path / "different-archive")
    with pytest.raises(ResearchRecoveryError):
        with research_step_lease_v1(ctx):
            finish_prepared_v1(packet.parent, archive, ctx)
    assert len(seen) == 1


@pytest.mark.parametrize("boundary", ["experiment", "failure", "gap", "archive", "ack"])
def test_physical_process_death_after_original_owner_write(
    measured_session, tmp_path, monkeypatch, boundary
):
    import src.experiments.canonical_research_prepared_execution_v1 as recovery

    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    actual = recovery.publish_v1

    def prepared_only(path, body):
        actual(path, body)
        if path.name == "prepared.json":
            raise RuntimeError("prepared original request before Phase10")

    monkeypatch.setattr(recovery, "publish_v1", prepared_only)
    with pytest.raises(RuntimeError):
        _step(provider, request, archive)
    monkeypatch.undo()
    packet = next(journal_root_v1(provider.context).glob("*/prepared.json"))
    original = packet.read_bytes()
    repo = Path(__file__).resolve().parents[2]
    args = [
        str(repo / "scripts/pt"),
        "-m",
        "tests.experiments._research_prepared_recovery_worker_v1",
        str(tmp_path),
        str(packet.parent),
    ]
    killed = subprocess.run([*args, boundary], cwd=repo, text=True, capture_output=True)
    assert killed.returncode == 79, killed.stdout + killed.stderr
    resumed = subprocess.run([*args, "resume"], cwd=repo, text=True, capture_output=True)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    r = json.loads(next(l[7:] for l in resumed.stdout.splitlines() if l.startswith("RESULT=")))
    assert r["created_at"] == "2026-08-18T18:00:00Z"
    assert packet.read_bytes() == original and len(seen) == 1
    assert len(list(archive.root.glob("*.json"))) == 1
    assert (
        archive.get(r["artifact_id"]).next_meta_input.research_loop_record["created_at"]
        == r["created_at"]
    )


def test_actual_session_rejects_same_id_replication_before_engine(
    measured_session, tmp_path, monkeypatch
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path, gap=0.01)
    _step(provider, request, archive)

    def forbidden(*a, **kw):
        raise AssertionError("no replication engine")

    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        forbidden,
    )
    with pytest.raises(ResearchRecoveryError, match="REPLICATION_NOT_SUPPORTED"):
        _step(
            replace(
                provider,
                context=replace(provider.context, retest_reason="same-identity-replication"),
            ),
            replace(request, retest_reason="same-identity-replication"),
            archive,
        )
    assert len(seen) == 1


def test_changed_context_cannot_replace_original_prepared_request(
    measured_session, tmp_path, monkeypatch
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)

    def fail(*a, **kw):
        raise RuntimeError("late archive")

    monkeypatch.setattr(archive, "append", fail)
    with pytest.raises(RuntimeError):
        _step(provider, request, archive)
    monkeypatch.undo()
    changed = replace(
        provider,
        context=replace(
            provider.context,
            gap_dimensions=tuple(replace(g, observed=1.0) for g in provider.context.gap_dimensions),
        ),
    )
    with pytest.raises(ResearchRecoveryError, match="CONTEXT_CONFLICT"):
        _step(changed, request, archive)
    assert len(seen) == 1


def test_exact_ack_retransmission_does_not_advance_to_another_candidate(
    measured_session, tmp_path, monkeypatch
):
    provider, request, archive, seen = _isolated(measured_session, tmp_path)
    first = _step(provider, request, archive)
    assert first.execution.next_meta_input.research_loop_record["failure_records"]

    def forbidden(*a, **kw):
        raise AssertionError("same request must neither measure nor run Phase10")

    monkeypatch.setattr(
        "src.experiments.canonical_native_research_measurements_v1.measure_native_research_candidate_v1",
        forbidden,
    )
    monkeypatch.setattr(
        "src.experiments.canonical_search_candidate_research_execution_v1.run_canonical_automated_offline_research_loop_v1",
        forbidden,
    )
    replay = _step(provider, request, archive)
    assert replay.status == "REUSE_ARCHIVED" and replay.artifact_id == first.artifact_id
    assert replay.execution.evidence == first.execution.evidence and len(seen) == 1
