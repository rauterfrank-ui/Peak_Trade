"""Preflight guards for scripts/run_shadow_paper_session.py (CI-parity env checks; no exchange I/O)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _clear_live_guard_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PT_LIVE_CONFIRM_TOKEN", raising=False)
    monkeypatch.delenv("PEAK_TRADE_LIVE_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_LIVE_ARMED", raising=False)


def test_shadow_paper_cli_assert_safe_environment_clean(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_live_guard_env(monkeypatch)
    from scripts.run_shadow_paper_session import shadow_paper_cli_assert_safe_environment

    shadow_paper_cli_assert_safe_environment()


@pytest.mark.parametrize(
    ("env_var", "value"), [("PEAK_TRADE_LIVE_ENABLED", "true"), ("PEAK_TRADE_LIVE_ARMED", "1")]
)
def test_shadow_paper_cli_assert_safe_environment_rejects_live_flags(
    monkeypatch: pytest.MonkeyPatch, env_var: str, value: str
) -> None:
    _clear_live_guard_env(monkeypatch)
    monkeypatch.setenv(env_var, value)
    from scripts.run_shadow_paper_session import (
        ShadowPaperCliPreflightError,
        shadow_paper_cli_assert_safe_environment,
    )

    with pytest.raises(ShadowPaperCliPreflightError):
        shadow_paper_cli_assert_safe_environment()


def test_shadow_paper_cli_assert_safe_environment_rejects_confirm_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_live_guard_env(monkeypatch)
    monkeypatch.setenv("PT_LIVE_CONFIRM_TOKEN", "dummy")
    from scripts.run_shadow_paper_session import (
        ShadowPaperCliPreflightError,
        shadow_paper_cli_assert_safe_environment,
    )

    with pytest.raises(ShadowPaperCliPreflightError):
        shadow_paper_cli_assert_safe_environment()


def test_main_dry_run_minimal_paper_config_no_exchange_construct(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_live_guard_env(monkeypatch)
    cfg = tmp_path / "paper.toml"
    cfg.write_text('[environment]\nmode = "paper"\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_shadow_paper_session", "--config", str(cfg), "--dry-run", "--no-logging"],
    )

    import scripts.run_shadow_paper_session as rsp

    with patch.object(rsp, "KrakenLiveCandleSource") as mock_src:
        code = rsp.main()
    assert code == 0
    mock_src.assert_called_once()


def test_main_preflight_returns_one_when_live_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_live_guard_env(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_LIVE_ENABLED", "true")
    cfg = tmp_path / "paper.toml"
    cfg.write_text('[environment]\nmode = "paper"\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_shadow_paper_session", "--config", str(cfg), "--dry-run", "--no-logging"],
    )

    import scripts.run_shadow_paper_session as rsp

    with patch.object(rsp, "KrakenLiveCandleSource") as mock_src:
        code = rsp.main()
    assert code == 1
    mock_src.assert_not_called()


def test_main_dry_run_live_mode_config_returns_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _clear_live_guard_env(monkeypatch)
    cfg = tmp_path / "live.toml"
    cfg.write_text('[environment]\nmode = "live"\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_shadow_paper_session", "--config", str(cfg), "--dry-run", "--no-logging"],
    )

    import scripts.run_shadow_paper_session as rsp

    with patch.object(rsp, "KrakenLiveCandleSource") as mock_src:
        code = rsp.main()
    assert code == 1
    mock_src.assert_not_called()
