"""Regression: dynamic Fresh-C1 candle GETs must refresh across S6 polls."""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    DISPOSITION_MAX_CYCLES,
    run_current_productive_governed_continuous_cycle_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    EH_SEAM_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_LIMIT,
    GET_PATH,
    map_injected_candles_payload_to_current_productive_c1_observation_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
)
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import _candles
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    C1_A,
    C1_B,
    CURSOR_FLOOR,
    NATIVE_ID,
    ORIGIN_SHA,
    _FakeClock,
    _auth,
    _seed_cursor,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _eg_stub,
    _t2_hold,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD as S5_DISPOSITION_HOLD,
)

_PUBLIC_CANDLES = f"{GET_PATH}?instId={NATIVE_ID}&bar=1m&limit={GET_LIMIT}"
_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments?instType=SWAP"


class _FakeResp:
    def __init__(self, *, status: int, body: bytes, url: str) -> None:
        self.status = status
        self._body = body
        self.url = url

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _patch_sequential_opener(
    monkeypatch: pytest.MonkeyPatch, *, responses: deque[tuple[int, bytes, str]]
) -> None:
    opener = MagicMock()

    def _open(req: object, **kwargs: object) -> _FakeResp:
        del kwargs
        status, body, url = responses.popleft()
        return _FakeResp(status=status, body=body, url=url)

    opener.open.side_effect = _open

    def _build_opener(*_args: object, **_kwargs: object) -> MagicMock:
        return opener

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1"
        ".productive_read_only_get_transport_v1.build_opener",
        _build_opener,
    )


def _candle_body(*, event_time: float) -> bytes:
    payload = _candles(last_ts_ms=int(event_time * 1000))
    return json.dumps(payload).encode("utf-8")


def _mark_body() -> bytes:
    payload = okx_public_mark_price_payload_v1(native_id=NATIVE_ID, mark_px=3500.0)
    return json.dumps(payload).encode("utf-8")


def test_dynamic_candle_get_refreshes_same_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = _PUBLIC_CANDLES
    url = f"https://{AUTHORIZED_HOST}{endpoint}"
    t0 = 1789668000.0
    t1 = 1789668060.0
    responses: deque[tuple[int, bytes, str]] = deque(
        [
            (200, _candle_body(event_time=t0), url),
            (200, _candle_body(event_time=t1), url),
        ]
    )
    _patch_sequential_opener(monkeypatch, responses=responses)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    first = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="poll-0",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    second = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="poll-1",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    assert transport.request_count == 2
    assert first.body_sha256 != second.body_sha256
    mapped0 = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=EH_SEAM_OWNER_GO,
        candles_payload=first.payload,
        native_id=NATIVE_ID,
    )
    mapped1 = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=EH_SEAM_OWNER_GO,
        candles_payload=second.payload,
        native_id=NATIVE_ID,
    )
    assert mapped0.observation is not None
    assert mapped1.observation is not None
    assert mapped0.observation.venue_event_time == t0
    assert mapped1.observation.venue_event_time == t1
    assert mapped1.observation.venue_event_time > mapped0.observation.venue_event_time


def test_cacheable_snapshot_still_hits_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    endpoint = _PUBLIC_INSTRUMENTS
    url = f"https://{AUTHORIZED_HOST}{endpoint}"
    body = json.dumps({"code": "0", "data": []}).encode("utf-8")
    responses: deque[tuple[int, bytes, str]] = deque([(200, body, url)])
    _patch_sequential_opener(monkeypatch, responses=responses)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    first = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="snap-0",
    )
    second = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="snap-1",
    )
    assert transport.request_count == 1
    assert first.body_sha256 == second.body_sha256


def test_live_fresh_c1_two_polls_observe_strictly_newer_c1(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cursor = _seed_cursor(tmp_path / "lane", event_time=CURSOR_FLOOR)
    candle_url = f"https://{AUTHORIZED_HOST}{_PUBLIC_CANDLES}"
    mark_url = f"https://{AUTHORIZED_HOST}{ENDPOINT_PUBLIC_MARK_PRICE}?instId={NATIVE_ID}"
    responses: deque[tuple[int, bytes, str]] = deque(
        [
            (200, _candle_body(event_time=C1_A), candle_url),
            (200, _mark_body(), mark_url),
            (200, _candle_body(event_time=C1_B), candle_url),
            (200, _mark_body(), mark_url),
        ]
    )
    _patch_sequential_opener(monkeypatch, responses=responses)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=8)
    source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id="dynamic-cache-repair",
        native_id=NATIVE_ID,
        transport=transport,
    )
    obs0 = source.poll()
    obs1 = source.poll()
    assert obs0 is not None and obs1 is not None
    m0 = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=EH_SEAM_OWNER_GO,
        candles_payload=obs0.candles_payload,
        native_id=NATIVE_ID,
    )
    m1 = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=EH_SEAM_OWNER_GO,
        candles_payload=obs1.candles_payload,
        native_id=NATIVE_ID,
    )
    assert m0.observation is not None and m1.observation is not None
    assert m0.observation.venue_event_time == C1_A
    assert m1.observation.venue_event_time == C1_B
    assert m1.observation.venue_event_time > m0.observation.venue_event_time


def _s5_hold_liveness_stub(**_kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(
        disposition=S5_DISPOSITION_HOLD,
        reason_code="HOLD",
        permit_created=False,
        post_count=0,
    )


def test_orchestrator_reaches_second_s5_cycle_with_live_fresh_c1_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cursor = _seed_cursor(tmp_path / "lane", event_time=CURSOR_FLOOR)
    candle_url = f"https://{AUTHORIZED_HOST}{_PUBLIC_CANDLES}"
    mark_url = f"https://{AUTHORIZED_HOST}{ENDPOINT_PUBLIC_MARK_PRICE}?instId={NATIVE_ID}"
    responses: deque[tuple[int, bytes, str]] = deque(
        [
            (200, _candle_body(event_time=C1_A), candle_url),
            (200, _mark_body(), mark_url),
            (200, _candle_body(event_time=C1_B), candle_url),
            (200, _mark_body(), mark_url),
        ]
    )
    _patch_sequential_opener(monkeypatch, responses=responses)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=8)
    obs_source = LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id="s6-orchestrator-repair",
        native_id=NATIVE_ID,
        transport=transport,
    )
    clock = _FakeClock()
    result = run_current_productive_governed_continuous_cycle_run_v1(
        authorization=_auth(max_cycles_per_run=2, wait_interval_seconds=0.001),
        origin_main_sha=ORIGIN_SHA,
        cursor_store_root=cursor,
        lock_root=tmp_path / "lock",
        evidence_root=tmp_path / "orch_evidence",
        observation_source=obs_source,
        execute_network=False,
        perform_get=False,
        eg_cycle_dispatch=_eg_stub,
        t2_cycle_dispatch=_t2_hold,
        s5_runner=_s5_hold_liveness_stub,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
    )
    assert result.disposition == DISPOSITION_MAX_CYCLES
    assert result.cycles_completed == 2
    assert result.s5_invoke_count == 2
    assert result.cycle_records[0].c1_venue_event_time == C1_A
    assert result.cycle_records[1].c1_venue_event_time == C1_B
    assert result.post_count == 0


def test_permanent_cache_would_fail_dynamic_regression_without_repair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Documents old semantics: cacheable reuse freezes the first candle payload."""
    endpoint = _PUBLIC_CANDLES
    url = f"https://{AUTHORIZED_HOST}{endpoint}"
    t0 = 1789668000.0
    t1 = 1789668060.0
    responses: deque[tuple[int, bytes, str]] = deque(
        [
            (200, _candle_body(event_time=t0), url),
            (200, _candle_body(event_time=t1), url),
        ]
    )
    _patch_sequential_opener(monkeypatch, responses=responses)
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    first = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="legacy-0",
        get_cache_policy=GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    )
    second = transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="legacy-1",
        get_cache_policy=GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    )
    assert transport.request_count == 1
    assert first.body_sha256 == second.body_sha256
    mapped = map_injected_candles_payload_to_current_productive_c1_observation_v1(
        owner_go=EH_SEAM_OWNER_GO,
        candles_payload=second.payload,
        native_id=NATIVE_ID,
    )
    assert mapped.observation is not None
    assert mapped.observation.venue_event_time == t0
