"""Static surface proving WP-B cannot emit WS trading mutations."""

from __future__ import annotations

import inspect
from typing import Any

from src.ops.okx_eea_private_account_state_runtime_v1 import constants_v1
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    FORBIDDEN_WS_MUTATION_OPS,
    PRIVATE_WS_AMEND_AUTHORIZED,
    PRIVATE_WS_CANCEL_AUTHORIZED,
    PRIVATE_WS_ORDER_SEND_AUTHORIZED,
)
from src.ops.okx_eea_private_account_state_runtime_v1 import ws_transport_v1


def list_public_wp_b_api_symbols_v1() -> tuple[str, ...]:
    modules = (constants_v1, ws_transport_v1)
    names: list[str] = []
    for mod in modules:
        for name, obj in inspect.getmembers(mod):
            if name.startswith("_"):
                continue
            if inspect.isfunction(obj) or inspect.isclass(obj):
                names.append(f"{mod.__name__}.{name}")
    return tuple(sorted(names))


def assert_no_ws_mutation_operations_in_public_api_v1() -> dict[str, Any]:
    if (
        PRIVATE_WS_ORDER_SEND_AUTHORIZED
        or PRIVATE_WS_AMEND_AUTHORIZED
        or PRIVATE_WS_CANCEL_AUTHORIZED
    ):
        raise RuntimeError("WS_MUTATION_FLAGS_MUST_BE_FALSE")
    for name in dir(ws_transport_v1):
        if name.startswith("_"):
            continue
        lowered = name.lower()
        for op in FORBIDDEN_WS_MUTATION_OPS:
            token = op.replace("-", "_")
            if token in lowered:
                raise RuntimeError(f"WS_MUTATION_SYMBOL_IN_TRANSPORT:{name}")
    return {
        "PRIVATE_WS_ORDER_SEND_AUTHORIZED": PRIVATE_WS_ORDER_SEND_AUTHORIZED,
        "PRIVATE_WS_AMEND_AUTHORIZED": PRIVATE_WS_AMEND_AUTHORIZED,
        "PRIVATE_WS_CANCEL_AUTHORIZED": PRIVATE_WS_CANCEL_AUTHORIZED,
        "forbidden_ops_absent_from_public_api": True,
    }
