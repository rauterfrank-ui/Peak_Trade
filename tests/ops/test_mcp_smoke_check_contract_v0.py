"""Contract tests for scripts/ops/mcp_smoke_check.py (offline, no subprocess tools)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = ROOT / "scripts" / "ops" / "mcp_smoke_check.py"


def _load_mcp_smoke_check():
    spec = importlib.util.spec_from_file_location("mcp_smoke_check", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sm():
    return _load_mcp_smoke_check()


def _write_mcp_json(root: Path, payload: dict) -> Path:
    cfg_dir = root / ".cursor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    p = cfg_dir / "mcp.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_load_mcp_config_success(sm, tmp_path: Path) -> None:
    p = _write_mcp_json(tmp_path, {"mcpServers": {"a": {"command": "npx"}}})
    data = sm.load_mcp_config(p)
    assert "mcpServers" in data
    assert data["mcpServers"]["a"]["command"] == "npx"


def test_load_mcp_config_missing_file(sm, tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        sm.load_mcp_config(missing)


def test_load_mcp_config_invalid_json(sm, tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{ not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        sm.load_mcp_config(p)


def test_load_mcp_config_missing_mcp_servers_key(sm, tmp_path: Path) -> None:
    p = tmp_path / "empty_servers.json"
    p.write_text(json.dumps({"x": 1}), encoding="utf-8")
    with pytest.raises(KeyError):
        sm.load_mcp_config(p)


def test_check_server_config_structural_with_command(sm) -> None:
    ok, msg = sm.check_server_config(
        "s1",
        {"command": "npx", "args": []},
        check_all=False,
        check_playwright=False,
        check_grafana=False,
    )
    assert ok is True
    assert "Konfiguriert" in msg
    assert "npx" in msg


def test_check_server_config_structural_missing_command(sm) -> None:
    ok, msg = sm.check_server_config(
        "s1",
        {"args": []},
        check_all=False,
        check_playwright=False,
        check_grafana=False,
    )
    assert ok is False
    assert "command" in msg


def test_structural_path_does_not_invoke_runtime_checkers(sm, monkeypatch) -> None:
    pw = MagicMock(side_effect=AssertionError("check_playwright_server should not run"))
    gf = MagicMock(side_effect=AssertionError("check_grafana_server should not run"))
    monkeypatch.setattr(sm, "check_playwright_server", pw)
    monkeypatch.setattr(sm, "check_grafana_server", gf)
    sm.check_server_config(
        "play",
        {"command": "npx", "args": ["@playwright/mcp@latest"]},
        check_all=False,
        check_playwright=False,
        check_grafana=False,
    )
    pw.assert_not_called()
    gf.assert_not_called()


def test_check_playwright_flag_runs_checker_when_server_is_npx(sm, monkeypatch) -> None:
    mock_pw = MagicMock(return_value=(True, "mocked ok"))
    monkeypatch.setattr(sm, "check_playwright_server", mock_pw)
    ok, msg = sm.check_server_config(
        "pw",
        {"command": "npx", "args": ["x"]},
        check_all=False,
        check_playwright=True,
        check_grafana=False,
    )
    assert ok is True
    assert msg == "mocked ok"
    mock_pw.assert_called_once_with(verbose=False)


def test_check_grafana_flag_runs_checker_for_grafana_image(sm, monkeypatch) -> None:
    mock_gf = MagicMock(return_value=(True, "grafana ok"))
    monkeypatch.setattr(sm, "check_grafana_server", mock_gf)
    ok, msg = sm.check_server_config(
        "graf",
        {"command": "docker", "args": ["run", "--rm", "grafana/mcp-grafana", "-h"]},
        check_all=False,
        check_playwright=False,
        check_grafana=True,
    )
    assert ok is True
    assert msg == "grafana ok"
    mock_gf.assert_called_once_with(verbose=False)


def test_check_all_triggers_playwright_for_npx_server(sm, monkeypatch) -> None:
    mock_pw = MagicMock(return_value=(True, "pw ok"))
    monkeypatch.setattr(sm, "check_playwright_server", mock_pw)
    ok, _msg = sm.check_server_config(
        "pw",
        {"command": "npx"},
        check_all=True,
        check_playwright=False,
        check_grafana=False,
    )
    assert ok is True
    mock_pw.assert_called_once()


def test_main_structural_success(monkeypatch, tmp_path: Path, capsys) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(
        tmp_path,
        {"mcpServers": {"alpha": {"command": "npx", "args": []}}},
    )
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "Alle Checks erfolgreich" in out or "erfolgreich" in out


def test_main_empty_servers_returns_zero(monkeypatch, tmp_path: Path, capsys) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(tmp_path, {"mcpServers": {}})
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 0
    out = capsys.readouterr().out
    assert "leer" in out or "Keine Server" in out


def test_main_missing_config_returns_one(monkeypatch, tmp_path: Path) -> None:
    sm = _load_mcp_smoke_check()
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 1


def test_main_invalid_json_returns_one(monkeypatch, tmp_path: Path) -> None:
    sm = _load_mcp_smoke_check()
    cfg_dir = tmp_path / ".cursor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "mcp.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 1


def test_main_missing_mcp_servers_key_returns_one(monkeypatch, tmp_path: Path, capsys) -> None:
    sm = _load_mcp_smoke_check()
    cfg_dir = tmp_path / ".cursor"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "mcp.json").write_text(json.dumps({"no_mcp_servers": True}), encoding="utf-8")
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 1
    assert "mcpServers" in capsys.readouterr().out


def test_main_check_playwright_uses_mocked_runtime(monkeypatch, tmp_path: Path, capsys) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(
        tmp_path,
        {"mcpServers": {"pw": {"command": "npx", "args": []}}},
    )
    mock_pw = MagicMock(return_value=(True, "stub playwright"))
    monkeypatch.setattr(sm, "check_playwright_server", mock_pw)
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py", "--check-playwright"])
    assert sm.main() == 0
    mock_pw.assert_called()
    assert "stub playwright" in capsys.readouterr().out


def test_main_check_grafana_uses_mocked_runtime(monkeypatch, tmp_path: Path, capsys) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(
        tmp_path,
        {
            "mcpServers": {
                "gf": {
                    "command": "docker",
                    "args": ["run", "grafana/mcp-grafana"],
                }
            }
        },
    )
    mock_gf = MagicMock(return_value=(True, "stub grafana"))
    monkeypatch.setattr(sm, "check_grafana_server", mock_gf)
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py", "--check-grafana"])
    assert sm.main() == 0
    mock_gf.assert_called()
    assert "stub grafana" in capsys.readouterr().out


def test_main_missing_server_command_returns_one(monkeypatch, tmp_path: Path) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(tmp_path, {"mcpServers": {"bad": {"args": []}}})
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py"])
    assert sm.main() == 1


def test_main_playwright_tool_unavailable_returns_three(monkeypatch, tmp_path: Path) -> None:
    sm = _load_mcp_smoke_check()
    _write_mcp_json(
        tmp_path,
        {"mcpServers": {"pw": {"command": "npx", "args": []}}},
    )
    monkeypatch.setattr(
        sm,
        "check_playwright_server",
        MagicMock(return_value=(False, "npx nicht verfügbar (Node.js/npm erforderlich)")),
    )
    monkeypatch.setattr(sm, "find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(sys, "argv", ["mcp_smoke_check.py", "--check-playwright"])
    assert sm.main() == 3
