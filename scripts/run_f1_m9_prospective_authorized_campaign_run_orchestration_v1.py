#!/usr/bin/env python3
"""Dry-run entry for F1/M9 authorized campaign run orchestration (build slice — no REAL effects)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.authorized_run_orchestration_v1 import (
    F1M9AuthorizedCampaignRunOrchestrationRequestV1,
    run_f1_m9_prospective_authorized_campaign_run_orchestration_v1,
)
from src.governance.f1_m9_prospective_candidate_selection_campaign_execution_v1.runtime_authorization_v1 import (
    load_runtime_authorization_from_path_v1,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-authorization-path",
        type=Path,
        help="Optional runtime authorization JSON (verify/bind only; no consume in build slice).",
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    payload = None
    if args.runtime_authorization_path is not None:
        payload = load_runtime_authorization_from_path_v1(args.runtime_authorization_path)
    result = run_f1_m9_prospective_authorized_campaign_run_orchestration_v1(
        F1M9AuthorizedCampaignRunOrchestrationRequestV1(
            runtime_authorization=payload,
            repo_root=repo_root,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.orchestration_status else 1


if __name__ == "__main__":
    sys.exit(main())
