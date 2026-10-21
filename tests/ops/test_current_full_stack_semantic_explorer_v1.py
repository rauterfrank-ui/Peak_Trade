"""Offline regressions for the five explorer slices. Fixture repo only."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetV1
from scripts.ops.current_full_stack_semantic_explorer_v1.run_v1 import run_explorer_v1

MOD_A = """\
AUTHORITY = "NONE"
DECISION_AUTHORITY = "NONE"
EXECUTION_AUTHORITY = "NONE"
SAFETY_AUTHORITY = "NONE"

def bar(x):
    return x

def foo(x):
    return bar(x)

def dyn(obj, name):
    getattr(obj, name)
    return obj.unknown()

def boom():
    raise ValueError("x")

def persist(path):
    open(path, "w")

if __name__ == "__main__":
    foo(1)
"""

MOD_B = """\
from sample_pkg.mod_a import foo

class Box:
    def get(self):
        return 1

def caller():
    return foo(1)
"""

MOD_C = """\
AUTHORITY = "OWNER"
"""

MOD_D = """\
SAFETY_AUTHORITY = "NONE"
"""

PARENT_NAMED = """\
def isolated():
    return 1
"""

MOD_E = """\
def ping():
    return 1

def pong():
    return ping()
"""

CONTRACT_A = {
    "subject": "sample_pkg/mod_a.py",
    "authority": "NONE",
    "decision_authority": "NONE",
    "execution_authority": "NONE",
    "safety_authority": "NONE",
}

CONTRACT_C = {
    "subject": "sample_pkg/mod_c.py",
    "authority": "NONE",
}


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _fixture(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    pkg = repo / "sample_pkg"
    pkg.mkdir(parents=True)
    (pkg / "mod_a.py").write_text(MOD_A, encoding="utf-8")
    (pkg / "mod_b.py").write_text(MOD_B, encoding="utf-8")
    (pkg / "mod_c.py").write_text(MOD_C, encoding="utf-8")
    (pkg / "mod_d.py").write_text(MOD_D, encoding="utf-8")
    (pkg / "parent_safety_guardian.py").write_text(PARENT_NAMED, encoding="utf-8")
    (pkg / "mod_e.py").write_text(MOD_E, encoding="utf-8")
    contracts = repo / "contracts"
    contracts.mkdir()
    (contracts / "mod_a.json").write_text(json.dumps(CONTRACT_A), encoding="utf-8")
    (contracts / "mod_c.json").write_text(json.dumps(CONTRACT_C), encoding="utf-8")
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
    return repo, _git(repo, "rev-parse", "HEAD")


def _claims(result: dict) -> list[dict]:
    found = []
    for item in result["slices"]:
        found.extend(item["claims"])
    return found


def _budget() -> BudgetV1:
    return BudgetV1(max_files=30, max_nodes=800, max_edges=800, max_depth=6, max_seconds=20)


def test_s1_commit_binding_and_symbols(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=_budget())
    s1 = result["slices"][0]
    assert s1["slice_id"] == "S1"
    assert s1["status"] == "PASS"
    assert result["commit_sha"] == sha
    assert all(claim["commit_sha"] == sha for claim in _claims(result))
    defined = {claim["subject"] for claim in s1["claims"] if claim["predicate"] == "DEFINES"}
    assert "sample_pkg/mod_a.py::foo" in defined
    assert "sample_pkg/mod_b.py::Box.get" in defined
    assert any(claim["predicate"] == "ENTRYPOINT" for claim in s1["claims"])


def test_s2_static_calls_and_dynamic_targets(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=_budget())
    claims = _claims(result)
    calls = [
        claim
        for claim in claims
        if claim["predicate"] == "CALLS"
        and claim["subject"] == "sample_pkg/mod_a.py::foo"
        and claim["object"] == "sample_pkg/mod_a.py::bar"
    ]
    assert len(calls) == 1
    assert calls[0]["status"] == "PROVEN"
    assert calls[0]["evidence_class"] == "STATIC"
    dynamic = [claim for claim in claims if claim["predicate"] == "DYNAMIC_TARGET"]
    assert dynamic
    assert all(claim["status"] == "UNPROVEN" for claim in dynamic)
    assert any(
        claim["predicate"] == "PERSISTS" and claim["subject"].endswith("::persist")
        for claim in claims
    )
    assert any(
        claim["predicate"] == "RAISES" and claim["object"] == "ValueError" for claim in claims
    )


def test_s3_authority_requires_agreeing_code_and_contract(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=_budget())
    claims = _claims(result)
    proven = [
        claim
        for claim in claims
        if claim["predicate"] == "DECISION_AUTHORITY" and claim["status"] == "PROVEN"
    ]
    assert len(proven) == 1
    assert proven[0]["subject"] == "sample_pkg/mod_a.py"
    assert proven[0]["object"] == "NONE"
    assert any(ref.endswith(".json") for ref in proven[0]["evidence_refs"])
    assert any(".py:" in ref for ref in proven[0]["evidence_refs"])
    mismatch = [
        claim
        for claim in claims
        if claim["subject"] == "sample_pkg/mod_c.py" and claim["predicate"] == "AUTHORITY"
    ]
    assert mismatch[0]["status"] == "UNPROVEN"
    assert "CONTRADICTION" in mismatch[0]["unknowns"]
    code_only = [
        claim
        for claim in claims
        if claim["subject"] == "sample_pkg/mod_d.py" and claim["predicate"] == "SAFETY_AUTHORITY"
    ]
    assert code_only[0]["status"] == "UNPROVEN"
    assert "CODE_WITHOUT_CONTRACT" in code_only[0]["unknowns"]
    assert not any(
        claim["status"] == "PROVEN"
        and "parent_safety" in claim["subject"]
        and "AUTHORITY" in claim["predicate"]
        for claim in claims
    )
    assert any(
        claim["predicate"] == "TRANSITIVE_DEPENDS_ON"
        and claim["subject"] == "sample_pkg/mod_b.py::caller"
        and claim["object"] == "sample_pkg/mod_a.py::bar"
        and claim["status"] == "PROVEN"
        for claim in claims
    )


def test_s4_wrong_revision_is_not_proof(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    capture = tmp_path / "wrong.json"
    capture.write_text(
        json.dumps(
            {
                "commit_sha": "0" * 40,
                "identity": "cap-1",
                "provenance": "offline-fixture",
                "observations": [
                    {
                        "subject": "sample_pkg/mod_a.py::foo",
                        "predicate": "CALLS",
                        "object": "sample_pkg/mod_a.py::bar",
                        "evidence_ref": "capture#0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    result = run_explorer_v1(repo, sha, capture_path=capture, budget=_budget())
    runtime = [
        claim
        for claim in result["slices"][3]["claims"]
        if claim["evidence_class"] == "RUNTIME_OBSERVED" and claim["status"] == "PROVEN"
    ]
    assert runtime == []
    assert any("REVISION_MISMATCH" in claim["unknowns"] for claim in result["slices"][3]["claims"])


def test_s4_matching_revision_stays_separate_from_static(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    capture = _matching_capture(tmp_path, sha)
    result = run_explorer_v1(repo, sha, capture_path=capture, budget=_budget())
    claims = _claims(result)
    static = [
        claim
        for claim in claims
        if claim["predicate"] == "CALLS" and claim["subject"] == "sample_pkg/mod_a.py::foo"
    ]
    assert static[0]["evidence_class"] == "STATIC"
    assert static[0]["status"] == "PROVEN"
    observed = [
        claim
        for claim in claims
        if claim["predicate"] == "RUNTIME_OBSERVES" and claim["status"] == "PROVEN"
    ]
    assert observed
    assert all(claim["evidence_class"] == "RUNTIME_OBSERVED" for claim in observed)
    correlated = [
        claim
        for claim in claims
        if claim["predicate"] == "CORRELATES" and claim["status"] == "PROVEN"
    ]
    assert correlated
    assert "STATIC_NOT_UPGRADED" in correlated[0]["unknowns"]


def test_s5_layers_follow_calls_not_parent_names(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=_budget())
    claims = _claims(result)
    members = [
        claim["object"]
        for claim in claims
        if claim["predicate"] == "CALL_GROUP_MEMBER" and claim["status"] == "PROVEN"
    ]
    assert all(
        claim["subject"].startswith("call_group:")
        for claim in claims
        if claim["predicate"] == "CALL_GROUP_MEMBER"
    )
    assert "sample_pkg/parent_safety_guardian.py::isolated" not in members
    assert any(
        claim["predicate"] == "UNASSIGNED"
        and claim["subject"] == "sample_pkg/parent_safety_guardian.py::isolated"
        and claim["status"] == "UNPROVEN"
        for claim in claims
    )
    assert any(
        claim["predicate"] == "CALL_GROUP_LINK" and claim["status"] == "PROVEN" for claim in claims
    )
    assert not any(claim["subject"].startswith("PARENT_") for claim in claims)
    meanings = [
        claim
        for claim in claims
        if claim["predicate"] == "FUNCTION_MEANING" and claim["subject"].endswith("::isolated")
    ]
    assert meanings[0]["status"] == "UNPROVEN"


def test_budget_abort_is_incomplete(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    result = run_explorer_v1(repo, sha, budget=BudgetV1(max_files=1, max_seconds=20))
    assert result["run_status"] == "INCOMPLETE"
    assert result["run_status"] != "PASS"
    assert result["slices"][0]["status"] == "INCOMPLETE"
    assert any(row["status"] == "NOT_STARTED" for row in result["file_outcomes"])
    admitted = [row for row in result["file_outcomes"] if row["slice_coverage"]["S1"] == "PASS"]
    assert admitted
    assert result["slices"][1]["status"] == "PASS"


def test_determinism_ignores_uncommitted_worktree_edits(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    cache = tmp_path / "cache"
    first = run_explorer_v1(repo, sha, cache_dir=cache, budget=_budget())
    second = run_explorer_v1(repo, sha, cache_dir=cache, budget=_budget())
    assert first == second
    target = repo / "sample_pkg" / "mod_a.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# uncommitted\n", encoding="utf-8")
    third = run_explorer_v1(repo, sha, cache_dir=cache, budget=_budget())
    assert third == first
    assert list(cache.glob("run-*.json"))


def test_e2e_five_slices_offline(tmp_path: Path) -> None:
    repo, sha = _fixture(tmp_path)
    capture = _matching_capture(tmp_path, sha)
    result = run_explorer_v1(repo, sha, capture_path=capture, budget=_budget())
    assert result["run_status"] == "PASS"
    assert result["external_effects"] == 0
    assert result["tool_authority"] == "NONE"
    assert [item["slice_id"] for item in result["slices"]] == ["S1", "S2", "S3", "S4", "S5"]
    assert all(item["status"] == "PASS" for item in result["slices"])
    assert all(item["claims"] for item in result["slices"])


def _matching_capture(tmp_path: Path, sha: str) -> Path:
    path = tmp_path / "match.json"
    path.write_text(
        json.dumps(
            {
                "commit_sha": sha,
                "identity": "cap-match",
                "provenance": "offline-fixture",
                "observations": [
                    {
                        "subject": "sample_pkg/mod_a.py::foo",
                        "predicate": "CALLS",
                        "object": "sample_pkg/mod_a.py::bar",
                        "evidence_ref": "capture#0",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path
