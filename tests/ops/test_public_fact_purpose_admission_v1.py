"""Actual durable-store→ranking source rejects wrong-purpose/PIT material."""

from copy import deepcopy
from dataclasses import replace

import pytest

from src.ops.economic_md_input_producer_v1.purpose_admission_v1 import PublicFactPurposePolicyV1
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.durable_store_v1 import (
    append_fact_v1,
    default_store_paths_v1,
)
from tests.ops.test_public_fact_consumer_semantics_v1 import _fact

NOW = 1793836802000
KINDS = ("FinalizedPt1mMarkFactV1", "BestBidAskFactV1")


def _policy():
    # Explicit test-only thresholds, not productive numeric defaults.
    return PublicFactPurposePolicyV1(
        purpose="RANKING",
        consumer="PublicRuntimeEconomicMdPublicSourceV1",
        canonical_instrument_id="inst-eth-usdt-perp",
        allowed_sources=tuple((k, "test-only-source") for k in KINDS),
        maximum_ages_seconds=tuple((k, 5, 5) for k in KINDS),
        maximum_capture_skew_seconds=2,
        allow_corrected=False,
        finalized_kinds=("FinalizedPt1mMarkFactV1",),
    )


def _rows():
    rows = [_fact(k) for k in KINDS]
    rows[0]["interval_start_ms"] -= 60000
    for r in rows:
        r["instrument"]["canonical_instrument_id"] = "inst-eth-usdt-perp"
        r["quality"] = {
            "finalized": True,
            "in_progress": False,
            "missing": False,
            "stale": False,
            "corrected": False,
            "gap_detected": False,
        }
    return rows


def _read(root, rows, policy=None):
    paths = default_store_paths_v1(root)
    for row in rows:
        append_fact_v1(paths, row)
    return PublicRuntimeEconomicMdPublicSourceV1(
        root, policy or _policy(), NOW
    ).collect_instrument_raw_input_v1(venue_native_id="ETH-USDT-SWAP")


def test_future_event_capture_and_effective_versions_cannot_replace_asof_quote(tmp_path):
    rows = _rows()
    for which in ("event", "capture", "effective"):
        future = deepcopy(rows[1])
        future["bid_px"] = "999"
        if which == "event":
            future["timestamps"]["venue_event_time_ms"] = NOW + 1000
        else:
            future["timestamps"]["captured_at" if which == "capture" else "effective_at"] = (
                "2026-11-05T00:00:03Z"
            )
        rows.append(future)
    result = _read(tmp_path, rows)
    assert result.ticker.bid_px == "100.1"
    assert len(result.marks) == 1


@pytest.mark.parametrize("purpose", ["TRADING", "LIQUIDITY", "OUTCOME", "RESEARCH"])
def test_another_purpose_policy_cannot_authorize_ranking(tmp_path, purpose):
    with pytest.raises(ValueError, match="CONSUMER_PURPOSE_MISMATCH"):
        _read(tmp_path, _rows(), replace(_policy(), purpose=purpose))


@pytest.mark.parametrize(
    "change,reason",
    [
        ("stale_event", "REQUIRED_KIND_UNAVAILABLE_ASOF"),
        ("stale_capture", "REQUIRED_KIND_UNAVAILABLE_ASOF"),
        ("source", "SOURCE_FORBIDDEN"),
        ("instrument", "INSTRUMENT_MISMATCH"),
        ("missing_quality", "QUALITY_REQUIRED"),
        ("gap", "QUALITY_REJECTED"),
        ("not_finalized", "QUALITY_REJECTED"),
        ("corrected", "CORRECTION_FORBIDDEN"),
    ],
)
def test_inadmissible_source_never_becomes_ranking_input(tmp_path, change, reason):
    rows = _rows()
    row = rows[0]
    if change == "stale_event":
        row["timestamps"]["venue_event_time_ms"] -= 6000
    elif change == "stale_capture":
        row["timestamps"]["captured_at"] = "2026-11-04T23:59:55Z"
    elif change == "source":
        row["provenance"]["endpoint_or_channel"] = "unapproved"
    elif change == "instrument":
        row["instrument"]["canonical_instrument_id"] = "foreign"
    elif change == "missing_quality":
        row.pop("quality")
    elif change == "gap":
        row["quality"]["gap_detected"] = True
    elif change == "not_finalized":
        row["quality"]["finalized"] = False
    else:
        row["quality"]["corrected"] = True
    with pytest.raises(ValueError, match=reason):
        _read(tmp_path, rows)


def test_quote_is_not_required_to_be_a_finalized_candle(tmp_path):
    rows = _rows()
    rows[1]["quality"]["finalized"] = False
    assert _read(tmp_path, rows).ticker is not None


def test_capture_skew_and_missing_policy_fail_closed(tmp_path):
    with pytest.raises(ValueError, match="CAPTURE_SKEW"):
        rows = _rows()
        rows[1]["timestamps"]["captured_at"] = "2026-11-05T00:00:00Z"
        _read(tmp_path, rows, replace(_policy(), maximum_capture_skew_seconds=0.5))
    with pytest.raises(ValueError, match="TYPED_POLICY_REQUIRED"):
        PublicRuntimeEconomicMdPublicSourceV1(
            tmp_path, as_of_ms=NOW
        ).collect_instrument_raw_input_v1(venue_native_id="ETH-USDT-SWAP")


def test_finalized_mark_flag_does_not_override_bar_close_time(tmp_path):
    rows = _rows()
    rows[0]["interval_start_ms"] += 60000
    with pytest.raises(ValueError, match="FINALIZED_MARK_NOT_CLOSED"):
        _read(tmp_path, rows)
