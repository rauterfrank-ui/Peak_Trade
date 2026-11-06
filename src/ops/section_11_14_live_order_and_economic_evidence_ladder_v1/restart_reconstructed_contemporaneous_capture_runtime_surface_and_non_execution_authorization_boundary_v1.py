"""Prove the contemporaneous capture runtime surface and authorization boundary.

Offline forensic census only. Does not GET. Does not POST. Does not wire-send.
Does not submit. Does not restart. Does not execute productive contemporaneous
capture. Does not lift Live/canary/testnet gates. Does not invent an isolated
capture shortcut. COMPLETE_CAPTURE_SEAM remains PROVEN as the predecessor
offline contract. CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED remains false.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_caller_v1 import (
    CALLER_RELPATH,
    HOST_JOIN_RELPATH,
    HOST_JOIN_SYMBOL,
    PRODUCTIVE_HOOK_CALLER,
    build_contemporaneous_field_provenance_from_bound_fill_v1,
    compose_live_order_pre_restart_capture_host_graph_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_restart_handoff_capture_hook_v1 import (
    run_capture_hook_after_bound_fill_before_restart_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    AMEND_ALLOWED,
    CANARY_AUTHORIZED,
    CANCEL_ALLOWED,
    CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED,
    CREDENTIAL_USE_ALLOWED,
    FLATTEN_EXECUTE_ALLOWED,
    FUNDING_ALLOWED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_RESTART_RECONSTRUCTED,
    ORDER_SUBMIT_ALLOWED,
    POST_ALLOWED,
    PRIVATE_GET_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
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
    INPUT_CLASS_TEST_FIXTURE,
    census_productive_capture_dataflow_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_create_productive_capture_owner_and_lifecycle_hook_v1 import (
    CANONICAL_BOUND_FILL_KIND,
    FORBIDDEN_BOUND_FILL_KINDS,
    HOOK_RELPATH,
    PRODUCTIVE_CAPTURE_OWNER,
    PRODUCTIVE_LIFECYCLE_HOOK,
    RESTART_BOUNDARY_PATH,
    RESTART_BOUNDARY_SYMBOL,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_future_authorized_contemporaneous_capture_window_v1 import (
    PRODUCER_RELPATH,
    PRODUCER_SYMBOL,
    WRITER_RELPATH,
    WRITER_SYMBOL,
    census_symbol_call_graph_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_owner_and_writer_v1 import (
    HANDOFF_FILENAME,
    RELATIVE_DURABLE_DIR,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    ADMISSIBLE_POS_SOURCE_KIND,
    REQUIRED_CAPTURE_TRIGGER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    POS_UNIT,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_productive_capture_hook_caller_binding_and_offline_call_path_proof_v1 import (
    census_productive_hook_caller_v1,
)

CANARY_EXECUTE_SYMBOL = "run_section_11_13_5_live_canary_minimum_exposure_v1"
CANARY_SUBMIT_TRANSPORT_SYMBOL = "run_canary_submit_transport_v1"
CANARY_RUNNER_RELPATH = "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/runner_v1.py"
CANARY_SUBMIT_TRANSPORT_RELPATH = (
    "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py"
)
ACCEPTANCE_SYMBOL = "accept_complete_contemporaneous_capture_inputs_v1"
SERIALIZER_SYMBOL = "_canonical_dumps"
PERSIST_SYMBOL = "_atomic_replace_write"
CAPTURE_POINT = "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
PRODUCTIVE_RUNTIME_ENTRYPOINT = HOST_JOIN_SYMBOL
CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE = "PROVEN"
CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY = "PROVEN"
CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION = False
CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE = True
MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT = "NONE_CAPTURE_ONLY"
UNAVOIDABLE_EXTERNAL_EFFECTS = "LIVE_IDENTITY_BOUND_VENUE_FILL"
EARLIEST_IRREVERSIBLE_EFFECT = "VENUE_FILL_OF_IDENTITY_BOUND_ORDER"
UNAVOIDABLE_PRODUCTIVE_PREDECESSOR = (
    "LIVE_IDENTITY_BOUND_VENUE_FILL after identity-bound venue fill of a "
    "previously submitted order; historical BOUND_* identity and TEST_FIXTURE "
    "are not valid productive contemporaneous provenance"
)
CASE_ADJUDICATION = (
    "CASE_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_SIDE_EFFECT_BOUNDARY_"
    "PROVEN_ISOLATION_FROM_LIVE_EXECUTION_FALSE_NO_EXECUTION"
)
PROPOSED_NEXT_SLICE = (
    "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_"
    "REQUIRES_SEPARATE_OWNER_GO_V1"
)
FORBIDDEN_CALL_ATTRS: frozenset[str] = frozenset(
    {
        "send",
        "urlopen",
        "request",
        "post",
        "POST",
        "restart",
        "reboot",
        "os._exit",
        "sys.exit",
        "kill",
    }
)
CAPTURE_SURFACE_RELPATHS: tuple[str, ...] = (
    HOST_JOIN_RELPATH,
    CALLER_RELPATH,
    HOOK_RELPATH,
    WRITER_RELPATH,
    PRODUCER_RELPATH,
)
_FORBIDDEN_NETWORK_MODULES: frozenset[str] = frozenset(
    {"http.client", "urllib.request", "urllib3", "requests", "aiohttp", "socket"}
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _repo_root(repo_root: object | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[3]
    return Path(repo_root)


def _parse_module(*, repo_root: Path, relpath: str) -> ast.Module:
    path = repo_root / relpath
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise Section1114OfflineSurfaceError("CALL_GRAPH_PARSE_FAILURE") from exc


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _function_calls_symbol(*, tree: ast.Module, function_name: str, symbol: str) -> bool:
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != function_name:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and _call_name(child.func) == symbol:
                return True
    return False


def _module_imports_network(*, tree: ast.Module) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = str(alias.name or "")
                if name in _FORBIDDEN_NETWORK_MODULES or name.split(".", 1)[0] in {
                    "requests",
                    "urllib3",
                    "aiohttp",
                }:
                    hits.append(name)
        if isinstance(node, ast.ImportFrom):
            module = str(node.module or "")
            if module in _FORBIDDEN_NETWORK_MODULES or module.startswith("urllib.request"):
                hits.append(module)
    return hits


def _module_calls_forbidden_effects(*, tree: ast.Module) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name in FORBIDDEN_CALL_ATTRS:
            hits.append(name)
    return hits


def _function_forbidden_effects(*, tree: ast.Module, function_name: str) -> list[str]:
    hits: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != function_name:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and _call_name(child.func) in FORBIDDEN_CALL_ATTRS:
                hits.append(_call_name(child.func))
    return hits


def census_productive_entrypoint_candidates_v1(
    *, repo_root: object | None = None
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    caller_census = census_symbol_call_graph_v1(
        repo_root=root,
        symbol=PRODUCTIVE_HOOK_CALLER,
        definition_relpath=CALLER_RELPATH,
    )
    host_join_census = census_symbol_call_graph_v1(
        repo_root=root,
        symbol=HOST_JOIN_SYMBOL,
        definition_relpath=HOST_JOIN_RELPATH,
    )
    canary_tree = _parse_module(repo_root=root, relpath=CANARY_RUNNER_RELPATH)
    submit_tree = _parse_module(repo_root=root, relpath=CANARY_SUBMIT_TRANSPORT_RELPATH)
    host_join_calls_caller = _function_calls_symbol(
        tree=canary_tree,
        function_name=HOST_JOIN_SYMBOL,
        symbol=PRODUCTIVE_HOOK_CALLER,
    )
    execute_calls_host_join = _function_calls_symbol(
        tree=canary_tree,
        function_name=CANARY_EXECUTE_SYMBOL,
        symbol=HOST_JOIN_SYMBOL,
    )
    execute_calls_caller = _function_calls_symbol(
        tree=canary_tree,
        function_name=CANARY_EXECUTE_SYMBOL,
        symbol=PRODUCTIVE_HOOK_CALLER,
    )
    submit_calls_host_join = _function_calls_symbol(
        tree=submit_tree,
        function_name=CANARY_SUBMIT_TRANSPORT_SYMBOL,
        symbol=HOST_JOIN_SYMBOL,
    )
    submit_calls_caller = _function_calls_symbol(
        tree=submit_tree,
        function_name=CANARY_SUBMIT_TRANSPORT_SYMBOL,
        symbol=PRODUCTIVE_HOOK_CALLER,
    )
    productive_caller_rows = [
        row
        for row in caller_census["rows"]
        if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    productive_host_join_rows = [
        row
        for row in host_join_census["rows"]
        if row["PRODUCTIVE_OR_TEST_ONLY"] == "PRODUCTIVE_RUNTIME"
    ]
    if not host_join_calls_caller:
        raise Section1114OfflineSurfaceError("HOST_JOIN_MUST_CALL_UNIQUE_PRODUCTIVE_CALLER")
    if execute_calls_host_join or execute_calls_caller:
        raise Section1114OfflineSurfaceError("CANARY_EXECUTE_MUST_NOT_INVOKE_CAPTURE")
    if submit_calls_host_join or submit_calls_caller:
        raise Section1114OfflineSurfaceError("CANARY_SUBMIT_MUST_NOT_INVOKE_CAPTURE")
    if len(productive_caller_rows) != 1:
        raise Section1114OfflineSurfaceError("PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER")
    if productive_caller_rows[0]["FILE"] != HOST_JOIN_RELPATH:
        raise Section1114OfflineSurfaceError("UNIQUE_CALLER_MUST_BE_INVOKED_ONLY_FROM_HOST_JOIN")
    if productive_host_join_rows:
        raise Section1114OfflineSurfaceError("HOST_JOIN_MUST_REMAIN_UNREACHABLE_FROM_EXECUTE")
    rows = (
        {
            "ENTRYPOINT_SYMBOL": CANARY_EXECUTE_SYMBOL,
            "ENTRYPOINT_PATH": CANARY_RUNNER_RELPATH,
            "CALLER": "GOVERNED_CANARY_RUNNER",
            "CALLEE": CANARY_SUBMIT_TRANSPORT_SYMBOL,
            "RUNTIME_OWNER": "SECTION_11_13_5_LIVE_CANARY_MINIMUM_EXPOSURE",
            "TRIGGER": "mode=execute",
            "LIFECYCLE_PHASE": "PRE_SUBMIT_THROUGH_OPTIONAL_WIRE",
            "REACHABILITY": "PRODUCTIVE_REACHABLE_FOR_CANARY_NOT_FOR_CAPTURE",
            "GATES": "CANARY_SUBMIT_GATES; LIVE_ENABLED; LIVE_ARMED; OWNER_GO_EXECUTE",
            "INPUT_SOURCE": "canary config + vault",
            "SIDE_EFFECTS": "POTENTIAL_EXCHANGE_SUBMIT_IF_AUTHORIZED",
            "EXTERNAL_IO": "AUTHENTICATED_NETWORK_WRITE_IF_WIRE_ENABLED",
            "PROCESS_CONTROL": "NONE_IN_CAPTURE_PATH",
            "ERROR_BEHAVIOR": "FAIL_CLOSED",
            "PRODUCTION_STATUS": "IMPLEMENTED_NOT_ACTIVATED",
            "EVIDENCE": "AST_NO_CAPTURE_CALL",
            "CLASSIFICATION": "PRODUCTIVE_REACHABLE",
            "CAPTURE_REACHABLE": False,
        },
        {
            "ENTRYPOINT_SYMBOL": HOST_JOIN_SYMBOL,
            "ENTRYPOINT_PATH": HOST_JOIN_RELPATH,
            "CALLER": "NONE_IN_PRODUCTIVE_LIFECYCLE",
            "CALLEE": PRODUCTIVE_HOOK_CALLER,
            "RUNTIME_OWNER": "LIVE_ORDER_HOST_JOIN",
            "TRIGGER": REQUIRED_CAPTURE_TRIGGER,
            "LIFECYCLE_PHASE": "AFTER_BOUND_FILL_BEFORE_RESTART",
            "REACHABILITY": "DECLARED_PRODUCTIVE_UNREACHABLE_FROM_CANARY_EXECUTE",
            "GATES": "LIVE_ENABLED=false; LIVE_ARMED=false; bound_fill_proven",
            "INPUT_SOURCE": "bound_fill_identity + S05 qty",
            "SIDE_EFFECTS": "FILESYSTEM_WRITE_VIA_HOOK_WRITER",
            "EXTERNAL_IO": "NONE",
            "PROCESS_CONTROL": "NONE",
            "ERROR_BEHAVIOR": "FAIL_CLOSED",
            "PRODUCTION_STATUS": "DECLARED_NOT_JOINED_TO_EXECUTE_RUNTIME",
            "EVIDENCE": "AST_PLUS_CALLGRAPH",
            "CLASSIFICATION": "DECLARED",
            "CAPTURE_REACHABLE": True,
        },
        {
            "ENTRYPOINT_SYMBOL": PRODUCTIVE_HOOK_CALLER,
            "ENTRYPOINT_PATH": CALLER_RELPATH,
            "CALLER": HOST_JOIN_SYMBOL,
            "CALLEE": PRODUCTIVE_LIFECYCLE_HOOK,
            "RUNTIME_OWNER": "LIVE_ORDER_PRODUCTIVE_HOOK_CALLER",
            "TRIGGER": REQUIRED_CAPTURE_TRIGGER,
            "LIFECYCLE_PHASE": "AFTER_BOUND_FILL_BEFORE_RESTART",
            "REACHABILITY": "PRODUCTIVE_REACHABLE_FROM_HOST_JOIN_ONLY",
            "GATES": "WRONG_LIFECYCLE_EVENT; LIVE_GATES_MUST_REMAIN_FALSE",
            "INPUT_SOURCE": "bound_fill_identity parameterized",
            "SIDE_EFFECTS": "DELEGATES_TO_HOOK",
            "EXTERNAL_IO": "NONE",
            "PROCESS_CONTROL": "NONE",
            "ERROR_BEHAVIOR": "FAIL_CLOSED",
            "PRODUCTION_STATUS": "UNIQUE_PRODUCTIVE_CALLER",
            "EVIDENCE": "CALLGRAPH",
            "CLASSIFICATION": "PRODUCTIVE_REACHABLE",
            "CAPTURE_REACHABLE": True,
        },
        {
            "ENTRYPOINT_SYMBOL": "prove_offline_capture_roundtrip_v1",
            "ENTRYPOINT_PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_complete_capture_seam_required_field_"
                "provenance_and_no_backfill_contract_v1.py"
            ),
            "CALLER": "FORENSIC_OFFLINE_CONTRACT",
            "CALLEE": HOST_JOIN_SYMBOL,
            "RUNTIME_OWNER": "SECTION_11_14_OFFLINE_CONTRACT",
            "TRIGGER": "OFFLINE_CONTRACT_PROOF",
            "LIFECYCLE_PHASE": "OFFLINE",
            "REACHABILITY": "OFFLINE_ONLY",
            "GATES": "INPUT_CLASS_TEST_FIXTURE",
            "INPUT_SOURCE": "TEST_FIXTURE",
            "SIDE_EFFECTS": "TEMPDIR_FILESYSTEM_WRITE",
            "EXTERNAL_IO": "NONE",
            "PROCESS_CONTROL": "NONE",
            "ERROR_BEHAVIOR": "FAIL_CLOSED",
            "PRODUCTION_STATUS": "FORENSIC_OFFLINE",
            "EVIDENCE": "CALLGRAPH",
            "CLASSIFICATION": "OFFLINE_ONLY",
            "CAPTURE_REACHABLE": False,
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_PRODUCTIVE_CAPTURE_ENTRYPOINT_CENSUS_V1",
        "PRODUCTIVE_HOOK_CALLER": PRODUCTIVE_HOOK_CALLER,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "HOST_JOIN_SYMBOL": HOST_JOIN_SYMBOL,
        "HOST_JOIN_PRODUCTIVE_LIFECYCLE_REACHABILITY": (
            "PRODUCTIVE_UNREACHABLE_FROM_CANARY_EXECUTE_AND_SUBMIT_TRANSPORT"
        ),
        "CANARY_EXECUTE_INVOKES_CAPTURE": False,
        "CANARY_SUBMIT_TRANSPORT_INVOKES_CAPTURE": False,
        "HOST_JOIN_PRODUCTIVE_CALLER_COUNT": len(productive_host_join_rows),
        "UNIQUE_PRODUCTIVE_CALLER_OF_HOOK_COUNT": len(productive_caller_rows),
        "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME": False,
        "rows": list(rows),
        "caller_census": caller_census,
        "host_join_census": host_join_census,
    }


def census_transitive_capture_callgraph_v1(*, repo_root: object | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    hook_census = census_productive_hook_caller_v1(repo_root=root)
    dataflow = census_productive_capture_dataflow_v1(repo_root=root)
    nodes = (
        {
            "SYMBOL": HOST_JOIN_SYMBOL,
            "PATH": HOST_JOIN_RELPATH,
            "PURPOSE": "Declared LIVE_ORDER production host join after bound fill",
            "INPUTS": "bound_fill_identity, S05 qty, lifecycle_event, timestamps",
            "OUTPUTS": "PRODUCTIVE_HOOK_CALLER_RESULT plus host_graph",
            "MUTATIONS": "NONE_DIRECT",
            "FILESYSTEM_EFFECTS": "NONE_DIRECT",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER",
        },
        {
            "SYMBOL": PRODUCTIVE_HOOK_CALLER,
            "PATH": CALLER_RELPATH,
            "PURPOSE": "Unique productive caller of the capture hook",
            "INPUTS": "bound_fill_proven, LIVE_IDENTITY_BOUND_VENUE_FILL, provenance",
            "OUTPUTS": "hook_result wrapper; CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false",
            "MUTATIONS": "NONE_DIRECT",
            "FILESYSTEM_EFFECTS": "NONE_DIRECT",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "WRONG_LIFECYCLE_EVENT; LIVE_GATES_MUST_REMAIN_FALSE",
        },
        {
            "SYMBOL": PRODUCTIVE_LIFECYCLE_HOOK,
            "PATH": HOOK_RELPATH,
            "PURPOSE": "Unique productive caller of the handoff writer",
            "INPUTS": "accepted capture gates from bound fill",
            "OUTPUTS": "PRODUCTIVE_CAPTURE_HOOK_RESULT",
            "MUTATIONS": "DELEGATES_TO_WRITER",
            "FILESYSTEM_EFFECTS": "INDIRECT_VIA_WRITER",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "RUNTIME_EXECUTION_UNAUTHORIZED unless TEST_FIXTURE",
        },
        {
            "SYMBOL": ACCEPTANCE_SYMBOL,
            "PATH": (
                "src/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
                "restart_reconstructed_complete_contemporaneous_capture_seam_"
                "and_required_field_provenance_v1.py"
            ),
            "PURPOSE": "Fail-closed acceptance of contemporaneous capture inputs",
            "INPUTS": "input_class, bound fill, S05 qty, provenance, timestamps",
            "OUTPUTS": "gates.writer_kwargs",
            "MUTATIONS": "NONE",
            "FILESYSTEM_EFFECTS": "NONE",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "CAPTURE_BEFORE_BOUND_FILL_PROVEN; INPUT_CLASS_REJECTED",
        },
        {
            "SYMBOL": PRODUCTIVE_CAPTURE_OWNER,
            "PATH": HOOK_RELPATH,
            "PURPOSE": "Unique productive capture owner identity",
            "INPUTS": "accepted gates",
            "OUTPUTS": "owner label on hook result",
            "MUTATIONS": "NONE",
            "FILESYSTEM_EFFECTS": "NONE",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "CAPTURE_OWNER_VACANCY",
        },
        {
            "SYMBOL": WRITER_SYMBOL,
            "PATH": WRITER_RELPATH,
            "PURPOSE": "Persist five-field contemporaneous handoff record",
            "INPUTS": "S05 qty, identity, captured_at_utc, provenance",
            "OUTPUTS": "DURABLE_SUCCESS_ACK",
            "MUTATIONS": "FILESYSTEM_WRITE",
            "FILESYSTEM_EFFECTS": (
                f"{RELATIVE_DURABLE_DIR}/{HANDOFF_FILENAME} mkdir+fsync+os.replace"
            ),
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "CAPTURE_TIMESTAMP_MISSING; WRITE_FAILURE",
        },
        {
            "SYMBOL": PRODUCER_SYMBOL,
            "PATH": PRODUCER_RELPATH,
            "PURPOSE": "Emit Peak_Trade-owned S05 pos; internal to writer",
            "INPUTS": "resulting_current_position_qty plus identity",
            "OUTPUTS": "five required handoff fields",
            "MUTATIONS": "NONE",
            "FILESYSTEM_EFFECTS": "NONE",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "QTY_UNAVAILABLE; POS_SOURCE_KIND_REJECTED",
        },
        {
            "SYMBOL": SERIALIZER_SYMBOL,
            "PATH": WRITER_RELPATH,
            "PURPOSE": "Canonical JSON serialization of the handoff record",
            "INPUTS": "handoff record mapping",
            "OUTPUTS": "canonical JSON text",
            "MUTATIONS": "NONE",
            "FILESYSTEM_EFFECTS": "NONE",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "SERIALIZATION_FAILURE",
        },
        {
            "SYMBOL": PERSIST_SYMBOL,
            "PATH": WRITER_RELPATH,
            "PURPOSE": "Atomic durable filesystem persist boundary",
            "INPUTS": "encoded record text",
            "OUTPUTS": "process-restart-readable file",
            "MUTATIONS": "FILESYSTEM_WRITE",
            "FILESYSTEM_EFFECTS": "tmp write, fsync, os.replace, dir fsync",
            "NETWORK_EFFECTS": "NONE",
            "PROCESS_EFFECTS": "NONE",
            "GLOBAL_STATE_EFFECTS": "NONE",
            "FAILURE_MODE": "WRITE_FAILURE; FSYNC_DURABILITY_UNCERTAINTY",
        },
        {
            "SYMBOL": RESTART_BOUNDARY_SYMBOL,
            "PATH": RESTART_BOUNDARY_PATH,
            "PURPOSE": "Process restart boundary AFTER capture; not part of capture",
            "INPUTS": "session_id",
            "OUTPUTS": "stop then start",
            "MUTATIONS": "PROCESS_STOP_START",
            "FILESYSTEM_EFFECTS": "SUPERVISOR_REGISTRY",
            "NETWORK_EFFECTS": "NONE_REQUIRED",
            "PROCESS_EFFECTS": "PROCESS_EXIT_THEN_START",
            "GLOBAL_STATE_EFFECTS": "SESSION_REGISTRY",
            "FAILURE_MODE": "NOT_INVOKED_BY_CAPTURE_SURFACE",
        },
    )
    edges = (
        {
            "from": "LIVE_IDENTITY_BOUND_VENUE_FILL",
            "to": HOST_JOIN_SYMBOL,
            "CALL_CONDITION": "bound_fill_proven is True and kind is canonical",
            "GATE": "CAPTURE_BEFORE_BOUND_FILL_PROVEN / BOUND_FILL_KIND_REJECTED",
            "ORDERING_CONSTRAINT": "BOUND_FILL_PROVEN_AT <= CAPTURE_STARTED_AT",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED_NO_PARTIAL_RECORD",
            "SIDE_EFFECT_BEFORE_CALL": "VENUE_FILL_ALREADY_OCCURRED",
            "SIDE_EFFECT_AFTER_CALL": "NONE_AT_HOST_JOIN",
        },
        {
            "from": HOST_JOIN_SYMBOL,
            "to": PRODUCTIVE_HOOK_CALLER,
            "CALL_CONDITION": "unique PRODUCTIVE_HOOK_CALLER node in host graph",
            "GATE": "PRODUCTION_GRAPH_WITHOUT_UNIQUE_CALLER",
            "ORDERING_CONSTRAINT": "HOST_JOIN_BEFORE_CALLER",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "NONE_DIRECT",
        },
        {
            "from": PRODUCTIVE_HOOK_CALLER,
            "to": PRODUCTIVE_LIFECYCLE_HOOK,
            "CALL_CONDITION": "lifecycle_event == REQUIRED_CAPTURE_TRIGGER",
            "GATE": "WRONG_LIFECYCLE_EVENT; LIVE_GATES_MUST_REMAIN_FALSE",
            "ORDERING_CONSTRAINT": "CALLER_BEFORE_HOOK",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "HOOK_MAY_PERSIST",
        },
        {
            "from": PRODUCTIVE_LIFECYCLE_HOOK,
            "to": ACCEPTANCE_SYMBOL,
            "CALL_CONDITION": "always before writer",
            "GATE": "acceptance contract",
            "ORDERING_CONSTRAINT": "ACCEPTANCE_BEFORE_WRITER",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED_NO_PARTIAL_RECORD",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "NONE",
        },
        {
            "from": PRODUCTIVE_LIFECYCLE_HOOK,
            "to": WRITER_SYMBOL,
            "CALL_CONDITION": "INPUT_CLASS == TEST_FIXTURE under current gates",
            "GATE": "RUNTIME_EXECUTION_UNAUTHORIZED for PRODUCTIVE_BOUND_FILL_INPUT",
            "ORDERING_CONSTRAINT": "HOOK_BEFORE_WRITER; WRITER_BEFORE_RESTART",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "FILESYSTEM_WRITE",
        },
        {
            "from": WRITER_SYMBOL,
            "to": PRODUCER_SYMBOL,
            "CALL_CONDITION": "writer-internal only",
            "GATE": "producer remain internal to writer",
            "ORDERING_CONSTRAINT": "PRODUCER_BEFORE_SERIALIZE",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "NONE",
        },
        {
            "from": WRITER_SYMBOL,
            "to": PERSIST_SYMBOL,
            "CALL_CONDITION": "after serialize; no existing conflicting identity",
            "GATE": "CAPTURE_TIMESTAMP_MISSING; NO_SECOND_IDENTITY",
            "ORDERING_CONSTRAINT": "SERIALIZE_BEFORE_PERSIST",
            "EXCEPTION_BEHAVIOR": "FAIL_CLOSED",
            "SIDE_EFFECT_BEFORE_CALL": "NONE",
            "SIDE_EFFECT_AFTER_CALL": "DURABLE_HANDOFF_FILE",
        },
        {
            "from": PRODUCTIVE_LIFECYCLE_HOOK,
            "to": RESTART_BOUNDARY_SYMBOL,
            "CALL_CONDITION": "MUST_NOT_CALL; ordering only",
            "GATE": "NO_BACKFILL_AFTER_RESTART; HOOK_BEFORE_RESTART",
            "ORDERING_CONSTRAINT": "CAPTURE_COMMITTED_AT < RESTART_BOUNDARY_AT",
            "EXCEPTION_BEHAVIOR": "CAPTURE_COMMIT_NOT_BEFORE_RESTART",
            "SIDE_EFFECT_BEFORE_CALL": "CAPTURE_PERSIST_IF_SUCCESS",
            "SIDE_EFFECT_AFTER_CALL": "RESTART_NOT_PART_OF_CAPTURE_SURFACE",
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_TRANSITIVE_CAPTURE_CALLGRAPH_V1",
        "TRANSITIVE_CALLGRAPH_COMPLETE": True,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "PRODUCTIVE_CAPTURE_CALLER": PRODUCTIVE_HOOK_CALLER,
        "CAPTURE_POINT": CAPTURE_POINT,
        "IRREVERSIBLE_EFFECT_BEFORE_CAPTURE_CALLER": "LIVE_IDENTITY_BOUND_VENUE_FILL",
        "nodes": list(nodes),
        "edges": list(edges),
        "hook_census": hook_census,
        "dataflow": dataflow,
    }


def prove_capture_point_timeline_v1() -> dict[str, Any]:
    steps = (
        {
            "ID": "T0",
            "RUNTIME_EVENT": "ORDER_PLAN_OPTIONAL_HISTORICAL",
            "EXTERNAL_EFFECT": "NONE_REQUIRED_FOR_CAPTURE_RECORD",
            "REVERSIBLE": True,
            "REQUIRED_FOR_CAPTURE": False,
            "AUTHORITY": "HISTORICAL_STATE",
        },
        {
            "ID": "T1",
            "RUNTIME_EVENT": "LIVE_SUBMIT_WIRE_SEND_ORDER_CREATE",
            "EXTERNAL_EFFECT": "EXCHANGE_SUBMIT",
            "REVERSIBLE": False,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "ADJUDICATED_CONCLUSIONS",
            "NOTE": (
                "Required to create the order that can produce a contemporaneous "
                "LIVE_IDENTITY_BOUND_VENUE_FILL. Not part of the capture call itself."
            ),
        },
        {
            "ID": "T2",
            "RUNTIME_EVENT": "SUBMIT_ACK",
            "EXTERNAL_EFFECT": "ORDER_STATE_MUTATION",
            "REVERSIBLE": False,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "ADJUDICATED_CONCLUSIONS",
            "NOTE": "ORDER_ACK is a forbidden capture trigger, but ack identity is required on the later bound fill.",
        },
        {
            "ID": "T3",
            "RUNTIME_EVENT": "LIVE_IDENTITY_BOUND_VENUE_FILL",
            "EXTERNAL_EFFECT": "VENUE_FILL; POSITION_EFFECT_AT_VENUE",
            "REVERSIBLE": False,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
            "NOTE": (
                "after_bound_fill means bound_fill_proven is True for kind "
                "LIVE_IDENTITY_BOUND_VENUE_FILL. Simulated/replay/ack/position-"
                "observation fills are forbidden. The fill is already externally "
                "executed before capture is allowed."
            ),
        },
        {
            "ID": "T4",
            "RUNTIME_EVENT": "PARAMETERIZE_BOUND_FILL_IDENTITY_AND_S05_QTY",
            "EXTERNAL_EFFECT": "NONE",
            "REVERSIBLE": True,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
        },
        {
            "ID": "T5",
            "RUNTIME_EVENT": HOST_JOIN_SYMBOL,
            "EXTERNAL_EFFECT": "NONE",
            "REVERSIBLE": True,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
        },
        {
            "ID": "T6",
            "RUNTIME_EVENT": PRODUCTIVE_HOOK_CALLER,
            "EXTERNAL_EFFECT": "NONE",
            "REVERSIBLE": True,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
        },
        {
            "ID": "T7",
            "RUNTIME_EVENT": PRODUCTIVE_LIFECYCLE_HOOK,
            "EXTERNAL_EFFECT": "NONE_UNTIL_WRITER",
            "REVERSIBLE": True,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
        },
        {
            "ID": "CAPTURE_POINT",
            "RUNTIME_EVENT": f"{WRITER_SYMBOL} commit captured_at_utc",
            "EXTERNAL_EFFECT": "FILESYSTEM_WRITE of handoff artifact only",
            "REVERSIBLE": False,
            "REQUIRED_FOR_CAPTURE": True,
            "AUTHORITY": "CANONICAL_AUTHORITY",
            "NOTE": (
                "Contemporaneous means CAPTURE_STARTED_AT >= BOUND_FILL_PROVEN_AT "
                "and CAPTURE_COMMITTED_AT < RESTART_BOUNDARY_AT. Capture is after "
                "fill confirmation and after Peak_Trade-owned S05 qty exists, "
                "before restart, and is not accounting/reconciliation persistence."
            ),
        },
        {
            "ID": "Tn",
            "RUNTIME_EVENT": RESTART_BOUNDARY_SYMBOL,
            "EXTERNAL_EFFECT": "PROCESS_STOP_START",
            "REVERSIBLE": False,
            "REQUIRED_FOR_CAPTURE": False,
            "AUTHORITY": "CANONICAL_AUTHORITY",
            "NOTE": "Must not have occurred yet. Capture does not invoke restart.",
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_POINT_TIMELINE_V1",
        "CAPTURE_POINT": CAPTURE_POINT,
        "AFTER_BOUND_FILL_MEANS": (
            "bound_fill_proven is True and bound_fill_kind == "
            "LIVE_IDENTITY_BOUND_VENUE_FILL for the same lifecycle; "
            "BOUND_FILL_PROVEN_AT <= CAPTURE_STARTED_AT"
        ),
        "UNDERLYING_FILL_ALREADY_EXTERNALLY_EXECUTED": True,
        "BOUND_FILL_ONLY_AFTER_SUCCESSFUL_EXCHANGE_FILL": True,
        "BOUND_FILL_CAN_BE_CREATED_OFFLINE_SYNTHETICALLY": (
            "STRUCTURALLY_YES_AS_TEST_FIXTURE_NOT_VALID_PRODUCTIVE_PROVENANCE"
        ),
        "CAPTURE_RELATIVE_TO_ORDER_SUBMIT": "AFTER",
        "CAPTURE_RELATIVE_TO_FILL_CONFIRMATION": "AFTER",
        "CAPTURE_RELATIVE_TO_POSITION_MUTATION": (
            "AFTER_VENUE_FILL_POSITION_EFFECT; S05_QTY_IS_PEAK_TRADE_OWNED_NOT_VENUE_GET"
        ),
        "CAPTURE_RELATIVE_TO_ACCOUNTING_RECONCILIATION": "INDEPENDENT_NOT_AFTER_REQUIRED",
        "CAPTURE_RELATIVE_TO_OTHER_PRODUCTIVE_PERSISTENCE": (
            "CAPTURE_WRITES_ONLY_HANDOFF_ARTIFACT"
        ),
        "PRODUCTIVE_CONTEMPORANEOUS_CAPTURE_REQUIRES_PRIOR_LIVE_OR_VENUE_ACTION": True,
        "steps": list(steps),
    }


def census_side_effects_v1(*, repo_root: object | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    network_hits: list[str] = []
    forbidden_hits: list[str] = []
    scoped_functions = {
        HOST_JOIN_RELPATH: HOST_JOIN_SYMBOL,
        CALLER_RELPATH: PRODUCTIVE_HOOK_CALLER,
        HOOK_RELPATH: PRODUCTIVE_LIFECYCLE_HOOK,
        WRITER_RELPATH: WRITER_SYMBOL,
        PRODUCER_RELPATH: PRODUCER_SYMBOL,
    }
    for relpath, symbol in scoped_functions.items():
        tree = _parse_module(repo_root=root, relpath=relpath)
        if relpath == HOST_JOIN_RELPATH:
            forbidden_hits.extend(
                f"{relpath}:{name}"
                for name in _function_forbidden_effects(tree=tree, function_name=symbol)
            )
        else:
            forbidden_hits.extend(
                f"{relpath}:{name}" for name in _module_calls_forbidden_effects(tree=tree)
            )
            network_hits.extend(f"{relpath}:{name}" for name in _module_imports_network(tree=tree))
    if network_hits:
        raise Section1114OfflineSurfaceError("CAPTURE_SURFACE_MUST_NOT_IMPORT_NETWORK")
    restart_hits = [row for row in forbidden_hits if row.endswith(":restart")]
    if restart_hits:
        raise Section1114OfflineSurfaceError("CAPTURE_SURFACE_MUST_NOT_CALL_RESTART")
    rows = (
        {
            "EFFECT": "FILESYSTEM_WRITE",
            "SYMBOL": PERSIST_SYMBOL,
            "PATH": WRITER_RELPATH,
            "BEFORE_OR_AFTER_CAPTURE": "AT_CAPTURE_POINT",
            "REQUIRED": True,
            "AVOIDABLE": False,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "DATABASE_WRITE",
            "SYMBOL": "NONE",
            "PATH": "NONE",
            "BEFORE_OR_AFTER_CAPTURE": "NONE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": False,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "NETWORK_WRITE",
            "SYMBOL": "NONE_ON_CAPTURE_SURFACE",
            "PATH": "NONE",
            "BEFORE_OR_AFTER_CAPTURE": "NONE_ON_CAPTURE_SURFACE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": False,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "EXCHANGE_SUBMIT",
            "SYMBOL": CANARY_SUBMIT_TRANSPORT_SYMBOL,
            "PATH": CANARY_SUBMIT_TRANSPORT_RELPATH,
            "BEFORE_OR_AFTER_CAPTURE": "BEFORE_REQUIRED_PREDECESSOR_NOT_ON_CAPTURE_SURFACE",
            "REQUIRED": True,
            "AVOIDABLE": False,
            "MOCKABLE": False,
            "ISOLATABLE": False,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
            "NOTE": "Unavoidable predecessor for a valid productive bound fill; not invoked by capture.",
        },
        {
            "EFFECT": "POSITION_MUTATION",
            "SYMBOL": "VENUE_FILL",
            "PATH": "EXCHANGE",
            "BEFORE_OR_AFTER_CAPTURE": "BEFORE",
            "REQUIRED": True,
            "AVOIDABLE": False,
            "MOCKABLE": False,
            "ISOLATABLE": False,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "ORDER_STATE_MUTATION",
            "SYMBOL": "VENUE_ACK_AND_FILL",
            "PATH": "EXCHANGE",
            "BEFORE_OR_AFTER_CAPTURE": "BEFORE",
            "REQUIRED": True,
            "AVOIDABLE": False,
            "MOCKABLE": False,
            "ISOLATABLE": False,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "PROCESS_EXIT",
            "SYMBOL": RESTART_BOUNDARY_SYMBOL,
            "PATH": RESTART_BOUNDARY_PATH,
            "BEFORE_OR_AFTER_CAPTURE": "AFTER_FORBIDDEN_DURING_CAPTURE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "RESTART",
            "SYMBOL": RESTART_BOUNDARY_SYMBOL,
            "PATH": RESTART_BOUNDARY_PATH,
            "BEFORE_OR_AFTER_CAPTURE": "AFTER_FORBIDDEN_DURING_CAPTURE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "HOST_CONTROL",
            "SYMBOL": "NONE",
            "PATH": "NONE",
            "BEFORE_OR_AFTER_CAPTURE": "NONE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": False,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "SECRET_ACCESS",
            "SYMBOL": "NONE_ON_CAPTURE_SURFACE",
            "PATH": "NONE",
            "BEFORE_OR_AFTER_CAPTURE": "NONE_ON_CAPTURE_SURFACE",
            "REQUIRED": False,
            "AVOIDABLE": True,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": False,
            "AUTHORIZED_NOW": False,
        },
        {
            "EFFECT": "CLOCK_DEPENDENCY",
            "SYMBOL": "captured_at_utc parameterized now_utc",
            "PATH": WRITER_RELPATH,
            "BEFORE_OR_AFTER_CAPTURE": "AT_CAPTURE_POINT",
            "REQUIRED": True,
            "AVOIDABLE": False,
            "MOCKABLE": True,
            "ISOLATABLE": True,
            "PRODUCTIVE": True,
            "AUTHORIZED_NOW": False,
            "NOTE": "Wall-clock substitution is forbidden; now_utc must be supplied.",
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_SIDE_EFFECT_CENSUS_V1",
        "SIDE_EFFECT_CENSUS_COMPLETE": True,
        "CAPTURE_SURFACE_NETWORK_IMPORTS": network_hits,
        "CAPTURE_SURFACE_FORBIDDEN_CALLS": forbidden_hits,
        "UNAVOIDABLE_EXTERNAL_EFFECTS": UNAVOIDABLE_EXTERNAL_EFFECTS,
        "EARLIEST_IRREVERSIBLE_EFFECT": EARLIEST_IRREVERSIBLE_EFFECT,
        "CAPTURE_SURFACE_FIRST_IRREVERSIBLE_EFFECT": "FILESYSTEM_WRITE_OF_HANDOFF_ARTIFACT",
        "rows": list(rows),
    }


def census_gates_v1() -> dict[str, Any]:
    rows = (
        {
            "GATE_NAME": "LIVE_ENABLED",
            "OWNER": "constants_v1.LIVE_ENABLED",
            "DEFAULT": False,
            "CURRENT_VALUE": LIVE_ENABLED,
            "EVALUATION_SITE": CALLER_RELPATH,
            "SCOPE": "SECTION_11_14_AND_CAPTURE_CALLER",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE_DURING_THIS_GO",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "LIVE_ARMED",
            "OWNER": "constants_v1.LIVE_ARMED",
            "DEFAULT": False,
            "CURRENT_VALUE": LIVE_ARMED,
            "EVALUATION_SITE": CALLER_RELPATH,
            "SCOPE": "SECTION_11_14_AND_CAPTURE_CALLER",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE_DURING_THIS_GO",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "CANARY_AUTHORIZED",
            "OWNER": "constants_v1.CANARY_AUTHORIZED",
            "DEFAULT": False,
            "CURRENT_VALUE": CANARY_AUTHORIZED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "NOT_A_CAPTURE_ENABLE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            "OWNER": "constants_v1.SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED",
            "DEFAULT": False,
            "CURRENT_VALUE": SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
            "EVALUATION_SITE": "host graph compose + caller",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "PRODUCTIVE_INPUT_CLASS_BLOCKED_WHILE_FALSE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "POST_ALLOWED",
            "OWNER": "constants_v1.POST_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": POST_ALLOWED,
            "EVALUATION_SITE": "host graph compose",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "ORDER_SUBMIT_ALLOWED",
            "OWNER": "constants_v1.ORDER_SUBMIT_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": ORDER_SUBMIT_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "PREDECESSOR_NOT_CAPTURE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "TESTNET_AUTHORIZED",
            "OWNER": "constants_v1.TESTNET_AUTHORIZED",
            "DEFAULT": False,
            "CURRENT_VALUE": TESTNET_AUTHORIZED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": False,
        },
        {
            "GATE_NAME": "HOOK_INPUT_CLASS_TEST_FIXTURE_ONLY",
            "OWNER": "run_capture_hook_after_bound_fill_before_restart_v1",
            "DEFAULT": "TEST_FIXTURE required",
            "CURRENT_VALUE": "PRODUCTIVE_BOUND_FILL_INPUT raises RUNTIME_EXECUTION_UNAUTHORIZED",
            "EVALUATION_SITE": HOOK_RELPATH,
            "SCOPE": "CAPTURE_HOOK",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "BLOCKS_PRODUCTIVE_CAPTURE_NOW",
            "LIVE_DEPENDENCY": False,
        },
        {
            "GATE_NAME": "bound_fill_proven",
            "OWNER": PRODUCTIVE_HOOK_CALLER,
            "DEFAULT": "must be True",
            "CURRENT_VALUE": "fail-closed unless True",
            "EVALUATION_SITE": CALLER_RELPATH,
            "SCOPE": "CAPTURE_CALLER",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "REQUIRED",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "CREDENTIAL_USE_ALLOWED",
            "OWNER": "constants_v1.CREDENTIAL_USE_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": CREDENTIAL_USE_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "NOT_REQUIRED_FOR_CAPTURE_CALL",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "PRIVATE_GET_ALLOWED",
            "OWNER": "constants_v1.PRIVATE_GET_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": PRIVATE_GET_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "NOT_REQUIRED_FOR_CAPTURE_CALL",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "CANCEL_ALLOWED",
            "OWNER": "constants_v1.CANCEL_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": CANCEL_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "AMEND_ALLOWED",
            "OWNER": "constants_v1.AMEND_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": AMEND_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "FLATTEN_EXECUTE_ALLOWED",
            "OWNER": "constants_v1.FLATTEN_EXECUTE_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": FLATTEN_EXECUTE_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": True,
        },
        {
            "GATE_NAME": "FUNDING_ALLOWED",
            "OWNER": "constants_v1.FUNDING_ALLOWED",
            "DEFAULT": False,
            "CURRENT_VALUE": FUNDING_ALLOWED,
            "EVALUATION_SITE": "section_11_14 constants",
            "SCOPE": "SECTION_11_14",
            "FAIL_CLOSED": True,
            "BYPASS_PATH": "NONE",
            "CAPTURE_DEPENDENCY": "MUST_REMAIN_FALSE",
            "LIVE_DEPENDENCY": True,
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_GATE_CENSUS_V1",
        "GATE_CENSUS_COMPLETE": True,
        "GATE_MUTATION_PERFORMED": False,
        "rows": list(rows),
    }


def census_input_preconditions_v1() -> dict[str, Any]:
    rows = (
        {
            "INPUT": "authoritative bound fill",
            "SOURCE": CANONICAL_BOUND_FILL_KIND,
            "WHEN_CREATED": "AT_VENUE_FILL_THEN_PARAMETERIZED",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
            "NOTE": "TEST_FIXTURE is structurally constructible and not productive provenance.",
        },
        {
            "INPUT": "clOrdId",
            "SOURCE": "bound_fill_identity.clOrdId",
            "WHEN_CREATED": "AT_SUBMIT",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "ordId",
            "SOURCE": "bound_fill_identity.ordId",
            "WHEN_CREATED": "AT_SUBMIT_ACK",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "instId",
            "SOURCE": "bound_fill_identity.instId",
            "WHEN_CREATED": "AT_ORDER_PLAN_OR_SUBMIT",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "posSide",
            "SOURCE": "bound_fill_identity.posSide",
            "WHEN_CREATED": "AT_SUBMIT",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "pos / fillSz",
            "SOURCE": "Peak_Trade-owned S05 qty Decimal-equal to fillSz",
            "WHEN_CREATED": "AT_BOUND_FILL",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "timestamps",
            "SOURCE": "bound_fill_proven_at, capture_started_at, captured_at_utc",
            "WHEN_CREATED": "CONTEMPORANEOUS_WITH_WINDOW",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": False,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "lifecycle_id / attempt_identity",
            "SOURCE": "runtime owner of the bound-fill lifecycle",
            "WHEN_CREATED": "AT_LIFECYCLE_START",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": False,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": True,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "capture destination",
            "SOURCE": "storage_root / durable pre-restart path",
            "WHEN_CREATED": "AT_WRITER",
            "OFFLINE_CREATABLE": True,
            "PRODUCTIVE_ONLY": False,
            "EXTERNAL_DATA_REQUIRED": False,
            "REQUIRED_FOR_CAPTURE": True,
            "REQUIRED_FOR_VALID_PROVENANCE": False,
            "STRUCTURALLY_CONSTRUCTIBLE": True,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
        },
        {
            "INPUT": "historical BOUND_* identity",
            "SOURCE": "fill_observed_identity_v1 / restart_reconstructed_identity_v1",
            "WHEN_CREATED": "HISTORICAL_LIVE_POST_AND_FILL",
            "OFFLINE_CREATABLE": False,
            "PRODUCTIVE_ONLY": True,
            "EXTERNAL_DATA_REQUIRED": True,
            "REQUIRED_FOR_CAPTURE": False,
            "REQUIRED_FOR_VALID_PROVENANCE": False,
            "STRUCTURALLY_CONSTRUCTIBLE": False,
            "VALID_CONTEMPORANEOUS_PRODUCTIVE_PROVENANCE": False,
            "NOTE": "Historical identity is not the current producer and is not contemporaneous.",
        },
    )
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_INPUT_PRECONDITION_CENSUS_V1",
        "INPUT_PRECONDITION_CENSUS_COMPLETE": True,
        "FORBIDDEN_BOUND_FILL_KINDS": sorted(FORBIDDEN_BOUND_FILL_KINDS),
        "CANONICAL_BOUND_FILL_KIND": CANONICAL_BOUND_FILL_KIND,
        "REQUIRED_HANDOFF_FIELDS": list(REQUIRED_HANDOFF_FIELDS),
        "TEST_FIXTURE_IS_NOT_PRODUCTIVE_PROVENANCE": True,
        "rows": list(rows),
    }


def prove_non_execution_v1(
    *,
    repo_root: object | None = None,
    storage_root: Path | None = None,
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    if LIVE_ENABLED is True or LIVE_ARMED is True or CANARY_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("LIVE_GATES_MUST_REMAIN_FALSE")
    if SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if POST_ALLOWED is True or ORDER_SUBMIT_ALLOWED is True:
        raise Section1114OfflineSurfaceError("POST_MUST_REMAIN_FORBIDDEN")
    if TESTNET_AUTHORIZED is True:
        raise Section1114OfflineSurfaceError("TESTNET_MUST_REMAIN_UNAUTHORIZED")
    if LIVE_RESTART_RECONSTRUCTED is True:
        raise Section1114OfflineSurfaceError("LIVE_RESTART_RECONSTRUCTED_MUST_REMAIN_FALSE")
    if CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED is True:
        raise Section1114OfflineSurfaceError("OBSERVATION_MUST_REMAIN_FALSE")
    identity = {
        "clOrdId": "ptprodidentityclordid000000001",
        "ordId": "9990008887776665554",
        "instId": "ETH-USD_UM_XPERP-NONEXEC",
        "posSide": "net",
        "fillSz": "1",
    }
    lifecycle_id = "non-execution-proof-lifecycle"
    provenance = build_contemporaneous_field_provenance_from_bound_fill_v1(
        bound_fill_identity=identity,
        peak_trade_owned_resulting_current_position_qty="1",
        lifecycle_id=lifecycle_id,
        input_class=INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
    )
    productive_kwargs: dict[str, Any] = {
        "storage_root": storage_root or (root / "durable_state"),
        "bound_fill_proven": True,
        "bound_fill_kind": CANONICAL_BOUND_FILL_KIND,
        "bound_fill_identity": identity,
        "peak_trade_owned_resulting_current_position_qty": "1",
        "source_kind": ADMISSIBLE_POS_SOURCE_KIND,
        "unit": POS_UNIT,
        "restart_already_occurred": False,
        "restart_not_yet_occurred_proven": True,
        "bound_fill_proven_at": "2026-09-07T16:00:00Z",
        "capture_started_at": "2026-09-07T16:00:01Z",
        "attempt_identity": "non-execution-proof-attempt",
        "input_class": INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        "lifecycle_id": lifecycle_id,
        "field_provenance": provenance,
    }
    productive_rejected = False
    productive_error = ""
    try:
        run_capture_hook_after_bound_fill_before_restart_v1(**productive_kwargs)
    except Section1114OfflineSurfaceError as exc:
        productive_rejected = True
        productive_error = str(exc)
    if productive_rejected is not True:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_INPUT_MUST_REMAIN_UNAUTHORIZED")
    if "RUNTIME_EXECUTION_UNAUTHORIZED" not in productive_error:
        raise Section1114OfflineSurfaceError("PRODUCTIVE_INPUT_MUST_REMAIN_UNAUTHORIZED")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_NON_EXECUTION_PROOF_V1",
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "HOST_CRASH_EXECUTED": False,
        "TESTNET_EXECUTED": False,
        "CANARY_EXECUTED": False,
        "PRODUCTIVE_INPUT_CLASS_REJECTED": True,
        "PRODUCTIVE_INPUT_CLASS_ERROR": productive_error,
        "TEST_FIXTURE_CLASS": INPUT_CLASS_TEST_FIXTURE,
        "PRODUCTIVE_INPUT_CLASS": INPUT_CLASS_PRODUCTIVE_BOUND_FILL_INPUT,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
    }


def adjudicate_isolation_v1() -> dict[str, Any]:
    if CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION is True:
        raise Section1114OfflineSurfaceError("ISOLATION_CLAIM_FORBIDDEN")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_CAPTURE_ISOLATION_ADJUDICATION_V1",
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
        "UNAVOIDABLE_PRODUCTIVE_PREDECESSOR": UNAVOIDABLE_PRODUCTIVE_PREDECESSOR,
        "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT": MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
        "REASON": (
            "A legitimate contemporaneous productive capture record requires "
            "LIVE_IDENTITY_BOUND_VENUE_FILL already proven for the same lifecycle. "
            "That bound fill is an identity-bound venue fill of a submitted order. "
            "TEST_FIXTURE capture is not productive provenance. Historical BOUND_* "
            "identity is not contemporaneous. Isolation from live submit/wire/"
            "order/position mutation is therefore false."
        ),
    }


def bind_authorization_boundary_v1() -> dict[str, Any]:
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_MINIMAL_FUTURE_AUTHORIZATION_BOUNDARY_V1",
        "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT": MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
        "MINIMAL_REQUIRED_GATES": (
            "FUTURE_OWNER_GO_FOR_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION; "
            "PRODUCTIVE_BOUND_FILL_INPUT authorization distinct from TEST_FIXTURE; "
            "LIVE_ENABLED/LIVE_ARMED remain independently gated and are not "
            "capture-enable tokens"
        ),
        "MINIMAL_REQUIRED_INPUTS": (
            "contemporaneous LIVE_IDENTITY_BOUND_VENUE_FILL + S05 qty + "
            "lifecycle timestamps + storage_root"
        ),
        "MINIMAL_REQUIRED_SIDE_EFFECTS": "FILESYSTEM_WRITE of the handoff artifact",
        "UNAVOIDABLE_EXTERNAL_EFFECTS": UNAVOIDABLE_EXTERNAL_EFFECTS,
        "PROHIBITED_TRANSITIVE_EFFECTS": (
            "LIVE_SUBMIT as part of capture; WIRE_SEND as part of capture; "
            "ORDER_MUTATION; FUNDING; TESTNET; CANARY_ENABLE; RESTART; "
            "PROCESS_EXIT; HOST_REBOOT; HOST_CRASH; LIVE_GATE_ENABLE; "
            "LIVE_GATE_ARM; AUTHENTICATION_MUTATION; persistence outside the "
            "handoff artifact"
        ),
        "STOP_CONDITION": (
            "Any attempt to treat TEST_FIXTURE or historical BOUND_* as "
            "productive contemporaneous provenance; any capture after restart; "
            "any missing required field"
        ),
        "SUCCESS_EVIDENCE": (
            "DURABLE_SUCCESS_ACK for PRODUCTIVE_BOUND_FILL_INPUT with "
            "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED remaining a separate "
            "empirical claim under a future observation GO"
        ),
        "ROLLBACK_SEMANTICS": (
            "Capture persist is identity-idempotent; a different identity is "
            "NO_SECOND_IDENTITY fail-closed. Restart is not a rollback."
        ),
        "FUTURE_OBSERVATION_GO_MUST_AUTHORIZE_PREDECESSOR": (
            "Identity-bound venue fill of a submitted order, then HOST_JOIN"
        ),
    }


def bind_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_v1(
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
    entrypoints = census_productive_entrypoint_candidates_v1(repo_root=root)
    callgraph = census_transitive_capture_callgraph_v1(repo_root=root)
    timeline = prove_capture_point_timeline_v1()
    effects = census_side_effects_v1(repo_root=root)
    gates = census_gates_v1()
    inputs = census_input_preconditions_v1()
    isolation = adjudicate_isolation_v1()
    boundary = bind_authorization_boundary_v1()
    non_execution = prove_non_execution_v1(repo_root=root, storage_root=storage_root)
    host_graph = compose_live_order_pre_restart_capture_host_graph_v1()
    if host_graph["CURRENT_RUNTIME_EXECUTION_AUTHORIZED"] is True:
        raise Section1114OfflineSurfaceError("RUNTIME_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    return {
        "DOCUMENT_CLASS": (
            "SECTION_11_14_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_"
            "NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1"
        ),
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "COMPLETE_CAPTURE_SEAM": "PROVEN",
        "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": True,
        "NO_BACKFILL_CONTRACT_PROVEN": True,
        "PRODUCTIVE_RUNTIME_ENTRYPOINT": PRODUCTIVE_RUNTIME_ENTRYPOINT,
        "PRODUCTIVE_CAPTURE_CALLER": PRODUCTIVE_HOOK_CALLER,
        "CAPTURE_POINT": CAPTURE_POINT,
        "TRANSITIVE_CALLGRAPH_COMPLETE": True,
        "SIDE_EFFECT_CENSUS_COMPLETE": True,
        "GATE_CENSUS_COMPLETE": True,
        "INPUT_PRECONDITION_CENSUS_COMPLETE": True,
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE": CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE,
        "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY": (
            CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY
        ),
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": False,
        "CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE": True,
        "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT": MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT,
        "UNAVOIDABLE_EXTERNAL_EFFECTS": UNAVOIDABLE_EXTERNAL_EFFECTS,
        "EARLIEST_IRREVERSIBLE_EFFECT": EARLIEST_IRREVERSIBLE_EFFECT,
        "UNAVOIDABLE_PRODUCTIVE_PREDECESSOR": UNAVOIDABLE_PRODUCTIVE_PREDECESSOR,
        "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": False,
        "CURRENT_RUNTIME_EXECUTION_AUTHORIZED": False,
        "AUTHORIZED_RUNTIME_SURFACE": "NONE",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": False,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "entrypoints": entrypoints,
        "callgraph": callgraph,
        "timeline": timeline,
        "side_effects": effects,
        "gates": gates,
        "inputs": inputs,
        "isolation": isolation,
        "authorization_boundary": boundary,
        "non_execution": non_execution,
        "host_graph": host_graph,
    }
