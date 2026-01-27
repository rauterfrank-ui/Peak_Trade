from __future__ import annotations

from pathlib import Path

import pytest

from src.core.peak_config import (
    _is_live_like_environment,
    _load_live_auto_overrides,
    load_config,
    load_config_with_live_overrides,
)


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _base_config_toml(*, mode: str) -> str:
    return f"""
[environment]
mode = "{mode}"
enable_live_trading = false

[portfolio]
leverage = 1.0

[strategy]
trigger_delay = 10.0

[macro]
regime_weight = 0.25

[nested.deep.more]
value = 1
""".lstrip()


def _overrides_toml() -> str:
    # Mix of quoted dotted-keys (recommended) and unquoted dotted-keys (nested tables)
    return """
[auto_applied]
"portfolio.leverage" = 1.75
"strategy.trigger_delay" = 8.0
macro.regime_weight = 0.35
"nested.deep.more.value" = 2
""".lstrip()


def test_is_live_like_environment_paper() -> None:
    # Use a temp file to avoid writing into repo root
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        cfg_path = _write(Path(d) / "cfg.toml", _base_config_toml(mode="paper"))
        cfg = load_config(cfg_path)
    assert _is_live_like_environment(cfg) is False


def test_is_live_like_environment_live(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path / "cfg.toml", _base_config_toml(mode="live")))
    assert _is_live_like_environment(cfg) is True


def test_is_live_like_environment_testnet(tmp_path: Path) -> None:
    cfg = load_config(_write(tmp_path / "cfg.toml", _base_config_toml(mode="testnet")))
    assert _is_live_like_environment(cfg) is True


def test_is_live_like_environment_enable_live_trading(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="paper") + "\n")
    # Patch enable_live_trading=True
    cfg_path.write_text(
        _base_config_toml(mode="paper").replace("enable_live_trading = false", "enable_live_trading = true"),
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    assert _is_live_like_environment(cfg) is True


def test_load_live_auto_overrides_missing_file(tmp_path: Path) -> None:
    assert _load_live_auto_overrides(tmp_path / "missing.toml") == {}


def test_load_live_auto_overrides_invalid_toml(tmp_path: Path) -> None:
    p = _write(tmp_path / "bad.toml", "this is not toml = = =\n")
    assert _load_live_auto_overrides(p) == {}


def test_load_live_auto_overrides_reads_and_flattens(tmp_path: Path) -> None:
    p = _write(tmp_path / "auto.toml", _overrides_toml())
    overrides = _load_live_auto_overrides(p)
    assert overrides["portfolio.leverage"] == 1.75
    assert overrides["strategy.trigger_delay"] == 8.0
    assert overrides["macro.regime_weight"] == 0.35
    assert overrides["nested.deep.more.value"] == 2


def test_load_config_with_live_overrides_paper_no_apply(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="paper"))
    ov_path = _write(tmp_path / "auto.toml", _overrides_toml())

    base = load_config(cfg_path)
    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)

    assert eff.get("portfolio.leverage") == base.get("portfolio.leverage") == 1.0


def test_load_config_with_live_overrides_live_apply(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="live"))
    ov_path = _write(tmp_path / "auto.toml", _overrides_toml())

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.75
    assert eff.get("strategy.trigger_delay") == 8.0
    assert eff.get("macro.regime_weight") == 0.35
    assert eff.get("nested.deep.more.value") == 2


def test_load_config_with_live_overrides_testnet_apply(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="testnet"))
    ov_path = _write(tmp_path / "auto.toml", _overrides_toml())

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.75


def test_load_config_with_live_overrides_force_apply(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="paper"))
    ov_path = _write(tmp_path / "auto.toml", _overrides_toml())

    eff = load_config_with_live_overrides(
        cfg_path, auto_overrides_path=ov_path, force_apply_overrides=True
    )
    assert eff.get("portfolio.leverage") == 1.75


def test_load_config_with_live_overrides_nested_paths(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="live"))
    ov_path = _write(tmp_path / "auto.toml", _overrides_toml())

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("nested.deep.more.value") == 2


def test_load_config_with_live_overrides_unknown_path_ignored(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config_toml(mode="live"))
    ov_path = _write(
        tmp_path / "auto.toml",
        _overrides_toml() + '\n"does.not.exist" = 123\n',
    )

    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("does.not.exist", None) is None
