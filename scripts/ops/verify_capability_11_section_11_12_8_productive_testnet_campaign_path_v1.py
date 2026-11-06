#!/usr/bin/env python3
"""Verify Cap 11 §11.12.8 productive Testnet campaign path evidence."""

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

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_path_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_section_11_12_8_productive_testnet_campaign_path_v1,
)


def main() -> int:
    verification = verify_capability_11_section_11_12_8_productive_testnet_campaign_path_v1()
    claims = verification.get("claims") or {}
    gates = {
        "verifier_ok": verification.get("ok") is True,
        "capability_implemented": claims.get("PRODUCTIVE_TESTNET_CAPABILITY_IMPLEMENTED") is True,
        "fixture_preserved": claims.get("FIXTURE_PROOF_PRESERVED") is True,
        "path_present": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_PATH_PRESENT") is True,
        "path_absent_false": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_PATH_ABSENT") is False,
        "execution_unauthorized": claims.get("PRODUCTIVE_TESTNET_EXECUTION_AUTHORIZED") is False,
        "campaign_not_started": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_STARTED") is False,
        "campaign_not_completed": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED") is False,
        "network_effect_none": claims.get("NETWORK_EFFECT") == "NONE",
        "order_effect_none": claims.get("ORDER_EFFECT") == "NONE",
        "order_send_disabled": claims.get("ORDER_SEND_DISABLED") is True,
        "orders_unauthorized": claims.get("ORDERS_AUTHORIZED") is False,
        "network_writes_unauthorized": claims.get("NETWORK_WRITES_AUTHORIZED") is False,
        "network_write_not_performed": claims.get("NETWORK_WRITE_PERFORMED") is False,
        "network_session_not_started": claims.get("NETWORK_SESSION_STARTED") is False,
        "order_submit_unreachable": claims.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
        "testnet_order_submit_false": claims.get("TESTNET_ORDER_SUBMIT_PERFORMED") is False,
        "live_unauthorized": claims.get("LIVE_AUTHORIZED") is False,
        "testnet_unauthorized_default": claims.get("TESTNET_AUTHORIZED") is False,
        "cap_11_13_not_started": claims.get("CAPABILITY_11_13_STARTED") is False,
        "section_11_13_not_started": claims.get("SECTION_11_13_STARTED") is False,
        "authorization_not_consumed": claims.get("AUTHORIZATION_CONSUMED") is False,
        "start_gate_may_start": claims.get("START_GATE_MAY_START") is True,
        "start_gate_not_started": claims.get("START_GATE_STARTED") is False,
        "path_only_not_may_start": claims.get("PATH_ONLY_MAY_START") is False,
        "live_blocked": claims.get("LIVE_BLOCKED") is True,
        "credential_scope_blocked": claims.get("CREDENTIAL_SCOPE_BLOCKED") is True,
        "enabled_false_blocked": claims.get("ENABLED_FALSE_BLOCKED") is True,
        "armed_false_blocked": claims.get("ARMED_FALSE_BLOCKED") is True,
        "owner_auth_blocked": claims.get("OWNER_AUTH_BLOCKED") is True,
        "confirm_invalid_blocked": claims.get("CONFIRM_INVALID_BLOCKED") is True,
        "confirm_mismatch_blocked": claims.get("CONFIRM_MISMATCH_BLOCKED") is True,
        "confirm_argv_blocked": claims.get("CONFIRM_ARGV_BLOCKED") is True,
        "scope_escalation_blocked": claims.get("SCOPE_ESCALATION_BLOCKED") is True,
        "campaign_start_refused": claims.get("CAMPAIGN_START_REFUSED") is True,
        "execution_refused": claims.get("EXECUTION_REFUSED") is True,
        "cap_11_13_refused": claims.get("CAP_11_13_REFUSED") is True,
        "order_submit_refused": claims.get("ORDER_SUBMIT_REFUSED") is True,
        "network_session_refused": claims.get("NETWORK_SESSION_REFUSED") is True,
        "live_path_refused": claims.get("LIVE_PATH_REFUSED") is True,
        "instrument_scope_blocked": claims.get("INSTRUMENT_SCOPE_BLOCKED") is True,
        "order_type_blocked": claims.get("ORDER_TYPE_BLOCKED") is True,
        "position_limit_blocked": claims.get("POSITION_LIMIT_BLOCKED") is True,
        "kill_switch_blocked": claims.get("KILL_SWITCH_BLOCKED") is True,
        "emergency_control_blocked": claims.get("EMERGENCY_CONTROL_BLOCKED") is True,
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
                "ORDER_EFFECT": claims.get("ORDER_EFFECT"),
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": claims.get(
                    "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"
                ),
                "SECTION_11_13_STARTED": claims.get("SECTION_11_13_STARTED"),
                "claims": claims,
            },
            sort_keys=True,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
