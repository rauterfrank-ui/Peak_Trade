#!/usr/bin/env python3
"""Fail-closed verifier for Cap 11.2 productive credential-load path binding evidence."""

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

from src.ops.capability_11_2_productive_credential_load_path_binding_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.capability_11_2_productive_credential_load_path_binding_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_2_productive_credential_load_path_binding_v1,
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
        "path_binding_proof.json",
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
    activation = _load(productive / "activation_state.json")
    tests = _load(productive / "test_results.json")
    proof = _load(productive / "path_binding_proof.json")
    live_verify = verify_capability_11_2_productive_credential_load_path_binding_v1()

    checks = {
        "capability_id_match": summary.get("capability_id") == CAPABILITY_ID,
        "verifier_summary_pass": summary.get("verifier_result") == "PASS",
        "live_verifier_pass": live_verify.get("ok") is True,
        "tests_passed": tests.get("passed") is True,
        "core_logic_unchanged": claims.get("CORE_LOGIC_CHANGE") is False,
        "activation_not_activated": activation.get("ACTIVATION_STATE") == "not_activated",
        "credential_load_allowed_default_false": claims.get("CREDENTIAL_LOAD_ALLOWED_DEFAULT")
        is False,
        "no_credential_load": claims.get("CREDENTIAL_LOAD_PERFORMED") is False,
        "no_credential_access": claims.get("EXCHANGE_CREDENTIAL_ACCESS_REACHABLE") is False,
        "no_network": claims.get("NETWORK_SESSION_STARTED") is False,
        "cap_11_3_not_started": claims.get("CAPABILITY_11_3_STARTED") is False,
        "cap_11_13_not_started": claims.get("CAPABILITY_11_13_STARTED") is False,
        "withdrawal_false": claims.get("WITHDRAWAL_PERMISSION") is False,
        "plaintext_rejected": proof.get("plaintext_rejected") is True,
        "complete_path_load_forbidden": proof.get("complete_path_load_still_forbidden") is True,
        "path_binding_ok": proof.get("ok") is True,
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
