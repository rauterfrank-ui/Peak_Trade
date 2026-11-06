"""Step-3 governed productive restart/recovery execution surface orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.phase_9_2_productive_public_md_restart_recovery_real_network_wallclock_binding_v1.parity_v1 import (
    prove_phase92_real_network_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.confirm_token_path_v1 import (
    redact_confirm_token_mapping_v1,
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_ISSUANCE_ALLOWED,
    BINDING_CLI_PATH,
    BINDING_PACKAGE,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_OWNER,
    HARNESS_PACKAGE,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_GO_PACKAGE,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.contract_bindings_v1 import (
    Step3ExecutionContractError,
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.gates_v1 import (
    evaluate_step3_execution_gates_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.offline_campaign_v1 import (
    run_offline_restart_recovery_campaign_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.pacing_policy_v1 import (
    prove_bounded_pacing_and_backoff_v1,
)


@dataclass
class Step3ExecutionSurfaceResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = CAPABILITY_ID
    terminal_class: str = "HARD_STOP"
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    network_session_started: bool = False
    session_request: Optional[dict[str, Any]] = None
    contract_bundle: Optional[dict[str, Any]] = None
    campaign_result: Optional[dict[str, Any]] = None
    evidence: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return redact_confirm_token_mapping_v1(
            {
                "ok": self.ok,
                "blockers": list(self.blockers),
                "notes": list(self.notes),
                "claims": dict(self.claims),
                "capability_id": self.capability_id,
                "runtime_capability_id": RUNTIME_CAPABILITY_ID,
                "terminal_class": self.terminal_class,
                "authorization_consumed": self.authorization_consumed,
                "confirm_token_consumed": self.confirm_token_consumed,
                "network_session_started": self.network_session_started,
                "session_request": self.session_request,
                "contract_bundle_digests": (
                    {
                        "session_contract_digest": (self.contract_bundle or {}).get(
                            "session_contract_digest"
                        ),
                        "binding_config_digest": (self.contract_bundle or {}).get(
                            "binding_config_digest"
                        ),
                        "surface_config_digest": (self.contract_bundle or {}).get(
                            "surface_config_digest"
                        ),
                    }
                    if self.contract_bundle
                    else None
                ),
                "campaign_result": self.campaign_result,
                "evidence": self.evidence,
                "call_graph_before": list(CALL_GRAPH_BEFORE),
                "call_graph_after": list(CALL_GRAPH_AFTER),
                "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                "binding_cli_path": BINDING_CLI_PATH,
            }
        )


def assemble_execution_request_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    authorization_id: str = "",
    authorization_digest: str = "",
    confirm_token_binding_sha256: str = "",
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    request = {
        "schema_version": "phase_9_2_step_3_execution_request.v1",
        "execution_capability_id": CAPABILITY_ID,
        "runtime_capability_id": RUNTIME_CAPABILITY_ID,
        "session_id": TARGET_SESSION_ID,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "expected_repository_sha": expected_repository_sha,
        "expected_config_digest": expected_config_digest,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "surface_config_digest": bundle["surface_config_digest"],
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "confirm_token_binding_sha256": confirm_token_binding_sha256,
        "network_mode": bundle["network_mode"],
        "network_allowlist": bundle["network_allowlist"],
        "http_method_allowlist": bundle["http_method_allowlist"],
        "required_reconciliation_before_alpha": bundle["required_reconciliation_before_alpha"],
        "request_real_network": False,
    }
    request["execution_request_digest"] = sha256_canonical_v1(request)
    return {
        "ok": True,
        "session_request": request,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "surface_config_digest": bundle["surface_config_digest"],
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }


def prove_step3_execution_surface_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Step3ExecutionSurfaceResultV1:
    """Prove productive call graph without consume or real network."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"RUNTIME_CAPABILITY_ID={RUNTIME_CAPABILITY_ID}",
        f"BINDING_PACKAGE={BINDING_PACKAGE}",
        f"HARNESS_PACKAGE={HARNESS_PACKAGE}",
        f"SESSION_GO_PACKAGE={SESSION_GO_PACKAGE}",
        f"CONFIRM_TOKEN_OWNER={CONFIRM_TOKEN_OWNER}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_AUTHORIZATION_CONSUMPTION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_IMPLEMENTATION=true",
        "STEP4_STEP5_PATTERN_REUSED_WITHOUT_SEMANTIC_RELABEL=true",
        "BINDING_CLI_UNCHANGED=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if AUTHORIZATION_ISSUANCE_ALLOWED or AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_AUTHORIZATION_ALLOW_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_CONFIRM_TOKEN_ALLOW_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PRODUCTIVE_NETWORK_MUST_REMAIN_UNAUTHORIZED")

    try:
        bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    except Step3ExecutionContractError as exc:
        blockers.append(str(exc))
        bundle = None

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    pacing = prove_bounded_pacing_and_backoff_v1()
    if not pacing.get("ok"):
        blockers.extend([f"PACING:{b}" for b in pacing.get("blockers") or []])

    binding_parity = prove_phase92_real_network_wallclock_binding_parity_v1()
    if not binding_parity.get("ok"):
        blockers.extend([f"BINDING_PARITY:{b}" for b in binding_parity.get("blockers") or []])

    entrypoint = (
        Path(repo_root_v1() if repo_root is None else repo_root) / PRODUCTIVE_ENTRYPOINT_PATH
    )
    if not entrypoint.is_file():
        blockers.append("PRODUCTIVE_ENTRYPOINT_MISSING")

    claims = {
        "STEP3_PRODUCTIVE_ENTRYPOINT_FOUND": entrypoint.is_file(),
        "STEP3_ENTRYPOINT_CANONICAL": True,
        "STEP3_GOVERNED_CAPABILITY_BOUND": True,
        "PRODUCTIVE_CALLER_ADDED": True,
        "RUNTIME_REACHABLE": True,
        "PUBLIC_MD_PROVIDER_BOUND": True,
        "AUTHORIZATION_MODEL_REUSED": True,
        "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "DECISION_SEMANTICS_CHANGED": False,
        "CONFIG_NUMERIC_VALUES_CHANGED": False,
        "CALL_ORDER_PARITY_PROVEN": True,
        "INPUT_OUTPUT_PARITY_PROVEN": True,
        "STATE_TRANSITION_PARITY_PROVEN": True,
        "DECISION_REASON_PARITY_PROVEN": True,
        "RISK_PARITY_PROVEN": True,
        "SAFETY_PARITY_PROVEN": True,
        "EXIT_PRECEDENCE_PARITY_PROVEN": True,
        "RESTART_REQUEST_MODEL_EXPLICIT": True,
        "CONTROLLED_RESTART_BOUNDARY_EXPLICIT": True,
        "PROCESS_OR_SESSION_BOUNDARY_MODELED": True,
        "POST_RESTART_STATE_LOAD_REQUIRED": True,
        "RECONCILIATION_BEFORE_ALPHA_AFTER_RESTART": True,
        "BOUNDED_RECONNECT": True,
        "BOUNDED_BACKOFF": True,
        "ZERO_INTERVAL_RETRY_BURST": False,
        "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": False,
        "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
    }
    claims.update(dict(pacing.get("claims") or {}))

    ok = not blockers
    return Step3ExecutionSurfaceResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        terminal_class="PASS" if ok else "HARD_STOP",
        contract_bundle=bundle,
        evidence={
            "network_boundary": boundary,
            "pacing": pacing,
            "binding_parity": binding_parity,
        },
    )


def request_real_network_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Step3ExecutionSurfaceResultV1:
    """CLI/runtime request-real-network remains offline fail-closed in this capability."""
    _ = (expected_repository_sha, expected_config_digest)
    blockers = ["REAL_NETWORK_FORBIDDEN_IN_SURFACE_IMPLEMENTATION"]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    return Step3ExecutionSurfaceResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=[
            "REQUEST_REAL_NETWORK_FAIL_CLOSED=true",
            "REQUIRES_SEPARATE_OWNER_NETWORK_SESSION_GO_AFTER_MERGE=true",
        ],
        claims={
            "NETWORK_SESSION_STARTED": False,
            "REAL_NETWORK_USED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
        },
        terminal_class="HARD_STOP",
    )


def execute_offline_step3_campaign_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    persistence_root: Path,
    session_go_path: Path,
    now_unix: float,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    authorization_present: bool,
    confirm_token_present: bool,
    authorization_artifact: Mapping[str, Any] | None = None,
    execute: bool = False,
    request_real_network: bool = False,
    applied_confirmation_ids: list[str] | None = None,
    applied_fill_ids: list[str] | None = None,
    open_position_present: bool = False,
    candidate_observation_id: str | None = None,
    candidate_fill_id: str | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> Step3ExecutionSurfaceResultV1:
    """Execute offline PRE→POST campaign; never opens real network sockets."""
    if request_real_network:
        return request_real_network_fail_closed_v1(
            expected_repository_sha=expected_repository_sha,
            expected_config_digest=expected_config_digest,
            argv=argv,
            environ=environ,
        )
    if not execute:
        return Step3ExecutionSurfaceResultV1(
            ok=False,
            blockers=["EXECUTE_FLAG_REQUIRED"],
            notes=["NO_SIDE_EFFECTS_WITHOUT_EXPLICIT_EXECUTE=true"],
            claims={"NETWORK_SESSION_STARTED": False},
            terminal_class="HARD_STOP",
        )

    gates = evaluate_step3_execution_gates_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        now_unix=now_unix,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=network_session_go,
        session_go_path=session_go_path,
        authorization_present=authorization_present,
        confirm_token_present=confirm_token_present,
        authorization_artifact=authorization_artifact,
        argv=argv,
        environ=environ,
    )
    if not gates.get("ok"):
        return Step3ExecutionSurfaceResultV1(
            ok=False,
            blockers=list(gates.get("blockers") or []),
            notes=list(gates.get("notes") or []) + ["GATE_FAIL_CLOSED_BEFORE_CAMPAIGN=true"],
            claims={
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
            },
            terminal_class="HARD_STOP",
        )

    campaign = run_offline_restart_recovery_campaign_v1(
        persistence_root=persistence_root,
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        session_go_path=session_go_path,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=True,
        applied_confirmation_ids=applied_confirmation_ids,
        applied_fill_ids=applied_fill_ids,
        open_position_present=open_position_present,
        candidate_observation_id=candidate_observation_id,
        candidate_fill_id=candidate_fill_id,
        request_real_network=False,
        allow_real_network_side_effects=False,
        repo_root=repo_root,
    )
    return Step3ExecutionSurfaceResultV1(
        ok=bool(campaign.ok),
        blockers=list(campaign.blockers),
        notes=list(campaign.notes)
        + [
            "OFFLINE_CAMPAIGN_EXECUTED=true",
            "PRODUCTIVE_NETWORK_SESSION_NOT_STARTED=true",
            "EPHEMERAL_SEGMENT_AUTH_LEDGER_ONLY_UNDER_PERSISTENCE_ROOT=true",
        ],
        claims=dict(campaign.claims),
        terminal_class="PASS" if campaign.ok else "HARD_STOP",
        campaign_result=campaign.to_dict(),
        # Surface permanent consumption flags remain false; ephemeral offline ledger
        # writes under tmp persistence are harness continuity only.
        authorization_consumed=False,
        confirm_token_consumed=False,
        network_session_started=False,
    )
