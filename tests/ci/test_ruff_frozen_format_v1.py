"""Frozen byte exceptions cannot hide edits or new formatting debt."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from runpy import run_path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
CHECK = run_path(str(ROOT / "scripts/ci/check_ruff_frozen_format_v1.py"))


@pytest.fixture
def frozen_case(tmp_path, monkeypatch):
    model = {"source_commit": "a" * 40, "source_tag": "freeze/test"}
    raw = b"frozen=  1\n"
    rows = []
    for rel in sorted(CHECK["PROTECTED"]):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        rows.append(
            {"path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "reason": "byte guard"}
        )
    manifest = {
        "schema": "peaktrade.ruff_frozen_format_exceptions.v1",
        "authority": "NONE",
        "runtime_authorization_effect": "NONE",
        **model,
        "files": rows,
    }
    for name, value in ((CHECK["MODEL"], model), (CHECK["MANIFEST"], manifest)):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
    for scope in ("tests", "scripts"):
        (tmp_path / scope).mkdir(exist_ok=True)

    def git(root, *args):
        if args[0] == "rev-parse":
            return (model["source_commit"] + "\n").encode()
        assert args[0] == "show"
        return raw

    monkeypatch.setitem(CHECK["frozen_exceptions"].__globals__, "_git", git)
    return tmp_path, manifest


def test_all_frozen_exceptions_are_checked_against_original_bytes(frozen_case):
    root, _ = frozen_case
    assert set(CHECK["frozen_exceptions"](root)) == CHECK["PROTECTED"]


@pytest.mark.parametrize("reseal", [False, True])
def test_changed_frozen_file_fails_even_with_resealed_working_digest(frozen_case, reseal):
    root, manifest = frozen_case
    row = manifest["files"][0]
    raw = b"frozen = 2\n"
    (root / row["path"]).write_bytes(raw)
    if reseal:
        row["sha256"] = hashlib.sha256(raw).hexdigest()
        (root / CHECK["MANIFEST"]).write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="FROZEN_FORMAT_SOURCE_CHANGED"):
        CHECK["frozen_exceptions"](root)


@pytest.mark.parametrize(
    "problem", ["missing", "extra", "duplicate", "traversal", "source", "tag", "authority"]
)
def test_exception_manifest_cannot_widen_or_rebind_the_frozen_scope(frozen_case, problem):
    root, original = frozen_case
    manifest = deepcopy(original)
    if problem == "missing":
        manifest["files"].pop()
    elif problem == "extra":
        manifest["files"].append({**manifest["files"][0], "path": "src/new.py"})
    elif problem == "duplicate":
        manifest["files"][-1] = manifest["files"][0]
    elif problem == "traversal":
        manifest["files"][0]["path"] = "src/../outside.py"
    elif problem == "source":
        manifest["source_commit"] = "b" * 40
    elif problem == "tag":
        manifest["source_tag"] = "moving/main"
    else:
        manifest["authority"] = "GRANTED"
    (root / CHECK["MANIFEST"]).write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        CHECK["frozen_exceptions"](root)


def test_frozen_symlink_is_rejected(frozen_case):
    root, manifest = frozen_case
    path = root / manifest["files"][0]["path"]
    original = root / "original.py"
    original.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(original)
    with pytest.raises(ValueError, match="FROZEN_FORMAT_SOURCE_CHANGED"):
        CHECK["frozen_exceptions"](root)


@pytest.mark.parametrize("scope", ["src", "tests", "scripts"])
def test_actual_formatter_rejects_new_debt_in_every_scan_root(frozen_case, scope):
    root, _ = frozen_case
    ruff = Path(sys.executable).with_name("ruff")
    assert ruff.is_file(), "Project dev dependency ruff is required"
    assert CHECK["check_format"](root, str(ruff)) == 0
    new = root / scope / "new.py"
    new.write_text("value=  2\n")
    assert CHECK["check_format"](root, str(ruff)) == 1
    new.write_text("value = 2\n")
    assert CHECK["check_format"](root, str(ruff)) == 0
