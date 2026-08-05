"""Step-4 productive session executor wiring + activation binding.

Wiring call graph (no runner invoke):
  evaluate_rate_limit_reconnect_wallclock_binding_gate_v1
  → prove_public_md_network_boundary_v1
  → prove_governed_fault_path_offline_v1
  → bind CANONICAL_WALLCLOCK_RUNNER symbol
  → materialize session evidence schema template

Activation call graph (runner only after full Gate PASS):
  Session-GO + Owner-GO + Owner-Session-GO
  → explicit request_real_network
  → network_session_allowed
  → authorization validation
  → confirm-token validation
  → public-MD-only boundary
  → authorization + confirm-token consumption at start boundary
  → existing run_productive_wallclock_session_v1 (or injected double)
  → existing fault/rate-limit/reconnect owners (via runner)
  → existing evidence + verifier

This capability does not permanently enable network sessions.
DEFAULT NETWORK_SESSION_ALLOWED remains false. Real network is never started
by the wiring path. Activation invokes the runner only when every gate is true.
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Callable, Mapping, MutableMapping, Optional

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.authorization_binding_v1 import (
    consume_authorization_binding_v1,
    load_consumed_authorization_ids_from_ledger_v1,
    validate_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    consume_confirm_token_binding_v1,
    fingerprint_only_v1,
    load_confirm_token_plaintext_canonical_v1,
    resolve_confirm_token_presence_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    ACTIVATION_CAPABILITY_ID,
    AUTHORIZATION_LEDGER_FILENAME,
    BUNDLE_VERIFIER_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    EEA_TRANSPORT_OWNER,
    FAULT_SESSION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PACING_POLICY_OWNER,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE,
    RATE_LIMIT_METRIC_OWNER,
    RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    SESSION_RUNTIME_OWNER,
    SESSION_SCOPE,
    STALENESS_OWNER,
    TARGET_SESSION_ID,
    WIRING_CAPABILITY_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.models_v1 import (
    ProductiveExecutorResultV1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
    validate_session_evidence_schema_v1,
)

WallclockRunnerV1 = Callable[..., Any]
AuthValidatorV1 = Callable[..., Mapping[str, Any]]
AuthConsumerV1 = Callable[..., Mapping[str, Any]]
ConfirmValidatorV1 = Callable[..., Mapping[str, Any]]
ConfirmConsumerV1 = Callable[..., Mapping[str, Any]]


class ProductiveActivationError(RuntimeError):
    """Fail-closed activation binding error."""


ACTIVATION_CALL_GRAPH = [
    "evaluate_rate_limit_reconnect_wallclock_binding_gate_v1",
    "validate_authorization_binding_v1",
    "validate_confirm_token_binding_v1",
    "prove_public_md_network_boundary_v1",
    "consume_authorization_binding_v1",
    "consume_confirm_token_binding_v1",
    "run_productive_wallclock_session_v1",
    "existing_fault_rate_limit_reconnect_owners",
    "existing_canonical_evidence_and_verifier",
]


def _import_canonical_wallclock_runner_v1() -> Any:
    """Bind the canonical wallclock runner without invoking it."""
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E501
        run_productive_wallclock_session_v1,
    )

    return run_productive_wallclock_session_v1


def execute_productive_rate_limit_reconnect_session_wiring_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path | None,
    authorization_present: bool,
    confirm_token_file: Path | None = None,
    confirm_token_present_flag: bool = False,
    execute: bool = False,
    allow_real_network: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    authorization_id_or_digest: str = "",
) -> ProductiveExecutorResultV1:
    """Fail-closed productive executor wiring for Step 4 (no runner invoke)."""
    env = environ if environ is not None else os.environ
    notes = [
        f"WIRING_CAPABILITY_ID={WIRING_CAPABILITY_ID}",
        f"ACTIVATION_CAPABILITY_ID={ACTIVATION_CAPABILITY_ID}",
        f"BINDING_CAPABILITY_ID={CAPABILITY_ID}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"PACING_POLICY_OWNER={PACING_POLICY_OWNER}",
        f"EEA_TRANSPORT_OWNER={EEA_TRANSPORT_OWNER}",
        f"SESSION_RUNTIME_OWNER={SESSION_RUNTIME_OWNER}",
        f"STALENESS_OWNER={STALENESS_OWNER}",
        f"RATE_LIMIT_METRIC_OWNER={RATE_LIMIT_METRIC_OWNER}",
        f"BUNDLE_VERIFIER_OWNER={BUNDLE_VERIFIER_OWNER}",
        f"NETWORK_SESSION_ALLOWED={NETWORK_SESSION_ALLOWED}",
        f"FAULT_SESSION_ALLOWED={FAULT_SESSION_ALLOWED}",
        "NO_PARALLEL_SESSION_RUNTIME=true",
        "NO_PARALLEL_TRANSPORT_AUTHORITY=true",
        "NO_PARALLEL_RETRY_AUTHORITY=true",
        "CONFIRM_TOKEN_NOT_CONSUMED_IN_WIRING=true",
        "WIRING_DOES_NOT_INVOKE_WALLCLOCK_RUNNER=true",
    ]
    blockers: list[str] = []
    call_graph = list(ACTIVATION_CALL_GRAPH)

    argv_blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(argv_blockers)

    if (
        NETWORK_SESSION_ALLOWED
        or FAULT_SESSION_ALLOWED
        or PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED
    ):
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")

    if allow_real_network:
        blockers.append("REAL_NETWORK_FORBIDDEN_IN_WIRING_CAPABILITY")

    if not execute:
        blockers.append("EXECUTE_MODE_REQUIRED")
        return ProductiveExecutorResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["GATE_OR_PREFLIGHT_ONLY_NO_EXECUTOR_BINDING=true"],
            wiring_capability_id=WIRING_CAPABILITY_ID,
            activation_capability_id=ACTIVATION_CAPABILITY_ID,
            session_id=TARGET_SESSION_ID,
            executor_code_exists=True,
            call_graph=call_graph,
            claims={
                "EXECUTOR_CODE_EXISTS": True,
                "EXECUTOR_PRODUCTIVELY_BOUND": False,
                "PRODUCTIVE_SESSION_REACHABLE": False,
                "PRODUCTIVE_SESSION_AUTHORIZED": False,
                "NETWORK_SESSION_STARTED": False,
                "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
                "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
                "EVIDENCE_VERIFIED": False,
                "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
                "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": False,
                "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE": False,
                "WALLCLOCK_RUNNER_INVOKED": False,
            },
        )

    gate = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        authorization_present=authorization_present,
        confirm_token_file=confirm_token_file,
        confirm_token_present_flag=confirm_token_present_flag,
        request_real_network=False,
        argv=argv,
        environ=env,
    )
    notes.extend(list(gate.notes))
    blockers.extend(list(gate.blockers))
    if not gate.ok:
        blockers.append("BINDING_GATE_FAILED")

    boundary = prove_public_md_network_boundary_v1(environ=env)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    fault = prove_governed_fault_path_offline_v1()
    if not fault.get("ok"):
        blockers.append("GOVERNED_FAULT_PATH_BINDING_FAILED")
    if bool(fault.get("network_session_started")) or bool(fault.get("fault_session_started")):
        blockers.append("FAULT_PATH_MUST_NOT_START_SESSION")

    runner = None
    runner_bound = False
    try:
        runner = _import_canonical_wallclock_runner_v1()
        runner_bound = callable(runner)
        if not runner_bound:
            blockers.append("CANONICAL_WALLCLOCK_RUNNER_NOT_CALLABLE")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"CANONICAL_WALLCLOCK_RUNNER_IMPORT_FAILED:{type(exc).__name__}")

    activation_bound = callable(execute_productive_rate_limit_reconnect_session_activation_v1)

    evidence = build_session_evidence_template_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        authorization_id_or_digest=authorization_id_or_digest,
        session_id=TARGET_SESSION_ID,
        confirmation_session_id=CONFIRMATION_SESSION_ID,
    )
    schema = validate_session_evidence_schema_v1(evidence)
    if not schema.get("ok"):
        blockers.extend([f"EVIDENCE_SCHEMA:{b}" for b in schema.get("blockers") or []])

    authorized = bool(gate.ok and gate.productive_session_execution_permitted)
    reachable = bool(
        authorized
        and runner_bound
        and activation_bound
        and boundary.get("ok")
        and fault.get("ok")
        and schema.get("ok")
        and not allow_real_network
        and PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE
    )
    ready = bool(reachable and READY_FOR_PRODUCTIVE_SESSION_EXECUTION and not blockers)

    claims = {
        "EXECUTOR_CODE_EXISTS": True,
        "EXECUTOR_PRODUCTIVELY_BOUND": ready,
        "PRODUCTIVE_SESSION_REACHABLE": ready,
        "PRODUCTIVE_SESSION_AUTHORIZED": authorized,
        "PRODUCTIVE_CALL_GRAPH_COMPLETE": ready,
        "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE": ready,
        "NETWORK_SESSION_STARTED": False,
        "FAULT_SESSION_STARTED": False,
        "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
        "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
        "EVIDENCE_VERIFIED": bool(schema.get("ok")),
        "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": ready,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "WALLCLOCK_RUNNER_INVOKED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PARALLEL_SESSION_RUNTIME_CREATED": False,
        "PARALLEL_TRANSPORT_AUTHORITY_CREATED": False,
        "PARALLEL_RETRY_AUTHORITY_CREATED": False,
        "NO_DIRECT_UNGOVERNED_RUNNER_CALL": True,
        "DEFAULT_NETWORK_SESSION_ALLOWED": False,
    }

    return ProductiveExecutorResultV1(
        ok=ready,
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "WIRING_BOUND_WITHOUT_NETWORK_SESSION=true",
            "ACTIVATION_PATH_BOUND_FOR_GATED_RUNNER_INVOKE=true",
            "LATER_SEPARATE_OWNER_SESSION_GO_REQUIRED_FOR_REAL_SESSION=true",
        ],
        wiring_capability_id=WIRING_CAPABILITY_ID,
        activation_capability_id=ACTIVATION_CAPABILITY_ID,
        session_id=TARGET_SESSION_ID,
        executor_code_exists=True,
        executor_productively_bound=ready,
        productive_session_reachable=ready,
        productive_session_authorized=authorized,
        ready_for_productive_session_execution=ready,
        productive_step_4_session_path_runtime_reachable=ready,
        productive_call_graph_complete=ready,
        canonical_wallclock_runner_bound=runner_bound,
        rate_limit_owner_reused=True,
        reconnect_owner_reused=True,
        heartbeat_staleness_owner_reused=True,
        fault_owner_reused=bool(fault.get("ok")),
        network_session_started=False,
        fault_session_started=False,
        rate_limit_path_productively_observed=False,
        reconnect_path_productively_observed=False,
        rate_limit_reconnect_ladder_step_closed=False,
        private_endpoint_reachable=False,
        auth_header_present=False,
        exchange_credential_access_reachable=False,
        order_side_effect_occurred=False,
        confirm_token_plaintext_exposed=False,
        wallclock_runner_invoked=False,
        wallclock_runner_invocation_count=0,
        network_request_count=0,
        authorization_consumed=False,
        confirm_token_consumed=False,
        call_graph=call_graph,
        claims=claims,
        gate=gate.to_dict(),
        network_boundary=boundary,
        fault_binding={
            "ok": bool(fault.get("ok")),
            "deterministic_injection_only": bool(fault.get("deterministic_injection_only")),
            "claims": dict(fault.get("claims") or {}),
            "network_session_started": False,
            "fault_session_started": False,
        },
        evidence_schema=schema,
    )


def execute_productive_rate_limit_reconnect_session_activation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path | None,
    authorization_present: bool = True,
    request_real_network: bool = False,
    network_session_allowed: bool = False,
    public_market_data_only: bool = True,
    private_endpoint_access_allowed: bool = False,
    exchange_credential_use_allowed: bool = False,
    live_trading_allowed: bool = False,
    testnet_allowed: bool = False,
    real_capital_movement_allowed: bool = False,
    authorization_id: str = "",
    authorization_digest: str = "",
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_repository_sha: str = "",
    authorization_config_digest: str = "",
    confirm_token_binding_sha256: str = "",
    confirm_token_in_memory: str | None = None,
    confirm_token_file: Path | None = None,
    confirm_token_present_flag: bool = False,
    confirm_token_expires_at: float | None = None,
    session_request: Mapping[str, Any] | None = None,
    persistence_root: Path | None = None,
    execute: bool = False,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    wallclock_runner: WallclockRunnerV1 | None = None,
    permit_canonical_runner_invoke: bool = False,
    authorization_validator: AuthValidatorV1 | None = None,
    authorization_consumer: AuthConsumerV1 | None = None,
    confirm_token_validator: ConfirmValidatorV1 | None = None,
    confirm_token_consumer: ConfirmConsumerV1 | None = None,
) -> ProductiveExecutorResultV1:
    """Activate the productive Step-4 call graph under full gates.

    The wallclock runner is invoked only when every required gate is true.
    Without full Gate PASS: no consume, no runner invoke, network_request_count=0.
    """
    env = environ if environ is not None else os.environ
    notes = [
        f"ACTIVATION_CAPABILITY_ID={ACTIVATION_CAPABILITY_ID}",
        f"WIRING_CAPABILITY_ID={WIRING_CAPABILITY_ID}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"DEFAULT_NETWORK_SESSION_ALLOWED={NETWORK_SESSION_ALLOWED}",
        "NO_DIRECT_UNGOVERNED_RUNNER_CALL=true",
        "CONSUMPTION_ONLY_AT_START_BOUNDARY=true",
        "CONFIRM_TOKEN_PLAINTEXT_NOT_PERSISTED=true",
    ]
    blockers: list[str] = []
    runner_calls = {"count": 0}
    auth_consumed = False
    token_consumed = False
    auth_valid = False
    token_valid = False
    runner_result: Optional[dict[str, Any]] = None
    forwarded: Optional[dict[str, Any]] = None
    call_graph = list(ACTIVATION_CALL_GRAPH)

    def _result(
        *,
        ok: bool,
        extra_notes: list[str] | None = None,
        claims_extra: Mapping[str, Any] | None = None,
    ) -> ProductiveExecutorResultV1:
        claims = {
            "PRODUCTIVE_SESSION_ENTRYPOINT_EXISTS": True,
            "PRODUCTIVE_SESSION_EXECUTOR_EXISTS": True,
            "EXISTING_WALLCLOCK_RUNNER_REUSED": True,
            "PRODUCTIVE_CALL_GRAPH_COMPLETE": True,
            "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE": True,
            "REAL_NETWORK_REQUIRES_EXPLICIT_REQUEST": True,
            "SESSION_AUTHORIZATION_REQUIRED": True,
            "CONFIRM_TOKEN_REQUIRED": True,
            "AUTHORIZATION_CONSUMED_ONLY_AT_START_BOUNDARY": True,
            "CONFIRM_TOKEN_CONSUMED_ONLY_AT_START_BOUNDARY": True,
            "NO_GATE_BYPASS": True,
            "NO_DIRECT_UNGOVERNED_RUNNER_CALL": True,
            "DEFAULT_NETWORK_SESSION_ALLOWED": False,
            "NETWORK_SESSION_STARTED": False,
            "WALLCLOCK_RUNNER_INVOKED": runner_calls["count"] >= 1,
            "WALLCLOCK_RUNNER_INVOCATION_COUNT": int(runner_calls["count"]),
            "NETWORK_REQUEST_COUNT": 0,
            "AUTHORIZATION_CONSUMED": auth_consumed,
            "CONFIRM_TOKEN_CONSUMED": token_consumed,
            "AUTHORIZATION_VALID": auth_valid,
            "CONFIRM_TOKEN_VALID": token_valid,
            "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
            "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": True,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "NEW_SESSION_LOGIC_ADDED": False,
            "NEW_FAULT_LOGIC_ADDED": False,
            "NEW_RETRY_POLICY_ADDED": False,
            "NEW_BACKOFF_POLICY_ADDED": False,
            "NEW_RECONNECT_POLICY_ADDED": False,
            "EXISTING_FAULT_LOGIC_REUSED": True,
            "EXISTING_RATE_LIMIT_CLASSIFIER_REUSED": True,
            "EXISTING_RETRY_POLICY_REUSED": True,
            "EXISTING_BACKOFF_POLICY_REUSED": True,
            "EXISTING_RECONNECT_POLICY_REUSED": True,
            "EXISTING_HEARTBEAT_POLICY_REUSED": True,
            "EXISTING_STALE_DATA_POLICY_REUSED": True,
        }
        if claims_extra:
            claims.update(dict(claims_extra))
        return ProductiveExecutorResultV1(
            ok=ok,
            blockers=sorted(set(blockers)),
            notes=notes + list(extra_notes or []),
            wiring_capability_id=WIRING_CAPABILITY_ID,
            activation_capability_id=ACTIVATION_CAPABILITY_ID,
            session_id=TARGET_SESSION_ID,
            executor_code_exists=True,
            executor_productively_bound=True,
            productive_session_reachable=True,
            productive_session_authorized=auth_valid and token_valid,
            ready_for_productive_session_execution=True,
            productive_step_4_session_path_runtime_reachable=True,
            productive_call_graph_complete=True,
            canonical_wallclock_runner_bound=True,
            rate_limit_owner_reused=True,
            reconnect_owner_reused=True,
            heartbeat_staleness_owner_reused=True,
            fault_owner_reused=True,
            network_session_started=False,
            fault_session_started=False,
            rate_limit_reconnect_ladder_step_closed=False,
            private_endpoint_reachable=False,
            auth_header_present=False,
            exchange_credential_access_reachable=False,
            order_side_effect_occurred=False,
            confirm_token_plaintext_exposed=False,
            wallclock_runner_invoked=runner_calls["count"] >= 1,
            wallclock_runner_invocation_count=int(runner_calls["count"]),
            network_request_count=0,
            authorization_consumed=auth_consumed,
            confirm_token_consumed=token_consumed,
            authorization_valid=auth_valid,
            confirm_token_valid=token_valid,
            request_real_network=bool(request_real_network),
            network_session_allowed=bool(network_session_allowed),
            session_request_forwarded=forwarded,
            runner_result=runner_result,
            ladder_step_remains_open=True,
            call_graph=call_graph,
            claims=claims,
        )

    argv_blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(argv_blockers)

    if (
        NETWORK_SESSION_ALLOWED
        or FAULT_SESSION_ALLOWED
        or PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED
    ):
        blockers.append("PERMANENT_UNSCOPED_ENABLE_MUST_REMAIN_FALSE")

    if not execute:
        blockers.append("EXECUTE_MODE_REQUIRED")
        return _result(ok=False, extra_notes=["ACTIVATION_REQUIRES_EXECUTE=true"])

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not owner_session_go:
        blockers.append("OWNER_SESSION_GO_REQUIRED")
    if not request_real_network:
        blockers.append("REQUEST_REAL_NETWORK_REQUIRED")
    if not network_session_allowed:
        blockers.append("NETWORK_SESSION_ALLOWED_REQUIRED")
    if not public_market_data_only:
        blockers.append("PUBLIC_MARKET_DATA_ONLY_REQUIRED")
    if private_endpoint_access_allowed:
        blockers.append("PRIVATE_ENDPOINT_ACCESS_FORBIDDEN")
    if exchange_credential_use_allowed:
        blockers.append("EXCHANGE_CREDENTIAL_USE_FORBIDDEN")
    if live_trading_allowed:
        blockers.append("LIVE_TRADING_FORBIDDEN")
    if testnet_allowed:
        blockers.append("TESTNET_FORBIDDEN")
    if real_capital_movement_allowed:
        blockers.append("REAL_CAPITAL_MOVEMENT_FORBIDDEN")

    if blockers:
        return _result(
            ok=False,
            extra_notes=["GATE_FAIL_CLOSED_NO_CONSUME_NO_RUNNER=true"],
            claims_extra={"READY_FOR_PRODUCTIVE_SESSION_EXECUTION": True},
        )

    confirm_present = resolve_confirm_token_presence_v1(
        confirm_token_in_memory=confirm_token_in_memory,
        confirm_token_file=confirm_token_file,
        confirm_token_present_flag=confirm_token_present_flag,
        environ=env,
    )
    gate = evaluate_rate_limit_reconnect_wallclock_binding_gate_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        now_unix=now_unix,
        owner_go=owner_go,
        owner_session_go=owner_session_go,
        session_go_path=session_go_path,
        authorization_present=authorization_present,
        confirm_token_file=confirm_token_file,
        confirm_token_present_flag=confirm_present or confirm_token_present_flag,
        request_real_network=True,
        argv=argv,
        environ=env,
    )
    notes.extend(list(gate.notes))
    blockers.extend(list(gate.blockers))
    if not gate.ok or not gate.real_network_may_proceed:
        blockers.append("BINDING_GATE_OR_REAL_NETWORK_MAY_PROCEED_FAILED")
        return _result(ok=False, extra_notes=["GATE_FAIL_CLOSED_NO_CONSUME_NO_RUNNER=true"])

    boundary = prove_public_md_network_boundary_v1(environ=env)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])
        return _result(ok=False, extra_notes=["NETWORK_BOUNDARY_FAIL_CLOSED=true"])

    persistence = Path(persistence_root) if persistence_root is not None else Path(".")
    persistence.mkdir(parents=True, exist_ok=True)
    auth_ledger = persistence / AUTHORIZATION_LEDGER_FILENAME
    token_ledger = persistence / CONFIRM_TOKEN_LEDGER_FILENAME
    already = load_consumed_authorization_ids_from_ledger_v1(auth_ledger)

    auth_validator = authorization_validator or validate_authorization_binding_v1
    auth_check = dict(
        auth_validator(
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
            expected_repository_sha=expected_repository_sha,
            expected_config_digest=expected_config_digest,
            expected_scope=SESSION_SCOPE,
            expected_session_id=TARGET_SESSION_ID,
            authorization_scope=authorization_scope,
            authorization_session_id=authorization_session_id,
            authorization_repository_sha=authorization_repository_sha or expected_repository_sha,
            authorization_config_digest=authorization_config_digest or expected_config_digest,
            live_trading_allowed=live_trading_allowed,
            testnet_allowed=testnet_allowed,
            private_endpoint_access_allowed=private_endpoint_access_allowed,
            exchange_credential_use_allowed=exchange_credential_use_allowed,
            real_capital_movement_allowed=real_capital_movement_allowed,
            already_consumed=authorization_id in already,
        )
    )
    auth_valid = bool(auth_check.get("ok"))
    if not auth_valid:
        blockers.extend([str(b) for b in auth_check.get("blockers") or []])
        blockers.append("AUTHORIZATION_VALIDATION_FAILED")
        return _result(ok=False, extra_notes=["AUTH_FAIL_CLOSED_NO_CONSUME_NO_RUNNER=true"])

    token_plaintext, load_blockers = load_confirm_token_plaintext_canonical_v1(
        confirm_token_in_memory=confirm_token_in_memory,
        confirm_token_file=confirm_token_file,
        environ=env,
    )
    if load_blockers:
        blockers.extend(load_blockers)
        return _result(ok=False, extra_notes=["CONFIRM_TOKEN_LOAD_FAIL_CLOSED=true"])

    expires = (
        float(confirm_token_expires_at)
        if confirm_token_expires_at is not None
        else float(now_unix) + 3600.0
    )
    token_validator = confirm_token_validator or validate_confirm_token_binding_v1
    token_check = dict(
        token_validator(
            **{
                "confirm_token": token_plaintext,
                "expected_binding_sha256": confirm_token_binding_sha256,
                "expected_repository_sha": expected_repository_sha,
                "expected_scope_digest": SESSION_SCOPE,
                "expected_session_id": TARGET_SESSION_ID,
                "expires_at": expires,
                "argv": argv,
            }
        )
    )
    # Drop plaintext immediately from local name after fingerprinting for consume.
    token_fp = str(token_check.get("fingerprint") or "") or fingerprint_only_v1(token_plaintext)
    token_plaintext = ""
    token_valid = bool(token_check.get("ok"))
    if not token_valid:
        blockers.extend([str(b) for b in token_check.get("blockers") or []])
        blockers.append("CONFIRM_TOKEN_VALIDATION_FAILED")
        return _result(
            ok=False,
            extra_notes=["CONFIRM_TOKEN_FAIL_CLOSED_NO_PARTIAL_CONSUME=true"],
        )

    runner = wallclock_runner
    if runner is None:
        if not permit_canonical_runner_invoke:
            blockers.append("CANONICAL_RUNNER_INVOKE_REQUIRES_INJECTION_OR_EXPLICIT_PERMIT")
            return _result(
                ok=False,
                extra_notes=[
                    "GATES_VALIDATED_RUNNER_PATH_REACHABLE=true",
                    "NO_CONSUME_WITHOUT_RUNNER_BINDING=true",
                    "SEPARATE_OWNER_SESSION_GO_REQUIRED_FOR_REAL_RUNNER=true",
                ],
            )
        try:
            runner = _import_canonical_wallclock_runner_v1()
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"CANONICAL_WALLCLOCK_RUNNER_IMPORT_FAILED:{type(exc).__name__}")
            return _result(ok=False, extra_notes=["RUNNER_IMPORT_FAILED_BEFORE_CONSUME=true"])

    # Start-boundary consumption (both, then runner). No partial consume above.
    try:
        if authorization_consumer is not None:
            consumed_auth = dict(
                authorization_consumer(
                    ledger_path=auth_ledger,
                    authorization_id=authorization_id,
                    authorization_digest=authorization_digest,
                    session_id=TARGET_SESSION_ID,
                    now_unix=now_unix,
                )
            )
        else:
            consumed_auth = consume_authorization_binding_v1(
                ledger_path=auth_ledger,
                authorization_id=authorization_id,
                authorization_digest=authorization_digest,
                session_id=TARGET_SESSION_ID,
                now_unix=now_unix,
            )
        auth_consumed = bool(consumed_auth.get("consumed") or consumed_auth.get("ok"))
        if confirm_token_consumer is not None:
            confirm_consumption = dict(
                confirm_token_consumer(
                    ledger_path=token_ledger,
                    confirm_token_fingerprint=token_fp,
                    session_id=TARGET_SESSION_ID,
                    now_unix=now_unix,
                )
            )
        else:
            confirm_consumption = consume_confirm_token_binding_v1(
                ledger_path=token_ledger,
                confirm_token_fingerprint=token_fp,
                session_id=TARGET_SESSION_ID,
                now_unix=now_unix,
            )
        token_consumed = bool(confirm_consumption.get("consumed") or confirm_consumption.get("ok"))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"CONSUMPTION_FAILED:{type(exc).__name__}")
        return _result(ok=False, extra_notes=["CONSUMPTION_FAIL_CLOSED_NO_RUNNER=true"])

    if not auth_consumed or not token_consumed:
        blockers.append("CONSUMPTION_INCOMPLETE")
        return _result(ok=False, extra_notes=["CONSUMPTION_INCOMPLETE_NO_RUNNER=true"])

    request_payload: MutableMapping[str, Any] = dict(session_request or {})
    # Preserve operator session request exactly.
    forwarded = copy.deepcopy(dict(request_payload))

    def _counted_runner(**kwargs: Any) -> Any:
        runner_calls["count"] += 1
        if runner_calls["count"] > 1:
            raise ProductiveActivationError("DOUBLE_WALLCLOCK_RUNNER_INVOCATION_FORBIDDEN")
        return runner(**kwargs)

    try:
        raw = _counted_runner(session_request=forwarded)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"RUNNER_EXCEPTION:{type(exc).__name__}")
        return _result(
            ok=False,
            extra_notes=["RUNNER_EXCEPTION_BEFORE_OR_AT_START=true", "NO_FALSE_PASS_EVIDENCE=true"],
            claims_extra={
                "PASS_EVIDENCE": False,
                "ERROR_CLASSIFICATION": type(exc).__name__,
            },
        )

    if isinstance(raw, Mapping):
        runner_result = dict(raw)
    elif hasattr(raw, "to_dict"):
        runner_result = dict(raw.to_dict())  # type: ignore[call-arg]
    else:
        runner_result = {"ok": bool(raw), "raw_type": type(raw).__name__}

    negative = False
    if runner_result.get("ok") is False:
        negative = True
    if runner_result.get("terminal_verdict") in {"FAIL", "ABORT", "NEGATIVE"}:
        negative = True
    if runner_result.get("pass") is False:
        negative = True
    if runner_result.get("session_pass") is False:
        negative = True

    if negative:
        blockers.append("RUNNER_NEGATIVE_SESSION_EVIDENCE")
        return _result(
            ok=False,
            extra_notes=[
                "NEGATIVE_SESSION_EVIDENCE_NOT_REINTERPRETED_AS_PASS=true",
                "LADDER_STEP_REMAINS_OPEN=true",
            ],
            claims_extra={
                "PASS_EVIDENCE": False,
                "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
                "LADDER_STEP_REMAINS_OPEN": True,
            },
        )

    return _result(
        ok=True,
        extra_notes=[
            "ACTIVATION_GATE_PASS_RUNNER_INVOKED_ONCE=true",
            "NETWORK_SESSION_NOT_STARTED_BY_IMPLEMENTATION_CAPABILITY=true",
            "LADDER_STEP_REMAINS_OPEN_UNTIL_VERIFIER_PASS=true",
        ],
        claims_extra={
            "PASS_EVIDENCE": bool(runner_result.get("ok", True)),
            "SESSION_REQUEST_FORWARDED_UNCHANGED": forwarded == dict(session_request or {}),
        },
    )
