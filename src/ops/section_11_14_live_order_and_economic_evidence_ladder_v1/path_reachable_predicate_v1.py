"""Canonical LIVE_EXECUTION_PATH_REACHABLE predicate and constituent matrix.

Binds reachability as traversal to the pre-submit boundary of the current
Live canary productive path. Does not require submit authorization. Does
not promote later §11.14 ladder fields. Does not POST.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_RUNBOOK_PATH,
    CANONICAL_SECTION_HEADING,
    FORBIDDEN_LIVE_SOURCE_KINDS,
    LIVE_EXECUTION_PATH_REACHABLE_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

ROLE_PART_OF_REACHABILITY = "PART_OF_REACHABILITY"
ROLE_NOT_PART_OF_REACHABILITY = "NOT_PART_OF_REACHABILITY"
ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION = "REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION"
ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE = "REQUIRED_ONLY_FOR_LATER_LADDER_STAGE"
ROLE_AMBIGUOUS_FAIL_CLOSED = "AMBIGUOUS_FAIL_CLOSED"

REACHABILITY_ROLES: frozenset[str] = frozenset(
    {
        ROLE_PART_OF_REACHABILITY,
        ROLE_NOT_PART_OF_REACHABILITY,
        ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
        ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE,
        ROLE_AMBIGUOUS_FAIL_CLOSED,
    }
)

# Required conjunction for PATH_REACHABLE. Order is canonical and stable.
REACHABILITY_CONSTITUENTS: tuple[str, ...] = (
    "STATIC_EXECUTION_GRAPH_COMPLETE",
    "ENTRYPOINT_INTEGRATED",
    "CURRENT_RUNTIME_PATH_SELECTABLE",
    "REQUIRED_FAIL_CLOSED_GATES_EVALUABLE",
    "TRANSPORT_CONSTRUCTIBLE",
    "REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE",
    "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
    "AUTHENTICATION_PATH_FUNCTIONAL",
    "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
    "NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY",
)
REACHABILITY_CONSTITUENT_COUNT = 10

# Candidate names from the Owner-GO that are classified, including rejects.
CANDIDATE_CONSTITUENTS: tuple[str, ...] = (
    "STATIC_EXECUTION_GRAPH_COMPLETE",
    "ENTRYPOINT_INTEGRATED",
    "CURRENT_RUNTIME_PATH_ENABLED_OR_SELECTABLE",
    "REQUIRED_FAIL_CLOSED_GATES_EVALUABLE",
    "TRANSPORT_CONSTRUCTIBLE",
    "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
    "AUTHENTICATION_PATH_FUNCTIONAL",
    "REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE",
    "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
    "NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY",
    "OWNER_OR_EXECUTION_PERMIT_STATE",
    "LIVE_ENABLED",
    "LIVE_ARMED",
    "SUBMIT_UNLOCKED",
    "CANARY_AUTHORIZED",
)

PROOF_LAYER_STATIC = "STATIC_OFFLINE"
PROOF_LAYER_CONFIG = "CONFIG_DEFAULT_INSPECTION"
PROOF_LAYER_CREDENTIAL_PRESENCE = "CREDENTIAL_MATERIAL_PRESENCE_WITHOUT_VALUES"
PROOF_LAYER_FRESH_PRIVATE_GET = "FRESH_AUTHENTICATED_PRIVATE_GET"

ADMISSIBILITY_PREDICATE = (
    "LIVE_EXECUTION_PATH_REACHABLE is true iff every PART_OF_REACHABILITY "
    "constituent is proven true on current origin/main using the lowest "
    "authority admissible evidence. The field means the current productive "
    "Live canary path can be traversed to the pre-submit boundary: the "
    "static graph is complete and integrated, the entrypoint is selectable, "
    "fail-closed gates are evaluable, the urllib Live transport is "
    "constructible, required SecretRef credential material is present, the "
    "production EEA host is connectable, and a current authenticated private "
    "GET demonstrates functional authentication and account/venue read "
    "access, with no static blocker preventing that pre-submit boundary. "
    "Submit-authorization gates (LIVE_ENABLED, LIVE_ARMED, SUBMIT_UNLOCKED, "
    "CANARY_AUTHORIZED, LIVE_AUTHORIZED, OWNER execute-permit, "
    "SECTION_11_14_AUTHORIZED) are not constituents. §4.9 CURRENTLY_REACHABLE, "
    "LIVE_EXECUTION_CODE_EXISTS, historical GET success, credential presence "
    "alone, configured defaults, and fixture/testnet/sim sources are each "
    "insufficient. True does not promote LIVE_PRIVATE_READ_ONLY_PROVEN or "
    "any later ladder field, and does not authorize POST or submit."
)


def _candidate(
    *,
    name: str,
    role: str,
    interpretation: str,
    proof_layer: str,
    notes: str,
) -> dict[str, Any]:
    if role not in REACHABILITY_ROLES:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_REACHABILITY_ROLE:{role}")
    return {
        "name": name,
        "role": role,
        "required_for_path_reachable": role == ROLE_PART_OF_REACHABILITY,
        "interpretation": interpretation,
        "proof_layer": proof_layer,
        "notes": notes,
    }


def candidate_constituent_classifications_v1() -> tuple[dict[str, Any], ...]:
    return (
        _candidate(
            name="STATIC_EXECUTION_GRAPH_COMPLETE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="CODE_EXISTS_GRAPH_MUST_REMAIN_COMPLETE",
            proof_layer=PROOF_LAYER_STATIC,
            notes="Predecessor LIVE_EXECUTION_CODE_EXISTS graph; not sufficient alone.",
        ),
        _candidate(
            name="ENTRYPOINT_INTEGRATED",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="RUN_CANARY_SUBMIT_TRANSPORT_IS_CURRENT_PRODUCTIVE_ORCHESTRATOR",
            proof_layer=PROOF_LAYER_STATIC,
            notes="Integrated Class-B orchestrator on the current Live canary path.",
        ),
        _candidate(
            name="CURRENT_RUNTIME_PATH_ENABLED_OR_SELECTABLE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="SELECTABLE_NOT_ENABLED",
            proof_layer=PROOF_LAYER_STATIC,
            notes=(
                "Bound as CURRENT_RUNTIME_PATH_SELECTABLE. ENABLED (LIVE_ENABLED / "
                "CANARY_SUBMIT_TRANSPORT_ACTIVATED) is submit authorization, not "
                "reachability. Selectable means the current productive orchestrator "
                "is constructible and callable as code."
            ),
        ),
        _candidate(
            name="REQUIRED_FAIL_CLOSED_GATES_EVALUABLE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="GATES_MUST_BE_EVALUABLE_NOT_CURRENTLY_PASSING_FOR_SUBMIT",
            proof_layer=PROOF_LAYER_STATIC,
            notes=(
                "evaluate_canary_submit_gates_v1 and refuse_submit_unless_gates_pass_v1 "
                "must exist and be callable. Current submit_allowed=false is expected "
                "under standing fail-closed flags and is not a reachability blocker."
            ),
        ),
        _candidate(
            name="TRANSPORT_CONSTRUCTIBLE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="URLLIB_LIVE_CANARY_TRANSPORT_CONSTRUCTIBLE",
            proof_layer=PROOF_LAYER_STATIC,
            notes="UrllibLiveCanaryTransportV1 and LiveCanaryHttpClientV1 constructible.",
        ),
        _candidate(
            name="TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="PRODUCTION_EEA_HOST_CURRENTLY_CONNECTABLE",
            proof_layer=PROOF_LAYER_FRESH_PRIVATE_GET,
            notes="eea.okx.com must currently accept the authenticated GET. Configured host is not the fact.",
        ),
        _candidate(
            name="AUTHENTICATION_PATH_FUNCTIONAL",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="CURRENT_SIGNED_PRIVATE_GET_AUTH_SUCCESS",
            proof_layer=PROOF_LAYER_FRESH_PRIVATE_GET,
            notes="Credential presence is not authentication success. Historical GET is not current.",
        ),
        _candidate(
            name="REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="SECRETREF_BOUND_AND_FIELDS_COMPLETE_WITHOUT_VALUES",
            proof_layer=PROOF_LAYER_CREDENTIAL_PRESENCE,
            notes="Vault/SecretRef presence and field completeness. Not auth success.",
        ),
        _candidate(
            name="CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="CURRENT_PRIVATE_GET_RETURNS_READABLE_ACCOUNT_PAYLOAD",
            proof_layer=PROOF_LAYER_FRESH_PRIVATE_GET,
            notes="HTTP 200 and OKX code 0 with parseable account/config data.",
        ),
        _candidate(
            name="NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY",
            role=ROLE_PART_OF_REACHABILITY,
            interpretation="NO_HARDCODED_DEAD_PATH_BEFORE_PRE_SUBMIT",
            proof_layer=PROOF_LAYER_STATIC,
            notes=(
                "Standing LIVE_ENABLED=false does not statically prevent gate "
                "evaluation. PRODUCTIVE_WIRE_SEND_DISABLED is a constructor default, "
                "not a deleted path. Submit-gate refusal is the pre-submit boundary."
            ),
        ),
        _candidate(
            name="OWNER_OR_EXECUTION_PERMIT_STATE",
            role=ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
            interpretation="EXECUTE_PERMIT_NOT_REQUIRED_TO_REACH_PRE_SUBMIT",
            proof_layer=PROOF_LAYER_CONFIG,
            notes="Owner execute-permit and canary confirm token are submit authorization.",
        ),
        _candidate(
            name="LIVE_ENABLED",
            role=ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
            interpretation="STANDING_FALSE_IS_NOT_A_REACHABILITY_CONSTITUENT",
            proof_layer=PROOF_LAYER_CONFIG,
            notes="Fail-closed submit gate. Evaluable while false. Not PATH_REACHABLE.",
        ),
        _candidate(
            name="LIVE_ARMED",
            role=ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
            interpretation="STANDING_FALSE_IS_NOT_A_REACHABILITY_CONSTITUENT",
            proof_layer=PROOF_LAYER_CONFIG,
            notes="Fail-closed submit gate. Evaluable while false. Not PATH_REACHABLE.",
        ),
        _candidate(
            name="SUBMIT_UNLOCKED",
            role=ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
            interpretation="STANDING_FALSE_IS_NOT_A_REACHABILITY_CONSTITUENT",
            proof_layer=PROOF_LAYER_CONFIG,
            notes="Fail-closed submit gate. Evaluable while false. Not PATH_REACHABLE.",
        ),
        _candidate(
            name="CANARY_AUTHORIZED",
            role=ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
            interpretation="STANDING_FALSE_IS_NOT_A_REACHABILITY_CONSTITUENT",
            proof_layer=PROOF_LAYER_CONFIG,
            notes="live_canary_authorized is submit authorization, not path reachability.",
        ),
    )


def build_constituent_matrix_v1() -> dict[str, Any]:
    rows = list(candidate_constituent_classifications_v1())
    required = [row["name"] for row in rows if row["required_for_path_reachable"] is True]
    # SELECTABLE is the bound required name for the ENABLED_OR_SELECTABLE candidate.
    required_bound = list(REACHABILITY_CONSTITUENTS)
    return {
        "schema_version": "section_11_14_path_reachable_constituent_matrix.v1",
        "canonical_definition": LIVE_EXECUTION_PATH_REACHABLE_CANONICAL_DEFINITION,
        "admissibility_predicate": ADMISSIBILITY_PREDICATE,
        "canonical_location": f"{CANONICAL_RUNBOOK_PATH} {CANONICAL_SECTION_HEADING}",
        "reachability_constituent_count": REACHABILITY_CONSTITUENT_COUNT,
        "reachability_constituents": required_bound,
        "candidate_count": len(rows),
        "candidate_required_names": required,
        "rows": rows,
        "submit_authorization_excluded": True,
        "later_ladder_fields_excluded": True,
        "section_4_9_currently_reachable_excluded": True,
    }


def evaluate_reachability_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str = "REPOSITORY_IMPLEMENTATION",
) -> dict[str, Any]:
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(
            f"FORBIDDEN_LIVE_SOURCE:{kind}:LIVE_EXECUTION_PATH_REACHABLE"
        )
    missing = [name for name in REACHABILITY_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "REACHABILITY_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    unknown = [name for name in constituent_values if name not in REACHABILITY_CONSTITUENTS]
    if unknown:
        raise Section1114OfflineSurfaceError(
            "UNKNOWN_REACHABILITY_CONSTITUENT:" + ",".join(sorted(unknown))
        )
    proven: dict[str, bool] = {}
    false_required: list[str] = []
    unobserved_required: list[str] = []
    for name in REACHABILITY_CONSTITUENTS:
        value = constituent_values[name]
        if value is True:
            proven[name] = True
        elif value is False:
            proven[name] = False
            false_required.append(name)
        else:
            proven[name] = False
            unobserved_required.append(name)
    claim = not false_required and not unobserved_required
    if false_required:
        reason = "FALSE_REQUIRED_CONSTITUENT:" + ",".join(false_required)
        adjudication = "FALSE_REQUIRED_CONSTITUENT"
    elif unobserved_required:
        reason = "UNOBSERVED_REQUIRED_CONSTITUENT:" + ",".join(unobserved_required)
        adjudication = "FALSE_UNOBSERVED_REQUIRED_CONSTITUENT"
    else:
        reason = "FULL_CONJUNCTION_PROVEN"
        adjudication = "TRUE_PRE_SUBMIT_PATH_REACHABLE"
    return {
        "canonical_definition": LIVE_EXECUTION_PATH_REACHABLE_CANONICAL_DEFINITION,
        "admissibility_predicate": ADMISSIBILITY_PREDICATE,
        "source_kind": kind,
        "constituents": dict(proven),
        "false_required": false_required,
        "unobserved_required": unobserved_required,
        "claim_value": claim,
        "adjudication": adjudication,
        "reason": reason,
        "live_private_read_only_proven_promoted": False,
        "submit_authorization_inferred": False,
        "later_ladder_fields_promoted": False,
    }
