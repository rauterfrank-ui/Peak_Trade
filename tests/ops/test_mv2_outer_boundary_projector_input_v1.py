"""WP1 fail-closed input and source-admission tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
    ProjectorRequestV1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.run_v1 import (
    run_mv2_outer_boundary_projector_v1,
)

REPO = Path(__file__).resolve().parents[2]
PIN_COMMIT = "7628005ae495c115ff341d32fa932b7f4642f456"
PIN_TREE = "e652f8d7b86c469311a068c34b0fb3f708c87d73"
WRONG_TREE = "0000000000000000000000000000000000000000"


def test_wrong_git_tree_fails_closed() -> None:
    request = ProjectorRequestV1(commit=PIN_COMMIT, tree=WRONG_TREE)
    with pytest.raises(ProjectorFailClosedV1) as caught:
        run_mv2_outer_boundary_projector_v1(request, repo_root=REPO)
    assert caught.value.code == "TREE_MISMATCH"


def test_worktree_read_and_ratification_and_historical_admission_fail_closed() -> None:
    with pytest.raises(ProjectorFailClosedV1) as worktree:
        run_mv2_outer_boundary_projector_v1(
            ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE, read_worktree=True),
            repo_root=REPO,
        )
    assert worktree.value.code == "WORKTREE_READ_REJECTED"
    with pytest.raises(ProjectorFailClosedV1) as historical:
        run_mv2_outer_boundary_projector_v1(
            ProjectorRequestV1(
                commit=PIN_COMMIT,
                tree=PIN_TREE,
                treat_historical_graph_as_current=True,
            ),
            repo_root=REPO,
        )
    assert historical.value.code == "HISTORICAL_GRAPH_CURRENT_PROOF_REJECTED"
    with pytest.raises(ProjectorFailClosedV1) as ratification:
        run_mv2_outer_boundary_projector_v1(
            ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE, request_ratification=True),
            repo_root=REPO,
        )
    assert ratification.value.code == "RATIFICATION_REQUEST_REJECTED"


def test_depth_other_than_one_fails_closed() -> None:
    with pytest.raises(ProjectorFailClosedV1) as caught:
        run_mv2_outer_boundary_projector_v1(
            ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE, max_depth=2),
            repo_root=REPO,
        )
    assert caught.value.code == "DEPTH"


def test_output_inside_repo_fails_closed(tmp_path: Path) -> None:
    inside = REPO / "tests" / "ops" / "_mv2_projector_should_not_write.json"
    request = ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE)
    with pytest.raises(ProjectorFailClosedV1) as caught:
        run_mv2_outer_boundary_projector_v1(request, repo_root=REPO, output_path=inside)
    assert caught.value.code == "OUTPUT_INSIDE_REPO"
    assert not inside.exists()
    outside = tmp_path / "unused.json"
    assert not outside.exists()
