"""The Atlas documents repository placement without promoting historical edges."""

import json
from pathlib import Path
from runpy import run_path

import pytest


ROOT = Path(__file__).resolve().parents[3]
COVERAGE = run_path(str(ROOT / "docs/system_atlas/coverage.py"))


def test_every_path_is_placed_and_current_research_boundaries_keep_their_scope():
    model = COVERAGE["_load"](ROOT, "current-model.json")
    doc, rows, routes, signals, counts = COVERAGE["load_coverage"](ROOT, model)
    assert counts["atlas_assigned_paths"] == len(rows)
    assert counts["atlas_assigned_paths"] - counts["atlas_baseline_assigned_paths"] == 146
    assert rows["scripts/ops/up_paper_ws_depth_v1.py"]["area"] == "DATA"
    assert rows["scripts/ops/up_paper_measurement_v1.py"]["area"] == "EVAL"
    learning = rows["scripts/ops/paper_episode_learning_handoff_v1.py"]
    assert learning["zuordnungsbasis_blob"] != learning["repo_blob"]
    assert learning["zuordnung_bytes"] == "geaendert"
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


def test_obsidian_comparison_preserves_secondary_areas_and_rejects_duplicate_paths(tmp_path):
    row = {"path": "example", "area": "DATA", "related_areas": ["EVAL"], "repo_blob": "a" * 40}
    rows = {"example": row}
    register = tmp_path / "register.jsonl"
    source = {
        "blob": row["repo_blob"],
        "area": "DATA",
        "related_areas": ["EVAL"],
        "path": "example",
    }
    line = json.dumps(source) + "\n"
    register.write_text(line)
    assert COVERAGE["compare_obsidian"](rows, register)["obsidian_matching_records"] == 1
    register.write_text(line + line)
    with pytest.raises(ValueError, match="Duplicate path"):
        COVERAGE["compare_obsidian"](rows, register)
    register.write_text(json.dumps({**source, "related_areas": []}))
    with pytest.raises(ValueError, match="Obsidian assignment differs: example"):
        COVERAGE["compare_obsidian"](rows, register)
