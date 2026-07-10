"""STEP29M bouchaud_microstructure_ohlcv_proxy/v1 offline economic baseline materialization v0.

Research-only helpers for implementation digest binding. No runtime, order,
or authority effect. No economic evaluation execution.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

MATERIALIZATION_OWNER = "research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0"
MATERIALIZATION_VERSION = "v0"
SCHEMA_VERSION = (
    "step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization.v0"
)
RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"

IMPLEMENTATION_SURFACE_PATHS: tuple[str, ...] = (
    "src/backtest/engine.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "src/backtest/strategy_signal_binding_v1.py",
    "src/research/bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0.py",
    "src/research/step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0.py",
    "src/strategies/bouchaud/bouchaud_microstructure_strategy.py",
)


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
