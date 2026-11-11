"""Disposable real N1 worker for physical technical-restart tests only."""

from dataclasses import asdict, replace
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

    def wrapped_factory(**kwargs):
        runner = original(**kwargs)
        calls = 0

        def run(**kw):
            nonlocal calls
            calls += 1
            if phase == "during" and calls == 2:
                write_json(
                    root / "checkpoint.json",
                    {"pid": os.getpid(), "cursor": str(cursor / CURSOR_FILENAME)},
                )
                threading.Event().wait()
            return runner(**kw)

        return run

    with patch.object(convergence, "make_n1_occupied_lane_s5_runner_v1", wrapped_factory):
        result = run_unattended_n1_host_v1(
            bounds=bounds, state_root=root / "controller", request_factory=factory
        )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
