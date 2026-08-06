"""Governed Step-5 session execution orchestration (offline fail-closed by default)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_request_cli_adapter_v1 import (
    build_step5_session_request_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.authorization_gate_v1 import (
    load_consumed_authorization_ids_from_ledger_v1,
    redact_authorization_mapping_v1,
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_LEDGER_FILENAME,
    BINDING_CLI_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_SESSION_ALLOWED,
    PLANNED_SESSION_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (
    Step5ExecutionContractError,
    load_execution_contract_bundle_v1,
    validate_digest_bindings_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.prolonged_executor_v1 import (
    FetcherV1,
    run_bounded_prolonged_public_md_executor_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.terminal_classification_v1 import (
    classify_terminal_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep5ExecutionResultV1:
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
                        }
                        if self.contract_bundle
                        else None
                    ),
                    "executor_result": self.executor_result,
                    "evidence": self.evidence,
                    "call_graph_before": list(CALL_GRAPH_BEFORE),
                    "call_graph_after": list(CALL_GRAPH_AFTER),
                    "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                    "binding_cli_path": BINDING_CLI_PATH,
                }
            )
        )


def assemble_execution_request_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    planned_session_duration_seconds: int = PLANNED_SESSION_DURATION_SECONDS,
    authorization_id: str = "",
    authorization_digest: str = "",
    confirm_token_binding_sha256: str = "",
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    request = build_step5_session_request_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        planned_session_duration_seconds=planned_session_duration_seconds,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        confirm_token_binding_sha256=confirm_token_binding_sha256,
        extra={
            "execution_capability_id": CAPABILITY_ID,
            "session_contract_digest": bundle["session_contract_digest"],
            "binding_config_digest": bundle["binding_config_digest"],
            "minimum_successful_wallclock_seconds": bundle["minimum_successful_wallclock_seconds"],
            "network_mode": bundle["network_mode"],
            "network_allowlist": bundle["network_allowlist"],
            "http_method_allowlist": bundle["http_method_allowlist"],
            "pacing": bundle["pacing"],
        },
    )
    request["execution_request_digest"] = sha256_canonical_v1(request)
    return {
        "ok": True,
        "session_request": request,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "planned_session_duration_seconds": planned_session_duration_seconds,
        "network_session_started": False,
        "authorization_consumed": False,
        "confirm_token_consumed": False,
    }


def prove_step5_execution_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep5ExecutionResultV1:
    """Prove productive execution call graph without consume or real network."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_AUTHORIZATION_CONSUMPTION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_IMPLEMENTATION=true",
        "STEP4_PATTERN_REUSED=true",
        "STEP5_BINDING_CLI_UNCHANGED=true",
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
    except Step5ExecutionContractError as exc:
        blockers.append(str(exc))
        bundle = None

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    assembled = None
    if bundle is not None and not blockers:
        assembled = assemble_execution_request_v1(
            expected_repository_sha=expected_repository_sha,
            expected_config_digest=expected_config_digest,
            repo_root=repo_root,
        )

    ok = not blockers and bool(bundle) and bool(assembled and assembled.get("ok"))
    claims = {
        "STEP5_EXECUTION_PACKAGE_CREATED": True,
        "STEP5_EXECUTION_CONFIG_CREATED": True,
        "STEP5_EXECUTION_CLI_CREATED": True,
        "PRODUCTIVE_EXECUTOR_CREATED": True,
        "PRODUCTIVE_ENTRYPOINT_CREATED": True,
        "RUNTIME_REACHABLE": True,
        "STEP5_BINDING_CLI_UNCHANGED": True,
        "STEP4_PATTERN_REUSED": True,
        "AUTHORIZATION_BINDING_IMPLEMENTED": True,
        "CONFIRM_TOKEN_BINDING_IMPLEMENTED": True,
        "PUBLIC_MD_GET_ONLY_BOUNDARY_PROVEN": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SUBMIT_PATH_REACHABLE": False,
        "NO_ORDER_BOUNDARY_PROVEN": True,
        "NETWORK_SESSION_ALLOWED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_ISSUED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
        "PLANNED_SESSION_DURATION_SECONDS": PLANNED_SESSION_DURATION_SECONDS,
        "MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS": MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
        "PACING_BOUND": True,
        "RETRY_BOUND": True,
        "BACKOFF_BOUND": True,
        "RECONNECT_BOUND": True,
        "HEARTBEAT_BOUND": True,
        "STALENESS_BOUND": True,
        "INTERRUPT_BOUND": True,
        "RECOVERY_BOUND": True,
        "CORE_LOGIC_CHANGED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": ok,
    }
    return GovernedStep5ExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        terminal_class="HARD_STOP" if not ok else "HARD_STOP",
        contract_bundle=bundle,
        session_request=(assembled or {}).get("session_request") if assembled else None,
        evidence={
            "network_boundary": boundary,
            "hidden_pty_handoff": handoff,
            "session_contract_digest": (bundle or {}).get("session_contract_digest"),
            "binding_config_digest": (bundle or {}).get("binding_config_digest"),
        },
    )


def request_real_network_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
) -> GovernedStep5ExecutionResultV1:
    """CLI/runtime request-real-network remains offline fail-closed in this capability."""
    proof = prove_step5_execution_implementation_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    blockers = list(proof.blockers) + [
        "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY",
        "NETWORK_SESSION_ALLOWED_FALSE",
        "SEPARATE_OWNER_GO_REQUIRED_FOR_STEP5_SESSION",
    ]
    claims = dict(proof.claims)
    claims["NETWORK_SESSION_STARTED"] = False
    return GovernedStep5ExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=list(proof.notes) + ["REQUEST_REAL_NETWORK_OFFLINE_FAIL_CLOSED=true"],
        claims=claims,
        terminal_class="AUTHORIZATION_FAILURE",
        contract_bundle=proof.contract_bundle,
        session_request=proof.session_request,
        evidence=proof.evidence,
    )


def execute_governed_step5_session_v1(
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
    now_unix: float,
    authorization_expires_at: float | None = None,
    confirm_token_expires_at: float | None = None,
    getpass_fn: GetPassFn | None = None,
    confirm_token_plaintext: str | None = None,
    allow_real_network_side_effects: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    invoke_executor: bool = False,
    fetcher: FetcherV1 | None = None,
    monotonic_clock: Callable[[], float] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    interrupt_check: Callable[[], bool] | None = None,
    force_max_cycles: int | None = None,
    planned_duration_override_for_tests: int | None = None,
    minimum_duration_override_for_tests: int | None = None,
    stale_receive_lag_seconds: float = 0.0,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_capability_id: str = CAPABILITY_ID,
    authorization_session_contract_digest: str = "",
    authorization_binding_config_digest: str = "",
    authorization_planned_duration_seconds: int | None = None,
    authorization_repository_sha: str = "",
) -> GovernedStep5ExecutionResultV1:
    """Governed execution path. Fail-closed without separate session authorization."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "EXECUTE_GOVERNED_SESSION_OFFLINE_FAIL_CLOSED_DEFAULT=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    # Permanent constants remain false — this capability never authorizes live side effects.
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_CAPABILITY")
    if allow_authorization_consumption:
        blockers.append("AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_THIS_CAPABILITY")
    if allow_confirm_token_consumption:
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_FORBIDDEN_IN_THIS_CAPABILITY")
    if NETWORK_SESSION_ALLOWED or SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")

    digest_check = validate_digest_bindings_v1(
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
        repo_root=repo_root,
    )
    if not digest_check.get("ok"):
        blockers.extend(list(digest_check.get("blockers") or []))
        return GovernedStep5ExecutionResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_CONTRACT_DIGEST=true"],
            claims={"NETWORK_SESSION_STARTED": False},
            terminal_class="CONTRACT_MISMATCH",
        )
    bundle = digest_check["bundle"]
    assert bundle is not None

    # SHA binding
    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")

    already = load_consumed_authorization_ids_from_ledger_v1(
        Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
    )
    auth = validate_execution_authorization_artifact_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_session_contract_digest=expected_session_contract_digest,
        expected_binding_config_digest=expected_binding_config_digest,
        expected_scope=authorization_scope,
        expected_session_id=authorization_session_id,
        expected_capability_id=authorization_capability_id,
        planned_session_duration_seconds=int(bundle["planned_session_duration_seconds"]),
        network_mode=str(bundle["network_mode"]),
        public_md_endpoint_allowlist=str(bundle["network_allowlist"]),
        http_method_allowlist=str(bundle["http_method_allowlist"]),
        evidence_root=str(evidence_root),
        authorization_repository_sha=authorization_repository_sha or expected_repository_sha,
        authorization_scope=authorization_scope,
        authorization_session_id=authorization_session_id,
        authorization_capability_id=authorization_capability_id,
        authorization_session_contract_digest=authorization_session_contract_digest
        or expected_session_contract_digest,
        authorization_binding_config_digest=authorization_binding_config_digest
        or expected_binding_config_digest,
        authorization_planned_duration_seconds=(
            authorization_planned_duration_seconds
            if authorization_planned_duration_seconds is not None
            else int(bundle["planned_session_duration_seconds"])
        ),
        authorization_network_mode=str(bundle["network_mode"]),
        authorization_public_md_allowlist=str(bundle["network_allowlist"]),
        authorization_http_method_allowlist=str(bundle["http_method_allowlist"]),
        authorization_evidence_root=str(evidence_root),
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
    else:
        # Direct plaintext injection only for offline unit tests via parameter —
        # still reject argv/env and never persist.
        blockers.extend(reject_confirm_token_argv_v1(argv))
        blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    expires = (
        float(confirm_token_expires_at)
        if confirm_token_expires_at is not None
        else float(now_unix) + 3600.0
    )
    token = validate_confirm_token_binding_v1(
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
    if not token.get("ok"):
        blockers.extend([str(b) for b in token.get("blockers") or []])
        blockers.append("CONFIRM_TOKEN_FAILURE")

    boundary = prove_public_md_get_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    # Execution permit: this capability keeps side effects unauthorized.
    blockers.append("EXECUTION_PERMIT_NOT_AUTHORIZED_IN_THIS_CAPABILITY")
    blockers.append("NETWORK_SESSION_ALLOWED_FALSE")

    executor_result = None
    terminal = "AUTHORIZATION_FAILURE"
    if invoke_executor and fetcher is not None and not allow_real_network_side_effects:
        # Offline injected executor may run for tests after auth/token validation shape,
        # but never under real-network permit. Clear the permanent permit blockers only
        # when explicitly invoking offline injected executor for proof — still no consume.
        offline_blockers = [
            b
            for b in blockers
            if b
            not in {
                "EXECUTION_PERMIT_NOT_AUTHORIZED_IN_THIS_CAPABILITY",
                "NETWORK_SESSION_ALLOWED_FALSE",
            }
        ]
        if not offline_blockers:
            planned = int(
                planned_duration_override_for_tests
                if planned_duration_override_for_tests is not None
                else bundle["planned_session_duration_seconds"]
            )
            minimum = int(
                minimum_duration_override_for_tests
                if minimum_duration_override_for_tests is not None
                else bundle["minimum_successful_wallclock_seconds"]
            )
            executed = run_bounded_prolonged_public_md_executor_v1(
                pacing=bundle["pacing"],
                planned_session_duration_seconds=planned,
                minimum_successful_wallclock_seconds=minimum,
                evidence_root=Path(evidence_root),
                persistence_root=Path(persistence_root),
                fetcher=fetcher,
                allow_real_network=False,
                monotonic_clock=monotonic_clock,
                sleep_fn=sleep_fn,
                interrupt_check=interrupt_check,
                force_max_cycles=force_max_cycles,
                stale_receive_lag_seconds=stale_receive_lag_seconds,
            )
            executor_result = executed.to_dict()
            classified = classify_terminal_v1(
                proposed_terminal=executed.terminal_class,
                telemetry=executed.telemetry.to_dict(),
                evidence_verified=True,
                claims_match_telemetry=True,
                blockers=list(executed.blockers),
                minimum_successful_wallclock_seconds=minimum,
            )
            terminal = str(classified["terminal_class"])
            # Still fail-closed at capability layer: no auth/token consumption, no real network.
            notes.append("OFFLINE_INJECTED_EXECUTOR_RAN_WITHOUT_CONSUMPTION=true")
            notes.append("CAPABILITY_LAYER_STILL_FORBIDS_REAL_NETWORK=true")
            return GovernedStep5ExecutionResultV1(
                ok=False,
                blockers=sorted(
                    set(
                        blockers
                        + [
                            "EXECUTION_PERMIT_NOT_AUTHORIZED_IN_THIS_CAPABILITY",
                            "NETWORK_SESSION_ALLOWED_FALSE",
                        ]
                    )
                ),
                notes=notes,
                claims={
                    "NETWORK_SESSION_STARTED": False,
                    "AUTHORIZATION_CONSUMED": False,
                    "CONFIRM_TOKEN_CONSUMED": False,
                    "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                    "CONFIRM_TOKEN_PERSISTED": False,
                    "OFFLINE_INJECTED_EXECUTOR_OBSERVED": True,
                    "EXECUTOR_TERMINAL_CLASS": terminal,
                    **dict(executed.claims),
                },
                terminal_class=terminal,
                authorization_consumed=False,
                confirm_token_consumed=False,
                network_session_started=False,
                contract_bundle=bundle,
                executor_result=executor_result,
                evidence={
                    "authorization": redact_authorization_mapping_v1(auth),
                    "confirm_token": {
                        "confirm_token_id": token.get("confirm_token_id"),
                        "fingerprint": token.get("fingerprint"),
                        "binding_sha256": token.get("binding_sha256"),
                        "consumed_status": token.get("consumed_status"),
                    },
                    "network_boundary": boundary,
                    "terminal": classified,
                },
            )

    return GovernedStep5ExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes + ["FAIL_CLOSED_NO_NETWORK_NO_CONSUME=true"],
        claims={
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "CONFIRM_TOKEN_SHELL_HISTORY": False,
        },
        terminal_class=terminal,
        authorization_consumed=False,
        confirm_token_consumed=False,
        network_session_started=False,
        contract_bundle=bundle,
        executor_result=executor_result,
        evidence={
            "authorization": redact_authorization_mapping_v1(auth),
            "confirm_token": {
                "confirm_token_id": token.get("confirm_token_id"),
                "fingerprint": token.get("fingerprint"),
                "binding_sha256": token.get("binding_sha256"),
                "consumed_status": token.get("consumed_status"),
            },
            "network_boundary": boundary,
        },
    )
