"""Focused owner tests for Momentum V2 vol-scaled offline signal implementation."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import pytest

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_research_program_v1 import (
    load_and_validate_repo_program,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_development_evaluation_entry_point_v1 import (
    load_and_validate_repo_entry_point,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_hypothesis_preregistration_v1 import (
    load_and_validate_repo_contract,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1 import (
    BASELINE_ID,
    DEFAULT_LOOKBACK_PERIOD,
    DEFAULT_VOL_SCALED_ENTRY_Z,
    DEFAULT_VOL_SCALED_EXIT_Z,
    FEE_BPS_PER_SIDE,
    HYPOTHESIS_ID,
    SHORT_ENTRY_FORBIDDEN,
    SIGNAL_ENTRY_LONG,
    SIGNAL_EXIT,
    SIGNAL_FORMULA_VERSION,
    SIGNAL_NONE,
    SLIPPAGE_BPS_PER_SIDE,
    STRATEGY_IDENTITY,
    canonical_round_trip_cost_bps_v1,
    compute_baseline_raw_entry_exit_event_v1,
    compute_entry_exit_event_v1,
    compute_raw_simple_return_v1,
    compute_trailing_realized_vol_v1,
    compute_vol_scaled_momentum_v1,
    is_eligible_universe_instrument_v1,
    validate_frozen_parameters_v1,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_strategy_implementation_binding_v1 import (
    REQUIRED_DIGEST,
    load_and_validate_repo_binding,
)

REPO = Path(__file__).resolve().parents[2]
SIGNAL_FILE = (
    REPO / "src/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_signal_v1.py"
)
NEAR_DUP = (
    REPO / "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "near_duplicate_gate_v1.json"
)
SELECTION = (
    REPO / "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
    "operator_selection_record_v1.json"
)
FORBIDDEN_IMPORT_ROOTS = (
    "src.runtime",
    "src.execution",
    "src.scheduler",
    "src.trading.master_v2",
    "src.risk",
    "requests",
    "urllib",
    "httpx",
    "aiohttp",
)
RETIRED = ("trend_following/v1", "bollinger_bands/v1", "momentum_1h/v1")


def _closes_trend(
    start: float = 100.0, n: int = 60, step: float = 1.01, noise: float = 0.004
) -> tuple[float, ...]:
    """Synthetic path with non-zero return variance (constant step alone => vol=0)."""
    values = [start]
    for i in range(n - 1):
        # alternate noise so trailing realized vol is strictly positive
        factor = step * (1.0 + noise if i % 2 == 0 else 1.0 - noise)
        values.append(values[-1] * factor)
    return tuple(values)


def _closes_flat_then_spike(n: int = 60) -> tuple[float, ...]:
    values = [100.0]
    # mild noisy flat then spike (keeps vol > 0 throughout)
    for i in range(n - 6):
        factor = 1.0 + (0.002 if i % 2 == 0 else -0.001)
        values.append(values[-1] * factor)
    cur = values[-1]
    for j in range(5):
        cur *= 1.05 * (1.0 + (0.001 if j % 2 == 0 else -0.0005))
        values.append(cur)
    return tuple(values)


def test_selection_near_duplicate_and_bindings() -> None:
    assert HYPOTHESIS_ID.endswith("NON_BITCOIN_PERPETUALS_V1")
    assert STRATEGY_IDENTITY == "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1"
    near = json.loads(NEAR_DUP.read_text(encoding="utf-8"))
    assert near["verdict"] == "MATERIALLY_DISTINCT"
    assert near["implementation_eligible"] is True
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    assert sel["selection_authorized"] is True
    assert sel["development_evaluation_authorized"] is False
    assert sel["development_run_slot_available"] is False
    assert sel["development_run_slot_consumed"] is True
    binding = load_and_validate_repo_binding(REPO)
    assert binding["valid"] is True
    assert binding["run_slot_consumed"] is True
    assert binding["development_run_slot_available"] is False
    assert binding["development_evaluation_executed"] is True
    assert binding["frozen_digest"] == REQUIRED_DIGEST
    entry = load_and_validate_repo_entry_point(REPO)
    assert entry["development_evaluation_authorized"] is True
    assert entry["development_run_slot_available"] is False
    assert entry["development_run_slot_consumed"] is True
    backlog = load_and_validate_repo_backlog(REPO)
    assert backlog["valid"] is True
    assert backlog["status"] == "DEVELOPMENT_FAIL_SLOT_CONSUMED"
    program = load_and_validate_repo_program(REPO)
    assert program["implementation_authorized"] is True
    assert program["development_evaluation_executed"] is True
    contract = load_and_validate_repo_contract(REPO)
    assert contract["implementation_authorized"] is False  # frozen measurement SSOT
    assert contract["development_run_count"] == 0
    summary = json.loads(
        (
            REPO
            / "docs/evidence/evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1/summary.json"
        ).read_text(encoding="utf-8")
    )
    assert summary["status"] == "DEVELOPMENT_FAIL"
    assert summary["economic_validity"] == "FAIL"
    assert summary["run_slot_consumed"] is True
    assert summary["development_run_count"] == 1


def test_frozen_signal_equation_and_vol_scaling() -> None:
    assert SIGNAL_FORMULA_VERSION == "vol_scaled_raw_return_over_trailing_realized_vol_v1"
    assert DEFAULT_LOOKBACK_PERIOD == 20
    assert DEFAULT_VOL_SCALED_ENTRY_Z == 1.0
    assert DEFAULT_VOL_SCALED_EXIT_Z == 0.0
    assert SHORT_ENTRY_FORBIDDEN is True
    assert BASELINE_ID == "FROZEN_RAW_RETURN_MOMENTUM_1H_ENTRY_EXIT_EVENT_V1"
    assert validate_frozen_parameters_v1(
        lookback_period=20, signal_lag_bars=1, entry_z=1.0, exit_z=0.0
    )
    assert (
        validate_frozen_parameters_v1(
            lookback_period=24, signal_lag_bars=1, entry_z=1.0, exit_z=0.0
        )
        is False
    )
    closes = _closes_trend(n=50, step=1.02)
    epoch = 40
    packed = compute_vol_scaled_momentum_v1(closes, epoch_index=epoch)
    assert packed is not None
    raw, vol, score = packed
    assert vol > 0.0
    assert score == pytest.approx(raw / vol)
    raw2 = compute_raw_simple_return_v1(
        closes, lookback_period=20, signal_lag_bars=1, epoch_index=epoch
    )
    vol2 = compute_trailing_realized_vol_v1(
        closes, lookback_period=20, signal_lag_bars=1, epoch_index=epoch
    )
    assert raw2 == pytest.approx(raw)
    assert vol2 == pytest.approx(vol)


def test_zero_vol_and_non_finite_fail_closed() -> None:
    flat = tuple([100.0] * 40)
    assert (
        compute_trailing_realized_vol_v1(
            flat, lookback_period=20, signal_lag_bars=1, epoch_index=30
        )
        is None
    )
    assert compute_vol_scaled_momentum_v1(flat, epoch_index=30) is None
    bad = list(_closes_trend(n=40))
    bad[25] = float("nan")
    assert (
        compute_entry_exit_event_v1(
            bad, instrument_id="okx:linear_perpetual:ETH-USDT", epoch_index=30
        )
        is None
    )


def test_pit_lag_and_warmup() -> None:
    closes = _closes_trend(n=25, step=1.01)
    # insufficient warmup with lag
    assert compute_vol_scaled_momentum_v1(closes, epoch_index=19) is None
    ok = compute_vol_scaled_momentum_v1(closes, epoch_index=21)
    assert ok is not None


def test_universe_btc_spot_restriction() -> None:
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USDT") is True
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:BTC-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:spot:ETH-USDT") is False
    assert is_eligible_universe_instrument_v1("okx:linear_perpetual:ETH-USD") is False
    obs = compute_entry_exit_event_v1(
        _closes_trend(),
        instrument_id="okx:linear_perpetual:BTC-USDT",
        epoch_index=40,
    )
    assert obs is None


def test_long_only_exit_cannot_create_short_entry() -> None:
    # Construct path that should emit exit without short semantics.
    # Rising then falling through exit_z=0.
    ups = list(_closes_trend(n=45, step=1.03))
    # append decline
    cur = ups[-1]
    for _ in range(20):
        cur *= 0.97
        ups.append(cur)
    closes = tuple(ups)
    # scan for any signals
    seen = set()
    for epoch in range(25, len(closes)):
        obs = compute_entry_exit_event_v1(
            closes,
            instrument_id="okx:linear_perpetual:ETH-USDT",
            epoch_index=epoch,
        )
        if obs is None:
            continue
        seen.add(obs.signal)
        assert obs.signal in (SIGNAL_NONE, SIGNAL_ENTRY_LONG, SIGNAL_EXIT)
        assert obs.signal != -2
    assert SIGNAL_ENTRY_LONG in seen or SIGNAL_EXIT in seen or SIGNAL_NONE in seen
    # Exit value is -1 but SHORT_ENTRY_FORBIDDEN remains true (event contract).
    assert SHORT_ENTRY_FORBIDDEN is True
    assert SIGNAL_EXIT == -1


def test_deterministic_and_baseline_identity() -> None:
    closes = _closes_flat_then_spike()
    a = compute_entry_exit_event_v1(
        closes, instrument_id="okx:linear_perpetual:ETH-USDT", epoch_index=50
    )
    b = compute_entry_exit_event_v1(
        closes, instrument_id="okx:linear_perpetual:ETH-USDT", epoch_index=50
    )
    assert a == b
    baseline = compute_baseline_raw_entry_exit_event_v1(
        closes, instrument_id="okx:linear_perpetual:ETH-USDT", epoch_index=50
    )
    assert baseline in (SIGNAL_NONE, SIGNAL_ENTRY_LONG, SIGNAL_EXIT)
    # Material distinction: treatment uses vol scaling; raw baseline uses raw thresholds.
    # Even when both defined, treatment score identity differs from raw return.
    packed = compute_vol_scaled_momentum_v1(closes, epoch_index=50)
    raw = compute_raw_simple_return_v1(
        closes, lookback_period=20, signal_lag_bars=1, epoch_index=50
    )
    assert packed is not None and raw is not None
    assert packed[2] != pytest.approx(raw) or packed[1] != pytest.approx(1.0)


def test_realistic_cost_identity_binding() -> None:
    assert FEE_BPS_PER_SIDE == 10.0
    assert SLIPPAGE_BPS_PER_SIDE == 5.0
    assert canonical_round_trip_cost_bps_v1() == 30.0


def test_no_forbidden_authority_imports_and_registry_untouched() -> None:
    tree = ast.parse(SIGNAL_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for root in FORBIDDEN_IMPORT_ROOTS:
                    assert not alias.name.startswith(root), alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            for root in FORBIDDEN_IMPORT_ROOTS:
                assert not node.module.startswith(root), node.module
    momentum = (REPO / "src/strategies/momentum.py").read_text(encoding="utf-8")
    assert "vol_scaled_momentum" not in momentum
    assert "MOMENTUM_V2_VOLATILITY_SCALED" not in momentum


def test_retired_momentum_not_reopened_and_slot_consumed_once() -> None:
    near = json.loads(NEAR_DUP.read_text(encoding="utf-8"))
    ids = {c["comparator_id"] for c in near["comparators"]}
    for rid in RETIRED:
        assert rid in ids
    binding = json.loads(
        (
            REPO / "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_v1_"
            "strategy_implementation_binding_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert binding["run_slot_consumed"] is True
    assert binding["development_run_count"] == 1
    assert binding["development_evaluation_executed"] is True
    assert binding["development_evaluation_authorized"] is False
    assert binding["holdout_authorized"] is False
    csrhr = json.loads(
        (
            REPO
            / "config/research/cross_sectional_short_horizon_return_reversal_hypothesis_backlog_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert csrhr["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"


def test_fail_closed_second_evaluate_rejected_after_slot_consumed() -> None:
    import subprocess
    import sys

    script = (
        REPO / "scripts/research/"
        "run_evaluate_momentum_v2_volatility_scaled_own_instrument_continuation_development_v1.py"
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--mode",
            "evaluate",
            "--authorize-single-development-evaluation",
            HYPOTHESIS_ID,
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["evaluation_executed"] is False
    assert payload["runner_started"] is False
    assert payload["holdout_accessed"] is False
    assert "RETRY_OR_SLOT_REUSE_REJECTED" in str(payload.get("reason") or "")
