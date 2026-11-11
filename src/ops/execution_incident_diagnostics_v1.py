"""Bounded, read-only execution incident observations independent of the order host."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from src.ops.execution_incident_safety_v1 import (
    ExecutionIncidentObservationError,
    OfflineExecutionIncidentScopeV1,
    observe_offline_execution_incident_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)


def iter_offline_execution_incident_diagnostics_v1(
    *,
    scope: OfflineExecutionIncidentScopeV1,
    envelope: FinalOrderEnvelopeV1,
    interval_seconds: float,
    samples: int,
) -> Iterator[dict]:
    """Read the original gate on each sample. A lost observation is never an all-clear."""
    if (
        type(samples) is not int
        or samples < 1
        or type(interval_seconds) not in (float, int)
        or not math.isfinite(interval_seconds)
        or interval_seconds <= 0
    ):
        raise ValueError("INCIDENT_DIAGNOSTIC_BOUNDS_INVALID")
    assert_envelope_unmodified_v1(envelope)
    for index in range(samples):
        if index:
            time.sleep(interval_seconds)
        try:
            observed = observe_offline_execution_incident_v1(scope=scope, envelope=envelope)
        except (ExecutionIncidentObservationError, OSError) as exc:
            yield {
                "observation_status": "UNAVAILABLE",
                "observation_error": (
                    str(exc)
                    if isinstance(exc, ExecutionIncidentObservationError)
                    else "INCIDENT_FILEGATE_READ_FAILED"
                ),
                "correlated_incident_veto": False,
            }
        else:
            yield {"observation_status": "OBSERVED", **observed}


def main(argv: list[str] | None = None) -> int:
    """Emit observations as JSON lines. Invoke through the repository launcher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    parser.add_argument("--envelope", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, required=True)
    parser.add_argument("--samples", type=int, required=True)
    args = parser.parse_args(argv)
    scope = OfflineExecutionIncidentScopeV1(
        args.root, args.account, args.session_id, args.started_at
    )
    envelope = FinalOrderEnvelopeV1(**json.loads(args.envelope.read_text()))
    for observation in iter_offline_execution_incident_diagnostics_v1(
        scope=scope, envelope=envelope, interval_seconds=args.interval_seconds, samples=args.samples
    ):
        print(json.dumps(observation, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
