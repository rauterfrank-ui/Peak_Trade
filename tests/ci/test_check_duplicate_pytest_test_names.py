"""Contract tests for scripts/ci/check_duplicate_pytest_test_names.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "check_duplicate_pytest_test_names.py"


def _run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_checker_passes_on_repo_with_allowlist() -> None:
    proc = _run_script()
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr == ""


def test_checker_fails_on_duplicate_without_allowlist(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_dup.py").write_text(
        "def test_same() -> None:\n    pass\n\ndef test_same() -> None:\n    pass\n",
        encoding="utf-8",
    )
    proc = _run_script(
        "--repo-root",
        str(tmp_path),
        "--paths",
        "tests",
        "--no-allowlist",
    )
    assert proc.returncode == 1
    assert "duplicate" in proc.stderr.lower()
    assert "test_same" in proc.stderr


def test_checker_stale_allowlisted_name_fails(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_dup.py").write_text(
        "def test_same() -> None:\n    pass\n\n"
        "def test_same() -> None:\n    pass\n\n"
        "def test_only_once() -> None:\n    pass\n",
        encoding="utf-8",
    )
    cfg = tmp_path / "config" / "ci"
    cfg.mkdir(parents=True)
    allow = {
        "version": 1,
        "allowed": {
            "tests/test_dup.py": {
                "reason": "stale allowlist name should fail integrity",
                "names": ["test_same", "test_only_once"],
            },
        },
    }
    (cfg / "duplicate_test_names_allowlist.json").write_text(
        json.dumps(allow),
        encoding="utf-8",
    )
    proc = _run_script(
        "--repo-root",
        str(tmp_path),
        "--paths",
        "tests",
        "--allowlist",
        str(cfg / "duplicate_test_names_allowlist.json"),
    )
    assert proc.returncode == 1
    assert "integrity" in proc.stderr.lower()
    assert "test_only_once" in proc.stderr


def test_checker_missing_allowlisted_file_fails_under_scan_scope(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    cfg = tmp_path / "config" / "ci"
    cfg.mkdir(parents=True)
    allow = {
        "version": 1,
        "allowed": {
            "tests/test_missing.py": {
                "reason": "missing path under scope",
                "names": ["test_x"],
            },
        },
    }
    (cfg / "duplicate_test_names_allowlist.json").write_text(
        json.dumps(allow),
        encoding="utf-8",
    )
    proc = _run_script(
        "--repo-root",
        str(tmp_path),
        "--paths",
        "tests",
        "--allowlist",
        str(cfg / "duplicate_test_names_allowlist.json"),
    )
    assert proc.returncode == 1
    assert "integrity" in proc.stderr.lower()
    assert "missing" in proc.stderr.lower()


def test_checker_scoped_paths_skip_off_scope_allowlist_integrity(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    (tests / "a").mkdir(parents=True)
    (tests / "b").mkdir(parents=True)
    (tests / "a" / "test_fine.py").write_text(
        "def test_same() -> None:\n    pass\n\ndef test_same() -> None:\n    pass\n",
        encoding="utf-8",
    )
    (tests / "b" / "test_stale.py").write_text(
        "def test_only_once() -> None:\n    pass\n",
        encoding="utf-8",
    )
    cfg = tmp_path / "config" / "ci"
    cfg.mkdir(parents=True)
    allow = {
        "version": 1,
        "allowed": {
            "tests/a/test_fine.py": {
                "reason": "in-scope duplicate",
                "names": ["test_same"],
            },
            "tests/b/test_stale.py": {
                "reason": "would fail integrity if scanned (name not duplicated)",
                "names": ["test_only_once"],
            },
        },
    }
    (cfg / "duplicate_test_names_allowlist.json").write_text(
        json.dumps(allow),
        encoding="utf-8",
    )
    proc = _run_script(
        "--repo-root",
        str(tmp_path),
        "--paths",
        "tests/a",
        "--allowlist",
        str(cfg / "duplicate_test_names_allowlist.json"),
    )
    assert proc.returncode == 0, proc.stderr


def test_checker_allows_listed_duplicates(tmp_path: Path) -> None:
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_dup.py").write_text(
        "def test_same() -> None:\n    pass\n\ndef test_same() -> None:\n    pass\n",
        encoding="utf-8",
    )
    cfg = tmp_path / "config" / "ci"
    cfg.mkdir(parents=True)
    allow = {
        "version": 1,
        "allowed": {
            "tests/test_dup.py": {
                "reason": "fixture duplicate for allowlist contract",
                "names": ["test_same"],
            },
        },
    }
    (cfg / "duplicate_test_names_allowlist.json").write_text(
        json.dumps(allow),
        encoding="utf-8",
    )
    proc = _run_script(
        "--repo-root",
        str(tmp_path),
        "--paths",
        "tests",
        "--allowlist",
        str(cfg / "duplicate_test_names_allowlist.json"),
    )
    assert proc.returncode == 0, proc.stderr


def test_checker_malformed_allowlist_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    proc = _run_script("--allowlist", str(bad))
    assert proc.returncode == 2
    assert "allowlist" in proc.stderr.lower()


def test_checker_wrong_allowlist_version_exits_2(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"version": 99, "allowed": {}}', encoding="utf-8")
    proc = _run_script("--allowlist", str(bad))
    assert proc.returncode == 2
