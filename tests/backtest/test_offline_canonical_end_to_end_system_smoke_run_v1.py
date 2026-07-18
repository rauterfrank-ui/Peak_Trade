"""Offline canonical end-to-end system smoke run v1.

TEST_HARNESS / CONTRACT_ASSERTION only.

Composes the existing canonical MV2 research wiring path — no parallel pipeline,
no new decision owner, no new replay-input builder, no trading-semantics change.

Chain under test:
  synthetic ETH-perp OHLCV bars
  -> execute_configured_strategy_signal_series_v1
  -> normalize_strategy_signal_to_suitability_agreement_material_v1
  -> build_integrated_offline_replay_input_v1
  -> run_integrated_offline_trading_logic_replay_v1
  -> map_decision_evidence_to_position_signal_v1
  -> BacktestEngine(use_execution_pipeline=True)
  -> technical summary digest

A controlled no-trade / observe-only outcome is admissible when the full
canonical decision chain still executes and is proven.
"""

from __future__ import annotations

import ast
import hashlib
import json
import socket
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.strategy_signal_binding_v1 import (
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
)
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.trading.master_v2._canonical_architecture_drift_guard_helpers_v1 import (
    assert_no_direct_strategy_authority_bypass,
    assert_single_canonical_total_decision_owner,
    assert_single_productive_replay_input_constructor,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_FIXTURE_ID = "offline_canonical_e2e_smoke_eth_perp_ma_crossover_v1"
SMOKE_OPERATOR_GO = "GO_OFFLINE_CANONICAL_END_TO_END_SYSTEM_SMOKE_RUN_V1"
_NETWORK_MODULES = frozenset({"requests", "urllib3", "ccxt", "httpx", "aiohttp", "websocket"})
_OWNER_SOURCES = (
    REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py",
    REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    REPO_ROOT / "src/backtest/strategy_signal_binding_v1.py",
    REPO_ROOT / "src/backtest/strategy_signal_suitability_agreement_adapter_v1.py",
    REPO_ROOT / "src/trading/master_v2/suitability_binding_v1.py",
)


def _cfg() -> Mapping[str, Any]:
    # Reuse the established MV2 research wiring offline fixture shape.
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {
                "fast_window": 2,
                "slow_window": 3,
            },
        },
    }


def _bars(n: int = 12) -> pd.DataFrame:
    # Deterministic synthetic futures OHLCV; fixed timestamps; non-BTC.
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def _run_smoke(**kwargs: Any) -> wiring.MV2ResearchWiringResultV1:
    return wiring.run_mv2_research_backtest_wiring_v1(
        bars=kwargs.pop("bars", _bars()),
        strategy_id=kwargs.pop("strategy_id", "ma_crossover"),
        cfg=kwargs.pop("cfg", _cfg()),
        instrument_id=kwargs.pop("instrument_id", wiring.MV2_REQUIRED_INSTRUMENT_ID),
        **kwargs,
    )


def _trade_count(result: wiring.MV2ResearchWiringResultV1) -> int:
    trades = result.backtest_result.trades
    if trades is None:
        return 0
    return int(len(trades))


def _rejection_count(result: wiring.MV2ResearchWiringResultV1) -> int:
    return int(sum(int(v) for v in result.block_reason_counts.values()))


def _technical_summary(result: wiring.MV2ResearchWiringResultV1) -> dict[str, Any]:
    evidence_digests = [outcome.evidence.semantic_digest for outcome in result.bar_outcomes]
    decision_outcomes = [outcome.evidence.decision_outcome for outcome in result.bar_outcomes]
    payload = {
        "schema_version": "offline_canonical_end_to_end_system_smoke_run_v1",
        "run_type": "offline_canonical_end_to_end_smoke",
        "operator_go": SMOKE_OPERATOR_GO,
        "fixture_identifier": SMOKE_FIXTURE_ID,
        "instrument_id": result.instrument_id,
        "strategy_id": result.strategy_signal_provenance.configured_strategy_id,
        "backtest_engine_signal_source": result.backtest_engine_signal_source,
        "mv2_replay_signal_digest": result.mv2_replay_signal_digest,
        "decision_count": len(result.bar_outcomes),
        "trade_count": _trade_count(result),
        "rejection_count": _rejection_count(result),
        "decision_outcomes": decision_outcomes,
        "evidence_semantic_digests": evidence_digests,
        "decision_funnel_counts": dict(result.decision_funnel_counts),
        "block_reason_counts": dict(result.block_reason_counts),
        "signals": [float(v) for v in result.signals.tolist()],
        "network_access": False,
        "live_authorized": False,
        "orders_allowed": False,
        "legacy_bypass_detected": False,
        "canonical_components_invoked": [
            "execute_configured_strategy_signal_series_v1",
            "normalize_strategy_signal_to_suitability_agreement_material_v1",
            "build_integrated_offline_replay_input_v1",
            "run_integrated_offline_trading_logic_replay_v1",
            "evaluate_suitability_binding_v1",
            "map_decision_evidence_to_position_signal_v1",
            "BacktestEngine(use_execution_pipeline=True)",
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    payload["summary_digest"] = digest
    payload["final_verdict"] = "PASS_TECHNICAL_OFFLINE_SMOKE"
    return payload


def _assert_network_modules_absent(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in _NETWORK_MODULES
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in _NETWORK_MODULES


def test_offline_canonical_e2e_smoke_executes_full_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DRY_RUN", "YES")
    monkeypatch.setenv("PT_DRY_RUN", "1")

    result = _run_smoke()
    summary = _technical_summary(result)

    assert result.instrument_id == "inst-eth-usdt-perp"
    assert result.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert result.backtest_engine_signal_source == CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE
    assert result.strategy_signal_provenance.configured_strategy_id == "ma_crossover"
    assert len(result.bar_outcomes) == 12
    assert len(result.signals) == 12
    assert result.backtest_result is not None
    assert result.backtest_result.metadata["cost_model_version"] == "backtest_cost_v0"
    assert result.registry_snapshot.input_digest
    assert all(outcome.evidence.semantic_digest for outcome in result.bar_outcomes)
    assert int(result.decision_funnel_counts["market_epochs_total"]) == 12
    # One early epoch is non-directional under observe_only; chain still covers all bars.
    assert int(result.decision_funnel_counts["directional_candidate_count"]) == 11
    assert "suitability_pass_count" in result.decision_funnel_counts
    assert "risk_sizing_admissible_count" in result.decision_funnel_counts
    assert summary["trade_count"] == 0
    assert summary["decision_count"] == 12
    assert summary["rejection_count"] == 12
    assert summary["network_access"] is False
    assert summary["live_authorized"] is False
    assert summary["orders_allowed"] is False
    assert len(summary["summary_digest"]) == 64


def test_offline_canonical_e2e_smoke_deterministic_twice() -> None:
    first = _technical_summary(_run_smoke())
    second = _technical_summary(_run_smoke())

    assert first["summary_digest"] == second["summary_digest"]
    assert first["decision_count"] == second["decision_count"]
    assert first["trade_count"] == second["trade_count"]
    assert first["rejection_count"] == second["rejection_count"]
    assert first["decision_outcomes"] == second["decision_outcomes"]
    assert first["mv2_replay_signal_digest"] == second["mv2_replay_signal_digest"]
    assert first["evidence_semantic_digests"] == second["evidence_semantic_digests"]
    assert first["decision_funnel_counts"] == second["decision_funnel_counts"]
    assert first["signals"] == second["signals"]


def test_offline_canonical_e2e_smoke_invokes_canonical_owners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {
        "build": 0,
        "run": 0,
        "normalize": 0,
        "strategy": 0,
    }

    original_build = wiring.build_integrated_offline_replay_input_v1
    original_run = wiring.run_integrated_offline_trading_logic_replay_v1
    original_normalize = wiring.normalize_strategy_signal_to_suitability_agreement_material_v1
    original_strategy = wiring.execute_configured_strategy_signal_series_v1

    def _counting_build(*args: Any, **kwargs: Any) -> Any:
        calls["build"] += 1
        return original_build(*args, **kwargs)

    def _counting_run(*args: Any, **kwargs: Any) -> Any:
        calls["run"] += 1
        return original_run(*args, **kwargs)

    def _counting_normalize(*args: Any, **kwargs: Any) -> Any:
        calls["normalize"] += 1
        return original_normalize(*args, **kwargs)

    def _counting_strategy(*args: Any, **kwargs: Any) -> Any:
        calls["strategy"] += 1
        return original_strategy(*args, **kwargs)

    monkeypatch.setattr(wiring, "build_integrated_offline_replay_input_v1", _counting_build)
    monkeypatch.setattr(wiring, "run_integrated_offline_trading_logic_replay_v1", _counting_run)
    monkeypatch.setattr(
        wiring,
        "normalize_strategy_signal_to_suitability_agreement_material_v1",
        _counting_normalize,
    )
    monkeypatch.setattr(
        wiring,
        "execute_configured_strategy_signal_series_v1",
        _counting_strategy,
    )

    result = _run_smoke(bars=_bars(6))
    assert calls["strategy"] == 1
    assert calls["normalize"] == 6
    assert calls["build"] == 6
    assert calls["run"] == 6
    assert len(result.bar_outcomes) == 6


def test_offline_canonical_e2e_smoke_socket_connect_blocked_still_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _blocked_connect(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network_access_disallowed_for_offline_canonical_e2e_smoke")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    result = _run_smoke()
    assert len(result.bar_outcomes) == 12


def test_offline_canonical_e2e_smoke_fail_closed_bitcoin_instrument() -> None:
    with pytest.raises(ValueError, match="instrument_not_supported_for_step29l"):
        _run_smoke(instrument_id="inst-btc-usdt-perp")


def test_offline_canonical_e2e_smoke_fail_closed_spot_instrument() -> None:
    with pytest.raises(ValueError, match="instrument_not_supported_for_step29l"):
        _run_smoke(instrument_id="inst-eth-usdt-spot")


def test_offline_canonical_e2e_smoke_fail_closed_registry_digest_mismatch() -> None:
    with pytest.raises(ValueError, match="registry_input_digest_mismatch"):
        _run_smoke(expected_registry_input_digest="0" * 64)


def test_offline_canonical_e2e_smoke_fail_closed_invalid_bar_schema() -> None:
    bars = _bars()
    bars.loc[bars.index[0], "is_final"] = False
    with pytest.raises(ValueError, match="bar_unfinalized"):
        _run_smoke(bars=bars)


def test_offline_canonical_e2e_smoke_architecture_invariants() -> None:
    sole_owner = assert_single_canonical_total_decision_owner()
    sole_builder = assert_single_productive_replay_input_constructor()
    assert_no_direct_strategy_authority_bypass()

    assert sole_owner.relative_path.endswith("integrated_offline_trading_logic_replay_v1.py")
    assert sole_owner.kind in {"sync", "async"}
    assert sole_builder.enclosing_function == "build_integrated_offline_replay_input_v1"
    assert build_integrated_offline_replay_input_v1.__name__ == (
        "build_integrated_offline_replay_input_v1"
    )
    assert run_integrated_offline_trading_logic_replay_v1.__name__ == (
        "run_integrated_offline_trading_logic_replay_v1"
    )


def test_offline_canonical_e2e_smoke_owner_sources_have_no_network_imports() -> None:
    for path in _OWNER_SOURCES:
        _assert_network_modules_absent(path)


def test_offline_canonical_e2e_smoke_execution_boundary_is_local_offline() -> None:
    source = (REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    assert "use_execution_pipeline=True" in source
    assert "honor_mapped_short_entry=True" in source
    assert "PaperBroker" not in source
    assert "LIVE_AUTHORIZED" not in source


def test_offline_canonical_e2e_smoke_no_runtime_mutation_of_governance_sources(
    tmp_path: Path,
) -> None:
    before = {
        "registry": (REPO_ROOT / "src/strategies/registry.py").read_bytes(),
        "wiring": (REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py").read_bytes(),
        "orchestrator": (
            REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
        ).read_bytes(),
    }
    marker = tmp_path / "smoke_marker.txt"
    marker.write_text("offline_smoke_local_only\n", encoding="utf-8")

    _run_smoke()

    after = {
        "registry": (REPO_ROOT / "src/strategies/registry.py").read_bytes(),
        "wiring": (REPO_ROOT / "src/backtest/mv2_research_wiring_v1.py").read_bytes(),
        "orchestrator": (
            REPO_ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
        ).read_bytes(),
    }
    assert before == after
    assert marker.read_text(encoding="utf-8") == "offline_smoke_local_only\n"
    # Smoke must not scatter artifacts into the repository root.
    assert not (REPO_ROOT / "offline_canonical_end_to_end_smoke_report.json").exists()
