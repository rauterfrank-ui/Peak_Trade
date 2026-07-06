#!/usr/bin/env python3
"""Dry-run runner for cross-sectional funding-rate rank-delta v0 evaluation infrastructure.

Validates infrastructure readiness and entrypoint wiring only. Does not execute
economic evaluation. Operator GO for infrastructure:
GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_V0_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_COMPLETION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_ohlcv_panel_series_for_backtest,
    run_full_evaluation_entrypoint_dry_run_v1,
)
from src.research.cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_infrastructure_readiness_v0 import (  # noqa: E402
    evaluate_rank_delta_offline_evaluation_infrastructure_readiness_v0,
    readiness_result_to_dict,
)
from src.research.cross_sectional_funding_rate_rank_delta_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_rank_delta_offline_economic_evaluation_scope_ratification_v0,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--staging-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, default=None)
    args = parser.parse_args()

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    ratification = materialize_rank_delta_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    readiness = evaluate_rank_delta_offline_evaluation_infrastructure_readiness_v0(
        repo_root=_REPO_ROOT,
        ratification=ratification,
    )
    if not readiness.evaluation_infrastructure_ready:
        _die(f"ERR: infrastructure_not_ready:{readiness.blockers}")

    try:
        panel_series = load_ohlcv_panel_series_for_backtest(args.staging_root)
    except FileNotFoundError:
        _die("ERR: staging_root_missing_ohlcv_panel")

    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=_REPO_ROOT,
        ratification=ratification,
        staging_root=args.staging_root,
        panel_series=panel_series,
        go_token=CONFIRM_GO,
    )
    payload = {
        "readiness": readiness_result_to_dict(readiness),
        "entrypoint": entrypoint_result_to_dict(result),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "economic_evaluation_executed": False,
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output_json:
        args.output_json.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
