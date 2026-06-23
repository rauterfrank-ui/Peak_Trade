"""Static contract: bounded testnet market input admission wiring v0."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    TestnetCompletionPathMarketInputV0,
    build_testnet_bounded_adapter_completion_path_wiring_section,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
    validate_testnet_completion_path_market_input,
)
from src.ops.bounded_testnet_market_input_admission_wiring_v0 import (
    BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER,
    CANONICAL_MARKET_INPUT_PRODUCER,
    CANONICAL_MARKET_OBSERVATION_OWNER,
    REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
    REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
    BoundedTestnetFuturesMarketObservationV0,
    BoundedTestnetFuturesMarketPriceTickObservationV0,
    build_testnet_completion_path_market_input_from_observation,
    resolve_testnet_completion_path_market_input,
    static_producer_owner_flags,
    validate_bounded_testnet_futures_market_observation,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesMarketType,
)
from trading.master_v2.double_play_state import ScopeEvent
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    OfflineDoublePlayScenarioTickV0,
    SYNTHETIC_FUTURES_INSTRUMENT,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SCRIPT = REPO_ROOT / "scripts" / "ops" / "run_testnet_bounded_observation_adapter_v0.py"
PRODUCER_OWNER = REPO_ROOT / "src" / "ops" / "bounded_testnet_market_input_admission_wiring_v0.py"
WIRING_OWNER = REPO_ROOT / "src" / "ops" / "bounded_master_v2_testnet_completion_path_wiring_v0.py"
SELECTOR = REPO_ROOT / "scripts" / "ops" / "ci_test_selection_v1.py"

MARKET_INPUT_ADMISSION_FILES = (
    "src/ops/bounded_testnet_market_input_admission_wiring_v0.py",
    "src/ops/bounded_master_v2_testnet_completion_path_wiring_v0.py",
    "scripts/ops/run_testnet_bounded_observation_adapter_v0.py",
    "tests/ops/test_bounded_testnet_market_input_admission_wiring_contract_v0.py",
    "scripts/ops/ci_test_selection_v1.py",
)


def _load_adapter():
    spec = importlib.util.spec_from_file_location(
        "run_testnet_bounded_observation_adapter_v0", ADAPTER_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _valid_price_tick(
    *,
    tick_index: int = 0,
    timestamp_ms: int = 1_700_000_000_000,
    mark_price: float = 2500.0,
    sequence: int = 1,
) -> BoundedTestnetFuturesMarketPriceTickObservationV0:
    return BoundedTestnetFuturesMarketPriceTickObservationV0(
        tick_index=tick_index,
        timestamp_ms=timestamp_ms,
        mark_price=mark_price,
        sequence=sequence,
    )


def _valid_observation(
    *,
    price_ticks: tuple[BoundedTestnetFuturesMarketPriceTickObservationV0, ...] | None = None,
    **overrides: object,
) -> BoundedTestnetFuturesMarketObservationV0:
    ticks = price_ticks or (_valid_price_tick(),)
    base = {
        "selected_future_id": REPO_GROUNDED_ETH_PERP_SELECTED_FUTURE_ID,
        "venue_symbol": REPO_GROUNDED_ETH_PERP_VENUE_SYMBOL,
        "exchange": "kraken_futures",
        "market_type": FuturesMarketType.PERPETUAL,
        "source_run_id": "testnet-market-input-run",
        "dataset_id": "testnet-bounded-observation-v0",
        "price_source": "testnet_bounded_observation",
        "freshness_state": FuturesFreshnessState.FRESH,
        "observed_at_utc": "2026-06-23T00:00:00Z",
        "price_timestamp_utc": "2026-06-23T00:00:00Z",
        "mark_price_available": True,
        "last_price_available": True,
        "index_price_available": True,
        "price_ticks": ticks,
    }
    base.update(overrides)
    return BoundedTestnetFuturesMarketObservationV0(**base)


def test_canonical_producer_owner_paths_present() -> None:
    assert PRODUCER_OWNER.is_file()
    assert WIRING_OWNER.is_file()
    assert ADAPTER_SCRIPT.is_file()
    flags = static_producer_owner_flags()
    assert flags["bounded_testnet_market_input_admission_wiring_owner"] == (
        BOUNDED_TESTNET_MARKET_INPUT_ADMISSION_WIRING_OWNER
    )
    assert flags["canonical_market_observation_owner"] == CANONICAL_MARKET_OBSERVATION_OWNER
    assert flags["canonical_market_input_producer"] == CANONICAL_MARKET_INPUT_PRODUCER
    assert flags["repo_grounded_eth_perp_selected_future_id"] == SYNTHETIC_FUTURES_INSTRUMENT
    assert flags["repo_grounded_eth_perp_venue_symbol"] == "PF_ETHUSD"


def test_producer_maps_valid_observation_to_market_input() -> None:
    observation = _valid_observation()
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is True
    assert result.market_input is not None
    assert result.market_input.selected_future_id == "ETH-PERP"
    assert len(result.market_input.ticks) == 1
    assert result.market_input.ticks[0].scope_event is ScopeEvent.NOOP
    assert validate_testnet_completion_path_market_input(result.market_input) == []


def test_stale_observation_fail_closed() -> None:
    observation = _valid_observation(freshness_state=FuturesFreshnessState.STALE)
    reasons = validate_bounded_testnet_futures_market_observation(observation)
    assert reasons
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_missing_provenance_fail_closed() -> None:
    observation = _valid_observation(dataset_id="")
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_btc_instrument_rejected() -> None:
    observation = _valid_observation(
        selected_future_id="XBT-PERP",
        venue_symbol="PF_XBTUSD",
    )
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_venue_symbol_mismatch_fail_closed() -> None:
    observation = _valid_observation(venue_symbol="PF_SOLUSD")
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_non_finite_price_fail_closed() -> None:
    observation = _valid_observation(
        price_ticks=(_valid_price_tick(mark_price=float("nan")),),
    )
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_synthetic_offline_fixture_rejected() -> None:
    observation = _valid_observation(synthetic_offline_fixture=True)
    result = build_testnet_completion_path_market_input_from_observation(observation)
    assert result.producer_pass is False
    assert result.market_input is None


def test_missing_observation_stays_fail_closed() -> None:
    assert resolve_testnet_completion_path_market_input(None) is None
    result = evaluate_bounded_master_v2_testnet_completion_path_wiring(None)
    assert result.admission_pass is False
    assert result.missing_testnet_market_input_fails_closed is True


def test_adapter_forwards_validated_market_input_without_fixture_fallback() -> None:
    mod = _load_adapter()
    observation = _valid_observation(
        price_ticks=(
            _valid_price_tick(tick_index=0, timestamp_ms=1_700_000_000_000, sequence=1),
            _valid_price_tick(
                tick_index=1,
                timestamp_ms=1_700_000_060_000,
                mark_price=2501.0,
                sequence=2,
            ),
        )
    )
    plan = mod.build_plan(
        mode="plan-only",
        staging_root=Path("/tmp/peak_trade_testnet_market_input_plan"),
        archive_root=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
        repo_root=REPO_ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="market_input_plan_test",
        market_observation=observation,
    )
    wiring = plan.to_dict()["completion_path_wiring"]
    assert wiring["market_input_bound"] is True
    assert wiring["machine_summary"]["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is False
    assert wiring["machine_summary"]["TESTNET_EXECUTES_CANONICAL_MASTER_V2"] is False


def test_adapter_without_observation_still_fail_closed() -> None:
    mod = _load_adapter()
    plan = mod.build_plan(
        mode="plan-only",
        staging_root=Path("/tmp/peak_trade_testnet_market_input_missing"),
        archive_root=Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
        ),
        repo_root=REPO_ROOT,
        duration_minutes=10,
        max_steps=120,
        step_interval_seconds=0.0,
        run_id="market_input_missing_test",
    )
    wiring = plan.to_dict()["completion_path_wiring"]
    assert wiring["market_input_bound"] is False
    assert wiring["admission_pass"] is False
    assert wiring["machine_summary"]["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is True


def test_wiring_section_accepts_forwarded_market_input() -> None:
    market_input = TestnetCompletionPathMarketInputV0(
        selected_future_id="ETH-PERP",
        ticks=(
            OfflineDoublePlayScenarioTickV0(
                tick_index=0,
                timestamp_ms=1_700_000_000_000,
                price=2500.0,
                scope_event=ScopeEvent.NOOP,
            ),
        ),
        source_run_id="section-test",
    )
    section = build_testnet_bounded_adapter_completion_path_wiring_section(
        run_id="section-test",
        mode="plan-only",
        market_input=market_input,
    )
    assert section["market_input_bound"] is True
    assert section["machine_summary"]["MISSING_TESTNET_MARKET_INPUT_FAILS_CLOSED"] is False


def test_zero_order_boundary_preserved_for_validated_market_input() -> None:
    observation = _valid_observation()
    admission = build_testnet_completion_path_market_input_from_observation(observation)
    assert admission.market_input is not None
    wiring = evaluate_bounded_master_v2_testnet_completion_path_wiring(admission.market_input)
    assert wiring.orders_total == 0
    assert wiring.cancels_total == 0
    assert wiring.fills_total == 0
    assert wiring.positions_opened_total == 0


def _run_selector(*files: str) -> dict[str, str]:
    cmd = [sys.executable, str(SELECTOR), "--event-name", "pull_request", "--files", *files]
    out = subprocess.check_output(cmd, text=True, cwd=REPO_ROOT)
    result: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.partition("=")
        result[key] = value
    return result


def test_ci_selector_market_input_admission_five_file_diff_focused() -> None:
    sel = _run_selector(*MARKET_INPUT_ADMISSION_FILES)
    assert sel["test_selection_mode"] == "FOCUSED"
    assert sel["test_selection_reason"] == "bounded_testnet_market_input_admission_wiring_focused"
    assert sel["tests_execute_full"] == "false"
    assert sel["tests_execute_focused"] == "true"
    targets = sorted(sel.get("focused_pytest_targets", "").split())
    assert "tests/ops/test_bounded_testnet_market_input_admission_wiring_contract_v0.py" in targets
    assert all("::test_" in target for target in targets if target.endswith(".py") is False)
    assert len(targets) >= 8


def test_ci_selector_market_input_admission_foreign_path_escalates_full() -> None:
    sel = _run_selector(
        *MARKET_INPUT_ADMISSION_FILES,
        "src/trading/master_v2/double_play_state.py",
    )
    assert sel["test_selection_mode"] == "FULL"
    assert sel["tests_execute_full"] == "true"
