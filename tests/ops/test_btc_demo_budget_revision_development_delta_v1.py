"""Exact read-only budget-source successor; other bodies remain rejected."""

import ast
import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
POLICY = run_path(str(ROOT / "docs/system_atlas/policy_projection.py"))
ATLAS = run_path(str(ROOT / "docs/system_atlas/current_atlas.py"))
LAW = json.loads((ROOT / POLICY["LAW"]).read_bytes())
PATH = next(iter(POLICY["BTC_DEMO_BUDGET_REVISION_READ_DELTAS"]))
BINDING = ROOT / "docs/system_atlas/source/development-binding-v1.json"
BASE = "f52d52a6e0cd47cbec048adba9e9ff8283f9f693"


@pytest.mark.parametrize("parent", [False, True])
def test_original_reader_accepts_exact_successor_and_previous_budget_source(monkeypatch, parent):
    read = Path.read_bytes
    previous = subprocess.check_output(["git", "show", BASE + ":" + PATH], cwd=ROOT)

    def source(path):
        raw = read(path)
        if parent and path == ROOT / PATH:
            return previous
        if parent and path == BINDING:
            doc = json.loads(raw)
            for row in doc["files"]:
                if row["path"] == PATH:
                    row["sha256"] = hashlib.sha256(previous).hexdigest()
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", source)
    assert POLICY["validate_policy_inventory"](ROOT, LAW)["runtime_effect_inferred"] is False


@pytest.mark.parametrize(
    "fault", ["unreviewed", "unreviewed_rehashed", "missing_row", "wrong_parent", "wrong_digest"]
)
def test_unreviewed_budget_body_or_incorrect_binding_remains_rejected(monkeypatch, fault):
    read = Path.read_bytes
    altered = read(ROOT / PATH) + b"\n# another unreviewed budget implementation\n"

    def source(path):
        raw = read(path)
        if path == ROOT / PATH and fault.startswith("unreviewed"):
            return altered
        if path == BINDING:
            doc = json.loads(raw)
            if fault == "missing_row":
                doc["files"] = [row for row in doc["files"] if row["path"] != PATH]
            for row in doc["files"]:
                if row["path"] == PATH:
                    if fault == "unreviewed_rehashed":
                        row["sha256"] = hashlib.sha256(altered).hexdigest()
                    elif fault == "wrong_parent":
                        row["before_sha256"] = "0" * 64
                    elif fault == "wrong_digest":
                        row["sha256"] = "0" * 64
            return json.dumps(doc).encode()
        return raw

    monkeypatch.setattr(Path, "read_bytes", source)
    if fault.startswith("unreviewed"):
        with pytest.raises(ValueError, match="DOUBLE_PLAY_POLICY_REVIEWED_BUNDLE_REQUIRED"):
            POLICY["validate_policy_inventory"](ROOT, LAW)
    else:
        # This budget source is an Atlas development source and a member of
        # the complete Double Play bundle, not an individual frozen policy row.
        reasons = {
            "missing_row": "UNSCOPED_CHANGE",
            "wrong_parent": "DEVELOPMENT_BASE_MISMATCH",
            "wrong_digest": "DEVELOPMENT_SOURCE_DRIFT",
        }
        with pytest.raises(AssertionError, match=reasons[fault]):
            ATLAS["validate"](ROOT)


def test_budget_source_diff_only_adds_read_only_committed_revision_accessor():
    before = ast.parse(subprocess.check_output(["git", "show", BASE + ":" + PATH], cwd=ROOT))
    after = ast.parse((ROOT / PATH).read_bytes())
    cls = next(
        node
        for node in after.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PortfolioCapitalReservationBudgetOwnerV1"
    )
    accessor = next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == "durable_revision_ref_v1"
    )
    assert not any(
        isinstance(node, (ast.Assign, ast.AugAssign, ast.Delete)) for node in ast.walk(accessor)
    )
    cls.body.remove(accessor)
    assert ast.dump(before) == ast.dump(after)
