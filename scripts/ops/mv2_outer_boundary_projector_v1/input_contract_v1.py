"""Fail-closed input contract for the outer-boundary projector."""

from __future__ import annotations

from dataclasses import dataclass

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    MAX_OUTER_DEPTH,
    SCOPE,
    TARGET_IDENTITY,
)


class ProjectorFailClosedV1(Exception):
    """The pinned input is unusable. No report is ratified."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


def _hex40(value: str) -> bool:
    return len(value) == 40 and all(char in "0123456789abcdef" for char in value)


@dataclass(frozen=True)
class ProjectorRequestV1:
    """Pinned-tree request. Evidence is read from git objects of ``commit``."""

    commit: str
    tree: str
    target_identity: str = TARGET_IDENTITY
    scope: str = SCOPE
    max_depth: int = MAX_OUTER_DEPTH
    read_worktree: bool = False
    treat_historical_graph_as_current: bool = False
    request_ratification: bool = False
    extra_candidates: tuple[dict[str, object], ...] = ()
    extra_edges: tuple[dict[str, object], ...] = ()
    extra_external_partners: tuple[dict[str, object], ...] = ()


def validate_request_v1(request: ProjectorRequestV1) -> None:
    if not _hex40(request.commit):
        raise ProjectorFailClosedV1("COMMIT_FORMAT", request.commit)
    if not _hex40(request.tree):
        raise ProjectorFailClosedV1("TREE_FORMAT", request.tree)
    if request.target_identity != TARGET_IDENTITY:
        raise ProjectorFailClosedV1("TARGET_IDENTITY", request.target_identity)
    if request.scope != SCOPE:
        raise ProjectorFailClosedV1("SCOPE", request.scope)
    if request.max_depth != MAX_OUTER_DEPTH:
        raise ProjectorFailClosedV1("DEPTH", str(request.max_depth))
    if request.read_worktree:
        raise ProjectorFailClosedV1(
            "WORKTREE_READ_REJECTED",
            "evidence must come from the pinned git tree",
        )
    if request.treat_historical_graph_as_current:
        raise ProjectorFailClosedV1(
            "HISTORICAL_GRAPH_CURRENT_PROOF_REJECTED",
            "a historical graph cannot be admitted as CURRENT proof",
        )
    if request.request_ratification:
        raise ProjectorFailClosedV1(
            "RATIFICATION_REQUEST_REJECTED",
            "the projector cannot ratify a universe boundary",
        )
