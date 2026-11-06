"""Every Exit publication swap and both original submit barriers stay fail closed."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import (
    OfflineHandoffJournalV1,
    HandoffRequestV1,
)
from src.ops.bounded_peaktrade_system_composition_v1.recovery_v1 import (
    recover_exit_handoff_ack_v1,
    recover_budget_handoff_ack_v1,
)
from src.ops.exit_policy_producer_binding_v1 import persistence_v1 as exits
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    EXIT_STATE_FILENAME,
    COMMIT_MARKER_FILENAME,
    MANIFEST_FILENAME,
)
from tests.ops.test_bounded_offline_episode_session_v1 import _setup, _session
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner


@pytest.mark.parametrize("crash_after", [0, 1, 2, 3])
def test_each_exit_owner_swap_is_either_verified_original_or_recovery_required(
    tmp_path, monkeypatch, crash_after
):
    manifest, _ = _setup(tmp_path)
    with _session(manifest, tmp_path / "session") as opened:
        episode = opened._episodes["LANE_1"]
        state = episode.binding.to_canonical_state()
        next_state = replace(state, commit_sequence=state.commit_sequence + 1)
        root = Path(episode.binding.state_root)
        request = HandoffRequestV1(
            manifest.digest(),
            "original-exit-swap",
            "original-exit-writer",
            "original_exit",
            state.digest(),
            next_state.digest(),
            str(root),
        )
        with OfflineHandoffJournalV1(
            root=tmp_path / "journal", session_manifest_digest=manifest.digest()
        ) as journal:
            journal.prepare_v1(request)
            original = exits.os.replace
            swaps = 0

            def interrupt(source, target):
                nonlocal swaps
                target = Path(target)
                is_owner = target.parent == root and target.name in {
                    EXIT_STATE_FILENAME,
                    COMMIT_MARKER_FILENAME,
                    MANIFEST_FILENAME,
                }
                if is_owner and swaps == crash_after:
                    raise OSError("injected exit publication crash")
                original(source, target)
                if is_owner:
                    swaps += 1
                    if swaps == 3 and crash_after == 3:
                        raise OSError("injected exit publication crash")

            with monkeypatch.context() as m:
                m.setattr(exits.os, "replace", interrupt)
                with pytest.raises(OSError, match="publication crash"):
                    exits.persist_exit_policy_state_atomic_v1(
                        state_root=root,
                        state=next_state,
                        writer_session_id="crash-control",
                        expected_prior_sequence=state.commit_sequence,
                    )
            retained = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
            if crash_after in {1, 2}:
                with pytest.raises(RuntimeError):
                    recover_exit_handoff_ack_v1(
                        journal,
                        request,
                        state_root=root,
                        repository_sha=state.repository_sha,
                        config_digest=state.config_digest,
                        instrument_id=state.instrument_id,
                    )
            else:
                result = recover_exit_handoff_ack_v1(
                    journal,
                    request,
                    state_root=root,
                    repository_sha=state.repository_sha,
                    config_digest=state.config_digest,
                    instrument_id=state.instrument_id,
                )
                assert result["status"] == (
                    "ACKNOWLEDGED" if crash_after == 3 else "RECOVERY_REQUIRED"
                )
            assert all((root / name).read_bytes() == body for name, body in retained.items())


def test_fresh_process_recovers_original_commit_without_consumer_ack(tmp_path):
    script = r"""
from pathlib import Path
from dataclasses import replace
import os,sys
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner,_auto,_reserve
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReservationStateV1
from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import OfflineHandoffJournalV1,HandoffRequestV1
from src.ops.bounded_peaktrade_system_composition_v1.recovery_v1 import reservation_readback_digest_v1
root=Path(sys.argv[1])
owner=_owner(root)
_auto(owner,root)
held=_reserve(owner).reservation
expected=replace(held,state=ReservationStateV1.COMMITTED,transition_trace=held.transition_trace+("COMMITTED",))
request=HandoffRequestV1("a"*64,"physical-commit-before-ack","original-budget","original_budget",
    reservation_readback_digest_v1(held),reservation_readback_digest_v1(expected),"portfolio-reservation:"+str(held.reservation_id))
with OfflineHandoffJournalV1(root=root/"journal",session_manifest_digest="a"*64) as journal:
    journal.prepare_v1(request)
    owner.commit_internal_pre_external_effect_v1(held.reservation_id)
    os._exit(93)
"""
    result = subprocess.run(
        ["./scripts/pt", "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 93, result.stderr
    owner = _owner(tmp_path, "recover")
    try:
        prepared = next(
            p
            for p in (tmp_path / "journal").iterdir()
            if p.name != "scope.json" and p.name != "writer.lock"
        )
        request = HandoffRequestV1(**json.loads(prepared.read_text())["request"])
        records = owner.risk_snapshot_v1()["state"]["reservations"]
        assert len(records) == 1
        record = records[0]
        with OfflineHandoffJournalV1(
            root=tmp_path / "journal", session_manifest_digest="a" * 64
        ) as journal:
            result = recover_budget_handoff_ack_v1(
                journal,
                request,
                owner=owner,
                slot_id=record["slot_id"],
                decision_id=record["decision_id"],
                cycle_id=record["cycle_id"],
                observation_id=record["observation_id"],
            )
        assert result["status"] == "ACKNOWLEDGED" and not result["resend_allowed"]
        assert owner.active_sum_v1() == 60 and owner.budget_state_v1().recovery_required
    finally:
        owner.close()


def test_actual_risk_reservation_commit_before_ack_survives_physical_process_exit(tmp_path):
    script = r"""
from pathlib import Path
import os,sys
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner,_auto
from tests.ops.test_bounded_offline_decision_risk_v1 import _request,_admit
from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import OfflineHandoffJournalV1
root=Path(sys.argv[1])
owner=_owner(root)
_auto(owner,root)
with OfflineHandoffJournalV1(root=root/"journal",session_manifest_digest="a"*64) as journal:
    journal.inspect_original_readback_v1=lambda *a,**kw:os._exit(94)
    _admit(owner,_request(),handoff_journal=journal)
raise AssertionError("expected exit after actual commit")
"""
    result = subprocess.run(
        ["./scripts/pt", "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 94, result.stdout + result.stderr
    owner = _owner(tmp_path, "recover")
    try:
        assert owner.active_sum_v1() == 100 and owner.budget_state_v1().recovery_required
        from tests.ops.test_durable_portfolio_budget_recovery_v1 import _auto
        from tests.ops.test_bounded_offline_decision_risk_v1 import _request, _admit
        from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReserveDispositionV1

        _auto(owner, tmp_path)
        record = owner.risk_snapshot_v1()["state"]["reservations"][0]
        prepared = next(
            p
            for p in (tmp_path / "journal").iterdir()
            if p.name not in {"scope.json", "writer.lock"}
        )
        request = HandoffRequestV1(**json.loads(prepared.read_text())["request"])
        with OfflineHandoffJournalV1(
            root=tmp_path / "journal", session_manifest_digest="a" * 64
        ) as journal:
            replay = _admit(owner, _request(), handoff_journal=journal)
            assert replay.disposition is ReserveDispositionV1.FAIL_CLOSED
            assert replay.reason_codes == ("HANDOFF_ORIGINAL_READBACK_ACK_REQUIRED",)
            ack = recover_budget_handoff_ack_v1(
                journal,
                request,
                owner=owner,
                slot_id=record["slot_id"],
                decision_id=record["decision_id"],
                cycle_id=record["cycle_id"],
                observation_id=record["observation_id"],
            )
        assert ack["status"] == "ACKNOWLEDGED"
        assert owner.reservation_risk_binding_v1(record["reservation_id"]).final_quantity == "1.00"
        with OfflineHandoffJournalV1(
            root=tmp_path / "journal", session_manifest_digest="a" * 64
        ) as journal:
            replay = _admit(owner, _request(), handoff_journal=journal)
            assert replay.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY
        assert owner.stored_reservation_count_v1() == 1 and owner.active_sum_v1() == 100
    finally:
        owner.close()


@pytest.mark.parametrize("crash_at", ["before-first", "between", "after-second"])
def test_no_submit_retry_after_any_original_durable_barrier(tmp_path, monkeypatch, crash_at):
    from tests.ops.test_portfolio_execution_recovery_v1 import seed
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
        _handle,
    )
    from src.ops.full_core_live_path_composition_root_v1 import (
        envelope_bound_external_effect_send_seam_v1 as send,
    )
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
    )

    host, rid, identity, envelope = seed(tmp_path)
    calls = []

    class Transport:
        def post_trade_order(self, **kw):
            calls.append(kw)
            raise RuntimeError("interrupted after both barriers before transport response")

    kwargs = dict(
        envelope=envelope,
        permit=_permit(envelope),
        store_root=tmp_path / "send",
        transport=Transport(),
        handle=_handle(),
        portfolio_budget_owner=host.owner,
        portfolio_reservation_id=rid,
        execution_identity=identity,
    )
    try:
        if crash_at == "before-first":
            original = host.owner.mark_execution_submit_boundary_v1
            monkeypatch.setattr(
                host.owner,
                "mark_execution_submit_boundary_v1",
                lambda *a, **kw: (_ for _ in ()).throw(OSError("before first barrier")),
            )
        elif crash_at == "between":
            monkeypatch.setattr(
                send,
                "persist_external_effect_durable_consume_v1",
                lambda **kw: (_ for _ in ()).throw(OSError("between barriers")),
            )
        with pytest.raises((OSError, RuntimeError)):
            send.attempt_envelope_bound_external_effect_send_v1(**kwargs)
        phase = host.owner.execution_links_v1()[rid]["phase"]
        assert phase == ("PLAN_BOUND" if crash_at == "before-first" else "SUBMIT_MAY_HAVE_OCCURRED")
        assert len(calls) == int(crash_at == "after-second")
        if crash_at == "between":
            assert not load_external_effect_durable_consume_v1(store_root=tmp_path / "send").get(
                "durable_consumed"
            )
        if crash_at != "before-first":
            with pytest.raises((RuntimeError, ValueError)):
                send.attempt_envelope_bound_external_effect_send_v1(**kwargs)
            assert len(calls) == int(crash_at == "after-second")
        assert host.owner.active_sum_v1() > 0
    finally:
        host.close()
