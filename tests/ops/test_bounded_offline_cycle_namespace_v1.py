"""Actual Root→N1→capture→shared-ledger identity, not bare Scope-label tests."""

from pathlib import Path
from dataclasses import replace
import json

import pytest

from src.ops.bounded_peaktrade_system_composition_v1 import session_v1 as sessions
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.bounded_peaktrade_system_composition_v1.cycle_namespace_v1 import (
    bind_offline_cycle_namespace_v1,
)
from tests.ops.test_bounded_offline_episode_session_v1 import _setup, _session


def _actual_session(root, requested_prefix):
    from tests.ops.test_bounded_offline_episode_session_v1 import (
        test_actual_n1_close_is_bound_to_session_and_restart_does_not_renew_attempts,
    )

    captured = []
    original_port = sessions.invoke_occupied_lane_governed_cycle_n1_consumer_v1
    original_run = sessions.BoundedOfflineEpisodeSessionV1.run_occupied_cycle_v1

    def with_local_prefix(self, pairs, **kwargs):
        kwargs["cycle_id_prefix"] = requested_prefix
        return original_run(self, pairs, **kwargs)

    def consume(pairs, **kwargs):
        records = original_port(pairs, **kwargs)
        result = records["LANE_1"]
        cycle = result.s7_invocation.cycle_result
        ledger = AppendOnlyDdoLedgerV0(
            Path(pairs["LANE_1"][0].lane_state_root) / "ddo_learning_capture_v1.jsonl"
        )
        captured.append(
            {
                "effective_prefix": kwargs["cycle_id_prefix"],
                "cycle_id": cycle.cycle_id,
                "scope_id": cycle.outgoing_cursor.existing_scope.scope_id,
                "outcome": cycle.decision_outcome,
                "quantity": result.governed_cycle_result.final_order_envelope.quantity,
                "envelope": result.governed_cycle_result.final_order_envelope,
                "records": [dict(r) for r in ledger.read_all()],
                "capture_summary": cycle.ddo_capture_summary,
            }
        )
        return records

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(sessions, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", consume)
        patch.setattr(
            sessions.BoundedOfflineEpisodeSessionV1, "run_occupied_cycle_v1", with_local_prefix
        )
        test_actual_n1_close_is_bound_to_session_and_restart_does_not_renew_attempts(root, patch, 1)
    assert len(captured) == 1
    receipt = json.loads((root / "session" / sessions.RECEIPT).read_text())
    assert receipt["prefixes"] == [requested_prefix]
    assert receipt["cycle_namespaces"][0]["requested_prefix"] == requested_prefix
    assert receipt["cycle_namespaces"][0]["effective_prefix"] == captured[0]["effective_prefix"]
    return captured[0]


@pytest.mark.parametrize("prefix", ["same-local-cycle", "über/" * 50 + "end"])
def test_same_local_cycle_in_two_sessions_keeps_actual_capture_records_distinct(tmp_path, prefix):
    a = _actual_session(tmp_path / "first", prefix)
    b = _actual_session(tmp_path / "second", prefix)
    assert a["scope_id"] == b["scope_id"]
    assert a["outcome"] == b["outcome"] == "exit"
    assert a["quantity"] == b["quantity"] == "0.4"
    assert a["records"] and b["records"]
    assert a["effective_prefix"] != b["effective_prefix"]
    for captured in (a, b):
        assert captured["capture_summary"]["ok"] is True
        for record in captured["records"]:
            assert captured["effective_prefix"] in record["cycle_id"]
            assert captured["effective_prefix"] in record["correlation_id"]
            assert len(record["cycle_id"]) <= 128
    ids_a = {r["record_id"] for r in a["records"]}
    ids_b = {r["record_id"] for r in b["records"]}
    assert ids_a.isdisjoint(ids_b), "Independent sessions reused DDO record identities"
    combined = AppendOnlyDdoLedgerV0(tmp_path / "combined" / "ddo.jsonl")
    for row in (*a["records"], *b["records"]):
        combined.append(row)
    combined.verify_integrity()
    assert len(combined.read_all()) == len(a["records"]) + len(b["records"])


def test_full_raw_prefix_and_manifest_are_bound_without_sanitizing_or_truncating(tmp_path):
    manifest, _ = _setup(tmp_path)
    prefixes = ["x" * 200 + "a", "x" * 200 + "b", "a/b", "a?b", "ä", "a"]
    rows = [
        bind_offline_cycle_namespace_v1(manifest=manifest, requested_prefix=p) for p in prefixes
    ]
    assert len({r.effective_prefix for r in rows}) == len(prefixes)
    for prefix, row in zip(prefixes, rows):
        assert row.requested_prefix == prefix
        assert len(row.effective_prefix) == 64
        assert row == bind_offline_cycle_namespace_v1(manifest=manifest, requested_prefix=prefix)
        assert row != bind_offline_cycle_namespace_v1(
            manifest=replace(manifest, session_id="other"), requested_prefix=prefix
        )


@pytest.mark.parametrize("change", ["digest", "prefix", "missing", "legacy"])
def test_recovery_rejects_altered_namespace_or_legacy_receipt(tmp_path, change):
    manifest, _ = _setup(tmp_path)
    root = tmp_path / "session"
    with _session(manifest, root):
        pass
    path = root / sessions.RECEIPT
    state = json.loads(path.read_text())
    state.update(attempts_used=1, prefixes=["raw"], last_observed_unix=1800000000.0)
    row = bind_offline_cycle_namespace_v1(manifest=manifest, requested_prefix="raw").to_dict()
    state["cycle_namespaces"] = [row]
    if change == "digest":
        row["effective_prefix"] = "0" * 64
    elif change == "prefix":
        row["requested_prefix"] = "different"
    elif change == "missing":
        state["cycle_namespaces"] = []
    else:
        state["schema"] = "bounded_offline_episode_session_state.v1"
        state.pop("cycle_namespaces")
    path.write_text(json.dumps(state))
    with pytest.raises(ValueError, match="OFFLINE_SESSION_.*INVALID"):
        with _session(manifest, root, "recover"):
            pytest.fail("accepted unbound recovery")
    assert json.loads(path.read_text()) == state
