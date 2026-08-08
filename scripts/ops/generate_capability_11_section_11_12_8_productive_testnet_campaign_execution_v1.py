#!/usr/bin/env python3
"""Generate durable evidence for Cap 11 §11.12.8 productive Testnet campaign execution."""

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

from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.verifier_v1 import (  # noqa: E402
    verify_capability_11_section_11_12_8_productive_testnet_campaign_execution_v1,
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

    test_node = (
        "tests/ops/test_capability_11_section_11_12_8_productive_testnet_campaign_execution_v1.py"
    )
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

    verification = verify_capability_11_section_11_12_8_productive_testnet_campaign_execution_v1()
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
    proof = verification["proofs"]["productive_execution"]
    _write_json(productive / "claims.json", claims)
    _write_json(productive / "call_graph_before.json", verification["call_graph_before"])
    _write_json(productive / "call_graph_after.json", verification["call_graph_after"])
    _write_json(productive / "productive_execution_proof.json", proof)
    _write_json(productive / "test_results.json", test_results)
    _write_json(
        productive / "repository_sha.json",
        {"HEAD": repo_sha, "origin_main": origin_main},
    )
    _write_json(
        productive / "activation_state.json",
        {
            "ACTIVATION_STATE": "not_activated",
            "REFERENCE_ONLY": False,
            "PRODUCTIVE_TESTNET_CAMPAIGN_EXECUTION_IMPLEMENTED": True,
            "PATH_PREDECESSOR_PRESERVED": True,
            "RUN_AUTHORIZED": False,
            "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
            "PRODUCTIVE_TESTNET_CAMPAIGN_COMPLETED": False,
            "NETWORK_EFFECT": "NONE",
            "ORDER_EFFECT": "NONE",
            "LIVE_ORDER_EFFECT": "NONE",
            "ORDER_SEND_DISABLED": True,
            "ORDERS_AUTHORIZED": False,
            "NETWORK_WRITES_AUTHORIZED": False,
            "NETWORK_WRITE_PERFORMED": False,
            "NETWORK_SESSION_STARTED": False,
            "EXCHANGE_ORDER_SUBMIT_REACHABLE": False,
            "TESTNET_ORDER_SUBMIT_PERFORMED": False,
            "CAPABILITY_11_13_STARTED": False,
            "SECTION_11_13_STARTED": False,
        },
    )
    _write_json(productive / "verifier_result.json", verification)

    summary = {
        "capability_id": CAPABILITY_ID,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "HEAD": repo_sha,
        "origin_main": origin_main,
        "PRODUCTIVE_TESTNET_CAMPAIGN_EXECUTION_IMPLEMENTED": True,
        "RUN_AUTHORIZED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "claims": claims,
    }
    _write_json(evidence_root / SUMMARY_FILENAME, summary)
    _write_json(evidence_root / CLAIMS_FILENAME, claims)

    files: list[Path] = []
    for path in sorted(evidence_root.rglob("*")):
        if path.is_file() and path.name != MANIFEST_FILENAME:
            files.append(path)
    lines = [
        f"{_sha256_bytes(path.read_bytes())}  {path.relative_to(evidence_root).as_posix()}"
        for path in files
    ]
    (evidence_root / MANIFEST_FILENAME).write_text("\n".join(lines) + "\n", encoding="utf-8")

    check = subprocess.run(
        ["shasum", "-a", "256", "-c", MANIFEST_FILENAME],
        cwd=str(evidence_root),
        capture_output=True,
        text=True,
        check=False,
    )
    print(
        json.dumps(
            {
                "ok": check.returncode == 0,
                "capability_id": CAPABILITY_ID,
                "MANIFEST_VERIFY_RC": check.returncode,
                "NETWORK_EFFECT": "NONE",
                "ORDER_EFFECT": "NONE",
                "LIVE_ORDER_EFFECT": "NONE",
                "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
                "RUN_AUTHORIZED": False,
                "SECTION_11_13_STARTED": False,
            },
            sort_keys=True,
        )
    )
    return 0 if check.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
