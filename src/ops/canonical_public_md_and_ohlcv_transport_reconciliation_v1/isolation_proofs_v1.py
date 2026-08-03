"""Deterministic isolation / negative-control proofs for O4 contracts."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    CLASS_DERIVED,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.dashboard_ohlcv_projection_v1 import (
    dashboard_ohlcv_authority_declaration_v1,
    project_authoritative_envelopes_to_dashboard_ohlcv_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.missing_stale_contract_v1 import (
    mark_missing_bar_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)


def _norm(
    *,
    canonical: str,
    venue_id: str,
    venue: str,
    mark: float,
    event_ts: float,
    receive_ts: float,
) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_id,
        venue=venue,
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=receive_ts,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="digest-o4",
        mapping_version="v1",
    )


def prove_no_instrument_cross_contamination_v1() -> dict[str, Any]:
    """Foreign instrument is fail-closed (C1 IDENTITY_CONFLICT) and must not mutate bar A.

    Separate producers remain instrument-isolated; mixed projection is rejected.
    """
    producer_a = CanonicalPublicMdBarProducerV1(
        session_id="sess-iso-a",
        repository_sha="a" * 40,
        config_digest="cfg-iso",
    )
    producer_b = CanonicalPublicMdBarProducerV1(
        session_id="sess-iso-b",
        repository_sha="a" * 40,
        config_digest="cfg-iso",
    )
    a = _norm(
        canonical="ETH-USDT-SWAP",
        venue_id="ETH-USDT-SWAP",
        venue="okx",
        mark=100.0,
        event_ts=1_700_000_100.0,
        receive_ts=1_700_000_101.0,
    )
    b = _norm(
        canonical="SOL-USDT-SWAP",
        venue_id="SOL-USDT-SWAP",
        venue="okx",
        mark=200.0,
        event_ts=1_700_000_200.0,
        receive_ts=1_700_000_201.0,
    )
    ra = producer_a.ingest_normalized_event(a)
    # Same producer: foreign instrument must not advance / contaminate.
    foreign = producer_a.ingest_normalized_event(b)
    env_a = producer_a.get_envelope(ra["bar_key"])
    assert env_a is not None
    rb = producer_b.ingest_normalized_event(b)
    env_b = producer_b.get_envelope(rb["bar_key"])
    assert env_b is not None
    mixed_projection_blocked = False
    try:
        project_authoritative_envelopes_to_dashboard_ohlcv_v1(
            [env_a, env_b],
            selection_bundle_id="bundle-mix",
        )
    except ValueError as exc:
        mixed_projection_blocked = "INSTRUMENT_CROSS_CONTAMINATION" in str(exc)
    return {
        "ok": (
            ra["advance"] is True
            and foreign["advance"] is False
            and foreign["classification"] == "identity_conflict"
            and env_a["canonical_instrument_id"] == "ETH-USDT-SWAP"
            and env_a["close"] == 100.0
            and env_b["canonical_instrument_id"] == "SOL-USDT-SWAP"
            and ra["bar_key"] != rb["bar_key"]
            and mixed_projection_blocked
        ),
        "proof": "NO_INSTRUMENT_CROSS_CONTAMINATION",
        "bar_keys": [ra["bar_key"], rb["bar_key"]],
        "foreign_classification": foreign["classification"],
    }


def prove_no_interval_cross_contamination_v1() -> dict[str, Any]:
    # Producer is bound to one interval; envelopes always carry that interval.
    producer = CanonicalPublicMdBarProducerV1(
        session_id="sess-int",
        repository_sha="b" * 40,
        config_digest="cfg-int",
        interval="PT1H",
    )
    evt = _norm(
        canonical="ETH-USDT-SWAP",
        venue_id="ETH-USDT-SWAP",
        venue="okx",
        mark=111.0,
        event_ts=1_700_000_500.0,
        receive_ts=1_700_000_501.0,
    )
    r = producer.ingest_normalized_event(evt)
    env = producer.get_envelope(r["bar_key"])
    assert env is not None
    return {
        "ok": env["interval"] == "PT1H" and producer.interval == "PT1H",
        "proof": "NO_INTERVAL_CROSS_CONTAMINATION",
        "interval": env["interval"],
    }


def prove_no_duplicate_finalization_v1() -> dict[str, Any]:
    producer = CanonicalPublicMdBarProducerV1(
        session_id="sess-fin",
        repository_sha="c" * 40,
        config_digest="cfg-fin",
    )
    evt = _norm(
        canonical="ETH-USDT-SWAP",
        venue_id="ETH-USDT-SWAP",
        venue="okx",
        mark=120.0,
        event_ts=1_700_001_000.0,
        receive_ts=1_700_001_001.0,
    )
    r = producer.ingest_normalized_event(evt)
    open_time = float(r["envelope"]["bar_open_time"])
    producer.finalize_bar(canonical_instrument_id="ETH-USDT-SWAP", bar_open_time=open_time)
    blocked = False
    try:
        producer.finalize_bar(canonical_instrument_id="ETH-USDT-SWAP", bar_open_time=open_time)
    except BarStateContractErrorV1 as exc:
        blocked = "DUPLICATE_FINALIZATION" in str(exc)
    return {"ok": blocked, "proof": "NO_DUPLICATE_FINALIZATION"}


def prove_no_silent_gap_fill_v1() -> dict[str, Any]:
    blocked = False
    try:
        mark_missing_bar_v1(fabricate_fill=True)
    except BarStateContractErrorV1 as exc:
        blocked = "SILENT_GAP_FILL_FORBIDDEN" in str(exc)
    producer = CanonicalPublicMdBarProducerV1(
        session_id="sess-gap",
        repository_sha="d" * 40,
        config_digest="cfg-gap",
    )
    explicit = producer.mark_missing(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx",
        bar_open_time=1_700_002_000.0,
        fabricate_fill=False,
    )
    return {
        "ok": blocked and explicit["state"] == "MISSING_BAR",
        "proof": "NO_SILENT_GAP_FILL",
        "explicit_missing": True,
    }


def prove_no_dashboard_authoritative_recomputation_v1() -> dict[str, Any]:
    decl = dashboard_ohlcv_authority_declaration_v1()
    producer = CanonicalPublicMdBarProducerV1(
        session_id="sess-dash",
        repository_sha="e" * 40,
        config_digest="cfg-dash",
    )
    evt = _norm(
        canonical="ETH-USDT-SWAP",
        venue_id="ETH-USDT-SWAP",
        venue="okx",
        mark=130.0,
        event_ts=1_700_003_000.0,
        receive_ts=1_700_003_001.0,
    )
    producer.ingest_normalized_event(evt)
    projected = project_authoritative_envelopes_to_dashboard_ohlcv_v1(
        producer.list_envelopes(),
        selection_bundle_id="bundle-o4",
    )
    return {
        "ok": (
            decl["authority_classification"] == CLASS_DERIVED
            and decl["independent_authoritative_recompute_allowed"] is False
            and projected["authority_classification"] == CLASS_DERIVED
            and projected["authoritative_bar_producer"] == AUTHORITATIVE_BAR_PRODUCER
            and projected["independent_authoritative_recompute"] is False
        ),
        "proof": "NO_DASHBOARD_AUTHORITATIVE_INDEPENDENT_RECOMPUTATION",
        "declaration": decl,
    }


def run_all_isolation_proofs_v1() -> dict[str, Any]:
    proofs = [
        prove_no_instrument_cross_contamination_v1(),
        prove_no_interval_cross_contamination_v1(),
        prove_no_duplicate_finalization_v1(),
        prove_no_silent_gap_fill_v1(),
        prove_no_dashboard_authoritative_recomputation_v1(),
    ]
    return {
        "ok": all(bool(p.get("ok")) for p in proofs),
        "proofs": proofs,
    }
