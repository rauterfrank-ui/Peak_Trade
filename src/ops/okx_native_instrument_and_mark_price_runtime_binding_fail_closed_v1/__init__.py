"""OKX_NATIVE_INSTRUMENT_AND_MARK_PRICE_RUNTIME_BINDING_FAIL_CLOSED_V1."""

from __future__ import annotations

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    CAPABILITY_ID,
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_FIELD,
    PACKAGE_MARKER,
    VENUE_MAPPING_VERSION,
)

__all__ = [
    "CAPABILITY_ID",
    "MARK_PRICE_ENDPOINT",
    "MARK_PRICE_FIELD",
    "PACKAGE_MARKER",
    "VENUE_MAPPING_VERSION",
    "classify_transport_message_v1",
    "fetch_normalized_public_market_data_v1",
    "parse_public_mark_price_response_v1",
    "resolve_okx_venue_instrument_mapping_v1",
    "run_offline_okx_native_mark_price_binding_probe_v1",
    "verify_okx_native_instrument_mark_price_authority_inventory_v1",
]


def __getattr__(name: str):
    if name == "classify_transport_message_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
            classify_transport_message_v1,
        )

        return classify_transport_message_v1
    if name == "parse_public_mark_price_response_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.mark_price_contract_v1 import (
            parse_public_mark_price_response_v1,
        )

        return parse_public_mark_price_response_v1
    if name == "resolve_okx_venue_instrument_mapping_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
            resolve_okx_venue_instrument_mapping_v1,
        )

        return resolve_okx_venue_instrument_mapping_v1
    if name == "fetch_normalized_public_market_data_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.productive_md_fetch_v1 import (
            fetch_normalized_public_market_data_v1,
        )

        return fetch_normalized_public_market_data_v1
    if name == "run_offline_okx_native_mark_price_binding_probe_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.offline_integration_probe_v1 import (
            run_offline_okx_native_mark_price_binding_probe_v1,
        )

        return run_offline_okx_native_mark_price_binding_probe_v1
    if name == "verify_okx_native_instrument_mark_price_authority_inventory_v1":
        from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.authority_inventory_v1 import (
            verify_okx_native_instrument_mark_price_authority_inventory_v1,
        )

        return verify_okx_native_instrument_mark_price_authority_inventory_v1
    raise AttributeError(name)
