"""Journal publication faults must not turn pending history into an empty index."""

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    store_v1 as store,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    resolver_v1 as resolver,
)
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    DECISION_REF,
    EVIDENCE_CLASS_TEST_FIXTURE,
    REPO_SHA,
    T_BAR1,
    _create_pending,
    _norm,
)


def _ingest(root, ts=T_BAR1):
    return resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF),
        normalized=_norm(mark=3500, event_ts=ts),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )


def test_deleted_index_is_rebuilt_in_memory_from_existing_journal(tmp_path):
    root = Path(_create_pending(tmp_path))
    out = _ingest(root)
    index = store._index_path(store.lane_pending_lane_dir_v1(root))
    index.unlink()
    restored = store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    assert restored == out.record
    assert not index.exists()
    assert store.list_open_pending_outcomes_v1(root) == (restored,)


def test_bad_index_is_not_authority_or_rewritten_on_read(tmp_path):
    root = Path(_create_pending(tmp_path))
    out = _ingest(root)
    index = store._index_path(store.lane_pending_lane_dir_v1(root))
    index.write_bytes(b"{broken-index")
    assert store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF) == out.record
    assert index.read_bytes() == b"{broken-index"


def test_index_publication_failure_keeps_acknowledgeable_journal_and_replay(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))

    def fail(*a, **kw):
        raise OSError("controlled index publication failure")

    monkeypatch.setattr(store, "_atomic_write_json_v1", fail)
    with pytest.raises(OSError, match="controlled index"):
        _ingest(root)
    restored = store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    events = store._events_path(store.lane_pending_lane_dir_v1(root))
    assert json.loads(events.read_text().splitlines()[-1])["event_type"] == "BAR_INGESTED"
    before = events.read_bytes()
    assert _ingest(root).duplicate
    assert events.read_bytes() == before
    producer = resolver._replay_producer_from_pending_events_v1(
        lane_state_root=root, pending=restored, repository_sha=REPO_SHA
    )
    assert producer.list_envelopes()[0]["sample_count"] == 1


def test_journal_append_failure_cannot_publish_new_index_state(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))
    index = store._index_path(store.lane_pending_lane_dir_v1(root))
    before = index.read_bytes()

    def fail(*a, **kw):
        raise OSError("controlled append failure")

    monkeypatch.setattr(store, "append_pending_outcome_event_v1", fail)
    with pytest.raises(OSError, match="controlled append"):
        _ingest(root)
    assert index.read_bytes() == before


@pytest.mark.parametrize("damage", [b"{torn", b"{}\n", b"\n"])
def test_torn_or_malformed_journal_blocks_read_and_preserves_original(tmp_path, damage):
    root = Path(_create_pending(tmp_path))
    events = store._events_path(store.lane_pending_lane_dir_v1(root))
    events.write_bytes(events.read_bytes() + damage)
    before = events.read_bytes()
    with pytest.raises(store.NaturalEnterPendingOutcomeStoreError):
        store.list_open_pending_outcomes_v1(root)
    assert events.read_bytes() == before


def test_missing_journal_with_existing_index_is_not_empty_state(tmp_path):
    root = Path(_create_pending(tmp_path))
    store._events_path(store.lane_pending_lane_dir_v1(root)).unlink()
    with pytest.raises(store.NaturalEnterPendingOutcomeStoreError, match="JOURNAL_MISSING"):
        store.list_open_pending_outcomes_v1(root)


def test_stale_pending_record_cannot_overwrite_acknowledged_sample(tmp_path):
    root = Path(_create_pending(tmp_path))
    stale = store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    _ingest(root)
    events = store._events_path(store.lane_pending_lane_dir_v1(root))
    before = events.read_bytes()
    out = resolver.ingest_pending_outcome_mark_observation_v1(
        lane_state_root=root,
        pending=stale,
        normalized=_norm(mark=3510, event_ts=T_BAR1 + 1),
        repository_sha=REPO_SHA,
        evidence_class=EVIDENCE_CLASS_TEST_FIXTURE,
        allow_test_fixture=True,
    )
    assert not out.ok and out.reason == "PENDING_STORE_EXPECTED_RECORD_MISMATCH"
    assert events.read_bytes() == before


def test_kernel_writer_lock_blocks_competing_publication(tmp_path):
    root = Path(_create_pending(tmp_path))
    path = store._events_path(store.lane_pending_lane_dir_v1(root))
    before = path.read_bytes()
    with store._writer_v2(root):
        out = _ingest(root)
        assert not out.ok and out.reason == "PENDING_STORE_WRITER_BUSY"
    assert path.read_bytes() == before
    assert _ingest(root).ok


def test_sigkill_after_fsynced_append_before_index_then_fresh_process_replay(tmp_path):
    import signal
    import subprocess
    import sys

    root = Path(_create_pending(tmp_path))
    index = store._index_path(store.lane_pending_lane_dir_v1(root))
    old_index = index.read_bytes()
    worker = """
import os, signal, sys
from pathlib import Path
from tests.ops.test_pending_outcome_journal_authority_v2 import _ingest
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import store_v1 as store
store._atomic_write_json_v1 = lambda *a, **kw: os.kill(os.getpid(), signal.SIGKILL)
_ingest(Path(sys.argv[1]))
"""
    killed = subprocess.run(
        [sys.executable, "-c", worker, str(root)], cwd=Path.cwd(), capture_output=True, timeout=20
    )
    assert killed.returncode == -signal.SIGKILL
    assert index.read_bytes() == old_index
    reader = """
import json,sys
from pathlib import Path
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import DECISION_REF,REPO_SHA
from tests.ops.test_pending_outcome_journal_authority_v2 import _ingest
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import store_v1 as store, resolver_v1 as resolver
root=Path(sys.argv[1]); pending=store.load_pending_outcome_by_decision_ref_v1(root,DECISION_REF)
producer=resolver._replay_producer_from_pending_events_v1(lane_state_root=root,pending=pending,repository_sha=REPO_SHA)
assert _ingest(root).duplicate
assert _ingest(root,1756732801.0).ok
print(json.dumps({'sample_count':producer.list_envelopes()[0]['sample_count'],'decision':pending.decision_event_ref}))
"""
    replay = subprocess.run(
        [sys.executable, "-c", reader, str(root)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["sample_count"] == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda event: event.update(pending_outcome_id="other"),
        lambda event: event["record"].update(n_bars_required=True),
        lambda event: event["record"].update(schema_version="future.v99"),
        lambda event: event["record"].pop("native_id"),
    ],
)
def test_corrupt_record_or_event_identity_is_not_normalized(tmp_path, mutation):
    root = Path(_create_pending(tmp_path))
    path = store._events_path(store.lane_pending_lane_dir_v1(root))
    event = json.loads(path.read_text())
    mutation(event)
    path.write_text(json.dumps(event) + "\n")
    before = path.read_bytes()
    with pytest.raises(store.NaturalEnterPendingOutcomeStoreError):
        store.load_pending_outcome_by_decision_ref_v1(root, DECISION_REF)
    assert path.read_bytes() == before
