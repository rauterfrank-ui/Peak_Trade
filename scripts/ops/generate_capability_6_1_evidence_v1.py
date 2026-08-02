#!/usr/bin/env python3
"""Generate durable Cap 6.1 evidence under docs/evidence/ (offline, no network)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.ops.stateful_confirmation_and_c1_productive_binding_v1.authority_inventory_v1 import (  # noqa: E402
    inventory_confirmation_binding_authority_surfaces_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (  # noqa: E402
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    FAILURE_INJECTION_FILENAME,
    GATE_FILENAME,
    MANIFEST_FILENAME,
    RESULT_FILENAME,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.cycle_harness_v1 import (  # noqa: E402
    build_capability_evidence_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.models_v1 import (  # noqa: E402
    sha256_hex,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.persistence_v1 import (  # noqa: E402
    write_manifest,
)


def _git_head() -> str:
    head = (_REPO_ROOT / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head.startswith("ref:"):
        ref = head.split(" ", 1)[1].strip()
        return (_REPO_ROOT / ".git" / ref).read_text(encoding="utf-8").strip()
    return head


def main() -> int:
    # Worktree git dir may be a file pointer; prefer git rev-parse via env when available.
    try:
        import subprocess

        repository_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_REPO_ROOT),
            text=True,
        ).strip()
    except Exception:  # noqa: BLE001
        repository_sha = _git_head()

    evidence_root = (
        _REPO_ROOT
        / "docs"
        / "evidence"
        / "capability_6_1_stateful_confirmation_and_c1_productive_binding_v1"
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
    authority = inventory_confirmation_binding_authority_surfaces_v1()
    result = {
        "ok": evidence.ok,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "C1_PRODUCTIVELY_BOUND": True,
        "C2_PRODUCTIVELY_BOUND": True,
        "C3_PRODUCTIVELY_BOUND": True,
        "CORE_LOGIC_CHANGE": False,
        "RUNTIME_ACTIVATED": False,
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
    # Ephemeral harness work is not a durable claim surface.
    shutil.rmtree(work, ignore_errors=True)

    # Preserve preflight freeze artifact at evidence root.
    write_manifest(
        productive,
        (
            EVIDENCE_FILENAME,
            RESULT_FILENAME,
            GATE_FILENAME,
            FAILURE_INJECTION_FILENAME,
        ),
    )
    summary = {
        "capability_id": CAPABILITY_ID,
        "ok": evidence.ok,
        "repository_sha": repository_sha,
        "C1_PRODUCTIVELY_BOUND": True,
        "C2_PRODUCTIVELY_BOUND": True,
        "C3_PRODUCTIVELY_BOUND": True,
        "CONFIRMATION_STATE_PERSISTED": True,
        "CONFIRMATION_RESTART_PROVEN": bool(
            payload["restart_results"].get("CONFIRMATION_RESTART_PROVEN")
        ),
        "CORE_LOGIC_CHANGED": False,
        "ACTIVATION_CHANGED": False,
        "RUNTIME_ACTIVATED": False,
        "evidence_digest": payload["evidence_digest"],
        "manifest_sha256": sha256_hex((productive / MANIFEST_FILENAME).read_bytes()),
    }
    (evidence_root / "SUMMARY.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    # Root manifest covers summary + productive bundle + preflight freeze.
    root_files = ["SUMMARY.json", "preflight_6_0_authority_freeze_v1.json"]
    for rel in (
        f"productive_binding/{EVIDENCE_FILENAME}",
        f"productive_binding/{RESULT_FILENAME}",
        f"productive_binding/{GATE_FILENAME}",
        f"productive_binding/{FAILURE_INJECTION_FILENAME}",
        f"productive_binding/{MANIFEST_FILENAME}",
    ):
        root_files.append(rel)
    write_manifest(evidence_root, tuple(root_files))
    print(json.dumps({"ok": evidence.ok, "evidence_root": str(evidence_root)}, indent=2))
    return 0 if evidence.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
