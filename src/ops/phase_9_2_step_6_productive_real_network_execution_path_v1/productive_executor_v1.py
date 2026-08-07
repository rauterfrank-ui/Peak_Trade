"""PRODUCTIVE_REAL_NETWORK_EXECUTOR for Step-6 (path implementation only).

This module implements the Owner-GO-capable productive Real-Network execution
path. It never starts a network session and never mints/consumes confirm tokens
in this capability. A later separate Owner-GO Real-TTY session may use the
structural gate (`network_session_may_start`) when all ephemeral gates pass.

Distinct from BINDING_EXECUTOR which always appends
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prepare_adverse_stale_runtime_overrides_v1,
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    assert_real_tty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.constants_v1 import (
    BINDING_EXECUTOR_CAPABILITY_ID,
    BINDING_EXECUTOR_ENTRYPOINT_PATH,
    BINDING_EXECUTOR_ROLE,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CANONICAL_PUBLIC_MD_FETCHER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
    LATER_SESSION_INVOCATION,
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_PATH_ONLY,
    NETWORK_SESSION_ALLOWED,
    NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTED,
    STEP5_FETCHER_WIRING_PATTERN_OWNER,
    STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT,
    STEP6_VERIFIER_OWNER,
    STEP7_STARTED,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)


@dataclass
class ProductiveRealNetworkExecutionPathResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_PROVE_PATH_ONLY
    terminal_class: str = "HARD_STOP"
    executor_role: str = PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE
    network_session_may_start: bool = False
    network_session_started: bool = False
    network_session_count: int = 0
    network_calls: int = 0
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    confirm_token_minted: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "mode": self.mode,
            "terminal_class": self.terminal_class,
            "executor_role": self.executor_role,
            "network_session_may_start": self.network_session_may_start,
            "network_session_started": self.network_session_started,
            "network_session_count": self.network_session_count,
            "network_calls": self.network_calls,
            "authorization_consumed": self.authorization_consumed,
            "confirm_token_consumed": self.confirm_token_consumed,
            "confirm_token_minted": self.confirm_token_minted,
            "evidence": dict(self.evidence),
            "capability_id": CAPABILITY_ID,
        }


def evaluate_productive_real_network_execution_gate_v1(
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
    allow_real_network_side_effects: bool = False,
) -> dict[str, Any]:
    """Structural gate for PRODUCTIVE_REAL_NETWORK_EXECUTOR.

    Unlike BINDING_EXECUTOR, this gate can return network_session_may_start=True
    when all ephemeral session gates pass. This capability still never starts
    network (callers must not invoke side effects here).
    """
    blockers: list[str] = []
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_PRODUCTIVE_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if PREDECESSOR_NETWORK_SESSION_ALLOWED:
        blockers.append("PREDECESSOR_NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("CONFIRM_TOKEN_CONSTANTS_MUST_REMAIN_FALSE")

    if mode == MODE_PROVE_PATH_ONLY:
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_PATH_ONLY,
            "network_session_may_start": False,
            "executor_role": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
            "notes": ["PATH_PROOF_MODE_NEVER_STARTS_NETWORK=true"],
        }

    if mode != MODE_GOVERNED_REAL_NETWORK_SESSION:
        blockers.append("UNKNOWN_EXECUTION_MODE")
        return {
            "ok": False,
            "blockers": blockers,
            "mode": mode,
            "network_session_may_start": False,
            "executor_role": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
        }

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_EXPLICIT_REQUIRED")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED")
    if not public_md_only:
        blockers.append("PUBLIC_MD_ONLY_REQUIRED")
    if not authorization_valid:
        blockers.append("AUTHORIZATION_INVALID")
    if not confirm_token_valid:
        blockers.append("CONFIRM_TOKEN_INVALID")
    if not stale_control_present:
        blockers.append("STALE_CONTROL_ABSENT")
    blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))

    structural_ok = not blockers
    # Productive path may authorize start structurally for a later session.
    # This capability still forbids actual side effects unless a later session
    # capability explicitly enables them under a separate Owner-GO.
    may_start = structural_ok
    if allow_real_network_side_effects:
        # Side effects remain forbidden inside this implementation capability.
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY")
        may_start = False

    return {
        "ok": not blockers and structural_ok and not allow_real_network_side_effects,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_REAL_NETWORK_SESSION,
        "network_session_may_start": bool(may_start and not allow_real_network_side_effects),
        "structural_gates_pass": structural_ok,
        "executor_role": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
        "notes": [
            "PRODUCTIVE_EXECUTOR_CAN_AUTHORIZE_MAY_START_UNDER_EPHEMERAL_GO=true",
            "THIS_IMPLEMENTATION_CAPABILITY_NEVER_STARTS_NETWORK=true",
            "CONFIRM_TOKEN_MINT_DEFERRED_TO_LATER_SESSION=true",
            "HIDDEN_CONFIRM_HANDOFF_FOR_LATER_SESSION_ONLY=true",
        ],
    }


def prove_canonical_fetcher_and_wallclock_bound_v1() -> dict[str, Any]:
    blockers: list[str] = []
    from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (  # noqa: E501
        resolve_wallclock_runner_symbol_v1,
    )

    runner = resolve_wallclock_runner_symbol_v1()
    if not runner.get("ok"):
        blockers.append("CANONICAL_WALLCLOCK_RUNNER_UNRESOLVED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "wallclock_runner": runner,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
        "fetcher_wiring_pattern_owner": STEP5_FETCHER_WIRING_PATTERN_OWNER,
        "parallel_network_runner_created": False,
        "notes": [
            "CANONICAL_WALLCLOCK_OWNER_REUSED=true",
            "CANONICAL_PUBLIC_MD_FETCHER_SYMBOL_BOUND=true",
            "NO_PARALLEL_NETWORK_RUNNER=true",
        ],
    }


def prove_productive_real_network_execution_path_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> ProductiveRealNetworkExecutionPathResultV1:
    """Prove productive path presence without starting network or minting tokens."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"EXECUTOR_ROLE={PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE}",
        f"BINDING_EXECUTOR_CAPABILITY_ID={BINDING_EXECUTOR_CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME_IN_THIS_CAPABILITY=true",
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
    if NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY or SESSION_EXECUTED:
        blockers.append("SESSION_CONSTANTS_MUST_REMAIN_FALSE")
    if STEP7_STARTED:
        blockers.append("STEP7_MUST_NOT_BE_STARTED")
    if STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT:
        blockers.append("PATH_ABSENT_CONSTANT_MUST_BE_FALSE")
    if not STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT:
        blockers.append("PATH_PRESENT_CONSTANT_MUST_BE_TRUE")
    if not STEP6_BINDING_ONLY_EXECUTOR_PRESERVED:
        blockers.append("BINDING_EXECUTOR_PRESERVATION_CONSTANT_MUST_BE_TRUE")

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

    owners = prove_canonical_fetcher_and_wallclock_bound_v1()
    if not owners.get("ok"):
        blockers.extend(list(owners.get("blockers") or []))

    entry = Path(PRODUCTIVE_ENTRYPOINT_PATH)
    binding_entry = Path(BINDING_EXECUTOR_ENTRYPOINT_PATH)
    if repo_root is not None:
        entry = Path(repo_root) / PRODUCTIVE_ENTRYPOINT_PATH
        binding_entry = Path(repo_root) / BINDING_EXECUTOR_ENTRYPOINT_PATH
    if repo_root is not None and not entry.is_file():
        blockers.append("PRODUCTIVE_ENTRYPOINT_MISSING")
    if repo_root is not None and not binding_entry.is_file():
        blockers.append("BINDING_EXECUTOR_ENTRYPOINT_MISSING")

    # Default path-proof gate must not authorize may_start.
    gate = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_PROVE_PATH_ONLY,
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
    if gate.get("network_session_may_start"):
        blockers.append("PATH_PROOF_MUST_NOT_AUTHORIZE_MAY_START")

    # Without NETWORK_SESSION_GO the productive executor must not authorize start.
    no_go = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    if no_go.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_FAIL_WITHOUT_NETWORK_SESSION_GO")
    if "NETWORK_SESSION_GO_REQUIRED" not in (no_go.get("blockers") or []):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_REQUIRE_NETWORK_SESSION_GO")

    # With full ephemeral gates, productive executor may authorize may_start
    # (still no network start in this capability).
    full = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    if not full.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    ok = (
        not blockers
        and bool(stale.get("ok"))
        and bool(handoff.get("ok"))
        and bool(owners.get("ok"))
    )
    claims = {
        "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT": (
            STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT and ok
        ),
        "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT": False,
        "STEP6_BINDING_ONLY_EXECUTOR_PRESERVED": STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
        "PRODUCTIVE_REAL_NETWORK_EXECUTOR_IMPLEMENTED": ok,
        "BINDING_EXECUTOR_ROLE": BINDING_EXECUTOR_ROLE,
        "PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
        "PRODUCTIVE_EXECUTOR_REQUIRES_SEPARATE_OWNER_GO_SESSION": True,
        "REAL_TTY_REQUIRED": True,
        "HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_SESSION": bool(handoff.get("ok")),
        "HIDDEN_CONFIRM_HANDOFF_USED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "EXPLICIT_SESSION_OWNER_GO_REQUIRED": True,
        "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
        "PUBLIC_MD_ONLY_ENFORCED": bool(boundary.get("PUBLIC_MD_ONLY")),
        "ORDERS_DISABLED": True,
        "GOVERNED_STALE_CONTROL_BOUND": bool(stale.get("ok")),
        "FAILURE_INJECTION_BOUND": bool((stale.get("classification") or {}).get("ok")),
        "WALLCLOCK_OWNER_REUSED": bool((owners.get("wallclock_runner") or {}).get("ok")),
        "STEP6_VERIFIER_BOUND": True,
        "STEP6_VERIFIER_OWNER": STEP6_VERIFIER_OWNER,
        "MAX_NETWORK_SESSION_COUNT": MAX_NETWORK_SESSION_COUNT,
        "NETWORK_CALLS_DURING_THIS_CAPABILITY": 0,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_COUNT": 0,
        "SESSION_EXECUTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "STEP7_STARTED": False,
        "TARGET_SESSION_ID": TARGET_SESSION_ID,
        "PRIVATE_ENDPOINT_REACHABLE": bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        "CREDENTIAL_PATH_REACHABLE": bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "PREDECESSOR_NETWORK_SESSION_ALLOWED_UNCHANGED": (
            PREDECESSOR_NETWORK_SESSION_ALLOWED is False
        ),
        "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION": ok,
        "CALL_GRAPH_BEFORE": list(CALL_GRAPH_BEFORE),
        "CALL_GRAPH_AFTER": list(CALL_GRAPH_AFTER),
        "HIDDEN_PTY_CONFIRM_HANDOFF_OWNER": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "STRUCTURAL_MAY_START_UNDER_FULL_GO": bool(full.get("network_session_may_start")),
        "STRUCTURAL_MAY_START_WITHOUT_NETWORK_SESSION_GO": bool(
            no_go.get("network_session_may_start")
        ),
    }
    return ProductiveRealNetworkExecutionPathResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_PATH_ONLY,
        terminal_class="PATH_PROOF" if ok else "HARD_STOP",
        network_session_may_start=False,
        evidence={
            "hidden_pty_handoff": handoff,
            "boundary": boundary,
            "adverse_stale_executor": stale,
            "owners": owners,
            "network_session_go": go,
            "gate_without_network_session_go": no_go,
            "gate_with_full_ephemeral_go": {k: v for k, v in full.items() if k != "notes"},
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
    )


def invoke_productive_executor_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_go: bool = False,
    public_md_only: bool = True,
    authorization_valid: bool = False,
    confirm_token_valid: bool = False,
    enable_receive_lag: bool = False,
    allow_real_network_side_effects: bool = False,
    stdin_isatty: bool | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> ProductiveRealNetworkExecutionPathResultV1:
    """Offline invoke of productive executor. Never starts network; never mints tokens."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "PRODUCTIVE_EXECUTOR_OFFLINE_INVOKE=true",
        "NO_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go, environ=environ
    )
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))

    stale_prep = prepare_adverse_stale_runtime_overrides_v1(
        enable_receive_lag=bool(enable_receive_lag and network_session_go and owner_go)
    )
    stale_present = bool(stale_prep.get("ok")) and (
        "governed_stale_data_control" in (stale_prep.get("runtime_overrides") or {})
    )
    if not stale_present:
        blockers.append("STALE_CONTROL_ABSENT")

    gate = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=public_md_only,
        authorization_valid=authorization_valid,
        confirm_token_valid=confirm_token_valid,
        stale_control_present=stale_present,
        stdin_isatty=stdin_isatty,
        allow_real_network_side_effects=allow_real_network_side_effects,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    # Implementation capability never starts network even when may_start is True.
    may_start = bool(gate.get("network_session_may_start"))
    notes.append(f"STRUCTURAL_NETWORK_SESSION_MAY_START={may_start}")
    notes.append("NETWORK_SESSION_START_DEFERRED_TO_SEPARATE_OWNER_GO_SESSION=true")

    return ProductiveRealNetworkExecutionPathResultV1(
        ok=False,  # never ok for real session inside this capability
        blockers=sorted(set(blockers + ["NETWORK_SESSION_START_DEFERRED_TO_LATER_SESSION"])),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "NETWORK_SESSION_COUNT": 0,
            "SESSION_EXECUTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "HIDDEN_CONFIRM_HANDOFF_USED": False,
            "NETWORK_SESSION_MAY_START_STRUCTURAL": may_start,
            "PRODUCTIVE_EXECUTOR_ROLE": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
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
        network_session_may_start=may_start,
        evidence={
            "network_session_go": go,
            "gate": gate,
            "stale_prep": {
                "ok": stale_prep.get("ok"),
                "stale_control_enabled": stale_prep.get("stale_control_enabled"),
                "receive_lag_schedule": stale_prep.get("receive_lag_schedule"),
                "blockers": stale_prep.get("blockers"),
            },
        },
    )
