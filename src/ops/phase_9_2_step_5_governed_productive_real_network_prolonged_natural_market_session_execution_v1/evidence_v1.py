"""Evidence materialization + verifier for Step-5 execution capability."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    BINDING_CLI_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    PLANNED_SESSION_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SCHEMA_VERSION,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.failure_injection_v1 import (
    run_step5_execution_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (
    prove_step5_execution_implementation_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def claims_match_telemetry_v1(
    *,
    claims: Mapping[str, Any],
    telemetry: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    pairs = (
        ("REQUEST_COUNT", "request_count"),
        ("DISTINCT_OBSERVATION_COUNT", "distinct_observation_count"),
        ("NETWORK_SESSION_STARTED", "network_session_started"),
    )
    for claim_key, tel_key in pairs:
        if claim_key in claims and tel_key in telemetry:
            if claims[claim_key] != telemetry[tel_key]:
                blockers.append(f"CLAIM_TELEMETRY_MISMATCH:{claim_key}")
    # Negative safety claims must stay false
    for key in (
        "ORDER_SIDE_EFFECT_OCCURRED",
        "CREDENTIAL_ACCESS_OCCURRED",
        "PRIVATE_ENDPOINT_ACCESS_OCCURRED",
        "AUTH_HEADER_TRANSMITTED",
    ):
        if bool(claims.get(key)) or bool(telemetry.get(key.lower())):
            blockers.append(f"SAFETY_CLAIM_DRIFT:{key}")
    return {"ok": not blockers, "blockers": blockers, "claims_match_telemetry": not blockers}


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
    if claims.get("CORE_LOGIC_CHANGED"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if int(claims.get("PLANNED_SESSION_DURATION_SECONDS") or 0) != PLANNED_SESSION_DURATION_SECONDS:
        blockers.append("PLANNED_DURATION_DRIFT")
    if (
        int(claims.get("MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS") or 0)
        != MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS
    ):
        blockers.append("MINIMUM_DURATION_DRIFT")
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


def materialize_terminal_evidence_v1(
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
    proof = prove_step5_execution_implementation_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        repo_root=root,
    )
    write_json_atomic_v1(fixtures / "implementation_proof_v1.json", proof.to_dict())
    bundle = load_execution_contract_bundle_v1(repo_root=root)
    write_json_atomic_v1(
        fixtures / "contract_digests_v1.json",
        {
            "session_contract_path": bundle["session_contract_path"],
            "session_contract_digest": bundle["session_contract_digest"],
            "binding_config_path": bundle["binding_config_path"],
            "binding_config_digest": bundle["binding_config_digest"],
            "planned_session_duration_seconds": bundle["planned_session_duration_seconds"],
            "minimum_successful_wallclock_seconds": bundle["minimum_successful_wallclock_seconds"],
            "pacing": bundle["pacing"],
        },
    )
    fi = run_step5_execution_failure_injection_v1(
        repository_sha=repository_sha,
        config_digest=cfg,
        persistence_root=fixtures / "failure_injection",
        repo_root=root,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    structural = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
        "binding_cli_path": BINDING_CLI_PATH,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
    write_json_atomic_v1(fixtures / "structural_proof_v1.json", structural)
    (fixtures / "focused_tests.txt").write_text(
        "tests/ops/test_phase_9_2_step_5_governed_productive_real_network_"
        "prolonged_natural_market_session_execution_v1.py\n",
        encoding="utf-8",
    )

    claims = dict(proof.claims)
    claims.update(
        {
            "FAILURE_INJECTION_OK": bool(fi.get("ok")),
            "EVIDENCE_CREATED": True,
            "SESSION_CONTRACT_DIGEST": bundle["session_contract_digest"],
            "BINDING_CONFIG_DIGEST": bundle["binding_config_digest"],
        }
    )
    manifest = {
        "schema": "phase_9_2_step_5_governed_prolonged_natural_market_session_execution_manifest.v1",
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "claims": claims,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }
    manifest["manifest_digest"] = sha256_canonical_v1(
        {k: v for k, v in manifest.items() if k != "manifest_digest"}
    )
    write_json_atomic_v1(fixtures / "manifest_v1.json", manifest)
    verified = verify_session_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)

    # Idempotent rewrite
    write_json_atomic_v1(fixtures / "manifest_v1.json", manifest)

    summary = {
        "ok": bool(proof.ok and fi.get("ok") and verified.get("ok")),
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "claims": claims,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
        "core_logic_changed": False,
        "verifier": verified,
        "evidence_root": str(out),
        "claims_match_evidence": bool(verified.get("ok")),
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    digest_lines = []
    for path in sorted(fixtures.rglob("*")):
        if path.is_file():
            digest_lines.append(
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
                f"fixtures/{path.relative_to(fixtures)}"
            )
    digest_lines.append(
        f"{hashlib.sha256((out / 'SUMMARY.json').read_bytes()).hexdigest()}  SUMMARY.json"
    )
    (out / "MANIFEST.sha256").write_text("\n".join(digest_lines) + "\n", encoding="utf-8")
    return summary
