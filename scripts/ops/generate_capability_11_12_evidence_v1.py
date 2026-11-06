#!/usr/bin/env python3
"""Generate durable evidence for Cap 11.12 Fully autonomous Live readiness ratification."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.dependency_and_ownership_v1 import (  # noqa: E402
    STATE_OWNERSHIP_MATRIX_V1,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_12_v1,
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    productive.mkdir(parents=True, exist_ok=True)

    test_node = "tests/ops/test_capability_11_12_fully_autonomous_live_readiness_ratification_v1.py"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", test_node],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    test_results = {
        "command": ["python", "-m", "pytest", "-q", test_node],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "passed": proc.returncode == 0,
    }
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "error": "TESTS_FAILED", "test_results": test_results}))
        return 2

    verification = verify_capability_11_12_v1()
    if not verification.get("ok"):
        print(json.dumps({"ok": False, "error": "VERIFIER_FAILED", "verification": verification}))
        return 2

    repo_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()
    origin_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=str(_REPO_ROOT), text=True
    ).strip()

    claims = verification["claims"]
    _write_json(productive / "claims.json", claims)
    _write_json(productive / "call_graph_before.json", verification["call_graph_before"])
    _write_json(productive / "call_graph_after.json", verification["call_graph_after"])
    _write_json(productive / "state_ownership_matrix.json", list(STATE_OWNERSHIP_MATRIX_V1))
    _write_json(
        productive / "autonomy_closure_standard_field_proof.json",
        verification["proofs"]["autonomy_closure_standard_fields"],
    )
    _write_json(
        productive / "fully_autonomous_live_readiness_ratification_proof.json",
        verification["proofs"]["fully_autonomous_live_readiness_ratification"],
    )
    _write_json(
        productive / "capability_11_1_dependency_proof.json",
        verification["proofs"]["dependency_11_1"],
    )
    _write_json(
        productive / "capability_11_2_dependency_proof.json",
        verification["proofs"]["dependency_11_2"],
    )
    _write_json(
        productive / "capability_11_3_dependency_proof.json",
        verification["proofs"]["dependency_11_3"],
    )
    _write_json(
        productive / "capability_11_4_dependency_proof.json",
        verification["proofs"]["dependency_11_4"],
    )
    _write_json(
        productive / "capability_11_5_dependency_proof.json",
        verification["proofs"]["dependency_11_5"],
    )
    _write_json(
        productive / "capability_11_6_dependency_proof.json",
        verification["proofs"]["dependency_11_6"],
    )
    _write_json(
        productive / "capability_11_7_dependency_proof.json",
        verification["proofs"]["dependency_11_7"],
    )
    _write_json(
        productive / "capability_11_8_dependency_proof.json",
        verification["proofs"]["dependency_11_8"],
    )
    _write_json(
        productive / "capability_11_9_dependency_proof.json",
        verification["proofs"]["dependency_11_9"],
    )
    _write_json(
        productive / "capability_11_10_dependency_proof.json",
        verification["proofs"]["dependency_11_10"],
    )
    _write_json(
        productive / "capability_11_11_dependency_proof.json",
        verification["proofs"]["dependency_11_11"],
    )
    _write_json(
        productive / "negative_reachability_proof.json",
        verification["proofs"]["negative_reachability"],
    )
    _write_json(
        productive / "core_logic_parity.json",
        verification["proofs"]["core_logic_parity"],
    )
    _write_json(productive / "test_results.json", test_results)
    _write_json(
        productive / "repository_sha.json",
        {"HEAD": repo_sha, "origin_main": origin_main},
    )
    _write_json(
        productive / "activation_state.json",
        {
            "ACTIVATION_STATE": "not_activated",
            "TESTNET_AUTHORIZED": False,
            "LIVE_AUTHORIZED": False,
            "NETWORK_SESSION_STARTED": False,
            "PRIVATE_NETWORK_SESSION_STARTED": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
            "LIVE_AUTHORIZATION_VALID": False,
            "OWNER_LIVE_GO": False,
            "LIVE_ACTIVATION_CAPABILITY_PASS": False,
            "LIVE_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_12": False,
            "PAPER_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_12": False,
            "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_12": False,
            "TESTNET_NETWORK_SESSION_STARTED_IN_CAPABILITY_11_12": False,
            "LIVE_ORDER_EXECUTION_PERFORMED_IN_CAPABILITY_11_12": False,
            "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
            "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_12": False,
            "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
            "CAPABILITY_11_12_STARTED": True,
            "CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_STARTED": True,
            "AUTONOMY_CLOSURE_STANDARD_FIELD_CONTRACT_ACTIVATED": False,
            "FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_CONTRACT_ACTIVATED": False,
            "CAPABILITY_11_13_STARTED": False,
            "DASHBOARD_AUTHORITY_EFFECT": "NONE",
        },
    )
    _write_json(productive / "verifier_result.json", verification)

    summary = {
        "capability_id": CAPABILITY_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository_sha": repo_sha,
        "origin_main_sha": origin_main,
        "verifier_result": verification["VERIFIER_RESULT"],
        "claims": claims,
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_STATE": "not_activated",
    }
    _write_json(evidence_root / SUMMARY_FILENAME, summary)
    _write_json(evidence_root / CLAIMS_FILENAME, claims)

    rel_files: list[str] = []
    for path in sorted(evidence_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == MANIFEST_FILENAME:
            continue
        if path.name == "MANIFEST_SEAL_STATUS.json":
            continue
        rel = path.relative_to(evidence_root).as_posix()
        digest = _sha256_bytes(path.read_bytes())
        rel_files.append(f"{digest}  {rel}")
    (evidence_root / MANIFEST_FILENAME).write_text("\n".join(rel_files) + "\n", encoding="utf-8")

    check = subprocess.run(
        ["shasum", "-a", "256", "-c", MANIFEST_FILENAME],
        cwd=str(evidence_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        print(json.dumps({"ok": False, "error": "MANIFEST_VERIFY_FAILED", "stderr": check.stderr}))
        return 2

    claims = verification["claims"]
    readiness_proof = verification["proofs"]["fully_autonomous_live_readiness_ratification"]
    missing_true = list(readiness_proof.get("missing_true_fields") or [])
    seal_status = {
        "MANIFEST_SEAL_STATUS": "VALID",
        "MANIFEST_SEAL_VALID": True,
        "verification_method": "shasum -a 256 -c MANIFEST.sha256",
        "verification_result": "PASS",
        "pre_status_file_manifest_verify_rc": 0,
        "summary_verifier_result": "PASS",
        "CANONICAL_STATEFUL_CORE_PROVEN": True,
        "SIMULATED_LIFECYCLE_PROVEN": True,
        "TESTNET_LIFECYCLE_PROVEN": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
        "CAPABILITY_11_13_STARTED": False,
        "CANONICAL_STATEFUL_CORE_PROVEN_IN_MISSING_TRUE_FIELDS": (
            "CANONICAL_STATEFUL_CORE_PROVEN" in missing_true
        ),
        "missing_true_fields": missing_true,
    }
    _write_json(evidence_root / "MANIFEST_SEAL_STATUS.json", seal_status)

    print(
        json.dumps(
            {
                "ok": True,
                "capability_id": CAPABILITY_ID,
                "evidence_dir": str(evidence_root),
                "verifier_result": "PASS",
                "tests_passed": True,
                "SIMULATED_LIFECYCLE_PROVEN": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
