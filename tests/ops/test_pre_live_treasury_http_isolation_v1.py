"""Treasury HTTP isolation for currently reachable pre-live / trading clients.

No network. No Permission-GET. Does not wire treasury_separation_gate.
PL-TF-002 remains FROZEN_PENDING_NETWORK_EVIDENCE.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS,
    PRIVATE_READONLY_GET_ENDPOINTS,
)
from src.ops.capability_11_section_11_12_1_productive_private_readonly_api_and_account_identity_v1.constants_v1 import (
    SECTION_11_12_1_ALLOWED_ENDPOINTS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
    METHOD_GET,
    PRIVATE_GET_PATHS,
    PUBLIC_GET_PATHS,
)
from src.ops.section_11_13_2_live_private_read_only_v1 import http_client_v1 as ro_http
from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    ENDPOINT_ALLOWLIST as RO_ALLOWLIST,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS as RO_FORBIDDEN,
    METHOD_ALLOWLIST as RO_METHODS,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1 import (
    http_client_v1 as shadow_http,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    ENDPOINT_ALLOWLIST as SHADOW_ALLOWLIST,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS as SHADOW_FORBIDDEN,
    METHOD_ALLOWLIST as SHADOW_METHODS,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1 import http_client_v1 as dry_http
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    ENDPOINT_ALLOWLIST as DRY_ALLOWLIST,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS as DRY_FORBIDDEN,
    METHOD_ALLOWLIST as DRY_METHODS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS as CANARY_FORBIDDEN,
    GET_ENDPOINTS_PRIVATE as CANARY_GET_PRIVATE,
    GET_ENDPOINTS_PUBLIC as CANARY_GET_PUBLIC,
    POST_ENDPOINTS_GATED as CANARY_POST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
)
from src.ops.treasury_separation_gate import TREASURY_ONLY_OPERATIONS, evaluate_treasury_policy

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1"

TREASURY_ENDPOINTS = (
    "/api/v5/asset/withdrawal",
    "/api/v5/asset/transfer",
    "/api/v5/asset/deposit-address",
)
TRADE_ORDER = "/api/v5/trade/order"


class _NoopCanaryTransport:
    transport_class = "INJECTED_TEST_DOUBLE"
    venue_live_contact = False

    def send(self, request):  # pragma: no cover - isolation tests never send
        raise AssertionError("treasury isolation test must not send")


def _canary_client() -> LiveCanaryHttpClientV1:
    return LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=_NoopCanaryTransport(),
    )


def test_treasury_separation_gate_remains_unwired_helper() -> None:
    texts = [path.read_text(encoding="utf-8") for path in PACKAGE_DIR.glob("*.py")]
    joined = "\n".join(texts)
    assert "treasury_separation_gate" not in joined
    assert "enforce_treasury_policy" not in joined
    bot = evaluate_treasury_policy("withdraw", role="bot")
    assert bot.allowed is False
    assert "withdraw" in TREASURY_ONLY_OPERATIONS


def test_canary_trade_order_remains_separately_governed() -> None:
    assert TRADE_ORDER in CANARY_POST
    for endpoint in TREASURY_ENDPOINTS:
        assert endpoint not in CANARY_POST
        assert endpoint not in CANARY_GET_PRIVATE
        assert endpoint not in CANARY_GET_PUBLIC


@pytest.mark.parametrize("endpoint", TREASURY_ENDPOINTS)
def test_canary_treasury_and_unknown_mutation_deny(endpoint: str) -> None:
    client = _canary_client()
    with pytest.raises(LiveCanaryHttpError, match="POST_ENDPOINT_NOT_ALLOWLISTED|MUTATION"):
        client._build_request(method="POST", endpoint=endpoint)
    with pytest.raises(LiveCanaryHttpError, match="ENDPOINT_NOT_ALLOWLISTED|MUTATION"):
        client._build_request(method="GET", endpoint=endpoint)


def test_canary_unknown_mutation_and_generic_post_path_deny() -> None:
    client = _canary_client()
    with pytest.raises(LiveCanaryHttpError, match="POST_ENDPOINT_NOT_ALLOWLISTED|MUTATION"):
        client._build_request(method="POST", endpoint="/api/v5/asset/withdrawal-auto")
    with pytest.raises(LiveCanaryHttpError, match="HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE"):
        client._build_request(method="PUT", endpoint=TRADE_ORDER)


@pytest.mark.parametrize(
    ("allowlist", "forbidden", "methods", "asserter"),
    [
        (RO_ALLOWLIST, RO_FORBIDDEN, RO_METHODS, ro_http.assert_endpoint_allowlisted_v1),
        (
            SHADOW_ALLOWLIST,
            SHADOW_FORBIDDEN,
            SHADOW_METHODS,
            shadow_http.assert_endpoint_allowlisted_v1,
        ),
        (DRY_ALLOWLIST, DRY_FORBIDDEN, DRY_METHODS, dry_http.assert_endpoint_allowlisted_v1),
    ],
)
def test_readonly_shadow_dryrun_clients_deny_treasury(
    allowlist, forbidden, methods, asserter
) -> None:
    assert methods == ("GET",)
    for endpoint in TREASURY_ENDPOINTS:
        assert endpoint not in allowlist
        with pytest.raises(Exception, match="ENDPOINT_NOT_ALLOWLISTED|MUTATION"):
            asserter(endpoint)
    assert any("withdrawal" in marker for marker in forbidden)
    assert any("transfer" in marker for marker in forbidden)


def test_section_11_12_1_and_cap_11_3_have_no_treasury_mutation() -> None:
    for endpoint in TREASURY_ENDPOINTS:
        assert endpoint not in SECTION_11_12_1_ALLOWED_ENDPOINTS
        assert endpoint not in PRIVATE_READONLY_GET_ENDPOINTS
    assert "withdraw" in PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS
    assert "transfer" in PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS
    assert "submit_order" in PRIVATE_READONLY_FORBIDDEN_MUTATION_ACTIONS


def test_full_core_transport_is_get_only_and_has_no_treasury_paths() -> None:
    assert METHOD_GET == "GET"
    for endpoint in TREASURY_ENDPOINTS:
        assert endpoint not in PUBLIC_GET_PATHS
        assert endpoint not in PRIVATE_GET_PATHS
    assert hasattr(FullCoreFreshPretradeGetTransportV1, "get")
    assert not hasattr(FullCoreFreshPretradeGetTransportV1, "post")
    assert not hasattr(FullCoreFreshPretradeGetTransportV1, "withdraw")
    assert not hasattr(FullCoreFreshPretradeGetTransportV1, "transfer")


def test_no_auto_withdraw_path_on_full_core_package() -> None:
    texts = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE_DIR.glob("*.py"))
    assert "asset/withdrawal" not in texts
    assert "auto-withdraw" not in texts
    assert "auto_withdraw" not in texts
