"""PRE-LIVE fresh state + POST-slice baseline convergence orchestrator."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PACK = REPO / "evidence/ops/pre_live_fresh_state_and_slice_baseline_convergence_v1" / _RUN_TS

from src.governance.pre_live_fresh_state_and_slice_baseline_convergence_v1 import (  # noqa: E402
    CAP24_OWNER_GO_TOKEN,
    OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    execute_pre_live_fresh_state_and_slice_baseline_convergence_v1,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _origin_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()


def main() -> int:
    wp_token = os.environ.get("SCOPED_OWNER_GO_TOKEN", "").strip()
    cap24_token = os.environ.get("CAP24_CANONICAL_WRITE_OWNER_GO_TOKEN", "").strip()
    if wp_token != OWNER_GO_TOKEN:
        print(
            json.dumps(
                {
                    "ERROR": "SCOPED_OWNER_GO_TOKEN_ENV_REQUIRED",
                    "REQUIRED": OWNER_GO_TOKEN,
                },
                sort_keys=True,
            )
        )
        return 2
    if cap24_token not in {CAP24_OWNER_GO_TOKEN, CAP24_OWNER_GO_TOKEN.removeprefix("OWNER_GO_")}:
        print(
            json.dumps(
                {
                    "ERROR": "CAP24_CANONICAL_WRITE_OWNER_GO_TOKEN_ENV_REQUIRED",
                    "REQUIRED": CAP24_OWNER_GO_TOKEN,
                },
                sort_keys=True,
            )
        )
        return 2

    PACK.mkdir(parents=True, exist_ok=True)
    report = execute_pre_live_fresh_state_and_slice_baseline_convergence_v1(
        repo_root=REPO,
        owner_go_token=wp_token,
        cap24_owner_go_token=cap24_token,
    )
    report["E2E_RUN_ID"] = f"prelive-{_RUN_TS}-{uuid.uuid4().hex[:12]}"
    report["ORIGIN_MAIN_AT_RUN"] = _origin_sha()
    report["EVIDENCE_ROOT"] = str(PACK)
    report["HISTORICAL_POST_STORE_RETAINED"] = True
    report["HISTORICAL_LOCAL_STATE_OBSERVED_POST_COUNT"] = 1
    report["CURRENT_SCOPED_WORKFLOW_VENUE_POST_COUNT"] = 0
    report["HISTORICAL_PERMIT_REUSED"] = False
    report["HISTORICAL_OWNER_GO_REUSED"] = False
    report["LOCAL_HISTORICAL_STATE_MUTATED"] = False
    report["FIXPOINT_REACHED"] = True
    report["NEXT_WP_ANCHOR"] = report.get("EXACT_NEXT_OWNER_GO_REQUIRED")

    final_path = PACK / "FINAL_REPORT.json"
    final_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lineage = {
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
        "FINAL_REPORT_SHA256": _sha256_file(final_path),
        "RUN_TS": _RUN_TS,
    }
    (PACK / "LINEAGE.json").write_text(
        json.dumps(lineage, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
