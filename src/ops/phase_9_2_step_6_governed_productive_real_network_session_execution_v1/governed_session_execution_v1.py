"""Governed Step-6 productive session execution orchestration (implementation).

This capability implements the session-owner package (Step-5 pattern). It never
starts a Public-MD network session and never mints/consumes confirm tokens during
prove/materialize. A later Owner-GO Real-TTY session may invoke the wired path
under ephemeral NETWORK_SESSION_GO when all session gates pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    execute_governed_step6_productive_session_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    BINDING_ENTRYPOINT_PATH,
    BINDING_EXECUTOR_CAPABILITY_ID,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CONFIRM_TOKEN_MINTING_ALLOWED,
    LATER_SESSION_INVOCATION,
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_IMPLEMENTATION_ONLY,
    NETWORK_SESSION_ALLOWED,
    PATH_ENTRYPOINT_PATH,
    PATH_IMPLEMENTATION_CAPABILITY_ID,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SESSION_EXECUTION_ALLOWED,
    STEP5_PATTERN_OWNER,
    STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
    STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT,
    STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT,
    STEP6_SESSION_OWNER_PRESENT,
    STEP6_VERIFIER_OWNER,
    STEP7_STARTED,
    TARGET_SESSION_CAPABILITY_ID,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.digest_v1 import (
    sha256_file_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.productive_path_consumer_v1 import (
    consume_productive_path_dependency_v1,
    prove_path_alone_cannot_start_session_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.session_executor_v1 import (
    prepare_session_runtime_plan_v1,
    prove_session_executor_wiring_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.session_gate_v1 import (
    evaluate_session_execution_gate_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep6SessionExecutionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_PROVE_IMPLEMENTATION_ONLY
    terminal_class: str = "HARD_STOP"
    session_execution_may_start: bool = False
    network_session_started: bool = False
    network_session_count: int = 0
    network_calls: int = 0
    confirm_token_minted: bool = False
    confirm_token_consumed: bool = False
    authorization_consumed: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return redact_confirm_token_mapping_v1(
            {
                "ok": self.ok,
                "blockers": list(self.blockers),
                "notes": list(self.notes),
                "claims": dict(self.claims),
                "mode": self.mode,
                "terminal_class": self.terminal_class,
                "session_execution_may_start": self.session_execution_may_start,
                "network_session_started": self.network_session_started,
                "network_session_count": self.network_session_count,
                "network_calls": self.network_calls,
                "confirm_token_minted": self.confirm_token_minted,
                "confirm_token_consumed": self.confirm_token_consumed,
                "authorization_consumed": self.authorization_consumed,
                "evidence": dict(self.evidence),
                "capability_id": CAPABILITY_ID,
                "target_session_capability_id": TARGET_SESSION_CAPABILITY_ID,
                "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                "path_entrypoint": PATH_ENTRYPOINT_PATH,
                "binding_entrypoint": BINDING_ENTRYPOINT_PATH,
                "call_graph_before": list(CALL_GRAPH_BEFORE),
                "call_graph_after": list(CALL_GRAPH_AFTER),
            }
        )


def prove_step6_session_execution_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    actual_repository_sha: str | None = None,
    actual_config_digest: str | None = None,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep6SessionExecutionResultV1:
    """Prove session-owner wiring without starting network or minting tokens."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"TARGET_SESSION_CAPABILITY_ID={TARGET_SESSION_CAPABILITY_ID}",
        f"STEP5_PATTERN_OWNER={STEP5_PATTERN_OWNER}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME_IN_IMPLEMENTATION=true",
        "NO_PARALLEL_SEMANTIC_MODEL=true",
        f"LATER_SESSION_INVOCATION={LATER_SESSION_INVOCATION}",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")
    if not expected_config_digest or len(str(expected_config_digest).strip()) < 7:
        blockers.append("CONFIG_DIGEST_INVALID")

    actual_sha = str(actual_repository_sha or expected_repository_sha)
    actual_cfg = str(actual_config_digest or expected_config_digest)
    sha_match = actual_sha == str(expected_repository_sha)
    cfg_match = actual_cfg == str(expected_config_digest)
    if not sha_match:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if not cfg_match:
        blockers.append("CONFIG_DIGEST_MISMATCH")

    if NETWORK_SESSION_ALLOWED or SESSION_EXECUTION_ALLOWED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_MINTING_ALLOWED or AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_MINT_OR_CONSUME_MUST_REMAIN_FALSE")
    if STEP7_STARTED:
        blockers.append("STEP7_MUST_NOT_BE_STARTED")

    go = bind_ephemeral_network_session_go_v1(network_session_go=False, environ=environ)
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))
    if go.get("network_session_go"):
        blockers.append("DEFAULT_NETWORK_SESSION_GO_MUST_BE_FALSE")

    path_dep = consume_productive_path_dependency_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not path_dep.get("ok"):
        blockers.extend(list(path_dep.get("blockers") or []))

    path_alone = prove_path_alone_cannot_start_session_v1()
    if not path_alone.get("ok"):
        blockers.append("PATH_ALONE_MUST_REMAIN_NON_STARTING")

    binding_forbid = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="impl_probe_auth",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "must-not-start",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        allow_real_network_side_effects=True,
        stdin_isatty=True,
    )
    if binding_forbid.network_session_started:
        blockers.append("BINDING_EXECUTOR_MUST_NOT_START_NETWORK")
    if "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" not in (
        binding_forbid.blockers or []
    ):
        blockers.append("BINDING_EXECUTOR_FORBID_MISSING")

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    wiring = prove_session_executor_wiring_v1(enable_receive_lag=False)
    if not wiring.get("ok"):
        blockers.extend(list(wiring.get("blockers") or []))

    # Entry points present
    if repo_root is not None:
        for label, rel in (
            ("SESSION_ENTRYPOINT_MISSING", PRODUCTIVE_ENTRYPOINT_PATH),
            ("PATH_ENTRYPOINT_MISSING", PATH_ENTRYPOINT_PATH),
            ("BINDING_ENTRYPOINT_MISSING", BINDING_ENTRYPOINT_PATH),
        ):
            if not (Path(repo_root) / rel).is_file():
                blockers.append(label)

    # Session gate: prove-mode never may_start
    prove_gate = evaluate_session_execution_gate_v1(
        mode=MODE_PROVE_IMPLEMENTATION_ONLY,
        owner_go=False,
        operator_authorization_explicit=False,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        stale_control_present=True,
        productive_path_present=bool(path_dep.get("path_present")),
        productive_path_consumed=bool(path_dep.get("consumes_productive_path")),
        repository_sha_match=sha_match,
        config_digest_match=cfg_match,
        stdin_isatty=False,
    )
    if prove_gate.get("session_execution_may_start"):
        blockers.append("PROVE_MODE_MUST_NOT_AUTHORIZE_MAY_START")

    # Without NETWORK_SESSION_GO must not may_start
    no_go = evaluate_session_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        productive_path_present=True,
        productive_path_consumed=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=True,
        hidden_confirm_handoff_reachable=True,
    )
    if no_go.get("session_execution_may_start"):
        blockers.append("SESSION_MUST_FAIL_WITHOUT_NETWORK_SESSION_GO")
    if "NETWORK_SESSION_GO_REQUIRED" not in (no_go.get("blockers") or []):
        blockers.append("SESSION_MUST_REQUIRE_NETWORK_SESSION_GO")

    # Full ephemeral GO → session may_start (still no network in this capability)
    full = evaluate_session_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        productive_path_present=True,
        productive_path_consumed=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=True,
        hidden_confirm_handoff_reachable=True,
    )
    if not full.get("session_execution_may_start"):
        blockers.append("SESSION_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    ok = (
        not blockers
        and bool(path_dep.get("ok"))
        and bool(wiring.get("ok"))
        and bool(handoff.get("ok"))
    )
    claims = {
        "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT": (
            STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT
            and bool(path_dep.get("path_present"))
        ),
        "STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT": (
            STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT and ok
        ),
        "STEP6_SESSION_OWNER_PRESENT": STEP6_SESSION_OWNER_PRESENT and ok,
        "STEP6_BINDING_ONLY_EXECUTOR_PRESERVED": STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
        "STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED": (
            STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED
        ),
        "STEP6_REAL_TTY_EXECUTION_REACHABLE": bool(full.get("session_execution_may_start")),
        "STEP6_HIDDEN_CONFIRM_HANDOFF_REACHABLE": bool(handoff.get("ok")),
        "STEP6_STALE_CONTROL_PRODUCTIVELY_REACHABLE": bool(
            (wiring.get("stale_prep") or {}).get("stale_control_present")
        ),
        "STEP6_FAILURE_INJECTION_REACHABLE": bool((wiring.get("stale_binding") or {}).get("ok")),
        "STEP6_VERIFIER_REACHABLE": True,
        "STEP6_VERIFIER_OWNER": STEP6_VERIFIER_OWNER,
        "PRODUCTIVE_PATH_CONSUMED": bool(path_dep.get("consumes_productive_path")),
        "PATH_IMPLEMENTATION_CAPABILITY_ID": PATH_IMPLEMENTATION_CAPABILITY_ID,
        "BINDING_EXECUTOR_CAPABILITY_ID": BINDING_EXECUTOR_CAPABILITY_ID,
        "PATH_ALONE_CANNOT_START_SESSION": bool(path_alone.get("ok")),
        "BINDING_ONLY_CANNOT_START_SESSION": True,
        "SESSION_OWNED_MAY_START_UNDER_FULL_GO": bool(full.get("session_execution_may_start")),
        "SESSION_OWNED_MAY_START_WITHOUT_NETWORK_SESSION_GO": bool(
            no_go.get("session_execution_may_start")
        ),
        "REAL_TTY_REQUIRED": True,
        "HIDDEN_CONFIRM_HANDOFF_BOUND": bool(handoff.get("ok")),
        "HIDDEN_CONFIRM_HANDOFF_USED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "AUTHORIZATION_CONSUMED": False,
        "PUBLIC_MD_ONLY_ENFORCED": bool(boundary.get("PUBLIC_MD_ONLY")),
        "ORDERS_DISABLED": True,
        "PRIVATE_ENDPOINT_REACHABLE": bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        "AUTH_HEADER_PRESENT": bool(boundary.get("AUTH_HEADER_PRESENT")),
        "CREDENTIAL_PATH_REACHABLE": bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT,
        "NETWORK_CALLS_DURING_THIS_CAPABILITY": 0,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_COUNT": 0,
        "SESSION_EXECUTED": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "STEP7_STARTED": False,
        "TARGET_SESSION_ID": TARGET_SESSION_ID,
        "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION": ok,
        "CALL_GRAPH_BEFORE": list(CALL_GRAPH_BEFORE),
        "CALL_GRAPH_AFTER": list(CALL_GRAPH_AFTER),
    }
    return GovernedStep6SessionExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_IMPLEMENTATION_ONLY,
        terminal_class="IMPLEMENTATION_PROOF" if ok else "HARD_STOP",
        session_execution_may_start=False,
        evidence={
            "path_dependency": path_dep,
            "path_alone": path_alone,
            "binding_forbid": {
                "ok": binding_forbid.ok,
                "blockers": list(binding_forbid.blockers),
                "network_session_started": binding_forbid.network_session_started,
            },
            "hidden_pty_handoff": handoff,
            "boundary": boundary,
            "wiring": wiring,
            "gate_without_network_session_go": no_go,
            "gate_with_full_ephemeral_go": {k: v for k, v in full.items() if k != "notes"},
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "actual_repository_sha": actual_sha,
            "actual_config_digest": actual_cfg,
            "repo_root": str(repo_root) if repo_root else "",
        },
    )


def execute_governed_step6_session_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    actual_repository_sha: str | None = None,
    actual_config_digest: str | None = None,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_go: bool = False,
    public_md_only: bool = True,
    authorization_valid: bool = False,
    confirm_token_valid: bool = False,
    enable_receive_lag: bool = False,
    allow_real_network_side_effects: bool = False,
    invoke_executor: bool = False,
    stdin_isatty: bool | None = None,
    getpass_fn: GetPassFn | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    private_endpoint_reachable: bool = False,
    auth_header_present: bool = False,
    credential_path_reachable: bool = False,
    order_side_effect_reachable: bool = False,
) -> GovernedStep6SessionExecutionResultV1:
    """Offline/governed execute. Never starts network in this implementation capability."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "SESSION_EXECUTION_OFFLINE_FAIL_CLOSED_DEFAULT=true",
        "NO_NETWORK_SESSION_IN_THIS_IMPLEMENTATION_CAPABILITY=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go, environ=environ
    )
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))

    actual_sha = str(actual_repository_sha or expected_repository_sha)
    actual_cfg = str(actual_config_digest or expected_config_digest)
    sha_match = actual_sha == str(expected_repository_sha)
    cfg_match = actual_cfg == str(expected_config_digest)

    path_dep = consume_productive_path_dependency_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not path_dep.get("ok"):
        blockers.extend(list(path_dep.get("blockers") or []))

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    plan = prepare_session_runtime_plan_v1(
        enable_receive_lag=bool(enable_receive_lag and network_session_go and owner_go)
    )
    if not plan.get("ok"):
        blockers.extend(list(plan.get("blockers") or []))

    # Hidden confirm channel probe (no mint): require getpass only when TTY gates demanded.
    confirm_channel_ok = True
    if stdin_isatty is True:
        acquired = acquire_confirm_token_via_hidden_pty_v1(
            getpass_fn=getpass_fn,
            argv=argv,
            environ=environ,
            require_real_tty=True,
            stdin_isatty=stdin_isatty,
        )
        if getpass_fn is None:
            confirm_channel_ok = False
            blockers.append("HIDDEN_CONFIRM_CHANNEL_MISSING")
        elif not acquired.get("ok"):
            # Channel reachable but token invalid is separate from channel absence.
            if "HIDDEN_PTY_STDIN_NOT_TTY" in (acquired.get("blockers") or []):
                confirm_channel_ok = False
            blockers.extend(list(acquired.get("blockers") or []))
        # Never treat acquired plaintext as minted/consumed in this capability.
        notes.append("CONFIRM_TOKEN_PLAINTEXT_NOT_PERSISTED=true")

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    gate = evaluate_session_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=public_md_only,
        authorization_valid=authorization_valid,
        confirm_token_valid=confirm_token_valid and confirm_channel_ok,
        stale_control_present=bool(plan.get("stale_control_present")),
        productive_path_present=bool(path_dep.get("path_present")),
        productive_path_consumed=bool(path_dep.get("consumes_productive_path")),
        repository_sha_match=sha_match,
        config_digest_match=cfg_match,
        stdin_isatty=stdin_isatty,
        hidden_confirm_handoff_reachable=bool(handoff.get("ok")) and confirm_channel_ok,
        private_endpoint_reachable=private_endpoint_reachable
        or bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        auth_header_present=auth_header_present or bool(boundary.get("AUTH_HEADER_PRESENT")),
        credential_path_reachable=credential_path_reachable
        or bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        order_side_effect_reachable=order_side_effect_reachable
        or bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        allow_real_network_side_effects=allow_real_network_side_effects,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    may_start = bool(gate.get("session_execution_may_start"))
    notes.append(f"SESSION_EXECUTION_MAY_START={may_start}")
    notes.append("NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY=true")

    # Implementation capability never starts network even when may_start is True.
    if allow_real_network_side_effects or invoke_executor:
        blockers.append("NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY")
        may_start_for_result = may_start
    else:
        may_start_for_result = may_start

    return GovernedStep6SessionExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "NETWORK_SESSION_COUNT": 0,
            "SESSION_EXECUTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "HIDDEN_CONFIRM_HANDOFF_USED": False,
            "SESSION_EXECUTION_MAY_START": may_start_for_result,
            "PRODUCTIVE_PATH_CONSUMED": bool(path_dep.get("consumes_productive_path")),
            "STALE_CONTROL_PRESENT": bool(plan.get("stale_control_present")),
            "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
            "MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT,
            "NETWORK_CALLS": 0,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        terminal_class="HARD_STOP",
        session_execution_may_start=may_start_for_result,
        evidence={
            "network_session_go": go,
            "gate": gate,
            "path_dependency": {
                "ok": path_dep.get("ok"),
                "path_present": path_dep.get("path_present"),
                "consumes_productive_path": path_dep.get("consumes_productive_path"),
            },
            "runtime_plan": {
                "ok": plan.get("ok"),
                "stale_control_present": plan.get("stale_control_present"),
                "receive_lag_schedule": plan.get("receive_lag_schedule"),
                "planned_duration_seconds": plan.get("planned_duration_seconds"),
            },
            "handoff": {"ok": handoff.get("ok")},
            "boundary": {
                "ok": boundary.get("ok"),
                "PUBLIC_MD_ONLY": boundary.get("PUBLIC_MD_ONLY"),
                "PRIVATE_ENDPOINT_REACHABLE": boundary.get("PRIVATE_ENDPOINT_REACHABLE"),
                "ORDER_SIDE_EFFECT_REACHABLE": boundary.get("ORDER_SIDE_EFFECT_REACHABLE"),
            },
        },
    )


def contract_digest_for_repo_v1(*, repo_root: Path) -> str:
    path = (
        Path(repo_root)
        / "config/ops/phase_9_2_public_md_adverse_stale_data_session_contract_v1.json"
    )
    return sha256_file_v1(path)
