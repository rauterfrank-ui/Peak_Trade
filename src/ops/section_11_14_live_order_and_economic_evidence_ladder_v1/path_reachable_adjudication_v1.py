"""Adjudicate LIVE_EXECUTION_PATH_REACHABLE from static proof plus optional GET."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_IMPLEMENTED,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    RecordingFakeCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
    refuse_submit_unless_gates_pass_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_SUBMIT_TRANSPORT_PATH,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    SP01_PATH,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
    inspect_credential_material_presence_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.path_reachable_predicate_v1 import (
    ADMISSIBILITY_PREDICATE,
    REACHABILITY_CONSTITUENT_COUNT,
    REACHABILITY_CONSTITUENTS,
    evaluate_reachability_conjunction_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.static_execution_graph_v1 import (
    build_static_execution_graph_v1,
    evaluate_live_execution_code_exists_predicate_v1,
)


def _static_constituents_v1(*, repo_root: Path) -> dict[str, Any]:
    graph = build_static_execution_graph_v1(repo_root=repo_root)
    code_exists = evaluate_live_execution_code_exists_predicate_v1(
        repo_root=repo_root,
        source_kind="REPOSITORY_IMPLEMENTATION",
        graph=graph,
    )
    graph_complete = bool(code_exists["claim_value"] is True) and bool(
        graph.get("chain_complete") is True
    )
    required = [item for item in graph["nodes"] if item["required_for_predicate"] is True]
    entry = next(item for item in required if item["symbol"] == "run_canary_submit_transport_v1")
    gates_eval = next(
        item for item in required if item["symbol"] == "evaluate_canary_submit_gates_v1"
    )
    gates_refuse = next(
        item for item in required if item["symbol"] == "refuse_submit_unless_gates_pass_v1"
    )
    transport = next(item for item in required if item["symbol"] == "UrllibLiveCanaryTransportV1")
    port = next(item for item in required if item["symbol"] == "LiveCanaryHttpClientV1")
    selectable = (
        entry["integrated"] is True
        and CANARY_SUBMIT_TRANSPORT_IMPLEMENTED is True
        and Path(repo_root, CANARY_SUBMIT_TRANSPORT_PATH).is_file()
    )
    gates_evaluable = (
        gates_eval["integrated"] is True
        and gates_refuse["integrated"] is True
        and callable(evaluate_canary_submit_gates_v1)
        and callable(refuse_submit_unless_gates_pass_v1)
    )
    constructed = False
    construct_error = None
    try:
        fake = RecordingFakeCanaryTransportV1()
        client = LiveCanaryHttpClientV1(
            rest_base=f"https://{REUSED_BINDING_REST_HOST}",
            rest_host=REUSED_BINDING_REST_HOST,
            transport=fake,
            max_request_count=1,
            max_retries=0,
        )
        wire = UrllibLiveCanaryTransportV1(wire_send_enabled=False)
        constructed = (
            isinstance(client, LiveCanaryHttpClientV1)
            and isinstance(wire, UrllibLiveCanaryTransportV1)
            and hasattr(client, "get")
            and hasattr(client, "post_entry_order")
            and callable(wire.send)
        )
        del client, wire, fake
    except Exception as exc:  # noqa: BLE001 — construction failure is a constituent fact
        construct_error = type(exc).__name__
        constructed = False
    transport_constructible = (
        transport["integrated"] is True
        and port["integrated"] is True
        and constructed is True
        and Path(repo_root, SP01_PATH).is_file()
    )
    no_static_blocker = (
        graph_complete
        and selectable
        and gates_evaluable
        and transport_constructible
        and LIVE_EXECUTION_CODE_EXISTS is True
    )
    return {
        "STATIC_EXECUTION_GRAPH_COMPLETE": graph_complete,
        "ENTRYPOINT_INTEGRATED": bool(entry["integrated"] is True),
        "CURRENT_RUNTIME_PATH_SELECTABLE": bool(selectable),
        "REQUIRED_FAIL_CLOSED_GATES_EVALUABLE": bool(gates_evaluable),
        "TRANSPORT_CONSTRUCTIBLE": bool(transport_constructible),
        "NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY": bool(no_static_blocker),
        "graph": graph,
        "code_exists": code_exists,
        "construct_error": construct_error,
    }


def adjudicate_live_execution_path_reachable_v1(
    *,
    repo_root: Path,
    credential_presence: Mapping[str, Any] | None = None,
    private_get_evidence: Mapping[str, Any] | None = None,
    source_kind: str = "REPOSITORY_IMPLEMENTATION",
) -> dict[str, Any]:
    static = _static_constituents_v1(repo_root=repo_root)
    if credential_presence is None:
        presence = inspect_credential_material_presence_v1(
            vault_file=default_vault_path_v1(repo_root=repo_root)
        )
    else:
        presence = dict(credential_presence)
    get_ev = dict(private_get_evidence or {})
    host = get_ev.get("TARGET_HOST_RESOLVABLE_OR_CONNECTABLE")
    auth = get_ev.get("AUTHENTICATION_PATH_FUNCTIONAL")
    read = get_ev.get("CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL")
    values: dict[str, bool | None] = {
        "STATIC_EXECUTION_GRAPH_COMPLETE": bool(static["STATIC_EXECUTION_GRAPH_COMPLETE"]),
        "ENTRYPOINT_INTEGRATED": bool(static["ENTRYPOINT_INTEGRATED"]),
        "CURRENT_RUNTIME_PATH_SELECTABLE": bool(static["CURRENT_RUNTIME_PATH_SELECTABLE"]),
        "REQUIRED_FAIL_CLOSED_GATES_EVALUABLE": bool(
            static["REQUIRED_FAIL_CLOSED_GATES_EVALUABLE"]
        ),
        "TRANSPORT_CONSTRUCTIBLE": bool(static["TRANSPORT_CONSTRUCTIBLE"]),
        "REQUIRED_CREDENTIAL_MATERIAL_AVAILABLE": (
            True if presence.get("available") is True else False
        ),
        "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE": (
            None if "TARGET_HOST_RESOLVABLE_OR_CONNECTABLE" not in get_ev else bool(host)
        ),
        "AUTHENTICATION_PATH_FUNCTIONAL": (
            None if "AUTHENTICATION_PATH_FUNCTIONAL" not in get_ev else bool(auth)
        ),
        "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL": (
            None if "CURRENT_ACCOUNT_OR_VENUE_READ_ACCESS_FUNCTIONAL" not in get_ev else bool(read)
        ),
        "NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY": bool(
            static["NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY"]
        ),
    }
    result = evaluate_reachability_conjunction_v1(
        constituent_values=values,
        source_kind=source_kind,
    )
    if result["claim_value"] is True and LIVE_PRIVATE_READ_ONLY_PROVEN is True:
        raise Section1114OfflineSurfaceError("PATH_REACHABLE_PROMOTED_PRIVATE_READ_ONLY_PROVEN")
    if get_ev.get("LIVE_PRIVATE_READ_ONLY_PROVEN") is True:
        raise Section1114OfflineSurfaceError("GET_EVIDENCE_PROMOTED_LIVE_PRIVATE_READ_ONLY_PROVEN")
    if get_ev.get("POST_USED") is True:
        raise Section1114OfflineSurfaceError("POST_INVOKED_BY_REACHABILITY_PROOF")
    return {
        "canonical_definition": result["canonical_definition"],
        "admissibility_predicate": ADMISSIBILITY_PREDICATE,
        "reachability_constituent_count": REACHABILITY_CONSTITUENT_COUNT,
        "reachability_constituents": list(REACHABILITY_CONSTITUENTS),
        "constituent_values": values,
        "static": {
            key: static[key]
            for key in (
                "STATIC_EXECUTION_GRAPH_COMPLETE",
                "ENTRYPOINT_INTEGRATED",
                "CURRENT_RUNTIME_PATH_SELECTABLE",
                "REQUIRED_FAIL_CLOSED_GATES_EVALUABLE",
                "TRANSPORT_CONSTRUCTIBLE",
                "NO_STATIC_BLOCKER_PREVENTS_REACHING_PRE_SUBMIT_BOUNDARY",
                "construct_error",
            )
        },
        "credential_presence": presence,
        "private_get_evidence_present": bool(get_ev),
        "conjunction": result,
        "adjudicated_value": bool(result["claim_value"] is True),
        "adjudication": result["adjudication"],
        "reason": result["reason"],
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "submit_authorization_inferred": False,
        "gate_mutation_performed": False,
        "post_used": False,
    }
