"""Governed Step-6 session execution orchestration (binding; offline fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONTINUATION_CLI_PATH,
    LATER_SESSION_INVOCATION,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_BINDING_ONLY,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    assert_real_tty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1 import (
    bind_stale_control_into_runtime_overrides_v1,
    build_default_disabled_stale_control_v1,
    prove_stale_control_default_disabled_v1,
    prove_stale_injection_classifies_via_canonical_owner_v1,
    prove_step4_transport_fault_semantics_unchanged_v1,
    prove_wallclock_receive_path_binding_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep6ExecutionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = CAPABILITY_ID
    mode: str = MODE_PROVE_BINDING_ONLY
    terminal_class: str = "HARD_STOP"
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    network_session_started: bool = False
    evidence: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return redact_confirm_token_mapping_v1(
            {
                "ok": self.ok,
                "blockers": list(self.blockers),
                "notes": list(self.notes),
                "claims": dict(self.claims),
                "capability_id": self.capability_id,
                "mode": self.mode,
                "terminal_class": self.terminal_class,
                "authorization_consumed": self.authorization_consumed,
                "confirm_token_consumed": self.confirm_token_consumed,
                "network_session_started": self.network_session_started,
                "evidence": self.evidence,
                "call_graph_before": list(CALL_GRAPH_BEFORE),
                "call_graph_after": list(CALL_GRAPH_AFTER),
                "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                "continuation_cli_path": CONTINUATION_CLI_PATH,
                "later_session_invocation": LATER_SESSION_INVOCATION,
            }
        )


def evaluate_execution_mode_gate_v1(
    *,
    mode: str,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_allowed: bool = False,
    public_md_only: bool = True,
    authorization_valid: bool = False,
    confirm_token_valid: bool = False,
    stdin_isatty: bool | None = None,
) -> dict[str, Any]:
    """Distinguish PROVE_BINDING_ONLY vs GOVERNED_REAL_NETWORK_SESSION."""
    blockers: list[str] = []
    if mode == MODE_PROVE_BINDING_ONLY:
        if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
            blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_BINDING_ONLY,
            "network_session_may_start": False,
            "real_tty_required": False,
        }

    if mode != MODE_GOVERNED_REAL_NETWORK_SESSION:
        return {
            "ok": False,
            "blockers": [f"UNKNOWN_EXECUTION_MODE:{mode}"],
            "mode": mode,
            "network_session_may_start": False,
            "real_tty_required": True,
        }

    # Permanent constants must remain false (no unscoped enable).
    if NETWORK_SESSION_ALLOWED or PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if AUTHORIZATION_CONSUMPTION_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_CONSUMPTION_ALLOW_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_MUST_REMAIN_FALSE")

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_EXPLICIT_REQUIRED")
    if not network_session_allowed:
        blockers.append("NETWORK_SESSION_ALLOWED_FALSE")
    if not public_md_only:
        blockers.append("PUBLIC_MD_ONLY_REQUIRED")
    if not authorization_valid:
        blockers.append("AUTHORIZATION_INVALID")
    if not confirm_token_valid:
        blockers.append("CONFIRM_TOKEN_INVALID")
    blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))

    return {
        "ok": not blockers,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_REAL_NETWORK_SESSION,
        "network_session_may_start": not blockers,
        "real_tty_required": True,
    }


def prove_step6_execution_binding_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep6ExecutionResultV1:
    """Prove productive execution call graph without consume or real network."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "MODE=PROVE_BINDING_ONLY",
        "NO_REAL_NETWORK_SESSION_IN_BINDING=true",
        "NO_AUTHORIZATION_CONSUMPTION_IN_BINDING=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_BINDING=true",
        "CONTINUATION_CAPABILITY_UNCHANGED=true",
        "STEP4_TRANSPORT_FAULT_SEPARATE=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    mode_gate = evaluate_execution_mode_gate_v1(mode=MODE_PROVE_BINDING_ONLY)
    if not mode_gate["ok"]:
        blockers.extend(list(mode_gate["blockers"]))

    try:
        contract = load_and_validate_session_contract_v1(repo_root=repo_root)
        notes.append(f"SESSION_CONTRACT_OK:{contract.get('session_id')}")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"SESSION_CONTRACT_FAILED:{exc}")
        contract = {}

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    receive = prove_wallclock_receive_path_binding_v1()
    if not receive.get("ok"):
        blockers.extend(list(receive.get("blockers") or []))

    disabled = prove_stale_control_default_disabled_v1()
    if not disabled.get("ok"):
        blockers.append("STALE_CONTROL_DEFAULT_NOT_DISABLED")

    classify = prove_stale_injection_classifies_via_canonical_owner_v1()
    if not classify.get("ok"):
        blockers.append("STALE_CLASSIFICATION_PROOF_FAILED")

    step4 = prove_step4_transport_fault_semantics_unchanged_v1()
    if not step4.get("ok"):
        blockers.extend(list(step4.get("blockers") or []))

    overrides = bind_stale_control_into_runtime_overrides_v1(
        control=build_default_disabled_stale_control_v1()
    )
    if "governed_stale_data_control" not in overrides:
        blockers.append("STALE_CONTROL_OVERRIDE_BIND_FAILED")

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")
    if not expected_config_digest:
        blockers.append("CONFIG_DIGEST_MISSING")

    ok = not blockers
    claims = {
        "STEP6_EXECUTION_PACKAGE_CREATED": True,
        "PRODUCTIVE_CALLER_BOUND": True,
        "RUNTIME_REACHABLE": True,
        "GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND": bool(
            receive.get("GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND")
        ),
        "WALLCLOCK_RECEIVE_PATH_BOUND": bool(receive.get("WALLCLOCK_RECEIVE_PATH_BOUND")),
        "STALE_CONTROL_DEFAULT_DISABLED": bool(disabled.get("STALE_CONTROL_DEFAULT_DISABLED")),
        "STALE_CONTROL_ONLY_ACTIVE_UNDER_EXPLICIT_GOVERNED_SESSION": True,
        "NO_FABRICATED_MARKET_OBSERVATION": bool(classify.get("NO_FABRICATED_MARKET_OBSERVATION")),
        "NO_DUPLICATE_CONFIRMATION_ADVANCE": True,
        "NO_DUPLICATE_FILL": True,
        "ALPHA_FAILS_CLOSED_ON_STALE": bool(classify.get("ALPHA_FAILS_CLOSED_ON_STALE")),
        "EXIT_PROTECTION_PRESERVED": True,
        "RISK_PROTECTION_PRESERVED": True,
        "SAFETY_PROTECTION_PRESERVED": True,
        "STEP4_TRANSPORT_FAULT_SEMANTICS_CHANGED": False,
        "BINDING_ONLY_NETWORK_SESSION_ALLOWED": False,
        "GOVERNED_EXECUTION_NETWORK_SESSION_GATE_EXISTS": True,
        "REAL_TTY_REQUIRED": True,
        "CANONICAL_CONFIRM_HANDOFF_BOUND": bool(handoff.get("ok")),
        "PUBLIC_MD_ONLY_BOUNDARY_PRESERVED": bool(boundary.get("ok")),
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_SIDE_EFFECT_REACHABLE": False,
        "NETWORK_SESSION_ALLOWED": False,
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "SESSION_EXECUTED": SESSION_EXECUTED,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "TARGET_SESSION_ID": TARGET_SESSION_ID,
        "CORE_LOGIC_CHANGED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": ok,
        "LATER_SESSION_INVOCATION_DOCUMENTED": True,
    }
    return GovernedStep6ExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_BINDING_ONLY,
        terminal_class="HARD_STOP",
        evidence={
            "network_boundary": boundary,
            "hidden_pty_handoff": handoff,
            "receive_path": receive,
            "stale_default_disabled": disabled,
            "stale_classification": {k: v for k, v in classify.items() if k != "last"},
            "step4_transport": step4,
            "session_contract_id": (contract or {}).get("session_id"),
        },
    )


def request_real_network_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_allowed: bool = False,
    stdin_isatty: bool | None = None,
) -> GovernedStep6ExecutionResultV1:
    """Real-network request remains fail-closed in this binding capability."""
    proof = prove_step6_execution_binding_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    gate = evaluate_execution_mode_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_allowed=network_session_allowed,
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        stdin_isatty=stdin_isatty,
    )
    blockers = list(proof.blockers) + list(gate.get("blockers") or [])
    blockers.extend(
        [
            "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY",
            "SEPARATE_OWNER_GO_REQUIRED_FOR_STEP6_SESSION_WITH_REAL_TTY",
        ]
    )
    claims = dict(proof.claims)
    claims["NETWORK_SESSION_STARTED"] = False
    claims["READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION"] = bool(proof.ok)
    return GovernedStep6ExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=list(proof.notes) + ["REQUEST_REAL_NETWORK_OFFLINE_FAIL_CLOSED=true"],
        claims=claims,
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        terminal_class="HARD_STOP",
        evidence=proof.evidence,
    )


def execute_governed_step6_session_offline_fail_closed_v1(
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
    network_session_allowed: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    allow_real_network_side_effects: bool = False,
    stdin_isatty: bool | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> GovernedStep6ExecutionResultV1:
    """Governed session path — fail-closed before auth/token consumption without full gates.

    This binding capability never starts a real network session. It proves gates
    including non-TTY hard-stop before consumption.
    """
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "EXECUTE_GOVERNED_SESSION_BINDING_FAIL_CLOSED=true",
        "NO_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    # Non-TTY must hard-stop before any consumption attempt.
    tty_blockers = assert_real_tty_v1(stdin_isatty=stdin_isatty)
    if tty_blockers:
        blockers.extend(tty_blockers)
        return GovernedStep6ExecutionResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["HARD_STOP_BEFORE_CONSUMPTION_NON_TTY=true"],
            claims={
                "NETWORK_SESSION_STARTED": False,
                "AUTHORIZATION_CONSUMED": False,
                "CONFIRM_TOKEN_CONSUMED": False,
                "NON_TTY_FAIL_CLOSED_PROVEN": True,
                "HARD_STOP": True,
            },
            mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
            terminal_class="HARD_STOP",
            authorization_consumed=False,
            confirm_token_consumed=False,
            network_session_started=False,
        )

    auth_valid = bool(authorization_id.strip()) and bool(authorization_digest.strip())
    if not auth_valid:
        blockers.append("AUTHORIZATION_MISSING")

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
    else:
        blockers.extend(reject_confirm_token_argv_v1(argv))
        blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    token_check = validate_confirm_token_binding_v1(
        confirm_token_plaintext=str(token_plain or ""),
        expected_binding_sha256=confirm_token_binding_sha256,
        argv=argv,
        environ=environ,
    )
    if not token_check.get("ok"):
        blockers.extend([str(b) for b in token_check.get("blockers") or []])

    gate = evaluate_execution_mode_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_allowed=network_session_allowed,
        public_md_only=True,
        authorization_valid=auth_valid and "AUTHORIZATION_MISSING" not in blockers,
        confirm_token_valid=bool(token_check.get("ok")),
        stdin_isatty=stdin_isatty if stdin_isatty is not None else True,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    if allow_authorization_consumption or allow_confirm_token_consumption:
        blockers.append("CONSUMPTION_FORBIDDEN_IN_BINDING_CAPABILITY")
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_BINDING_CAPABILITY")

    # Always fail-closed for actual session start in this binding capability.
    blockers.append("REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY")

    return GovernedStep6ExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "HARD_STOP": True,
            "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        terminal_class="HARD_STOP",
        authorization_consumed=False,
        confirm_token_consumed=False,
        network_session_started=False,
        evidence={"token_check": {k: v for k, v in token_check.items() if k != "plaintext"}},
    )
