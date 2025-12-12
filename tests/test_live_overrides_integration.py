"""
Tests für die Live-Overrides-Integration in PeakConfig.

Testet, dass config/live_overrides/auto.toml korrekt in Live-Environments
geladen und angewendet wird.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.core.peak_config import (
    PeakConfig,
    load_config_with_live_overrides,
    _is_live_like_environment,
    _load_live_auto_overrides,
)


def test_load_live_auto_overrides_missing_file():
    """Test dass missing file ein leeres Dict zurückgibt."""
    result = _load_live_auto_overrides(Path("/nonexistent/auto.toml"))
    assert result == {}


def test_load_live_auto_overrides_valid_file():
    """Test dass eine valide auto.toml korrekt geladen wird."""
    with TemporaryDirectory() as tmpdir:
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
"macro.regime_weight" = 0.35
""",
            encoding="utf-8",
        )

        result = _load_live_auto_overrides(auto_path)

        assert result == {
            "portfolio.leverage": 1.75,
            "strategy.trigger_delay": 8.0,
            "macro.regime_weight": 0.35,
        }


def test_load_live_auto_overrides_invalid_toml():
    """Test dass ungültiges TOML nicht zum Crash führt."""
    with TemporaryDirectory() as tmpdir:
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text("invalid toml [[[", encoding="utf-8")

        # Sollte leeres Dict zurückgeben und Warning ausgeben
        with pytest.warns(UserWarning, match="Failed to load"):
            result = _load_live_auto_overrides(auto_path)

        assert result == {}


def test_is_live_like_environment_paper():
    """Test dass Paper-Environment nicht als live-like erkannt wird."""
    cfg = PeakConfig(raw={"environment": {"mode": "paper"}})
    assert not _is_live_like_environment(cfg)


def test_is_live_like_environment_live():
    """Test dass Live-Environment als live-like erkannt wird."""
    cfg = PeakConfig(raw={"environment": {"mode": "live"}})
    assert _is_live_like_environment(cfg)


def test_is_live_like_environment_testnet():
    """Test dass Testnet-Environment als live-like erkannt wird."""
    cfg = PeakConfig(raw={"environment": {"mode": "testnet"}})
    assert _is_live_like_environment(cfg)


def test_is_live_like_environment_enable_live_trading():
    """Test dass enable_live_trading Flag erkannt wird."""
    cfg = PeakConfig(
        raw={"environment": {"mode": "paper", "enable_live_trading": True}}
    )
    assert _is_live_like_environment(cfg)


def test_load_config_with_live_overrides_paper_no_apply():
    """Test dass Overrides in Paper nicht angewendet werden."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "paper"

[portfolio]
leverage = 1.0

[strategy]
trigger_delay = 10.0
""",
            encoding="utf-8",
        )

        # Auto-Overrides erstellen
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
""",
            encoding="utf-8",
        )

        # Config laden (ohne force)
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path
        )

        # Overrides sollten NICHT angewendet sein
        assert cfg.get("portfolio.leverage") == 1.0
        assert cfg.get("strategy.trigger_delay") == 10.0


def test_load_config_with_live_overrides_live_apply():
    """Test dass Overrides in Live-Environment angewendet werden."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "live"

[portfolio]
leverage = 1.0

[strategy]
trigger_delay = 10.0
""",
            encoding="utf-8",
        )

        # Auto-Overrides erstellen
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
""",
            encoding="utf-8",
        )

        # Config laden
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path
        )

        # Overrides sollten angewendet sein
        assert cfg.get("portfolio.leverage") == 1.75
        assert cfg.get("strategy.trigger_delay") == 8.0


def test_load_config_with_live_overrides_testnet_apply():
    """Test dass Overrides in Testnet-Environment angewendet werden."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "testnet"

[portfolio]
leverage = 1.0
""",
            encoding="utf-8",
        )

        # Auto-Overrides erstellen
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.leverage" = 2.0
""",
            encoding="utf-8",
        )

        # Config laden
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path
        )

        # Overrides sollten angewendet sein
        assert cfg.get("portfolio.leverage") == 2.0


def test_load_config_with_live_overrides_force_apply():
    """Test dass force_apply_overrides auch in Paper funktioniert."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "paper"

[portfolio]
leverage = 1.0
""",
            encoding="utf-8",
        )

        # Auto-Overrides erstellen
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.leverage" = 1.5
""",
            encoding="utf-8",
        )

        # Config laden mit force_apply
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path, force_apply_overrides=True
        )

        # Overrides sollten angewendet sein (trotz Paper)
        assert cfg.get("portfolio.leverage") == 1.5


def test_load_config_with_live_overrides_nested_paths():
    """Test dass verschachtelte dotted paths korrekt angewendet werden."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "live"

[portfolio.risk]
max_position = 0.1

[strategy.ma_crossover]
fast_window = 10
slow_window = 30
""",
            encoding="utf-8",
        )

        # Auto-Overrides erstellen
        auto_path = Path(tmpdir) / "auto.toml"
        auto_path.write_text(
            """
[auto_applied]
"portfolio.risk.max_position" = 0.15
"strategy.ma_crossover.fast_window" = 12
""",
            encoding="utf-8",
        )

        # Config laden
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path
        )

        # Overrides sollten angewendet sein
        assert cfg.get("portfolio.risk.max_position") == 0.15
        assert cfg.get("strategy.ma_crossover.fast_window") == 12
        # Unveränderte Werte bleiben
        assert cfg.get("strategy.ma_crossover.slow_window") == 30


def test_load_config_with_live_overrides_missing_auto_file():
    """Test dass fehlende auto.toml kein Problem ist."""
    with TemporaryDirectory() as tmpdir:
        # Config erstellen
        config_path = Path(tmpdir) / "config.toml"
        config_path.write_text(
            """
[environment]
mode = "live"

[portfolio]
leverage = 1.0
""",
            encoding="utf-8",
        )

        # Kein auto.toml erstellen
        auto_path = Path(tmpdir) / "auto.toml"

        # Config laden (sollte funktionieren ohne auto.toml)
        cfg = load_config_with_live_overrides(
            config_path, auto_overrides_path=auto_path
        )

        # Original-Werte bleiben erhalten
        assert cfg.get("portfolio.leverage") == 1.0
