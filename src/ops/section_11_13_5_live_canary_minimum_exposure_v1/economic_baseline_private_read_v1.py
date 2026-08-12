"""GET-only productive private-read helper for §11.13.5.E economic baseline.

Reuses §11.13.3 HTTP/signer/credential primitives. Does not reuse the consumed
§11.13.3 Owner-GO. No orders, no account mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    build_live_shadow_recon_venue_binding_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.http_client_v1 import (
    LiveShadowReconHttpClientV1,
    UrllibLiveTransportV1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_ephemeral_material_v1,
    resolve_and_load_live_secretref_ephemeral_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.okx_live_ro_signer_v1 import (
    build_okx_live_ro_get_auth_headers_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.reconciliation_v1 import (
    build_exchange_snapshot_from_endpoint_payloads_v1,
    build_local_expected_flat_shadow_state_v1,
    evaluate_live_shadow_exchange_reconciliation_v1,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.response_assertions_v1 import (
    assert_authenticated_private_read_success_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_ENTITY,
    REUSED_BINDING_REGION,
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (
    adopt_exchange_economic_baseline_local_state_v1,
)

REQUIRED_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/config",
    "/api/v5/account/balance",
    "/api/v5/account/positions",
    "/api/v5/trade/orders-pending",
)
SHADOW_RECON_SECRETREF = "secretref://vault/peak-trade/live-shadow-recon/okx"
SHADOW_RECON_CREDENTIAL_CLASS = "LIVE_SHADOW_RECONCILIATION_READ_ONLY_API_KEY"


class EconomicBaselinePrivateReadError(RuntimeError):
    """Fail-closed productive private-read violation."""


def run_economic_baseline_productive_private_read_v1(
    *,
    vault_file: Path | str,
    secretref_uri: str = SHADOW_RECON_SECRETREF,
    credential_class: str = SHADOW_RECON_CREDENTIAL_CLASS,
) -> dict[str, Any]:
    """Execute minimum GET-only private-read and adopt exchange economic baseline."""
    binding = build_live_shadow_recon_venue_binding_v1(
        environment="LIVE",
        venue=REUSED_BINDING_VENUE,
        entity=REUSED_BINDING_ENTITY,
        region=REUSED_BINDING_REGION,
        rest_host=REUSED_BINDING_REST_HOST,
        rest_base=f"https://{REUSED_BINDING_REST_HOST}",
        account_scope=REUSED_BINDING_ACCOUNT_SCOPE,
        instrument_scope=None,
    )
    backend = build_file_secretref_vault_backend_v1(vault_file=Path(vault_file))
    handle = resolve_and_load_live_secretref_ephemeral_v1(
        secret_reference=secretref_uri,
        vault_backend=backend,
        credential_class=credential_class,
    )
    try:
        client = LiveShadowReconHttpClientV1(
            binding=binding,
            transport=UrllibLiveTransportV1(),
            endpoint_allowlist=REQUIRED_ENDPOINTS,
            max_request_count=4,
            max_retries=1,
            timeout_seconds=10.0,
        )
        payloads: dict[str, Mapping[str, Any]] = {}
        endpoint_summaries: dict[str, Any] = {}
        for endpoint in REQUIRED_ENDPOINTS:
            url = f"{binding.rest_base.rstrip('/')}{endpoint}"
            headers = build_okx_live_ro_get_auth_headers_v1(handle=handle, url=url)
            response = client.get(endpoint=endpoint, headers=headers)
            headers.clear()
            assert_authenticated_private_read_success_v1(
                response=response,
                transport_class="LIVE_PRODUCTIVE_HTTP",
                venue_live_contact=True,
                expected_account_scope=(
                    binding.account_scope if endpoint.endswith("/config") else None
                ),
                require_account_identity=endpoint.endswith("/config"),
            )
            body = json.loads(response.body_bytes.decode("utf-8"))
            payloads[endpoint] = body
            endpoint_summaries[endpoint] = {
                "status_code": response.status_code,
                "code": body.get("code"),
                "ok": body.get("code") == "0",
            }
        exchange = build_exchange_snapshot_from_endpoint_payloads_v1(
            payloads_by_endpoint=payloads,
            account_identity=binding.account_scope,
        )
        local_flat = build_local_expected_flat_shadow_state_v1(account_scope=binding.account_scope)
        local_adopted = adopt_exchange_economic_baseline_local_state_v1(
            local_expected_state=local_flat,
            exchange_snapshot=exchange,
        )
        before = evaluate_live_shadow_exchange_reconciliation_v1(
            local_expected_state=local_flat,
            exchange_snapshot=exchange,
        )
        after = evaluate_live_shadow_exchange_reconciliation_v1(
            local_expected_state=local_adopted,
            exchange_snapshot=exchange,
        )
        counters = client.counters.to_dict()
        if counters.get("WRITE_REQUEST_COUNT", 0) != 0:
            raise EconomicBaselinePrivateReadError("WRITE_REQUEST_DETECTED")
        if counters.get("ORDER_REQUEST_COUNT", 0) != 0:
            raise EconomicBaselinePrivateReadError("ORDER_REQUEST_DETECTED")
        return {
            "binding": binding.to_dict(),
            "secretref_uri": secretref_uri,
            "credential_class": credential_class,
            "endpoint_summaries": endpoint_summaries,
            "counters": counters,
            "exchange_snapshot": exchange,
            "local_expected_state_flat": local_flat,
            "local_expected_state_adopted": local_adopted,
            "reconciliation_before_adoption": before.to_dict(),
            "reconciliation_after_adoption": after.to_dict(),
            "SECRET_VALUE_ACCESS": "EPHEMERAL_IN_MEMORY_BORROW_RELEASED",
            "ORDER_EFFECT": "NONE",
            "ACCOUNT_MUTATION_EFFECT": "NONE",
            "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT", 0),
            "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT", 0),
            "ok": True,
        }
    finally:
        release_live_ephemeral_material_v1(handle)
