"""Prove contemporaneous PRE-RESTART capture observation or close non-execution.

Re-proves the productive capture call path, side-effect boundary, and
isolation claim from the current tree. Builds an explicit authorization
matrix. Adjudicates observation admissibility. Does not execute a
productive contemporaneous capture when any admissibility conjunct is not
provably true. Does not GET. Does not POST. Does not wire-send. Does not
submit. Does not restart. Does not mutate LIVE_ENABLED or LIVE_ARMED.
Does not bypass runtime gates. Does not backfill or synthesize a capture.
Does not promote LIVE_RESTART_RECONSTRUCTED or HOST_CRASH_DURABILITY.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_RELPATH,
    HOST_JOIN_SYMBOL,
    PRODUCTIVE_HOOK_CALLER,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AMEND_ALLOWED,
    CANCEL_ALLOWED,
    CREDENTIAL_USE_ALLOWED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    PUBLIC_GET_ALLOWED,
    RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_capture_seam_required_field_provenance_and_no_backfill_contract_v1 import (
    COMPLETE_CAPTURE_SEAM,
    NO_BACKFILL_CONTRACT_PROVEN,
    PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_complete_contemporaneous_capture_seam_and_required_field_provenance_v1 import (
    INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1 import (
    CAPTURE_POINT,
    CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION,
    CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE,
    CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE,
    CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY,
    EARLIEST_IRREVERSIBLE_EFFECT,
    MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
    PRODUCTIVE_RUNTIME_ENTRYPOINT,
    UNAVOIDABLE_EXTERNAL_EFFECTS,
    bind_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1,
    prove_non_execution_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    HANDOFF_FILENAME,
    RELATIVE_DURABLE_DIR,
)

CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION = "NOT_EXECUTED"
CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED = False
CASE_ADJUDICATION = (
    "CASE_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_NOT_EXECUTED_"
    "NON_EXECUTION_PROOF_ISOLATION_FALSE_BLOCKERS_BOUND"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_"
    "REQUIRES_SEPARATE_OWNER_GO_FOR_LIVE_IDENTITY_BOUND_VENUE_FILL_V1"
)
AUTHORIZATION_MATRIX_STATUS = "COMPLETE"
NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED = False
PRODUCTIVE_DURABLE_HANDOFF_RELPATH = f"{RELATIVE_DURABLE_DIR}/{HANDOFF_FILENAME}"
EFFECT_NAMES: tuple[str, ...] = (
    "CAPTURE_PERSIST",
    "PRIVATE_GET",
    "PUBLIC_GET",
    "SESSION_AUTH",
    "WIRE_SEND",
    "ORDER_SUBMIT",
    "ORDER_CANCEL",
    "ORDER_AMEND",
    "POSITION_MUTATION",
    "RESTART",
    "CRASH_INJECTION",
    "LIVE_ENABLED_MUTATION",
    "LIVE_ARMED_MUTATION",
)


def _repo_root(repo_root: object | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[3]
    return Path(repo_root)


def reprove_productive_capture_call_path_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    if CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    surface = (
        bind_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1(
            repo_root=root,
            storage_root=storage_root,
        )
    )
    entrypoints = surface["entrypoints"]
    callgraph = surface["callgraph"]
    isolation = surface["isolation"]
    if entrypoints["UNIQUE_PRODUCTIVE_CALLER_OF_HOOK_COUNT"] != 1:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")
    if entrypoints["HOST_JOIN_PRODUCTIVE_CALLER_COUNT"] != 0:
        raise Section1114OfflineSurfaceError("HOST_JOIN_MUST_REMAIN_UNREACHABLE_FROM_EXECUTE")
    if entrypoints["CANARY_EXECUTE_INVOKES_CAPTURE"] is True:
        raise Section1114OfflineSurfaceError("CANARY_EXECUTE_MUST_NOT_INVOKE_CAPTURE")
    if entrypoints["CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE"] is True:
        raise Section1114OfflineSurfaceError("CANARY_SUBMIT_MUST_NOT_INVOKE_CAPTURE")
    if isolation["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    if surface["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    if callgraph["IRREVERSIBLE_EFFECT_BEFORE_CAPTURE_CALLER"] != "LIVE_IDENTITY_BOUND_VENUE_FILL":
        raise Section1114OfflineSurfaceError("IRREVERSIBLE_PREDECESSOR_DRIFT")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_CALL_PATH_REPROOF_V1",
        "CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "CAPTURE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_CALLER_COUNT": 1,
        "PRODUCTIVE_CALLERS": (PRODUCTIVE_HOOK_CALLER,),
        "PRE_RESTART_CALL_SITE": f"{CALLER_RELPATH}::{PRODUCTIVE_HOOK_CALLER}",
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "HOST_JOIN_RELPATH": HOST_JOIN_RELPATH,
        "HOOK_RELPATH": HOOK_RELPATH,
        "CAPTURE_POINT": CAPTURE_POINT,
        "PERSISTENCE_DESTINATION": PRODUCTIVE_DURABLE_HANDOFF_RELPATH,
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_REPROVEN": (
            CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE
        ),
        "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY_REPROVEN": (
            CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY
        ),
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
        "CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE": (
            CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE
        ),
        "UNAVOIDABLE_EXTERNAL_EFFECTS": UNAVOIDABLE_EXTERNAL_EFFECTS,
        "EARLIEST_IRREVERSIBLE_EFFECT": EARLIEST_IRREVERSIBLE_EFFECT,
        "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT": MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
        "entrypoints": entrypoints,
        "callgraph": callgraph,
        "timeline": surface["timeline"],
        "side_effects": surface["side_effects"],
        "gates": surface["gates"],
        "inputs": surface["inputs"],
        "isolation": isolation,
        "host_graph": surface["host_graph"],
        "predecessor_surface": surface,
    }


def build_authorization_matrix_v1() -> dict[str, Any]:
    if LIVE_ENABLED is True or LIVE_ARMED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    rows = (
        {
            "EFFECT": "CAPTURE_PERSIST",
            "REACHABLE": True,
            "TECHNICALLY_REQUIRED": True,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": True,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "AUTHORIZED_ONLY_IF_ADMISSIBLE_CONTEMPORANEOUS_PRODUCTIVE_CAPTURE",
            "PROOF_SOURCE": f"{HOOK_RELPATH}::{PRODUCTIVE_LIFECYCLE_HOOK} -> writer",
        },
        {
            "EFFECT": "PRIVATE_GET",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.PRIVATE_GET_ALLOWED={PRIVATE_GET_ALLOWED}",
        },
        {
            "EFFECT": "PUBLIC_GET",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.PUBLIC_GET_ALLOWED={PUBLIC_GET_ALLOWED}",
        },
        {
            "EFFECT": "SESSION_AUTH",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.CREDENTIAL_USE_ALLOWED={CREDENTIAL_USE_ALLOWED}",
        },
        {
            "EFFECT": "WIRE_SEND",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": True,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "NOTE": (
                "Required as the LIVE_IDENTITY_BOUND_VENUE_FILL predecessor, "
                "not as a capture-surface call. Isolation is therefore false."
            ),
            "PROOF_SOURCE": f"constants_v1.POST_ALLOWED={POST_ALLOWED}; isolation census",
        },
        {
            "EFFECT": "ORDER_SUBMIT",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": True,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "NOTE": "Required predecessor of contemporaneous bound fill. Not capture-local.",
            "PROOF_SOURCE": (
                f"constants_v1.ORDER_SUBMIT_ALLOWED={ORDER_SUBMIT_ALLOWED}; isolation census"
            ),
        },
        {
            "EFFECT": "ORDER_CANCEL",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.CANCEL_ALLOWED={CANCEL_ALLOWED}",
        },
        {
            "EFFECT": "ORDER_AMEND",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.AMEND_ALLOWED={AMEND_ALLOWED}",
        },
        {
            "EFFECT": "POSITION_MUTATION",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": True,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "NOTE": "Venue fill of the identity-bound order is the irreversible predecessor.",
            "PROOF_SOURCE": "census_side_effects_v1 EXCHANGE_FILL; isolation census",
        },
        {
            "EFFECT": "RESTART",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"{CALLER_RELPATH} restart_already_occurred fail-closed",
        },
        {
            "EFFECT": "CRASH_INJECTION",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": "capture surface AST census; no crash injector on call path",
        },
        {
            "EFFECT": "LIVE_ENABLED_MUTATION",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.LIVE_ENABLED={LIVE_ENABLED}; caller fail-closed",
        },
        {
            "EFFECT": "LIVE_ARMED_MUTATION",
            "REACHABLE": False,
            "TECHNICALLY_REQUIRED": False,
            "CURRENTLY_GATED": True,
            "AUTHORIZED_BY_THIS_OWNER_GO": False,
            "MAY_OCCUR_THIS_WORKPACKAGE": False,
            "STATUS": "NOT_AUTHORIZED",
            "PROOF_SOURCE": f"constants_v1.LIVE_ARMED={LIVE_ARMED}; caller fail-closed",
        },
    )
    names = tuple(row["EFFECT"] for row in rows)
    if names != EFFECT_NAMES:
        raise Section1114OfflineSurfaceError("AUTHORIZATION_MATRIX_INCOMPLETE")
    unauthorized = [row["EFFECT"] for row in rows if row["EFFECT"] != "CAPTURE_PERSIST"]
    if any(
        row["AUTHORIZED_BY_THIS_OWNER_GO"] is True
        for row in rows
        if row["EFFECT"] != "CAPTURE_PERSIST"
    ):
        raise Section1114OfflineSurfaceError("NON_CAPTURE_SIDE_EFFECT_MUST_REMAIN_UNAUTHORIZED")
    if any(row["MAY_OCCUR_THIS_WORKPACKAGE"] is True for row in rows):
        raise Section1114OfflineSurfaceError("NO_BOUND3_EFFECT_MAY_OCCUR_BEFORE_ADMISSIBILITY")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_AUTHORIZATION_MATRIX_V1",
        "AUTHORIZATION_MATRIX_STATUS": AUTHORIZATION_MATRIX_STATUS,
        "NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED": NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED,
        "UNAUTHORIZED_EFFECTS": unauthorized,
        "rows": list(rows),
    }


def census_required_runtime_state_v1(*, repo_root: object | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    productive_handoff = root / RELATIVE_DURABLE_DIR / HANDOFF_FILENAME
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_REQUIRED_CAPTURE_RUNTIME_STATE_CENSUS_V1",
        "LIVE_ENABLED": LIVE_ENABLED,
        "LIVE_ARMED": LIVE_ARMED,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": (SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED),
        "POST_ALLOWED": POST_ALLOWED,
        "ORDER_SUBMIT_ALLOWED": ORDER_SUBMIT_ALLOWED,
        "CURRENT_PROCESS_HAS_CONTEMPORANEOUS_BOUND_FILL": False,
        "PRODUCTIVE_DURABLE_HANDOFF_PRESENT": productive_handoff.is_file(),
        "PRODUCTIVE_DURABLE_HANDOFF_PATH": PRODUCTIVE_DURABLE_HANDOFF_RELPATH,
        "HISTORICAL_BOUND_IDENTITY_IS_NOT_CONTEMPORANEOUS": True,
        "TEST_FIXTURE_IS_NOT_PRODUCTIVE_PROVENANCE": True,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED,
        "HOOK_REJECTS_PRODUCTIVE_BOUND_FILL_INPUT": True,
    }


def adjudicate_observation_admissibility_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    call_path = reprove_productive_capture_call_path_v1(
        repo_root=root,
        storage_root=storage_root,
    )
    matrix = build_authorization_matrix_v1()
    state = census_required_runtime_state_v1(repo_root=root)
    non_execution = call_path["predecessor_surface"]["non_execution"]
    if call_path["CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION"] is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    if state["LIVE_ENABLED"] is True or state["LIVE_ARMED"] is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if state["SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED is True:
        raise Section1114OfflineSurfaceError("RETROACTIVE_SYNTHESIS_MUST_REMAIN_FORBIDDEN")
    if non_execution["PRODUCTIVE_INPUT_CLASS_REJECTED"] is not True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_INPUT_MUST_REMAIN_UNAUTHORIZED")
    conjunct_a = {
        "ID": "A",
        "QUESTION": (
            "Can a genuine contemporaneous PRE-RESTART capture observation be "
            "produced without an unauthorized BOUND-3 effect?"
        ),
        "ANSWER": False,
        "PROVABLE": True,
        "BLOCKER": (
            "Isolation from live execution is false. Legitimate productive "
            "contemporaneous capture requires LIVE_IDENTITY_BOUND_VENUE_FILL "
            "of a submitted order. ORDER_SUBMIT/WIRE_SEND/POSITION_MUTATION "
            "are not authorized. TEST_FIXTURE persist is not productive "
            "provenance. Historical BOUND_* identity is backfill."
        ),
    }
    conjunct_b = {
        "ID": "B",
        "QUESTION": (
            "Is the required contemporaneous bound-fill state already present "
            "without mutating LIVE_ENABLED/LIVE_ARMED or entering submit/restart?"
        ),
        "ANSWER": False,
        "PROVABLE": True,
        "BLOCKER": (
            "LIVE_ENABLED=false; LIVE_ARMED=false; "
            "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false; no current-process "
            "contemporaneous bound fill; no productive durable handoff present; "
            "hook rejects PRODUCTIVE_BOUND_FILL_INPUT as RUNTIME_EXECUTION_UNAUTHORIZED."
        ),
    }
    conjunct_c = {
        "ID": "C",
        "QUESTION": ("Would the observation be contemporaneous and not backfilled or synthesized?"),
        "ANSWER": False,
        "PROVABLE": True,
        "BLOCKER": (
            "No contemporaneous productive capture can be produced under this GO. "
            "Using historical BOUND_* would be backfill. TEST_FIXTURE would be synthesis."
        ),
    }
    conjunct_d = {
        "ID": "D",
        "QUESTION": (
            "Can contemporaneous provenance be fully bound for a productive capture artifact?"
        ),
        "ANSWER": False,
        "PROVABLE": True,
        "BLOCKER": (
            "No productive capture artifact is produced. Provenance fields remain "
            "fail-closed. OWNER_GO presence does not bypass HOOK_INPUT_CLASS_TEST_FIXTURE_ONLY."
        ),
    }
    conjuncts = (conjunct_a, conjunct_b, conjunct_c, conjunct_d)
    if any(row["ANSWER"] is True or row["PROVABLE"] is not True for row in conjuncts):
        raise Section1114OfflineSurfaceError("ADMISSIBILITY_MUST_FAIL_CLOSED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_OBSERVATION_ADMISSIBILITY_ADJUDICATION_V1",
        "ADMISSIBLE": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "BACKFILL_USED": False,
        "RETROACTIVE_SYNTHESIS_USED": False,
        "conjuncts": list(conjuncts),
        "call_path": call_path,
        "authorization_matrix": matrix,
        "required_state": state,
        "non_execution": non_execution,
    }


def prove_capture_was_not_executed_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    non_execution = prove_non_execution_v1(repo_root=root, storage_root=storage_root)
    if non_execution["CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED"] is True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_CAPTURE_MUST_NOT_BE_CLAIMED")
    if hasattr(run_capture_hook_after_bound_fill_before_restart_v1, "__name__") is False:
        raise Section1114OfflineSurfaceError("HOOK_SYMBOL_MISSING")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_NON_EXECUTION_PROOF_V1",
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CAPTURE_TIMESTAMP": None,
        "CAPTURE_ARTIFACT_ID": None,
        "CAPTURE_ARTIFACT_HASH": None,
        "CAPTURE_PROVENANCE_VALIDATED": False,
        "BACKFILL_USED": False,
        "RETROACTIVE_SYNTHESIS_USED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_INJECTION_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "LIVE_ENABLED_MUTATED": False,
        "LIVE_ARMED_MUTATED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "INPUT_CLASS_PRODUCTIVE_REJECTED": True,
        "INPUT_CLASS_PRODUCTIVE": INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        "non_execution": non_execution,
    }


def bind_contemporaneous_pre_restart_capture_observation_and_non_execution_proof_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    if COMPLETE_CAPTURE_SEAM != "PROVEN":
        raise Section1114OfflineSurfaceError("COMPLETE_CAPTURE_SEAM_MUST_REMAIN_PROVEN")
    if PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL is not True:
        raise Section1114OfflineSurfaceError("NO_BACKFILL_CONTRACT_UNPROVEN")
    if NO_BACKFILL_CONTRACT_PROVEN is not True:
        raise Section1114OfflineSurfaceError("NO_BACKFILL_CONTRACT_UNPROVEN")
    admissibility = adjudicate_observation_admissibility_v1(
        repo_root=root,
        storage_root=storage_root,
    )
    if admissibility["ADMISSIBLE"] is True:
        raise Section1114OfflineSurfaceError("ADMISSIBILITY_MUST_FAIL_CLOSED")
    non_exec = prove_capture_was_not_executed_v1(repo_root=root, storage_root=storage_root)
    call_path = admissibility["call_path"]
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
            "AND_NON_EXECUTION_PROOF_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "COMPLETE_CAPTURE_SEAM": "PROVEN",
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": True,
        "NO_BACKFILL_CONTRACT_PROVEN": True,
        "CAPTURE_OWNER": PRODUCTIVE_CAPTURE_OWNER,
        "CAPTURE_LIFECYCLE_HOOK": PRODUCTIVE_LIFECYCLE_HOOK,
        "PRODUCTIVE_CALLER_COUNT": 1,
        "PRODUCTIVE_CALLERS": [PRODUCTIVE_HOOK_CALLER],
        "PRE_RESTART_CALL_SITE": call_path["PRE_RESTART_CALL_SITE"],
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "CAPTURE_POINT": CAPTURE_POINT,
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_REPROVEN": (
            CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE
        ),
        "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY_REPROVEN": (
            CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY
        ),
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
        "CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE": True,
        "AUTHORIZATION_MATRIX_STATUS": AUTHORIZATION_MATRIX_STATUS,
        "NON_CAPTURE_SIDE_EFFECTS_AUTHORIZED": False,
        "CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION": (
            CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION
        ),
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CAPTURE_TIMESTAMP": None,
        "CAPTURE_ARTIFACT_ID": None,
        "CAPTURE_ARTIFACT_HASH": None,
        "CAPTURE_PROVENANCE_VALIDATED": False,
        "BACKFILL_USED": False,
        "RETROACTIVE_SYNTHESIS_USED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_INJECTION_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "LIVE_ENABLED_MUTATED": False,
        "LIVE_ARMED_MUTATED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "OWNER_GO_IS_NOT_GATE_BYPASS": True,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "call_path": call_path,
        "authorization_matrix": admissibility["authorization_matrix"],
        "observation_admissibility": {
            "ADMISSIBLE": False,
            "conjuncts": admissibility["conjuncts"],
            "required_state": admissibility["required_state"],
        },
        "non_execution": non_exec,
        "host_graph": call_path["host_graph"],
        "entrypoints": call_path["entrypoints"],
        "callgraph": call_path["callgraph"],
        "timeline": call_path["timeline"],
        "side_effects": call_path["side_effects"],
        "gates": call_path["gates"],
        "inputs": call_path["inputs"],
        "isolation": call_path["isolation"],
    }
