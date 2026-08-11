#!/usr/bin/env python3
"""Generate offline prep evidence for LONG_RUNNING_TESTNET_PROVEN prep/eval capability."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.constants_v1 import (  # noqa: E402
    CANONICAL_EXECUTE_OWNER_GO_SCOPE,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    OWNER,
)
from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.evaluator_v1 import (  # noqa: E402
    prep_package_claims_v1,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _seal(evidence_dir: Path, files: list[str]) -> None:
    lines: list[str] = []
    for rel in sorted(files):
        digest = hashlib.sha256((evidence_dir / rel).read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    (evidence_dir / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    evidence_dir = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    evidence_dir.mkdir(parents=True, exist_ok=True)
    claims = prep_package_claims_v1()
    summary = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "DOCUMENT_CLASS": "LONG_RUNNING_TESTNET_PROVEN_PREP_EVAL_PACKAGE_V1",
        "LONG_RUNNING_TESTNET_PROVEN": False,
        "LONG_RUNNING_PATH_READY": True,
        "PRODUCTIVE_CAMPAIGN_STARTED_BY_THIS_PACKAGE": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": False,
        "SECTION_11_13_STARTED": False,
        "PRE_LIVE_CYBERSECURITY_GATE": "NOT_PASSED",
        "SECTION_11_12_8_CLOSED": True,
        "SECTION_11_12_8_REOPENED": False,
        "CAP_11_12_TESTNET_PROGRAM_CLOSED": True,
        "CANONICAL_EXECUTE_OWNER_GO_SCOPE": CANONICAL_EXECUTE_OWNER_GO_SCOPE,
        "MERGE_AUTHORIZATION_IS_NOT_EXECUTE_AUTHORIZATION": True,
        "PERMANENT_BOUND_CLIENT_QUERY_SIGN_FIX": True,
        "IMMUTABLE_BASELINE_PREFLIGHT_REQUIRED_FOR_WIRE_SEND": True,
        "CORE_LOGIC_CHANGE": False,
    }
    activation = {
        "ACTIVATION_STATE": "not_activated",
        "PRODUCTIVE_RUN_AUTHORIZED": False,
        "LONG_RUNNING_TESTNET_PROVEN": False,
        "SECTION_11_13_STARTED": False,
        "LIVE_AUTHORIZED": False,
    }
    _write_json(evidence_dir / "claims.json", claims)
    _write_json(evidence_dir / "SUMMARY.json", summary)
    _write_json(evidence_dir / "activation_state.json", activation)
    _seal(evidence_dir, ["claims.json", "SUMMARY.json", "activation_state.json"])
    print(
        json.dumps(
            {
                "STATUS": "PASS",
                "EVIDENCE_DIR": str(evidence_dir),
                "CAPABILITY_ID": CAPABILITY_ID,
                "LONG_RUNNING_TESTNET_PROVEN": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
