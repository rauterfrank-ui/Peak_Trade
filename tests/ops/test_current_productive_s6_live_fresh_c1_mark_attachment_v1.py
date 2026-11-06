"""ROOT_WIRING_01: LiveFreshC1 poll attaches canonical public mark-price payloads."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    ProductiveCanonicalPriceProvenanceError,
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_PATH,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops.test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1 import (
    NATIVE_ID,
)
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _seed_cursor,
)

CANDLES = {
    "code": "0",
    "msg": "",
    "data": [["1700000000000", "1", "2", "1", "1.5", "10", "100", "USDT", "1"]],
}


@dataclass
class _MockGetResult:
    get_performed: bool
    payload: dict[str, Any] | None


class _RoutingMockTransport:
    def __init__(self, routes: dict[str, dict[str, Any] | None]) -> None:
        self._routes = routes
        self.calls: list[str] = []
        self.call_policies: list[str] = []
        self.call_pretrade_ids: list[str] = []

    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
        get_cache_policy: str = "",
    ) -> _MockGetResult:
        assert auth_required is False
        self.calls.append(endpoint)
        self.call_policies.append(get_cache_policy)
        self.call_pretrade_ids.append(pretrade_decision_id)
        path = endpoint.split("?", 1)[0]
        payload = self._routes.get(path)
        if payload is None and "?" in endpoint:
            payload = self._routes.get(endpoint)
        return _MockGetResult(get_performed=payload is not None, payload=payload)


def _mark_routes(
    native_id: str = NATIVE_ID, *, mark_px: float = 3500.0, index_px: float = 3490.0
) -> dict[str, dict[str, Any] | None]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )

    return {
        GET_PATH: CANDLES,
        ENDPOINT_PUBLIC_MARK_PRICE: okx_public_mark_price_payload_v1(
            native_id=native_id,
            mark_px=mark_px,
            index_px=index_px,
        ),
    }


def test_poll_attaches_mark_price_payload_cold_lane(tmp_path: Path) -> None:
    transport = _RoutingMockTransport(_mark_routes())
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=tmp_path / "cold_lane",
        evidence_root=tmp_path / "evidence",
        run_id="rw01-cold",
        native_id=NATIVE_ID,
        transport=transport,
    )
    obs = source.poll()
    assert obs is not None
    assert obs.mark_price_payload is not None
    prov = build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
        mark_price_payload=obs.mark_price_payload,
        venue_native_id=NATIVE_ID,
        index_from_index_tickers=obs.index_tickers_payload,
    )
    assert prov.venue_native_id == NATIVE_ID
    assert ENDPOINT_PUBLIC_MARK_PRICE in transport.calls[1]


def test_poll_with_seeded_cursor_attaches_mark(tmp_path: Path) -> None:
    cursor = _seed_cursor(tmp_path / "lane", event_time=0.0)
    transport = _RoutingMockTransport(_mark_routes())
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id="rw01-warm",
        native_id=NATIVE_ID,
        transport=transport,
    )
    obs = source.poll()
    assert obs is not None
    assert obs.mark_price_payload is not None


def test_missing_mark_payload_fail_closed(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )

    transport = _RoutingMockTransport({GET_PATH: CANDLES, ENDPOINT_PUBLIC_MARK_PRICE: None})
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=tmp_path / "cold_lane",
        evidence_root=tmp_path / "evidence",
        run_id="rw01-no-mark",
        native_id=NATIVE_ID,
        transport=transport,
    )
    assert source.poll() is None


def test_malformed_mark_payload_fail_closed(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )

    transport = _RoutingMockTransport(
        {
            GET_PATH: CANDLES,
            ENDPOINT_PUBLIC_MARK_PRICE: {"code": "0", "data": []},
        }
    )
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=tmp_path / "cold_lane",
        evidence_root=tmp_path / "evidence",
        run_id="rw01-bad-mark",
        native_id=NATIVE_ID,
        transport=transport,
    )
    assert source.poll() is None


def test_instrument_mismatch_mark_fail_closed(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )

    wrong_mark = okx_public_mark_price_payload_v1(native_id="OTHER-SWAP", mark_px=1.0, index_px=1.0)
    transport = _RoutingMockTransport({GET_PATH: CANDLES, ENDPOINT_PUBLIC_MARK_PRICE: wrong_mark})
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=tmp_path / "cold_lane",
        evidence_root=tmp_path / "evidence",
        run_id="rw01-mismatch",
        native_id=NATIVE_ID,
        transport=transport,
    )
    assert source.poll() is None


def _mark_call_indices(transport: _RoutingMockTransport) -> list[int]:
    return [
        i
        for i, endpoint in enumerate(transport.calls)
        if endpoint.split("?", 1)[0] == ENDPOINT_PUBLIC_MARK_PRICE
    ]


def test_two_polls_mark_get_uses_dynamic_refresh_required(tmp_path: Path) -> None:
    cursor = _seed_cursor(tmp_path / "lane", event_time=0.0)
    transport = _RoutingMockTransport(_mark_routes())
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id="rw01-mark-dynamic",
        native_id=NATIVE_ID,
        transport=transport,
    )
    assert source.poll() is not None
    assert source.poll() is not None
    mark_indices = _mark_call_indices(transport)
    assert len(mark_indices) >= 2
    for idx in mark_indices:
        assert transport.call_policies[idx] == GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
    candle_indices = [i for i, ep in enumerate(transport.calls) if ep.split("?", 1)[0] == GET_PATH]
    assert len(candle_indices) >= 2
    for idx in candle_indices:
        assert transport.call_policies[idx] == GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED
    mark_pretrade = [transport.call_pretrade_ids[i] for i in mark_indices]
    assert len(set(mark_pretrade)) == len(mark_pretrade)


def test_no_synthetic_mark_without_public_get(tmp_path: Path) -> None:
    """Poll must not invent mark when public mark GET is absent."""
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_PATH,
    )

    transport = _RoutingMockTransport({GET_PATH: CANDLES})
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=tmp_path / "cold_lane",
        evidence_root=tmp_path / "evidence",
        run_id="rw01-no-synthetic",
        native_id=NATIVE_ID,
        transport=transport,
    )
    assert source.poll() is None
