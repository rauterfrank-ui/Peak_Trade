"""Original-owner readback and bounded stop are independent of process health."""

from dataclasses import replace
import json
import os

import pytest

from src.ops.bounded_peaktrade_system_composition_v1 import session_v1
from src.ops.bounded_peaktrade_system_composition_v1.readiness_v1 import (
    OfflineProcessObservationV1,
    project_offline_session_readiness_v1,
    STOP,
    run_readiness_checked_offline_cycle_v1,
)
from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import (
    HandoffRequestV1,
    OfflineHandoffJournalV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.recovery_v1 import (
    recover_budget_handoff_ack_v1,
    reservation_readback_digest_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    ReservationStateV1,
    ReserveDispositionV1,
)
from tests.ops.test_bounded_offline_episode_session_v1 import _setup, _session
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner, _auto, _reserve


def _process(session, **kw):
    return replace(
        OfflineProcessObservationV1(
            session.manifest.session_id, session.manifest.digest(), os.getpid(), 1000.0, True
        ),
        **kw,
    )


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "dead-pid",
        "foreign-session",
        "future",
        "stale",
        "false-health",
        "recovery",
        "state-drift",
        "foreign-pid-owner",
    ],
)
def test_process_health_cannot_override_original_readiness(tmp_path, fault):
    manifest, pairs = _setup(tmp_path)
    root = tmp_path / "session"
    with _session(manifest, root) as opened:
        process = _process(opened)
        if fault == "dead-pid":
            process = replace(process, pid=99999999)
        if fault == "foreign-session":
            process = replace(process, session_id="other")
        if fault == "future":
            process = replace(process, heartbeat_unix=1001.0)
        if fault == "stale":
            process = replace(process, heartbeat_unix=990.0)
        if fault == "false-health":
            process = replace(process, healthy=False)
        if fault == "recovery":
            opened._state["status"] = "RECOVERY_REQUIRED"
            session_v1._write(root / session_v1.RECEIPT, opened._state)
        if fault == "state-drift":
            value = opened.state
            value["status"] = "RECOVERY_REQUIRED"
            session_v1._write(root / session_v1.RECEIPT, value)
        if fault == "foreign-pid-owner":
            opened._process_pid = 99999999
        result = project_offline_session_readiness_v1(
            opened, process=process, now_unix=1000.0, maximum_heartbeat_age_seconds=5
        )
        assert result["ready"] is (fault is None), result
        assert result["venue_truth_proven"] is result["external_effect_authorized"] is False
        assert opened.state["attempts_used"] == 0


def test_stop_survives_reopen_and_does_not_charge_or_renew_attempts(tmp_path, monkeypatch):
    manifest, pairs = _setup(tmp_path)
    root = tmp_path / "session"
    calls = []
    monkeypatch.setattr(
        session_v1,
        "invoke_occupied_lane_governed_cycle_n1_consumer_v1",
        lambda *a, **kw: calls.append(kw),
    )
    with _session(manifest, root) as opened:
        before = opened.state
        opened.request_stop_v1(reason="explicit-offline-stop", requested_unix=1000.0)
        stopped = (root / STOP).read_bytes()
        with pytest.raises(ValueError, match="STOP_REQUESTED"):
            opened.run_occupied_cycle_v1(pairs)
        assert opened.state == before
    with _session(manifest, root, "recover") as reopened:
        assert reopened.state == before and (root / STOP).read_bytes() == stopped
        result = project_offline_session_readiness_v1(
            reopened, process=_process(reopened), now_unix=1000.0, maximum_heartbeat_age_seconds=5
        )
        assert not result["ready"] and any("STOP_REQUESTED" in x for x in result["reason_codes"])
        with pytest.raises(ValueError, match="STOP_REQUESTED"):
            reopened.run_occupied_cycle_v1(pairs)
        assert not calls


def test_budget_recovery_required_is_not_overruled_by_healthy_session(tmp_path):
    manifest, _ = _setup(tmp_path)
    owner = _owner(tmp_path)
    try:
        with _session(manifest, tmp_path / "session") as opened:
            result = project_offline_session_readiness_v1(
                opened,
                process=_process(opened),
                now_unix=1000.0,
                maximum_heartbeat_age_seconds=5,
                portfolio_owner=owner,
            )
            assert (
                not result["ready"]
                and "PORTFOLIO_OWNER_RECOVERY_REQUIRED" in result["reason_codes"]
            )
    finally:
        owner.close()


def test_readiness_block_is_consumed_before_n1_and_preserves_original_attempt(
    tmp_path, monkeypatch
):
    manifest, pairs = _setup(tmp_path)
    calls = []
    monkeypatch.setattr(
        session_v1,
        "invoke_occupied_lane_governed_cycle_n1_consumer_v1",
        lambda *a, **kw: calls.append(kw),
    )
    with _session(manifest, tmp_path / "session") as opened:
        before = opened.state
        with pytest.raises(ValueError, match="READINESS_BLOCKED"):
            run_readiness_checked_offline_cycle_v1(
                opened,
                pairs,
                process=_process(opened, session_id="foreign"),
                now_unix=1000.0,
                maximum_heartbeat_age_seconds=5,
            )
        assert not calls and opened.state == before
        result = project_offline_session_readiness_v1(
            opened,
            process=_process(opened),
            now_unix=1000.0,
            maximum_heartbeat_age_seconds=5,
            action_scope="NEW_ENTRY",
        )
        assert (
            not result["ready"]
            and "NEW_ENTRY_FORBIDDEN_IN_OCCUPIED_EPISODE_PROFILE" in result["reason_codes"]
        )


def test_original_budget_commit_before_ack_is_recovered_without_new_hold(tmp_path):
    owner = _owner(tmp_path)
    scope = "a" * 64
    try:
        _auto(owner, tmp_path)
        held = _reserve(owner).reservation
        expected = replace(
            held,
            state=ReservationStateV1.COMMITTED,
            transition_trace=held.transition_trace + ("COMMITTED",),
        )
        request = HandoffRequestV1(
            scope,
            "commit-existing-hold",
            "bounded-offline-root",
            "original_budget",
            reservation_readback_digest_v1(held),
            reservation_readback_digest_v1(expected),
            "portfolio-reservation:" + str(held.reservation_id),
        )
        with OfflineHandoffJournalV1(
            root=tmp_path / "handoffs", session_manifest_digest=scope
        ) as journal:
            journal.prepare_v1(request)
            pending = recover_budget_handoff_ack_v1(
                journal,
                request,
                owner=owner,
                slot_id=held.slot_id,
                decision_id=held.decision_id,
                cycle_id=held.cycle_id,
                observation_id=held.observation_id,
            )
            assert pending["status"] == "RECOVERY_REQUIRED"
            committed = owner.commit_internal_pre_external_effect_v1(held.reservation_id)
            assert committed.disposition is ReserveDispositionV1.ADMITTED
            # Simulated loss of the consumer ACK; original durable commit stands.
    finally:
        owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        with OfflineHandoffJournalV1(
            root=tmp_path / "handoffs", session_manifest_digest=scope
        ) as journal:
            retained = {
                p.name: p.read_bytes() for p in (tmp_path / "handoffs").iterdir() if p.is_file()
            }
            result = recover_budget_handoff_ack_v1(
                journal,
                request,
                owner=owner,
                slot_id=held.slot_id,
                decision_id=held.decision_id,
                cycle_id=held.cycle_id,
                observation_id=held.observation_id,
            )
            assert result == {
                "status": "ACKNOWLEDGED",
                "automatic_owner_action": False,
                "resend_allowed": False,
            }
            assert owner.active_sum_v1() == 60 and owner.budget_state_v1().recovery_required
            assert owner.stored_reservation_count_v1() == 1
            for name, body in retained.items():
                assert (tmp_path / "handoffs" / name).read_bytes() == body
            assert (
                recover_budget_handoff_ack_v1(
                    journal,
                    request,
                    owner=owner,
                    slot_id=held.slot_id,
                    decision_id=held.decision_id,
                    cycle_id=held.cycle_id,
                    observation_id=held.observation_id,
                )
                == result
            )
            with pytest.raises(ValueError, match="CONFLICT"):
                journal.prepare_v1(replace(request, original_input_digest="b" * 64))
        with pytest.raises(ValueError, match="FOREIGN_SESSION"):
            with OfflineHandoffJournalV1(
                root=tmp_path / "handoffs", session_manifest_digest="b" * 64
            ):
                pass
    finally:
        owner.close()


@pytest.mark.parametrize("corrupt", ["prepared", "ack"])
def test_corrupt_coordination_records_cannot_acknowledge_or_change_owner(tmp_path, corrupt):
    scope = "a" * 64
    request = HandoffRequestV1(
        scope, "owner-edge", "source", "original_exit", "b" * 64, "c" * 64, "original-state-root"
    )
    with OfflineHandoffJournalV1(
        root=tmp_path / "journal", session_manifest_digest=scope
    ) as journal:
        journal.prepare_v1(request)
        journal.inspect_original_readback_v1(request, verified_original_output_digest="c" * 64)
        path = (
            next(p for p in (tmp_path / "journal").iterdir() if p.name.endswith("ack.json"))
            if corrupt == "ack"
            else journal._path(request)
        )
        path.write_text(json.dumps({"altered": True}))
        before = path.read_bytes()
        with pytest.raises(ValueError, match="CORRUPT"):
            journal.inspect_original_readback_v1(request, verified_original_output_digest="c" * 64)
        assert path.read_bytes() == before
