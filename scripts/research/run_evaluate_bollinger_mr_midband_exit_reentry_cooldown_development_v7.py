#!/usr/bin/env python3
"""Canonical V7 entry point for Bollinger/MR midband reentry-cooldown evaluation.

Default mode is preflight-only (no slot claim, no panel access, no evaluation).

Future single authorized DEVELOPMENT evaluation (DO NOT run in implementation slice):

  PYTHONPATH=src:. python3 scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7.py \\
    --mode evaluate \\
    --authorize-single-development-evaluation BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7 \\
    --output-dir docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7 \\
    --archive-root \"$PEAK_TRADE_DATA_ARCHIVE_ROOT/dev_pre_holdout_panel_v1_20260720T2052Z\"

Generic LIVE/SHADOW/TESTNET/SCHEDULER flags cannot authorize this runner.
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

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.constants_v7 import (  # noqa: E402
    HYPOTHESIS_ID,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.hypothesis_dispatch_v7 import (  # noqa: E402
    resolve_v7_dispatch,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7.panel_runner_v7 import (  # noqa: E402
    run_development_evaluation,
    run_preflight_only,
)
from src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1 import (  # noqa: E402
    DEV_PANEL_SUBDIR,
)


def _default_archive_root() -> Path | None:
    env = os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT")
    if not env:
        return None
    return Path(env).expanduser().resolve() / DEV_PANEL_SUBDIR


def _slot_already_consumed(output_dir: Path) -> bool:
    if (output_dir / "run_slot_claim.json").is_file():
        return True
    summary_path = output_dir / "summary.json"
    if not summary_path.is_file():
        return False
    try:
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return int(existing.get("evaluation_run_count", -1)) >= 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "V7 Bollinger/MR reentry-cooldown DEVELOPMENT entry point (default: preflight-only)."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("preflight", "evaluate"),
        default="preflight",
        help="preflight (default) or evaluate (requires explicit authorization).",
    )
    parser.add_argument(
        "--authorize-single-development-evaluation",
        default="",
        help=f"Must equal {HYPOTHESIS_ID} to authorize evaluate mode.",
    )
    preflight_default = (
        REPO_ROOT / "docs/evidence/preflight_bollinger_mr_midband_exit_reentry_cooldown_v7_wiring"
    )
    evaluate_default = (
        REPO_ROOT
        / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Output directory. Preflight defaults to wiring preflight path; "
            "evaluate defaults to evaluate evidence path (created only after auth)."
        ),
    )
    parser.add_argument("--archive-root", type=Path, default=None)
    # Explicitly ignore generic runtime switches if somehow passed via env wrappers.
    parser.add_argument("--live", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--shadow", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--testnet", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--scheduler", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.live or args.shadow or args.testnet or args.scheduler:
        print("RESULT_CLASS=CONTRACT_INFRA_RESULT_CLASS_UNRESOLVED_BLOCKER")
        print("REASON=GENERIC_RUNTIME_SWITCH_CANNOT_AUTHORIZE_V7")
        return 2

    # Dispatch binding proof (fail-closed if hypothesis unbound).
    resolve_v7_dispatch(HYPOTHESIS_ID)

    if args.mode == "preflight":
        output_dir: Path = args.output_dir or preflight_default
        summary = run_preflight_only(output_dir=output_dir, repo_root=REPO_ROOT)
        print("MODE=preflight")
        print(f"PASSED={summary.get('passed')}")
        print(f"RESULT_CLASS={summary.get('result_class')}")
        print("EVALUATION_RUN_COUNT=0")
        print("RUNNER_STARTED=false")
        print("RUN_SLOT_CLAIMED=false")
        print("PANEL_DATA_ACCESSED=false")
        print("HOLDOUT_DATA_ACCESSED=false")
        return 0 if summary.get("passed") else 1

    # evaluate mode — do not create evaluate evidence dir before authorization
    auth = str(args.authorize_single_development_evaluation or "")
    if auth != HYPOTHESIS_ID:
        print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
        print("REASON=V7_EVALUATION_NOT_AUTHORIZED")
        print("EVALUATION_EXECUTED=false")
        print("RUNNER_STARTED=false")
        print("RUN_SLOT_CLAIMED=false")
        print("PANEL_DATA_ACCESSED=false")
        return 2

    output_dir = args.output_dir or evaluate_default
    if _slot_already_consumed(output_dir):
        print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
        print("REASON=EVALUATION_RUN_SLOT_ALREADY_CONSUMED")
        print("EVALUATION_RUN_COUNT=1")
        print("AUTO_RERUN_EXECUTED=false")
        return 2

    archive = args.archive_root
    if archive is None:
        archive = _default_archive_root()
        if archive is None:
            # Still fail closed before panel: missing archive is not an auth bypass.
            print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
            print("REASON=PEAK_TRADE_DATA_ARCHIVE_ROOT_UNSET")
            print("EVALUATION_EXECUTED=false")
            print("RUN_SLOT_CLAIMED=false")
            print("PANEL_DATA_ACCESSED=false")
            return 2

    try:
        summary = run_development_evaluation(
            output_dir=output_dir,
            archive_root=archive,
            authorize_hypothesis_id=auth,
            allow_panel_run=True,
            repo_root=REPO_ROOT,
        )
    except RuntimeError as exc:
        print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
        print(f"REASON={exc}")
        print("EVALUATION_EXECUTED=false")
        print("RUNNER_STARTED=false")
        print("RUN_SLOT_CLAIMED=false")
        print("PANEL_DATA_ACCESSED=false")
        return 2
    except Exception as exc:  # noqa: BLE001
        print("RESULT_CLASS=INCONCLUSIVE_INFRASTRUCTURE_FAILURE")
        print(f"REASON={type(exc).__name__}")
        print("AUTO_RERUN_EXECUTED=false")
        return 1

    print(f"RESULT_CLASS={summary.get('result_class')}")
    print(f"EVALUATION_RUN_COUNT={summary.get('evaluation_run_count')}")
    print(f"HOLDOUT_DATA_ACCESSED={summary.get('holdout_data_accessed')}")
    print("AUTO_RERUN_EXECUTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
