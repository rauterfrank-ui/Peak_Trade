#!/usr/bin/env python3
"""Release sealed DEVELOPMENT panel from quarantine to default archive layout.

Does not authorize evaluation. Does not start runners. Does not touch holdout.

  PEAK_TRADE_DATA_ARCHIVE_ROOT=/Users/frnkhrz/Peak_Trade_data_archive \\
  PYTHONPATH=src:. python3 scripts/research/run_release_independent_dev_panel_quarantine_v1.py \\
    --mode preflight

  PEAK_TRADE_DATA_ARCHIVE_ROOT=/Users/frnkhrz/Peak_Trade_data_archive \\
  PYTHONPATH=src:. python3 scripts/research/run_release_independent_dev_panel_quarantine_v1.py \\
    --mode release
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.independent_dev_panel_quarantine_release_v1 import (  # noqa: E402
    PanelQuarantineReleaseError,
    preflight_quarantine_release,
    release_quarantine_panel,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Byte-identical quarantine release for independent DEVELOPMENT panel."
    )
    parser.add_argument("--mode", choices=("preflight", "release"), default="preflight")
    parser.add_argument("--archive-root", type=Path, default=None)
    args = parser.parse_args(argv)

    archive = args.archive_root
    if archive is None:
        env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
        archive = Path(env).expanduser() if env else None

    try:
        if args.mode == "preflight":
            summary = preflight_quarantine_release(archive_root=archive, repo_root=REPO_ROOT)
            print("MODE=preflight")
            print(f"PASSED={summary.get('passed')}")
            print(f"SOURCE={summary.get('source_path')}")
            print(f"TARGET={summary.get('target_path')}")
            print(f"TARGET_EXISTS={summary.get('target_exists')}")
            print("RUNNER_STARTED=false")
            print("EVALUATION_AUTHORIZED=false")
            print("HOLDOUT_DATA_ACCESSED=false")
            return 0 if summary.get("passed") else 1

        summary = release_quarantine_panel(
            archive_root=archive, repo_root=REPO_ROOT, write_repo_evidence=True
        )
        print("MODE=release")
        print(f"PANEL_RELEASED={summary.get('panel_released')}")
        print(f"STATUS={summary.get('status')}")
        print(f"RELEASE_MODE={summary.get('release_mode')}")
        print(f"TARGET={summary.get('target_path')}")
        print("RUNNER_STARTED=false")
        print("EVALUATION_AUTHORIZED=false")
        print("HOLDOUT_DATA_ACCESSED=false")
        return 0 if summary.get("panel_released") else 1
    except PanelQuarantineReleaseError as exc:
        print(f"RESULT=FAIL")
        print(f"REASON={exc}")
        print("RUNNER_STARTED=false")
        print("HOLDOUT_DATA_ACCESSED=false")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
