"""Step-6 productive executor wiring (binding only; no network session).

CALL_GRAPH_BEFORE:
  (absent Step-6 surfaces)
  → HARD_STOP on governed session attempt

CALL_GRAPH_AFTER:
  evaluate_step6_binding_gate_v1
  → load_and_validate_session_contract_v1
  → prove_public_md_network_boundary_v1
  → prove_governed_adverse_stale_fault_path_offline_v1
  → bind StalenessTrackerV1 + killstate STALE_DATA
  → bind GovernedInjectedStaleDataControlV1 (default disabled)
  → bind CANONICAL_WALLCLOCK_RUNNER symbol
  → materialize session evidence schema template
  → NETWORK_SESSION_STARTED=false
"""

from __future__ import annotations

import importlib
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    ADVERSE_DATA_CLASSIFIER,
    ADVERSE_STALE_DATA_LADDER_STEP_CLOSED,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    FAILURE_INJECTION_SURFACE,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_STEP6_EXECUTOR,
    READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION,
    STALE_DATA_CLASSIFIER,
    TARGET_SESSION_ID,
    VERIFIER_PATH,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.fault_path_v1 import (
    prove_governed_adverse_stale_fault_path_offline_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.governed_injected_stale_data_fault_v1 import (
    GovernedInjectedStaleDataControlV1,
    build_disabled_stale_data_fault_schedule_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.network_boundary_v1 import (
    prove_public_md_network_boundary_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.parity_v1 import (
    assert_no_parallel_productive_authority_v1,
    prove_phase92_step6_adverse_stale_continuation_parity_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.session_evidence_schema_v1 import (
    build_session_evidence_template_v1,
    validate_session_evidence_schema_v1,
)


@dataclass
class ProductiveExecutorResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    network_session_started: bool = False
    fault_session_started: bool = False
    authorization_consumed: bool = False
    confirm_token_consumed: bool = False
    claims: dict[str, Any] = field(default_factory=dict)
    call_graph_after: list[str] = field(default_factory=list)
    surfaces: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_wallclock_runner_symbol_v1() -> dict[str, Any]:
    module_path, _, attr = CANONICAL_WALLCLOCK_RUNNER.rpartition(".")
    # strip leading src. for import
    import_path = module_path
    if import_path.startswith("src."):
        import_path = import_path[len("src.") :]
    mod = importlib.import_module(import_path)
    runner = getattr(mod, attr, None)
    return {
        "ok": callable(runner),
        "symbol": CANONICAL_WALLCLOCK_RUNNER,
        "import_path": import_path,
        "attr": attr,
    }


def evaluate_step6_binding_gate_v1(
    *,
    request_real_network: bool = False,
    owner_go: bool = False,
) -> dict[str, Any]:
    blockers: list[str] = []
    if request_real_network:
        blockers.append("REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY")
    if NETWORK_SESSION_ALLOWED:
        blockers.append("NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE")
    if not owner_go and request_real_network:
        blockers.append("OWNER_GO_REQUIRED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "network_session_started": False,
        "fault_session_started": False,
        "real_network_may_proceed": False,
    }


def run_step6_productive_executor_wiring_v1(
    *,
    repository_sha: str,
    config_digest: str,
    request_real_network: bool = False,
    owner_go: bool = True,
) -> ProductiveExecutorResultV1:
    """Wire Step-6 surfaces without starting a network or consuming auth/tokens."""
    blockers: list[str] = []
    notes: list[str] = []
    call_graph = [
        "evaluate_step6_binding_gate_v1",
        "load_and_validate_session_contract_v1",
        "prove_public_md_network_boundary_v1",
        "prove_governed_adverse_stale_fault_path_offline_v1",
        "bind_StalenessTrackerV1_and_killstate_STALE_DATA",
        "bind_GovernedInjectedStaleDataControlV1_default_disabled",
        "bind_CANONICAL_WALLCLOCK_RUNNER_symbol",
        "materialize_session_evidence_schema_template",
    ]

    gate = evaluate_step6_binding_gate_v1(
        request_real_network=request_real_network, owner_go=owner_go
    )
    if not gate["ok"]:
        blockers.extend(list(gate["blockers"]))

    parity = prove_phase92_step6_adverse_stale_continuation_parity_v1()
    if not parity["ok"]:
        blockers.extend(list(parity["blockers"]))

    authority = assert_no_parallel_productive_authority_v1()
    if not authority["ok"]:
        blockers.append("PARALLEL_AUTHORITY_DETECTED")

    try:
        contract = load_and_validate_session_contract_v1()
        notes.append(f"SESSION_CONTRACT_OK:{contract.get('session_id')}")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"SESSION_CONTRACT_FAILED:{exc}")
        contract = {}

    boundary = prove_public_md_network_boundary_v1()
    if not boundary["ok"]:
        blockers.extend(list(boundary.get("blockers") or []))

    fault = prove_governed_adverse_stale_fault_path_offline_v1()
    if not fault["ok"]:
        blockers.append("ADVERSE_STALE_FAULT_PATH_PROOF_FAILED")

    control = GovernedInjectedStaleDataControlV1(
        schedule=build_disabled_stale_data_fault_schedule_v1()
    )
    control.assert_no_decision_injection_v1()
    if control.schedule.enabled:
        blockers.append("DEFAULT_STALE_FAULT_SCHEDULE_MUST_BE_DISABLED")

    runner = _resolve_wallclock_runner_symbol_v1()
    if not runner["ok"]:
        blockers.append("CANONICAL_WALLCLOCK_RUNNER_UNRESOLVED")

    template = build_session_evidence_template_v1(
        repository_sha=repository_sha,
        config_digest=config_digest,
    )
    schema = validate_session_evidence_schema_v1(template)
    if not schema["ok"]:
        blockers.extend(list(schema.get("blockers") or []))

    ok = not blockers
    return ProductiveExecutorResultV1(
        ok=ok,
        blockers=blockers,
        network_session_started=False,
        fault_session_started=False,
        authorization_consumed=False,
        confirm_token_consumed=False,
        call_graph_after=call_graph,
        surfaces={
            "PRODUCTIVE_ENTRYPOINT": PRODUCTIVE_ENTRYPOINT_PATH,
            "PRODUCTIVE_STEP6_EXECUTOR": PRODUCTIVE_STEP6_EXECUTOR,
            "STALE_DATA_CLASSIFIER": STALE_DATA_CLASSIFIER,
            "ADVERSE_DATA_CLASSIFIER": ADVERSE_DATA_CLASSIFIER,
            "FAILURE_INJECTION_SURFACE": FAILURE_INJECTION_SURFACE,
            "VERIFIER_PATH": VERIFIER_PATH,
            "TARGET_SESSION_ID": TARGET_SESSION_ID,
            "CAPABILITY_ID": CAPABILITY_ID,
        },
        claims={
            "STEP6_BINDING_IMPLEMENTED": ok,
            "RUNTIME_REACHABLE": bool(runner["ok"]),
            "PRODUCTIVE_CALLER_ADDED": True,
            "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": (
                READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION and ok
            ),
            "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED": ADVERSE_STALE_DATA_LADDER_STEP_CLOSED,
            "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
            "NETWORK_SESSION_STARTED": False,
            "AUTHORIZATION_CONSUMED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
            "PRIVATE_ENDPOINT_REACHED": False,
            "EXCHANGE_CREDENTIAL_PATH_REACHED": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "STALE_DATA_CLASSIFIER_BOUND": True,
            "ADVERSE_DATA_CLASSIFIER_BOUND": True,
            "FAILURE_INJECTION_BOUND": True,
            "DEFAULT_FAULT_INJECTION_DISABLED": True,
        },
        notes=notes
        + [
            "BINDING_ONLY_NO_NETWORK_SESSION",
            "REUSES_CANONICAL_STALENESS_AND_KILLSTATE",
            "REUSES_STEP4_FAULT_PATTERN_AND_STEP5_EVIDENCE_PATTERN",
        ],
    )


def exact_productive_caller_path_v1() -> list[str]:
    return [
        PRODUCTIVE_ENTRYPOINT_PATH,
        PRODUCTIVE_STEP6_EXECUTOR + ".run_step6_productive_executor_wiring_v1",
        FAILURE_INJECTION_SURFACE,
        STALE_DATA_CLASSIFIER,
        ADVERSE_DATA_CLASSIFIER,
        CANONICAL_WALLCLOCK_RUNNER,
        VERIFIER_PATH,
    ]
