"""Exactly two adapter successors over the unchanged reviewed rotation bundle."""

from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
EXTENSION = POLICY["OPEN_TEST_SLOT_LOSS_PROTECTION_DELTAS"]
ROTATION = POLICY["RESERVED_SLOT_ROTATION_DELTAS"]
PARENT = "6b132fa1bd4788a937243c179cf294658c5389f7"


def seed(root, *, current):
    for path in ROTATION:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(
            (ROOT / path).read_bytes()
            if current
            else subprocess.check_output(["git", "show", PARENT + ":" + path], cwd=ROOT)
        )


@pytest.mark.parametrize("current", [False, True])
def test_reviewed_rotation_parent_and_complete_two_adapter_successor_are_valid(tmp_path, current):
    seed(tmp_path, current=current)
    POLICY["validate_reserved_slot_rotation_bundle"](tmp_path)


@pytest.mark.parametrize("path", tuple(EXTENSION))
def test_half_applied_loss_exit_adapter_bundle_is_rejected(tmp_path, path):
    seed(tmp_path, current=True)
    (tmp_path / path).write_bytes(
        subprocess.check_output(["git", "show", PARENT + ":" + path], cwd=ROOT)
    )
    with pytest.raises(ValueError, match="REVIEWED_BUNDLE_REQUIRED"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path)


@pytest.mark.parametrize("path", tuple(EXTENSION))
def test_unknown_loss_exit_adapter_body_is_rejected(tmp_path, path):
    seed(tmp_path, current=True)
    with (tmp_path / path).open("a") as f:
        f.write("\n# unreviewed successor\n")
    with pytest.raises(ValueError, match="REVIEWED_BUNDLE_REQUIRED"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path)


def test_original_rotation_parent_cannot_be_redefined(tmp_path, monkeypatch):
    seed(tmp_path, current=True)
    path = next(iter(EXTENSION))
    monkeypatch.setitem(EXTENSION, path, ("0" * 64, EXTENSION[path][1]))
    with pytest.raises(ValueError, match="LOSS_PROTECTION_PARENT_INVALID"):
        POLICY["validate_reserved_slot_rotation_bundle"](tmp_path)
