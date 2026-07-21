#!/usr/bin/env python3
"""Run exactly one preregistered DEVELOPMENT midband exit-efficiency evaluation.

Research-only. No holdout. No runtime / orders / productive authority mutation.

Lifecycle observability: catchable signals, durable member progress, and
exception diagnostics are persisted under the output directory. Incomplete runs
are classified as INCONCLUSIVE_INFRASTRUCTURE_FAILURE without auto-rerun.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.constants_v1 import (  # noqa: E402
    EVALUATION_RUN_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.panel_runner_v1 import (  # noqa: E402
    run_development_evaluation,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (  # noqa: E402
    DEV_PANEL_SUBDIR,
)
from src.research.evaluation_runner_lifecycle_observability_v1 import (  # noqa: E402
    EvaluationRunnerLifecycleObservabilityV1,
)


def _default_archive_root() -> Path | None:
    env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
    if not env:
        return None
    return Path(env).expanduser().resolve() / DEV_PANEL_SUBDIR


def _slot_already_consumed(output_dir: Path) -> bool:
    summary_path = output_dir / "summary.json"
    if not summary_path.is_file():
        return False
    try:
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return int(existing.get("evaluation_run_count") or 0) >= 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Bollinger/MR midband exit-efficiency (DEVELOPMENT, one run)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT
        / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v1",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help="Optional sealed DEVELOPMENT panel archive root override.",
    )
    args = parser.parse_args()
    archive = args.archive_root
    if archive is None:
        archive = _default_archive_root()
        if archive is None:
            raise SystemExit("PEAK_TRADE_DATA_ARCHIVE_ROOT_UNSET")

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fail-closed before lifecycle attach so a consumed slot cannot pollute
    # historical evidence SSOT with new heartbeat/terminal files.
    if _slot_already_consumed(output_dir):
        print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
        print("REASON=EVALUATION_RUN_SLOT_ALREADY_CONSUMED")
        print("EVALUATION_RUN_COUNT=1")
        print("HOLDOUT_DATA_ACCESSED=false")
        print("AUTO_RERUN_EXECUTED=false")
        return 2

    lifecycle = EvaluationRunnerLifecycleObservabilityV1(
        output_dir,
        run_id=EVALUATION_RUN_ID,
    )
    lifecycle.install_signal_handlers()
    try:
        summary = run_development_evaluation(
            output_dir=output_dir,
            archive_root=archive,
            lifecycle=lifecycle,
        )
    except Exception as exc:  # noqa: BLE001 — persist then fail-closed
        terminal = lifecycle.record_exception(exc)
        print(f"RESULT_CLASS={terminal.get('result_class')}")
        print(f"REASON={terminal.get('death_class')}")
        print("EVALUATION_RUN_COUNT_UNCHANGED_BY_LIFECYCLE=true")
        print("HOLDOUT_DATA_ACCESSED=false")
        print("AUTO_RERUN_EXECUTED=false")
        return 1
    finally:
        lifecycle.uninstall_signal_handlers()

    print(f"RESULT_CLASS={summary.get('result_class')}")
    print(f"REASON={summary.get('decision', {}).get('reason')}")
    print(f"EVALUATION_RUN_COUNT={summary.get('evaluation_run_count')}")
    print(f"HOLDOUT_DATA_ACCESSED={summary.get('holdout_data_accessed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
