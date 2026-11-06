"""Negative contracts: legacy overlay loader is not a config authority."""

from __future__ import annotations

import ast
from pathlib import Path

from src.core.peak_config import load_config, load_config_with_live_overrides


REPO_ROOT = Path(__file__).resolve().parents[1]
LIVE_SESSION_PATH = REPO_ROOT / "src" / "execution" / "live_session.py"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _base_config(*, mode: str) -> str:
    return f"""
[environment]
mode = "{mode}"
enable_live_trading = false

[portfolio]
leverage = 1.0

[flags]
enabled = false
""".lstrip()


def _overlay_toml() -> str:
    return """
[auto_applied]
"portfolio.leverage" = 1.75
"flags.enabled" = true
"environment.mode" = "live"
""".lstrip()


def test_live_mode_overlay_does_not_change_leverage(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config(mode="live"))
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.0


def test_testnet_mode_overlay_is_not_applied(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config(mode="testnet"))
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("portfolio.leverage") == 1.0
    assert eff.get("environment.mode") == "testnet"


def test_paper_force_apply_overlay_is_not_applied(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config(mode="paper"))
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    eff = load_config_with_live_overrides(
        cfg_path, auto_overrides_path=ov_path, force_apply_overrides=True
    )
    assert eff.get("portfolio.leverage") == 1.0
    assert eff.get("environment.mode") == "paper"


def test_overlay_enabled_flag_does_not_mutate_base(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config(mode="live"))
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    eff = load_config_with_live_overrides(cfg_path, auto_overrides_path=ov_path)
    assert eff.get("flags.enabled") is False


def test_force_apply_equals_plain_load_config_for_authority_values(tmp_path: Path) -> None:
    cfg_path = _write(tmp_path / "cfg.toml", _base_config(mode="paper"))
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    base = load_config(cfg_path)
    eff = load_config_with_live_overrides(
        cfg_path, auto_overrides_path=ov_path, force_apply_overrides=True
    )
    assert eff.get("portfolio.leverage") == base.get("portfolio.leverage")
    assert eff.get("environment.mode") == base.get("environment.mode")
    live_flag = "environment.enable_live_trading"
    assert eff.get(live_flag) == base.get(live_flag)


def test_shadow_and_live_force_apply_remain_non_authoritative(tmp_path: Path) -> None:
    ov_path = _write(tmp_path / "auto.toml", _overlay_toml())
    for mode in ("shadow", "live"):
        cfg_path = _write(tmp_path / f"{mode}.toml", _base_config(mode=mode))
        base = load_config(cfg_path)
        eff = load_config_with_live_overrides(
            cfg_path, auto_overrides_path=ov_path, force_apply_overrides=True
        )
        assert eff.get("portfolio.leverage") == base.get("portfolio.leverage") == 1.0
        assert eff.get("environment.mode") == base.get("environment.mode") == mode
        assert eff.get("flags.enabled") is False


def test_live_session_imports_bounded_live_not_legacy_overlay_loader() -> None:
    source = LIVE_SESSION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(LIVE_SESSION_PATH))
    imported: set[str] = set()
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names = {alias.name for alias in node.names}
            if node.module and node.module.endswith("peak_config"):
                imported.update(names)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called.add(node.func.id)
    assert "load_config_with_bounded_live" in imported
    assert "load_config_with_bounded_live" in called
    assert "load_config_with_live_overrides" not in imported
    assert "load_config_with_live_overrides" not in called
    assert "load_config_with_live_overrides" not in source
