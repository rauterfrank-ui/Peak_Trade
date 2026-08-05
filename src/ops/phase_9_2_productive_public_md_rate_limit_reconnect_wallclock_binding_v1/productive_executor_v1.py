"""Step-4 productive session executor wiring.

Call graph after Gate PASS (wiring capability):
  evaluate_rate_limit_reconnect_wallclock_binding_gate_v1
  → prove_public_md_network_boundary_v1
  → prove_governed_fault_path_offline_v1  (bind fault owners; no fault session)
  → bind CANONICAL_WALLCLOCK_RUNNER symbol (run_productive_wallclock_session_v1)
  → materialize session evidence schema template

This capability NEVER starts a real Public-MD network session and NEVER starts a
fault session. allow_real_network=True fails closed. Confirm-token plaintext is
never consumed here — only presence via the canonical path is validated by gate.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.binding_gate_v1 import (
    evaluate_rate_limit_reconnect_wallclock_binding_gate_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    BUNDLE_VERIFIER_OWNER,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    EEA_TRANSPORT_OWNER,
    FAULT_SESSION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PACING_POLICY_OWNER,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    RATE_LIMIT_METRIC_OWNER,
    RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    SESSION_RUNTIME_OWNER,
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
    """Fail-closed productive executor wiring for Step 4.

    Requires execute=True for readiness binding. Real network remains forbidden.
    """
    env = environ if environ is not None else os.environ
    notes = [
        f"WIRING_CAPABILITY_ID={WIRING_CAPABILITY_ID}",
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
    ]
    blockers: list[str] = []
    call_graph = [
        "evaluate_rate_limit_reconnect_wallclock_binding_gate_v1",
        "prove_public_md_network_boundary_v1",
        "prove_governed_fault_path_offline_v1",
        "run_productive_wallclock_session_v1",
        "build_session_evidence_template_v1",
    ]

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
        and boundary.get("ok")
        and fault.get("ok")
        and schema.get("ok")
        and not allow_real_network
    )
    ready = bool(reachable and READY_FOR_PRODUCTIVE_SESSION_EXECUTION and not blockers)

    claims = {
        "EXECUTOR_CODE_EXISTS": True,
        "EXECUTOR_PRODUCTIVELY_BOUND": ready,
        "PRODUCTIVE_SESSION_REACHABLE": ready,
        "PRODUCTIVE_SESSION_AUTHORIZED": authorized,
        "NETWORK_SESSION_STARTED": False,
        "FAULT_SESSION_STARTED": False,
        "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED": False,
        "RECONNECT_PATH_PRODUCTIVELY_OBSERVED": False,
        "EVIDENCE_VERIFIED": bool(schema.get("ok")),
        "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
        "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": ready,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "WALLCLOCK_RUNNER_INVOKED": False,
        "PARALLEL_SESSION_RUNTIME_CREATED": False,
        "PARALLEL_TRANSPORT_AUTHORITY_CREATED": False,
        "PARALLEL_RETRY_AUTHORITY_CREATED": False,
    }

    return ProductiveExecutorResultV1(
        ok=ready,
        blockers=sorted(set(blockers)),
        notes=notes
        + [
            "WIRING_BOUND_WITHOUT_NETWORK_SESSION=true",
            "LATER_SEPARATE_OWNER_SESSION_GO_REQUIRED_FOR_REAL_SESSION=true",
        ],
        wiring_capability_id=WIRING_CAPABILITY_ID,
        session_id=TARGET_SESSION_ID,
        executor_code_exists=True,
        executor_productively_bound=ready,
        productive_session_reachable=ready,
        productive_session_authorized=authorized,
        ready_for_productive_session_execution=ready,
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
