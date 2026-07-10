"""STEP29M bouchaud_microstructure_ohlcv_proxy/v1 offline economic baseline materialization v0.

Research-only helpers for implementation digest binding and accounting reconciliation.
No runtime, order, or authority effect. No economic evaluation execution.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (
    accounting_reconciliation_to_dict,
    reconcile_legacy_backtest_result_accounting_v0,
)

MATERIALIZATION_OWNER = "research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0"
MATERIALIZATION_VERSION = "v0"
SCHEMA_VERSION = (
    "step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization.v0"
)
RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"

IMPLEMENTATION_SURFACE_PATHS: tuple[str, ...] = (
    "scripts/ops/invoke_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py",
    "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py",
    "src/backtest/engine.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "src/backtest/strategy_signal_binding_v1.py",
    "src/research/bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0.py",
    "src/research/bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0.py",
    "src/research/step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0.py",
    "src/strategies/bouchaud/bouchaud_microstructure_strategy.py",
)

METRICS_SUMMARY_FILENAME = "metrics_summary.json"


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    content = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.stem}_",
        suffix=path.suffix or ".json",
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception as exc:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise OSError(str(exc)) from exc
    finally:
        if not closed:
            os.close(fd)


def materialize_resilience_metrics_summary_json_v0(
    evidence_dir: Path,
    collector: Any,
) -> dict[str, Any]:
    summary = collector.get_summary()
    target = evidence_dir / METRICS_SUMMARY_FILENAME
    _atomic_write_json(target, summary)
    return summary


def materialize_legacy_backtest_accounting_reconciliation_v0(
    backtest_result: Any,
    *,
    initial_cash: float,
    funding_drag: float = 0.0,
    spread_drag: float = 0.0,
    slippage_impact: float = 0.0,
) -> dict[str, Any]:
    result = reconcile_legacy_backtest_result_accounting_v0(
        backtest_result,
        initial_cash=initial_cash,
        funding_drag=funding_drag,
        spread_drag=spread_drag,
        slippage_impact=slippage_impact,
    )
    payload = accounting_reconciliation_to_dict(result)
    payload["accounting_reconciliation_pass"] = result.reconciled
    payload["failure_class"] = (
        None
        if result.reconciled
        else (result.failure_class or "ACCOUNTING_RECONCILIATION_MISMATCH")
    )
    return payload


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(
    repo_root: Path,
) -> str:
    """Digest over bound offline evaluation implementation surfaces."""
    surfaces = {
        rel: _sha256_file(repo_root / rel)
        for rel in IMPLEMENTATION_SURFACE_PATHS
        if (repo_root / rel).is_file()
    }
    return _stable_digest(
        {
            "owner": MATERIALIZATION_OWNER,
            "version": MATERIALIZATION_VERSION,
            "research_scope": RESEARCH_SCOPE,
            "proxy_semantics": True,
            "true_tick_l2_microstructure": False,
            "surfaces": surfaces,
        }
    )


def compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
    *,
    config_digest: str,
    data_digest: str,
    implementation_digest: str,
    strategy_params_digest: str,
    material_difference_digest: str,
    hypothesis_id: str,
    instrument_id: str,
    data_period: str,
) -> str:
    return _stable_digest(
        {
            "research_scope": RESEARCH_SCOPE,
            "hypothesis_id": hypothesis_id,
            "instrument_id": instrument_id,
            "data_period": data_period,
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": implementation_digest,
            "strategy_params_digest": strategy_params_digest,
            "material_difference_digest": material_difference_digest,
            "proxy_semantics": True,
            "true_tick_l2_microstructure": False,
        }
    )
