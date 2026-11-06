#!/usr/bin/env python3
"""Fail-closed verifier for Cap 11.5 durable evidence package."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.capability_11_5_testnet_restart_recovery_and_kill_switch_closure_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_5_v1,
)


def _fail(msg: str) -> int:
    print(json.dumps({"ok": False, "error": msg}, sort_keys=True))
    return 2


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    summary_path = evidence_root / SUMMARY_FILENAME
    manifest_path = evidence_root / MANIFEST_FILENAME
    if not summary_path.is_file():
        return _fail("SUMMARY_MISSING")
    if not manifest_path.is_file():
        return _fail("MANIFEST_MISSING")

    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", MANIFEST_FILENAME],
        cwd=str(evidence_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return _fail(f"MANIFEST_VERIFY_FAILED:{proc.stderr.strip()}")

    required = [
        "claims.json",
        "call_graph_before.json",
        "call_graph_after.json",
        "state_ownership_matrix.json",
        "unknown_submit_reconnect_recovery_proof.json",
        "restart_with_open_order_position_proof.json",
        "kill_switch_and_emergency_control_proof.json",
        "autonomous_recovery_degradation_proof.json",
        "capability_11_1_dependency_proof.json",
        "capability_11_2_dependency_proof.json",
        "capability_11_3_dependency_proof.json",
        "capability_11_4_dependency_proof.json",
        "negative_reachability_proof.json",
        "core_logic_parity.json",
        "test_results.json",
        "repository_sha.json",
        "activation_state.json",
        "verifier_result.json",
    ]
    for name in required:
        if not (productive / name).is_file():
            return _fail(f"MISSING_EVIDENCE_FILE:{name}")

    summary = _load(summary_path)
    claims = _load(productive / "claims.json")
    reach = _load(productive / "negative_reachability_proof.json")
    activation = _load(productive / "activation_state.json")
    tests = _load(productive / "test_results.json")
    dep_11_1 = _load(productive / "capability_11_1_dependency_proof.json")
    dep_11_2 = _load(productive / "capability_11_2_dependency_proof.json")
    dep_11_3 = _load(productive / "capability_11_3_dependency_proof.json")
    dep_11_4 = _load(productive / "capability_11_4_dependency_proof.json")
    live_verify = verify_capability_11_5_v1()

    checks = {
        "capability_id_match": summary.get("capability_id") == CAPABILITY_ID,
        "verifier_summary_pass": summary.get("verifier_result") == "PASS",
        "live_verifier_pass": live_verify.get("ok") is True,
        "tests_passed": tests.get("passed") is True,
        "core_logic_unchanged": claims.get("CORE_LOGIC_CHANGE") is False,
        "activation_not_activated": activation.get("ACTIVATION_STATE") == "not_activated",
        "testnet_unauthorized": claims.get("TESTNET_AUTHORIZED") is False,
        "live_unauthorized": claims.get("LIVE_AUTHORIZED") is False,
        "cap_11_1_dependency": dep_11_1.get("CAPABILITY_11_1_DEPENDENCY_SATISFIED") is True,
        "cap_11_2_dependency": dep_11_2.get("CAPABILITY_11_2_DEPENDENCY_SATISFIED") is True,
        "cap_11_3_dependency": dep_11_3.get("CAPABILITY_11_3_DEPENDENCY_SATISFIED") is True,
        "cap_11_4_dependency": dep_11_4.get("CAPABILITY_11_4_DEPENDENCY_SATISFIED") is True,
        "testnet_unreachable": reach.get("TESTNET_EXECUTION_REACHABLE") is False,
        "live_unreachable": reach.get("LIVE_EXECUTION_REACHABLE") is False,
        "no_real_adapter": reach.get("REAL_EXECUTION_ADAPTER_CONSTRUCTED") is False,
        "no_exchange_submit": reach.get("EXCHANGE_ORDER_SUBMIT_REACHABLE") is False,
        "no_credentials": reach.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
        "no_network_session": reach.get("NETWORK_SESSION_STARTED") is False,
        "no_testnet_submit": claims.get("TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_5")
        is False,
        "no_credential_load": claims.get("CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_5") is False,
        "no_auth_consumption": claims.get("AUTHORIZATION_CONSUMPTION_ALLOWED") is False,
        "cap_11_5_started": claims.get("CAPABILITY_11_5_RESTART_RECOVERY_KILL_SWITCH_STARTED")
        is True,
        "no_cap_11_6": claims.get("CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED")
        is False,
        "no_restart_proven_claim": claims.get("TESTNET_RESTART_PROVEN") is False,
        "no_unknown_recovery_proven_claim": claims.get("TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN")
        is False,
        "no_kill_switch_proven_claim": claims.get("TESTNET_KILL_SWITCH_PROVEN") is False,
        "no_autonomous_recovery_proven_claim": claims.get("TESTNET_AUTONOMOUS_RECOVERY_PROVEN")
        is False,
        "unknown_recovery_bound": claims.get("UNKNOWN_SUBMIT_RECONNECT_RECOVERY_CONTRACT_BOUND")
        is True,
        "restart_bound": claims.get("RESTART_WITH_OPEN_ORDER_POSITION_CONTRACT_BOUND") is True,
        "kill_switch_bound": claims.get("KILL_SWITCH_AND_EMERGENCY_CONTROL_CONTRACT_BOUND") is True,
        "recovery_bound": claims.get("AUTONOMOUS_RECOVERY_DEGRADATION_CONTRACT_BOUND") is True,
        "kill_switch_not_activated": claims.get("KILL_SWITCH_CONTRACT_ACTIVATED") is False,
    }
    if not all(checks.values()):
        return _fail(f"CLAIM_CHECKS_FAILED:{json.dumps(checks, sort_keys=True)}")

    print(
        json.dumps(
            {
                "ok": True,
                "capability_id": CAPABILITY_ID,
                "verifier_result": "PASS",
                "checks": checks,
                "evidence_dir": str(evidence_root),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
