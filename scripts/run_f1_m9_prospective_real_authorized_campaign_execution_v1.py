#!/usr/bin/env python3
"""REAL authorized F1/M9 prospective campaign execution entry (explicit; not default)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.execution_mode_v1 import (
    F1M9OrchestrationExecutionModeV1,
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
    repo_root = Path(__file__).resolve().parents[1]
    payload = load_runtime_authorization_from_path_v1(args.runtime_authorization_path)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=payload,
            repo_root=repo_root,
            execution_mode=F1M9OrchestrationExecutionModeV1.REAL_AUTHORIZED_CAMPAIGN_EXECUTION,
            expected_bound_origin_main_sha=args.expected_bound_origin_main_sha,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    ok_statuses = {
        "F1_M9_REAL_AUTHORIZED_CAMPAIGN_RUN_TERMINAL_VERDICT_PASS",
        "F1_M9_REAL_CAMPAIGN_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE",
    }
    return 0 if result.orchestration_status in ok_statuses else 1


if __name__ == "__main__":
    sys.exit(main())
