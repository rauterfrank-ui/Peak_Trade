"""Unit tests for market_data_cache_observation_reader (local/offline only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

from src.data.kraken_cache_loader import KrakenDataHealth
from src.ops.market_data_cache_observation_reader import (
    READER_SCHEMA_VERSION,
    read_market_data_cache_observation,
)


def test_unknown_when_no_config(tmp_path: Path) -> None:
    out = read_market_data_cache_observation(tmp_path, None)
    assert out["market_data_cache"] == "unknown"
    assert out["observation_reason"] == "no_config_path"
    assert out["data_source"] == "none"


def test_unknown_when_config_missing_file(tmp_path: Path) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("[general]\nstarting_capital = 10000\n", encoding="utf-8")
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "unknown"
    assert out["observation_reason"] == "cache_base_path_absent"


@patch("src.data.kraken_cache_loader.check_data_health_only")
@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_ok_when_health_ok(
    mock_rms: MagicMock,
    mock_health: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("[general]\n", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    mock_rms.return_value = {
        "base_path": "data/cache",
        "default_market": "BTC/EUR",
        "default_timeframe": "1h",
        "min_bars": 10,
    }
    mock_health.return_value = KrakenDataHealth(status="ok", num_bars=100)
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "ok"
    assert out["data_source"] == "kraken_parquet_cache_local"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION


@patch("src.data.kraken_cache_loader.check_data_health_only")
@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_degraded_when_missing_file(
    mock_rms: MagicMock,
    mock_health: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# x\n", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    mock_rms.return_value = {
        "base_path": "data/cache",
        "default_market": "BTC/EUR",
        "default_timeframe": "1h",
        "min_bars": 10,
    }
    mock_health.return_value = KrakenDataHealth(status="missing_file", notes="nope")
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "degraded"
    assert "missing_file" in out["observation_reason"]


@patch("src.data.kraken_cache_loader.check_data_health_only")
@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_unknown_when_health_check_raises(
    mock_rms: MagicMock,
    mock_health: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# x\n", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    mock_rms.return_value = {"base_path": "data/cache", "min_bars": 1}
    mock_health.side_effect = RuntimeError("boom")
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "unknown"
    assert out["observation_reason"] == "health_check_failed"


@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_unknown_when_config_load_raises(
    mock_rms: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("[general]\n", encoding="utf-8")
    mock_rms.side_effect = ValueError("rms load failed")
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "unknown"
    assert out["observation_reason"] == "config_load_failed"


@patch("src.data.kraken_cache_loader.check_data_health_only")
@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_unknown_when_health_status_unmapped(
    mock_rms: MagicMock,
    mock_health: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# x\n", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    mock_rms.return_value = {
        "base_path": "data/cache",
        "default_market": "BTC/EUR",
        "default_timeframe": "1h",
        "min_bars": 10,
    }
    mock_health.return_value = KrakenDataHealth(
        status=cast(Any, "not_a_mapped_status"),
        num_bars=0,
    )
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "unknown"
    assert out["observation_reason"] == "unmapped_health_status"
    assert out["provenance"].get("kraken_health_status") == "not_a_mapped_status"


@patch("src.data.kraken_cache_loader.check_data_health_only")
@patch("src.data.kraken_cache_loader.get_real_market_smokes_config")
def test_warn_when_health_status_other(
    mock_rms: MagicMock,
    mock_health: MagicMock,
    tmp_path: Path,
) -> None:
    cfg = tmp_path / "config" / "config.toml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("# x\n", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    mock_rms.return_value = {
        "base_path": "data/cache",
        "default_market": "BTC/EUR",
        "default_timeframe": "1h",
        "min_bars": 10,
    }
    mock_health.return_value = KrakenDataHealth(status="other", num_bars=1, notes="n")
    out = read_market_data_cache_observation(tmp_path, cfg)
    assert out["market_data_cache"] == "warn"
    assert out["observation_reason"] == "kraken_cache_health_other"
