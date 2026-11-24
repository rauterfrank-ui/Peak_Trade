"""Inspect a generation's Slot 4 Shadow handoff offline; exit 2 if COMMIT is blocked."""

import argparse
import json
from pathlib import Path

from src.ops.ranked_shadow_slot4_successor_v1 import (
    Slot4ShadowRecoveryRequired,
    prepare_slot4_shadow_rotation_v1,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predecessor-profile", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    args = parser.parse_args(argv)
    result = {
        "surface": "SHADOW",
        "lane": "LANE_4",
        "instrument": None,
        "authority": "NONE",
        "published": False,
    }
    try:
        portfolio, decision, digest = prepare_slot4_shadow_rotation_v1(
            args.predecessor_profile, args.evidence_root
        )
    except Slot4ShadowRecoveryRequired as exc:
        result.update(
            status="BLOCKED",
            reason=str(exc),
            recovery=exc.evidence,
            instrument=exc.evidence["assignment"]["venue_native_id"],
        )
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        AttributeError,
        ArithmeticError,
        RuntimeError,
    ) as exc:
        result.update(status="BLOCKED", reason=str(exc))
    else:
        result.update(
            instrument="PIEVERSE-USDT-SWAP",
            status="READY_FOR_ROTATION_REVIEW" if decision.allowed else "BLOCKED",
            reason=decision.reason_code,
            source_id=portfolio.source_id,
            event_time_unix=portfolio.event_time_unix,
            evidence_manifest_sha256=digest,
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "READY_FOR_ROTATION_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
