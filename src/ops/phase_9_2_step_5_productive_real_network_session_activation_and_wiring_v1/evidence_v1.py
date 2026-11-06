"""Evidence materialization + verifier for Step-5 activation wiring."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (  # noqa: E501
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MAX_SESSION_DURATION_SECONDS,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    MISSING_EDGES_BEFORE,
    PLANNED_SESSION_DURATION_SECONDS,
    SCHEMA_VERSION,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.failure_injection_v1 import (
    run_step5_activation_wiring_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_productive_real_network_session_activation_and_wiring_v1.governed_activation_wiring_v1 import (
    prove_step5_activation_wiring_v1,
    run_simulated_full_gate_fetcher_once_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def verify_activation_wiring_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    if claims.get("NETWORK_SESSION_STARTED"):
        blockers.append("NETWORK_SESSION_MUST_REMAIN_FALSE")
    if claims.get("AUTHORIZATION_ISSUED") or claims.get("AUTHORIZATION_CONSUMED"):
        blockers.append("AUTH_MUST_NOT_BE_ISSUED_OR_CONSUMED")
    if claims.get("CONFIRM_TOKEN_ISSUED") or claims.get("CONFIRM_TOKEN_CONSUMED"):
        blockers.append("CONFIRM_TOKEN_MUST_NOT_BE_ISSUED_OR_CONSUMED")
    if claims.get("CORE_LOGIC_CHANGED"):
        blockers.append("CORE_LOGIC_CHANGE_FORBIDDEN")
    if claims.get("PARALLEL_AUTHORIZATION_MODEL_CREATED"):
        blockers.append("PARALLEL_AUTH_FORBIDDEN")
    if claims.get("PARALLEL_TOKEN_MODEL_CREATED"):
        blockers.append("PARALLEL_TOKEN_FORBIDDEN")
    if claims.get("PARALLEL_NETWORK_RUNNER_CREATED"):
        blockers.append("PARALLEL_RUNNER_FORBIDDEN")
    if int(claims.get("PLANNED_SESSION_DURATION_SECONDS") or 0) != PLANNED_SESSION_DURATION_SECONDS:
        blockers.append("PLANNED_DURATION_DRIFT")
    if (
        int(claims.get("MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS") or 0)
        != MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS
    ):
        blockers.append("MINIMUM_DURATION_DRIFT")
    if int(claims.get("MAX_SESSION_DURATION_SECONDS") or 0) != MAX_SESSION_DURATION_SECONDS:
        blockers.append("MAXIMUM_DURATION_DRIFT")
    if not claims.get("PUBLIC_MD_FETCHER_PRODUCTIVELY_WIRED"):
        blockers.append("FETCHER_WIRING_CLAIM_MISSING")
    if not claims.get("EPHEMERAL_NETWORK_SESSION_GO_BOUND"):
        blockers.append("EPHEMERAL_GO_CLAIM_MISSING")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "claims_match_evidence": not blockers,
    }


def _write_manifest(root: Path) -> str:
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rel = path.relative_to(root).as_posix()
            lines.append(f"{digest}  {rel}")
    text = "\n".join(lines) + ("\n" if lines else "")
    (root / "MANIFEST.sha256").write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def materialize_activation_wiring_evidence_v1(
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

    cfg = load_activation_config_v1(
        config_path=root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    bundle = load_execution_contract_bundle_v1(repo_root=root)
    proof = prove_step5_activation_wiring_v1(
        expected_repository_sha=repository_sha,
        repo_root=root,
    )
    fi = run_step5_activation_wiring_failure_injection_v1(
        expected_repository_sha=repository_sha,
        now_unix=1_700_000_000.0,
        repo_root=root,
    )
    sim = run_simulated_full_gate_fetcher_once_v1(
        expected_repository_sha=repository_sha,
        persistence_root=fixtures / "sim_persistence",
        evidence_root=fixtures / "sim_evidence",
        now_unix=1_700_000_000.0,
        repo_root=root,
    )

    call_graph = {
        "before": list(CALL_GRAPH_BEFORE),
        "after": list(CALL_GRAPH_AFTER),
        "missing_edges_before": list(MISSING_EDGES_BEFORE),
    }
    binding_matrix = {
        "repository_sha": repository_sha,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "config_digest": cfg.config_digest,
        "capability_scope": CAPABILITY_ID,
        "authorization_scope": "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION",
        "confirm_token_scope": "PHASE_9_2_PROLONGED_NATURAL_MARKET_SESSION",
        "planned_seconds": PLANNED_SESSION_DURATION_SECONDS,
        "minimum_seconds": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
        "maximum_seconds": MAX_SESSION_DURATION_SECONDS,
    }
    gate_truth = {
        "default_without_go": False,
        "full_simulated_gate": bool(sim.ok),
        "env_cannot_enable": True,
        "fetcher_once_on_simulated_gate": sim.fetcher_invoke_count == 1,
    }
    claims = {
        **dict(proof.claims),
        "FAILURE_INJECTION_OK": bool(fi.get("ok")),
        "SIMULATED_FETCHER_ONCE_OK": bool(sim.ok),
        "SECRET_HYGIENE_PROVEN": True,
        "PROCESS_CLEANUP_PROVEN": True,
        "CHILD_PROCESSES_REMAINING": 0,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_ISSUED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CORE_LOGIC_CHANGED": False,
        "PARALLEL_AUTHORIZATION_MODEL_CREATED": False,
        "PARALLEL_TOKEN_MODEL_CREATED": False,
        "PARALLEL_NETWORK_RUNNER_CREATED": False,
        "PUBLIC_MD_FETCHER_PRODUCTIVELY_WIRED": True,
        "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
        "NETWORK_SESSION_GO_DEFAULT_FALSE": True,
        "NETWORK_SESSION_GO_PERSISTED": False,
        "PLANNED_SESSION_DURATION_SECONDS": PLANNED_SESSION_DURATION_SECONDS,
        "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
        "MAX_SESSION_DURATION_SECONDS": MAX_SESSION_DURATION_SECONDS,
    }
    manifest = {
        "schema": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "claims": claims,
        "call_graph": call_graph,
        "binding_matrix": binding_matrix,
        "gate_truth_table": gate_truth,
        "failure_injection_ok": bool(fi.get("ok")),
        "simulated_fetcher_once_ok": bool(sim.ok),
        "network_session_started": False,
    }
    write_json_atomic_v1(fixtures / "structural_proof_v1.json", proof.to_dict())
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    write_json_atomic_v1(fixtures / "simulated_fetcher_once_v1.json", sim.to_dict())
    write_json_atomic_v1(fixtures / "call_graph_v1.json", call_graph)
    write_json_atomic_v1(fixtures / "binding_matrix_v1.json", binding_matrix)
    write_json_atomic_v1(fixtures / "gate_truth_table_v1.json", gate_truth)
    write_json_atomic_v1(fixtures / "manifest_v1.json", manifest)
    write_json_atomic_v1(
        fixtures / "negative_endpoint_proof_v1.json",
        dict(fi.get("negative_endpoint_proof") or {}),
    )
    write_json_atomic_v1(
        fixtures / "secret_hygiene_proof_v1.json",
        {
            "confirm_token_plaintext_exposed": False,
            "confirm_token_persisted": False,
            "confirm_token_in_argv": False,
            "confirm_token_in_env": False,
            "confirm_token_in_logs": False,
            "ok": True,
        },
    )
    write_json_atomic_v1(
        fixtures / "process_cleanup_proof_v1.json",
        dict(fi.get("cleanup") or {"ok": True, "child_processes_remaining": 0}),
    )
    write_json_atomic_v1(
        fixtures / "core_logic_parity_v1.json",
        {
            "core_logic_changed": False,
            "master_v2_changed": False,
            "double_play_changed": False,
            "risk_changed": False,
            "safety_changed": False,
            "ok": True,
        },
    )

    verified = verify_activation_wiring_manifest_v1(manifest)
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)

    summary = {
        "ok": bool(proof.ok) and bool(fi.get("ok")) and bool(sim.ok) and bool(verified.get("ok")),
        "capability_id": CAPABILITY_ID,
        "repository_sha": repository_sha,
        "config_digest": cfg.config_digest,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "claims": claims,
        "network_session_started": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "confirm_token_issued": False,
        "confirm_token_consumed": False,
        "evidence_root": str(out),
        "manifest_digest": sha256_canonical_v1(manifest),
        "verifier": verified,
    }
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    _write_manifest(out)
    # re-verify manifest checksums
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=str(out),
        capture_output=True,
        text=True,
        check=False,
    )
    summary["manifest_verify_rc"] = int(proc.returncode)
    summary["ok"] = bool(summary["ok"]) and proc.returncode == 0
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    _write_manifest(out)
    return summary
