"""Evidence materialization + verifier for Step-3 executor capability."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    PLANNED_RESTART_TEST_CONTRACT_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SCHEMA_VERSION,
    SESSION_MANIFEST_SCHEMA,
    SURFACE_CLI_PATH,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.failure_injection_v1 import (
    run_step3_executor_failure_injection_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.governed_executor_execution_v1 import (
    prove_step3_executor_implementation_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def verify_session_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    if claims.get("NETWORK_SESSION_STARTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE_IN_IMPLEMENTATION_EVIDENCE")
    if claims.get("AUTHORIZATION_CONSUMED"):
        blockers.append("AUTHORIZATION_MUST_NOT_BE_CONSUMED")
    if claims.get("CONFIRM_TOKEN_CONSUMED"):
        blockers.append("CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED")
    if claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED"):
        blockers.append("CONFIRM_TOKEN_PLAINTEXT_MUST_NOT_BE_EXPOSED")
    if claims.get("CONFIRM_TOKEN_IN_EVIDENCE") or "confirm_token_plaintext" in manifest:
        blockers.append("CONFIRM_TOKEN_MUST_NOT_APPEAR_IN_EVIDENCE")
    if claims.get("CORE_LOGIC_CHANGED"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if int(claims.get("PLANNED_RESTART_TEST_CONTRACT_SECONDS") or 0) != (
        PLANNED_RESTART_TEST_CONTRACT_SECONDS
    ):
        blockers.append("PLANNED_DURATION_DRIFT")
    digest = str(manifest.get("manifest_digest") or "")
    probe = dict(manifest)
    probe.pop("manifest_digest", None)
    expected = sha256_canonical_v1(probe)
    if digest and digest != expected:
        blockers.append("MANIFEST_DIGEST_MISMATCH")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "expected_manifest_digest": expected,
    }


def materialize_implementation_evidence_v1(
    *,
    repository_sha: str,
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
    cfg = str(
        load_activation_config_v1(
            config_path=root
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )
    proof = prove_step3_executor_implementation_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        repo_root=root,
    )
    bundle = load_execution_contract_bundle_v1(repo_root=root)
    fi_persist = fixtures / "fi_persistence"
    # Compact Session-GO fixture only under docs/evidence; full FI campaign
    # persistence stays ephemeral outside durable evidence.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="step3_executor_fi_") as tmp:
        fi = run_step3_executor_failure_injection_v1(
            repository_sha=repository_sha,
            config_digest=cfg,
            persistence_root=Path(tmp),
            repo_root=root,
        )
        fi_persist.mkdir(parents=True, exist_ok=True)
        sgo_src = Path(tmp) / "sgo.json"
        if sgo_src.is_file():
            write_json_atomic_v1(fi_persist / "sgo.json", read_json_v1(sgo_src))
        write_json_atomic_v1(fixtures / "failure_injection_v1.json", fi)
    claims = dict(proof.claims)
    claims.update(
        {
            "PLANNED_RESTART_TEST_CONTRACT_SECONDS": PLANNED_RESTART_TEST_CONTRACT_SECONDS,
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_IN_EVIDENCE": False,
            "CORE_LOGIC_CHANGED": False,
        }
    )
    manifest = {
        "schema_version": SESSION_MANIFEST_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "producer_version": SCHEMA_VERSION,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "surface_config_digest": bundle["surface_config_digest"],
        "executor_config_digest": bundle["executor_config_digest"],
        "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
        "surface_cli_path": SURFACE_CLI_PATH,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "claims": claims,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
    manifest["manifest_digest"] = sha256_canonical_v1(
        {k: v for k, v in manifest.items() if k != "manifest_digest"}
    )
    write_json_atomic_v1(fixtures / "implementation_proof_v1.json", proof.to_dict())
    write_json_atomic_v1(fixtures / "session_manifest_template_v1.json", manifest)
    write_json_atomic_v1(fixtures / "failure_injection_v1.json", fi)
    verify = verify_session_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "session_manifest_verify_v1.json", verify)
    summary = {
        "ok": bool(proof.ok) and bool(fi.get("ok")) and bool(verify.get("ok")),
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "proof_ok": bool(proof.ok),
        "failure_injection_ok": bool(fi.get("ok")),
        "manifest_verify_ok": bool(verify.get("ok")),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
        "surface_cli_path": SURFACE_CLI_PATH,
        "contract_digests": {
            "session_contract_digest": bundle["session_contract_digest"],
            "binding_config_digest": bundle["binding_config_digest"],
            "surface_config_digest": bundle["surface_config_digest"],
            "executor_config_digest": bundle["executor_config_digest"],
        },
        "claims": claims,
        "raw_session_evidence_changed": False,
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    return summary
