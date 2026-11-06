"""The actual lane release waits for verified durable retention, preserving bytes."""

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    retention_v1 as retention,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.artifact_matrix_v1 import (
    purge_lane_local_artifacts_for_release_v1,
    execute_lane_generation_transition_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
)
from tests.ops.test_current_mf_n5_instrument_runtime_identity_closure_v1 import _bound
from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    StateCarryDisposition,
)


def _lane(tmp_path):
    root = tmp_path / "lane"
    root.mkdir()
    (root / "side_state_v1.json").write_bytes(b'{"old":"side"}\n')
    (root / "ddo_learning_capture_v1.jsonl").write_bytes(
        b'{"old":"original source, preserved even if unreadable"}\n'
    )
    return root


def test_actual_generation_transition_archives_original_before_identity_change(tmp_path):
    root = _lane(tmp_path)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    old = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-A")
    )
    new = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id="LANE_1", bound=_bound(lane_id="LANE_1", native="VENUE-B")
    )
    disposition = execute_lane_generation_transition_v1(
        lane_state_root=root, identity=new, prior_identity=old.lane_identity
    )
    assert disposition in {StateCarryDisposition.RESET, StateCarryDisposition.REKEY}
    ack = next(tmp_path.glob(".peaktrade_lane_retention_v1/*/*/retention_ack_v1.json"))
    for name, raw in before.items():
        assert (ack.parent / "snapshot" / name).read_bytes() == raw
        assert (ack.parent / "released_originals" / name).read_bytes() == raw
        assert not (root / name).exists()
    assert (
        json.loads((root / "lane_runtime_instrument_identity_manifest_v1.json").read_text())[
            "venue_native_id"
        ]
        == "VENUE-B"
    )


@pytest.mark.parametrize("boundary", ["copy", "ack", "readback"])
def test_retention_failure_prevents_any_lane_release(tmp_path, monkeypatch, boundary):
    root = _lane(tmp_path)
    original = {p: p.read_bytes() for p in root.iterdir()}
    actual = retention.durable_bytes_v1

    def broken(path, raw):
        if boundary == "copy" or boundary == "ack" and path.name == "retention_ack_v1.json":
            raise OSError("test-only disk failure")
        actual(path, raw)
        if boundary == "readback" and "snapshot" in path.parts:
            path.write_bytes(b"corrupt copied bytes")

    monkeypatch.setattr(retention, "durable_bytes_v1", broken)
    with pytest.raises((OSError, retention.OutcomeRetentionError)):
        purge_lane_local_artifacts_for_release_v1(root)
    assert all(p.read_bytes() == raw for p, raw in original.items())
    assert not (root / "lane_runtime_instrument_identity_manifest_v1.json").exists()


def test_original_ddo_writer_exclusion_blocks_release(tmp_path):
    from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
    from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoConcurrentWriterError

    root = _lane(tmp_path)
    ledger = AppendOnlyDdoLedgerV0(root / "ddo_learning_capture_v1.jsonl")
    raw = ledger.ledger_path.read_bytes()
    with ledger._exclusive_writer():
        with pytest.raises(DdoConcurrentWriterError):
            purge_lane_local_artifacts_for_release_v1(root)
    assert ledger.ledger_path.read_bytes() == raw
    assert not list(tmp_path.glob(".peaktrade_lane_retention_v1/*/*/retention_ack_v1.json"))


def test_interrupted_release_preserves_originals_and_can_finish(tmp_path, monkeypatch):
    root = _lane(tmp_path)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    actual = Path.rename
    count = []

    def fail_after_move(self, target):
        result = actual(self, target)
        if self.parent == root and not count:
            count.append(True)
            raise RuntimeError("interruption after first release move")
        return result

    monkeypatch.setattr(Path, "rename", fail_after_move)
    with pytest.raises(RuntimeError):
        purge_lane_local_artifacts_for_release_v1(root)
    assert count
    for name, raw in before.items():
        copies = list(tmp_path.glob(f".peaktrade_lane_retention_v1/*/*/snapshot/{name}"))
        assert any(p.read_bytes() == raw for p in copies)
    monkeypatch.setattr(Path, "rename", actual)
    purge_lane_local_artifacts_for_release_v1(root)
    for name, raw in before.items():
        assert not (root / name).exists()
        originals = list(
            tmp_path.glob(f".peaktrade_lane_retention_v1/*/*/released_originals/{name}")
        )
        assert len(originals) == 1 and originals[0].read_bytes() == raw
