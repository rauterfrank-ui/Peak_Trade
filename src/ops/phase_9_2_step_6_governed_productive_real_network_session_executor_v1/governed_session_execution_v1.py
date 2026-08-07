"""Governed Step-6 productive real-network session executor (binding fail-closed).

This binding capability never starts a Public-MD network session and never
mints/consumes confirm tokens for side effects. It proves the productive
executor call graph and fail-closed gates required for a later separate
Owner-GO session on a real interactive TTY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.authorization_gate_v1 import (
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    LATER_SESSION_INVOCATION,
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_BINDING_ONLY,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTED,
    STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    assert_real_tty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.terminal_classification_v1 import (
    classify_terminal_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep6ProductiveExecutorResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_PROVE_BINDING_ONLY
    terminal_class: str = "HARD_STOP"
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    network_session_started: bool = False
    network_session_count: int = 0
    network_calls: int = 0
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
                "authorization_consumed": self.authorization_consumed,
                "confirm_token_consumed": self.confirm_token_consumed,
                "network_session_started": self.network_session_started,
                "network_session_count": self.network_session_count,
                "network_calls": self.network_calls,
                "evidence": dict(self.evidence),
                "capability_id": CAPABILITY_ID,
            }
        )


def evaluate_productive_session_gate_v1(
    *,
    mode: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    public_md_only: bool,
    authorization_valid: bool,
    confirm_token_valid: bool,
    stale_control_present: bool,
    stdin_isatty: bool | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_PRODUCTIVE_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if PREDECESSOR_NETWORK_SESSION_ALLOWED:
        blockers.append("PREDECESSOR_NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE")

    if mode == MODE_PROVE_BINDING_ONLY:
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_BINDING_ONLY,
            "network_session_may_start": False,
        }

    if mode != MODE_GOVERNED_REAL_NETWORK_SESSION:
        blockers.append("UNKNOWN_EXECUTION_MODE")
        return {"ok": False, "blockers": blockers, "mode": mode, "network_session_may_start": False}

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_EXPLICIT_REQUIRED")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_FALSE")
    if not public_md_only:
        blockers.append("PUBLIC_MD_ONLY_REQUIRED")
    if not authorization_valid:
        blockers.append("AUTHORIZATION_INVALID")
    if not confirm_token_valid:
        blockers.append("CONFIRM_TOKEN_INVALID")
    if not stale_control_present:
        blockers.append("STALE_CONTROL_ABSENT")
    blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_REAL_NETWORK_SESSION,
        # Binding capability never authorizes start even when gates structurally pass.
        "network_session_may_start": False,
        "notes": [
            "EPHEMERAL_GO_REQUIRED_FOR_FUTURE_SESSION=true",
            "BINDING_CAPABILITY_FORBIDS_NETWORK_START=true",
        ],
    }


def prove_step6_productive_executor_binding_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep6ProductiveExecutorResultV1:
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_BINDING=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_BINDING=true",
        "STEP5_PATTERN_REUSED=true",
        "NO_PARALLEL_SEMANTIC_MODEL=true",
        f"LATER_SESSION_INVOCATION={LATER_SESSION_INVOCATION}",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")
    if not expected_config_digest or len(str(expected_config_digest).strip()) < 7:
        blockers.append("CONFIG_DIGEST_INVALID")

    if NETWORK_SESSION_ALLOWED or PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")
    if PREDECESSOR_NETWORK_SESSION_ALLOWED:
        blockers.append("PREDECESSOR_MUST_NOT_FLIP_NETWORK_SESSION_ALLOWED")

    go = bind_ephemeral_network_session_go_v1(network_session_go=False, environ=environ)
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))
    if go.get("network_session_go"):
        blockers.append("DEFAULT_NETWORK_SESSION_GO_MUST_BE_FALSE")

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    stale = prove_adverse_stale_executor_binding_v1()
    if not stale.get("ok"):
        blockers.extend(list(stale.get("blockers") or []))

    entry = Path(PRODUCTIVE_ENTRYPOINT_PATH)
    if repo_root is not None:
        entry = Path(repo_root) / PRODUCTIVE_ENTRYPOINT_PATH
    if not entry.is_file() and repo_root is not None:
        # During development before CLI write, tolerate via package presence.
        blockers.append("PRODUCTIVE_ENTRYPOINT_MISSING")

    gate = evaluate_productive_session_gate_v1(
        mode=MODE_PROVE_BINDING_ONLY,
        owner_go=False,
        operator_authorization_explicit=False,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        stale_control_present=True,
        stdin_isatty=False,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    terminal = classify_terminal_v1(
        proposed_terminal="BINDING_PROOF",
        binding_only=True,
        blockers=blockers,
    )

    ok = not blockers and bool(stale.get("ok")) and bool(handoff.get("ok"))
    claims = {
        "PRODUCTIVE_EXECUTOR_BOUND": ok,
        "STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND": (
            STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND and ok
        ),
        "REAL_TTY_REQUIRED": True,
        "HIDDEN_CONFIRM_HANDOFF_BOUND": bool(handoff.get("ok")),
        "EXPLICIT_SESSION_OWNER_GO_REQUIRED": True,
        "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
        "PUBLIC_MD_ONLY_ENFORCED": bool(boundary.get("PUBLIC_MD_ONLY")),
        "ORDERS_DISABLED": True,
        "GOVERNED_STALE_CONTROL_BOUND": bool(stale.get("ok")),
        "FAILURE_INJECTION_BOUND": bool((stale.get("classification") or {}).get("ok")),
        "WALLCLOCK_OWNER_REUSED": bool((stale.get("wallclock_runner") or {}).get("ok")),
        "MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT,
        "NETWORK_CALLS_DURING_BINDING_CAPABILITY": 0,
        "NETWORK_SESSION_STARTED": False,
        "SESSION_EXECUTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "TARGET_SESSION_ID": TARGET_SESSION_ID,
        "PRIVATE_ENDPOINT_REACHABLE": bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        "CREDENTIAL_PATH_REACHABLE": bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        "PREDECESSOR_NETWORK_SESSION_ALLOWED_UNCHANGED": (
            PREDECESSOR_NETWORK_SESSION_ALLOWED is False
        ),
        "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION": ok,
        "CALL_GRAPH_BEFORE": list(CALL_GRAPH_BEFORE),
        "CALL_GRAPH_AFTER": list(CALL_GRAPH_AFTER),
    }
    return GovernedStep6ProductiveExecutorResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_BINDING_ONLY,
        terminal_class=str(terminal.get("terminal_class") or "BINDING_PROOF"),
        evidence={
            "hidden_pty_handoff": handoff,
            "boundary": boundary,
            "adverse_stale_executor": stale,
            "network_session_go": go,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
    )


def request_real_network_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_go: bool = False,
    stdin_isatty: bool | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep6ProductiveExecutorResultV1:
    proof = prove_step6_productive_executor_binding_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
        environ=environ,
    )
    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go, environ=environ
    )
    gate = evaluate_productive_session_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        stale_control_present=True,
        stdin_isatty=stdin_isatty,
    )
    blockers = (
        list(proof.blockers) + list(gate.get("blockers") or []) + list(go.get("blockers") or [])
    )
    blockers.extend(
        [
            "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY",
            "SEPARATE_OWNER_GO_REQUIRED_ON_REAL_TTY_AFTER_MERGE",
        ]
    )
    claims = dict(proof.claims)
    claims["NETWORK_SESSION_STARTED"] = False
    return GovernedStep6ProductiveExecutorResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=list(proof.notes) + ["REQUEST_REAL_NETWORK_OFFLINE_FAIL_CLOSED=true"],
        claims=claims,
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        terminal_class="HARD_STOP",
        evidence=proof.evidence,
    )


def execute_governed_step6_productive_session_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    authorization_id: str = "",
    authorization_digest: str = "",
    confirm_token_binding_sha256: str = "",
    getpass_fn: GetPassFn | None = None,
    confirm_token_plaintext: str | None = None,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_go: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    allow_real_network_side_effects: bool = False,
    enable_receive_lag: bool = False,
    stdin_isatty: bool | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> GovernedStep6ProductiveExecutorResultV1:
    """Fail-closed execute path for this binding — zero network calls."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "EXECUTE_GOVERNED_SESSION_BINDING_FAIL_CLOSED=true",
        "NO_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
        f"SESSION_EXECUTED_CONSTANT={SESSION_EXECUTED}",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    tty_blockers = assert_real_tty_v1(stdin_isatty=stdin_isatty)
    if tty_blockers:
        blockers.extend(tty_blockers)
        return GovernedStep6ProductiveExecutorResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["HARD_STOP_BEFORE_CONSUMPTION_NON_TTY=true"],
            claims={
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "NON_TTY_FAIL_CLOSED_PROVEN": True,
                "HARD_STOP": True,
                "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            },
            mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
            terminal_class="HARD_STOP",
        )

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go, environ=environ
    )
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))

    auth = validate_execution_authorization_artifact_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
    )
    if not auth.get("ok"):
        blockers.extend(list(auth.get("blockers") or []))

    token_plain = confirm_token_plaintext
    if token_plain is None:
        acquired = acquire_confirm_token_via_hidden_pty_v1(
            getpass_fn=getpass_fn,
            argv=argv,
            environ=environ,
            require_real_tty=True,
            stdin_isatty=stdin_isatty,
        )
        if not acquired.get("ok"):
            blockers.extend([str(b) for b in acquired.get("blockers") or []])
            token_plain = ""
        else:
            token_plain = str(acquired.get("plaintext") or "")

    token_check = validate_confirm_token_binding_v1(
        confirm_token_plaintext=str(token_plain or ""),
        expected_binding_sha256=confirm_token_binding_sha256,
        argv=argv,
        environ=environ,
    )
    if not token_check.get("ok"):
        blockers.extend([str(b) for b in token_check.get("blockers") or []])

    # Stale control must be present for Step-6 session semantics.
    from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (  # noqa: E501
        prepare_adverse_stale_runtime_overrides_v1,
    )

    stale_prep = prepare_adverse_stale_runtime_overrides_v1(
        enable_receive_lag=bool(enable_receive_lag and network_session_go and owner_go)
    )
    stale_present = bool(stale_prep.get("ok")) and (
        "governed_stale_data_control" in (stale_prep.get("runtime_overrides") or {})
    )
    if not stale_present:
        blockers.append("STALE_CONTROL_ABSENT")

    gate = evaluate_productive_session_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=True,
        authorization_valid=bool(auth.get("ok")),
        confirm_token_valid=bool(token_check.get("ok")),
        stale_control_present=stale_present,
        stdin_isatty=True if stdin_isatty is None else bool(stdin_isatty),
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    if allow_authorization_consumption or allow_confirm_token_consumption:
        blockers.append("CONSUMPTION_FORBIDDEN_IN_BINDING_CAPABILITY")
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_BINDING_CAPABILITY")
    if CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_CONSTANT_MUST_REMAIN_FALSE")

    blockers.append("REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY")

    return GovernedStep6ProductiveExecutorResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "SESSION_EXECUTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "HARD_STOP": True,
            "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            "STALE_CONTROL_PRESENT": stale_present,
            "MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT,
            "NETWORK_CALLS": 0,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        terminal_class="HARD_STOP",
        evidence={
            "token_check": {k: v for k, v in token_check.items() if k != "plaintext"},
            "authorization": auth,
            "network_session_go": go,
            "stale_prep": {
                "ok": stale_prep.get("ok"),
                "stale_control_enabled": stale_prep.get("stale_control_enabled"),
                "receive_lag_schedule": stale_prep.get("receive_lag_schedule"),
                "blockers": stale_prep.get("blockers"),
            },
        },
    )
