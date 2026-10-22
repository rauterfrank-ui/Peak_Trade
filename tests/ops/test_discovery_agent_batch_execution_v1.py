"""Batch controller regressions. Fixture repos, plus one bounded current slice."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.ops.current_full_stack_semantic_explorer_v1.batch_controller_v1 import (
    BatchStop,
    WorkFile,
    execute_worklist,
    merge_agent_results,
    plan_batches,
    validate_workfiles,
)
from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetV1
from scripts.ops.current_full_stack_semantic_explorer_v1.run_v1 import run_explorer_v1
from tests.ops.test_current_full_stack_semantic_explorer_v1 import _claims, _git

CURRENT = "3a24dd6112ee8f73290f2b98bdaeb82c2d32c5f3"
TREE = "2a2951c5bdca304721ed5bf8f4001e40428bca0e"
REAL_PATHS = (
    "src/notifications/__init__.py",
    "src/notifications/base.py",
    "src/notifications/slack.py",
)


def _repo(tmp_path: Path, sources: dict[str, str]) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    for name, text in sources.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    _git(repo, "init")
    _git(repo, "add", ".")
    _git(
        repo,
        "-c",
        "user.email=explorer@example.com",
        "-c",
        "user.name=explorer",
        "commit",
        "-m",
        "fixture",
    )
    sha = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    return repo, sha, tree


def _files(repo: Path, sha: str, paths: list[str]) -> list[WorkFile]:
    return [WorkFile(path, _git(repo, "rev-parse", f"{sha}:{path}")) for path in paths]


def _chain(count: int) -> str:
    lines = []
    for index in range(count):
        name = f"f{index}"
        if index + 1 == count:
            lines.append(f"def {name}():\n    return 1\n")
        else:
            lines.append(f"def {name}():\n    return f{index + 1}()\n")
    return "\n".join(lines)


def test_batch_under_forty_files_completes(tmp_path: Path) -> None:
    repo, sha, tree = _repo(
        tmp_path,
        {
            "pkg/a.py": "def a():\n    return 1\n",
            "pkg/b.py": "def b():\n    return 1\n",
            "pkg/c.py": "def c():\n    return 1\n",
        },
    )
    files = _files(repo, sha, ["pkg/a.py", "pkg/b.py", "pkg/c.py"])
    assert len(plan_batches(files, 40)) == 1
    result = execute_worklist(repo, sha, tree, "01", "wl", files, tmp_path / "cp")
    assert len(result["files"]) == 3
    assert all(item["status"] == "COMPLETE" for item in result["files"])
    assert all(
        all(item["slice_coverage"][name] == "PASS" for name in ("S1", "S2", "S3", "S4", "S5"))
        for item in result["files"]
    )


def test_node_budget_mid_file_does_not_block_later_file(tmp_path: Path) -> None:
    huge = "\n".join(f"def h{index}():\n    return {index}\n" for index in range(80))
    repo, sha, tree = _repo(
        tmp_path,
        {
            "pkg/a.py": "def a():\n    return 1\n",
            "pkg/b_huge.py": huge,
            "pkg/c.py": "def c():\n    return 2\n",
        },
    )
    files = _files(repo, sha, ["pkg/a.py", "pkg/b_huge.py", "pkg/c.py"])
    result = execute_worklist(
        repo,
        sha,
        tree,
        "01",
        "wl",
        files,
        tmp_path / "cp",
        budget=BudgetV1(max_files=40, max_nodes=40, max_edges=800, max_depth=6, max_seconds=20),
    )
    by_path = {item["path"]: item for item in result["files"]}
    assert by_path["pkg/a.py"]["status"] == "COMPLETE"
    assert by_path["pkg/c.py"]["status"] == "COMPLETE"
    assert by_path["pkg/b_huge.py"]["status"] == "INCOMPLETE"
    assert "NODE_BUDGET" in by_path["pkg/b_huge.py"]["stop_reasons"]
    assert by_path["pkg/b_huge.py"]["slice_coverage"]["S1"] != "PASS"


def test_edge_budget_is_visible_unproven(tmp_path: Path) -> None:
    repo, sha, _tree = _repo(tmp_path, {"pkg/chain.py": _chain(4)})
    result = run_explorer_v1(
        repo,
        sha,
        path_prefixes=("pkg/chain.py",),
        budget=BudgetV1(max_files=40, max_nodes=400, max_edges=1, max_depth=6, max_seconds=20),
    )
    assert result["slices"][2]["status"] == "INCOMPLETE"
    assert any(
        claim["status"] == "UNPROVEN" and "EDGE_BUDGET" in claim["unknowns"]
        for claim in result["slices"][2]["claims"]
    )
    assert result["file_outcomes"][0]["status"] != "COMPLETE"


def test_time_budget_stops_without_complete(tmp_path: Path) -> None:
    repo, sha, tree = _repo(tmp_path, {"pkg/a.py": "def a():\n    return 1\n"})
    files = _files(repo, sha, ["pkg/a.py"])
    calls = {"n": 0}

    def clock() -> float:
        calls["n"] += 1
        return 0.0 if calls["n"] == 1 else 100.0

    result = execute_worklist(
        repo,
        sha,
        tree,
        "01",
        "wl",
        files,
        tmp_path / "cp",
        clock=clock,
    )
    assert result["files"][0]["status"] == "INCOMPLETE"
    assert "TIME_BUDGET" in result["files"][0]["stop_reasons"]
    assert calls["n"] < 50


def test_resume_repeats_only_incomplete_units(tmp_path: Path) -> None:
    repo, sha, tree = _repo(
        tmp_path,
        {"pkg/a.py": "def a():\n    return 1\n", "pkg/b.py": "def b():\n    return 1\n"},
    )
    files = _files(repo, sha, ["pkg/a.py", "pkg/b.py"])
    first = execute_worklist(repo, sha, tree, "01", "wl", files, tmp_path / "cp")
    assert all(item["status"] == "COMPLETE" for item in first["files"])
    kept = next(item for item in first["files"] if item["path"] == "pkg/a.py")
    kept_path = next((tmp_path / "cp" / "files").glob("*.json"))
    # Remove only b by rewriting the directory from the a checkpoint identity.
    stored = {
        path: path.read_text(encoding="utf-8")
        for path in (tmp_path / "cp" / "files").glob("*.json")
    }
    for path, text in stored.items():
        if json.loads(text)["path"] == "pkg/b.py":
            path.unlink()
    before = {
        path: path.read_text(encoding="utf-8")
        for path in (tmp_path / "cp" / "files").glob("*.json")
    }
    second = execute_worklist(repo, sha, tree, "01", "wl", files, tmp_path / "cp", resume=True)
    after = {
        path: path.read_text(encoding="utf-8")
        for path in (tmp_path / "cp" / "files").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8"))["path"] == "pkg/a.py"
    }
    assert before == after
    assert all(item["status"] == "COMPLETE" for item in second["files"])
    assert kept["blob_sha"] == next(
        item["blob_sha"] for item in second["files"] if item["path"] == "pkg/a.py"
    )
    del kept_path


def test_resume_stops_on_commit_or_blob_mismatch(tmp_path: Path) -> None:
    repo, sha, tree = _repo(tmp_path, {"pkg/a.py": "def a():\n    return 1\n"})
    files = _files(repo, sha, ["pkg/a.py"])
    execute_worklist(repo, sha, tree, "01", "wl", files, tmp_path / "cp")
    path = next((tmp_path / "cp" / "files").glob("*.json"))
    document = json.loads(path.read_text(encoding="utf-8"))
    document["commit_sha"] = "0" * 40
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(BatchStop) as raised:
        execute_worklist(repo, sha, tree, "01", "wl", files, tmp_path / "cp", resume=True)
    assert raised.value.reason == "CHECKPOINT_BINDING_MISMATCH"


def test_depth_over_six_is_incomplete(tmp_path: Path) -> None:
    repo, sha, _tree = _repo(tmp_path, {"pkg/deep.py": _chain(8)})
    result = run_explorer_v1(
        repo,
        sha,
        path_prefixes=("pkg/deep.py",),
        budget=BudgetV1(max_files=40, max_nodes=400, max_edges=800, max_depth=6, max_seconds=20),
    )
    truncated = [
        claim
        for claim in _claims(result)
        if claim["predicate"] == "TRANSITIVE_DEPENDS_ON" and "DEPTH_LIMIT" in claim["unknowns"]
    ]
    assert truncated
    assert all(claim["status"] == "UNPROVEN" for claim in truncated)
    assert "INCOMPLETE" in truncated[0]["unknowns"]
    assert result["slices"][2]["status"] == "INCOMPLETE"
    assert result["file_outcomes"][0]["status"] == "INCOMPLETE"


def test_missing_capture_stays_unproven(tmp_path: Path) -> None:
    repo, sha, _tree = _repo(tmp_path, {"pkg/a.py": "def a():\n    return 1\n"})
    result = run_explorer_v1(repo, sha, path_prefixes=("pkg/a.py",))
    missing = [
        claim for claim in result["slices"][3]["claims"] if claim["predicate"] == "RUNTIME_CAPTURE"
    ]
    assert len(missing) == 1
    assert missing[0]["status"] == "UNPROVEN"
    assert "CAPTURE_NOT_SUPPLIED" in missing[0]["unknowns"]


def test_duplicate_or_missing_worklist_stops(tmp_path: Path) -> None:
    repo, sha, tree = _repo(tmp_path, {"pkg/a.py": "def a():\n    return 1\n"})
    present = _files(repo, sha, ["pkg/a.py"])[0]
    with pytest.raises(BatchStop) as duplicate:
        validate_workfiles(
            repo,
            sha,
            tree,
            [present, present],
            observed_commit=sha,
            observed_tree=tree,
        )
    assert duplicate.value.reason == "DUPLICATE_WORKLIST_ENTRY"
    with pytest.raises(BatchStop) as missing:
        validate_workfiles(
            repo,
            sha,
            tree,
            [WorkFile("pkg/missing.py", present.blob_sha)],
            observed_commit=sha,
            observed_tree=tree,
        )
    assert missing.value.reason == "MISSING_WORKLIST_ENTRY"


def test_merge_keeps_every_claim_and_separates_coverage() -> None:
    claim_a = {
        "claim_id": "aaa",
        "predicate": "CALLS",
        "status": "PROVEN",
        "subject": "pkg/a.py::a",
        "object": "pkg/a.py::b",
        "evidence_class": "STATIC",
    }
    claim_b = {
        "claim_id": "bbb",
        "predicate": "RUNTIME_CAPTURE",
        "status": "UNPROVEN",
        "subject": "commit",
        "object": "",
        "evidence_class": "RUNTIME_OBSERVED",
        "unknowns": ["CAPTURE_NOT_SUPPLIED"],
    }
    merged = merge_agent_results(
        [
            {
                "agent_id": "01",
                "files": [
                    {
                        "path": "pkg/a.py",
                        "blob_sha": "1",
                        "status": "COMPLETE",
                        "slice_coverage": {name: "PASS" for name in ("S1", "S2", "S3", "S4", "S5")},
                    }
                ],
                "claims": [claim_a, claim_b],
            },
            {
                "agent_id": "02",
                "files": [
                    {
                        "path": "pkg/b.py",
                        "blob_sha": "2",
                        "status": "INCOMPLETE",
                        "slice_coverage": {
                            "S1": "PASS",
                            "S2": "INCOMPLETE",
                            "S3": "NOT_RUN",
                            "S4": "NOT_RUN",
                            "S5": "NOT_RUN",
                        },
                    }
                ],
                "claims": [claim_a],
            },
        ]
    )
    ids = {claim["claim_id"] for claim in merged["claims"]}
    assert ids == {"aaa", "bbb"}
    assert merged["duplicate_claim_ids"] == ["aaa"]
    assert merged["coverage"] == {
        "physical": 2,
        "semantic": 1,
        "causal": 1,
        "runtime_proven": 0,
        "runtime_unproven": 1,
    }
    assert merged["open_relations"][0]["claim_id"] == "bbb"
    assert "parent_id" not in merged
    assert merged["authority"] == "NONE"


def test_non_module_status_is_isolated_from_sibling_node_budget(tmp_path: Path) -> None:
    huge = "\n".join(f"def h{index}():\n    return {index}\n" for index in range(200))
    repo, sha, tree = _repo(
        tmp_path,
        {
            "notes.txt": "note\n",
            "pkg/a.py": "def a():\n    return 1\n",
            "pkg/z_huge.py": huge,
            "readme.md": "# readme\n",
        },
    )
    names = ["notes.txt", "pkg/a.py", "pkg/z_huge.py", "readme.md"]
    files = _files(repo, sha, names)
    standing = BudgetV1()
    assert (standing.max_files, standing.max_nodes, standing.max_edges, standing.max_depth) == (
        40,
        400,
        800,
        6,
    )
    assert standing.max_seconds == 20.0
    destination = tmp_path / "cp"
    result = execute_worklist(repo, sha, tree, "01", "wl", files, destination)
    by_path = {item["path"]: item for item in result["files"]}
    isolated = {
        "S1": "PASS",
        "S2": "NOT_RUN",
        "S3": "NOT_RUN",
        "S4": "NOT_RUN",
        "S5": "NOT_RUN",
    }
    for path in ("notes.txt", "readme.md"):
        assert by_path[path]["status"] == "INCOMPLETE"
        assert by_path[path]["stop_reasons"] == ["S2_NOT_APPLICABLE"]
        assert by_path[path]["slice_coverage"] == isolated
    assert by_path["pkg/z_huge.py"]["status"] == "INCOMPLETE"
    assert by_path["pkg/z_huge.py"]["stop_reasons"] == ["NODE_BUDGET"]
    assert by_path["pkg/z_huge.py"]["slice_coverage"]["S1"] == "PASS"
    assert by_path["pkg/z_huge.py"]["slice_coverage"]["S2"] == "INCOMPLETE"
    assert by_path["pkg/a.py"]["status"] == "COMPLETE"
    assert by_path["pkg/a.py"]["slice_coverage"] == {
        name: "PASS" for name in ("S1", "S2", "S3", "S4", "S5")
    }
    assert all(item["stop_reasons"] for item in result["files"] if item["status"] == "INCOMPLETE")
    direct = run_explorer_v1(repo, sha, path_prefixes=tuple(names))
    repeated = run_explorer_v1(repo, sha, path_prefixes=tuple(names))
    assert [claim["claim_id"] for claim in _claims(direct)] == [
        claim["claim_id"] for claim in _claims(repeated)
    ]
    assert not any(
        claim["scope"] == "semantic"
        and str(claim["subject"]).startswith(("notes.txt", "readme.md"))
        for claim in _claims(direct)
    )
    before = {
        path.name: path.read_bytes()
        for path in (destination / "files").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8"))["path"] == "pkg/a.py"
    }
    resumed = execute_worklist(repo, sha, tree, "01", "wl", files, destination, resume=True)
    after = {
        path.name: path.read_bytes()
        for path in (destination / "files").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8"))["path"] == "pkg/a.py"
    }
    assert before == after
    resumed_by = {item["path"]: item for item in resumed["files"]}
    assert resumed_by["notes.txt"]["stop_reasons"] == ["S2_NOT_APPLICABLE"]
    assert resumed_by["readme.md"]["stop_reasons"] == ["S2_NOT_APPLICABLE"]
    assert resumed_by["pkg/z_huge.py"]["stop_reasons"] == ["NODE_BUDGET"]
    assert resumed_by["pkg/a.py"]["status"] == "COMPLETE"


def test_reality_check_current_files_survive_node_abort() -> None:
    repo = Path(__file__).resolve().parents[2]
    files = []
    for path in REAL_PATHS:
        proc = subprocess.run(
            ["git", "rev-parse", f"{CURRENT}:{path}"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        files.append(WorkFile(path, proc.stdout.strip()))
    destination = Path("/tmp/bwp_discovery_agent_batch_reality_v1")
    result = execute_worklist(
        repo,
        CURRENT,
        TREE,
        "01",
        "reality",
        files,
        destination,
        budget=BudgetV1(max_files=40, max_nodes=25, max_edges=800, max_depth=6, max_seconds=20),
    )
    by_path = {item["path"]: item for item in result["files"]}
    assert set(by_path) == set(REAL_PATHS)
    assert by_path["src/notifications/__init__.py"]["status"] == "COMPLETE"
    assert by_path["src/notifications/__init__.py"]["slice_coverage"] == {
        name: "PASS" for name in ("S1", "S2", "S3", "S4", "S5")
    }
    for path in ("src/notifications/base.py", "src/notifications/slack.py"):
        assert by_path[path]["status"] == "INCOMPLETE"
        assert by_path[path]["status"] != "COMPLETE"
        assert "NODE_BUDGET" in by_path[path]["stop_reasons"]
    assert all(item["commit_sha"] == CURRENT for item in result["files"])
    assert all(item["tree_sha"] == TREE for item in result["files"])
