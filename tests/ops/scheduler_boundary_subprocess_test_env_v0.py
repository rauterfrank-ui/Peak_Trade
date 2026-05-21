"""Non-authorizing preflight override for subprocess harness tests only."""

from __future__ import annotations

import json

_ALLOWED_SUBPROCESS_PREFLIGHT = {
    "status": "READY",
    "scheduler_execution_authorized": True,
    "hold_context_v0": {"current_state": "CLEAR"},
}


def scheduler_boundary_subprocess_test_env() -> dict[str, str]:
    return {
        "PEAK_TRADE_SCHEDULER_BOUNDARY_TEST_PREFLIGHT_JSON": json.dumps(
            _ALLOWED_SUBPROCESS_PREFLIGHT
        ),
    }
