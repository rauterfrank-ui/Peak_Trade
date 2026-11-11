"""Disposable real N1 worker for physical technical-restart tests only."""

from dataclasses import asdict, replace
from contextlib import ExitStack
import json
import os
from pathlib import Path
import sys
import threading
import time
from unittest.mock import patch

from src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1 import (
    UnattendedHostBoundsV1,
    run_unattended_n1_host_v1,
    unattended_request_digest_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json
from src.ops.gates.risk_gate import canonical_kill_switch_state_path
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops._n1_standing_supervisor_offline_inject_harness_v1 import (
    bootstrap_lane,
    supervisor_config_from_roots,
    seed_public_marks,
    f1_m9_evaluator_factory,
    public_rest_empty,
    _fixture_rest,
    OWNER_GO_BASELINE_SHA,
)
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _bound_lane_1,
    _lane_g17,
    _continuous_auth,
    _observation_from_closes,
    strong_uptrend_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
    build_s8_occupied_lane_pairs_v1,
    _cursor_floor_or_zero,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _FakeClock,
)
import src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 as convergence
import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 as s6
import src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 as s5


def main():
    root, phase = Path(sys.argv[1]), sys.argv[2]
    repo = Path(__file__).resolve().parents[2]
    if not (root / "lane_state").exists():
        seed_public_marks(root / "public_store")
        bootstrap_lane(session_root=root, repo_root=repo)
    bound = _bound_lane_1()
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=root / "lane_state", bound=bound)
    cursor = Path(pairs["LANE_1"][0].lane_state_root)
    g17 = _lane_g17(pairs)
    path = strong_uptrend_closes_v1(count=128)
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120)
    first = _observation_from_closes(closes=path[:106], event_ts=t0)
    second = _observation_from_closes(closes=path[:108], event_ts=t0 + 60)

    def factory(index, evidence):
        class Source:
            polls = 0

            def poll(self):
                self.polls += 1
                if phase == "before" and index == 1 and self.polls == 2:
                    write_json(
                        root / "checkpoint.json",
                        {"pid": os.getpid(), "cursor": str(cursor / CURSOR_FILENAME)},
                    )
                    threading.Event().wait()
                return first if self.polls == 1 else second

        clock = _FakeClock()
        original_evaluator = f1_m9_evaluator_factory(repo_root=repo, ledger_root=root / "f1")

        def evaluate(cycle_index):
            decision = original_evaluator(cycle_index)
            if phase in {"kill-during-admission", "reactivated-during-admission"} and index == 2:
                filegate = StatePersistence(canonical_kill_switch_state_path())
                filegate.save(
                    KillSwitchState.KILLED, trigger_reason="fixture kill during N1 admission"
                )
                if phase == "reactivated-during-admission":
                    filegate.save(KillSwitchState.ACTIVE)
            return decision

        return dict(
            config=supervisor_config_from_roots(
                public_store=root / "public_store",
                private_store=root / "private_store",
                lane_state=root / "lane_state",
                evidence_root=evidence,
                lock_root=root / "shared_lock",
            ),
            origin_main_sha=OWNER_GO_BASELINE_SHA,
            bound=bound,
            authorization=replace(
                _continuous_auth(native_id=bound.venue_native_id, max_cycles=2),
                expected_cursor_floor=_cursor_floor_or_zero(cursor),
            ),
            observation_source=Source(),
            g17_producers=g17,
            f1_m9_cycle_evaluator=evaluate,
            repo_root=repo,
            public_rest_fetch=public_rest_empty,
            private_rest_fetch=_fixture_rest,
            time_fn=clock.time,
            sleep_fn=clock.sleep,
        )

    ticket = root / "bounds.json"
    if not ticket.exists():
        bounds = UnattendedHostBoundsV1(
            host_id="offline-host-crash-proof",
            repository_sha=OWNER_GO_BASELINE_SHA,
            runtime_config_digest=unattended_request_digest_v1(factory(1, root / "unused")),
            expires_at_unix=time.time() + 120,
            max_total_cycles=2,
            max_total_seconds=120,
            wait_interval_seconds=0.01,
        )
        write_json(ticket, asdict(bounds))
    bounds = UnattendedHostBoundsV1(**json.loads(ticket.read_text()))
    original = convergence.make_n1_occupied_lane_s5_runner_v1

    def signal_checkpoint(**details):
        write_json(
            root / "checkpoint.json",
            {"pid": os.getpid(), "cursor": str(cursor / CURSOR_FILENAME), **details},
        )
        threading.Event().wait()

    def wrapped_factory(**kwargs):
        runner = original(**kwargs)
        calls = 0

        def run(**kw):
            nonlocal calls
            calls += 1
            if phase in {"during", "managed-restore-wait"} and calls == 2:
                signal_checkpoint()
            if phase == "managed-partial-s5" and calls == 2:
                (root / "before-partial-s5-cursor.json").write_bytes(
                    (cursor / CURSOR_FILENAME).read_bytes()
                )
            return runner(**kw)

        return run

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(convergence, "make_n1_occupied_lane_s5_runner_v1", wrapped_factory)
        )
        if phase in {"managed-hold-publish", "managed-restore-wait", "managed-joint-rollback"}:
            original_write = s6._persist_json

            def write(*, path, payload):
                if payload.get("reason_code") == "HOLD_WAIT_NEXT_FRESH_C1":
                    if phase == "managed-hold-publish":
                        signal_checkpoint(consume_id=payload["consumed_instance_ids"][-1])
                    else:
                        (root / "earlier-wait.json").write_text(s6.canonical_json_text(payload))
                        if phase == "managed-joint-rollback":
                            (root / "earlier-cursor.json").write_bytes(
                                (cursor / CURSOR_FILENAME).read_bytes()
                            )
                            (root / "earlier-filegate.json").write_bytes(
                                Path(canonical_kill_switch_state_path()).read_bytes()
                            )
                original_write(path=path, payload=payload)

            stack.enter_context(patch.object(s6, "_persist_json", write))
        if phase == "managed-partial-s5":
            original_s5_write = s5._persist_json

            def write_s5(*, path, payload):
                if (
                    path.name == s5.LEDGER_FILENAME
                    and payload.get("state") == s5.STATE_COMPLETED
                    and (root / "before-partial-s5-cursor.json").exists()
                ):
                    signal_checkpoint(s5_ledger=str(path))
                original_s5_write(path=path, payload=payload)

            stack.enter_context(patch.object(s5, "_persist_json", write_s5))
        if phase == "managed-joint-rollback":
            original_advance = s6._advance_persisted_c1_cursor_floor_v1

            def advance(**kwargs):
                original_advance(**kwargs)
                if (root / "earlier-cursor.json").exists():
                    signal_checkpoint()

            stack.enter_context(patch.object(s6, "_advance_persisted_c1_cursor_floor_v1", advance))
        if phase in {"after-managed-boot", "after-managed-joint-rollback"}:
            for module in (
                "src.ops.n1_standing_pre_external_runtime_supervisor_v1.unattended_v1",
                "src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1",
            ):
                stack.enter_context(
                    patch(
                        module + ".read_local_boot_identity_v1", return_value="synthetic-new-boot"
                    )
                )
        host_options = {}
        if phase in {"after-managed-monitor", "after-managed-joint-rollback"}:
            from nacl.signing import SigningKey

            from src.ops.managed_fault_recovery_v1 import ManagedFaultRecoveryV1
            from src.ops.managed_filegate_v1 import configured_filegate_writer_v1

            held_polls = 0

            def confirm_hold(_):
                nonlocal held_polls
                receipt = root / "controller" / "host_restart_state_v1.json"
                persisted = json.loads(receipt.read_bytes())
                assert persisted["status"] == "RECOVERY_CHECKPOINT_REQUIRED"
                assert persisted["attempts"] == 1
                if phase == "after-managed-joint-rollback":
                    observed = persisted["last_fault_observation"]
                    assert observed["status"] == "BLOCKED_OBSERVING"
                    assert observed["stop"]["causes"] == ["R03", "R09"]
                held_polls += 1
                if held_polls == 2:
                    (root / "controller" / "STOP").touch()

            host_options = {
                "fault_recovery": ManagedFaultRecoveryV1(
                    writer=configured_filegate_writer_v1(canonical_kill_switch_state_path()),
                    issuer_key=SigningKey.generate(),
                    observations={role: lambda _: None for role in ("CAUSE", "ACCOUNT", "HOST")},
                    interval_seconds=1,
                ),
                "sleeper": confirm_hold,
            }
        result = run_unattended_n1_host_v1(
            bounds=bounds, state_root=root / "controller", request_factory=factory, **host_options
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
