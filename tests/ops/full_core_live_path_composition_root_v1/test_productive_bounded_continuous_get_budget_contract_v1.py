"""Regression: Product shared-transport GET budget tracks S6 poll contract."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_get_budget_contract_v1 import (
    ANTI_HANG_POLL_ITERATION_MARGIN,
    FINITE_GET_BUDGET_SAFETY_MARGIN,
    PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS,
    PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL,
    PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS,
    compute_max_canonical_continuous_poll_iterations_v1,
    compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1,
    compute_worst_case_legitimate_shared_transport_charged_gets_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    HARD_CAP_MAX_CYCLES_PER_RUN,
    HARD_CAP_MAX_RUN_DURATION_SECONDS,
    RUNTIME_OWNER_GO,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)


def _canonical_product_auth(
    **overrides: object,
) -> CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    base = dict(
        continuous_owner_go=RUNTIME_OWNER_GO,
        native_id="APR-USDT-SWAP",
        bar="1m",
        expected_cursor_floor=0.0,
        max_cycles_per_run=HARD_CAP_MAX_CYCLES_PER_RUN,
        max_run_duration_seconds=HARD_CAP_MAX_RUN_DURATION_SECONDS,
        wait_interval_seconds=5.0,
        max_wait_for_next_c1_seconds=60.0,
        stall_seconds=60.0,
    )
    base.update(overrides)
    return CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(**base)


def test_canonical_poll_iterations_match_orchestrator_formula() -> None:
    assert (
        compute_max_canonical_continuous_poll_iterations_v1(
            max_run_duration_seconds=180.0,
            wait_interval_seconds=5.0,
            max_cycles_per_run=4,
        )
        == int(180 // 5) + 4 + ANTI_HANG_POLL_ITERATION_MARGIN
    )


def test_derived_budget_finite_and_above_legacy_32() -> None:
    budget = compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1(
        _canonical_product_auth()
    )
    assert budget > 32
    assert budget < 10_000


def test_derived_budget_covers_forensic_worst_case_53() -> None:
    budget = compute_worst_case_legitimate_shared_transport_charged_gets_v1(
        max_run_duration_seconds=180.0,
        wait_interval_seconds=5.0,
        max_cycles_per_run=4,
    )
    assert budget >= 53
    assert budget == (
        PRODUCTIVE_SHARED_TRANSPORT_G17_CHARGED_GETS
        + PRODUCTIVE_COLD_BOOTSTRAP_WORST_CASE_CHARGED_GETS
        + 48 * PRODUCTIVE_S6_DYNAMIC_CANDLE_GETS_PER_POLL
        + FINITE_GET_BUDGET_SAFETY_MARGIN
    )


def test_budget_scales_with_duration_and_cycles() -> None:
    short = compute_worst_case_legitimate_shared_transport_charged_gets_v1(
        max_run_duration_seconds=90.0,
        wait_interval_seconds=5.0,
        max_cycles_per_run=2,
    )
    long = compute_worst_case_legitimate_shared_transport_charged_gets_v1(
        max_run_duration_seconds=180.0,
        wait_interval_seconds=5.0,
        max_cycles_per_run=4,
    )
    assert long > short


def test_transport_raises_when_derived_budget_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    budget = compute_productive_policy_governed_live_c1_shared_transport_max_request_count_v1(
        _canonical_product_auth()
    )
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=budget)
    endpoint = f"https://{AUTHORIZED_HOST}/api/v5/market/candles?instId=X&bar=1m&limit=2"

    class _Resp:
        status = 200

        def read(self) -> bytes:
            return b'{"code":"0","data":[]}'

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1"
        ".productive_read_only_get_transport_v1.build_opener",
        lambda *_a, **_k: type("O", (), {"open": lambda _s, _r, **k: _Resp()})(),
    )

    for _ in range(budget):
        transport.get(
            endpoint=endpoint,
            auth_required=False,
            pretrade_decision_id="budget-proof",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
    with pytest.raises(FullCoreProductiveReadOnlyGetError, match="MAX_REQUEST_COUNT_EXCEEDED"):
        transport.get(
            endpoint=endpoint,
            auth_required=False,
            pretrade_decision_id="budget-proof-overflow",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )


def test_snapshot_cache_still_avoids_extra_request_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = FullCoreProductiveReadOnlyGetTransportV1(max_request_count=4)
    endpoint = f"https://{AUTHORIZED_HOST}/api/v5/public/instruments?instType=SWAP"

    class _Resp:
        status = 200

        def read(self) -> bytes:
            return b'{"code":"0","data":[]}'

        def __enter__(self) -> _Resp:
            return self

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1"
        ".productive_read_only_get_transport_v1.build_opener",
        lambda *_a, **_k: type("O", (), {"open": lambda _s, _r, **k: _Resp()})(),
    )
    transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="snap-0",
        get_cache_policy=GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    )
    transport.get(
        endpoint=endpoint,
        auth_required=False,
        pretrade_decision_id="snap-1",
        get_cache_policy=GET_CACHE_POLICY_CACHEABLE_SNAPSHOT,
    )
    assert transport.request_count == 1
