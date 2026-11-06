#!/usr/bin/env python3
"""Generate durable evidence for Phase 11 §11.17 SIMULATED_LIFECYCLE_PROVEN closure."""

from __future__ import annotations

import hashlib
import json
import os
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

from src.ops.phase_11_section_11_17_simulated_lifecycle_proven_evidence_closure_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.phase_11_section_11_17_simulated_lifecycle_proven_evidence_closure_v1.verifier_v1 import (  # noqa: E402
    verify_phase_11_section_11_17_simulated_lifecycle_proven_v1,
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _resolve_sha(*, env_key: str, git_arg: str) -> str:
    override = os.environ.get(env_key, "").strip()
    if override:
        return override
    return subprocess.check_output(
        ["git", "rev-parse", git_arg], cwd=str(_REPO_ROOT), text=True
    ).strip()


def main() -> int:
    evidence_root = _REPO_ROOT / "docs" / "evidence" / EVIDENCE_DIRNAME
    productive = evidence_root / "productive_binding"
    productive.mkdir(parents=True, exist_ok=True)

    skip_pytest = os.environ.get("PEAK_TRADE_SKIP_PYTEST", "").strip() == "1"
    test_node = (
        "tests/ops/test_phase_11_section_11_17_simulated_lifecycle_proven_evidence_closure_v1.py"
    )
    if skip_pytest:
        test_results = {
            "command": ["python", "-m", "pytest", "-q", test_node],
            "returncode": None,
            "stdout": "PEAK_TRADE_SKIP_PYTEST=1_NO_REAL_PYTEST_EXECUTED",
            "stderr": "",
            "passed": False,
            "SKIPPED_ON_AGENT_SURFACE": True,
            "RUNTIME_VERIFICATION": "NOT_RUN",
            "STATIC_CONTRACT_VALIDATION": "NOT_APPLICABLE_FOR_PYTEST",
            "TEST_RESULT": "UNVERIFIED_NO_SHELL_SURFACE",
            "integrity_note": (
                "Skip path must never encode passed=true. "
                "Do not interpret agent-surface skip as runtime PASS."
            ),
        }
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "PYTEST_SKIP_FORBIDDEN_FOR_DURABLE_SEAL",
                    "test_results": test_results,
                },
                sort_keys=True,
            )
        )
        return 2

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

    verification = verify_phase_11_section_11_17_simulated_lifecycle_proven_v1()
    if not verification.get("ok"):
        print(json.dumps({"ok": False, "error": "VERIFIER_FAILED", "verification": verification}))
        return 2

    repo_sha = _resolve_sha(env_key="PEAK_TRADE_REPOSITORY_SHA", git_arg="HEAD")
    origin_main = _resolve_sha(env_key="PEAK_TRADE_ORIGIN_MAIN_SHA", git_arg="origin/main")

    binding = verification["binding"]
    claims = verification["claims"]
    _write_json(productive / "claims.json", claims)
    _write_json(productive / "binding_proof.json", binding)
    _write_json(productive / "verifier_result.json", verification)
    _write_json(productive / "test_results.json", test_results)
    _write_json(
        productive / "repository_sha.json",
        {"HEAD": repo_sha, "origin_main": origin_main},
    )
    _write_json(
        productive / "activation_state.json",
        {
            "ACTIVATION_STATE": "not_activated",
            "NETWORK_SESSION_STARTED": False,
            "CREDENTIAL_ACCESS": False,
            "ORDER_SUBMIT_REACHABLE": False,
            "CAPABILITY_11_13_STARTED": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
            "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
            "CANONICAL_STATEFUL_CORE_PROVEN": True,
            "SIMULATED_LIFECYCLE_PROVEN": True,
        },
    )
    _write_json(
        productive / "negative_controls.json",
        {
            "NETWORK_SESSION_STARTED": False,
            "CREDENTIAL_ACCESS": False,
            "ORDER_SUBMIT_REACHABLE": False,
            "CAPABILITY_11_13_STARTED": False,
            "CORE_LOGIC_CHANGE": False,
            "TRADING_LOGIC_CHANGE": False,
            "REPROOF_EXECUTED": False,
            "FIXTURE_ONLY": False,
            "EXECUTION_STARTED": False,
        },
    )

    summary = {
        "capability_id": CAPABILITY_ID,
        "SECTION_11_17_FIELD": "SIMULATED_LIFECYCLE_PROVEN",
        "CANONICAL_STATEFUL_CORE_PROVEN": True,
        "SIMULATED_LIFECYCLE_PROVEN": True,
        "CLOSURE_METHOD": "EXISTING_EVIDENCE_BINDING",
        "SOURCE_CAPABILITY_ID": binding["SOURCE_CAPABILITY_ID"],
        "SOURCE_EVIDENCE_DIGEST": binding["SOURCE_EVIDENCE_DIGEST"],
        "EVIDENCE_REUSED": True,
        "REPROOF_EXECUTED": False,
        "TESTNET_LIFECYCLE_PROVEN": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_ACTIVE": False,
        "CAPABILITY_11_13_STARTED": False,
        "CORE_LOGIC_CHANGE": False,
        "ACTIVATION_STATE": "not_activated",
        "EXECUTION_STARTED": False,
        "NETWORK_SESSION_STARTED": False,
        "CREDENTIAL_ACCESS": False,
        "verifier_result": "PASS",
        "ok": True,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository_sha": repo_sha,
        "origin_main_sha": origin_main,
        "claims": claims,
    }
    _write_json(evidence_root / "claims.json", claims)
    _write_json(evidence_root / SUMMARY_FILENAME, summary)

    lines: list[str] = []
    for path in sorted(evidence_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == MANIFEST_FILENAME:
            continue
        if path.name == "MANIFEST_SEAL_STATUS.json":
            continue
        rel = path.relative_to(evidence_root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    (evidence_root / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "capability_id": CAPABILITY_ID,
                "SIMULATED_LIFECYCLE_PROVEN": True,
                "evidence_dir": str(evidence_root),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
