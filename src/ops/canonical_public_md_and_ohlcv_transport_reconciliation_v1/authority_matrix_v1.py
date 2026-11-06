"""Authority inventory matrix for public-MD / OHLCV producers and consumers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence, Tuple

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    CANONICAL_NORMALIZED_EVENT_PATH,
    CAPABILITY_ID,
    CLASS_AUTHORITATIVE,
    CLASS_DERIVED,
    CLASS_FORBIDDEN,
    CLASS_LEGACY,
    DASHBOARD_OHLCV_CLASSIFICATION,
    DASHBOARD_TRANSPORT,
)


@dataclass(frozen=True)
class AuthorityMatrixRowV1:
    path_id: str
    surface: str
    role: str
    classification: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_public_md_ohlcv_authority_matrix_v1() -> Tuple[AuthorityMatrixRowV1, ...]:
    """Enumerate every relevant public-MD / OHLCV path with one classification."""
    rows: list[AuthorityMatrixRowV1] = [
        AuthorityMatrixRowV1(
            path_id="normalized_public_market_data_v1",
            surface=(
                "src/ops/okx_native_instrument_and_mark_price_runtime_binding_"
                "fail_closed_v1/normalized_market_data_v1.py"
            ),
            role="normalized_event_schema",
            classification=CLASS_AUTHORITATIVE,
            notes="Single normalized public-MD event schema; no parallel SSOT.",
        ),
        AuthorityMatrixRowV1(
            path_id="observation_identity_v1",
            surface="src/trading/market_state/observation_identity_v1.py",
            role="observation_identity",
            classification=CLASS_AUTHORITATIVE,
            notes="Distinctness identity derived from NormalizedPublicMarketDataV1.",
        ),
        AuthorityMatrixRowV1(
            path_id="distinct_market_observation_acceptor_v1",
            surface="src/trading/market_state/distinct_market_observation_acceptor_v1.py",
            role="observation_acceptor",
            classification=CLASS_AUTHORITATIVE,
            notes="Only DISTINCT advances observation epoch; duplicates are no-ops.",
        ),
        AuthorityMatrixRowV1(
            path_id="productive_md_fetch_v1",
            surface=(
                "src/ops/okx_native_instrument_and_mark_price_runtime_binding_"
                "fail_closed_v1/productive_md_fetch_v1.py"
            ),
            role="normalized_event_producer",
            classification=CLASS_AUTHORITATIVE,
            notes="Productive fetch → NormalizedPublicMarketDataV1.",
        ),
        AuthorityMatrixRowV1(
            path_id="okx_public_market_data_client_v1",
            surface="src/ops/okx_public_market_data_client_v1.py",
            role="public_md_http_client",
            classification=CLASS_AUTHORITATIVE,
            notes="Canonical public REST client; must consume O1 proxy/env contract.",
        ),
        AuthorityMatrixRowV1(
            path_id="eea_public_md_transport_v1",
            surface=(
                "src/ops/integrated_paper_shadow_observation_wallclock_session_"
                "execution_v1/eea_public_md_transport_v1.py"
            ),
            role="public_md_http_client",
            classification=CLASS_AUTHORITATIVE,
            notes="Wallclock EEA transport; network-boundary guard + O1 proxy policy.",
        ),
        AuthorityMatrixRowV1(
            path_id="canonical_public_md_bar_producer_v1",
            surface=(
                "src/ops/canonical_public_md_and_ohlcv_transport_reconciliation_v1/"
                "canonical_bar_producer_v1.py"
            ),
            role="bar_producer",
            classification=CLASS_AUTHORITATIVE,
            notes=f"Sole authoritative bar producer: {AUTHORITATIVE_BAR_PRODUCER}.",
        ),
        AuthorityMatrixRowV1(
            path_id="okx_selected_instrument_ohlcv_readmodel_v1",
            surface="src/ops/okx_selected_instrument_ohlcv_readmodel_v1.py",
            role="ohlcv_materializer",
            classification=CLASS_DERIVED,
            notes=(
                "Dashboard candles/trades materializer demoted to DERIVED projection; "
                f"transport remains {DASHBOARD_TRANSPORT}."
            ),
        ),
        AuthorityMatrixRowV1(
            path_id="dashboard_ohlcv_projection_v1",
            surface=(
                "src/ops/canonical_public_md_and_ohlcv_transport_reconciliation_v1/"
                "dashboard_ohlcv_projection_v1.py"
            ),
            role="dashboard_projection",
            classification=CLASS_DERIVED,
            notes="Projects canonical bar envelopes into dashboard OHLCV readmodel shape.",
        ),
        AuthorityMatrixRowV1(
            path_id="market_landscape_ohlcv_http_json_poll",
            surface="src/webui/market_dashboard_landscape_shell_router_v2.py",
            role="dashboard_consumer",
            classification=CLASS_DERIVED,
            notes=f"HTTP_JSON_POLL consumer only; authority_effect=NONE; class={DASHBOARD_OHLCV_CLASSIFICATION}.",
        ),
        AuthorityMatrixRowV1(
            path_id="refresh_okx_market_dashboard_v1",
            surface="scripts/ops/refresh_okx_market_dashboard_v1.py",
            role="operator_refresh",
            classification=CLASS_DERIVED,
            notes="Operator refresh helper for derived dashboard readmodel.",
        ),
        AuthorityMatrixRowV1(
            path_id="shadow_ohlcv_builder",
            surface="src/data/shadow/ohlcv_builder.py",
            role="bar_producer",
            classification=CLASS_LEGACY,
            notes="Legacy shadow tick→bar builder; non-authoritative.",
        ),
        AuthorityMatrixRowV1(
            path_id="single_future_public_md_shadow_capture",
            surface=(
                "src/ops/single_future_canonical_runtime_public_md_no_order_shadow_"
                "evidence_v1/public_md_capture_v1.py"
            ),
            role="ingress_shadow_capture",
            classification=CLASS_LEGACY,
            notes="Shadow/evidence capture family; non-authoritative for live OHLCV truth.",
        ),
        AuthorityMatrixRowV1(
            path_id="pre_economic_okx_readonly_telemetry",
            surface="src/ops/pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1.py",
            role="ingress_telemetry",
            classification=CLASS_LEGACY,
            notes="Evidence-session telemetry; non-authoritative bar ownership.",
        ),
        AuthorityMatrixRowV1(
            path_id="bouchaud_ohlcv_proxy_research",
            surface="src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py",
            role="research_producer",
            classification=CLASS_LEGACY,
            notes="Research OHLCV proxy naming only; must not conflate with HTTP egress proxy.",
        ),
        AuthorityMatrixRowV1(
            path_id="pit_okx_pt1h_panel_ohlcv_dataset",
            surface="src/research/pit_okx_pt1h_panel_ohlcv_dataset_v1.py",
            role="research_dataset",
            classification=CLASS_LEGACY,
            notes="Research/PIT panel dataset; non-authoritative runtime producer.",
        ),
        AuthorityMatrixRowV1(
            path_id="browser_direct_okx_access",
            surface="dashboard_frontend_direct_venue",
            role="forbidden_transport",
            classification=CLASS_FORBIDDEN,
            notes="Browser must not call OKX directly.",
        ),
        AuthorityMatrixRowV1(
            path_id="parallel_normalized_event_ssot",
            surface="forbidden_parallel_normalized_ssot",
            role="forbidden_ssot",
            classification=CLASS_FORBIDDEN,
            notes="No second NormalizedPublicMarketData SSOT may be introduced.",
        ),
        AuthorityMatrixRowV1(
            path_id="silent_gap_fill_fabrication",
            surface="forbidden_silent_gap_fill",
            role="forbidden_behavior",
            classification=CLASS_FORBIDDEN,
            notes="Silent gap fill / fabricated live state is forbidden.",
        ),
        AuthorityMatrixRowV1(
            path_id="dashboard_authoritative_independent_recompute",
            surface="forbidden_dashboard_authoritative_recompute",
            role="forbidden_behavior",
            classification=CLASS_FORBIDDEN,
            notes="Dashboard must not independently recompute authoritative bars.",
        ),
    ]
    return tuple(rows)


def authority_matrix_summary_v1(
    rows: Sequence[AuthorityMatrixRowV1] | None = None,
) -> dict[str, Any]:
    matrix = tuple(rows) if rows is not None else build_public_md_ohlcv_authority_matrix_v1()
    by_class: dict[str, list[str]] = {
        CLASS_AUTHORITATIVE: [],
        CLASS_DERIVED: [],
        CLASS_LEGACY: [],
        CLASS_FORBIDDEN: [],
    }
    for row in matrix:
        by_class.setdefault(row.classification, []).append(row.path_id)

    authoritative_bar_producers = [
        r.path_id
        for r in matrix
        if r.role == "bar_producer" and r.classification == CLASS_AUTHORITATIVE
    ]
    return {
        "capability_id": CAPABILITY_ID,
        "canonical_normalized_event_path": CANONICAL_NORMALIZED_EVENT_PATH,
        "authoritative_bar_producer": AUTHORITATIVE_BAR_PRODUCER,
        "authoritative_bar_producer_path_ids": authoritative_bar_producers,
        "exactly_one_authoritative_bar_producer": len(authoritative_bar_producers) == 1,
        "dashboard_ohlcv_classification": DASHBOARD_OHLCV_CLASSIFICATION,
        "dashboard_transport": DASHBOARD_TRANSPORT,
        "counts_by_classification": {k: len(v) for k, v in by_class.items()},
        "rows": [r.to_dict() for r in matrix],
        "ok": len(authoritative_bar_producers) == 1,
    }


def assert_authority_matrix_invariants_v1(
    summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(summary) if summary is not None else authority_matrix_summary_v1()
    blockers: list[str] = []
    if not payload.get("exactly_one_authoritative_bar_producer"):
        blockers.append("AUTHORITATIVE_BAR_PRODUCER_COUNT_NOT_ONE")
    if payload.get("dashboard_ohlcv_classification") != CLASS_DERIVED:
        blockers.append("DASHBOARD_OHLCV_NOT_DERIVED")
    if payload.get("dashboard_transport") != DASHBOARD_TRANSPORT:
        blockers.append("DASHBOARD_TRANSPORT_DRIFT")
    rows = payload.get("rows") or []
    forbidden_ids = {
        "browser_direct_okx_access",
        "parallel_normalized_event_ssot",
        "silent_gap_fill_fabrication",
        "dashboard_authoritative_independent_recompute",
    }
    present_forbidden = {
        r["path_id"] for r in rows if isinstance(r, Mapping) and r.get("path_id") in forbidden_ids
    }
    if present_forbidden != forbidden_ids:
        blockers.append("FORBIDDEN_ROWS_INCOMPLETE")
    return {"ok": not blockers, "blockers": blockers, "summary": payload}
