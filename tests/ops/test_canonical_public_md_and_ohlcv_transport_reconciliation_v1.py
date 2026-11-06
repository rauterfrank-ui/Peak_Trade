"""Deterministic contract tests for CAPABILITY_O4."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.authority_envelope_v1 import (
    AuthoritativeOhlcvBarEnvelopeV1,
    assert_envelope_has_required_fields_v1,
    authority_envelope_field_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.authority_matrix_v1 import (
    assert_authority_matrix_invariants_v1,
    authority_matrix_summary_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
    bar_state_contract_v1,
    normalize_bar_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    AUTHORITATIVE_BAR_PRODUCER,
    AUTHORITY_ENVELOPE_FIELDS,
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
    BAR_STATE_IN_PROGRESS,
    CANONICAL_NORMALIZED_EVENT_PATH,
    CAPABILITY_ID,
    CLASS_DERIVED,
    DASHBOARD_TRANSPORT,
    SAFETY_INVARIANTS,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.correction_revision_contract_v1 import (
    assert_correction_allowed_v1,
    correction_contract_v1,
    revision_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.dashboard_ohlcv_projection_v1 import (
    dashboard_ohlcv_authority_declaration_v1,
    project_authoritative_envelopes_to_dashboard_ohlcv_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.deduplication_contract_v1 import (
    deduplication_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.finalization_contract_v1 import (
    finalization_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.interval_contract_v1 import (
    IntervalContractErrorV1,
    interval_duration_seconds_v1,
    normalize_interval_id_v1,
    supported_intervals_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.isolation_proofs_v1 import (
    run_all_isolation_proofs_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.missing_stale_contract_v1 import (
    missing_bar_contract_v1,
    stale_bar_contract_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.network_boundary_coverage_matrix_v1 import (
    network_boundary_coverage_summary_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.normalized_event_path_v1 import (
    assert_no_parallel_normalized_ssot_v1,
    canonical_normalized_event_path_descriptor_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.out_of_order_contract_v1 import (
    out_of_order_contract_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)
from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
    AUTHORITY_CLASSIFICATION,
    DASHBOARD_TRANSPORT as READMODEL_TRANSPORT,
    INDEPENDENT_AUTHORITATIVE_RECOMPUTE_ALLOWED,
    o4_derived_authority_stamp_v1,
)


def _md(
    *,
    mark: float,
    event_ts: float,
    receive_ts: float | None = None,
    canonical: str = "ETH-USDT-SWAP",
    venue_id: str = "ETH-USDT-SWAP",
) -> NormalizedPublicMarketDataV1:
    return NormalizedPublicMarketDataV1(
        canonical_instrument_id=canonical,
        venue_instrument_id=venue_id,
        venue="okx",
        mark_px=mark,
        event_ts_unix=event_ts,
        receive_ts_unix=float(receive_ts if receive_ts is not None else event_ts + 0.25),
        mark_price_endpoint="/api/v5/public/mark-price",
        mark_price_field="markPx",
        mapping_digest="o4-digest",
        mapping_version="v1",
    )


def _producer() -> CanonicalPublicMdBarProducerV1:
    return CanonicalPublicMdBarProducerV1(
        session_id="o4-session",
        repository_sha="f" * 40,
        config_digest="cfg-o4",
    )


def test_capability_constants_and_safety_invariants() -> None:
    assert CAPABILITY_ID.endswith("_V1")
    assert AUTHORITATIVE_BAR_PRODUCER == "CanonicalPublicMdBarProducerV1"
    assert SAFETY_INVARIANTS["NO_PARALLEL_NORMALIZED_EVENT_SSOT"] is True
    assert SAFETY_INVARIANTS["NETWORK_SESSION_ALLOWED"] is False
    assert SAFETY_INVARIANTS["ORDERS_ALLOWED"] is False


def test_authority_matrix_exactly_one_authoritative_bar_producer() -> None:
    summary = authority_matrix_summary_v1()
    assert summary["ok"] is True
    assert summary["exactly_one_authoritative_bar_producer"] is True
    assert summary["dashboard_ohlcv_classification"] == CLASS_DERIVED
    assert summary["dashboard_transport"] == DASHBOARD_TRANSPORT
    checked = assert_authority_matrix_invariants_v1(summary)
    assert checked["ok"] is True


def test_canonical_normalized_event_path_reuses_existing_ssot() -> None:
    desc = canonical_normalized_event_path_descriptor_v1()
    assert desc["path"] == CANONICAL_NORMALIZED_EVENT_PATH
    assert desc["parallel_normalized_event_ssot_allowed"] is False
    assert assert_no_parallel_normalized_ssot_v1()["ok"] is True
    with pytest.raises(ValueError, match="PARALLEL_NORMALIZED_EVENT_SSOT"):
        assert_no_parallel_normalized_ssot_v1(extra_ssot_declared=True)


def test_interval_contract_aliases_and_duration() -> None:
    assert normalize_interval_id_v1("1H") == "PT1H"
    assert normalize_interval_id_v1("PT1H") == "PT1H"
    assert interval_duration_seconds_v1("1H") == 3600
    assert supported_intervals_contract_v1()["cross_interval_contamination_forbidden"] is True
    with pytest.raises(IntervalContractErrorV1):
        normalize_interval_id_v1("5m")


def test_shared_state_and_finalization_correction_contracts() -> None:
    assert set(bar_state_contract_v1()["states"]) >= {
        BAR_STATE_IN_PROGRESS,
        BAR_STATE_FINALIZED,
        BAR_STATE_CORRECTED,
    }
    assert finalization_contract_v1()["duplicate_finalization_forbidden"] is True
    assert correction_contract_v1()["correction_increments_revision"] is True
    assert revision_contract_v1()["revision_monotonic_non_decreasing"] is True
    assert deduplication_contract_v1()["duplicate_events_do_not_advance_authoritative_state"]
    assert out_of_order_contract_v1()["out_of_order_must_be_explicitly_classified"]
    assert missing_bar_contract_v1()["silent_gap_fill_forbidden"] is True
    assert stale_bar_contract_v1()["stale_is_explicit_state"] is True
    assert normalize_bar_state_v1("FINALIZED") == BAR_STATE_FINALIZED
    rev = assert_correction_allowed_v1(current_state=BAR_STATE_FINALIZED, current_revision=0)
    assert rev == 1


def test_authority_envelope_required_fields() -> None:
    fields = authority_envelope_field_contract_v1()["required_fields"]
    assert list(AUTHORITY_ENVELOPE_FIELDS) == fields
    identity = {
        "venue": "okx",
        "canonical_instrument_id": "ETH-USDT-SWAP",
        "venue_instrument_id": "ETH-USDT-SWAP",
        "venue_event_time": 1_700_000_000.0,
        "mark_price": 10.0,
    }
    env = AuthoritativeOhlcvBarEnvelopeV1(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx",
        interval="PT1H",
        bar_open_time=1_700_000_000.0,
        bar_close_time=1_700_003_600.0,
        event_time=1_700_000_100.0,
        receive_time=1_700_000_101.0,
        first_observation_identity=identity,
        last_observation_identity=identity,
        session_id="s1",
        repository_sha="a" * 40,
        config_digest="cfg",
        transport_lag=1.0,
        quality_state=BAR_STATE_IN_PROGRESS,
        finalization_state=BAR_STATE_IN_PROGRESS,
        revision=0,
        open=10.0,
        high=10.0,
        low=10.0,
        close=10.0,
        volume=0.0,
    )
    payload = env.to_dict()
    assert_envelope_has_required_fields_v1(payload)
    for field in AUTHORITY_ENVELOPE_FIELDS:
        assert field in payload


def test_duplicate_does_not_advance_authoritative_state() -> None:
    producer = _producer()
    evt = _md(mark=101.0, event_ts=1_700_010_000.0)
    first = producer.ingest_normalized_event(evt)
    second = producer.ingest_normalized_event(evt)
    assert first["advance"] is True
    assert second["advance"] is False
    assert second["classification"] in {"duplicate", "transport_only_duplicate"}
    env = producer.get_envelope(first["bar_key"])
    assert env is not None
    assert env["sample_count"] == 1


def test_out_of_order_classified_and_does_not_mutate_finalized() -> None:
    producer = _producer()
    later = _md(mark=110.0, event_ts=1_700_020_500.0)
    earlier = _md(mark=109.0, event_ts=1_700_020_100.0)
    r1 = producer.ingest_normalized_event(later)
    producer.finalize_bar(
        canonical_instrument_id="ETH-USDT-SWAP",
        bar_open_time=float(r1["envelope"]["bar_open_time"]),
    )
    with pytest.raises(Exception):
        producer.ingest_normalized_event(earlier)


def test_finalized_immutable_except_explicit_correction() -> None:
    producer = _producer()
    r = producer.ingest_normalized_event(_md(mark=120.0, event_ts=1_700_030_100.0))
    open_time = float(r["envelope"]["bar_open_time"])
    producer.finalize_bar(canonical_instrument_id="ETH-USDT-SWAP", bar_open_time=open_time)
    with pytest.raises(BarStateContractErrorV1, match="FINALIZED_IMMUTABLE"):
        producer.ingest_normalized_event(_md(mark=121.0, event_ts=1_700_030_200.0))
    corrected = producer.ingest_normalized_event(
        _md(mark=122.0, event_ts=1_700_030_300.0),
        allow_correction_on_finalized=True,
    )
    assert corrected["corrected"] is True
    assert corrected["envelope"]["revision"] == 1
    assert corrected["envelope"]["finalization_state"] == BAR_STATE_CORRECTED


def test_in_progress_update_and_missing_stale() -> None:
    producer = _producer()
    r1 = producer.ingest_normalized_event(_md(mark=130.0, event_ts=1_700_040_100.0))
    r2 = producer.ingest_normalized_event(_md(mark=131.0, event_ts=1_700_040_200.0))
    assert r1["advance"] and r2["advance"]
    env = producer.get_envelope(r2["bar_key"])
    assert env is not None
    assert env["open"] == 130.0
    assert env["high"] == 131.0
    assert env["close"] == 131.0
    assert env["sample_count"] == 2
    missing = producer.mark_missing(
        canonical_instrument_id="ETH-USDT-SWAP",
        venue_instrument_id="ETH-USDT-SWAP",
        venue="okx",
        bar_open_time=1_700_043_600.0,
    )
    assert missing["state"] == "MISSING_BAR"
    stale = producer.mark_stale(bar_key=r2["bar_key"])
    assert stale["state"] == "STALE_BAR"


def test_dashboard_demotion_and_projection() -> None:
    assert AUTHORITY_CLASSIFICATION == CLASS_DERIVED
    assert READMODEL_TRANSPORT == DASHBOARD_TRANSPORT
    assert INDEPENDENT_AUTHORITATIVE_RECOMPUTE_ALLOWED is False
    stamp = o4_derived_authority_stamp_v1()
    assert stamp["authority_classification"] == CLASS_DERIVED
    decl = dashboard_ohlcv_authority_declaration_v1()
    assert decl["independent_authoritative_recompute_allowed"] is False
    producer = _producer()
    producer.ingest_normalized_event(_md(mark=140.0, event_ts=1_700_050_100.0))
    projected = project_authoritative_envelopes_to_dashboard_ohlcv_v1(
        producer.list_envelopes(),
        selection_bundle_id="bundle",
    )
    assert projected["authority_classification"] == CLASS_DERIVED
    assert projected["dashboard_transport"] == DASHBOARD_TRANSPORT
    assert projected["independent_authoritative_recompute"] is False
    assert projected["authoritative_bar_producer"] == AUTHORITATIVE_BAR_PRODUCER


def test_network_boundary_coverage_matrix() -> None:
    summary = network_boundary_coverage_summary_v1()
    assert summary["ok"] is True
    assert summary["authoritative_client_count"] >= 2
    for row in summary["rows"]:
        if row["classification"] == "AUTHORITATIVE":
            assert row["consumes_o1_environment_contract"] is True
            assert row["consumes_o1_proxy_contract"] is True
            assert row["starts_network_in_o4_tests"] is False


def test_isolation_proofs_bundle() -> None:
    result = run_all_isolation_proofs_v1()
    assert result["ok"] is True
    names = {p["proof"] for p in result["proofs"]}
    assert "NO_INSTRUMENT_CROSS_CONTAMINATION" in names
    assert "NO_INTERVAL_CROSS_CONTAMINATION" in names
    assert "NO_DUPLICATE_FINALIZATION" in names
    assert "NO_SILENT_GAP_FILL" in names
    assert "NO_DASHBOARD_AUTHORITATIVE_INDEPENDENT_RECOMPUTATION" in names


def test_no_network_session_or_orders_in_module_tree(repo_root: Path | None = None) -> None:
    root = Path(__file__).resolve().parents[2]
    pkg = root / "src/ops/canonical_public_md_and_ohlcv_transport_reconciliation_v1"
    forbidden = ("urlopen(", "OkxPublicMarketDataClientV1(", "requests.get", "httpx.")
    for path in pkg.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains {token}"
