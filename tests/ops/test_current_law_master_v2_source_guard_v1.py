"""Exercise the actual source guard against changes in isolated Git fixtures."""

from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD = run_path(str(ROOT / "tests/ops/test_current_law_impact_map_v1.py"))[
    "test_master_v2_unchanged_against_accepted_current_source"
]


def git(root, *args):
    return subprocess.check_output(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "user.name=Offline source-guard fixture",
            "-c",
            "user.email=offline-fixture@example.invalid",
            *args,
        ],
        cwd=root,
        text=True,
    ).strip()


@pytest.fixture
def source_guard(tmp_path, monkeypatch):
    git(tmp_path, "init", "--quiet")
    core = tmp_path / "src/trading/master_v2/core.py"
    core.parent.mkdir(parents=True)
    core.write_text("accepted = True\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "--quiet", "-m", "Synthetic accepted source")
    accepted = git(tmp_path, "rev-parse", "HEAD")
    # Isolate only the source-diff boundary. The real guard separately executes
    # its original frozen-tag/Atlas binding against the real checkout.
    monkeypatch.setitem(GUARD.__globals__, "REPO", tmp_path)
    monkeypatch.setitem(GUARD.__globals__, "ACCEPTED_MASTER_V2_SOURCE", accepted)
    monkeypatch.setitem(GUARD.__globals__, "_frozen_source", lambda: accepted)
    return tmp_path, core


@pytest.mark.parametrize(
    "change",
    [
        "none",
        "outside_core",
        "unstaged",
        "staged",
        "committed",
        "deleted",
        "added_staged",
        "untracked",
        "staged_with_original_working_file",
    ],
)
def test_source_guard_preserves_fixed_baseline_and_detects_drift(source_guard, change):
    root, core = source_guard
    if change == "outside_core":
        (root / "outside.txt").write_text("outside source-guard scope\n")
        git(root, "add", "outside.txt")
        git(root, "commit", "--quiet", "-m", "Unrelated committed source")
    elif change in {"unstaged", "staged", "committed", "staged_with_original_working_file"}:
        original = core.read_text()
        core.write_text("accepted = False\n")
        if change != "unstaged":
            git(root, "add", ".")
        if change == "committed":
            git(root, "commit", "--quiet", "-m", "Unaccepted Core change")
        if change == "staged_with_original_working_file":
            core.write_text(original)
    elif change == "deleted":
        core.unlink()
    elif change in {"added_staged", "untracked"}:
        (core.parent / "new.py").write_text("unaccepted = True\n")
        if change == "added_staged":
            git(root, "add", ".")
    if change in {"none", "outside_core"}:
        GUARD()
    else:
        with pytest.raises(AssertionError):
            GUARD()
