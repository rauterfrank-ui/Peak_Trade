#!/usr/bin/env python3
"""REAL authorized F1/M9 prospective campaign execution entry (explicit; not default)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[1]
_BOOTSTRAP_PATH = _REPO_ROOT / "src/ops/peak_trade_python_script_entry_bootstrap_v1.py"
_spec = importlib.util.spec_from_file_location(
    "peak_trade_python_script_entry_bootstrap_v1",
    _BOOTSTRAP_PATH,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError("PEAK_TRADE_SCRIPT_ENTRY_BOOTSTRAP_MISSING")
_bootstrap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bootstrap)
_bootstrap.ensure_peak_trade_script_entry_bootstrap_v1(script_path=_SCRIPT_PATH)

import argparse
import json
import sys

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_mode_v1 import (
    F1M9OrchestrationExecutionModeV1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.production_real_public_md_session_adapter_v1 import (
    build_production_real_public_md_session_adapter_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    load_runtime_authorization_from_path_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-authorization-path",
        type=Path,
        required=True,
        help="Fresh issued runtime authorization JSON (required for REAL mode).",
    )
    parser.add_argument(
        "--expected-bound-origin-main-sha",
        type=str,
        default=None,
        help="Optional bound origin/main SHA enforced against issuance record.",
    )
    args = parser.parse_args(argv)
    payload = load_runtime_authorization_from_path_v1(args.runtime_authorization_path)
    adapter = build_production_real_public_md_session_adapter_v1()
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=payload,
            repo_root=_REPO_ROOT,
            execution_mode=F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION,
            real_public_md_adapter=adapter,
            expected_bound_origin_main_sha=args.expected_bound_origin_main_sha,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    ok_statuses = {
        "F1_M9_REAL_AUTHORIZED_CAMPAIGN_RUN_TERMINAL_VERDICT_PASS",
    }
    return 0 if result.orchestration_status in ok_statuses else 1


if __name__ == "__main__":
    sys.exit(main())
