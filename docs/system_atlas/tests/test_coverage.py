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
    assert counts["atlas_assigned_paths"] - counts["atlas_baseline_assigned_paths"] == 158
    assert rows["src/ops/ranked_shadow_slot4_pre_tick_v1.py"]["area"] == "STORE"
    assert rows["src/ops/ranked_shadow_slot4_rotation_v1.py"]["area"] == "ACCOUNTING"
    assert rows["scripts/ops/up_paper_ws_depth_v1.py"]["area"] == "DATA"
    assert rows["scripts/ops/up_paper_measurement_v1.py"]["area"] == "EVAL"
    learning = rows["scripts/ops/paper_episode_learning_handoff_v1.py"]
    assert learning["zuordnungsbasis_blob"] != learning["repo_blob"]
    assert learning["zuordnung_bytes"] == "geaendert"
    assert counts["atlas_boundary_records"] == len(doc["routes"]) + len(doc["repo_contracts"])
    assert rows["scripts/ops/inspect_btc_demo_account_v1.py"]["area"] == "VIEW"
    assert rows["tests/ops/test_inspect_btc_demo_account_v1.py"]["role"] == "test"
    assert rows["tests/ops/test_btc_demo_entry_reservation_rehearsal_v1.py"]["role"] == "test"
    assert rows["src/ops/btc_demo_testnet_entry_reservation_v1.py"]["area"] == "BUDGET"
    assert rows["tests/ops/test_btc_demo_testnet_entry_reservation_v1.py"]["role"] == "test"
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


def test_file_connections_keep_the_six_obsidian_directions_and_seven_source_sites():
    bundle = COVERAGE["_load"](ROOT, "development-binding-v1.json")["reviewed_file_connections"]
    assert (
        bundle["obsidian_sha256"]
        == "343195ecb2262e22080cfcbf52d8e7c963c4959fb132a0e4a351357f02ee833b"
    )
    edges = bundle["evidence"]["connections"]
    atlas = "docs/system_atlas/"
    binding = atlas + "source/development-binding-v1.json"
    view = atlas + "generated/BOUNDARIES.md"
    test = atlas + "tests/test_coverage.py"
    assert {
        (edge["source"], edge["target"]): (
            edge["category"],
            [(s["line"], s["end_line"]) for s in edge["sites"]],
        )
        for edge in edges
    } == {
        (atlas + "coverage.py", binding): ("Dateizugriff", [(275, 277)]),
        (atlas + "current_atlas.py", view): ("Dateizugriff", [(518, 520), (557, 559)]),
        (view, binding): ("Dokumentlink", [(573, 573)]),
        (test, "scripts/ops/up_paper_ws_depth_v1.py"): ("Katalogprüfung", [(19, 19)]),
        (test, "scripts/ops/up_paper_measurement_v1.py"): ("Katalogprüfung", [(20, 20)]),
        (test, "scripts/ops/paper_episode_learning_handoff_v1.py"): ("Katalogprüfung", [(21, 23)]),
    }


def test_file_connection_validation_checks_the_original_git_lines():
    from hashlib import sha256

    bundle = COVERAGE["_load"](ROOT, "development-binding-v1.json")["reviewed_file_connections"]
    bundle["evidence"]["connections"][0]["sites"][0]["line"] += 1
    validate = COVERAGE["_validate_file_connections"]
    with pytest.raises(ValueError, match="File connection digest mismatch"):
        validate(ROOT, bundle)
    raw = (json.dumps(bundle["evidence"], indent=2, ensure_ascii=False) + "\n").encode()
    bundle["obsidian_sha256"] = sha256(raw).hexdigest()
    with pytest.raises(ValueError, match="File connection source differs"):
        validate(ROOT, bundle)
