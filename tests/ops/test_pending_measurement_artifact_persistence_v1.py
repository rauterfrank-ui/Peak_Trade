"""Stored outcome refs must resolve to their complete validated measurement pair."""

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1 import (
    resolver_v1 as resolver,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.constants_v1 import (
    EVIDENCE_CLASS_REAL_PUBLIC,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
    load_pending_outcome_by_decision_ref_v1,
)
from tests.ops.test_pending_outcome_elapsed_horizon_v2 import _ingest
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
    DECISION_REF,
    REPO_SHA,
    T_BAR1,
    T_BAR2,
    _create_pending,
)


def _complete(root):
    # Injected public-input contract, never a natural market/source-authenticity proof.
    for ts in (T_BAR1, T_BAR2, (int(T_BAR2) // 3600 + 1) * 3600):
        out = _ingest(root, ts, source=EVIDENCE_CLASS_REAL_PUBLIC)
    return out


def test_closed_refs_resolve_to_full_validated_artifacts_in_new_process(tmp_path):
    import subprocess
    import sys

    root = Path(_create_pending(tmp_path))
    out = _complete(root)
    assert out.closed and out.record.closure_refs["measurement_bundle_ref"]
    script = """
import sys,json
from pathlib import Path
from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import DECISION_REF
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import load_pending_outcome_by_decision_ref_v1
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.measurement_store_v1 import load_pending_measurement_artifacts_v1
root=Path(sys.argv[1]);pending=load_pending_outcome_by_decision_ref_v1(root,DECISION_REF)
bundle=load_pending_measurement_artifacts_v1(root,pending,expected_ref=pending.closure_refs['measurement_bundle_ref'])
assert bundle['measurement_evidence_artifact']['actual_outcome_ref']==pending.closure_refs['measurement_ref']
assert bundle['evaluation_time_information_set_artifact']['evaluation_time_information_set_ref']==pending.closure_refs['evaluation_information_set_ref']
print(json.dumps({'start_price':bundle['measurement_evidence_artifact']['start_price']}))
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["start_price"] == 3500


def test_artifact_persistence_failure_precedes_evaluation_and_learning(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))
    ledger = root / "LANE_1/ddo_learning_capture_v1.jsonl"
    before = ledger.read_bytes()

    def fail(*a, **kw):
        raise OSError("controlled artifact write failure")

    monkeypatch.setattr(resolver, "persist_pending_measurement_artifacts_v1", fail, raising=False)
    out = _complete(root)
    assert not out.closed and out.reason == "PENDING_MEASUREMENT_PERSISTENCE_FAILED"
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("damage", ["delete", "tamper"])
def test_closed_measurement_loss_or_tampering_is_not_reported_as_verified(tmp_path, damage):
    root = Path(_create_pending(tmp_path))
    out = _complete(root)
    assert out.closed
    paths = list(root.rglob("measurement_artifacts_v1.json"))
    assert len(paths) == 1
    if damage == "delete":
        paths[0].unlink()
    else:
        raw = json.loads(paths[0].read_text())
        raw["measurement_evidence_artifact"]["start_price"] = 999
        paths[0].write_text(json.dumps(raw))
    again = resolver.try_close_pending_outcome_v1(
        lane_state_root=root, pending=out.record, repository_sha=REPO_SHA
    )
    assert not again.ok and again.reason == "PENDING_CLOSED_ARTIFACTS_UNVERIFIED"
    assert load_pending_outcome_by_decision_ref_v1(root, DECISION_REF).status == "CLOSED"


def test_failed_evaluation_reuses_original_immutable_artifact_pair(tmp_path, monkeypatch):
    root = Path(_create_pending(tmp_path))
    original = resolver.invoke_productive_n_bars_evaluation_runtime_v1
    monkeypatch.setattr(
        resolver,
        "invoke_productive_n_bars_evaluation_runtime_v1",
        lambda *a, **kw: {"ok": False, "reason": "CONTROLLED_EVALUATION_STOP"},
    )
    out = _complete(root)
    assert not out.closed
    paths = list(root.rglob("measurement_artifacts_v1.json"))
    assert len(paths) == 1
    before = paths[0].read_bytes()
    monkeypatch.setattr(resolver, "invoke_productive_n_bars_evaluation_runtime_v1", original)
    closed = resolver.try_close_pending_outcome_v1(
        lane_state_root=root, pending=out.record, repository_sha=REPO_SHA
    )
    assert closed.ok and paths[0].read_bytes() == before


@pytest.mark.parametrize(
    "field", ["measurement_evidence_artifact", "evaluation_time_information_set_artifact"]
)
def test_partial_artifact_pair_never_reaches_learning(tmp_path, monkeypatch, field):
    root = Path(_create_pending(tmp_path))
    ledger = root / "LANE_1/ddo_learning_capture_v1.jsonl"
    before = ledger.read_bytes()
    original = resolver.invoke_productive_n_bars_horizon_observation_v1

    def partial(*args, **kwargs):
        result = original(*args, **kwargs)
        result[field] = None
        return result

    monkeypatch.setattr(resolver, "invoke_productive_n_bars_horizon_observation_v1", partial)
    out = _complete(root)
    assert not out.closed and out.reason == "PENDING_MEASUREMENT_PERSISTENCE_FAILED"
    assert ledger.read_bytes() == before


def _stored_before_evaluation(root, monkeypatch):
    monkeypatch.setattr(
        resolver,
        "invoke_productive_n_bars_evaluation_runtime_v1",
        lambda *a, **kw: {"ok": False, "reason": "CONTROLLED_STOP"},
    )
    out = _complete(root)
    path = next(root.rglob("measurement_artifacts_v1.json"))
    return out.record, path, json.loads(path.read_text())


def test_valid_artifact_pair_cannot_be_rebound_to_another_instrument(tmp_path, monkeypatch):
    import hashlib
    from dataclasses import replace
    from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.measurement_store_v1 import (
        load_pending_measurement_artifacts_v1,
    )

    root = Path(_create_pending(tmp_path))
    pending, path, _bundle = _stored_before_evaluation(root, monkeypatch)
    expected = "pending.nbars.bundle." + hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(DdoValidationError, match="INSTRUMENT_MISMATCH"):
        load_pending_measurement_artifacts_v1(
            root, replace(pending, canonical_instrument_id="OTHER"), expected_ref=expected
        )


def test_existing_measurement_bytes_cannot_be_replaced_with_changed_observation(
    tmp_path, monkeypatch
):
    from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.measurement_store_v1 import (
        persist_pending_measurement_artifacts_v1,
    )

    root = Path(_create_pending(tmp_path))
    pending, path, bundle = _stored_before_evaluation(root, monkeypatch)
    before = path.read_bytes()
    bundle["evaluation_observation"]["economic_score"] = "CONTROLLED_CHANGED_LABEL"
    with pytest.raises(DdoValidationError, match="CONTENT_CONFLICT"):
        persist_pending_measurement_artifacts_v1(
            lane_state_root=root,
            pending=pending,
            horizon_result=bundle,
            producer_observed_at_unix=bundle["producer_observed_at_unix"] + 1,
        )
    assert path.read_bytes() == before


def test_artifact_writer_independently_refuses_fixture_history(tmp_path, monkeypatch):
    from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.measurement_store_v1 import (
        persist_pending_measurement_artifacts_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.store_v1 import (
        _events_path,
        lane_pending_lane_dir_v1,
    )
    from tests.ops.test_natural_enter_cross_session_outcome_closure_v1 import (
        EVIDENCE_CLASS_TEST_FIXTURE,
    )

    root = Path(_create_pending(tmp_path))
    pending, path, bundle = _stored_before_evaluation(root, monkeypatch)
    events = _events_path(lane_pending_lane_dir_v1(root))
    rows = [json.loads(line) for line in events.read_text().splitlines()]
    for row in rows:
        if row["event_type"] == "BAR_INGESTED":
            row["detail"]["evidence_class"] = EVIDENCE_CLASS_TEST_FIXTURE
    events.write_text("".join(json.dumps(row) + "\n" for row in rows))
    before = path.read_bytes()
    with pytest.raises(DdoValidationError, match="SOURCE_NOT_BOUND"):
        persist_pending_measurement_artifacts_v1(
            lane_state_root=root,
            pending=pending,
            horizon_result=bundle,
            producer_observed_at_unix=bundle["producer_observed_at_unix"] + 1,
        )
    assert path.read_bytes() == before
