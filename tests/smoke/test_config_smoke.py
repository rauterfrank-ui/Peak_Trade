# tests/smoke/test_config_smoke.py
"""
Smoke Test: Config Loading.

Stellt sicher, dass die Default-Config ladbar ist und grundlegende Invarianten erfüllt.
"""
import pytest
from pathlib import Path


def test_config_toml_exists():
    """Test dass config.toml existiert."""
    config_path = Path("config.toml")
    assert config_path.exists(), "config.toml must exist"


def test_config_loadable():
    """Test dass Config geladen werden kann."""
    from src.core.peak_config import load_config

    cfg = load_config()
    assert cfg is not None


def test_config_has_required_sections():
    """Test dass Config die wichtigsten Sections hat."""
    from src.core.peak_config import load_config

    cfg = load_config()

    # Check critical sections
    assert cfg.get("environment.mode") is not None
    assert cfg.get("general.base_currency") is not None


def test_environment_config_safe_default():
    """Test dass Environment-Config safe-by-default ist."""
    from src.core.peak_config import load_config

    cfg = load_config()

    # Live-Trading muss standardmäßig deaktiviert sein
    enable_live = cfg.get("environment.enable_live_trading", True)  # Default True to fail if not set
    assert enable_live is False, "enable_live_trading must be False by default (safe-by-default)"


def test_live_risk_config_exists():
    """Test dass Live-Risk-Config existiert."""
    from src.core.peak_config import load_config

    cfg = load_config()

    # Live-Risk sollte konfiguriert sein
    enabled = cfg.get("live_risk.enabled")
    assert enabled is not None  # Muss gesetzt sein (True oder False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
