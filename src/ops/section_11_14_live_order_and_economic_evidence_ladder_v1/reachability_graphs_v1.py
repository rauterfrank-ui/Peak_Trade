"""Static reachability, runtime-dependency, and authority-boundary graphs."""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_PATH,
    SP01_PATH,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_predicate_v1 import (
    REACHABILITY_CONSTITUENTS,
    ROLE_PART_OF_REACHABILITY,
    ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE,
    ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
)


def build_static_reachability_graph_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_static_reachability_graph.v1",
        "pre_submit_boundary": "refuse_submit_unless_gates_pass_v1",
        "status": "COMPLETE_TO_PRE_SUBMIT_BOUNDARY",
        "nodes": [
            {
                "id": "DECISION_GATE",
                "symbol": "evaluate_canary_submit_gates_v1",
                "path": "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py",
                "layer": "STATIC",
                "crosses_pre_submit": False,
            },
            {
                "id": "GATE_REFUSAL",
                "symbol": "refuse_submit_unless_gates_pass_v1",
                "path": "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py",
                "layer": "STATIC",
                "crosses_pre_submit": False,
                "notes": "Hard-blocks POST when submit gates fail. Evaluable while standing flags are false.",
            },
            {
                "id": "SUBMIT_ORCHESTRATOR",
                "symbol": "run_canary_submit_transport_v1",
                "path": CANARY_SUBMIT_TRANSPORT_PATH,
                "layer": "STATIC",
                "crosses_pre_submit": True,
                "notes": "POST occurs only after gates pass. Reachability stops at the refusal seam.",
            },
            {
                "id": "LIVE_HTTP_PORT",
                "symbol": "LiveCanaryHttpClientV1.get / post_entry_order",
                "path": SP01_PATH,
                "layer": "STATIC",
                "get_constructible": True,
                "post_constructible": True,
                "post_authorized_by_this_go": False,
            },
            {
                "id": "LIVE_HTTP_TRANSPORT",
                "symbol": "UrllibLiveCanaryTransportV1.send",
                "path": SP01_PATH,
                "layer": "STATIC",
                "default_wire_send_enabled": False,
                "wire_send_may_be_enabled_for_authorized_get": True,
            },
        ],
        "static_proof_ends_at": "TRANSPORT_AND_GATE_EVALUATION_CONSTRUCTIBLE",
        "runtime_proof_begins_at": "CREDENTIAL_PRESENCE_THEN_AUTHENTICATED_PRIVATE_GET",
        "post_not_on_reachability_path": True,
    }


def build_runtime_dependency_graph_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_runtime_dependency_graph.v1",
        "status": "BOUND",
        "edges": [
            {
                "from": "REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE",
                "to": "AUTHENTICATION_PATH_FUNCTIONAL",
                "kind": "NECESSARY_NOT_SUFFICIENT",
            },
            {
                "from": "TRANSPORT_CONSTRUCTIBLE",
                "to": "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
                "kind": "NECESSARY_NOT_SUFFICIENT",
            },
            {
                "from": "AUTHENTICATION_PATH_FUNCTIONAL",
                "to": "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
                "kind": "JOINT_PRIVATE_GET_FACT",
            },
            {
                "from": "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
                "to": "AUTHENTICATION_PATH_FUNCTIONAL",
                "kind": "JOINT_PRIVATE_GET_FACT",
            },
        ],
        "fresh_private_get_constituents": [
            "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
            "AUTHENTICATION_PATH_FUNCTIONAL",
            "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
        ],
        "offline_constituents": [
            name
            for name in REACHABILITY_CONSTITUENTS
            if name
            not in {
                "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE",
                "AUTHENTICATION_PATH_FUNCTIONAL",
                "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL",
            }
        ],
        "post_dependency": "NOT_PART_OF_REACHABILITY",
    }


def build_authority_boundary_map_v1() -> dict[str, Any]:
    return {
        "schema_version": "section_11_14_authority_boundary_map.v1",
        "status": "BOUND",
        "this_go_may": [
            "BIND_PATH_REACHABLE_PREDICATE",
            "PROVE_STATIC_CONSTITUENTS",
            "INSPECT_REPO_DEFAULTS_WITHOUT_MUTATION",
            "CONDITIONAL_PRIVATE_GET",
            "PERSIST_SANITIZED_GET_EVIDENCE",
            "SET_LIVE_EXECUTION_PATH_REACHABLE_IF_CONJUNCTION_PROVEN",
        ],
        "this_go_must_not": [
            "POST",
            "ORDER_SUBMIT",
            "CANCEL",
            "AMEND",
            "FLATTEN_EXECUTE",
            "FUNDING",
            "LIVE_ENABLED_MUTATION",
            "LIVE_ARMED_MUTATION",
            "SUBMIT_UNLOCKED_MUTATION",
            "CANARY_AUTHORIZED_MUTATION",
            "PROMOTE_LIVE_PRIVATE_READ_ONLY_PROVEN",
            "PROMOTE_LATER_LADDER_FIELDS",
            "MARK_SECTION_11_14_COMPLETE",
        ],
        "boundaries": [
            {
                "name": "PRE_SUBMIT_BOUNDARY",
                "role": ROLE_PART_OF_REACHABILITY,
                "description": "Gate evaluation plus authenticated read connectivity.",
            },
            {
                "name": "SUBMIT_AUTHORIZATION_BOUNDARY",
                "role": ROLE_REQUIRED_ONLY_FOR_SUBMIT_AUTHORIZATION,
                "description": "LIVE_ENABLED/ARMED/SUBMIT_UNLOCKED/CANARY_AUTHORIZED/execute permit.",
            },
            {
                "name": "PRIVATE_READ_ONLY_PROVEN_BOUNDARY",
                "role": ROLE_REQUIRED_ONLY_FOR_LATER_LADDER_STAGE,
                "description": "§11.14 LIVE_PRIVATE_READ_ONLY_PROVEN requires a later Owner-GO.",
            },
        ],
    }
