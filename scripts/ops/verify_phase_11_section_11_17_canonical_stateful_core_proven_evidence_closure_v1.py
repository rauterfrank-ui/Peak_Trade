#!/usr/bin/env python3
"""Fail-closed static verifier for Phase 11 §11.17 CANONICAL_STATEFUL_CORE_PROVEN evidence."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.phase_11_section_11_17_canonical_stateful_core_proven_evidence_closure_v1.verifier_v1 import (  # noqa: E402
    verify_phase_11_section_11_17_canonical_stateful_core_proven_v1,
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
        "binding_proof.json",
        "verifier_result.json",
        "test_results.json",
        "repository_sha.json",
        "activation_state.json",
        "negative_controls.json",
    ]
    for name in required:
        if not (productive / name).is_file():
            return _fail(f"MISSING_EVIDENCE_FILE:{name}")

    live = verify_phase_11_section_11_17_canonical_stateful_core_proven_v1()
    if not live.get("ok"):
        return _fail(f"LIVE_VERIFIER_FAILED:{live.get('error', live)}")

    summary = _load(summary_path)
    claims = _load(productive / "claims.json")
    binding = _load(productive / "binding_proof.json")
    activation = _load(productive / "activation_state.json")
    negatives = _load(productive / "negative_controls.json")
    tests = _load(productive / "test_results.json")

    if summary.get("capability_id") != CAPABILITY_ID:
        return _fail("SUMMARY_CAPABILITY_ID_MISMATCH")
    if summary.get("CANONICAL_STATEFUL_CORE_PROVEN") is not True:
        return _fail("SUMMARY_FIELD_NOT_TRUE")
    if summary.get("SIMULATED_LIFECYCLE_PROVEN") is not False:
        return _fail("SIMULATED_LIFECYCLE_MUST_REMAIN_FALSE")
    if summary.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is not False:
        return _fail("READY_MUST_REMAIN_FALSE")
    if summary.get("FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE") is not False:
        return _fail("ACTIVE_MUST_REMAIN_FALSE")
    if summary.get("CAPABILITY_11_13_STARTED") is not False:
        return _fail("CAP_11_13_MUST_REMAIN_FALSE")
    if claims.get("CANONICAL_STATEFUL_CORE_PROVEN") is not True:
        return _fail("CLAIMS_FIELD_NOT_TRUE")
    if binding.get("CANONICAL_STATEFUL_CORE_PROVEN") is not True:
        return _fail("BINDING_FIELD_NOT_TRUE")
    if binding.get("FIXTURE_ONLY") is not False:
        return _fail("BINDING_MUST_NOT_BE_FIXTURE_ONLY")
    if binding.get("EVIDENCE_REUSED") is not True:
        return _fail("BINDING_MUST_REUSE_EVIDENCE")
    if binding.get("REPROOF_EXECUTED") is not False:
        return _fail("REPROOF_MUST_BE_FALSE")
    if activation.get("CANONICAL_STATEFUL_CORE_PROVEN") is not True:
        return _fail("ACTIVATION_STATE_FIELD_NOT_TRUE")
    if activation.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is not False:
        return _fail("ACTIVATION_READY_NOT_FALSE")
    if negatives.get("ORDER_SUBMIT_REACHABLE") is not False:
        return _fail("ORDER_SUBMIT_REACHABLE")
    if negatives.get("NETWORK_SESSION_STARTED") is not False:
        return _fail("NETWORK_SESSION_STARTED")
    if negatives.get("CREDENTIAL_ACCESS") is not False:
        return _fail("CREDENTIAL_ACCESS")
    if tests.get("passed") is not True:
        return _fail("TEST_RESULTS_NOT_PASSED")
    if tests.get("SKIPPED_ON_AGENT_SURFACE") is True:
        return _fail("SKIPPED_AGENT_SURFACE_TESTS_FORBIDDEN_FOR_DURABLE_SEAL")
    if tests.get("RUNTIME_VERIFICATION") == "NOT_RUN":
        return _fail("RUNTIME_VERIFICATION_NOT_RUN")
    if summary.get("RUNTIME_VERIFICATION") == "NOT_RUN":
        return _fail("SUMMARY_RUNTIME_VERIFICATION_NOT_RUN")
    if summary.get("verifier_result") != "PASS":
        return _fail("SUMMARY_VERIFIER_RESULT_NOT_PASS")

    print(
        json.dumps(
            {
                "ok": True,
                "VERIFIER_RESULT": "PASS",
                "CAPABILITY_ID": CAPABILITY_ID,
                "CANONICAL_STATEFUL_CORE_PROVEN": True,
                "MANIFEST_VERIFY_RC": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
