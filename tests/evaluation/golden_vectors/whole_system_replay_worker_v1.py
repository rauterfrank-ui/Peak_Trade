"""Subprocess worker: BWP-9 whole-system protected digest (cross-process determinism)."""

from __future__ import annotations

import json
import os
import sys

from tests.evaluation.golden_vectors.whole_system_fixtures_v1 import run_whole_system_success


def main() -> int:
    record = run_whole_system_success(unique_run=True, verify_replay=True)
    out = {
        "protected_output_digest": record.protected_output_digest,
        "state_sequence": [s.value for s in record.state_history],
        "registry_ref": record.registry_ref,
        "promotion_digest": (
            record.promotion_envelope.evidence_digest if record.promotion_envelope else ""
        ),
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "tz": os.environ.get("TZ", ""),
    }
    sys.stdout.write(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
