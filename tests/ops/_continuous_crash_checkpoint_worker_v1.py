"""Disposable offline subprocess for the S6/S7 crash-checkpoint regression."""

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import threading
from unittest.mock import patch

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_persistent_natural_enter_convergence_v1 as convergence,
)

from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
    run_offline_persistent_natural_enter_convergence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json
from tests.ops.test_current_productive_persistent_natural_enter_convergence_v1 import (
    _bound_lane_1,
    _lane_g17,
    _continuous_auth,
    _cursor_floor_or_zero,
    _observation_from_closes,
    build_s8_occupied_lane_pairs_v1,
    ORIGIN_SHA,
    _FakeClock,
    bootstrap_s8_lane_via_s7_compose_v1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    strong_uptrend_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("before", "during", "after", "old-ledger"))
    args = parser.parse_args()
    root = args.root
    bound = _bound_lane_1()
    lane = root / "lane"
    pairs = build_s8_occupied_lane_pairs_v1(lane_state_root=lane, bound=bound)
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    path = strong_uptrend_closes_v1(count=128)
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120)
    boot = _observation_from_closes(closes=path[:104], event_ts=t0 - 60)
    first = _observation_from_closes(closes=path[:106], event_ts=t0)
    second = _observation_from_closes(closes=path[:108], event_ts=t0 + 60)
    if not (cursor_root / CURSOR_FILENAME).exists():
        bootstrap_s8_lane_via_s7_compose_v1(
            composed_pairs=pairs,
            origin_main_sha=ORIGIN_SHA,
            g17_producers=_lane_g17(pairs),
            candles_payload=boot.candles_payload,
            mark_price_payload=boot.mark_price_payload,
            venue_native_id=str(bound.venue_native_id),
            index_tickers_payload=boot.index_tickers_payload,
            mark_acquired_at_utc=boot.mark_acquired_at_utc,
        )
    floor = _cursor_floor_or_zero(cursor_root)

    class Source:
        polls = 0

        def poll(self):
            self.polls += 1
            if args.phase == "before" and self.polls == 2:
                # S5/S7 and cursor advancement have finished; we are outside a
                # cycle, inside observation polling. Parent kills this process.
                write_json(
                    root / "checkpoint.json",
                    {"pid": os.getpid(), "cursor": str(cursor_root / CURSOR_FILENAME)},
                )
                threading.Event().wait()
            return first if self.polls == 1 else second

    clock = _FakeClock()
    auth = replace(
        _continuous_auth(
            native_id=str(bound.venue_native_id),
            max_cycles=2 if args.phase in {"before", "during"} else 1,
        ),
        expected_cursor_floor=floor,
    )
    real_factory = convergence.make_n1_occupied_lane_s5_runner_v1

    def factory(**kwargs):
        runner = real_factory(**kwargs)
        calls = 0

        def wrapped(**cycle):
            nonlocal calls
            calls += 1
            if args.phase == "during" and calls == 2:
                write_json(
                    root / "checkpoint.json",
                    {"pid": os.getpid(), "cursor": str(cursor_root / CURSOR_FILENAME)},
                )
                threading.Event().wait()
            return runner(**cycle)

        return wrapped

    with patch.object(convergence, "make_n1_occupied_lane_s5_runner_v1", factory):
        result = run_offline_persistent_natural_enter_convergence_v1(
            authorization=auth,
            origin_main_sha=ORIGIN_SHA,
            lane_state_root=lane,
            bound=bound,
            g17_producers=_lane_g17(pairs),
            observation_source=Source(),
            bootstrap_observation=boot,
            evidence_root=root
            / ("before" if args.phase in {"before", "during", "old-ledger"} else "after"),
            lock_root=root / "shared_lock",
            time_fn=clock.time,
            sleep_fn=clock.sleep,
        )
    print(
        json.dumps(
            {
                "cycles": result.cycles_completed,
                "post_count": result.post_count,
                "external_effect_count": result.external_effect_count,
                "permit_created": result.permit_created,
                "accepted": [r.c1_venue_event_time for r in result.cycle_records],
                "consume_ids": result.consume_instance_ids,
                "floor_before": result.cursor_floor_before,
                "floor_after": result.cursor_floor_after,
            }
        )
    )


if __name__ == "__main__":
    main()
