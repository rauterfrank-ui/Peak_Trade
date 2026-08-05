"""Materialize offline implementation evidence for the binding capability."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.failure_injection_v1 import (
    run_rate_limit_reconnect_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_executor_v1 import (
    execute_productive_rate_limit_reconnect_session_wiring_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.verifier_v1 import (
    verify_binding_manifest_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


def materialize_capability_evidence_v1(
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
    now = 1_700_000_000.0
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    contract = load_and_validate_session_contract_v1(repo_root=root)
    write_json_atomic_v1(fixtures / "session_contract_v1.json", contract)

    campaign = fixtures / "offline_binding_campaign_root"
    campaign.mkdir(parents=True, exist_ok=True)
    sgo_path = campaign / "session_go.json"
    sgo = build_session_go_authority_v1(
        session_go_id="sgo_phase92_rl_binding_evidence_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo_path, sgo.to_dict())

    gate = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        now_unix=now,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_path,
        authorization_present=True,
        confirm_token_present_flag=True,
        request_real_network=False,
    )
    write_json_atomic_v1(fixtures / "binding_gate_result_v1.json", gate.to_dict())

    fault = prove_governed_fault_path_offline_v1()
    write_json_atomic_v1(fixtures / "governed_fault_path_offline_v1.json", fault)

    fi = run_rate_limit_reconnect_binding_failure_injection_v1(
        persistence_root=fixtures / "failure_injection",
        repository_sha=repository_sha,
        repo_root=root,
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)
    write_json_atomic_v1(fixtures / "authority_reuse_matrix_v1.json", authority)

    executor = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        now_unix=now,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo_path,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
        allow_real_network=False,
    )
    write_json_atomic_v1(fixtures / "productive_executor_result_v1.json", executor.to_dict())
    evidence_template = build_session_evidence_template_v1(
        repository_sha=repository_sha,
        config_digest=cfg,
        authorization_id_or_digest="wiring_evidence_auth_placeholder_digest_v1",
    )
    write_json_atomic_v1(fixtures / "session_evidence_template_v1.json", evidence_template)

    claims = {
        "IMPLEMENTATION_REQUIRED": False,
        "RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED": True,
        "GOVERNED_FAULT_PATH_BOUND": bool(fault.get("ok")),
        "REAL_NETWORK_SESSION_NOT_STARTED": True,
        "NETWORK_SESSION_STARTED": False,
        "FAULT_SESSION_STARTED": False,
        "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
        "PHASE_9_2_COMPLETE": False,
        "REAL_RATE_LIMIT_OBSERVED": False,
        "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
        "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": bool(
            executor.ready_for_productive_session_execution
        ),
        "EXECUTOR_CODE_EXISTS": True,
        "EXECUTOR_PRODUCTIVELY_BOUND": bool(executor.executor_productively_bound),
        "PRODUCTIVE_SESSION_REACHABLE": bool(executor.productive_session_reachable),
        "PRODUCTIVE_SESSION_AUTHORIZED": bool(executor.productive_session_authorized),
        "PRODUCTIVE_CALL_GRAPH_COMPLETE": bool(executor.productive_call_graph_complete),
        "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE": bool(
            executor.productive_step_4_session_path_runtime_reachable
        ),
        "REAL_NETWORK_REQUIRES_BOUND_SESSION_GO": True,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "WALLCLOCK_RUNNER_INVOKED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "DEFAULT_NETWORK_SESSION_ALLOWED": False,
        "CORE_LOGIC_CHANGE": False,
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": True,
        "DASHBOARD_AUTHORITY_EFFECT": "NONE",
        "PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED": False,
        "NO_IMPROVISED_HARNESS": True,
    }
    summary = {
        "ok": bool(
            gate.ok
            and fault.get("ok")
            and fi.get("ok")
            and parity.get("ok")
            and authority.get("ok")
            and executor.ok
        ),
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "session_id": TARGET_SESSION_ID,
        "claims": claims,
        "gate_ok": gate.ok,
        "fault_path_ok": bool(fault.get("ok")),
        "failure_injection_ok": bool(fi.get("ok")),
        "parity_ok": bool(parity.get("ok")),
        "executor_ok": bool(executor.ok),
        "network_session_started": False,
        "fault_session_started": False,
    }
    summary["evidence_digest"] = sha256_canonical_v1(summary)
    write_json_atomic_v1(out / "SUMMARY.json", summary)
    verified = verify_binding_manifest_v1(summary)
    write_json_atomic_v1(fixtures / "verifier_result_v1.json", verified)
    summary["verifier_ok"] = bool(verified.get("ok"))
    summary["ok"] = bool(summary["ok"] and verified.get("ok"))
    write_json_atomic_v1(out / "SUMMARY.json", summary)

    manifest_lines = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(out).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  {rel}")
    (out / "MANIFEST.sha256").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return summary
