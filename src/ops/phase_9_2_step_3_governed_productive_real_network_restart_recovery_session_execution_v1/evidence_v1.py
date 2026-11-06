"""Evidence materialization + offline verifier for Step-3 surface implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    BINDING_CLI_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    PRODUCTIVE_ENTRYPOINT_PATH,
    RUNTIME_CAPABILITY_ID,
    SCHEMA_VERSION,
    SESSION_MANIFEST_SCHEMA,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.governed_execution_surface_v1 import (
    prove_step3_execution_surface_implementation_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def build_session_manifest_template_v1(*, claims: Mapping[str, Any]) -> dict[str, Any]:
    payload = {
        "schema": SESSION_MANIFEST_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "runtime_capability_id": RUNTIME_CAPABILITY_ID,
        "session_id": TARGET_SESSION_ID,
        "claims": dict(claims),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "productive_session_manifest": False,
        "implementation_surface_only": True,
    }
    payload["manifest_digest"] = sha256_canonical_v1(
        {k: v for k, v in payload.items() if k != "manifest_digest"}
    )
    return payload


def verify_session_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    schema = str(manifest.get("schema") or "")
    capability = str(manifest.get("capability_id") or "")

    if schema != SESSION_MANIFEST_SCHEMA:
        blockers.append("MANIFEST_SCHEMA_MISMATCH")
    if capability != CAPABILITY_ID:
        blockers.append("MANIFEST_CAPABILITY_MISMATCH")
    # Reject Step-4 / Step-5 relabeling.
    if "STEP_4" in capability or "STEP_5" in capability or "prolonged" in schema.lower():
        blockers.append("STEP4_OR_STEP5_EVIDENCE_RELABEL_FORBIDDEN")
    if claims.get("NETWORK_SESSION_STARTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE_IN_IMPLEMENTATION_EVIDENCE")
    if claims.get("AUTHORIZATION_CONSUMED"):
        blockers.append("AUTHORIZATION_MUST_NOT_BE_CONSUMED")
    if claims.get("CONFIRM_TOKEN_CONSUMED"):
        blockers.append("CONFIRM_TOKEN_MUST_NOT_BE_CONSUMED")
    if claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED"):
        blockers.append("CONFIRM_TOKEN_PLAINTEXT_MUST_NOT_BE_EXPOSED")
    if claims.get("CORE_LOGIC_CHANGED"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if claims.get("REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED"):
        blockers.append("OVERCLAIM_REAL_SESSION_COMPLETED")
    if claims.get("RESTART_RECOVERY_LADDER_STEP_CLOSED"):
        blockers.append("OVERCLAIM_LADDER_STEP_CLOSED")

    digest = str(manifest.get("manifest_digest") or "")
    probe = dict(manifest)
    probe.pop("manifest_digest", None)
    expected = sha256_canonical_v1(probe)
    if digest and digest != expected:
        blockers.append("MANIFEST_DIGEST_MISMATCH")
    if not digest:
        blockers.append("MANIFEST_DIGEST_MISSING")

    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "expected_manifest_digest": expected,
        "claims_match_evidence": not blockers,
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
    from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.failure_injection_v1 import (  # noqa: E501
        run_step3_surface_failure_injection_v1,
    )

    proof = prove_step3_execution_surface_implementation_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        repo_root=root,
    )
    fi = run_step3_surface_failure_injection_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        repo_root=root,
        persistence_root=fixtures / "fi_persistence",
    )
    bundle = load_execution_contract_bundle_v1(repo_root=root)
    manifest = build_session_manifest_template_v1(claims=proof.claims)
    verify = verify_session_manifest_v1(manifest)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "runtime_capability_id": RUNTIME_CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
        "binding_cli_path": BINDING_CLI_PATH,
        "session_id": TARGET_SESSION_ID,
        "proof_ok": bool(proof.ok),
        "failure_injection_ok": bool(fi.get("ok")),
        "manifest_verify_ok": bool(verify.get("ok")),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "raw_session_evidence_changed": False,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "contract_digests": {
            "session_contract_digest": bundle["session_contract_digest"],
            "binding_config_digest": bundle["binding_config_digest"],
            "surface_config_digest": bundle["surface_config_digest"],
        },
        "claims": dict(proof.claims),
        "ok": bool(proof.ok and fi.get("ok") and verify.get("ok")),
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    write_json_atomic_v1(fixtures / "implementation_proof_v1.json", proof.to_dict())
    write_json_atomic_v1(fixtures / "failure_injection_v1.json", fi)
    write_json_atomic_v1(fixtures / "session_manifest_template_v1.json", manifest)
    write_json_atomic_v1(fixtures / "session_manifest_verify_v1.json", verify)
    write_json_atomic_v1(
        fixtures / "authority_reuse_matrix_v1.json",
        {
            "binding": BINDING_CLI_PATH,
            "harness": "phase_9_2_restart_recovery_session_contract_and_productive_harness_v1",
            "session_go": "phase_9_2_productive_restart_recovery_session_go_capability_v1",
            "confirm_token": "paper_shadow_observation_operator_go_session_preregistration_v1",
            "no_parallel_authority": True,
        },
    )
    return summary
