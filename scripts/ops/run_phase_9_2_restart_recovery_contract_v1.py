#!/usr/bin/env python3
"""Build or validate a Phase 9.2 restart-session contract (no network)."""

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
    RESTART_CAMPAIGN_ID,
    SEGMENT_ROLE_PRE,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.contract_v1 import (  # noqa: E402
    RestartContractError,
    build_restart_session_contract_v1,
    validate_restart_session_contract_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (  # noqa: E402
    sha256_canonical_v1,
)


def _repo_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", type=Path, default=None, help="Validate contract JSON path")
    parser.add_argument("--write", type=Path, default=None, help="Write built PRE contract JSON")
    args = parser.parse_args()

    if args.validate is not None:
        payload = json.loads(Path(args.validate).read_text(encoding="utf-8"))
        try:
            contract = validate_restart_session_contract_v1(payload)
        except RestartContractError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True, indent=2))
            return 1
        print(json.dumps({"ok": True, "contract": contract.to_dict()}, sort_keys=True, indent=2))
        return 0

    repository_sha = _repo_sha()
    runtime = "phase92_restart_contract_preview_runtime_v1"
    auth = "phase92_restart_contract_preview_auth_v1"
    placeholders = {
        "runtime": sha256_canonical_v1({"preview": "runtime"}),
        "portfolio": sha256_canonical_v1({"preview": "portfolio"}),
        "scope": sha256_canonical_v1({"preview": "scope"}),
        "accounting": sha256_canonical_v1({"preview": "accounting"}),
        "cursor": sha256_canonical_v1({"preview": "cursor"}),
    }
    contract = build_restart_session_contract_v1(
        repository_sha=repository_sha,
        segment_role=SEGMENT_ROLE_PRE,
        segment_id="segment_pre_restart_preview_v1",
        runtime_session_id=runtime,
        authorization_id=auth,
        authorization_digest=authorization_digest_v1(
            authorization_id=auth,
            segment_role=SEGMENT_ROLE_PRE,
            restart_campaign_id=RESTART_CAMPAIGN_ID,
            runtime_session_id=runtime,
        ),
        expected_runtime_state_digest=placeholders["runtime"],
        expected_portfolio_digest=placeholders["portfolio"],
        expected_scope_digest=placeholders["scope"],
        expected_accounting_digest=placeholders["accounting"],
        expected_evidence_cursor=placeholders["cursor"],
        repo_root=_REPO_ROOT,
    )
    payload = contract.to_dict()
    if args.write is not None:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(
            json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
    print(
        json.dumps(
            {"ok": True, "contract": payload, "network_started": False}, sort_keys=True, indent=2
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
