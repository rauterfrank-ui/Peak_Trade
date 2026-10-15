"""Dual-layer read-only endpoint contract: PL-TF-002 session vs Full-Core transport."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    PRIVATE_GET_PATHS,
    PUBLIC_GET_PATHS,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FORBIDDEN_ENDPOINTS,
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import (
    FORBIDDEN_MUTATION_ENDPOINTS,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    _assert_get_only_surface_v1,
)


def test_pl_tf_002_session_allowlist_matches_fresh_pretrade_paths_only() -> None:
    allowed = PUBLIC_GET_PATHS | PRIVATE_GET_PATHS
    for path in sorted(allowed):
        _assert_get_only_surface_v1(endpoint_path=path, method="GET")
    assert READ_ONLY_EXACT_ORDER_LOOKUP_PATH not in allowed


@pytest.mark.parametrize(
    "endpoint_path",
    [
        "/api/v5/trade/order",
        "/api/v5/trade/cancel-order",
        "/api/v5/asset/withdrawal",
        "/api/v5/asset/transfer",
    ],
)
def test_pl_tf_002_session_rejects_mutation_marked_endpoints(endpoint_path: str) -> None:
    assert endpoint_path in FORBIDDEN_MUTATION_ENDPOINTS
    with pytest.raises(
        PlTf002ProductiveReadOnlySessionError,
        match="TREASURY_OR_MUTATION_ENDPOINT_FORBIDDEN",
    ):
        _assert_get_only_surface_v1(endpoint_path=endpoint_path, method="GET")


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_pl_tf_002_session_rejects_non_get_methods(method: str) -> None:
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="HTTP_METHOD_FORBIDDEN"):
        _assert_get_only_surface_v1(endpoint_path=ENDPOINT_ACCOUNT_CONFIG, method=method)


def test_transport_exact_order_lookup_not_in_forbidden_endpoints() -> None:
    assert READ_ONLY_EXACT_ORDER_LOOKUP_PATH == "/api/v5/trade/order"
    assert READ_ONLY_EXACT_ORDER_LOOKUP_PATH not in FORBIDDEN_ENDPOINTS


def test_transport_still_blocks_treasury_and_cancel_paths() -> None:
    transport = FullCoreProductiveReadOnlyGetTransportV1(handle=None)
    for endpoint in FORBIDDEN_ENDPOINTS:
        with pytest.raises(FullCoreProductiveReadOnlyGetError, match="FORBIDDEN_ENDPOINT"):
            transport.get(
                endpoint=endpoint,
                auth_required=False,
                pretrade_decision_id="contract-test",
            )


def test_transport_trade_order_get_not_classified_as_forbidden_endpoint() -> None:
    """Reconciliation scope: GET exact-order lookup is not a transport hard-block."""
    transport = FullCoreProductiveReadOnlyGetTransportV1(handle=None)
    path = READ_ONLY_EXACT_ORDER_LOOKUP_PATH
    try:
        transport.get(
            endpoint=f"{path}?instId=TEST&clOrdId=cl-test",
            auth_required=True,
            pretrade_decision_id="contract-test",
        )
    except FullCoreProductiveReadOnlyGetError as exc:
        assert "FORBIDDEN_ENDPOINT" not in str(exc)
    else:
        pytest.fail("expected fail-closed before live network (missing handle or wire)")
