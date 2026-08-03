"""Canonical public-MD network-boundary coverage matrix."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Tuple

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    CAPABILITY_ID,
    CLASS_AUTHORITATIVE,
    CLASS_DERIVED,
    CLASS_LEGACY,
)


@dataclass(frozen=True)
class NetworkBoundaryCoverageRowV1:
    client_id: str
    surface: str
    classification: str
    consumes_o1_environment_contract: bool
    consumes_o1_proxy_contract: bool
    starts_network_in_o4_tests: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_public_md_network_boundary_coverage_matrix_v1() -> Tuple[
    NetworkBoundaryCoverageRowV1, ...
]:
    return (
        NetworkBoundaryCoverageRowV1(
            client_id="okx_public_market_data_client_v1",
            surface="src/ops/okx_public_market_data_client_v1.py",
            classification=CLASS_AUTHORITATIVE,
            consumes_o1_environment_contract=True,
            consumes_o1_proxy_contract=True,
            starts_network_in_o4_tests=False,
            notes="assert_http_client_proxy_env_clean_v1 on default fetcher construction.",
        ),
        NetworkBoundaryCoverageRowV1(
            client_id="eea_public_md_transport_v1",
            surface=(
                "src/ops/integrated_paper_shadow_observation_wallclock_session_"
                "execution_v1/eea_public_md_transport_v1.py"
            ),
            classification=CLASS_AUTHORITATIVE,
            consumes_o1_environment_contract=True,
            consumes_o1_proxy_contract=True,
            starts_network_in_o4_tests=False,
            notes="validate_request_boundary_v1 + O1 proxy fail-closed guard.",
        ),
        NetworkBoundaryCoverageRowV1(
            client_id="okx_selected_instrument_ohlcv_readmodel_http",
            surface="src/ops/okx_selected_instrument_ohlcv_readmodel_v1.py",
            classification=CLASS_DERIVED,
            consumes_o1_environment_contract=True,
            consumes_o1_proxy_contract=True,
            starts_network_in_o4_tests=False,
            notes="Uses OkxPublicMarketDataClientV1; DERIVED dashboard materializer.",
        ),
        NetworkBoundaryCoverageRowV1(
            client_id="pre_economic_okx_readonly_telemetry",
            surface="src/ops/pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1.py",
            classification=CLASS_LEGACY,
            consumes_o1_environment_contract=True,
            consumes_o1_proxy_contract=True,
            starts_network_in_o4_tests=False,
            notes="Reuses OkxPublicMarketDataClientV1; non-authoritative telemetry.",
        ),
        NetworkBoundaryCoverageRowV1(
            client_id="single_future_public_md_shadow_capture",
            surface=(
                "src/ops/single_future_canonical_runtime_public_md_no_order_shadow_"
                "evidence_v1/public_md_capture_v1.py"
            ),
            classification=CLASS_LEGACY,
            consumes_o1_environment_contract=True,
            consumes_o1_proxy_contract=True,
            starts_network_in_o4_tests=False,
            notes="Shadow capture via OkxPublicMarketDataClientV1; non-authoritative.",
        ),
    )


def network_boundary_coverage_summary_v1() -> dict[str, Any]:
    rows = build_public_md_network_boundary_coverage_matrix_v1()
    authoritative = [r for r in rows if r.classification == CLASS_AUTHORITATIVE]
    blockers: list[str] = []
    for row in authoritative:
        if not row.consumes_o1_environment_contract:
            blockers.append(f"MISSING_O1_ENV:{row.client_id}")
        if not row.consumes_o1_proxy_contract:
            blockers.append(f"MISSING_O1_PROXY:{row.client_id}")
        if row.starts_network_in_o4_tests:
            blockers.append(f"NETWORK_STARTED_IN_O4:{row.client_id}")
    return {
        "capability_id": CAPABILITY_ID,
        "authoritative_public_md_http_clients_must_consume_o1": True,
        "rows": [r.to_dict() for r in rows],
        "authoritative_client_count": len(authoritative),
        "ok": not blockers,
        "blockers": blockers,
    }
