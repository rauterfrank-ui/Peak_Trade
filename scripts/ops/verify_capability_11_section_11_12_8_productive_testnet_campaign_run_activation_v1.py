#!/usr/bin/env python3
"""Verify Cap 11 §11.12.8 productive Testnet campaign run activation evidence."""

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

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1,
)


def main() -> int:
    verification = (
        verify_capability_11_section_11_12_8_productive_testnet_campaign_run_activation_v1()
    )
    claims = verification.get("claims") or {}
    gates = {
        "verifier_ok": verification.get("ok") is True,
        "implemented": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_IMPLEMENTED") is True,
        "run_preserved": claims.get("RUN_PREDECESSOR_PRESERVED") is True,
        "run_sha_bound": claims.get("RUN_PREDECESSOR_ORIGIN_MAIN_SHA")
        == RUN_PREDECESSOR_ORIGIN_MAIN_SHA,
        "surface_present": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT")
        is True,
        "surface_absent_false": claims.get(
            "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_ABSENT"
        )
        is False,
        "entrypoint_present": claims.get("PRODUCTIVE_ACTIVATION_ENTRYPOINT_PRESENT") is True,
        "run_unauthorized": claims.get("RUN_AUTHORIZED") is False,
        "activation_unauthorized": claims.get("ACTIVATION_AUTHORIZED") is False,
        "campaign_not_started": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_STARTED") is False,
        "campaign_not_completed": claims.get("PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED") is False,
        "network_effect_none": claims.get("NETWORK_EFFECT") == "NONE",
        "order_effect_none": claims.get("ORDER_EFFECT") == "NONE",
        "live_order_effect_none": claims.get("LIVE_ORDER_EFFECT") == "NONE",
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
        "future_activation_go_not_allowed": claims.get("FUTURE_ACTIVATION_GO_CONSUMPTION_ALLOWED")
        is False,
        "future_activation_go_not_consumed": claims.get("FUTURE_ACTIVATION_GO_CONSUMED") is False,
        "prove_only_not_may_start": claims.get("PROVE_ONLY_MAY_START") is False,
        "gate_may_start": claims.get("GATE_MAY_START") is True,
        "gate_not_started": claims.get("GATE_STARTED") is False,
        "activation_auth_blocked": claims.get("ACTIVATION_AUTH_BLOCKED") is True,
        "live_blocked": claims.get("LIVE_BLOCKED") is True,
        "credential_scope_blocked": claims.get("CREDENTIAL_SCOPE_BLOCKED") is True,
        "enabled_false_blocked": claims.get("ENABLED_FALSE_BLOCKED") is True,
        "armed_false_blocked": claims.get("ARMED_FALSE_BLOCKED") is True,
        "owner_auth_blocked": claims.get("OWNER_AUTH_BLOCKED") is True,
        "kill_switch_blocked": claims.get("KILL_SWITCH_BLOCKED") is True,
        "emergency_control_blocked": claims.get("EMERGENCY_CONTROL_BLOCKED") is True,
        "risk_scope_blocked": claims.get("RISK_SCOPE_BLOCKED") is True,
        "future_activation_go_blocked": claims.get("FUTURE_ACTIVATION_GO_BLOCKED") is True,
        "run_predecessor_sha_blocked": claims.get("RUN_PREDECESSOR_SHA_BLOCKED") is True,
        "confirm_invalid_blocked": claims.get("CONFIRM_INVALID_BLOCKED") is True,
        "activation_refused": claims.get("ACTIVATION_REFUSED") is True,
        "refuse_ok": claims.get("REFUSE_OK") is True,
        "next_consumer_activation_go": claims.get("NEXT_CONSUMER_CAPABILITY_ID")
        == "SEPARATE_OWNER_GO_REQUIRED_FOR_PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION",
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
                "LIVE_ORDER_EFFECT": claims.get("LIVE_ORDER_EFFECT"),
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": claims.get(
                    "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED"
                ),
                "RUN_AUTHORIZED": claims.get("RUN_AUTHORIZED"),
                "ACTIVATION_AUTHORIZED": claims.get("ACTIVATION_AUTHORIZED"),
                "ACTIVATION_SURFACE_PRESENT": claims.get(
                    "PRODUCTIVE_TESTNET_CAMPAIGN_RUN_ACTIVATION_SURFACE_PRESENT"
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
