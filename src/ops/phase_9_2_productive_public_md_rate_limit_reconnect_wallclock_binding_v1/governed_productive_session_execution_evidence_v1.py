"""Evidence materialization for Step-4 governed productive session execution implementation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CANONICAL_WALLCLOCK_RUNNER,
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SESSION_EXECUTION_EVIDENCE_DIRNAME,
    SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_failure_injection_v1 import (
    run_governed_productive_session_execution_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_productive_session_execution_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    prove_governed_productive_session_execution_implementation_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def verify_session_execution_implementation_manifest_v1(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    if claims.get("NETWORK_SESSION_EXECUTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE")
    if claims.get("AUTHORIZATION_CONSUMED"):
        blockers.append("AUTHORIZATION_MUST_NOT_BE_CONSUMED")
    if claims.get("CONFIRM_TOKEN_CONSUMED"):
        blockers.append("CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED")
    if claims.get("REAL_NETWORK_REQUEST_COUNT", 0) not in (0, False):
        blockers.append("REAL_NETWORK_REQUEST_COUNT_MUST_BE_ZERO")
    if not claims.get("PRODUCTIVE_CALL_GRAPH_COMPLETE"):
        blockers.append("PRODUCTIVE_CALL_GRAPH_COMPLETE_REQUIRED")
    if not claims.get("READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION"):
        blockers.append("READY_FOR_SEPARATE_SESSION_REQUIRED")
    if claims.get("RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED"):
        blockers.append("LADDER_MUST_REMAIN_OPEN")
    if claims.get("CORE_LOGIC_CHANGE"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    return {"ok": not blockers, "blockers": blockers, "verified": not blockers, "claims": claims}


def materialize_session_execution_implementation_evidence_v1(
    *,
    repository_sha: str,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    out = (
        Path(evidence_root)
        if evidence_root is not None
        else root / "docs" / "evidence" / SESSION_EXECUTION_EVIDENCE_DIRNAME
    )
    fixtures = out / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)
    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    now = 1_700_000_000.0
    proof = prove_governed_productive_session_execution_implementation_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "implementation_proof_v1.json", proof.to_dict())
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)
    fi = run_governed_productive_session_execution_failure_injection_v1(
        repository_sha=repository_sha,
        config_digest=cfg,
        persistence_root=fixtures / "failure_injection",
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    structural = {
        "implementation_capability_id": SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
        "runtime_capability_id": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        "binding_capability_id": GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
        "session_request_adapter_capability_id": SESSION_REQUEST_ADAPTER_CAPABILITY_ID,
        "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
        "productive_session_runner": CANONICAL_WALLCLOCK_RUNNER,
        "network_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "real_network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
    write_json_atomic_v1(fixtures / "structural_proof_v1.json", structural)
    (fixtures / "focused_tests.txt").write_text(
        "tests/ops/test_phase_9_2_step_4_governed_productive_session_execution_implementation_v1.py\n",
        encoding="utf-8",
    )

    claims = dict(proof.claims)
    claims.update(
        {
            "RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED": True,
            "REAL_NETWORK_SESSION_NOT_STARTED": True,
            "GOVERNED_FAULT_PATH_BOUND": bool((proof.fault_path or {}).get("ok")),
            "EXECUTOR_CODE_EXISTS": True,
            "EXECUTOR_PRODUCTIVELY_BOUND": bool(proof.productive_runner_bound),
            "PRODUCTIVE_SESSION_REACHABLE": bool(proof.ok),
            "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE": bool(proof.ok),
            "PRODUCTIVE_CALL_GRAPH_COMPLETE": bool(proof.ok),
            "FAILURE_INJECTION_OK": bool(fi.get("ok")),
            "PARITY_OK": bool(parity.get("ok")),
        }
    )
    manifest = {
        "schema": "phase_9_2_step_4_governed_productive_session_execution_implementation_manifest.v1",
        "capability_id": SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "claims": claims,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "network_session_executed": False,
        "real_network_request_count": 0,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
    manifest["manifest_digest"] = sha256_canonical_v1(manifest)
    write_json_atomic_v1(fixtures / "manifest_v1.json", manifest)
    verified = verify_session_execution_implementation_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)

    summary = {
        "ok": bool(proof.ok and fi.get("ok") and parity.get("ok") and verified.get("ok")),
        "capability_id": SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
        "runtime_capability_id": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "claims": claims,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "network_session_executed": False,
        "real_network_request_count": 0,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "core_logic_changed": False,
        "verifier": verified,
        "evidence_root": str(out),
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    digest_lines = []
    for path in sorted(fixtures.rglob("*")):
        if path.is_file():
            digest_lines.append(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  fixtures/{path.relative_to(fixtures)}"
            )
    digest_lines.append(
        f"{hashlib.sha256((out / 'SUMMARY.json').read_bytes()).hexdigest()}  SUMMARY.json"
    )
    (out / "MANIFEST.sha256").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return summary
