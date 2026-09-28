"""Post-6948 productive continuous-run authority / Live-C1 convergence (no runtime)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.governance.post_6948_productive_continuous_run_authority_live_c1_convergence_v1 import (  # noqa: E402
    WORKPACKAGE_ID,
    build_convergence_report_v1,
)


def _origin_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()


def main() -> int:
    report = build_convergence_report_v1(repo_root=REPO, baseline_sha=_origin_sha())
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"WORKPACKAGE_ID={WORKPACKAGE_ID}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
