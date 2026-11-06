#!/usr/bin/env python3
"""Generate durable Cap 6.5 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.exit_policy_producer_binding_v1.authority_matrix_v1 import (  # noqa: E402
    inventory_exit_policy_authority_v1,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (  # noqa: E402
    AUTHORITY_MATRIX_FILENAME,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    FAILURE_INJECTION_FILENAME,
    GATE_FILENAME,
    MANIFEST_FILENAME,
    RESULT_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import sha256_hex  # noqa: E402
from src.ops.exit_policy_producer_binding_v1.persistence_v1 import write_manifest  # noqa: E402


def main() -> int:
    try:
        import subprocess

        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = "UNKNOWN"

    evidence_root = (
        _REPO_ROOT / "docs" / "evidence" / "capability_6_5_exit_policy_producer_binding_v1"
    )
    productive = evidence_root / "productive_binding"
    if productive.exists():
        shutil.rmtree(productive)
    productive.mkdir(parents=True, exist_ok=True)
    work = productive / "work"
    work.mkdir(parents=True, exist_ok=True)

    evidence = build_capability_evidence_v1(
        repository_sha=repository_sha,
        work_root=work,
    )
    payload = evidence.to_dict()
    authority = inventory_exit_policy_authority_v1()
    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "EXIT_POLICY_PRODUCERS_BOUND": bool(payload["claims"].get("EXIT_POLICY_PRODUCERS_BOUND")),
        "PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB": bool(
            payload["claims"].get("PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB")
        ),
        "EXIT_PATH_RUNTIME_REACHABLE": bool(payload["claims"].get("EXIT_PATH_RUNTIME_REACHABLE")),
        "EXIT_INDEPENDENCE_PROVEN": bool(payload["claims"].get("EXIT_INDEPENDENCE_PROVEN")),
        "EXIT_END_TO_END_EVIDENCE_PROVEN": False,
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
        "CONFIG_DIGEST": payload["config_digest"],
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "evidence_digest": payload["evidence_digest"],
        "claims": payload["claims"],
        "authority_inventory": authority,
    }
    gate = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "gate_flags": payload["claims"],
        "parity_results": payload["parity_results"],
        "restart_results": payload["restart_results"],
        "failure_injection_results": payload["failure_injection_results"],
    }

    (productive / EVIDENCE_FILENAME).write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (productive / RESULT_FILENAME).write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (productive / GATE_FILENAME).write_text(
        json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (productive / FAILURE_INJECTION_FILENAME).write_text(
        json.dumps(payload["failure_injection_results"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (productive / AUTHORITY_MATRIX_FILENAME).write_text(
        json.dumps(authority, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(
        productive,
        (
            EVIDENCE_FILENAME,
            RESULT_FILENAME,
            GATE_FILENAME,
            FAILURE_INJECTION_FILENAME,
            AUTHORITY_MATRIX_FILENAME,
        ),
    )
    shutil.rmtree(work, ignore_errors=True)

    summary = {
        "capability_id": CAPABILITY_ID,
        "ok": evidence.ok,
        "repository_sha": repository_sha,
        "evidence_digest": payload["evidence_digest"],
        "manifest_sha256": sha256_hex((productive / MANIFEST_FILENAME).read_bytes()),
        "EXIT_POLICY_PRODUCERS_BOUND": result["EXIT_POLICY_PRODUCERS_BOUND"],
        "PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB": result[
            "PLACEHOLDER_FALSE_SIGNAL_USED_AS_UNBOUND_STUB"
        ],
        "EXIT_PATH_RUNTIME_REACHABLE": result["EXIT_PATH_RUNTIME_REACHABLE"],
        "EXIT_INDEPENDENCE_PROVEN": result["EXIT_INDEPENDENCE_PROVEN"],
        "EXIT_END_TO_END_EVIDENCE_PROVEN": False,
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
    }
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    write_manifest(evidence_root, ("SUMMARY.json", f"productive_binding/{MANIFEST_FILENAME}"))

    print(json.dumps(summary, sort_keys=True))
    return 0 if evidence.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
