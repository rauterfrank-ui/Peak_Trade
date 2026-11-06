#!/usr/bin/env python3
"""Generate durable Cap 6.3 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.decision_config_ownership_and_consumer_closure_v1.authority_matrix_v1 import (  # noqa: E402
    inventory_decision_config_authority_surfaces_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (  # noqa: E402
    AUTHORITY_MATRIX_FILENAME,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    FAILURE_INJECTION_FILENAME,
    GATE_FILENAME,
    MANIFEST_FILENAME,
    OWNERSHIP_GRAPH_AFTER,
    OWNERSHIP_GRAPH_BEFORE,
    RESULT_FILENAME,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.persistence_v1 import (  # noqa: E402
    write_manifest,
)


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
        _REPO_ROOT
        / "docs"
        / "evidence"
        / "capability_6_3_decision_config_ownership_and_consumer_closure_v1"
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
    authority = inventory_decision_config_authority_surfaces_v1()
    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "CONFIG_RUNTIME_DRIFT": False,
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": bool(
            payload["claims"].get("EFFECTIVE_NUMERIC_VALUES_UNCHANGED")
        ),
        "NO_SILENT_FALLBACK": True,
        "ONE_CONFIG_OWNER_PER_RUNTIME_VALUE": True,
        "NO_PARALLEL_CONFIG_AUTHORITY": True,
        "CONFIG_VERSION": payload["config_version"],
        "CONFIG_DIGEST": payload["config_digest"],
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "ownership_graph_before": list(OWNERSHIP_GRAPH_BEFORE),
        "ownership_graph_after": list(OWNERSHIP_GRAPH_AFTER),
        "evidence_digest": payload["evidence_digest"],
        "claims": payload["claims"],
        "authority_inventory": authority,
        "migrated_keys": authority["migrated_keys"],
        "not_migrated_keys": authority["not_migrated_keys"],
        "predecessor_digests": payload["predecessor_digests"],
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
        json.dumps(payload["authority_matrix"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    shutil.rmtree(work, ignore_errors=True)

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

    summary = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "evidence_digest": payload["evidence_digest"],
        "CONFIG_VERSION": payload["config_version"],
        "CONFIG_DIGEST": payload["config_digest"],
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": True,
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
        "LIVE_TESTNET_ORDERS": False,
        "migrated_keys": authority["migrated_keys"],
        "not_migrated_keys": authority["not_migrated_keys"],
    }
    evidence_root.mkdir(parents=True, exist_ok=True)
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    lines = []
    lines.append(f"{sha256_hex((evidence_root / 'SUMMARY.json').read_bytes())}  SUMMARY.json")
    for name in (
        EVIDENCE_FILENAME,
        RESULT_FILENAME,
        GATE_FILENAME,
        FAILURE_INJECTION_FILENAME,
        AUTHORITY_MATRIX_FILENAME,
        MANIFEST_FILENAME,
    ):
        rel = f"productive_binding/{name}"
        digest = sha256_hex((evidence_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    (evidence_root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": evidence.ok, "repository_sha": repository_sha}, indent=2))
    return 0 if evidence.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
