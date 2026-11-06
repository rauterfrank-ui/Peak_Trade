#!/usr/bin/env python3
"""Run a fixture POST_RESTART segment against an existing PRE terminal (no network)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (  # noqa: E402
    authorization_digest_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (  # noqa: E402
    PRE_TERMINAL_MANIFEST_FILENAME,
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_POST,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (  # noqa: E402
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (  # noqa: E402
    read_json_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (  # noqa: E402
    run_post_restart_segment_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persistence-root", type=Path, required=True)
    parser.add_argument("--candidate-observation-id", default=None)
    parser.add_argument("--candidate-fill-id", default=None)
    args = parser.parse_args()

    repository_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()
    pre = read_json_v1(args.persistence_root / PRE_TERMINAL_MANIFEST_FILENAME)
    runtime = "phase92_restart_post_cli_runtime_v1"
    auth = "phase92_restart_post_cli_auth_v1"
    contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_POST,
        segment_id="segment_post_restart_cli_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_POST,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=str(pre["runtime_state_digest"]),
        expected_portfolio_digest=str(pre["portfolio_digest"]),
        expected_scope_digest=str(pre["scope_digest"]),
        expected_accounting_digest=str(pre["accounting_digest"]),
        expected_evidence_cursor=str(pre["evidence_cursor"]),
        predecessor_segment_id=str(pre["segment_id"]),
        predecessor_terminal_manifest_digest=str(pre["terminal_manifest_digest"]),
        repo_root=_REPO_ROOT,
    )
    result = run_post_restart_segment_v1(
        contract=contract,
        persistence_root=args.persistence_root,
        candidate_observation_id=args.candidate_observation_id,
        candidate_fill_id=args.candidate_fill_id,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
