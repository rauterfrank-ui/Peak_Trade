#!/usr/bin/env python3
"""Verify Cap 11 §11.12.2 order serialization dry-run evidence."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
)
from src.ops.capability_11_section_11_12_2_order_serialization_dry_run_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_section_11_12_2_order_serialization_dry_run_v1,
)


def main() -> int:
    verification = verify_capability_11_section_11_12_2_order_serialization_dry_run_v1()
    claims = verification.get("claims") or {}
    gates = {
        "verifier_ok": verification.get("ok") is True,
        "order_send_disabled": claims.get("ORDER_SEND_DISABLED") is True,
        "orders_unauthorized": claims.get("ORDERS_AUTHORIZED") is False,
        "network_writes_unauthorized": claims.get("NETWORK_WRITES_AUTHORIZED") is False,
        "network_write_not_performed": claims.get("NETWORK_WRITE_PERFORMED") is False,
        "network_effect_none": claims.get("ORDER_SERIALIZATION_NETWORK_EFFECT") == "NONE",
        "dry_run_performed": claims.get("ORDER_SERIALIZATION_DRY_RUN_PERFORMED") is True,
        "cap_11_4_contract_reused": claims.get("CAP_11_4_ORDER_SERIALIZATION_CONTRACT_REUSED")
        is True,
        "predecessor_bound": claims.get("SECTION_11_12_1_PREDECESSOR_BOUND") is True,
        "submitted_false": claims.get("SUBMITTED") is False,
        "order_submit_unreachable": claims.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
        "testnet_order_submit_false": claims.get("TESTNET_ORDER_SUBMIT_PERFORMED") is False,
        "cap_11_4_not_started": claims.get("CAPABILITY_11_4_STARTED") is False,
        "cap_11_4_adapter_inactive": claims.get(
            "CAPABILITY_11_4_TESTNET_EXECUTION_ADAPTER_ACTIVATED"
        )
        is False,
        "section_11_12_3_not_started": claims.get("SECTION_11_12_3_STARTED") is False,
        "cap_11_13_not_started": claims.get("CAPABILITY_11_13_STARTED") is False,
    }
    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    manifest = evidence_root / MANIFEST_FILENAME
    manifest_rc = 1
    if manifest.is_file():
        check = subprocess.run(
            ["shasum", "-a", "256", "-c", MANIFEST_FILENAME],
            cwd=str(evidence_root),
            capture_output=True,
            text=True,
            check=False,
        )
        manifest_rc = check.returncode
        gates["manifest_ok"] = check.returncode == 0
    else:
        gates["manifest_ok"] = False

    ok = all(gates.values())
    print(
        json.dumps(
            {
                "ok": ok,
                "capability_id": CAPABILITY_ID,
                "VERIFIER_RESULT": "PASS" if ok else "FAIL",
                "gates": gates,
                "MANIFEST_VERIFY_RC": manifest_rc,
                "claims": claims,
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
