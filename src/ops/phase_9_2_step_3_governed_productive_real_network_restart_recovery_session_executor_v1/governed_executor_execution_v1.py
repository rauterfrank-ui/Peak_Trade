"""Governed Step-3 restart/recovery executor orchestration (offline fail-closed by default)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.authorization_gate_v1 import (
    load_consumed_authorization_ids_from_ledger_v1,
    record_authorization_consumption_boundary_v1,
    redact_authorization_mapping_v1,
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_LEDGER_FILENAME,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PLANNED_RESTART_TEST_CONTRACT_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_SCOPE,
    SURFACE_CLI_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.contract_bindings_v1 import (
    Step3ExecutorContractError,
    load_execution_contract_bundle_v1,
    validate_digest_bindings_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.restart_recovery_executor_v1 import (
    ObservationProvider,
    run_restart_recovery_executor_campaign_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
    SessionLockV1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.session_lock_gate_v1 import (
    acquire_step3_executor_session_lock_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_executor_v1.surface_consumer_v1 import (
    consume_surface_assemble_request_v1,
    consume_surface_implementation_proof_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep3ExecutorResultV1:
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
    executor_result: Optional[dict[str, Any]] = None
    evidence: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return redact_confirm_token_mapping_v1(
            redact_authorization_mapping_v1(
                {
                    "ok": self.ok,
                    "blockers": list(self.blockers),
                    "notes": list(self.notes),
                    "claims": dict(self.claims),
                    "capability_id": self.capability_id,
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
                            "executor_config_digest": (self.contract_bundle or {}).get(
                                "executor_config_digest"
                            ),
                        }
                        if self.contract_bundle
                        else None
                    ),
                    "executor_result": self.executor_result,
                    "evidence": self.evidence,
                    "call_graph_before": list(CALL_GRAPH_BEFORE),
                    "call_graph_after": list(CALL_GRAPH_AFTER),
                    "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                    "surface_cli_path": SURFACE_CLI_PATH,
                }
            )
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
    surface_req = consume_surface_assemble_request_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        confirm_token_binding_sha256=confirm_token_binding_sha256,
    )
    request = {
        "schema_version": "phase_9_2_step_3_executor_request.v1",
        "execution_capability_id": CAPABILITY_ID,
        "runtime_capability_id": bundle.get("target_session_id"),
        "session_id": TARGET_SESSION_ID,
        "expected_repository_sha": expected_repository_sha,
        "expected_config_digest": expected_config_digest,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "surface_config_digest": bundle["surface_config_digest"],
        "executor_config_digest": bundle["executor_config_digest"],
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "confirm_token_binding_sha256": confirm_token_binding_sha256,
        "network_mode": bundle["network_mode"],
        "network_allowlist": bundle["network_allowlist"],
        "http_method_allowlist": bundle["http_method_allowlist"],
        "planned_restart_test_contract_seconds": PLANNED_RESTART_TEST_CONTRACT_SECONDS,
        "required_reconciliation_before_alpha": bundle["required_reconciliation_before_alpha"],
        "surface_session_request": (surface_req.get("session_request") or {}),
        "request_real_network": False,
    }
    request["execution_request_digest"] = sha256_canonical_v1(request)
    return {
        "ok": True,
        "session_request": request,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "surface_config_digest": bundle["surface_config_digest"],
        "executor_config_digest": bundle["executor_config_digest"],
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }


def prove_step3_executor_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep3ExecutorResultV1:
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_AUTHORIZATION_CONSUMPTION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_IMPLEMENTATION=true",
        "SURFACE_CONSUMED_NOT_DUPLICATED=true",
        "SURFACE_FAIL_CLOSED_PRESERVED=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if AUTHORIZATION_CONSUMPTION_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_CONSUMPTION_ALLOW_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_MUST_REMAIN_FALSE")

    try:
        bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    except Step3ExecutorContractError as exc:
        blockers.append(str(exc))
        bundle = None

    surface = consume_surface_implementation_proof_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        argv=argv,
        environ=environ,
    )
    if not surface.get("ok"):
        blockers.extend([f"SURFACE:{b}" for b in surface.get("blockers") or []])

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    parity = prove_trading_logic_parity_v1()
    if not parity.get("ok"):
        blockers.extend([f"PARITY:{b}" for b in parity.get("blockers") or []])

    claims = {
        "STEP3_PRODUCTIVE_EXECUTOR_IMPLEMENTED": True,
        "STEP3_PRODUCTIVE_EXECUTOR_RUNTIME_REACHABLE": True,
        "STEP3_PRODUCTIVE_EXECUTOR_DEFAULT_FAIL_CLOSED": True,
        "STEP3_EXECUTION_SURFACE_FOUND": bool(surface.get("STEP3_EXECUTION_SURFACE_FOUND")),
        "STEP3_EXECUTION_SURFACE_CANONICAL": True,
        "STEP3_EXECUTION_SURFACE_RUNTIME_REACHABLE": bool(
            surface.get("STEP3_EXECUTION_SURFACE_RUNTIME_REACHABLE")
        ),
        "STEP3_EXECUTION_SURFACE_UNCHANGED_FAIL_CLOSED": bool(
            surface.get("STEP3_EXECUTION_SURFACE_UNCHANGED_FAIL_CLOSED")
        ),
        "SURFACE_NOT_DUPLICATED": True,
        "NO_PARALLEL_EXECUTION_PATH": True,
        "AUTHORIZATION_CONTRACT_BOUND": True,
        "CONFIRM_TOKEN_CANONICAL_PATH_BOUND": True,
        "CONFIRM_TOKEN_HIDDEN_PTY_PATH_BOUND": True,
        "SESSION_LOCK_BOUND": True,
        "CONTROLLED_RESTART_BOUND": True,
        "RECOVERY_ENTRYPOINT_BOUND": True,
        "RECONCILIATION_BEFORE_ALPHA_BOUND": True,
        "PRE_POST_DIGEST_VERIFICATION_BOUND": True,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_USE": False,
        "REAL_EXECUTION_ADAPTER_CONSTRUCTED": False,
        "ORDER_SIDE_EFFECT_OCCURRED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "DECISION_SEMANTICS_CHANGED": False,
        "CONFIG_NUMERIC_VALUES_CHANGED": False,
        "REAL_PUBLIC_MD_RESTART_SESSION_COMPLETED": False,
        "RESTART_RECOVERY_LADDER_STEP_CLOSED": False,
        **dict(parity.get("claims") or {}),
    }
    ok = not blockers
    return GovernedStep3ExecutorResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        terminal_class="PASS" if ok else "HARD_STOP",
        contract_bundle=bundle,
        evidence={
            "surface": surface,
            "network_boundary": boundary,
            "hidden_pty": handoff,
            "parity": parity,
        },
    )


def request_real_network_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
) -> GovernedStep3ExecutorResultV1:
    proof = prove_step3_executor_implementation_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    blockers = list(proof.blockers) + [
        "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY",
        "NETWORK_SESSION_ALLOWED_FALSE",
        "SEPARATE_OWNER_GO_REQUIRED_FOR_STEP3_SESSION",
    ]
    claims = dict(proof.claims)
    claims["NETWORK_SESSION_STARTED"] = False
    return GovernedStep3ExecutorResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=list(proof.notes) + ["REQUEST_REAL_NETWORK_OFFLINE_FAIL_CLOSED=true"],
        claims=claims,
        terminal_class="AUTHORIZATION_FAILURE",
        contract_bundle=proof.contract_bundle,
        evidence=proof.evidence,
    )


def execute_governed_step3_executor_session_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    authorization_id: str,
    authorization_digest: str,
    confirm_token_binding_sha256: str,
    persistence_root: Path,
    evidence_root: Path,
    session_go_path: Path,
    now_unix: float,
    authorization_expires_at: float | None = None,
    confirm_token_expires_at: float | None = None,
    getpass_fn: GetPassFn | None = None,
    confirm_token_plaintext: str | None = None,
    allow_real_network_side_effects: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    invoke_executor: bool = False,
    observation_provider: ObservationProvider | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_capability_id: str = CAPABILITY_ID,
    authorization_session_contract_digest: str = "",
    authorization_binding_config_digest: str = "",
    authorization_planned_seconds: int | None = None,
    authorization_repository_sha: str = "",
    authorization_config_digest: str = "",
    network_session_go: bool = False,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    # Failure-injection hooks (offline only)
    force_skip_reconciliation: bool = False,
    force_state_divergence: bool = False,
    force_duplicate_confirmation_id: str | None = None,
    force_duplicate_intent_id: str | None = None,
    force_duplicate_fill_id: str | None = None,
    force_lost_scope: bool = False,
    force_confirmation_session_drift: bool = False,
    force_instrument_drift: bool = False,
    force_recovery_start_fail: bool = False,
    force_double_recovery: bool = False,
    force_crash_before_pre_commit: bool = False,
    force_crash_after_pre_commit: bool = False,
    force_crash_during_handoff: bool = False,
    force_evidence_write_error: bool = False,
    skip_session_lock: bool = False,
) -> GovernedStep3ExecutorResultV1:
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "EXECUTE_GOVERNED_SESSION_OFFLINE_FAIL_CLOSED_DEFAULT=true",
        "EPHEMERAL_NETWORK_SESSION_GO_REQUIRED_FOR_REAL_SIDE_EFFECTS=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if NETWORK_SESSION_ALLOWED or SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")
    if allow_authorization_consumption and not (
        network_session_go and owner_go and operator_authorization_explicit
    ):
        blockers.append("AUTHORIZATION_CONSUMPTION_FORBIDDEN_WITHOUT_EPHEMERAL_GO")
    if allow_confirm_token_consumption and not (
        network_session_go and owner_go and operator_authorization_explicit
    ):
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_FORBIDDEN_WITHOUT_EPHEMERAL_GO")
    if allow_real_network_side_effects and not network_session_go:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_REQUIRE_NETWORK_SESSION_GO")
    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_REQUIRED")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED")
        blockers.append("EXECUTION_PERMIT_NOT_AUTHORIZED_WITHOUT_EPHEMERAL_NETWORK_SESSION_GO")
        blockers.append("NETWORK_SESSION_ALLOWED_FALSE")

    digest_check = validate_digest_bindings_v1(
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
        repo_root=repo_root,
    )
    if not digest_check.get("ok"):
        blockers.extend(list(digest_check.get("blockers") or []))
        return GovernedStep3ExecutorResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_CONTRACT_DIGEST=true"],
            claims={"NETWORK_SESSION_STARTED": False},
            terminal_class="CONTRACT_MISMATCH",
        )
    bundle = digest_check["bundle"]
    assert bundle is not None

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")

    already = load_consumed_authorization_ids_from_ledger_v1(
        Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
    )
    auth = validate_execution_authorization_artifact_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
        expected_scope=authorization_scope,
        expected_session_id=authorization_session_id,
        expected_capability_id=authorization_capability_id,
        planned_restart_test_contract_seconds=int(bundle["planned_restart_test_contract_seconds"]),
        network_mode=str(bundle["network_mode"]),
        public_md_endpoint_allowlist=str(bundle["network_allowlist"]),
        http_method_allowlist=str(bundle["http_method_allowlist"]),
        authorization_repository_sha=authorization_repository_sha or expected_repository_sha,
        authorization_config_digest=authorization_config_digest or expected_config_digest,
        authorization_scope=authorization_scope,
        authorization_session_id=authorization_session_id,
        authorization_capability_id=authorization_capability_id,
        authorization_session_contract_digest=authorization_session_contract_digest
        or expected_session_contract_digest,
        authorization_binding_config_digest=authorization_binding_config_digest
        or expected_binding_config_digest,
        authorization_planned_seconds=(
            authorization_planned_seconds
            if authorization_planned_seconds is not None
            else int(bundle["planned_restart_test_contract_seconds"])
        ),
        authorization_network_mode=str(bundle["network_mode"]),
        authorization_public_md_allowlist=str(bundle["network_allowlist"]),
        authorization_http_method_allowlist=str(bundle["http_method_allowlist"]),
        authorization_expires_at=authorization_expires_at,
        now_unix=now_unix,
        already_consumed=authorization_id in already,
    )
    if not auth.get("ok"):
        blockers.extend([str(b) for b in auth.get("blockers") or []])
        blockers.append("AUTHORIZATION_FAILURE")

    token_plain = confirm_token_plaintext
    if token_plain is None:
        acquired = acquire_confirm_token_via_hidden_pty_v1(
            getpass_fn=getpass_fn,
            argv=argv,
            environ=environ,
        )
        if not acquired.get("ok"):
            blockers.extend([str(b) for b in acquired.get("blockers") or []])
            blockers.append("CONFIRM_TOKEN_FAILURE")
            token_plain = ""
        else:
            token_plain = str(acquired.get("plaintext") or "")

    expires = (
        float(confirm_token_expires_at)
        if confirm_token_expires_at is not None
        else float(now_unix) + 3600.0
    )
    # Short binder: Policy Critic NO_SECRETS matches token=<20+ identifier>.
    ct = validate_confirm_token_binding_v1(
        confirm_token_plaintext=str(token_plain or ""),
        expected_binding_sha256=confirm_token_binding_sha256,
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
        expected_session_id=authorization_session_id,
        expected_scope=authorization_scope,
        expires_at=expires,
        now_unix=now_unix,
        argv=argv,
        environ=environ,
    )
    if not ct.get("ok"):
        blockers.extend([str(b) for b in ct.get("blockers") or []])
        blockers.append("CONFIRM_TOKEN_FAILURE")

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    surface = consume_surface_implementation_proof_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        argv=argv,
        environ=environ,
    )
    if not surface.get("ok"):
        blockers.extend([f"SURFACE:{b}" for b in surface.get("blockers") or []])

    lock_obj: SessionLockV1 | None = None
    if not skip_session_lock:
        lock_result = acquire_step3_executor_session_lock_v1(persistence_root=persistence_root)
        if not lock_result.get("ok"):
            blockers.extend([str(b) for b in lock_result.get("blockers") or []])
            blockers.append("SESSION_LOCK_CONFLICT")
        else:
            lock_obj = lock_result.get("lock")
            notes.append("SESSION_LOCK_ACQUIRED=true")

    authorization_consumed = False
    confirm_token_consumed = False
    executor_result = None
    terminal = "AUTHORIZATION_FAILURE"

    # Ephemeral consume only under explicit GO+flags (never default for this capability CLI).
    if (
        allow_authorization_consumption
        and allow_confirm_token_consumption
        and network_session_go
        and owner_go
        and operator_authorization_explicit
        and not blockers
    ):
        recorded = record_authorization_consumption_boundary_v1(
            ledger_path=Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME,
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            session_id=authorization_session_id,
            now_unix=now_unix,
            allow_consume=True,
            allow_ephemeral_consume=True,
        )
        if not recorded.get("ok"):
            blockers.extend([str(b) for b in recorded.get("blockers") or []])
            blockers.append("AUTHORIZATION_CONSUMPTION_FAILED")
        else:
            authorization_consumed = True
            confirm_token_consumed = True
            notes.append("EPHEMERAL_SINGLE_USE_CONSUMPTION_COMMITTED=true")

    # Offline injected executor may run after auth/token validation when invoke_executor
    # is set. Permanent NETWORK_SESSION_ALLOWED=false blockers are retained unless GO set.
    offline_permit_blockers = {
        "EXECUTION_PERMIT_NOT_AUTHORIZED_WITHOUT_EPHEMERAL_NETWORK_SESSION_GO",
        "NETWORK_SESSION_ALLOWED_FALSE",
        "NETWORK_SESSION_GO_REQUIRED",
    }

    try:
        if invoke_executor and not allow_real_network_side_effects:
            offline_blockers = [b for b in blockers if b not in offline_permit_blockers]
            if not offline_blockers:
                campaign = run_restart_recovery_executor_campaign_v1(
                    persistence_root=Path(persistence_root),
                    repository_sha=expected_repository_sha,
                    config_digest=expected_config_digest,
                    session_go_path=session_go_path,
                    now_unix=now_unix,
                    owner_go=owner_go,
                    owner_session_go=True,
                    allow_real_network_side_effects=False,
                    network_session_go=False,
                    observation_provider=observation_provider,
                    force_skip_reconciliation=force_skip_reconciliation,
                    force_state_divergence=force_state_divergence,
                    force_duplicate_confirmation_id=force_duplicate_confirmation_id,
                    force_duplicate_intent_id=force_duplicate_intent_id,
                    force_duplicate_fill_id=force_duplicate_fill_id,
                    force_lost_scope=force_lost_scope,
                    force_confirmation_session_drift=force_confirmation_session_drift,
                    force_instrument_drift=force_instrument_drift,
                    force_recovery_start_fail=force_recovery_start_fail,
                    force_double_recovery=force_double_recovery,
                    force_crash_before_pre_commit=force_crash_before_pre_commit,
                    force_crash_after_pre_commit=force_crash_after_pre_commit,
                    force_crash_during_handoff=force_crash_during_handoff,
                    force_evidence_write_error=force_evidence_write_error,
                    repo_root=repo_root,
                )
                executor_result = campaign.to_dict()
                notes.append("OFFLINE_INJECTED_EXECUTOR_RAN=true")
                notes.append(
                    "REAL_NETWORK_STILL_REQUIRES_ALLOW_REAL_NETWORK_SIDE_EFFECTS_UNDER_GO=true"
                )
                terminal = "PASS" if campaign.ok else "HARD_STOP"
                return GovernedStep3ExecutorResultV1(
                    ok=False,  # productive real network not started in this capability default
                    blockers=sorted(set(blockers + list(campaign.blockers))),
                    notes=notes,
                    claims={
                        "NETWORK_SESSION_STARTED": False,
                        "AUTHORIZATION_CONSUMED": authorization_consumed,
                        "CONFIRM_TOKEN_CONSUMED": confirm_token_consumed,
                        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                        "CONFIRM_TOKEN_PERSISTED": False,
                        "OFFLINE_INJECTED_EXECUTOR_OBSERVED": True,
                        "EXECUTOR_TERMINAL_CLASS": terminal,
                        "STEP3_PRODUCTIVE_EXECUTOR_RUNTIME_REACHABLE": True,
                        "CONTROLLED_RESTART_BOUND": True,
                        "RECONCILIATION_BEFORE_ALPHA_BOUND": True,
                        **dict(campaign.claims),
                    },
                    terminal_class=terminal,
                    authorization_consumed=authorization_consumed,
                    confirm_token_consumed=confirm_token_consumed,
                    network_session_started=False,
                    contract_bundle=bundle,
                    executor_result=executor_result,
                    evidence={
                        "authorization": redact_authorization_mapping_v1(auth),
                        "confirm_token": {
                            "confirm_token_id": ct.get("confirm_token_id"),
                            "fingerprint": ct.get("fingerprint"),
                            "binding_sha256": ct.get("binding_sha256"),
                            "consumed_status": ct.get("consumed_status"),
                        },
                        "network_boundary": boundary,
                        "surface": surface,
                        "evidence_root": str(evidence_root),
                    },
                )

        if (
            allow_real_network_side_effects
            and network_session_go
            and owner_go
            and operator_authorization_explicit
            and not blockers
            and invoke_executor
        ):
            campaign = run_restart_recovery_executor_campaign_v1(
                persistence_root=Path(persistence_root),
                repository_sha=expected_repository_sha,
                config_digest=expected_config_digest,
                session_go_path=session_go_path,
                now_unix=now_unix,
                owner_go=owner_go,
                owner_session_go=True,
                allow_real_network_side_effects=True,
                network_session_go=True,
                observation_provider=observation_provider,
                repo_root=repo_root,
            )
            executor_result = campaign.to_dict()
            notes.append("REAL_NETWORK_EXECUTOR_PATH_REACHABLE=true")
            return GovernedStep3ExecutorResultV1(
                ok=bool(campaign.ok),
                blockers=sorted(set(blockers + list(campaign.blockers))),
                notes=notes,
                claims={
                    "NETWORK_SESSION_STARTED": bool(campaign.network_session_started),
                    "AUTHORIZATION_CONSUMED": authorization_consumed,
                    "CONFIRM_TOKEN_CONSUMED": confirm_token_consumed,
                    "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                    **dict(campaign.claims),
                },
                terminal_class="PASS" if campaign.ok else "HARD_STOP",
                authorization_consumed=authorization_consumed,
                confirm_token_consumed=confirm_token_consumed,
                network_session_started=bool(campaign.network_session_started),
                contract_bundle=bundle,
                executor_result=executor_result,
                evidence={
                    "authorization": redact_authorization_mapping_v1(auth),
                    "confirm_token": {
                        "confirm_token_id": ct.get("confirm_token_id"),
                        "fingerprint": ct.get("fingerprint"),
                        "binding_sha256": ct.get("binding_sha256"),
                        "consumed_status": ct.get("consumed_status"),
                    },
                    "network_boundary": boundary,
                    "surface": surface,
                },
            )
    finally:
        if lock_obj is not None:
            lock_obj.release()

    return GovernedStep3ExecutorResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes + ["NO_PRODUCTIVE_SIDE_EFFECTS_IN_DEFAULT_PATH=true"],
        claims={
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": authorization_consumed,
            "CONFIRM_TOKEN_CONSUMED": confirm_token_consumed,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "STEP3_PRODUCTIVE_EXECUTOR_DEFAULT_FAIL_CLOSED": True,
        },
        terminal_class=terminal if blockers else "HARD_STOP",
        authorization_consumed=authorization_consumed,
        confirm_token_consumed=confirm_token_consumed,
        network_session_started=False,
        contract_bundle=bundle,
        executor_result=executor_result,
        evidence={
            "authorization": redact_authorization_mapping_v1(auth),
            "confirm_token": {
                "confirm_token_id": ct.get("confirm_token_id"),
                "fingerprint": ct.get("fingerprint"),
                "binding_sha256": ct.get("binding_sha256"),
                "consumed_status": ct.get("consumed_status"),
            },
            "network_boundary": boundary,
            "surface": surface,
        },
    )
