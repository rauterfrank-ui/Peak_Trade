"""Isolated constants for offline GET-evidence admission.

AUTHORITY_EFFECT=NONE. This module does not call OKX, open a socket, or import
the pretrade runtime module. That module's import graph reaches the productive
cycle. The public identity extractor is reused by compiling only its function.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    BASELINE_REST_GET_ALLOWLIST,
)

PACKAGE_ID = "h1_get_evidence_admission_v1"
AUTHORITY_EFFECT = "NONE"
POST_ALLOWED = False
EXTERNAL_EFFECT_AUTHORIZED = False
WRITER_HANDOFF = "NONE"
PRODUCTIVE_COMPLETENESS = False
FLAT_EMITTED = False
PRODUCTIVE_CYCLE_BINDING = "NONE"
PRODUCTIVE_ACTIVATION = False

STATUS_ADMITTED = "ADMITTED"
STATUS_UNKNOWN_BLOCKED = "UNKNOWN_BLOCKED"
INVENTORY_ATTESTED_ZERO = "ATTESTED_ZERO_INVENTORY"
INVENTORY_ATTESTED_ROWS = "ATTESTED_ROWS"
INVENTORY_UNPROVEN = "UNPROVEN"

POSITIVE_REASON_CODES = (
    "ACCOUNT_IDENTITY",
    "DIGEST_INTEGRITY",
    "FRESHNESS",
    "INSTRUMENT_IDENTITY",
    "PAGINATION_COMPLETENESS",
    "TEMPORAL_CONSISTENCY",
)

REASON_INPUT_ABSENT = "INPUT_ABSENT"
REASON_INPUT_MALFORMED = "INPUT_MALFORMED"
REASON_RESPONSE_MALFORMED = "RESPONSE_MALFORMED"
REASON_MISSING_RESPONSE = "MISSING_RESPONSE"
REASON_DUPLICATE_RESPONSE = "DUPLICATE_RESPONSE"
REASON_ACCOUNT_PARAMETER_ABSENT = "ACCOUNT_PARAMETER_ABSENT"
REASON_ACCOUNT_IDENTITY_ABSENT = "ACCOUNT_IDENTITY_ABSENT"
REASON_ACCOUNT_IDENTITY_MALFORMED = "ACCOUNT_IDENTITY_MALFORMED"
REASON_ACCOUNT_IDENTITY_MISMATCH = "ACCOUNT_IDENTITY_MISMATCH"
REASON_INSTRUMENT_PARAMETER_ABSENT = "INSTRUMENT_PARAMETER_ABSENT"
REASON_INSTRUMENT_ABSENT = "INSTRUMENT_ABSENT"
REASON_INSTRUMENT_MALFORMED = "INSTRUMENT_MALFORMED"
REASON_INSTRUMENT_MISMATCH = "INSTRUMENT_MISMATCH"
REASON_FRESHNESS_WINDOW_ABSENT = "FRESHNESS_WINDOW_ABSENT"
REASON_ADMISSION_TIME_ABSENT = "ADMISSION_TIME_ABSENT"
REASON_VENUE_TIMESTAMP_ABSENT = "VENUE_TIMESTAMP_ABSENT"
REASON_CAPTURED_AT_ABSENT = "CAPTURED_AT_ABSENT"
REASON_STALE_EVIDENCE = "STALE_EVIDENCE"
REASON_PAGINATION_TERMINAL_ABSENT = "PAGINATION_TERMINAL_ABSENT"
REASON_PAGINATION_TERMINAL_SOURCE_ABSENT = "PAGINATION_TERMINAL_SOURCE_ABSENT"
REASON_ADMISSION_WINDOW_ABSENT = "ADMISSION_WINDOW_ABSENT"
REASON_TEMPORAL_INCONSISTENCY = "TEMPORAL_INCONSISTENCY"
REASON_DIGEST_ABSENT = "DIGEST_ABSENT"
REASON_DIGEST_MISMATCH = "DIGEST_MISMATCH"
REASON_EMPTY_POSITIONS_WITHOUT_COMPLETENESS = "EMPTY_POSITIONS_WITHOUT_COMPLETENESS"
REASON_DUPLICATE_FILL_CONFLICT = "DUPLICATE_FILL_CONFLICT"
REASON_LATE_FILL_OUTSIDE_WINDOW = "LATE_FILL_OUTSIDE_WINDOW"
REASON_FILL_TRADE_ID_ABSENT = "FILL_TRADE_ID_ABSENT"
REASON_FILL_TIMESTAMP_MALFORMED = "FILL_TIMESTAMP_MALFORMED"

_PUBLIC_EXTRACTOR_NAME = "extract_identity_fields_from_payload_v1"
_PUBLIC_MODULE = (
    Path(__file__).resolve().parents[1]
    / "full_core_live_path_composition_root_v1"
    / "fresh_pretrade_runtime_get_v1.py"
)
_ACCOUNT_CONSTANT_NAMES = (
    "ENDPOINT_ACCOUNT_CONFIG",
    "ENDPOINT_ACCOUNT_BALANCE",
    "ENDPOINT_ACCOUNT_POSITIONS",
)
_ALLOWED_CALL_NAMES = frozenset({"isinstance", "str", "tuple"})
_ALLOWED_ATTR_CALLS = frozenset({"get", "append", "strip"})

ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
ENDPOINT_ORDERS_HISTORY = "/api/v5/trade/orders-history"
ENDPOINT_FILLS = "/api/v5/trade/fills"


def _public_tree() -> ast.Module:
    return ast.parse(_PUBLIC_MODULE.read_text(encoding="utf-8"), filename=str(_PUBLIC_MODULE))


def _assigned_string_constants(tree: ast.Module, names: tuple[str, ...]) -> dict[str, str]:
    found: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in names:
            continue
        if target.id in found:
            raise RuntimeError(f"duplicate public constant {target.id}")
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            raise RuntimeError(f"public constant {target.id} is not a string")
        found[target.id] = node.value.value
    missing = [name for name in names if name not in found]
    if missing:
        raise RuntimeError("public endpoint constants missing: " + ",".join(missing))
    return found


def _isolated_extractor(tree: ast.Module) -> Callable[..., Any]:
    found: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == _PUBLIC_EXTRACTOR_NAME:
            if found is not None:
                raise RuntimeError("duplicate public identity extractor")
            found = node
    if found is None:
        raise RuntimeError("public identity extractor missing")
    for sub in ast.walk(found):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Name):
            if func.id not in _ALLOWED_CALL_NAMES:
                raise RuntimeError(f"public extractor calls {func.id}")
        elif isinstance(func, ast.Attribute):
            if func.attr not in _ALLOWED_ATTR_CALLS:
                raise RuntimeError(f"public extractor calls attribute {func.attr}")
        else:
            raise RuntimeError("public extractor has an unsupported call")
    function = found
    function.returns = None
    function.decorator_list = []
    for arg in (
        *function.args.args,
        *function.args.posonlyargs,
        *function.args.kwonlyargs,
    ):
        arg.annotation = None
    if function.args.vararg is not None:
        function.args.vararg.annotation = None
    if function.args.kwarg is not None:
        function.args.kwarg.annotation = None
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {"Mapping": Mapping}
    exec(compile(module, str(_PUBLIC_MODULE), "exec"), namespace)  # noqa: S102
    loaded = namespace[_PUBLIC_EXTRACTOR_NAME]
    if not callable(loaded):
        raise RuntimeError("public identity extractor did not load")
    return loaded


def _load_public_contract() -> tuple[str, str, str, Callable[..., Any]]:
    if not _PUBLIC_MODULE.is_file():
        raise RuntimeError("public pretrade module is not readable")
    tree = _public_tree()
    constants = _assigned_string_constants(tree, _ACCOUNT_CONSTANT_NAMES)
    extractor = _isolated_extractor(tree)
    config = constants["ENDPOINT_ACCOUNT_CONFIG"]
    balance = constants["ENDPOINT_ACCOUNT_BALANCE"]
    positions = constants["ENDPOINT_ACCOUNT_POSITIONS"]
    required = (
        config,
        balance,
        positions,
        ENDPOINT_ORDERS_PENDING,
        ENDPOINT_ORDERS_HISTORY,
        ENDPOINT_FILLS,
    )
    missing = [path for path in required if path not in BASELINE_REST_GET_ALLOWLIST]
    if missing:
        raise RuntimeError("public endpoint left the GET allowlist: " + ",".join(missing))
    return config, balance, positions, extractor


(
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_POSITIONS,
    extract_identity_fields_from_payload_v1,
) = _load_public_contract()

REQUIRED_ENDPOINTS = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_FILLS,
)
ACCOUNT_ENDPOINTS = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
)
PAGINATED_ENDPOINTS = (
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_FILLS,
)
INSTRUMENT_SCOPED_ENDPOINTS = PAGINATED_ENDPOINTS
