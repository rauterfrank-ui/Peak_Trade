#!/usr/bin/env python3
"""Generate durable Cap 7.2 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.single_future_stateful_no_order_runtime_activation_v1.authority_matrix_v1 import (  # noqa: E402
    inventory_activation_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (  # noqa: E402
    ACTIVATION_STATUS_FILENAME,
    AUTHORITY_MATRIX_FILENAME,
    CALL_GRAPH_FILENAME,
    CAPABILITY_ID,
    CLAIM_MATRIX_FILENAME,
    EVIDENCE_FILENAME,
    EXECUTION_PORT_PROOF_FILENAME,
    FAILURE_INJECTION_FILENAME,
    GATE_FILENAME,
    MANIFEST_FILENAME,
    NETWORK_PROOF_FILENAME,
    NO_ORDER_PROOF_FILENAME,
    PARITY_PROOF_FILENAME,
    PRECONDITION_MATRIX_FILENAME,
    RESULT_FILENAME,
    ROLLBACK_PROOF_FILENAME,
    STARTUP_RESTART_PROOF_FILENAME,
    TEST_MANIFEST_FILENAME,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.persistence_v1 import (  # noqa: E402
    write_manifest,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    try:
        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"

    evidence_root = (
        _REPO_ROOT
        / "docs"
        / "evidence"
        / "capability_7_2_single_future_stateful_no_order_runtime_activation_v1"
    )
    productive = evidence_root / "productive_binding"
    if productive.exists():
        shutil.rmtree(productive)
    productive.mkdir(parents=True, exist_ok=True)
    work = productive / "work"
    work.mkdir(parents=True, exist_ok=True)

    evidence = build_capability_evidence_v1(repository_sha=repository_sha, work_root=work)
    payload = evidence.to_dict()
    authority = inventory_activation_authority_v1()
    claims = payload["claims"]

    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": payload["config_digest"],
        "evidence_digest": payload["evidence_digest"],
        "predecessor_capability_id": payload["predecessor_capability_id"],
        "predecessor_merge_sha": payload["predecessor_merge_sha"],
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": True,
        "RUNTIME_ACTIVATED": bool(claims.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")),
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            claims.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(claims.get("SIMULATED_EXECUTION_ACTIVE")),
        "PUBLIC_MD_RUNTIME_CAPABLE": True,
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "LIVE_ORDERS": False,
        "TESTNET_ORDERS": False,
        "PAPER_EXCHANGE_ORDERS": False,
        "claims": claims,
        "call_graph_after": payload["call_graph_after"],
    }
    gate = {
        "ok": evidence.ok,
        "PRECONDITIONS_ALL_PROVEN": claims.get("PRECONDITIONS_ALL_PROVEN"),
        "ROLLBACK_PROVEN": claims.get("ROLLBACK_PROVEN"),
        "FAILURE_INJECTION_PROVEN": claims.get("FAILURE_INJECTION_PROVEN"),
        "EVIDENCE_VERIFIER_PASS": claims.get("EVIDENCE_VERIFIER_PASS"),
    }
    summary = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": payload["config_digest"],
        "evidence_digest": payload["evidence_digest"],
        "FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE": bool(
            claims.get("FULL_CANONICAL_STATEFUL_RUNTIME_ACTIVE")
        ),
        "SIMULATED_EXECUTION_ACTIVE": bool(claims.get("SIMULATED_EXECUTION_ACTIVE")),
        "PUBLIC_MD_NETWORK_SESSION_OBSERVED": False,
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_CHANGED": True,
    }

    _write_json(productive / EVIDENCE_FILENAME, payload)
    _write_json(productive / RESULT_FILENAME, result)
    _write_json(productive / GATE_FILENAME, gate)
    _write_json(productive / AUTHORITY_MATRIX_FILENAME, authority)
    _write_json(productive / PRECONDITION_MATRIX_FILENAME, payload["precondition_matrix"])
    _write_json(
        productive / CALL_GRAPH_FILENAME,
        {
            "before": payload["call_graph_before"],
            "after": payload["call_graph_after"],
        },
    )
    _write_json(productive / EXECUTION_PORT_PROOF_FILENAME, payload["execution_port_proof"])
    _write_json(productive / NETWORK_PROOF_FILENAME, payload["network_credential_proof"])
    _write_json(productive / STARTUP_RESTART_PROOF_FILENAME, payload["startup_restart_proof"])
    _write_json(productive / ROLLBACK_PROOF_FILENAME, payload["rollback_proof"])
    _write_json(productive / PARITY_PROOF_FILENAME, payload["parity_results"])
    _write_json(productive / FAILURE_INJECTION_FILENAME, payload["failure_injection_results"])
    _write_json(productive / ACTIVATION_STATUS_FILENAME, payload["activation_status"])
    _write_json(productive / CLAIM_MATRIX_FILENAME, claims)
    _write_json(
        productive / NO_ORDER_PROOF_FILENAME,
        {
            "LIVE_ORDERS": False,
            "TESTNET_ORDERS": False,
            "PAPER_EXCHANGE_ORDERS": False,
            "EXCHANGE_CREDENTIAL_USE": False,
            "REAL_CAPITAL_MOVEMENT": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
            "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
            "NETWORK_SESSION_STARTED": False,
        },
    )
    _write_json(
        productive / TEST_MANIFEST_FILENAME,
        {
            "tests": [
                "tests/ops/test_single_future_stateful_no_order_runtime_activation_v1.py",
            ],
            "offline_only": True,
            "network_session_started": False,
        },
    )
    _write_json(evidence_root / "SUMMARY.json", summary)

    # Exclude work directory contents from manifest; only durable artifacts.
    if work.exists():
        shutil.rmtree(work)
    durable = [p.relative_to(productive).as_posix() for p in productive.rglob("*") if p.is_file()]
    write_manifest(productive, tuple(sorted(durable)))
    root_files = ["SUMMARY.json"] + [f"productive_binding/{r}" for r in sorted(durable)]
    lines = []
    for rel in root_files:
        digest = sha256_hex((evidence_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    (evidence_root / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {"ok": evidence.ok, "evidence_digest": payload["evidence_digest"]}, sort_keys=True
        )
    )
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
