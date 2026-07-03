"""Contract tests for okx_production_instrument_lifecycle_source_v1."""

from __future__ import annotations

import pytest

from src.research.okx_production_instrument_lifecycle_source_v1 import (
    MIN_ELIGIBLE_INSTRUMENT_COUNT,
    SOURCE_ID,
    OkxLifecycleSourceErrorCode,
    build_lifecycle_source_observations_v1,
    build_okx_lifecycle_source_snapshot_v1,
    evaluate_okx_instrument_eligibility_v1,
    is_forbidden_okx_instrument_token,
    is_okx_linear_usdt_perpetual,
    select_eligible_okx_instruments_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1,
    _REGISTERED_SOURCES_V0,
    assemble_registry_snapshot_v1,
)


def _live_inst(base: str, *, inst_id: str | None = None) -> dict[str, str]:
    symbol = inst_id or f"{base}-USDT-SWAP"
    return {
        "instId": symbol,
        "instType": "SWAP",
        "settleCcy": "USDT",
        "ctType": "linear",
        "baseCcy": base,
        "state": "live",
        "listTime": "1609459200000",
        "expTime": "",
    }


class TestProductionSourceRegistration:
    def test_production_source_registered_in_registry_owner(self) -> None:
        assert (
            OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1
            in _REGISTERED_SOURCES_V0
        )
        assert SOURCE_ID == OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1


class TestNegativeEligibility:
    @pytest.mark.parametrize(
        "inst,expected",
        [
            (_live_inst("BTC"), OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value),
            (
                {**_live_inst("ETH"), "instType": "SPOT"},
                OkxLifecycleSourceErrorCode.NON_LINEAR_USDT_SWAP.value,
            ),
            (
                {**_live_inst("ETH"), "settleCcy": "ETH"},
                OkxLifecycleSourceErrorCode.NON_LINEAR_USDT_SWAP.value,
            ),
            (
                {**_live_inst("ETH"), "state": "suspend"},
                OkxLifecycleSourceErrorCode.NON_LIVE_STATE_BLOCKED.value,
            ),
            (
                {**_live_inst("ETH"), "listTime": ""},
                OkxLifecycleSourceErrorCode.MISSING_LIST_TIME.value,
            ),
        ],
    )
    def test_fail_closed_exclusions(self, inst: dict[str, str], expected: str) -> None:
        result = evaluate_okx_instrument_eligibility_v1(inst)
        assert not result.eligible
        assert expected in result.error_codes

    def test_bitcoin_alias_blocked(self) -> None:
        assert is_forbidden_okx_instrument_token("XBT-USDT-SWAP", "XBT")


class TestDeterministicSelection:
    def test_selects_at_least_five_non_bitcoin_instruments(self) -> None:
        instruments = [
            _live_inst("BTC"),
            _live_inst("ETH"),
            _live_inst("SOL"),
            _live_inst("ADA"),
            _live_inst("DOT"),
            _live_inst("LINK"),
            _live_inst("AVAX"),
        ]
        selected, exclusions = select_eligible_okx_instruments_v1(instruments)
        assert len(selected) >= MIN_ELIGIBLE_INSTRUMENT_COUNT
        assert OkxLifecycleSourceErrorCode.BITCOIN_INSTRUMENT_BLOCKED.value in exclusions
        assert all("btc" not in item.inst_id.lower() for item in selected)

    def test_selection_is_deterministic_by_instrument_id(self) -> None:
        instruments = [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")]
        first, _ = select_eligible_okx_instruments_v1(instruments)
        second, _ = select_eligible_okx_instruments_v1(list(reversed(instruments)))
        assert [item.inst_id for item in first] == [item.inst_id for item in second]


class TestLifecycleAssembly:
    def test_builds_registry_snapshot_from_production_source(self) -> None:
        instruments = [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")]
        snapshot = build_okx_lifecycle_source_snapshot_v1(
            instruments,
            retrieval_timestamp_utc="2026-07-03T03:30:00Z",
            source_snapshot_ref="okx_public_instruments_swap:test",
        )
        observations = build_lifecycle_source_observations_v1(snapshot)
        assembly = assemble_registry_snapshot_v1(
            observations,
            generated_at="2026-07-03T03:30:00Z",
            venue_scope=("okx",),
            config_digest="d" * 64,
            implementation_digest="e" * 64,
            registered_sources=frozenset({SOURCE_ID}),
            approved_snapshot_digests=frozenset({snapshot.raw_snapshot_digest}),
        )
        assert assembly.success
        assert assembly.snapshot is not None
        assert len(assembly.snapshot.intervals) >= MIN_ELIGIBLE_INSTRUMENT_COUNT

    def test_is_okx_linear_usdt_perpetual_positive(self) -> None:
        assert is_okx_linear_usdt_perpetual(_live_inst("ETH"))
