"""Instrument and interval isolation proofs for O5 read-model projection."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.isolation_proofs_v1 import (
    prove_no_instrument_cross_contamination_v1,
    prove_no_interval_cross_contamination_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.read_model_v1 import (
    project_o4_envelopes_to_canonical_dashboard_read_model_v1,
)


def _md(
    *,
    mark: float,
    event_ts: float,
    canonical: str,
    venue_id: str | None = None,
) -> NormalizedPublicMarketDataV1:
    vid = venue_id or canonical
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=canonical,
        venue_instrument_id=vid,
        venue="okx",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 0.25,
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="o5-digest",
        mapping_version="v1",
    )


def prove_instrument_isolation_via_read_model_v1() -> dict[str, Any]:
    """O5 projection rejects mixed-instrument envelopes; O4 producer isolation reused."""
    o4 = prove_no_instrument_cross_contamination_v1()
    producer_a = CanonicalPublicMdBarProducerV1(
        session_id="o5-iso-a",
        repository_sha="a" * 40,
        config_digest="cfg-o5-a",
    )
    producer_b = CanonicalPublicMdBarProducerV1(
        session_id="o5-iso-b",
        repository_sha="b" * 40,
        config_digest="cfg-o5-b",
    )
    ra = producer_a.ingest_normalized_event(
        _md(mark=100.0, event_ts=1_700_000_100.0, canonical="ETH-USDT-SWAP")
    )
    rb = producer_b.ingest_normalized_event(
        _md(mark=200.0, event_ts=1_700_000_100.0, canonical="SOL-USDT-SWAP")
    )
    env_a = producer_a.get_envelope(ra["bar_key"])
    env_b = producer_b.get_envelope(rb["bar_key"])
    assert env_a is not None and env_b is not None

    model_a = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
        [env_a],
        selection_bundle_id="bundle-a",
        projection_time_unix=1_700_000_110.0,
    )
    model_b = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
        [env_b],
        selection_bundle_id="bundle-b",
        projection_time_unix=1_700_000_110.0,
    )
    mixed_blocked = False
    try:
        project_o4_envelopes_to_canonical_dashboard_read_model_v1(
            [env_a, env_b],
            selection_bundle_id="bundle-mix",
            projection_time_unix=1_700_000_110.0,
        )
    except ValueError as exc:
        mixed_blocked = any(
            token in str(exc)
            for token in (
                "INSTRUMENT_CROSS_CONTAMINATION",
                "SESSION_ID_CROSS_CONTAMINATION",
                "REPOSITORY_SHA_CROSS_CONTAMINATION",
                "CONFIG_DIGEST_CROSS_CONTAMINATION",
            )
        )

    return {
        "ok": (
            o4["ok"] is True
            and model_a["instrument"] == "ETH-USDT-SWAP"
            and model_b["instrument"] == "SOL-USDT-SWAP"
            and model_a["instrument"] != model_b["instrument"]
            and mixed_blocked
        ),
        "proof": "INSTRUMENT_ISOLATION",
        "o4_proof": o4["proof"],
        "mixed_projection_blocked": mixed_blocked,
    }


def prove_interval_isolation_via_read_model_v1() -> dict[str, Any]:
    """O5 read model preserves single-interval envelopes; O4 interval isolation reused."""
    o4 = prove_no_interval_cross_contamination_v1()
    producer = CanonicalPublicMdBarProducerV1(
        session_id="o5-int",
        repository_sha="c" * 40,
        config_digest="cfg-o5-int",
    )
    r = producer.ingest_normalized_event(
        _md(mark=111.0, event_ts=1_700_010_100.0, canonical="ETH-USDT-SWAP")
    )
    env = producer.get_envelope(r["bar_key"])
    assert env is not None
    model = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
        [env],
        selection_bundle_id="bundle-int",
        projection_time_unix=1_700_010_110.0,
    )
    foreign = dict(env)
    foreign["interval"] = "PT5M"
    mixed_blocked = False
    try:
        project_o4_envelopes_to_canonical_dashboard_read_model_v1(
            [env, foreign],
            selection_bundle_id="bundle-int-mix",
            projection_time_unix=1_700_010_110.0,
        )
    except ValueError as exc:
        mixed_blocked = "INTERVAL_CROSS_CONTAMINATION" in str(exc)

    return {
        "ok": (o4["ok"] is True and model["interval"] == "PT1H" and mixed_blocked),
        "proof": "INTERVAL_ISOLATION",
        "o4_proof": o4["proof"],
        "interval": model["interval"],
        "mixed_projection_blocked": mixed_blocked,
    }


def run_all_o5_isolation_proofs_v1() -> dict[str, Any]:
    proofs = [
        prove_instrument_isolation_via_read_model_v1(),
        prove_interval_isolation_via_read_model_v1(),
    ]
    return {"ok": all(p["ok"] for p in proofs), "proofs": proofs}
