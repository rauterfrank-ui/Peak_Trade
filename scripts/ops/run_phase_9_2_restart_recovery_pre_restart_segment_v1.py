#!/usr/bin/env python3
"""Run a fixture PRE_RESTART segment (no network, no live authorization issuance)."""

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
    CANONICAL_INSTRUMENT_ID,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_EXIT_CODE,
    DURABLE_STATE_LINEAGE_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (  # noqa: E402
    build_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (  # noqa: E402
    sha256_canonical_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.segment_harness_v1 import (  # noqa: E402
    run_pre_restart_segment_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (  # noqa: E402
    build_fixture_checkpoint_v1,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--persistence-root",
        type=Path,
        required=True,
        help="Local persistence root for the PRE segment fixtures",
    )
    parser.add_argument("--open-position", action="store_true")
    args = parser.parse_args()

    repository_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()
    checkpoint = build_fixture_checkpoint_v1(
        confirmation_session_id=CONFIRMATION_SESSION_ID,
        observation_epoch=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
        open_position_present=bool(args.open_position),
        distinct_observation_count=MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
        evidence_cursor=sha256_canonical_v1({"cursor": "cli_pre"}),
        portfolio_seed="cli_portfolio",
        scope_seed="cli_scope",
        accounting_seed="cli_accounting",
        runtime_seed="cli_runtime",
        instrument_id=CANONICAL_INSTRUMENT_ID,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        applied_fill_ids=["fill_cli_001"] if args.open_position else [],
        applied_confirmation_ids=["conf_cli_001"],
    )
    runtime = "phase92_restart_pre_cli_runtime_v1"
    auth = "phase92_restart_pre_cli_auth_v1"
    contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_PRE,
        segment_id="segment_pre_restart_cli_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_PRE,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=checkpoint.runtime_state_digest,
        expected_portfolio_digest=checkpoint.portfolio_digest,
        expected_scope_digest=checkpoint.scope_digest,
        expected_accounting_digest=checkpoint.accounting_digest,
        expected_evidence_cursor=checkpoint.evidence_cursor,
        repo_root=_REPO_ROOT,
    )
    result = run_pre_restart_segment_v1(
        contract=contract,
        persistence_root=args.persistence_root,
        checkpoint=checkpoint,
        request_controlled_restart=True,
    )
    print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    if result.ok:
        return int(CONTROLLED_RESTART_EXIT_CODE)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
