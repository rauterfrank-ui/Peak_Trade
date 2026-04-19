"""Legacy entry point retired; use canonical reconciler directly."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "ERROR: scripts/ci/required_checks_drift_detector.py is retired and unsupported. "
        "Use scripts/ops/reconcile_required_checks_branch_protection.py --check.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
