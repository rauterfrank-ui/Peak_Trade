"""Contract tests for bouchaud OHLCV proxy v1 offline baseline materialization v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (
    IMPLEMENTATION_SURFACE_PATHS,
    compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0,
    compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_CONFIG = (
    REPO_ROOT
    / "config/ops/step29m_okx_inst_eth_usdt_perp_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_v1.json"
)
BINDING_CONFIG = (
    REPO_ROOT
    / "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)


def test_implementation_digest_stable_and_matches_binding() -> None:
    digest = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(REPO_ROOT)
    binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    assert digest == binding["binding"]["digest_bindings"]["implementation_digest"]["value"]
    assert len(digest) == 64


def test_config_digest_matches_binding() -> None:
    cfg = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    digest = compute_evaluation_config_digest_v1(cfg)
    binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    assert digest == binding["binding"]["digest_bindings"]["config_digest"]["value"]


def test_binding_digest_roundtrip_deterministic() -> None:
    binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    digests = binding["binding"]["digest_bindings"]
    first = compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
        config_digest=digests["config_digest"]["value"],
        data_digest=digests["data_digest"]["value"],
        implementation_digest=digests["implementation_digest"]["value"],
        strategy_params_digest=digests["strategy_params_digest"]["value"],
        material_difference_digest=digests["material_difference_digest"]["value"],
        hypothesis_id=binding["hypothesis_id"],
        instrument_id="inst-eth-usdt-perp",
        data_period=binding["binding"]["period_binding"]["data_period"],
    )
    second = compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
        config_digest=digests["config_digest"]["value"],
        data_digest=digests["data_digest"]["value"],
        implementation_digest=digests["implementation_digest"]["value"],
        strategy_params_digest=digests["strategy_params_digest"]["value"],
        material_difference_digest=digests["material_difference_digest"]["value"],
        hypothesis_id=binding["hypothesis_id"],
        instrument_id="inst-eth-usdt-perp",
        data_period=binding["binding"]["period_binding"]["data_period"],
    )
    assert first == second


def test_implementation_surface_paths_exist() -> None:
    for rel in IMPLEMENTATION_SURFACE_PATHS:
        assert (REPO_ROOT / rel).is_file()


def test_repeated_implementation_digest_empty_diff() -> None:
    first = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(REPO_ROOT)
    second = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(REPO_ROOT)
    assert first == second
