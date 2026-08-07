"""Governed Step-7 Real-TTY campaign execution owner (implementation).

Implements campaign-owner wiring and the productive invoke edge
(`execute_governed_step7_campaign_v1`). Prove/materialize/offline paths never
start a Public-MD network session and never mint confirm tokens. A later
Owner-GO Real-TTY campaign may invoke the wired start edge under ephemeral
NETWORK_SESSION_GO when all campaign gates pass and session count satisfies >1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.network_boundary_v1 import (
    prove_public_md_only_boundary_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    acquire_confirm_token_via_hidden_pty_v1,
    prove_hidden_pty_confirm_handoff_binding_v1,
    redact_confirm_token_mapping_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.campaign_gate_v1 import (
    evaluate_campaign_execution_gate_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.campaign_start_invoke_v1 import (
    invoke_step7_productive_campaign_sessions_v1,
    prove_public_md_fetcher_symbol_bound_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_SUPPORTED,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    BINDING_CAMPAIGN_CAPABILITY_ID,
    BINDING_ENTRYPOINT_PATH,
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CAMPAIGN_EXECUTION_ALLOWED,
    CAMPAIGN_ID,
    CAPABILITY_ID,
    CONFIRM_TOKEN_MINTING_ALLOWED,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    DEFAULT_AUTHORIZATION_CHANNEL,
    DEFAULT_PLANNED_SESSION_COUNT,
    DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
    LATER_CAMPAIGN_INVOCATION,
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    MODE_PROVE_IMPLEMENTATION_ONLY,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PATH_ENTRYPOINT_PATH,
    PATH_IMPLEMENTATION_CAPABILITY_ID,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL,
    PRODUCTIVE_ENTRYPOINT_PATH,
    READY_FOR_SEPARATE_OWNER_GO_DELEGATED_CURSOR_CAMPAIGN,
    READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN,
    REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
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
    STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT,
    STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE,
    STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT,
    STEP7_STARTED,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    TARGET_SESSION_ID_PREFIX,
    is_target_campaign_capability_id_v1,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (
    DelegatedCursorSecureConfirmLatchV1,
    acquire_delegated_cursor_secure_confirm_v1,
    prove_delegated_cursor_secure_confirm_broker_binding_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.network_session_go_v1 import (
    bind_ephemeral_network_session_go_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.productive_path_consumer_v1 import (
    consume_productive_campaign_path_dependency_v1,
    prove_path_alone_cannot_start_campaign_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.repository_binding_gate_v1 import (
    evaluate_delegated_cursor_repository_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_verifier_v1 import (
    verify_campaign_bundle_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (
    prove_step7_reuse_bindings_v1,
)

GetPassFn = Callable[[str], str]


@dataclass
class GovernedStep7CampaignExecutionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    mode: str = MODE_PROVE_IMPLEMENTATION_ONLY
    terminal_class: str = "HARD_STOP"
    campaign_may_start: bool = False
    network_session_may_start: bool = False
    network_session_started: bool = False
    network_session_count: int = 0
    planned_session_count: int = 0
    completed_session_count: int = 0
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
                "campaign_may_start": self.campaign_may_start,
                "network_session_may_start": self.network_session_may_start,
                "network_session_started": self.network_session_started,
                "network_session_count": self.network_session_count,
                "planned_session_count": self.planned_session_count,
                "completed_session_count": self.completed_session_count,
                "network_calls": self.network_calls,
                "confirm_token_minted": self.confirm_token_minted,
                "confirm_token_consumed": self.confirm_token_consumed,
                "authorization_consumed": self.authorization_consumed,
                "evidence": dict(self.evidence),
                "capability_id": CAPABILITY_ID,
                "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
                "productive_entrypoint": PRODUCTIVE_ENTRYPOINT_PATH,
                "real_tty_operator_entrypoint": REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
                "delegated_cursor_operator_entrypoint": DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
                "path_entrypoint": PATH_ENTRYPOINT_PATH,
                "binding_entrypoint": BINDING_ENTRYPOINT_PATH,
                "call_graph_before": list(CALL_GRAPH_BEFORE),
                "call_graph_after": list(CALL_GRAPH_AFTER),
            }
        )


def prove_step7_campaign_execution_owner_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    actual_repository_sha: str | None = None,
    actual_config_digest: str | None = None,
    repo_root: Path | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> GovernedStep7CampaignExecutionResultV1:
    """Prove Real-TTY campaign owner wiring without starting network or minting tokens."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"TARGET_CAMPAIGN_CAPABILITY_ID={TARGET_CAMPAIGN_CAPABILITY_ID}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_MINT_OR_CONSUME_IN_IMPLEMENTATION=true",
        "NO_PARALLEL_SEMANTIC_MODEL=true",
        f"LATER_CAMPAIGN_INVOCATION={LATER_CAMPAIGN_INVOCATION}",
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

    if NETWORK_SESSION_ALLOWED or CAMPAIGN_EXECUTION_ALLOWED:
        blockers.append("PERMANENT_ENABLE_MUST_REMAIN_FALSE")
    if CONFIRM_TOKEN_MINTING_ALLOWED or AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_MINT_OR_CONSUME_MUST_REMAIN_FALSE")
    if STEP7_STARTED or PHASE_9_2_SESSION_LADDER_COMPLETE:
        blockers.append("STEP7_OR_LADDER_MUST_REMAIN_OPEN_INCOMPLETE")
    if PHASE_9_2_STEP_6_STATUS != "CLOSED_PASS":
        blockers.append("STEP6_STATUS_MUST_BE_CLOSED_PASS")
    if PHASE_9_2_STEP_7_STATUS != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT:
        blockers.append("PATH_ABSENT_CONSTANT_MUST_BE_FALSE")
    if not STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT:
        blockers.append("PATH_PRESENT_CONSTANT_MUST_BE_TRUE")

    go = bind_ephemeral_network_session_go_v1(network_session_go=False, environ=environ)
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))
    if go.get("network_session_go"):
        blockers.append("DEFAULT_NETWORK_SESSION_GO_MUST_BE_FALSE")

    path_dep = consume_productive_campaign_path_dependency_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not path_dep.get("ok"):
        blockers.extend(list(path_dep.get("blockers") or []))

    path_alone = prove_path_alone_cannot_start_campaign_v1()
    if not path_alone.get("ok"):
        blockers.append("PATH_ALONE_MUST_REMAIN_NON_STARTING")

    binding_forbid = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    if binding_forbid.get("ok"):
        blockers.append("BINDING_MUST_FORBID_REAL_NETWORK")
    if "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" not in (
        binding_forbid.get("blockers") or []
    ):
        blockers.append("BINDING_MUST_EMIT_REAL_NETWORK_FORBIDDEN")

    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        owner_go=True,
        request_real_network=False,
        repo_root=repo_root,
    )
    if not harness.get("ok"):
        blockers.extend(list(harness.get("blockers") or []))

    reuse = prove_step7_reuse_bindings_v1()
    if not reuse.get("ok"):
        blockers.extend(list(reuse.get("blockers") or []))

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if not handoff.get("ok"):
        blockers.append("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    delegated_broker = prove_delegated_cursor_secure_confirm_broker_binding_v1()
    if not delegated_broker.get("ok"):
        blockers.append("DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_BINDING_FAILED")

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    fetcher_proof = prove_public_md_fetcher_symbol_bound_v1()
    if not fetcher_proof.get("ok"):
        blockers.append("CANONICAL_PUBLIC_MD_FETCHER_UNRESOLVED")
    if not callable(invoke_step7_productive_campaign_sessions_v1):
        blockers.append("CAMPAIGN_INVOKE_HELPER_UNRESOLVED")
    if not callable(verify_campaign_bundle_v1):
        blockers.append("STEP7_CAMPAIGN_VERIFIER_UNRESOLVED")

    if repo_root is not None:
        for label, rel in (
            ("CAMPAIGN_OWNER_ENTRYPOINT_MISSING", PRODUCTIVE_ENTRYPOINT_PATH),
            ("REAL_TTY_OPERATOR_ENTRYPOINT_MISSING", REAL_TTY_OPERATOR_ENTRYPOINT_PATH),
            (
                "DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_MISSING",
                DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
            ),
            ("PATH_ENTRYPOINT_MISSING", PATH_ENTRYPOINT_PATH),
            ("BINDING_ENTRYPOINT_MISSING", BINDING_ENTRYPOINT_PATH),
        ):
            if not (Path(repo_root) / rel).is_file():
                blockers.append(label)

    prove_gate = evaluate_campaign_execution_gate_v1(
        mode=MODE_PROVE_IMPLEMENTATION_ONLY,
        owner_go=False,
        operator_authorization_explicit=False,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=False,
        confirm_token_valid=False,
        planned_session_count=DEFAULT_PLANNED_SESSION_COUNT,
        productive_path_present=bool(path_dep.get("path_present")),
        productive_path_consumed=bool(path_dep.get("consumes_productive_path")),
        harness_bound=bool(harness.get("ok")),
        verifier_bound=True,
        repository_sha_match=sha_match,
        config_digest_match=cfg_match,
        stdin_isatty=False,
    )
    if prove_gate.get("campaign_may_start"):
        blockers.append("PROVE_MODE_MUST_NOT_AUTHORIZE_MAY_START")

    one_session = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        productive_path_present=True,
        productive_path_consumed=True,
        harness_bound=True,
        verifier_bound=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=True,
        hidden_confirm_handoff_reachable=True,
    )
    if one_session.get("campaign_may_start"):
        blockers.append("CAMPAIGN_MUST_REJECT_SINGLE_SESSION")
    if "MULTI_SESSION_REQUIREMENT_NOT_SATISFIED" not in (one_session.get("blockers") or []):
        blockers.append("CAMPAIGN_MUST_REQUIRE_MULTI_SESSION")

    no_go = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=DEFAULT_PLANNED_SESSION_COUNT,
        productive_path_present=True,
        productive_path_consumed=True,
        harness_bound=True,
        verifier_bound=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=True,
        hidden_confirm_handoff_reachable=True,
    )
    if no_go.get("campaign_may_start"):
        blockers.append("CAMPAIGN_MUST_FAIL_WITHOUT_NETWORK_SESSION_GO")
    if "NETWORK_SESSION_GO_REQUIRED" not in (no_go.get("blockers") or []):
        blockers.append("CAMPAIGN_MUST_REQUIRE_NETWORK_SESSION_GO")

    full = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=DEFAULT_PLANNED_SESSION_COUNT,
        productive_path_present=True,
        productive_path_consumed=True,
        harness_bound=True,
        verifier_bound=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=True,
        hidden_confirm_handoff_reachable=True,
        authorization_channel=AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    )
    if not full.get("campaign_may_start"):
        blockers.append("CAMPAIGN_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    full_delegated = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=DEFAULT_PLANNED_SESSION_COUNT,
        productive_path_present=True,
        productive_path_consumed=True,
        harness_bound=True,
        verifier_bound=True,
        repository_sha_match=True,
        config_digest_match=True,
        stdin_isatty=False,
        hidden_confirm_handoff_reachable=False,
        authorization_channel=AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
        delegated_secure_confirm_verified=True,
        head_equals_origin_main=True,
        tracked_worktree_clean=True,
        allow_real_network_side_effects=True,
    )
    if not full_delegated.get("campaign_may_start"):
        blockers.append("CAMPAIGN_MUST_AUTHORIZE_MAY_START_UNDER_DELEGATED_CURSOR")

    if not STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT:
        blockers.append("CAMPAIGN_INVOKE_EDGE_CONSTANT_FALSE")
    if not STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE:
        blockers.append("CAMPAIGN_INVOKE_EDGE_NOT_RUNTIME_REACHABLE")

    ok = (
        not blockers
        and bool(path_dep.get("ok"))
        and bool(harness.get("ok"))
        and bool(handoff.get("ok"))
        and bool(delegated_broker.get("ok"))
        and bool(reuse.get("ok"))
        and bool(fetcher_proof.get("ok"))
        and STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT
        and callable(invoke_step7_productive_campaign_sessions_v1)
    )
    claims = {
        "STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT": STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT and ok,
        "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT": (
            STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT and ok
        ),
        "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE": (
            STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE and ok
        ),
        "PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL": PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL,
        "TARGET_CAMPAIGN_CAPABILITY_ID": TARGET_CAMPAIGN_CAPABILITY_ID,
        "BINDING_CAMPAIGN_CAPABILITY_ID": BINDING_CAMPAIGN_CAPABILITY_ID,
        "PATH_IMPLEMENTATION_CAPABILITY_ID": PATH_IMPLEMENTATION_CAPABILITY_ID,
        "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT": (
            STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT and bool(path_dep.get("path_present"))
        ),
        "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT": False,
        "STEP7_BINDING_ONLY_PRESERVED": STEP7_BINDING_ONLY_PRESERVED,
        "BINDING_ONLY_NOT_USED_AS_CAMPAIGN_OWNER": True,
        "PATH_ALONE_CANNOT_START_CAMPAIGN": bool(path_alone.get("ok")),
        "PRODUCTIVE_PATH_CONSUMED": bool(path_dep.get("consumes_productive_path")),
        "STEP7_CAMPAIGN_HARNESS_BOUND": STEP7_CAMPAIGN_HARNESS_BOUND and bool(harness.get("ok")),
        "STEP7_CAMPAIGN_VERIFIER_PRESENT": STEP7_CAMPAIGN_VERIFIER_PRESENT,
        "STEP7_CAMPAIGN_HARNESS_OWNER": STEP7_CAMPAIGN_HARNESS_OWNER,
        "STEP7_CAMPAIGN_VERIFIER_OWNER": STEP7_CAMPAIGN_VERIFIER_OWNER,
        "STEP7_CAMPAIGN_BUNDLE_OWNER": STEP7_CAMPAIGN_BUNDLE_OWNER,
        "STEP3_RESTART_OWNER": STEP3_RESTART_OWNER,
        "STEP4_RECONNECT_OWNER": STEP4_RECONNECT_OWNER,
        "STEP6_STALE_ADVERSE_OWNER": STEP6_STALE_ADVERSE_OWNER,
        "MULTI_SESSION_REQUIREMENT_EXPRESSION": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_ONE": multi_session_requirement_satisfied_v1(1),
        "MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_TWO": multi_session_requirement_satisfied_v1(2),
        "REPEATED_MULTI_SESSION_SUPPORTED": True,
        "PUBLIC_MD_FETCHER_BOUND": bool(fetcher_proof.get("ok")),
        "REAL_TTY_REQUIRED": True,
        "REAL_TTY_CHANNEL_SUPPORTED": AUTH_CHANNEL_REAL_TTY_SUPPORTED and ok,
        "DELEGATED_CURSOR_SECURE_CONFIRM_SUPPORTED": (
            AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED and ok
        ),
        "AUTH_CHANNEL_REAL_TTY_SUPPORTED": AUTH_CHANNEL_REAL_TTY_SUPPORTED and ok,
        "AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED": AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED and ok,
        "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
        "HIDDEN_CONFIRM_HANDOFF_BOUND": bool(handoff.get("ok")),
        "DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_BOUND": bool(delegated_broker.get("ok")),
        "HIDDEN_CONFIRM_HANDOFF_USED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "PUBLIC_MD_ONLY_ENFORCED": bool(boundary.get("PUBLIC_MD_ONLY")),
        "ORDERS_DISABLED": True,
        "PRIVATE_ENDPOINT_REACHABLE": bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        "CREDENTIAL_PATH_REACHABLE": bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        "ORDER_SIDE_EFFECT_REACHABLE": bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        "EXCHANGE_CREDENTIAL_PATH_CHANGED": False,
        "CORE_LOGIC_CHANGED": False,
        "TRADING_LOGIC_CHANGED": False,
        "NETWORK_CALLS_DURING_THIS_CAPABILITY": 0,
        "NETWORK_SESSION_STARTED": False,
        "NETWORK_SESSION_COUNT": 0,
        "CAMPAIGN_EXECUTED": False,
        "CAMPAIGN_OWNED_MAY_START_UNDER_FULL_GO": bool(full.get("campaign_may_start")),
        "CAMPAIGN_OWNED_MAY_START_UNDER_DELEGATED_CURSOR": bool(
            full_delegated.get("campaign_may_start")
        ),
        "CAMPAIGN_OWNED_MAY_START_WITHOUT_NETWORK_SESSION_GO": bool(
            no_go.get("campaign_may_start")
        ),
        "CAMPAIGN_OWNED_MAY_START_WITH_SINGLE_SESSION": bool(one_session.get("campaign_may_start")),
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        "STEP7_STARTED": False,
        "CAMPAIGN_ID": CAMPAIGN_ID,
        "TARGET_SESSION_ID_PREFIX": TARGET_SESSION_ID_PREFIX,
        "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN": (
            READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN and ok
        ),
        "READY_FOR_SEPARATE_OWNER_GO_DELEGATED_CURSOR_CAMPAIGN": (
            READY_FOR_SEPARATE_OWNER_GO_DELEGATED_CURSOR_CAMPAIGN and ok
        ),
        "CALL_GRAPH_BEFORE": list(CALL_GRAPH_BEFORE),
        "CALL_GRAPH_AFTER": list(CALL_GRAPH_AFTER),
        "REAL_TTY_OPERATOR_ENTRYPOINT_PATH": REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
        "DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH": DELEGATED_CURSOR_OPERATOR_ENTRYPOINT_PATH,
    }
    return GovernedStep7CampaignExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims=claims,
        mode=MODE_PROVE_IMPLEMENTATION_ONLY,
        terminal_class="IMPLEMENTATION_PROOF" if ok else "HARD_STOP",
        campaign_may_start=False,
        network_session_may_start=False,
        evidence={
            "path_dependency": path_dep,
            "path_alone": path_alone,
            "binding_forbid_real_network": binding_forbid,
            "harness": {
                "ok": harness.get("ok"),
                "blockers": harness.get("blockers"),
                "NETWORK_SESSION_STARTED": harness.get("NETWORK_SESSION_STARTED"),
            },
            "reuse": reuse,
            "hidden_pty_handoff": handoff,
            "delegated_cursor_secure_confirm_broker": delegated_broker,
            "boundary": boundary,
            "fetcher_proof": fetcher_proof,
            "gate_single_session": {k: v for k, v in one_session.items() if k != "notes"},
            "gate_without_network_session_go": {k: v for k, v in no_go.items() if k != "notes"},
            "gate_with_full_ephemeral_go": {k: v for k, v in full.items() if k != "notes"},
            "gate_with_delegated_cursor": {k: v for k, v in full_delegated.items() if k != "notes"},
            "campaign_invoke_symbol": PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "actual_repository_sha": actual_sha,
            "actual_config_digest": actual_cfg,
            "repo_root": str(repo_root) if repo_root else "",
        },
    )


def execute_governed_step7_campaign_offline_fail_closed_v1(
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
    planned_session_count: int = DEFAULT_PLANNED_SESSION_COUNT,
    allow_real_network_side_effects: bool = False,
    invoke_executor: bool = False,
    stdin_isatty: bool | None = None,
    getpass_fn: GetPassFn | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
) -> GovernedStep7CampaignExecutionResultV1:
    """Offline/governed execute. Never starts network in this implementation capability."""
    blockers: list[str] = []
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "CAMPAIGN_EXECUTION_OFFLINE_FAIL_CLOSED_DEFAULT=true",
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

    path_dep = consume_productive_campaign_path_dependency_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not path_dep.get("ok"):
        blockers.extend(list(path_dep.get("blockers") or []))

    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        owner_go=True,
        request_real_network=False,
        repo_root=repo_root,
    )
    handoff = prove_hidden_pty_confirm_handoff_binding_v1()

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
            if "HIDDEN_PTY_STDIN_NOT_TTY" in (acquired.get("blockers") or []):
                confirm_channel_ok = False
            blockers.extend(list(acquired.get("blockers") or []))
        notes.append("CONFIRM_TOKEN_PLAINTEXT_NOT_PERSISTED=true")

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    gate = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=public_md_only,
        authorization_valid=authorization_valid,
        confirm_token_valid=confirm_token_valid and confirm_channel_ok,
        planned_session_count=planned_session_count,
        productive_path_present=bool(path_dep.get("path_present")),
        productive_path_consumed=bool(path_dep.get("consumes_productive_path")),
        harness_bound=bool(harness.get("ok")),
        verifier_bound=True,
        repository_sha_match=sha_match,
        config_digest_match=cfg_match,
        stdin_isatty=stdin_isatty,
        hidden_confirm_handoff_reachable=bool(handoff.get("ok")) and confirm_channel_ok,
        private_endpoint_reachable=bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        auth_header_present=bool(boundary.get("AUTH_HEADER_PRESENT")),
        credential_path_reachable=bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        order_side_effect_reachable=bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        allow_real_network_side_effects=allow_real_network_side_effects,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    may_start = bool(gate.get("campaign_may_start"))
    notes.append(f"CAMPAIGN_MAY_START={may_start}")
    notes.append("NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY=true")

    if allow_real_network_side_effects or invoke_executor:
        blockers.append("NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY")

    return GovernedStep7CampaignExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": False,
            "NETWORK_SESSION_COUNT": 0,
            "CAMPAIGN_EXECUTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "HIDDEN_CONFIRM_HANDOFF_USED": False,
            "CAMPAIGN_MAY_START": may_start,
            "PRODUCTIVE_PATH_CONSUMED": bool(path_dep.get("consumes_productive_path")),
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
        planned_session_count=int(planned_session_count),
        evidence={
            "network_session_go": go,
            "gate": gate,
            "path_dependency": {
                "ok": path_dep.get("ok"),
                "path_present": path_dep.get("path_present"),
                "consumes_productive_path": path_dep.get("consumes_productive_path"),
            },
            "harness": {"ok": harness.get("ok")},
            "handoff": {"ok": handoff.get("ok")},
            "boundary": {
                "ok": boundary.get("ok"),
                "PUBLIC_MD_ONLY": boundary.get("PUBLIC_MD_ONLY"),
                "PRIVATE_ENDPOINT_REACHABLE": boundary.get("PRIVATE_ENDPOINT_REACHABLE"),
                "ORDER_SIDE_EFFECT_REACHABLE": boundary.get("ORDER_SIDE_EFFECT_REACHABLE"),
            },
        },
    )


def execute_governed_step7_campaign_v1(
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
    planned_session_count: int = DEFAULT_PLANNED_SESSION_COUNT,
    allow_real_network_side_effects: bool = False,
    invoke_executor: bool = False,
    stdin_isatty: bool | None = None,
    getpass_fn: GetPassFn | None = None,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    repo_root: Path | None = None,
    expected_capability_id: str = TARGET_CAMPAIGN_CAPABILITY_ID,
    wallclock_runner: Callable[..., Any] | None = None,
    wallclock_kwargs: Mapping[str, Any] | None = None,
    campaign_start_state: dict[str, Any] | None = None,
    runtime_overrides: Mapping[str, Any] | None = None,
    authorization_channel: str | None = None,
    delegated_confirm_latch: DelegatedCursorSecureConfirmLatchV1 | None = None,
    delegated_confirm_token_file: Path | None = None,
    head_equals_origin_main: bool | None = None,
    tracked_worktree_clean: bool | None = None,
) -> GovernedStep7CampaignExecutionResultV1:
    """Productive Step-7 campaign invoke under TARGET_CAMPAIGN_CAPABILITY_ID.

    Multi-session wallclock start only when all ephemeral gates pass and
    ``invoke_executor`` + ``allow_real_network_side_effects`` are set.
    Confirm channels:
      REAL_TTY_HUMAN_CONFIRM (default) — Hidden-PTY getpass
      DELEGATED_CURSOR_SECURE_CONFIRM — EPHEMERAL_EXECUTION_LATCH broker
    Tests inject ``wallclock_runner`` doubles; prove/materialize never call this
    with a real network runner.
    """
    blockers: list[str] = []
    channel = str(authorization_channel or DEFAULT_AUTHORIZATION_CHANNEL)
    notes = [
        f"CAPABILITY_ID={CAPABILITY_ID}",
        f"TARGET_CAMPAIGN_CAPABILITY_ID={TARGET_CAMPAIGN_CAPABILITY_ID}",
        f"PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL={PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL}",
        f"AUTHORIZATION_CHANNEL={channel}",
        f"TOKEN_ROLE={CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH}",
        "CAMPAIGN_INVOKE_EDGE_ACTIVE=true",
        "BINDING_ONLY_EXECUTOR_NOT_USED=true",
        "PATH_IMPLEMENTATION_NOT_USED_AS_START_OWNER=true",
        "TOKEN_IS_NOT_HUMAN_TTY_PRESENCE_PROOF=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))

    if not is_target_campaign_capability_id_v1(expected_capability_id):
        blockers.append("WRONG_CAPABILITY_ID")

    go = bind_ephemeral_network_session_go_v1(
        network_session_go=network_session_go, environ=environ
    )
    if not go.get("ok"):
        blockers.extend(list(go.get("blockers") or []))

    actual_sha = str(actual_repository_sha or expected_repository_sha)
    actual_cfg = str(actual_config_digest or expected_config_digest)
    sha_match = actual_sha == str(expected_repository_sha)
    cfg_match = actual_cfg == str(expected_config_digest)

    path_dep = consume_productive_campaign_path_dependency_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    if not path_dep.get("ok"):
        blockers.extend(list(path_dep.get("blockers") or []))

    harness = run_step7_campaign_harness_binding_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        owner_go=True,
        request_real_network=False,
        repo_root=repo_root,
    )
    if not harness.get("ok"):
        blockers.extend(list(harness.get("blockers") or []))

    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    delegated_broker = prove_delegated_cursor_secure_confirm_broker_binding_v1()

    confirm_channel_ok = True
    confirm_token_consumed = False
    confirm_fingerprint = ""
    real_tty_verified = False
    delegated_secure_confirm_verified = False
    temp_secret_cleaned = True
    acquired: dict[str, Any] = {"ok": False, "blockers": [], "fingerprint": ""}
    head_ok = False
    worktree_ok = False

    if channel == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM:
        if stdin_isatty is True and getpass_fn is not None:
            acquired = acquire_confirm_token_via_hidden_pty_v1(
                getpass_fn=getpass_fn,
                argv=argv,
                environ=environ,
                require_real_tty=True,
                stdin_isatty=stdin_isatty,
            )
            if not acquired.get("ok"):
                confirm_channel_ok = False
                blockers.extend(list(acquired.get("blockers") or []))
                blockers.append("CONFIRM_TOKEN_FAILURE")
            else:
                confirm_token_consumed = True
                confirm_fingerprint = str(acquired.get("fingerprint") or "")
                real_tty_verified = True
                notes.append("HIDDEN_CONFIRM_HANDOFF_USED=true")
                notes.append("CONFIRM_TOKEN_PLAINTEXT_NOT_PERSISTED=true")
        elif stdin_isatty is True and getpass_fn is None:
            confirm_channel_ok = False
            blockers.append("HIDDEN_CONFIRM_CHANNEL_MISSING")
        elif confirm_token_valid and stdin_isatty is not True:
            blockers.extend(["REAL_TTY_REQUIRED", "HIDDEN_PTY_STDIN_NOT_TTY"])
            confirm_channel_ok = False
    elif channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM:
        repo_binding: dict[str, Any] = {
            "ok": False,
            "HEAD_EQUALS_ORIGIN_MAIN": False,
            "tracked_worktree_clean": False,
        }
        if head_equals_origin_main is not None and tracked_worktree_clean is not None:
            head_ok = bool(head_equals_origin_main)
            worktree_ok = bool(tracked_worktree_clean)
            if not head_ok:
                blockers.append("HEAD_NOT_EQUAL_ORIGIN_MAIN")
            if not worktree_ok:
                blockers.append("TRACKED_WORKTREE_DIRTY")
            repo_binding = {
                "ok": head_ok and worktree_ok,
                "HEAD_EQUALS_ORIGIN_MAIN": head_ok,
                "tracked_worktree_clean": worktree_ok,
                "blockers": [
                    b
                    for b in blockers
                    if b
                    in {
                        "HEAD_NOT_EQUAL_ORIGIN_MAIN",
                        "TRACKED_WORKTREE_DIRTY",
                    }
                ],
            }
        elif repo_root is not None:
            repo_binding = evaluate_delegated_cursor_repository_binding_v1(
                repo_root=Path(repo_root)
            )
            head_ok = bool(repo_binding.get("HEAD_EQUALS_ORIGIN_MAIN"))
            worktree_ok = bool(repo_binding.get("tracked_worktree_clean"))
            if not repo_binding.get("ok"):
                blockers.extend(list(repo_binding.get("blockers") or []))
        else:
            blockers.append("REPOSITORY_ROOT_REQUIRED_FOR_DELEGATED_CURSOR")

        try:
            acquired = acquire_delegated_cursor_secure_confirm_v1(
                latch=delegated_confirm_latch,
                token_file=delegated_confirm_token_file,
                argv=argv,
                environ=environ,
            )
        except Exception as exc:  # noqa: BLE001
            confirm_channel_ok = False
            blockers.append(f"DELEGATED_CONFIRM_FAILURE:{type(exc).__name__}")
            acquired = {"ok": False, "blockers": blockers[-1:], "fingerprint": ""}
            if delegated_confirm_latch is not None:
                try:
                    delegated_confirm_latch.cleanup_temp_secret_v1()
                    delegated_confirm_latch.clear_v1()
                except Exception:
                    pass
            temp_secret_cleaned = True
        else:
            temp_secret_cleaned = bool(acquired.get("temp_secret_cleaned", True))
            if not acquired.get("ok"):
                confirm_channel_ok = False
                blockers.extend(list(acquired.get("blockers") or []))
                blockers.append("CONFIRM_TOKEN_FAILURE")
            else:
                confirm_token_consumed = True
                confirm_fingerprint = str(acquired.get("fingerprint") or "")
                delegated_secure_confirm_verified = True
                notes.append("DELEGATED_CURSOR_SECURE_CONFIRM_USED=true")
                notes.append("CONFIRM_TOKEN_PLAINTEXT_NOT_PERSISTED=true")
                notes.append("CONFIRM_TOKEN_DIGEST_ONLY=true")
        if not delegated_broker.get("ok"):
            blockers.append("DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_BINDING_FAILED")
            confirm_channel_ok = False
    else:
        blockers.append("UNKNOWN_AUTHORIZATION_CHANNEL")
        confirm_channel_ok = False

    boundary = prove_public_md_only_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend(list(boundary.get("blockers") or []))

    hidden_reachable = (
        bool(handoff.get("ok")) and confirm_channel_ok
        if channel == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM
        else True
    )
    gate = evaluate_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=owner_go,
        operator_authorization_explicit=operator_authorization_explicit,
        network_session_go=bool(go.get("network_session_go")),
        public_md_only=public_md_only,
        authorization_valid=authorization_valid,
        confirm_token_valid=bool(
            confirm_token_valid and confirm_channel_ok and confirm_token_consumed
        ),
        planned_session_count=planned_session_count,
        productive_path_present=bool(path_dep.get("path_present")),
        productive_path_consumed=bool(path_dep.get("consumes_productive_path")),
        harness_bound=bool(harness.get("ok")),
        verifier_bound=True,
        repository_sha_match=sha_match,
        config_digest_match=cfg_match,
        stdin_isatty=stdin_isatty,
        hidden_confirm_handoff_reachable=hidden_reachable,
        private_endpoint_reachable=bool(boundary.get("PRIVATE_ENDPOINT_REACHABLE")),
        auth_header_present=bool(boundary.get("AUTH_HEADER_PRESENT")),
        credential_path_reachable=bool(boundary.get("CREDENTIAL_PATH_REACHABLE")),
        order_side_effect_reachable=bool(boundary.get("ORDER_SIDE_EFFECT_REACHABLE")),
        allow_real_network_side_effects=allow_real_network_side_effects,
        authorization_channel=channel,
        delegated_secure_confirm_verified=delegated_secure_confirm_verified,
        head_equals_origin_main=head_ok
        if channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
        else True,
        tracked_worktree_clean=worktree_ok
        if channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
        else True,
    )
    if not gate.get("ok"):
        blockers.extend(list(gate.get("blockers") or []))

    may_start = bool(gate.get("campaign_may_start"))
    notes.append(f"CAMPAIGN_MAY_START={may_start}")

    start_state = campaign_start_state if campaign_start_state is not None else {}
    wallclock_invoked_count = int(start_state.get("wallclock_invoked_count") or 0)
    completed_session_count = int(start_state.get("completed_session_count") or 0)
    invoke_result: dict[str, Any] | None = None
    network_session_started = False

    if (
        may_start
        and invoke_executor
        and allow_real_network_side_effects
        and confirm_token_consumed
        and not blockers
    ):
        invoke_result = invoke_step7_productive_campaign_sessions_v1(
            planned_session_count=planned_session_count,
            runtime_overrides=dict(runtime_overrides or {}),
            wallclock_kwargs=wallclock_kwargs,
            wallclock_runner=wallclock_runner,
            campaign_start_state=start_state,
            allow_real_network=True,
            target_campaign_capability_id=expected_capability_id,
        )
        if not invoke_result.get("ok"):
            blockers.extend(list(invoke_result.get("blockers") or []))
        else:
            notes.extend(list(invoke_result.get("notes") or []))
            wallclock_invoked_count = int(invoke_result.get("wallclock_invoked_count") or 0)
            completed_session_count = int(invoke_result.get("completed_session_count") or 0)
            if wallclock_runner is not None:
                network_session_started = False
                notes.append("TEST_DOUBLE_INVOKE_DOES_NOT_CLAIM_REAL_NETWORK_SESSION=true")
            else:
                network_session_started = bool(invoke_result.get("network_session_started"))
    elif invoke_executor and allow_real_network_side_effects:
        notes.append("START_INVOKE_SKIPPED_DUE_TO_GATE_OR_CONFIRM_FAILURE=true")
    elif invoke_executor and not allow_real_network_side_effects:
        notes.append("INVOKE_WITHOUT_ALLOW_REAL_NETWORK_DOES_NOT_START=true")

    ok = (
        may_start
        and invoke_result is not None
        and multi_session_requirement_satisfied_v1(completed_session_count)
        and wallclock_invoked_count == int(planned_session_count)
        and not blockers
    )
    terminal = "CAMPAIGN_START_INVOKE_OK" if ok else "HARD_STOP"

    return GovernedStep7CampaignExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes,
        claims={
            "NETWORK_SESSION_STARTED": network_session_started,
            "NETWORK_SESSION_COUNT": completed_session_count if network_session_started else 0,
            "WALLCLOCK_INVOKED_COUNT": wallclock_invoked_count,
            "COMPLETED_SESSION_COUNT": completed_session_count,
            "PLANNED_SESSION_COUNT": int(planned_session_count),
            "CAMPAIGN_EXECUTED": bool(ok and network_session_started),
            "AUTHORIZATION_CONSUMED": False,
            "AUTHORIZATION_CHANNEL": channel,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "REAL_TTY_VERIFIED": real_tty_verified,
            "DELEGATED_SECURE_CONFIRM_VERIFIED": delegated_secure_confirm_verified,
            "CONFIRM_TOKEN_MINTED": channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM
            and bool(delegated_confirm_latch is not None or delegated_confirm_token_file),
            "CONFIRM_TOKEN_CONSUMED": confirm_token_consumed,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "CONFIRM_TOKEN_DIGEST_ONLY": True,
            "TEMP_SECRET_CLEANED": temp_secret_cleaned,
            "HIDDEN_CONFIRM_HANDOFF_USED": bool(
                confirm_token_consumed and channel == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM
            ),
            "CAMPAIGN_MAY_START": may_start,
            "PRODUCTIVE_PATH_CONSUMED": bool(path_dep.get("consumes_productive_path")),
            "STEP7_CAMPAIGN_HARNESS_BOUND": bool(harness.get("ok")),
            "STEP7_CAMPAIGN_VERIFIER_PRESENT": True,
            "PUBLIC_MD_FETCHER_BOUND": True,
            "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT": True,
            "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE": True,
            "BINDING_ONLY_NOT_USED_AS_CAMPAIGN_OWNER": True,
            "TARGET_CAMPAIGN_CAPABILITY_ID": TARGET_CAMPAIGN_CAPABILITY_ID,
            "MULTI_SESSION_REQUIREMENT_EXPRESSION": MULTI_SESSION_REQUIREMENT_EXPRESSION,
            "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
            "NETWORK_CALLS": 0 if wallclock_runner is not None else wallclock_invoked_count,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "confirm_token_fingerprint": confirm_fingerprint,
            "repo_root": str(repo_root) if repo_root else "",
        },
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        terminal_class=terminal,
        campaign_may_start=may_start,
        network_session_may_start=may_start,
        network_session_started=network_session_started,
        network_session_count=completed_session_count if network_session_started else 0,
        planned_session_count=int(planned_session_count),
        completed_session_count=completed_session_count,
        network_calls=0 if wallclock_runner is not None else wallclock_invoked_count,
        confirm_token_minted=bool(
            channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM and confirm_token_consumed
        ),
        confirm_token_consumed=confirm_token_consumed,
        authorization_consumed=False,
        evidence={
            "network_session_go": go,
            "gate": gate,
            "path_dependency": {
                "ok": path_dep.get("ok"),
                "path_present": path_dep.get("path_present"),
                "consumes_productive_path": path_dep.get("consumes_productive_path"),
            },
            "harness": {"ok": harness.get("ok")},
            "handoff": {"ok": handoff.get("ok")},
            "delegated_broker": {"ok": delegated_broker.get("ok")},
            "boundary": {
                "ok": boundary.get("ok"),
                "PUBLIC_MD_ONLY": boundary.get("PUBLIC_MD_ONLY"),
                "PRIVATE_ENDPOINT_REACHABLE": boundary.get("PRIVATE_ENDPOINT_REACHABLE"),
                "ORDER_SIDE_EFFECT_REACHABLE": boundary.get("ORDER_SIDE_EFFECT_REACHABLE"),
            },
            "invoke": {
                "ok": bool((invoke_result or {}).get("ok")) if invoke_result else False,
                "wallclock_invoked_count": wallclock_invoked_count,
                "completed_session_count": completed_session_count,
                "public_md_fetcher_bound": bool(
                    (invoke_result or {}).get("public_md_fetcher_bound")
                ),
                "session_results": list((invoke_result or {}).get("session_results") or []),
            },
            "confirm_token": redact_confirm_token_mapping_v1(
                {
                    "fingerprint": confirm_fingerprint,
                    "consumed": confirm_token_consumed,
                    "acquired_ok": bool(acquired.get("ok")),
                    "AUTHORIZATION_CHANNEL": channel,
                    "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
                    "REAL_TTY_VERIFIED": real_tty_verified,
                    "DELEGATED_SECURE_CONFIRM_VERIFIED": delegated_secure_confirm_verified,
                    "temp_secret_cleaned": temp_secret_cleaned,
                }
            ),
        },
    )
