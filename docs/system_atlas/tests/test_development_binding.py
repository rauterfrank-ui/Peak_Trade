"""Exact development deltas preserve the frozen baseline and reject drift."""

import json
from pathlib import Path
from runpy import run_path

import pytest

ATLAS = run_path(str(Path(__file__).resolve().parents[1] / "current_atlas.py"))


def _case(tmp_path, monkeypatch):
    script = ATLAS["validate_development_binding"]
    monkeypatch.setitem(script.__globals__, "git", lambda *a: b"")
    root = tmp_path
    p = root / "src/changed.py"
    p.parent.mkdir()
    p.write_text("value = 2\n")
    old = {"src/changed.py": {"sha256": "a" * 64}}
    binding = {
        "schema": "peaktrade.atlas_development_binding.v1",
        "authority": "NONE",
        "runtime_authorization_effect": "NONE",
        "frozen_source_commit": "f" * 40,
        "development_parent_commit": "b" * 40,
        "files": [
            {
                "path": "src/changed.py",
                "before_sha256": "a" * 64,
                "sha256": ATLAS["digest"](p.read_bytes()),
            }
        ],
    }
    manifest = root / ATLAS["DEVELOPMENT_BINDING"]
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(binding))
    return script, root, old, binding, manifest


def test_exact_delta_is_bound_separately_from_frozen_inventory(tmp_path, monkeypatch):
    check, root, old, _, _ = _case(tmp_path, monkeypatch)
    result = check(root, {"source_commit": "f" * 40}, old, ["src/changed.py"], [], None)
    assert result["src/changed.py"]["before_sha256"] == old["src/changed.py"]["sha256"]
    assert old["src/changed.py"]["sha256"] == "a" * 64


@pytest.mark.parametrize(
    "problem",
    [
        "before",
        "after",
        "missing_entry",
        "traversal",
        "duplicate",
        "source_ref",
        "authority",
        "parent",
    ],
)
def test_unbound_or_inconsistent_development_is_rejected(tmp_path, monkeypatch, problem):
    check, root, old, binding, manifest = _case(tmp_path, monkeypatch)
    row = binding["files"][0]
    if problem == "before":
        row["before_sha256"] = "0" * 64
    elif problem == "after":
        row["sha256"] = "0" * 64
    elif problem == "missing_entry":
        binding["files"] = []
    elif problem == "traversal":
        row["path"] = "src/../changed.py"
    elif problem == "duplicate":
        binding["files"].append(dict(row))
    elif problem == "source_ref":
        binding["frozen_source_commit"] = "0" * 40
    elif problem == "authority":
        binding["authority"] = "EXECUTION"
    elif problem == "parent":
        binding["development_parent_commit"] = "unknown"
    manifest.write_text(json.dumps(binding))
    with pytest.raises(AssertionError):
        check(root, {"source_commit": "f" * 40}, old, ["src/changed.py"], [], None)


def test_an_additional_unbound_source_is_rejected(tmp_path, monkeypatch):
    check, root, old, _, _ = _case(tmp_path, monkeypatch)
    with pytest.raises(AssertionError, match="UNSCOPED_CHANGE"):
        check(root, {"source_commit": "f" * 40}, old, ["src/changed.py"], ["src/extra.py"], None)
