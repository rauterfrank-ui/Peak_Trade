"""Static Live-execution graph and LIVE_EXECUTION_CODE_EXISTS predicate.

Offline only. Does not contact a venue, load credentials, or infer
reachability, authorization, or later §11.14 ladder fields.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ADMISSIBLE_OFFLINE_SOURCE_KINDS,
    CANONICAL_RUNBOOK_PATH,
    CANONICAL_SECTION_HEADING,
    FORBIDDEN_LIVE_SOURCE_KINDS,
    LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)

COMPONENT_CLASSES: tuple[str, ...] = (
    "IMPLEMENTED_COMPONENT",
    "INTEGRATED_COMPONENT",
    "DEAD_OR_UNREACHABLE_CODE",
    "TEST_ONLY",
    "FIXTURE_ONLY",
    "HISTORICAL_ONLY",
    "CURRENT_PRODUCTIVE_PATH",
    "UNKNOWN",
)

DISALLOWED_PREDICATE_CLASSES: frozenset[str] = frozenset(
    {
        "DEAD_OR_UNREACHABLE_CODE",
        "TEST_ONLY",
        "FIXTURE_ONLY",
        "HISTORICAL_ONLY",
        "UNKNOWN",
    }
)

STATIC_EDGE_CHAIN: tuple[str, ...] = (
    "DECISION_GATE",
    "GATE_REFUSAL",
    "SUBMIT_ORCHESTRATOR",
    "ORDER_PLAN_CONSUMER",
    "PAYLOAD_BUILDER",
    "CLIENT_ORDER_ID",
    "LIVE_HTTP_PORT",
    "LIVE_HTTP_TRANSPORT",
)


@dataclass(frozen=True)
class GraphNodeV1:
    node_id: str
    role: str
    path: str
    symbol: str
    required_name_tokens: tuple[str, ...]
    classification: str
    required_for_predicate: bool
    notes: str


def canonical_graph_nodes_v1() -> tuple[GraphNodeV1, ...]:
    return (
        GraphNodeV1(
            node_id="SP02_SUBMIT_GATES_EVALUATE",
            role="DECISION_GATE",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py"),
            symbol="evaluate_canary_submit_gates_v1",
            required_name_tokens=("submit_allowed", "OWNER_GO_EXECUTE"),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="Canonical Live execution decision/gate boundary.",
        ),
        GraphNodeV1(
            node_id="SP02_SUBMIT_GATES_REFUSE",
            role="GATE_REFUSAL",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_gates_v1.py"),
            symbol="refuse_submit_unless_gates_pass_v1",
            required_name_tokens=("CANARY_SUBMIT_HARD_BLOCKED",),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="Fail-closed refusal before transport invocation.",
        ),
        GraphNodeV1(
            node_id="SP02_SUBMIT_TRANSPORT",
            role="SUBMIT_ORCHESTRATOR",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"),
            symbol="run_canary_submit_transport_v1",
            required_name_tokens=(
                "evaluate_canary_submit_gates_v1",
                "refuse_submit_unless_gates_pass_v1",
                "build_minimum_valid_canary_order_plan_v1",
                "post_entry_order",
            ),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="Class-B Live canary orchestrator. Integrates gates, plan, POST.",
        ),
        GraphNodeV1(
            node_id="SP02_ORDER_PLAN",
            role="ORDER_PLAN_CONSUMER",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/order_plan_v1.py"),
            symbol="build_minimum_valid_canary_order_plan_v1",
            required_name_tokens=(
                "build_venue_native_order_body_v1",
                "serialize_canary_clordid_v1",
            ),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="Live canary order-plan builder consumed by the submit orchestrator.",
        ),
        GraphNodeV1(
            node_id="VENUE_NATIVE_PAYLOAD",
            role="PAYLOAD_BUILDER",
            path=(
                "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
                "okx_response_mapper_v1.py"
            ),
            symbol="build_venue_native_order_body_v1",
            required_name_tokens=("clOrdId", "instId", "tdMode"),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=True,
            notes=(
                "Canonical REQUEST_BODY_OWNER reused on the Live canary path. "
                "Package location is historical Testnet; current Live integration "
                "is proven by the order-plan import/call, not by Testnet execution."
            ),
        ),
        GraphNodeV1(
            node_id="CLIENT_ORDER_ID",
            role="CLIENT_ORDER_ID",
            path="src/ops/okx_europe_adapter_lifecycle_contract_v0.py",
            symbol="build_client_order_id",
            required_name_tokens=("CLIENT_ORDER_ID",),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=True,
            notes="Idempotency / clOrdId machinery consumed by serialize_canary_clordid_v1.",
        ),
        GraphNodeV1(
            node_id="SP01_HTTP_PORT",
            role="LIVE_HTTP_PORT",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
            symbol="LiveCanaryHttpClientV1",
            required_name_tokens=("post_entry_order", "DUPLICATE_ENTRY_SUBMIT_FORBIDDEN"),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="§4.9 SP-01 Live canary HTTP port. Class A.",
        ),
        GraphNodeV1(
            node_id="SP01_URLLIB_TRANSPORT",
            role="LIVE_HTTP_TRANSPORT",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
            symbol="UrllibLiveCanaryTransportV1",
            required_name_tokens=("send", "PRODUCTIVE_WIRE_SEND_DISABLED", "build_opener"),
            classification="CURRENT_PRODUCTIVE_PATH",
            required_for_predicate=True,
            notes="Concrete urllib Live POST invocation surface.",
        ),
        GraphNodeV1(
            node_id="SP01_ACK_EVIDENCE",
            role="RESPONSE_ACK_HANDLING",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
            symbol="extract_canary_http_response_evidence_v1",
            required_name_tokens=("http_status", "okx_code"),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=True,
            notes="Response/ack extraction used by the submit orchestrator.",
        ),
        GraphNodeV1(
            node_id="SP01_REQUEST_EVIDENCE",
            role="EVIDENCE_PROVENANCE",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
            symbol="extract_canary_venue_native_request_evidence_v1",
            required_name_tokens=("CANARY_VENUE_NATIVE_REQUEST_FIELDS_V1",),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=True,
            notes="Request provenance extraction. Not Live observation.",
        ),
        GraphNodeV1(
            node_id="FLATTEN_EXECUTE",
            role="FLATTEN_EXECUTION",
            path=(
                "src/ops/section_11_13_5_productive_flatten_post_and_reconciliation_v1/"
                "execute_v1.py"
            ),
            symbol="execute_productive_flatten_post_and_reconciliation_v1",
            required_name_tokens=("submit_productive_flatten_v1",),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=False,
            notes="Inventoried Live flatten execution. Separate mutation path.",
        ),
        GraphNodeV1(
            node_id="FLATTEN_GATED_SUBMIT",
            role="FLATTEN_EXECUTION",
            path=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/flatten_gated_submit_v1.py"
            ),
            symbol="submit_productive_flatten_v1",
            required_name_tokens=("FlattenGatedSubmitBoundaryV1",),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=False,
            notes="Inventoried flatten submit boundary.",
        ),
        GraphNodeV1(
            node_id="FORENSIC_RECONCILIATION",
            role="RECONCILIATION_HOOK",
            path=(
                "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
                "forensic_reconciliation_v1.py"
            ),
            symbol="classify_from_sealed_evidence_roots_v1",
            required_name_tokens=("classify_hard_stop_layers_from_sealed_snapshots_v1",),
            classification="INTEGRATED_COMPONENT",
            required_for_predicate=False,
            notes="Inventoried reconciliation hook. Not a Live observed field.",
        ),
        GraphNodeV1(
            node_id="LIFECYCLE_KILL_SWITCH_CONTRACT",
            role="KILL_SWITCH_INTEGRATION",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/lifecycle_v1.py"),
            symbol="build_lifecycle_and_closeout_contract_v1",
            required_name_tokens=("emergency_kill_switch_interaction",),
            classification="IMPLEMENTED_COMPONENT",
            required_for_predicate=False,
            notes=(
                "Kill-switch interaction is contract-bound on the canary lifecycle. "
                "Not a static callee of run_canary_submit_transport_v1."
            ),
        ),
        GraphNodeV1(
            node_id="RISK_LAYER_KILL_SWITCH",
            role="KILL_SWITCH_INTEGRATION",
            path="src/risk_layer/kill_switch/core.py",
            symbol="KillSwitch",
            required_name_tokens=("check_and_block", "trigger"),
            classification="IMPLEMENTED_COMPONENT",
            required_for_predicate=False,
            notes="Risk-layer kill switch implementation. Not the §11.14 Live submit chain.",
        ),
        GraphNodeV1(
            node_id="FAKE_TRANSPORT",
            role="FIXTURE_TRANSPORT",
            path=("src/ops/section_11_13_5_live_canary_minimum_exposure_v1/http_client_v1.py"),
            symbol="RecordingFakeCanaryTransportV1",
            required_name_tokens=("send",),
            classification="FIXTURE_ONLY",
            required_for_predicate=False,
            notes="Inadmissible as Live proof. Must not satisfy the predicate.",
        ),
        GraphNodeV1(
            node_id="SP04_TESTNET_PORT",
            role="TESTNET_EXECUTION_PORT",
            path=(
                "src/ops/section_11_12_8_actual_productive_testnet_campaign_run_start_v1/"
                "productive_execution_port_v1.py"
            ),
            symbol="ProductiveTestnetExecutionPortV1",
            required_name_tokens=("submit_order_v1",),
            classification="HISTORICAL_ONLY",
            required_for_predicate=False,
            notes="§4.9 SP-04 Testnet. Inadmissible as Live execution code.",
        ),
        GraphNodeV1(
            node_id="SP10_KRAKEN_LIVE",
            role="HISTORICAL_LIVE_TRANSPORT",
            path="src/exchange/kraken_live.py",
            symbol="KrakenLiveClient",
            required_name_tokens=("place_order",),
            classification="HISTORICAL_ONLY",
            required_for_predicate=False,
            notes="§4.9 SP-10 historical bounded-pilot. Not the canonical OKX EEA Live path.",
        ),
    )


def _module_ast(repo_root: Path, rel: str) -> ast.Module | None:
    path = repo_root / rel
    if not path.is_file():
        return None
    return ast.parse(path.read_text(encoding="utf-8"), filename=rel)


def _iter_named_nodes(tree: ast.AST) -> dict[str, ast.AST]:
    found: dict[str, ast.AST] = {}
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            found[node.name] = node
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        found[f"{node.name}.{child.name}"] = child
                        found[child.name] = child
    return found


def _source_of(node: ast.AST) -> str:
    return ast.unparse(node)


def inspect_node_v1(*, repo_root: Path, spec: GraphNodeV1) -> dict[str, Any]:
    tree = _module_ast(repo_root, spec.path)
    file_exists = tree is not None
    named = _iter_named_nodes(tree) if tree is not None else {}
    symbol_found = spec.symbol in named
    source = _source_of(named[spec.symbol]) if symbol_found else ""
    missing_tokens = [token for token in spec.required_name_tokens if token not in source]
    integrated = file_exists and symbol_found and not missing_tokens
    return {
        "node_id": spec.node_id,
        "role": spec.role,
        "path": spec.path,
        "symbol": spec.symbol,
        "classification": spec.classification,
        "required_for_predicate": spec.required_for_predicate,
        "notes": spec.notes,
        "file_exists": file_exists,
        "symbol_found": symbol_found,
        "missing_tokens": missing_tokens,
        "integrated": integrated,
    }


def file_presence_alone_v1(*, repo_root: Path, paths: Sequence[str]) -> dict[str, Any]:
    existing = [rel for rel in paths if (repo_root / rel).is_file()]
    return {
        "probe_name": "FILE_PRESENCE_ALONE",
        "admissible_as_live_execution_code_exists": False,
        "all_listed_files_exist": len(existing) == len(tuple(paths)) and bool(paths),
        "existing_paths": existing,
        "reason": "CODE_PRESENCE_ALONE_INADMISSIBLE",
    }


def build_static_execution_graph_v1(
    *,
    repo_root: Path,
    nodes: Sequence[GraphNodeV1] | None = None,
) -> dict[str, Any]:
    specs = tuple(nodes) if nodes is not None else canonical_graph_nodes_v1()
    inspections = [inspect_node_v1(repo_root=repo_root, spec=spec) for spec in specs]
    required = [item for item in inspections if item["required_for_predicate"] is True]
    required_ok = all(
        item["integrated"] is True and item["classification"] not in DISALLOWED_PREDICATE_CLASSES
        for item in required
    )
    roles_present = {item["role"] for item in required if item["integrated"] is True}
    chain_complete = all(role in roles_present for role in STATIC_EDGE_CHAIN)
    classification_summary = {
        item["node_id"]: {
            "classification": item["classification"],
            "integrated": item["integrated"],
            "required_for_predicate": item["required_for_predicate"],
        }
        for item in inspections
    }
    return {
        "schema_version": "section_11_14_static_execution_graph.v1",
        "canonical_path": (
            "evaluate_canary_submit_gates_v1 -> "
            "refuse_submit_unless_gates_pass_v1 -> "
            "run_canary_submit_transport_v1 -> "
            "build_minimum_valid_canary_order_plan_v1 -> "
            "build_venue_native_order_body_v1 / build_client_order_id -> "
            "LiveCanaryHttpClientV1.post_entry_order -> "
            "UrllibLiveCanaryTransportV1.send"
        ),
        "STATIC_EDGE_CHAIN": list(STATIC_EDGE_CHAIN),
        "chain_complete": chain_complete,
        "required_nodes_integrated": required_ok,
        "nodes": inspections,
        "classification_summary": classification_summary,
        "runtime_invoked": False,
        "credentials_used": False,
        "path_reachable_inferred": False,
        "authorization_inferred": False,
    }


def evaluate_live_execution_code_exists_predicate_v1(
    *,
    repo_root: Path,
    source_kind: str = "REPOSITORY_IMPLEMENTATION",
    graph: Mapping[str, Any] | None = None,
    nodes: Sequence[GraphNodeV1] | None = None,
) -> dict[str, Any]:
    kind = str(source_kind or "").strip().upper()
    if kind in FORBIDDEN_LIVE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(
            f"FORBIDDEN_LIVE_SOURCE:{kind}:LIVE_EXECUTION_CODE_EXISTS"
        )
    if kind == "GOVERNED_CURRENT_PRIVATE_GET":
        raise Section1114OfflineSurfaceError(
            "PRIVATE_GET_CANNOT_SATISFY_LIVE_EXECUTION_CODE_EXISTS"
        )
    if kind not in ADMISSIBLE_OFFLINE_SOURCE_KINDS:
        raise Section1114OfflineSurfaceError(f"SOURCE_KIND_NOT_ADMISSIBLE:{kind}")
    built = (
        dict(graph)
        if graph is not None
        else build_static_execution_graph_v1(
            repo_root=repo_root,
            nodes=nodes,
        )
    )
    required = [item for item in built["nodes"] if item["required_for_predicate"] is True]
    disallowed = [
        item["node_id"]
        for item in required
        if item["classification"] in DISALLOWED_PREDICATE_CLASSES
    ]
    missing = [item["node_id"] for item in required if item["integrated"] is not True]
    conjuncts = {
        "CANONICAL_DEFINITION_BOUND": bool(LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION),
        "SOURCE_KIND_ADMISSIBLE": kind in ADMISSIBLE_OFFLINE_SOURCE_KINDS,
        "SOURCE_KIND_NOT_FIXTURE_TESTNET_SIM": kind not in FORBIDDEN_LIVE_SOURCE_KINDS,
        "REQUIRED_NODES_INTEGRATED": not missing,
        "REQUIRED_NODES_NOT_DISALLOWED_CLASS": not disallowed,
        "STATIC_EDGE_CHAIN_COMPLETE": bool(built.get("chain_complete") is True),
        "FILE_PRESENCE_ALONE_REJECTED": True,
        "PATH_REACHABLE_NOT_INFERRED": built.get("path_reachable_inferred") is False,
        "AUTHORIZATION_NOT_INFERRED": built.get("authorization_inferred") is False,
    }
    admissible = all(bool(value) is True for value in conjuncts.values())
    return {
        "canonical_definition": LIVE_EXECUTION_CODE_EXISTS_CANONICAL_DEFINITION,
        "admissibility_predicate": (
            "LIVE_EXECUTION_CODE_EXISTS is true iff current origin/main contains a "
            "complete integrated static call graph from the Live canary decision/"
            "gate boundary through order-plan consumption, venue-native payload "
            "and client-order-id construction, fail-closed submit gates, the Live "
            "HTTP port, and UrllibLiveCanaryTransportV1.send. File presence, "
            "historical code, fixture/testnet/sim/paper/shadow sources, Cap "
            "11.7-11.11 contracts-only constants, and §4.9 CURRENTLY_REACHABLE "
            "are each insufficient. True does not imply LIVE_EXECUTION_PATH_"
            "REACHABLE, authorization, credentials, or any later ladder field."
        ),
        "source_kind": kind,
        "conjuncts": conjuncts,
        "missing_required_nodes": missing,
        "disallowed_required_nodes": disallowed,
        "admissible": admissible,
        "claim_value": admissible,
        "graph_status": "COMPLETE" if conjuncts["STATIC_EDGE_CHAIN_COMPLETE"] else "INCOMPLETE",
        "canonical_location": f"{CANONICAL_RUNBOOK_PATH} {CANONICAL_SECTION_HEADING}",
    }
