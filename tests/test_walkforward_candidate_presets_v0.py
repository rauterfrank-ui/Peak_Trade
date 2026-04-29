"""
Tests for walk-forward explicit candidate presets (schema v0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtest.walkforward import (
    WALKFORWARD_CANDIDATE_PRESETS_SCHEMA_V0,
    WalkForwardConfig,
    WalkForwardResult,
    WalkForwardWindowResult,
    load_walkforward_candidate_presets,
    run_walkforward_for_candidate_presets,
)
from tests.test_walkforward_backtest import create_test_data


def _minimal_ma_preset_doc() -> dict:
    return {
        "schema_version": WALKFORWARD_CANDIDATE_PRESETS_SCHEMA_V0,
        "strategy": "ma_crossover",
        "candidates": [
            {
                "name": "preset_a",
                "params": {
                    "fast_period": 5,
                    "slow_period": 20,
                    "stop_pct": 0.02,
                },
            },
            {
                "name": "preset_b",
                "params": {
                    "fast_period": 12,
                    "slow_period": 30,
                    "stop_pct": 0.02,
                },
            },
        ],
    }


class TestLoadWalkforwardCandidatePresets:
    def test_missing_file(self, tmp_path: Path) -> None:
        p = tmp_path / "none.json"
        with pytest.raises(FileNotFoundError, match="not found"):
            load_walkforward_candidate_presets(p)

    def test_invalid_json(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_walkforward_candidate_presets(p)

    def test_wrong_schema_version(self, tmp_path: Path) -> None:
        p = tmp_path / "wrong.json"
        p.write_text(
            json.dumps({"schema_version": "other", "strategy": "x", "candidates": []}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="Unsupported schema_version"):
            load_walkforward_candidate_presets(p)

    def test_empty_candidates(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.json"
        p.write_text(
            json.dumps(
                {
                    "schema_version": WALKFORWARD_CANDIDATE_PRESETS_SCHEMA_V0,
                    "strategy": "ma_crossover",
                    "candidates": [],
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="non-empty list"):
            load_walkforward_candidate_presets(p)

    def test_load_ok(self, tmp_path: Path) -> None:
        p = tmp_path / "ok.json"
        doc = _minimal_ma_preset_doc()
        p.write_text(json.dumps(doc), encoding="utf-8")
        strategy, cands = load_walkforward_candidate_presets(p)
        assert strategy == "ma_crossover"
        assert len(cands) == 2
        assert cands[0]["name"] == "preset_a"
        assert cands[0]["params"]["fast_period"] == 5


class TestRunWalkforwardCandidatePresets:
    def test_duplicate_names_get_unique_config_ids(self, tmp_path: Path) -> None:
        p = tmp_path / "dup.json"
        doc = _minimal_ma_preset_doc()
        doc["candidates"] = [
            {"name": "same", "params": doc["candidates"][0]["params"]},
            {"name": "same", "params": doc["candidates"][1]["params"]},
        ]
        p.write_text(json.dumps(doc), encoding="utf-8")

        df = create_test_data(n_bars=500, freq="1d")
        wf = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
            output_dir=tmp_path / "out",
        )
        results = run_walkforward_for_candidate_presets(p, "label_sweep", wf, df=df)
        assert len(results) == 2
        ids = [r.config_id for r in results]
        assert ids[0] == "same"
        assert ids[1] == "same_2"

    def test_preset_names_in_config_id_and_reports_metadata(self, tmp_path: Path) -> None:
        p = tmp_path / "run.json"
        p.write_text(json.dumps(_minimal_ma_preset_doc()), encoding="utf-8")
        df = create_test_data(n_bars=500, freq="1d")
        wf = WalkForwardConfig(
            train_window="90d",
            test_window="30d",
            output_dir=tmp_path / "out",
        )
        results = run_walkforward_for_candidate_presets(p, "wf_test_sweep", wf, df=df)
        assert len(results) == 2
        by_id = {r.config_id: r for r in results}
        assert "preset_a" in by_id
        assert "preset_b" in by_id
        assert by_id["preset_a"].strategy_name == "ma_crossover"


class TestRunWalkforwardBacktestCliPresetBranch:
    """CLI uses presets path without calling top-N sweep loader."""

    def test_run_from_args_preset_skips_top_n_sweep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import scripts.run_walkforward_backtest as rwmod

        wr = WalkForwardWindowResult(
            window_index=0,
            train_start=pd.Timestamp("2020-01-01"),
            train_end=pd.Timestamp("2020-04-01"),
            test_start=pd.Timestamp("2020-04-01"),
            test_end=pd.Timestamp("2020-05-01"),
            metrics={"sharpe": 0.2, "total_return": 0.01},
        )
        fake_result = WalkForwardResult(
            config_id="from_preset",
            strategy_name="ma_crossover",
            windows=[wr],
            aggregate_metrics={
                "avg_sharpe": 0.2,
                "avg_return": 0.01,
                "win_rate_windows": 1.0,
                "total_windows": 1,
            },
        )

        def fail_topn(*_a, **_k):
            raise AssertionError("run_walkforward_for_top_n_from_sweep must not be used")

        monkeypatch.setattr(rwmod, "run_walkforward_for_top_n_from_sweep", fail_topn)

        def fake_presets(preset_path, sweep_name, wf_config, *, df, logger=None):
            assert Path(preset_path).is_file()
            assert sweep_name == "cli_sweep_label"
            return [fake_result]

        monkeypatch.setattr(rwmod, "run_walkforward_for_candidate_presets", fake_presets)

        preset_file = tmp_path / "c.json"
        preset_file.write_text(json.dumps(_minimal_ma_preset_doc()), encoding="utf-8")
        out_dir = tmp_path / "reports"

        code = rwmod.run_from_args(
            rwmod.build_parser().parse_args(
                [
                    "--sweep-name",
                    "cli_sweep_label",
                    "--train-window",
                    "30d",
                    "--test-window",
                    "10d",
                    "--use-dummy-data",
                    "--dummy-bars",
                    "120",
                    "--candidate-presets",
                    str(preset_file),
                    "--output-dir",
                    str(out_dir),
                ]
            )
        )
        assert code == 0


class TestNoRegistryWrites:
    """Regression: preset loader does not touch registry/out/ops paths."""

    def test_load_only_reads_file(self, tmp_path: Path) -> None:
        p = tmp_path / "only.json"
        p.write_text(json.dumps(_minimal_ma_preset_doc()), encoding="utf-8")
        load_walkforward_candidate_presets(p)
        assert {f.name for f in tmp_path.iterdir()} == {"only.json"}
