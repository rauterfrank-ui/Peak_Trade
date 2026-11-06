"""Test-only death checkpoint after the session charge, before a real N1 call."""

import signal
import sys
from pathlib import Path

from src.ops.bounded_peaktrade_system_composition_v1 import session_v1 as sessions
from src.ops.bounded_peaktrade_system_composition_v1.manifest_v1 import (
    load_offline_episode_session_manifest_v1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import IsolatedLaneSlotV1
from tests.ops.test_position_episode_exit_continuity_v1 import _bound


def main():
    manifest_path, root, checkpoint = map(Path, sys.argv[1:])
    manifest = load_offline_episode_session_manifest_v1(manifest_path)
    lane = manifest.lanes[0]
    bound = _bound()
    slot = IsolatedLaneSlotV1(
        lane_id=lane.identity.lane_id,
        occupancy="OCCUPIED",
        canonical_instrument_id=bound.instrument_id,
        lane_state_root=lane.cursor_state_root,
        universe_snapshot_id=bound.universe_snapshot_id,
        ranking_snapshot_id=bound.ranking_snapshot_id,
        ranking_integrity_digest=bound.ranking_integrity_digest,
    )

    def before_real_owner(*args, **kwargs):
        checkpoint.write_text("DURABLE_CHARGE_BEFORE_REAL_N1\n")
        signal.pause()  # parent kills this disposable worker
        raise RuntimeError("test worker must not continue")

    sessions.invoke_occupied_lane_governed_cycle_n1_consumer_v1 = before_real_owner
    with sessions.BoundedOfflineEpisodeSessionV1(
        manifest=manifest, state_root=root, mode="recover"
    ) as session:
        session.run_occupied_cycle_v1(
            {lane.identity.lane_id: (slot, bound)},
            origin_main_sha=manifest.origin_main_sha,
            cycle_id_prefix="physical-death-checkpoint",
            observed_unix=1700000300.0,
            last_finalized_event_ts_unix=1700000240.0,
        )


if __name__ == "__main__":
    main()
