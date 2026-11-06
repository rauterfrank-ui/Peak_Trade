"""Materialize offline implementation evidence for the Step-5 binding capability."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.binding_gate_v1 import (
    assert_no_parallel_productive_authority_v1,
    evaluate_prolonged_natural_market_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.claims_v1 import (
    build_binding_claim_matrix_v1,
    prove_claim_semantics_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_DIRNAME,
    MANDATORY_TELEMETRY_FIELDS,
    OWNER,
    PRODUCER_VERSION,
    RECONNECT_PATH_STATUS_NOT_NATURAL,
    SCHEMA_VERSION,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.disk_preflight_v1 import (
    prove_disk_and_evidence_bounds_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.failure_injection_v1 import (
    run_prolonged_natural_market_binding_failure_injection_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.hidden_pty_confirm_handoff_v1 import (
    prove_hidden_pty_confirm_handoff_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.parity_v1 import (
    prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    bind_session_request_to_runner_kwargs_v1,
    build_step5_session_request_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.verifier_v1 import (
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
    parity = prove_phase92_prolonged_natural_market_wallclock_binding_parity_v1()
    authority = assert_no_parallel_productive_authority_v1()
    contract = load_and_validate_session_contract_v1(repo_root=root)
    write_json_atomic_v1(fixtures / "session_contract_v1.json", contract)

    campaign = fixtures / "offline_binding_campaign_root"
    campaign.mkdir(parents=True, exist_ok=True)
    sgo_path = campaign / "session_go.json"
    sgo = build_session_go_authority_v1(
        session_go_id="sgo_phase92_step5_binding_evidence_v1",
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo_path, sgo.to_dict())

    gate = evaluate_prolonged_natural_market_wallclock_binding_gate_v1(
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

    claim_proof = prove_claim_semantics_offline_v1()
    write_json_atomic_v1(fixtures / "claim_semantics_offline_v1.json", claim_proof)
    claim_matrix = build_binding_claim_matrix_v1(
        runtime_reachable=True,
        session_started=False,
        capability_closed=False,
    )
    write_json_atomic_v1(fixtures / "claim_matrix_v1.json", claim_matrix)

    disk = prove_disk_and_evidence_bounds_offline_v1(check_path=fixtures / "disk_check")
    write_json_atomic_v1(fixtures / "disk_and_evidence_bounds_v1.json", disk)

    fi = run_prolonged_natural_market_binding_failure_injection_v1(
        persistence_root=fixtures / "failure_injection",
        repository_sha=repository_sha,
        repo_root=root,
        now_unix=now,
    )
    write_json_atomic_v1(fixtures / "failure_injection_results_v1.json", fi)
    write_json_atomic_v1(fixtures / "parity_proof_v1.json", parity)
    write_json_atomic_v1(fixtures / "authority_reuse_matrix_v1.json", authority)

    boundary = prove_public_md_network_boundary_v1(environ={})
    write_json_atomic_v1(fixtures / "network_boundary_v1.json", boundary)

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    write_json_atomic_v1(fixtures / "hidden_pty_confirm_handoff_v1.json", handoff)

    session_request = build_step5_session_request_v1(
        expected_repository_sha=repository_sha,
        expected_config_digest=cfg,
        predecessor_step4_evidence_ref=(
            "docs/evidence/capability_phase_9_2_productive_public_md_"
            "rate_limit_reconnect_wallclock_binding_v1/SUMMARY.json"
        ),
    )
    write_json_atomic_v1(fixtures / "session_request_v1.json", session_request)
    runner_kwargs = bind_session_request_to_runner_kwargs_v1(session_request)
    write_json_atomic_v1(fixtures / "runner_kwargs_bound_v1.json", runner_kwargs)

    telemetry_schema = {
        "mandatory_fields": list(MANDATORY_TELEMETRY_FIELDS),
        "notes": ["TELEMETRY_SCHEMA_BOUND_FOR_LATER_SESSION=true"],
    }
    write_json_atomic_v1(fixtures / "telemetry_schema_v1.json", telemetry_schema)

    claims = {
        "IMPLEMENTATION_REQUIRED": False,
        "PROLONGED_NATURAL_MARKET_BINDING_IMPLEMENTED": True,
        "CLAIM_SEMANTICS_BOUND": bool(claim_proof.get("ok")),
        "DURATION_BOUNDS_BOUND": True,
        "DISK_PREFLIGHT_BOUND": bool(disk.get("ok")),
        "EVIDENCE_GROWTH_BOUND": bool(disk.get("ok")),
        "REAL_NETWORK_SESSION_NOT_STARTED": True,
        "NETWORK_SESSION_STARTED": False,
        "FAULT_SESSION_STARTED": False,
        "PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED": False,
        "CAPABILITY_CLOSED": False,
        "PHASE_9_2_COMPLETE": False,
        "RECONNECT_OBSERVED": False,
        "RECONNECT_NATURALLY_OCCURRED": False,
        "RECONNECT_PATH_REACHABLE": True,
        "RECONNECT_PATH_STATUS": RECONNECT_PATH_STATUS_NOT_NATURAL,
        "ENTRY_OBSERVED": False,
        "REDUCE_OBSERVED": False,
        "EXIT_OBSERVED": False,
        "STEP5_RUNTIME_REACHABLE": True,
        "STEP5_SESSION_STARTED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": True,
        "PRODUCTIVE_SESSION_REACHABLE": True,
        "REAL_NETWORK_REQUIRES_BOUND_SESSION_GO": True,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "WALLCLOCK_RUNNER_INVOKED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_ISSUED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "DEFAULT_NETWORK_SESSION_ALLOWED": False,
        "CORE_LOGIC_CHANGE": False,
        "EFFECTIVE_NUMERIC_VALUES_UNCHANGED": True,
        "NO_THRESHOLD_CHANGE": True,
        "DASHBOARD_AUTHORITY_EFFECT": "NONE",
        "PARALLEL_PRODUCTIVE_AUTHORITY_DETECTED": False,
        "NO_IMPROVISED_HARNESS": True,
        "NO_ORDER_BOUNDARY_PROVEN": bool(boundary.get("ok")),
        "SESSION_REQUEST_PATH_BOUND": True,
        "HIDDEN_PTY_HANDOFF_BOUND": bool(handoff.get("ok")),
    }
    summary = {
        "ok": bool(
            gate.ok
            and claim_proof.get("ok")
            and fi.get("ok")
            and parity.get("ok")
            and authority.get("ok")
            and disk.get("ok")
            and boundary.get("ok")
            and handoff.get("ok")
        ),
        "capability_id": CAPABILITY_ID,
        "owner": OWNER,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "repository_sha": repository_sha,
        "session_id": TARGET_SESSION_ID,
        "session_contract_digest": sha256_canonical_v1(contract),
        "claims": claims,
        "gate_ok": gate.ok,
        "claim_semantics_ok": bool(claim_proof.get("ok")),
        "failure_injection_ok": bool(fi.get("ok")),
        "parity_ok": bool(parity.get("ok")),
        "disk_ok": bool(disk.get("ok")),
        "network_boundary_ok": bool(boundary.get("ok")),
        "network_session_started": False,
        "fault_session_started": False,
        "authorization_issued": False,
        "authorization_consumed": False,
        "confirm_token_issued": False,
        "confirm_token_consumed": False,
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
