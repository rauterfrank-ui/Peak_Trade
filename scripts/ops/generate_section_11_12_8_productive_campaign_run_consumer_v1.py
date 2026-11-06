#!/usr/bin/env python3
"""Generate durable evidence for §11.12.8 productive campaign RUN CONSUMER."""

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

from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CLAIMS_FILENAME,
    EVIDENCE_DIRNAME,
    MANIFEST_FILENAME,
    SUMMARY_FILENAME,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.verifier_v1 import (  # noqa: E402
    verify_section_11_12_8_run_consumer_v1,
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

    test_node = "tests/ops/test_section_11_12_8_productive_campaign_run_consumer_v1.py"
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

    verification = verify_section_11_12_8_run_consumer_v1()
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
    proof = verification["proofs"]["run_consumer"]
    _write_json(productive / "claims.json", claims)
    _write_json(productive / "call_graph_before.json", verification["call_graph_before"])
    _write_json(productive / "call_graph_after.json", verification["call_graph_after"])
    _write_json(productive / "run_consumer_proof.json", proof)
    _write_json(productive / "test_results.json", test_results)
    _write_json(
        productive / "repository_sha.json",
        {"HEAD": repo_sha, "origin_main": origin_main},
    )
    _write_json(
        productive / "activation_state.json",
        {
            "ACTIVATION_STATE": "not_activated",
            "IMPLEMENTATION_ONLY": True,
            "PRODUCTIVE_RUN_CONSUMER_IMPLEMENTED": True,
            "PRODUCTIVE_RUN_CONSUMER_PRESENT": True,
            "PRODUCTIVE_RUN_EXECUTION_AUTHORIZED": False,
            "NEW_WRAPPER_LAYER_CREATED": False,
            "TERMINAL_CONSUMER_ROLE_UNCHANGED": True,
            "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
            "CREDENTIAL_PLAINTEXT_LOADED": False,
            "NETWORK_EFFECT": "NONE",
            "ORDER_EFFECT": "NONE",
            "LIVE_ORDER_EFFECT": "NONE",
            "SECTION_11_13_STARTED": False,
        },
    )

    claim_root = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "PRODUCTIVE_RUN_CONSUMER_PRESENT": True,
        "PRODUCTIVE_RUN_EXECUTION_AUTHORIZED": False,
        "TERMINAL_CONSUMER_ROLE_UNCHANGED": True,
        "NEW_WRAPPER_LAYER_CREATED": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "SECTION_11_13_STARTED": False,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": False,
    }
    _write_json(evidence_root / CLAIMS_FILENAME, claim_root)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    summary = {
        "CAPABILITY_ID": CAPABILITY_ID,
        "generated_at": generated_at,
        "HEAD": repo_sha,
        "origin_main": origin_main,
        "verifier_ok": True,
        "tests_passed": True,
        "claims": claims,
    }
    _write_json(evidence_root / SUMMARY_FILENAME, summary)

    manifest_lines: list[str] = []
    for path in sorted(evidence_root.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(evidence_root).as_posix()
        digest = _sha256_bytes(path.read_bytes())
        manifest_lines.append(f"{digest}  {rel}")
    (evidence_root / MANIFEST_FILENAME).write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "CAPABILITY_ID": CAPABILITY_ID,
                "evidence_root": str(evidence_root),
                "HEAD": repo_sha,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
