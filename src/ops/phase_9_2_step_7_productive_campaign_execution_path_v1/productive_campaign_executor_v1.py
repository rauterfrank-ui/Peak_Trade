"""PRODUCTIVE_CAMPAIGN_EXECUTOR for Step-7 (path implementation only).

Implements the Owner-GO-capable productive multi-session campaign execution
path. Never starts a network session and never mints/consumes confirm tokens
in this capability. A later separate Owner-GO Real-TTY campaign may use the
structural gate (`campaign_may_start` / `network_session_may_start`) when all
ephemeral gates pass and session_count satisfies MULTI_SESSION_REQUIREMENT (>1).

Distinct from BINDING_CAMPAIGN_EXECUTOR which always appends
REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    assert_real_tty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    AUTHORIZATION_REUSE_FORBIDDEN,
    BINDING_CAMPAIGN_CAPABILITY_ID,
    BINDING_CAMPAIGN_ROLE,
    BINDING_ENTRYPOINT_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAMPAIGN_EXECUTED,
    CAMPAIGN_ID,
    CANONICAL_PUBLIC_MD_FETCHER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_REUSE_FORBIDDEN,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
    LATER_CAMPAIGN_INVOCATION,
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    MODE_PROVE_PATH_ONLY,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_LADDER_STEP,
    STEP3_RESTART_OWNER,
    STEP4_RECONNECT_OWNER,
    STEP6_STALE_ADVERSE_OWNER,
    STEP7_BINDING_ONLY_PRESERVED,
    STEP7_CAMPAIGN_BUNDLE_OWNER,
    STEP7_CAMPAIGN_HARNESS_BOUND,
    STEP7_CAMPAIGN_HARNESS_OWNER,
    STEP7_CAMPAIGN_VERIFIER_OWNER,
    STEP7_CAMPAIGN_VERIFIER_PRESENT,
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT,
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT,
    STEP7_STARTED,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_state_contract_v1 import (
    load_and_validate_campaign_state_contract_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as BINDING_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (
    prove_step7_reuse_bindings_v1,
)


@dataclass
class ProductiveCampaignExecutionPathResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_PROVE_PATH_ONLY
    terminal_class: str = "HARD_STOP"
    executor_role: str = PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE
    campaign_may_start: bool = False
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
            "campaign_may_start": self.campaign_may_start,
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


def resolve_wallclock_runner_symbol_v1() -> dict[str, Any]:
    module_path, _, attr = CANONICAL_WALLCLOCK_RUNNER.rpartition(".")
    import_path = module_path[len("src.") :] if module_path.startswith("src.") else module_path
    mod = importlib.import_module(import_path)
    runner = getattr(mod, attr, None)
    return {
        "ok": callable(runner),
        "symbol": CANONICAL_WALLCLOCK_RUNNER,
        "import_path": import_path,
        "attr": attr,
        "runner_bound": callable(runner),
    }


def evaluate_productive_campaign_execution_gate_v1(
    *,
    mode: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    public_md_only: bool,
    authorization_valid: bool,
    confirm_token_valid: bool,
    planned_session_count: int,
    stdin_isatty: bool | None = None,
    allow_real_network_side_effects: bool = False,
) -> dict[str, Any]:
    """Structural gate for PRODUCTIVE_CAMPAIGN_EXECUTOR.

    Unlike BINDING_CAMPAIGN_EXECUTOR, this gate can return
    campaign_may_start/network_session_may_start=True when all ephemeral
    session gates pass and planned_session_count satisfies >1. This
    capability still never starts network.
    """
    blockers: list[str] = []
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_PRODUCTIVE_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if BINDING_NETWORK_SESSION_ALLOWED or BINDING_PRODUCTIVE_AUTHORIZED:
        blockers.append("BINDING_NETWORK_FLAGS_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("CONFIRM_TOKEN_CONSTANTS_MUST_REMAIN_FALSE")

    if mode == MODE_PROVE_PATH_ONLY:
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_PATH_ONLY,
            "campaign_may_start": False,
            "network_session_may_start": False,
            "executor_role": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
            "notes": ["PATH_PROOF_MODE_NEVER_STARTS_NETWORK=true"],
        }

    if mode != MODE_GOVERNED_MULTI_SESSION_CAMPAIGN:
        blockers.append("UNKNOWN_EXECUTION_MODE")
        return {
            "ok": False,
            "blockers": blockers,
            "mode": mode,
            "campaign_may_start": False,
            "network_session_may_start": False,
            "executor_role": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
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
    if not multi_session_requirement_satisfied_v1(planned_session_count):
        blockers.append("MULTI_SESSION_REQUIREMENT_NOT_SATISFIED")
    blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))

    structural_ok = not blockers
    may_start = structural_ok
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY")
        may_start = False

    return {
        "ok": not blockers and structural_ok and not allow_real_network_side_effects,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        "campaign_may_start": bool(may_start and not allow_real_network_side_effects),
        "network_session_may_start": bool(may_start and not allow_real_network_side_effects),
        "structural_gates_pass": structural_ok,
        "planned_session_count": int(planned_session_count),
        "multi_session_requirement_expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "executor_role": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
        "notes": [
            "PRODUCTIVE_CAMPAIGN_EXECUTOR_CAN_AUTHORIZE_MAY_START_UNDER_EPHEMERAL_GO=true",
            "THIS_IMPLEMENTATION_CAPABILITY_NEVER_STARTS_NETWORK=true",
            "CONFIRM_TOKEN_MINT_DEFERRED_TO_LATER_CAMPAIGN=true",
            "HIDDEN_CONFIRM_HANDOFF_FOR_LATER_CAMPAIGN_ONLY=true",
            "PER_SESSION_AUTHORIZATION_REQUIRED=true",
            f"MULTI_SESSION_REQUIREMENT_EXPRESSION={MULTI_SESSION_REQUIREMENT_EXPRESSION}",
        ],
    }


def prove_canonical_wallclock_bound_v1() -> dict[str, Any]:
    blockers: list[str] = []
    runner = resolve_wallclock_runner_symbol_v1()
    if not runner.get("ok"):
        blockers.append("CANONICAL_WALLCLOCK_RUNNER_UNRESOLVED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "wallclock_runner": runner,
        "canonical_wallclock_runner": CANONICAL_WALLCLOCK_RUNNER,
        "canonical_public_md_fetcher": CANONICAL_PUBLIC_MD_FETCHER,
        "productive_entrypoint_bound_to_wallclock_runner": bool(runner.get("ok")),
        "parallel_network_runner_created": False,
        "notes": [
            "CANONICAL_WALLCLOCK_OWNER_REUSED=true",
            "CANONICAL_PUBLIC_MD_FETCHER_SYMBOL_BOUND=true",
            "NO_PARALLEL_NETWORK_RUNNER=true",
            "PRODUCTIVE_ENTRYPOINT_BOUND_TO_GOVERNED_REAL_NETWORK_SESSION_OWNER=true",
        ],
    }


def prove_productive_campaign_execution_path_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> ProductiveCampaignExecutionPathResultV1:
    """Prove productive campaign path presence without starting network or minting tokens."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"EXECUTOR_ROLE={PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE}",
        f"BINDING_CAMPAIGN_CAPABILITY_ID={BINDING_CAMPAIGN_CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_THIS_CAPABILITY=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME_IN_THIS_CAPABILITY=true",
        "STEP7_HARNESS_AND_VERIFIER_REUSED=true",
        "NO_PARALLEL_SEMANTIC_MODEL=true",
        f"LATER_CAMPAIGN_INVOCATION={LATER_CAMPAIGN_INVOCATION}",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if not expected_repository_sha or len(str(expected_repository_sha).strip()) < 7:
        blockers.append("REPOSITORY_SHA_INVALID")
    if not expected_config_digest or len(str(expected_config_digest).strip()) < 7:
        blockers.append("CONFIG_DIGEST_INVALID")

    if NETWORK_SESSION_ALLOWED or PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")
    if BINDING_NETWORK_SESSION_ALLOWED or BINDING_PRODUCTIVE_AUTHORIZED:
        blockers.append("BINDING_MUST_NOT_FLIP_NETWORK_FLAGS")
    if NETWORK_SESSION_STARTED_BY_THIS_CAPABILITY or CAMPAIGN_EXECUTED:
        blockers.append("CAMPAIGN_CONSTANTS_MUST_REMAIN_FALSE")
    if STEP7_STARTED:
        blockers.append("STEP7_MUST_NOT_BE_STARTED_BY_THIS_CAPABILITY")
    if STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT:
        blockers.append("PATH_ABSENT_CONSTANT_MUST_BE_FALSE")
    if not STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT:
        blockers.append("PATH_PRESENT_CONSTANT_MUST_BE_TRUE")
    if not STEP7_BINDING_ONLY_PRESERVED:
        blockers.append("BINDING_PRESERVATION_CONSTANT_MUST_BE_TRUE")
    if PHASE_9_2_SESSION_LADDER_COMPLETE:
        blockers.append("SESSION_LADDER_MUST_REMAIN_INCOMPLETE")
    if PHASE_9_2_STEP_6_STATUS != "CLOSED_PASS":
        blockers.append("STEP6_STATUS_MUST_BE_CLOSED_PASS")
    if PHASE_9_2_STEP_7_STATUS != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if not AUTHORIZATION_REUSE_FORBIDDEN or not CONFIRM_TOKEN_REUSE_FORBIDDEN:
        blockers.append("AUTH_OR_CONFIRM_REUSE_MUST_REMAIN_FORBIDDEN")

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

    contract = load_and_validate_campaign_state_contract_v1(repo_root=repo_root)
    if str(contract.get("session_ladder_step") or "") != SESSION_LADDER_STEP:
        blockers.append("CAMPAIGN_CONTRACT_LADDER_STEP_DRIFT")
    req = dict(contract.get("multi_session_requirement") or {})
    if str(req.get("expression") or "") != MULTI_SESSION_REQUIREMENT_EXPRESSION:
        blockers.append("MULTI_SESSION_REQUIREMENT_EXPRESSION_DRIFT")

    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        owner_go=True,
        request_real_network=False,
        repo_root=repo_root,
    )
    if not harness.get("ok"):
        blockers.extend(list(harness.get("blockers") or []))

    binding_forbid = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    if binding_forbid.get("ok"):
        blockers.append("BINDING_MUST_FORBID_REAL_NETWORK")
    if "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" not in (
        binding_forbid.get("blockers") or []
    ):
        blockers.append("BINDING_MUST_EMIT_REAL_NETWORK_FORBIDDEN")

    reuse = prove_step7_reuse_bindings_v1()
    if not reuse.get("ok"):
        blockers.extend(list(reuse.get("blockers") or []))

    owners = prove_canonical_wallclock_bound_v1()
    if not owners.get("ok"):
        blockers.extend(list(owners.get("blockers") or []))

    entry = Path(PRODUCTIVE_ENTRYPOINT_PATH)
    binding_entry = Path(BINDING_ENTRYPOINT_PATH)
    if repo_root is not None:
        entry = Path(repo_root) / PRODUCTIVE_ENTRYPOINT_PATH
        binding_entry = Path(repo_root) / BINDING_ENTRYPOINT_PATH
    if repo_root is not None and not entry.is_file():
        blockers.append("PRODUCTIVE_ENTRYPOINT_MISSING")
    if repo_root is not None and not binding_entry.is_file():
        blockers.append("BINDING_ENTRYPOINT_MISSING")

    gate = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_PROVE_PATH_ONLY,
        owner_go=False,
        operator_authorization_explicit=False,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        planned_session_count=2,
        stdin_isatty=False,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))
    if gate.get("campaign_may_start") or gate.get("network_session_may_start"):
        blockers.append("PATH_PROOF_MUST_NOT_AUTHORIZE_MAY_START")

    one_session = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        stdin_isatty=True,
    )
    if one_session.get("campaign_may_start") or one_session.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_REJECT_SINGLE_SESSION")
    if "MULTI_SESSION_REQUIREMENT_NOT_SATISFIED" not in (one_session.get("blockers") or []):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_REQUIRE_MULTI_SESSION")

    no_go = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
    )
    if no_go.get("campaign_may_start") or no_go.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_FAIL_WITHOUT_NETWORK_SESSION_GO")
    if "NETWORK_SESSION_GO_REQUIRED" not in (no_go.get("blockers") or []):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_REQUIRE_NETWORK_SESSION_GO")

    full = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
    )
    if not full.get("campaign_may_start") or not full.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    ok = (
        not blockers
        and bool(harness.get("ok"))
        and bool(handoff.get("ok"))
        and bool(owners.get("ok"))
        and bool(reuse.get("ok"))
    )
    claims = {
        "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT": (
            STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT and ok
        ),
        "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT": False,
        "STEP7_BINDING_ONLY_PRESERVED": STEP7_BINDING_ONLY_PRESERVED,
        "PRODUCTIVE_CAMPAIGN_EXECUTOR_IMPLEMENTED": ok,
        "BINDING_CAMPAIGN_ROLE": BINDING_CAMPAIGN_ROLE,
        "PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
        "PRODUCTIVE_EXECUTOR_REQUIRES_SEPARATE_OWNER_GO_CAMPAIGN": True,
        "REAL_TTY_REQUIRED": True,
        "HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_CAMPAIGN": bool(handoff.get("ok")),
        "HIDDEN_CONFIRM_HANDOFF_USED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "EXPLICIT_CAMPAIGN_OWNER_GO_REQUIRED": True,
        "EPHEMERAL_NETWORK_SESSION_GO_BOUND": True,
        "PUBLIC_MD_ONLY_ENFORCED": bool(boundary.get("PUBLIC_MD_ONLY")),
        "ORDERS_DISABLED": True,
        "WALLCLOCK_OWNER_REUSED": bool((owners.get("wallclock_runner") or {}).get("ok")),
        "PRODUCTIVE_ENTRYPOINT_BOUND_TO_WALLCLOCK_RUNNER": bool(
            owners.get("productive_entrypoint_bound_to_wallclock_runner")
        ),
        "STEP7_CAMPAIGN_HARNESS_BOUND": STEP7_CAMPAIGN_HARNESS_BOUND and bool(harness.get("ok")),
        "STEP7_CAMPAIGN_VERIFIER_PRESENT": STEP7_CAMPAIGN_VERIFIER_PRESENT,
        "STEP7_CAMPAIGN_HARNESS_OWNER": STEP7_CAMPAIGN_HARNESS_OWNER,
        "STEP7_CAMPAIGN_VERIFIER_OWNER": STEP7_CAMPAIGN_VERIFIER_OWNER,
        "STEP7_CAMPAIGN_BUNDLE_OWNER": STEP7_CAMPAIGN_BUNDLE_OWNER,
        "STEP3_RESTART_OWNER": STEP3_RESTART_OWNER,
        "STEP4_RECONNECT_OWNER": STEP4_RECONNECT_OWNER,
        "STEP6_STALE_ADVERSE_OWNER": STEP6_STALE_ADVERSE_OWNER,
        "MULTI_SESSION_REQUIREMENT_EXPRESSION": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "REPEATED_MULTI_SESSION_SUPPORTED": True,
        "MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_ONE": multi_session_requirement_satisfied_v1(1),
        "MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_TWO": multi_session_requirement_satisfied_v1(2),
        "NETWORK_CALLS_DURING_THIS_CAPABILITY": 0,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_COUNT": 0,
        "CAMPAIGN_EXECUTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        "STEP7_STARTED": False,
        "CAMPAIGN_ID": CAMPAIGN_ID,
        "TARGET_CAMPAIGN_CAPABILITY_ID": TARGET_CAMPAIGN_CAPABILITY_ID,
        "TARGET_SESSION_ID_PREFIX": TARGET_SESSION_ID_PREFIX,
        "PRIVATE_ENDPOINT_REACHABLE": bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        "CREDENTIAL_PATH_REACHABLE": bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION": ok,
        "CALL_GRAPH_BEFORE": list(CALL_GRAPH_BEFORE),
        "CALL_GRAPH_AFTER": list(CALL_GRAPH_AFTER),
        "HIDDEN_PTY_CONFIRM_HANDOFF_OWNER": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "STRUCTURAL_MAY_START_UNDER_FULL_GO": bool(full.get("campaign_may_start")),
        "STRUCTURAL_MAY_START_WITHOUT_NETWORK_SESSION_GO": bool(no_go.get("campaign_may_start")),
        "STRUCTURAL_MAY_START_WITH_SINGLE_SESSION": bool(one_session.get("campaign_may_start")),
        "REAL_NETWORK_SESSION_FORBIDDEN_IN_IMPLEMENTATION_CAPABILITY": True,
    }
    return ProductiveCampaignExecutionPathResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_PATH_ONLY,
        terminal_class="PATH_PROOF" if ok else "HARD_STOP",
        campaign_may_start=False,
        network_session_may_start=False,
        evidence={
            "hidden_pty_handoff": handoff,
            "boundary": boundary,
            "campaign_contract": {
                "session_ladder_step": contract.get("session_ladder_step"),
                "multi_session_requirement": contract.get("multi_session_requirement"),
            },
            "harness": {
                "ok": harness.get("ok"),
                "blockers": harness.get("blockers"),
                "NETWORK_SESSION_STARTED": harness.get("NETWORK_SESSION_STARTED"),
            },
            "binding_forbid_real_network": binding_forbid,
            "reuse": reuse,
            "owners": owners,
            "network_session_go": go,
            "gate_single_session": {k: v for k, v in one_session.items() if k != "notes"},
            "gate_without_network_session_go": {k: v for k, v in no_go.items() if k != "notes"},
            "gate_with_full_ephemeral_go": {k: v for k, v in full.items() if k != "notes"},
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
    )


def invoke_productive_campaign_executor_offline_fail_closed_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    owner_go: bool = False,
    operator_authorization_explicit: bool = False,
    network_session_go: bool = False,
    public_md_only: bool = True,
    authorization_valid: bool = False,
    confirm_token_valid: bool = False,
    planned_session_count: int = 2,
    allow_real_network_side_effects: bool = False,
    stdin_isatty: bool | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> ProductiveCampaignExecutionPathResultV1:
    """Offline invoke of productive campaign executor. Never starts network."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "PRODUCTIVE_CAMPAIGN_EXECUTOR_OFFLINE_INVOKE=true",
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

    gate = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=public_md_only,
        authorization_valid=authorization_valid,
        confirm_token_valid=confirm_token_valid,
        planned_session_count=planned_session_count,
        stdin_isatty=stdin_isatty,
        allow_real_network_side_effects=allow_real_network_side_effects,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    may_start = bool(gate.get("campaign_may_start"))
    notes.append(f"STRUCTURAL_CAMPAIGN_MAY_START={may_start}")
    notes.append("NETWORK_SESSION_START_DEFERRED_TO_SEPARATE_OWNER_GO_CAMPAIGN=true")

    return ProductiveCampaignExecutionPathResultV1(
        ok=False,  # never ok for real campaign inside this capability
        blockers=sorted(set(blockers + ["NETWORK_SESSION_START_DEFERRED_TO_LATER_CAMPAIGN"])),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "NETWORK_SESSION_COUNT": 0,
            "CAMPAIGN_EXECUTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "HIDDEN_CONFIRM_HANDOFF_USED": False,
            "CAMPAIGN_MAY_START_STRUCTURAL": may_start,
            "NETWORK_SESSION_MAY_START_STRUCTURAL": may_start,
            "PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
            "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
            "MULTI_SESSION_REQUIREMENT_EXPRESSION": MULTI_SESSION_REQUIREMENT_EXPRESSION,
            "PLANNED_SESSION_COUNT": int(planned_session_count),
            "NETWORK_CALLS": 0,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "repo_root": str(repo_root) if repo_root else "",
        },
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        terminal_class="HARD_STOP",
        campaign_may_start=may_start,
        network_session_may_start=may_start,
        evidence={
            "network_session_go": go,
            "gate": gate,
        },
    )
