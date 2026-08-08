#!/usr/bin/env python3
"""Generate durable evidence for §11.12.8 real productive execute-path unlock."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (str(_REPO_ROOT), str(_SRC_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (  # noqa: E402
    ACCEPTANCE_PROOF_FILENAME,
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    EVIDENCE_DIRNAME,
    FORENSIC_TRACE_FILENAME,
    GOVERNANCE_ACCEPTANCE_FILENAME,
    MANIFEST_FILENAME,
    RUNTIME_TRACE_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.verifier_v1 import (  # noqa: E402
    verify_section_11_12_8_real_productive_testnet_execute_path_unlock_v1,
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

    test_node = "tests/ops/test_section_11_12_8_real_productive_testnet_execute_path_unlock_v1.py"
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
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-2000:],
        "passed": proc.returncode == 0,
    }
    if proc.returncode != 0:
        print(json.dumps({"ok": False, "error": "TESTS_FAILED", "test_results": test_results}))
        return 2

    import tempfile

    with tempfile.TemporaryDirectory(prefix="pt_unlock_gen_") as tmp:
        verification = verify_section_11_12_8_real_productive_testnet_execute_path_unlock_v1(
            work_dir=Path(tmp) / "verify"
        )
    if not verification.get("ok"):
        print(json.dumps({"ok": False, "error": "VERIFIER_FAILED", "verification": verification}))
        return 2

    repo_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(_REPO_ROOT), text=True
    ).strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    claims = verification["claims"]
    gate = verification["gate"]
    forensic = verification["forensic"]
    governance = verification.get("governance") or {}
    runtime_audit = gate.get("runtime_audit") or {}

    _write_json(productive / "repository_sha.json", {"repository_sha": repo_sha})
    _write_json(productive / "test_results.json", test_results)
    _write_json(productive / ACCEPTANCE_PROOF_FILENAME, gate)
    _write_json(productive / FORENSIC_TRACE_FILENAME, forensic)
    _write_json(productive / RUNTIME_TRACE_FILENAME, runtime_audit)
    _write_json(productive / GOVERNANCE_ACCEPTANCE_FILENAME, governance)
    _write_json(productive / CLAIMS_FILENAME, claims)
    _write_json(evidence_root / CLAIMS_FILENAME, claims)

    summary = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "HEAD": repo_sha,
        "origin_main": repo_sha,
        "generated_at": generated_at,
        "tests_passed": True,
        "verifier_ok": True,
        "PRE_MERGE_ACCEPTANCE_GATE": gate.get("PRE_MERGE_ACCEPTANCE_GATE"),
        "GOVERNANCE_ACCEPTANCE": governance.get("GOVERNANCE_ACCEPTANCE"),
        "CANONICAL_NEXT_STEP_AFTER_MERGE": claims.get("CANONICAL_NEXT_STEP_AFTER_MERGE"),
        "AUTHORIZATION_REQUIRED": claims.get("AUTHORIZATION_REQUIRED"),
        "NETWORK_SEND_BOUNDARY_REACHED": gate.get("NETWORK_SEND_BOUNDARY_REACHED"),
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "claims": claims,
    }
    _write_json(evidence_root / SUMMARY_FILENAME, summary)

    manifest_lines: list[str] = []
    for path in sorted(productive.rglob("*")):
        if path.is_file():
            rel = path.relative_to(evidence_root).as_posix()
            digest = _sha256_bytes(path.read_bytes())
            manifest_lines.append(f"{digest}  {rel}")
    for name in (CLAIMS_FILENAME, SUMMARY_FILENAME):
        path = evidence_root / name
        digest = _sha256_bytes(path.read_bytes())
        manifest_lines.append(f"{digest}  {name}")
    (evidence_root / MANIFEST_FILENAME).write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "evidence_root": str(evidence_root), "summary": summary}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
