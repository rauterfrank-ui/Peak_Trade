#!/usr/bin/env python3
"""Persist GAP-TRUE-01 EXECUTABLE→Envelope→PRE_EXTERNAL evidence (transport-bound)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_root = str(REPO_ROOT)
if _root not in sys.path:
    sys.path.insert(0, _root)


def _main() -> int:
    parser = argparse.ArgumentParser(description="GAP-TRUE-01 evidence persist")
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--lane-state-root", type=Path, required=True)
    args = parser.parse_args()

    from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
        MockCurrentProductive29PIntegrityBackendV1,
    )
    from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
        governed_c1_candles_payload_from_enter_closes_v1,
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1 import (
        OWNER_GO,
        execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1,
    )
    from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
        _bound,
        _origin_main_sha,
        _productive_transport,
    )
    from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
        _produced_g17_producer,
    )

    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    g17 = _produced_g17_producer(instrument_id=bound.instrument_id)
    lanes_root = Path(args.lane_state_root)
    _arm, enter_closes, mark_px, event_ts = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=g17,
            lane_state_root=lanes_root,
        )
    )
    del _arm
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    result = execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        fresh_get_transport=_productive_transport(),
        lane_state_root=lanes_root,
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "gap-true-01-cli",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        evidence_root=args.evidence_root,
        execution_integrity_backend=integrity,
    )
    print(json.dumps({"store_root": result.store_root, "verdict": result.gap_true_01_verdict}))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
