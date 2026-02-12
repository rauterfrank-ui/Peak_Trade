from __future__ import annotations

from pathlib import Path

from src.core.peak_config import load_config_with_live_overrides


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _cfg(mode: str) -> str:
    return f"""
[environment]
mode = "{mode}"
enable_live_trading = false

[portfolio]
leverage = 1.0

[strategy]
trigger_delay = 10.0
name = "ma_crossover"

[macro]
regime_weight = 0.10

[deep.a.b.c]
value = 1

[flags]
enabled = false
""".lstrip()


def test_end_to_end_live_applies_multiple_overrides(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("live"))
    ov_path = _write(
        tmp_path / "auto.toml",
        """
[auto_applied]
"portfolio.leverage" = 1.5
"strategy.trigger_delay" = 7.0
"macro.regime_weight" = 0.25
""".lstrip(),
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.5
    assert eff.get("strategy.trigger_delay") == 7.0
    assert eff.get("macro.regime_weight") == 0.25


def test_paper_does_not_apply_overrides(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("paper"))
    ov_path = _write(
        tmp_path / "auto.toml",
        """
[auto_applied]
"portfolio.leverage" = 1.5
""".lstrip(),
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.0


def test_incremental_overrides_only_touch_listed_keys(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("testnet"))
    ov_path = _write(
        tmp_path / "auto.toml",
        """
[auto_applied]
"portfolio.leverage" = 1.25
""".lstrip(),
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.25
    # Unmentioned keys stay unchanged
    assert eff.get("strategy.trigger_delay") == 10.0
    assert eff.get("macro.regime_weight") == 0.10


def test_mixed_data_types_apply_if_path_exists(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("live"))
    ov_path = _write(
        tmp_path / "auto.toml",
        """
[auto_applied]
"flags.enabled" = true
""".lstrip(),
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("flags.enabled") is True


def test_deeply_nested_path_override(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("live"))
    ov_path = _write(
        tmp_path / "auto.toml",
        """
[auto_applied]
"deep.a.b.c.value" = 2
""".lstrip(),
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("deep.a.b.c.value") == 2


def test_invalid_toml_graceful_fallback(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _cfg("live"))
    ov_path = _write(tmp_path / "auto.toml", "not = = toml\n")

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    # Base value preserved
    assert eff.get("portfolio.leverage") == 1.0
