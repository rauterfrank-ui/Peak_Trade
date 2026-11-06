"""Evidence materialization for Step-6 session-execution implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.failure_injection_v1 import (
    run_step6_session_execution_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.governed_session_execution_v1 import (
    prove_step6_session_execution_implementation_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.verifier_v1 import (
    verify_session_execution_implementation_manifest_v1,
)


def materialize_session_execution_implementation_evidence_v1(
    *,
    repository_sha: str,
    config_digest: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    proof = prove_step6_session_execution_implementation_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        repo_root=root,
    )
    fi = run_step6_session_execution_failure_injection_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
    )

    write_json_atomic_v1(
        fixtures / "session_execution_implementation_proof_v1.json", proof.to_dict()
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "target_session_id": TARGET_SESSION_ID,
        "claims": dict(proof.claims),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "confirm_token_minted": False,
        "network_calls": 0,
        "failure_injection_ok": bool(fi.get("ok")),
        "proof_ok": bool(proof.ok),
        "blockers": list(proof.blockers),
        "manifest_digest": "",
    }
    manifest["manifest_digest"] = sha256_canonical_v1({**manifest, "manifest_digest": ""})
    write_json_atomic_v1(out / "session_execution_implementation_manifest_v1.json", manifest)

    verifier = verify_session_execution_implementation_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "session_execution_implementation_verifier_v1.json", verifier)

    summary = {
        "ok": bool(proof.ok and fi.get("ok") and verifier.get("ok")),
        "capability_id": CAPABILITY_ID,
        "evidence_root": str(out),
        "claims": dict(proof.claims),
        "verifier": verifier,
        "failure_injection_ok": bool(fi.get("ok")),
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_COUNT": 0,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "SESSION_EXECUTED": False,
        "PHASE_9_2_STEP_6_STATUS": "OPEN",
        "PHASE_9_2_STEP_7_STATUS": "OPEN",
        "STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT": True,
        "STEP6_SESSION_OWNER_PRESENT": True,
        "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT": True,
        "STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_PRESENT": True,
        "STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_RUNTIME_REACHABLE": True,
        "STEP6_GOVERNED_SESSION_CLOSED": False,
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    lines = []
    for rel in (
        "SUMMARY.json",
        "session_execution_implementation_manifest_v1.json",
        "fixtures/session_execution_implementation_proof_v1.json",
        "fixtures/failure_injection_results_v1.json",
        "fixtures/session_execution_implementation_verifier_v1.json",
    ):
        p = out / rel
        digest = sha256_canonical_v1(p.read_text(encoding="utf-8"))
        lines.append(f"{digest}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return summary
