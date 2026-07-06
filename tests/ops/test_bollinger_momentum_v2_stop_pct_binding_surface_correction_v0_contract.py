"""Contract tests for bollinger/momentum v2 stop_pct binding surface correction v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.research.post_pr4922_offline_economic_evaluation_execution_v0 import (
    BINDING_CONFIG_DIGEST,
    PREVIOUS_BINDING_CONFIG_DIGEST,
    STRATEGY_PARAM_EXCLUDED_FROM_SIGNAL_BINDING_V0,
    build_post_pr4922_runtime_step31f_config_v0,
    compute_binding_config_digest_v0,
    strategy_params_for_signal_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = (
    REPO_ROOT / "config/research/post_pr4921_versioned_research_bindings_no_eval_v0.json"
)
PARENT_REVIEW_BUNDLE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/offline_economic_validity_evidence_and_binding_parameter_gap_decomposition_"
    "bollinger_momentum_v2_20260706T125607Z"
)
BOLLINGER_TEMPLATE = (
    REPO_ROOT
    / "config/ops/step31f_okx_inst_eth_usdt_perp_bollinger_bands_v1_economic_evaluation_v1.json"
)
MOMENTUM_TEMPLATE = (
    REPO_ROOT
    / "config/ops/step31f_okx_inst_eth_usdt_perp_momentum_1h_v1_economic_evaluation_v1.json"
)
TREND_TEMPLATE = (
    REPO_ROOT
    / "config/ops/step31f_okx_inst_eth_usdt_perp_trend_following_v1_economic_evaluation_v1.json"
)

ALLOWED_STRATEGY_PARAMS = {
    "bollinger_bands": frozenset({"bb_period", "bb_std", "entry_threshold", "exit_threshold"}),
    "momentum_1h": frozenset({"lookback_period", "entry_threshold", "exit_threshold"}),
    "trend_following": frozenset(
        {"adx_period", "adx_threshold", "exit_threshold", "ma_period", "use_ma_filter"}
    ),
}


def _binding_by_candidate(candidate_id: str) -> dict:
    config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    for binding in config["versioned_bindings"]:
        if binding["candidate_id"] == candidate_id:
            return binding
    raise KeyError(candidate_id)


class TestBollingerMomentumV2StopPctBindingSurfaceCorrectionV0Contract:
    def test_binding_config_digest_updated(self) -> None:
        config = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert compute_binding_config_digest_v0(config) == BINDING_CONFIG_DIGEST
        assert BINDING_CONFIG_DIGEST != PREVIOUS_BINDING_CONFIG_DIGEST

    def test_stop_pct_absent_from_bollinger_parameter_binding(self) -> None:
        binding = _binding_by_candidate("bollinger_bands")
        values = binding["parameter_binding"]["values"]
        assert "stop_pct" not in values
        assert set(values) <= ALLOWED_STRATEGY_PARAMS["bollinger_bands"]

    def test_stop_pct_absent_from_momentum_parameter_binding(self) -> None:
        binding = _binding_by_candidate("momentum_1h")
        values = binding["parameter_binding"]["values"]
        assert "stop_pct" not in values
        assert set(values) <= ALLOWED_STRATEGY_PARAMS["momentum_1h"]

    def test_trend_following_binding_unchanged(self) -> None:
        binding = _binding_by_candidate("trend_following")
        values = binding["parameter_binding"]["values"]
        assert "stop_pct" not in values
        assert values == {
            "adx_period": 14,
            "adx_threshold": 25.0,
            "exit_threshold": 20.0,
            "ma_period": 50,
            "use_ma_filter": True,
        }

    @pytest.mark.parametrize(
        ("strategy_id", "params"),
        [
            ("bollinger_bands", {"bb_period": 20, "bb_std": 2.0}),
            (
                "momentum_1h",
                {"lookback_period": 20, "entry_threshold": 0.02, "exit_threshold": -0.01},
            ),
        ],
    )
    def test_strategy_signal_binding_accepts_corrected_params(
        self, strategy_id: str, params: dict
    ) -> None:
        effective, _ = resolve_effective_strategy_params_v1(strategy_id, params)
        assert set(effective) <= ALLOWED_STRATEGY_PARAMS[strategy_id]

    @pytest.mark.parametrize("strategy_id", ["bollinger_bands", "momentum_1h"])
    def test_stop_pct_rejected_by_strategy_signal_binding(self, strategy_id: str) -> None:
        binding = _binding_by_candidate(strategy_id)
        polluted = dict(binding["parameter_binding"]["values"])
        polluted["stop_pct"] = 0.025
        with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param:stop_pct"):
            project_strategy_params_for_binding_v1(strategy_id, polluted)

    def test_strategy_params_filter_removes_stop_pct(self) -> None:
        filtered = strategy_params_for_signal_binding_v0(
            {"bb_period": 20, "bb_std": 2.0, "stop_pct": 0.02}
        )
        assert filtered == {"bb_period": 20, "bb_std": 2.0}
        assert STRATEGY_PARAM_EXCLUDED_FROM_SIGNAL_BINDING_V0 == frozenset({"stop_pct"})

    @pytest.mark.parametrize(
        ("template_path", "strategy_id"),
        [
            (BOLLINGER_TEMPLATE, "bollinger_bands"),
            (MOMENTUM_TEMPLATE, "momentum_1h"),
        ],
    )
    def test_step31f_template_preserves_stop_pct_only_in_sizing_contract(
        self, template_path: Path, strategy_id: str
    ) -> None:
        cfg = json.loads(template_path.read_text(encoding="utf-8"))
        strategy_params = cfg["economic_evaluation_v1"]["strategy_params"]
        sizing = cfg["offline_evaluation_sizing_contract_v1"]
        assert "stop_pct" not in strategy_params
        assert sizing["stop_pct"] == 0.025

    def test_build_runtime_step31f_config_excludes_stop_pct_from_strategy_params(
        self, tmp_path: Path
    ) -> None:
        from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
            NarrowDatasetMaterializationV0,
        )

        polluted_binding = _binding_by_candidate("bollinger_bands")
        polluted_binding = dict(polluted_binding)
        polluted_binding["parameter_binding"] = {
            **polluted_binding["parameter_binding"],
            "values": {
                **polluted_binding["parameter_binding"]["values"],
                "stop_pct": 0.02,
            },
        }
        narrow = NarrowDatasetMaterializationV0(
            dataset_root=tmp_path,
            bars_path=tmp_path / "bars.parquet",
            manifest_path=tmp_path / "dataset_manifest.json",
            dataset_digest="digest",
            manifest_digest="manifest",
            row_count=100,
            bar_granularity="1h",
            training_period="2024-05-01 00:00:00+00:00..2024-07-01 11:00:00+00:00",
            validation_period="2024-07-01 12:00:00+00:00..2024-08-01 05:00:00+00:00",
            out_of_sample_period="2024-08-01 06:00:00+00:00..2024-09-01 00:00:00+00:00",
        )
        output_path = tmp_path / "runtime_step31f.json"
        build_post_pr4922_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id="bollinger_bands",
            narrow_dataset=narrow,
            versioned_binding=polluted_binding,
            output_path=output_path,
        )
        cfg = json.loads(output_path.read_text(encoding="utf-8"))
        assert "stop_pct" not in cfg["economic_evaluation_v1"]["strategy_params"]
        assert cfg["offline_evaluation_sizing_contract_v1"]["stop_pct"] == 0.025

    def test_trend_following_template_unchanged(self) -> None:
        cfg = json.loads(TREND_TEMPLATE.read_text(encoding="utf-8"))
        assert cfg["economic_evaluation_v1"]["strategy_params"] == {
            "adx_period": 14,
            "adx_threshold": 25.0,
            "exit_threshold": 20.0,
            "ma_period": 50,
            "use_ma_filter": True,
        }
        assert cfg["offline_evaluation_sizing_contract_v1"]["stop_pct"] == 0.025

    def test_parent_review_bundle_path_documented(self) -> None:
        assert PARENT_REVIEW_BUNDLE.name.startswith(
            "offline_economic_validity_evidence_and_binding_parameter_gap_decomposition_"
        )
