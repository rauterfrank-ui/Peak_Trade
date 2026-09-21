"""Dashboard-only host / OHLCV poll contract markers (Landscape V2).

Separates canonical HTML host (archive-backed poll) from O2 supervised host
(O5 durable read-only poll) without merging data sources or authority.
AUTHORITY_EFFECT=NONE — classification only.
"""

from __future__ import annotations

from typing import Any, Mapping

HOST_CONTRACT_SCHEMA_NAME = "market_dashboard_landscape_host_contract.v1"
HOST_CONTRACT_SCHEMA_VERSION = 1

DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML = "CANONICAL_LANDSCAPE_HTML_HOST"
DASHBOARD_HOST_MODE_O2_SUPERVISED = "O2_SUPERVISED_DASHBOARD_HOST"

OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL = "ARCHIVE_OKX_SELECTED_INSTRUMENT_OHLCV_READMODEL_V1"
OHLCV_SOURCE_CLASS_O5_DURABLE = "O5_DURABLE_DERIVED_READ_MODEL_V1"

LANDSCAPE_POLL_CONTRACT_CANONICAL_ARCHIVE = "canonical_landscape_html_archive_poll_v1"
LANDSCAPE_POLL_CONTRACT_O2_O5_DURABLE = "o2_supervised_o5_durable_poll_v1"

HEADER_DASHBOARD_HOST_MODE = "X-Peak-Trade-Dashboard-Host-Mode"
HEADER_OHLCV_SOURCE_CLASS = "X-Peak-Trade-Ohlcv-Source-Class"
HEADER_LANDSCAPE_POLL_CONTRACT = "X-Peak-Trade-Landscape-Poll-Contract-Id"


def canonical_landscape_html_host_contract_v1() -> dict[str, Any]:
    return {
        "host_contract_schema_name": HOST_CONTRACT_SCHEMA_NAME,
        "host_contract_schema_version": HOST_CONTRACT_SCHEMA_VERSION,
        "dashboard_host_mode": DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML,
        "ohlcv_source_class": OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL,
        "landscape_poll_contract_id": LANDSCAPE_POLL_CONTRACT_CANONICAL_ARCHIVE,
        "is_canonical_landscape_html_host_poll": True,
        "is_o2_supervised_host_poll": False,
    }


def o2_supervised_dashboard_host_contract_v1() -> dict[str, Any]:
    return {
        "host_contract_schema_name": HOST_CONTRACT_SCHEMA_NAME,
        "host_contract_schema_version": HOST_CONTRACT_SCHEMA_VERSION,
        "dashboard_host_mode": DASHBOARD_HOST_MODE_O2_SUPERVISED,
        "ohlcv_source_class": OHLCV_SOURCE_CLASS_O5_DURABLE,
        "landscape_poll_contract_id": LANDSCAPE_POLL_CONTRACT_O2_O5_DURABLE,
        "is_canonical_landscape_html_host_poll": False,
        "is_o2_supervised_host_poll": True,
    }


def merge_host_contract_into_poll_payload(
    payload: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = dict(payload)
    out.update(contract)
    return out


def poll_response_headers_from_contract(contract: Mapping[str, Any]) -> dict[str, str]:
    return {
        HEADER_DASHBOARD_HOST_MODE: str(contract["dashboard_host_mode"]),
        HEADER_OHLCV_SOURCE_CLASS: str(contract["ohlcv_source_class"]),
        HEADER_LANDSCAPE_POLL_CONTRACT: str(contract["landscape_poll_contract_id"]),
    }


def html_root_host_contract_attributes(*, contract: Mapping[str, Any]) -> dict[str, str]:
    return {
        "dashboard_host_mode": str(contract["dashboard_host_mode"]),
        "ohlcv_source_class": str(contract["ohlcv_source_class"]),
        "landscape_poll_contract_id": str(contract["landscape_poll_contract_id"]),
    }
