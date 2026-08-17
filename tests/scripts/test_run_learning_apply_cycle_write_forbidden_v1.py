"""Fail-closed contract: run_learning_apply_cycle must not write config files."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.run_learning_apply_cycle import (
    LEARNING_APPLY_WRITE_FORBIDDEN,
    _write_override_toml,
    main,
)


def _write_snippet(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '{"patches": [{"target": "portfolio.leverage", "new_value": 1.75}]}',
        encoding="utf-8",
    )


def test_write_override_toml_raises_and_does_not_create_file(tmp_path: Path) -> None:
    out = tmp_path / "learning.override.toml"
    with pytest.raises(PermissionError, match="LEARNING_APPLY_WRITE_FORBIDDEN"):
        _write_override_toml(out, {"portfolio.leverage": 1.75})
    assert not out.exists()
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.backup"))


def test_non_dry_run_refuses_write_and_creates_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    in_dir = tmp_path / "snippets"
    _write_snippet(in_dir / "patch.json")
    out = tmp_path / "config" / "auto" / "learning.override.toml"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_learning_apply_cycle.py",
            "--in-dir",
            str(in_dir),
            "--out-file",
            str(out),
        ],
    )
    rc = main()
    captured = capsys.readouterr()
    assert rc == 1
    assert "LEARNING_APPLY_WRITE_FORBIDDEN" in captured.out
    assert "REFUSED" in captured.out
    assert "Wrote " not in captured.out
    assert not out.exists()
    assert not (tmp_path / "config" / "auto").exists()
    assert not list(tmp_path.rglob("*.backup"))
    assert not list(tmp_path.rglob("*.tmp"))


def test_non_dry_run_does_not_replace_or_backup_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    in_dir = tmp_path / "snippets"
    _write_snippet(in_dir / "patch.json")
    out = tmp_path / "learning.override.toml"
    original = '[overrides]\n"portfolio.leverage" = 1.0\n'
    out.write_text(original, encoding="utf-8")
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_learning_apply_cycle.py",
            "--in-dir",
            str(in_dir),
            "--out-file",
            str(out),
        ],
    )
    rc = main()
    captured = capsys.readouterr()
    assert rc == 1
    assert LEARNING_APPLY_WRITE_FORBIDDEN in captured.out
    assert out.read_text(encoding="utf-8") == original
    assert not out.with_suffix(out.suffix + ".backup").exists()
    assert not (tmp_path / (out.name + ".tmp")).exists()


def test_dry_run_remains_preview_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    in_dir = tmp_path / "snippets"
    _write_snippet(in_dir / "patch.json")
    out = tmp_path / "learning.override.toml"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_learning_apply_cycle.py",
            "--in-dir",
            str(in_dir),
            "--out-file",
            str(out),
            "--dry-run",
        ],
    )
    rc = main()
    captured = capsys.readouterr()
    assert rc == 0
    assert "Dry-run" in captured.out
    assert "portfolio.leverage" in captured.out
    assert "Wrote " not in captured.out
    assert not out.exists()
    assert not list(tmp_path.glob("*.backup"))
    assert not list(tmp_path.glob("*.tmp"))
