"""Subprocess-only restart evaluation entry (test harness, not production).

Invoked after Process A (hard-crash child) to prove evaluation in a fresh interpreter.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.ops._current_productive_post_hard_crash_harness_v1 import (  # noqa: E402
    CrashPointV1,
    evaluate_restart_after_crash_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (  # noqa: E402
    _new_risk_envelope,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store-root", required=True)
    parser.add_argument("--crash-point", default="C9")
    args = parser.parse_args()
    store = Path(args.store_root)
    point = CrashPointV1(args.crash_point)
    env = _new_risk_envelope()
    restart = evaluate_restart_after_crash_v1(
        store_root=store,
        crash_point=point,
        first_envelope=env,
    )
    payload = {
        "durable_consumed": restart.durable_consumed,
        "durable_state": restart.durable_state,
        "second_admission_blocked": restart.second_admission_blocked,
        "second_admission_reason": restart.second_admission_reason,
        "mock_post_attempts_after_restart": restart.mock_post_attempts_after_restart,
        "replay_attempt_executed": restart.replay_attempt_executed,
        "notes": list(restart.notes),
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
