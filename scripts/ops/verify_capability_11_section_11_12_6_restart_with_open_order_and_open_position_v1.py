#!/usr/bin/env python3
"""Verify Cap 11 §11.12.6 restart with open order and open position evidence."""

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

from src.ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.constants_v1 import (  # noqa: E402
    ALLOWED_SECTION_11_12_6_PATHS,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
)
from src.ops.capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1,
)


def main() -> int:
    verification = (
        verify_capability_11_section_11_12_6_restart_with_open_order_and_open_position_v1()
    )
    claims = verification.get("claims") or {}
    gates = {
        "verifier_ok": verification.get("ok") is True,
        "order_send_disabled": claims.get("ORDER_SEND_DISABLED") is True,
        "orders_unauthorized": claims.get("ORDERS_AUTHORIZED") is False,
        "network_writes_unauthorized": claims.get("NETWORK_WRITES_AUTHORIZED") is False,
        "network_write_not_performed": claims.get("NETWORK_WRITE_PERFORMED") is False,
        "network_effect_none": claims.get("LIFECYCLE_NETWORK_EFFECT") == "NONE",
        "restart_performed": claims.get("RESTART_WITH_OPEN_ORDER_AND_OPEN_POSITION_PERFORMED")
        is True,
        "cap_11_5_contract_reused": claims.get(
            "CAP_11_5_RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_REUSED"
        )
        is True,
        "predecessor_bound": claims.get("SECTION_11_12_5_PREDECESSOR_BOUND") is True,
        "exchange_submit_false": claims.get("EXCHANGE_SUBMIT_PERFORMED") is False,
        "order_submit_unreachable": claims.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
        "testnet_order_submit_false": claims.get("TESTNET_ORDER_SUBMIT_PERFORMED") is False,
        "cap_11_5_not_started": claims.get("CAPABILITY_11_5_STARTED") is False,
        "cap_11_5_adapter_inactive": claims.get(
            "CAPABILITY_11_5_TESTNET_RESTART_RECOVERY_ACTIVATED"
        )
        is False,
        "section_11_12_7_not_started": claims.get("SECTION_11_12_7_STARTED") is False,
        "cap_11_13_not_started": claims.get("CAPABILITY_11_13_STARTED") is False,
        "testnet_order_lifecycle_not_proven": claims.get("TESTNET_ORDER_LIFECYCLE_PROVEN") is False,
        "testnet_unknown_submit_not_proven": claims.get("TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN")
        is False,
        "testnet_restart_not_proven": claims.get("TESTNET_RESTART_PROVEN") is False,
        "silent_reinitialization_blocked": claims.get("SILENT_REINITIALIZATION_BLOCKED") is True,
        "restart_network_blocked": claims.get("RESTART_NETWORK_SESSION_ACTIVATION_BLOCKED") is True,
        "paths_completed_match": claims.get("PATHS_COMPLETED")
        == list(ALLOWED_SECTION_11_12_6_PATHS),
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
                "NETWORK_EFFECT": claims.get("NETWORK_EFFECT"),
                "ORDER_EFFECT": "NONE",
                "claims": claims,
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
