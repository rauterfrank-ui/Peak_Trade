"""The Atlas documents repository placement without promoting historical edges."""

from pathlib import Path
from runpy import run_path

import pytest


ROOT = Path(__file__).resolve().parents[3]
COVERAGE = run_path(str(ROOT / "docs/system_atlas/coverage.py"))


def test_every_path_is_placed_and_current_research_boundaries_keep_their_scope():
    model = COVERAGE["_load"](ROOT, "current-model.json")
    doc, rows, routes, signals, counts = COVERAGE["load_coverage"](ROOT, model)
    assert counts["atlas_assigned_paths"] == len(rows)
    assert counts["atlas_boundary_records"] == len(doc["routes"]) + len(doc["repo_contracts"])
    assert len(signals) == 58

    assert routes["GRENZE-P26"]["status"] == "retired_direct_path"
    assert routes["HANDOFF-H098"]["status"] == "historical_claim"
    assert routes["REPO-7241-SL-OPT"]["from"] == "SL"
    assert routes["REPO-7241-OPT-EVAL"]["to"] == "EVAL"
    assert rows[COVERAGE["CORE_CATALOG"]]["area"] == "CORE"
    assert rows["src/experiments/offline_ddo_research_cycle_v1.py"]["area"] == "OPT"
    assert (
        rows["src/evaluation/golden_vectors/integration/offline_native_learning_replay_v1.py"][
            "area"
        ]
        == "EVAL"
    )


def test_unassigned_checkout_artifact_is_reported_in_strict_mode(monkeypatch):
    model = COVERAGE["_load"](ROOT, "current-model.json")
    load = COVERAGE["load_coverage"]
    git = load.__globals__["_git"]

    def with_unmapped_file(root, *args):
        result = git(root, *args)
        return result + b"new-artefact\0" if args[0] == "ls-files" else result

    monkeypatch.setitem(load.__globals__, "_git", with_unmapped_file)
    with pytest.raises(ValueError, match="Checkout coverage drift: .*new-artefact"):
        load(ROOT, model, strict=True)
