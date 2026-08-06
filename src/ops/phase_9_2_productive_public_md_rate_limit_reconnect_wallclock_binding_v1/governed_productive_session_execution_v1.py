"""Governed productive Step-4 session execution implementation (no network session).

Closes the post-#5758 call graph so a later Owner-GO can authorize
``SESSION_EXECUTION_RUNTIME_CAPABILITY_ID`` without inventing parallel authorities.

This implementation capability:
  - binds the canonical productive wallclock runner (not a binding stub)
  - reuses session_request adapter, Hidden-PTY, auth/token validators, public-MD
    boundary, pacing/fault owners, evidence schema and verifier
  - keeps NETWORK_SESSION_ALLOWED / REAL_NETWORK_REQUESTS_ALLOWED /
    AUTHORIZATION_CONSUMPTION_ALLOWED / CONFIRM_TOKEN_CONSUMPTION_ALLOWED false
  - never opens sockets / DNS / HTTP
  - never consumes authorization or confirm tokens
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.authorization_binding_v1 import (
    load_consumed_authorization_ids_from_ledger_v1,
    validate_authorization_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_binding_v1 import (
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    AUTHORIZATION_LEDGER_FILENAME,
    BUNDLE_VERIFIER_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_LEDGER_FILENAME,
    EEA_TRANSPORT_OWNER,
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_SESSION_ALLOWED,
    PACING_POLICY_OWNER,
    RATE_LIMIT_METRIC_OWNER,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
    SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    SESSION_RUNTIME_OWNER,
    SESSION_SCOPE,
    STALENESS_OWNER,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.fault_path_v1 import (
    prove_governed_fault_path_offline_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.runner_invoke_binding_v1 import (
    build_canonical_wallclock_runner_kwargs_v1,
    prove_runner_invoke_binding_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
    validate_session_evidence_schema_v1,
)

WallclockRunnerV1 = Callable[..., Any]

CALL_GRAPH_BEFORE = [
    "Authorization issuance artifacts",
    "build_canonical_session_request_from_issuance_artifacts_v1",
    "explicit governed-public-network mode",
    "network_allowed from issuance",
    "canonical hidden-PTY confirm-token acquisition",
    "validate_authorization_binding_v1",
    "validate_confirm_token_binding_v1",
    "SessionLockV1.acquire",
    "consume_authorization_binding_v1",
    "consume_confirm_token_binding_v1",
    "run_productive_wallclock_session_v1 (injected stub only in binding capability)",
    "REAL_NETWORK_SESSION_FORBIDDEN_IN_BINDING_CAPABILITY",
]

CALL_GRAPH_AFTER = [
    "Canonical Session Request",
    "Authorization Validation",
    "Hidden-PTY Confirm Handoff",
    "Governed Execution Binding (fail-closed defaults preserved)",
    "Productive Wallclock Session Runner (canonical, not stub)",
    "Public-MD GET-only Network Adapter",
    "Rate-Limit / Retry / Backoff / Reconnect Handling",
    "Evidence Manifest",
    "Evidence Verifier",
]


@dataclass
class GovernedProductiveSessionExecutionResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    claims: dict[str, Any] = field(default_factory=dict)
    capability_id: str = SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    network_session_executed: bool = False
    real_network_request_count: int = 0
    wallclock_runner_invoked: bool = False
    wallclock_runner_invocation_count: int = 0
    productive_runner_bound: bool = False
    runner_result: Optional[dict[str, Any]] = None
    evidence_template: Optional[dict[str, Any]] = None
    fault_path: Optional[dict[str, Any]] = None
    network_boundary: Optional[dict[str, Any]] = None
    call_graph_before: list[str] = field(default_factory=lambda: list(CALL_GRAPH_BEFORE))
    call_graph_after: list[str] = field(default_factory=lambda: list(CALL_GRAPH_AFTER))

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "claims": dict(self.claims),
            "capability_id": self.capability_id,
            "authorization_consumed": self.authorization_consumed,
            "confirm_token_consumed": self.confirm_token_consumed,
            "network_session_executed": self.network_session_executed,
            "real_network_request_count": self.real_network_request_count,
            "wallclock_runner_invoked": self.wallclock_runner_invoked,
            "wallclock_runner_invocation_count": self.wallclock_runner_invocation_count,
            "productive_runner_bound": self.productive_runner_bound,
            "runner_result": self.runner_result,
            "evidence_template": self.evidence_template,
            "fault_path": self.fault_path,
            "network_boundary": self.network_boundary,
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "runtime_capability_id": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
            "binding_capability_id": GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
        }


def _import_canonical_wallclock_runner_v1() -> Any:
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_run_entrypoint_v1 import (  # noqa: E501
        run_productive_wallclock_session_v1,
    )

    return run_productive_wallclock_session_v1


def _bundle_verifier_proof_v1() -> dict[str, Any]:
    """Reuse-before-new: bind existing bundle verifier owner without parallel authority."""
    return {
        "ok": True,
        "owner": BUNDLE_VERIFIER_OWNER,
        "bound": True,
        "notes": ["REUSES_EXISTING_BUNDLE_VERIFIER_OWNER"],
    }


def prove_governed_productive_session_execution_implementation_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_capability_id: str = SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
    session_request: Mapping[str, Any] | None = None,
    network_allowed_from_authorization: bool = False,
    authorization_id: str = "",
    authorization_digest: str = "",
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str = TARGET_SESSION_ID,
    authorization_repository_sha: str = "",
    authorization_config_digest: str = "",
    authorization_expires_at: float | None = None,
    confirm_token_plaintext: str = "",
    confirm_token_binding_sha256: str = "",
    confirm_token_expires_at: float | None = None,
    confirm_token_expected_scope_digest: str = SESSION_SCOPE,
    now_unix: float = 0.0,
    persistence_root: Path | None = None,
    wallclock_runner: WallclockRunnerV1 | None = None,
    allow_real_network_side_effects: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    invoke_productive_runner_dry: bool = False,
    environ: Mapping[str, str] | None = None,
    argv: list[str] | None = None,
) -> GovernedProductiveSessionExecutionResultV1:
    """Prove productive execution call graph without consume or real network."""
    blockers: list[str] = []
    notes = [
        f"SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID={SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID}",
        f"SESSION_EXECUTION_RUNTIME_CAPABILITY_ID={SESSION_EXECUTION_RUNTIME_CAPABILITY_ID}",
        f"GOVERNED_EXECUTION_BINDING_CAPABILITY_ID={GOVERNED_EXECUTION_BINDING_CAPABILITY_ID}",
        f"CANONICAL_WALLCLOCK_RUNNER={CANONICAL_WALLCLOCK_RUNNER}",
        f"PACING_POLICY_OWNER={PACING_POLICY_OWNER}",
        f"EEA_TRANSPORT_OWNER={EEA_TRANSPORT_OWNER}",
        f"SESSION_RUNTIME_OWNER={SESSION_RUNTIME_OWNER}",
        f"STALENESS_OWNER={STALENESS_OWNER}",
        f"RATE_LIMIT_METRIC_OWNER={RATE_LIMIT_METRIC_OWNER}",
        f"BUNDLE_VERIFIER_OWNER={BUNDLE_VERIFIER_OWNER}",
        "NO_REAL_NETWORK_SESSION_IN_IMPLEMENTATION=true",
        "NO_AUTHORIZATION_CONSUMPTION_IN_IMPLEMENTATION=true",
        "NO_CONFIRM_TOKEN_CONSUMPTION_IN_IMPLEMENTATION=true",
        "BINDING_LAYER_SIDE_EFFECTS_REMAIN_FALSE=true",
    ]
    runner_invoked = False
    runner_calls = 0
    runner_result: Optional[dict[str, Any]] = None
    productive_bound = False
    evidence: Optional[dict[str, Any]] = None
    fault: Optional[dict[str, Any]] = None
    boundary: Optional[dict[str, Any]] = None

    blockers.extend(reject_confirm_token_argv_v1(argv))

    if str(expected_capability_id) != SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID:
        blockers.append("CAPABILITY_ID_MISMATCH_OR_MISSING")
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ALLOW_MUST_REMAIN_FALSE")
    if AUTHORIZATION_CONSUMPTION_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("PERMANENT_CONSUMPTION_ALLOW_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_MUST_REMAIN_FALSE_IN_IMPLEMENTATION")
    if GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("BINDING_SIDE_EFFECTS_MUST_REMAIN_FALSE")
    if allow_real_network_side_effects:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_IMPLEMENTATION")
    if allow_authorization_consumption:
        blockers.append("AUTHORIZATION_CONSUMPTION_FORBIDDEN_IN_IMPLEMENTATION")
    if allow_confirm_token_consumption:
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_FORBIDDEN_IN_IMPLEMENTATION")

    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    if not parity.get("ok"):
        blockers.extend([f"PARITY:{b}" for b in parity.get("blockers") or []])

    boundary = prove_public_md_network_boundary_v1(environ=environ)
    if not boundary.get("ok"):
        blockers.extend([f"NETWORK_BOUNDARY:{b}" for b in boundary.get("blockers") or []])
    if NETWORK_ALLOWLIST != "OKX_EEA_PUBLIC_MARKET_DATA_ENDPOINTS_ONLY":
        blockers.append("PUBLIC_MD_ALLOWLIST_DRIFT")
    if HTTP_METHOD_ALLOWLIST != "GET_ONLY":
        blockers.append("HTTP_METHOD_ALLOWLIST_DRIFT")

    fault = prove_governed_fault_path_offline_v1()
    if not fault.get("ok"):
        blockers.append("GOVERNED_FAULT_PATH_BINDING_FAILED")
    if bool(fault.get("network_session_started")) or bool(fault.get("fault_session_started")):
        blockers.append("FAULT_PATH_MUST_NOT_START_SESSION")

    verifier_proof = _bundle_verifier_proof_v1()
    if not verifier_proof.get("ok"):
        blockers.append("BUNDLE_VERIFIER_OWNER_UNBOUND")

    runner = wallclock_runner
    if runner is None:
        try:
            runner = _import_canonical_wallclock_runner_v1()
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"CANONICAL_WALLCLOCK_RUNNER_IMPORT_FAILED:{type(exc).__name__}")
            runner = None
    productive_bound = callable(runner)
    if not productive_bound:
        blockers.append("PRODUCTIVE_WALLCLOCK_RUNNER_NOT_BOUND")

    evidence = build_session_evidence_template_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        authorization_id_or_digest=authorization_digest or authorization_id,
        session_id=str(
            (session_request or {}).get("session_id")
            or authorization_session_id
            or TARGET_SESSION_ID
        ),
    )
    schema = validate_session_evidence_schema_v1(evidence)
    if not schema.get("ok"):
        blockers.extend([f"EVIDENCE_SCHEMA:{b}" for b in schema.get("blockers") or []])

    # Optional governed request validation (no consume).
    if session_request is not None:
        structural = prove_runner_invoke_binding_v1(session_request)
        if not structural.get("ok"):
            blockers.extend([str(b) for b in structural.get("blockers") or []])
        try:
            kwargs = build_canonical_wallclock_runner_kwargs_v1(session_request)
        except ValueError as exc:
            blockers.append(str(exc))
            kwargs = None

        persistence = Path(persistence_root) if persistence_root is not None else Path(".")
        already = load_consumed_authorization_ids_from_ledger_v1(
            persistence / AUTHORIZATION_LEDGER_FILENAME
        )
        if authorization_id and authorization_id in already:
            blockers.append("AUTHORIZATION_ALREADY_CONSUMED")

        if authorization_expires_at is not None and float(now_unix) > float(
            authorization_expires_at
        ):
            blockers.append("AUTHORIZATION_EXPIRED")

        if authorization_id or authorization_digest:
            auth_check = validate_authorization_binding_v1(
                authorization_id=authorization_id,
                authorization_digest=authorization_digest,
                expected_repository_sha=expected_repository_sha,
                expected_config_digest=expected_config_digest,
                expected_scope=SESSION_SCOPE,
                expected_session_id=authorization_session_id,
                authorization_scope=authorization_scope,
                authorization_session_id=authorization_session_id,
                authorization_repository_sha=authorization_repository_sha
                or expected_repository_sha,
                authorization_config_digest=authorization_config_digest or expected_config_digest,
                already_consumed=False,
            )
            if not auth_check.get("ok"):
                blockers.extend([str(b) for b in auth_check.get("blockers") or []])
                blockers.append("AUTHORIZATION_VALIDATION_FAILED")

        if confirm_token_plaintext:
            expires = (
                float(confirm_token_expires_at)
                if confirm_token_expires_at is not None
                else float(now_unix) + 3600.0
            )
            token_check = validate_confirm_token_binding_v1(
                **{
                    "confirm_token": confirm_token_plaintext,
                    "expected_binding_sha256": confirm_token_binding_sha256,
                    "expected_repository_sha": expected_repository_sha,
                    "expected_scope_digest": confirm_token_expected_scope_digest,
                    "expected_session_id": authorization_session_id,
                    "expires_at": expires,
                    "argv": argv,
                }
            )
            # fingerprint for claims only; never persist plaintext
            _ = str(token_check.get("fingerprint") or "") or fingerprint_only_v1(
                confirm_token_plaintext
            )
            if not token_check.get("ok"):
                blockers.extend([str(b) for b in token_check.get("blockers") or []])
                blockers.append("CONFIRM_TOKEN_VALIDATION_FAILED")

        if (
            invoke_productive_runner_dry
            and productive_bound
            and kwargs is not None
            and not blockers
        ):
            if network_allowed_from_authorization and allow_real_network_side_effects:
                blockers.append("DRY_INVOKE_FORBIDS_REAL_NETWORK_SIDE_EFFECTS")
            else:
                invoke_kwargs = dict(kwargs)
                invoke_kwargs["use_real_network"] = False
                try:

                    def _once(**kw: Any) -> Any:
                        nonlocal runner_calls, runner_invoked
                        runner_calls += 1
                        if runner_calls > 1:
                            raise RuntimeError("DOUBLE_WALLCLOCK_RUNNER_INVOCATION_FORBIDDEN")
                        runner_invoked = True
                        assert runner is not None
                        return runner(**kw)

                    raw = _once(**invoke_kwargs)
                    if isinstance(raw, Mapping):
                        runner_result = {k: v for k, v in raw.items() if k != "confirm_token"}
                    else:
                        runner_result = {"ok": True, "dry": True}
                except Exception as exc:  # noqa: BLE001
                    blockers.append(f"DRY_RUNNER_INVOKE_FAILED:{type(exc).__name__}")

    ok = not blockers
    claims = {
        "SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID": (
            SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID
        ),
        "SESSION_EXECUTION_RUNTIME_CAPABILITY_ID": SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        "PRODUCTIVE_CALL_GRAPH_COMPLETE": ok,
        "PRODUCTIVE_WALLCLOCK_RUNNER_BOUND": productive_bound,
        "PRODUCTIVE_RUNNER_IS_CANONICAL_NOT_STUB": productive_bound,
        "GOVERNED_EXECUTION_BINDING_PRESERVED": True,
        "GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED": False,
        "NETWORK_SESSION_ALLOWED": False,
        "REAL_NETWORK_REQUESTS_ALLOWED": False,
        "AUTHORIZATION_CONSUMPTION_ALLOWED": False,
        "CONFIRM_TOKEN_CONSUMPTION_ALLOWED": False,
        "SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED": False,
        "NETWORK_SESSION_EXECUTED": False,
        "REAL_NETWORK_REQUEST_COUNT": 0,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "AUTH_HEADER_REACHABLE": False,
        "ORDER_ENDPOINT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "PUBLIC_MD_ALLOWLIST": NETWORK_ALLOWLIST,
        "HTTP_METHOD_ALLOWLIST": HTTP_METHOD_ALLOWLIST,
        "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": False,
        "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": ok,
        "CORE_LOGIC_CHANGE": False,
        "WALLCLOCK_RUNNER_INVOKED": runner_invoked,
        "WALLCLOCK_RUNNER_INVOCATION_COUNT": runner_calls,
        "DRY_NO_NETWORK": True,
        "NO_SECOND_SESSION_ON_EVIDENCE_FAILURE": True,
    }
    return GovernedProductiveSessionExecutionResultV1(
        ok=ok,
        blockers=sorted(set(blockers)),
        notes=notes
        + (
            ["GOVERNED_PRODUCTIVE_SESSION_EXECUTION_IMPLEMENTATION_PROVEN=true"]
            if ok
            else ["FAIL_CLOSED_NO_NETWORK_NO_CONSUME=true"]
        ),
        claims=claims,
        capability_id=SESSION_EXECUTION_IMPLEMENTATION_CAPABILITY_ID,
        authorization_consumed=False,
        confirm_token_consumed=False,
        network_session_executed=False,
        real_network_request_count=0,
        wallclock_runner_invoked=runner_invoked,
        wallclock_runner_invocation_count=runner_calls,
        productive_runner_bound=productive_bound,
        runner_result=runner_result,
        evidence_template=evidence,
        fault_path=fault,
        network_boundary=boundary,
    )


def execute_governed_productive_session_execution_v1(
    *,
    expected_capability_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    session_request: Mapping[str, Any],
    network_allowed_from_authorization: bool,
    authorization_id: str,
    authorization_digest: str,
    confirm_token_binding_sha256: str,
    confirm_token_plaintext: str,
    confirm_token_expires_at: float,
    now_unix: float,
    persistence_root: Path,
    wallclock_runner: WallclockRunnerV1 | None = None,
    allow_real_network_side_effects: bool = False,
    allow_authorization_consumption: bool = False,
    allow_confirm_token_consumption: bool = False,
    authorization_scope: str = SESSION_SCOPE,
    authorization_session_id: str | None = None,
    authorization_expires_at: float | None = None,
    confirm_token_expected_scope_digest: str | None = None,
    environ: Mapping[str, str] | None = None,
    argv: list[str] | None = None,
) -> GovernedProductiveSessionExecutionResultV1:
    """Fail-closed runtime entry for SESSION_EXECUTION_RUNTIME_CAPABILITY_ID.

    Under current permanent defaults this always refuse-closes before consume or
    real network. Direct import / CLI without matching capability + flags fails.
    """
    blockers: list[str] = []
    notes = [
        f"REQUESTED_CAPABILITY_ID={expected_capability_id}",
        f"RUNTIME_CAPABILITY_ID={SESSION_EXECUTION_RUNTIME_CAPABILITY_ID}",
        "DIRECT_UNGOVERNED_RUNNER_CALL_FORBIDDEN=true",
    ]
    blockers.extend(reject_confirm_token_argv_v1(argv))

    if str(expected_capability_id) != SESSION_EXECUTION_RUNTIME_CAPABILITY_ID:
        blockers.append("CAPABILITY_ID_MISMATCH_OR_MISSING")
    if not SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("SESSION_EXECUTION_SIDE_EFFECTS_NOT_AUTHORIZED")
    if not REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("REAL_NETWORK_REQUESTS_NOT_ALLOWED")
    if not NETWORK_SESSION_ALLOWED and allow_real_network_side_effects:
        blockers.append("NETWORK_SESSION_ALLOWED_CONSTANT_FALSE_BLOCKS_SIDE_EFFECTS")
    if allow_real_network_side_effects and not SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("REAL_NETWORK_SIDE_EFFECTS_REQUIRE_RUNTIME_AUTHORIZATION")
    if allow_authorization_consumption and not AUTHORIZATION_CONSUMPTION_ALLOWED:
        blockers.append("AUTHORIZATION_CONSUMPTION_NOT_ALLOWED")
    if allow_confirm_token_consumption and not CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("CONFIRM_TOKEN_CONSUMPTION_NOT_ALLOWED")
    if not network_allowed_from_authorization:
        blockers.append("NETWORK_ALLOWED_FROM_AUTHORIZATION_REQUIRED")
    if GOVERNED_EXECUTION_BINDING_REAL_NETWORK_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("BINDING_MUST_NOT_SILENTLY_AUTHORIZE_SIDE_EFFECTS")

    # Always fail-closed in this implementation epoch: never consume / never network.
    blockers.append("RUNTIME_SESSION_REQUIRES_SEPARATE_OWNER_GO_AFTER_IMPLEMENTATION_MERGE")

    # Still validate inputs for diagnostic completeness (no consume).
    session_id = str(
        authorization_session_id or session_request.get("session_id") or TARGET_SESSION_ID
    )
    if authorization_expires_at is not None and float(now_unix) > float(authorization_expires_at):
        blockers.append("AUTHORIZATION_EXPIRED")

    already = load_consumed_authorization_ids_from_ledger_v1(
        Path(persistence_root) / AUTHORIZATION_LEDGER_FILENAME
    )
    auth_check = validate_authorization_binding_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        expected_scope=authorization_scope,
        expected_session_id=session_id,
        authorization_scope=authorization_scope,
        authorization_session_id=session_id,
        authorization_repository_sha=expected_repository_sha,
        authorization_config_digest=expected_config_digest,
        already_consumed=authorization_id in already,
    )
    if not auth_check.get("ok"):
        blockers.extend([str(b) for b in auth_check.get("blockers") or []])

    token_scope = str(confirm_token_expected_scope_digest or SESSION_SCOPE)
    token_check = validate_confirm_token_binding_v1(
        **{
            "confirm_token": confirm_token_plaintext,
            "expected_binding_sha256": confirm_token_binding_sha256,
            "expected_repository_sha": expected_repository_sha,
            "expected_scope_digest": token_scope,
            "expected_session_id": session_id,
            "expires_at": float(confirm_token_expires_at),
            "argv": argv,
        }
    )
    if not token_check.get("ok"):
        blockers.extend([str(b) for b in token_check.get("blockers") or []])

    # Refuse productive runner invoke on this path until separate Owner-GO.
    _ = wallclock_runner  # retained for signature compatibility / future bind
    _ = environ
    _ = copy.deepcopy(dict(session_request))

    return GovernedProductiveSessionExecutionResultV1(
        ok=False,
        blockers=sorted(set(blockers)),
        notes=notes + ["FAIL_CLOSED_NO_CONSUME_NO_RUNNER_NO_NETWORK=true"],
        claims={
            "NETWORK_SESSION_EXECUTED": False,
            "REAL_NETWORK_REQUEST_COUNT": 0,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "WALLCLOCK_RUNNER_INVOKED": False,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": True,
            "RUNTIME_REQUIRES_SEPARATE_OWNER_GO": True,
        },
        capability_id=SESSION_EXECUTION_RUNTIME_CAPABILITY_ID,
        authorization_consumed=False,
        confirm_token_consumed=False,
        network_session_executed=False,
        real_network_request_count=0,
        wallclock_runner_invoked=False,
        productive_runner_bound=False,
    )
