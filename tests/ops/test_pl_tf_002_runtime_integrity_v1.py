"""Tests for PL-TF-002 runtime integrity (current origin/main + protected surfaces)."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.ops.pl_tf_002_productive_read_only_session_executor_v1.constants_v1 import OWNER_GO
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.runtime_integrity_v1 import (
    PROTECTED_WIRE_SURFACE_PATHS,
    assert_pl_tf_002_runtime_integrity_v1,
)
from src.ops.pl_tf_002_productive_read_only_session_executor_v1.session_executor_v1 import (
    build_pl_tf_002_read_only_get_session_preflight_v1,
)

_CANONICAL_MAIN = "9bd633bb175dab27dc383b91a512e379bd31cefa"


@dataclass(frozen=True)
class _FakeIntegrityBackend:
    origin_main: str
    head: str
    drift: str = ""

    def resolve_origin_main_sha_v1(self) -> str:
        return self.origin_main

    def resolve_head_sha_v1(self) -> str:
        return self.head

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str:
        del paths
        return self.drift


def test_runtime_integrity_passes_when_head_matches_origin_main_and_surfaces_clean() -> None:
    backend = _FakeIntegrityBackend(
        origin_main=_CANONICAL_MAIN,
        head=_CANONICAL_MAIN,
        drift="",
    )
    bound = assert_pl_tf_002_runtime_integrity_v1(
        owner_go=OWNER_GO,
        declared_origin_main_sha=_CANONICAL_MAIN,
        required_owner_go=OWNER_GO,
        integrity_backend=backend,
    )
    assert bound == _CANONICAL_MAIN


def test_declared_sha_mismatch_origin_main_fail_closed() -> None:
    backend = _FakeIntegrityBackend(origin_main=_CANONICAL_MAIN, head=_CANONICAL_MAIN)
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        assert_pl_tf_002_runtime_integrity_v1(
            owner_go=OWNER_GO,
            declared_origin_main_sha="b58f622de2b82be664b2ea2eeee76db90d529a92",
            required_owner_go=OWNER_GO,
            integrity_backend=backend,
        )


def test_head_not_at_origin_main_fail_closed() -> None:
    backend = _FakeIntegrityBackend(
        origin_main=_CANONICAL_MAIN,
        head="b58f622de2b82be664b2ea2eeee76db90d529a92",
    )
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="HEAD_NOT_AT_ORIGIN_MAIN"):
        assert_pl_tf_002_runtime_integrity_v1(
            owner_go=OWNER_GO,
            declared_origin_main_sha=_CANONICAL_MAIN,
            required_owner_go=OWNER_GO,
            integrity_backend=backend,
        )


def test_protected_surface_drift_fail_closed() -> None:
    backend = _FakeIntegrityBackend(
        origin_main=_CANONICAL_MAIN,
        head=_CANONICAL_MAIN,
        drift="diff --git a/x b/x\n",
    )
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="PROTECTED_WIRE_SURFACE_DRIFT"):
        assert_pl_tf_002_runtime_integrity_v1(
            owner_go=OWNER_GO,
            declared_origin_main_sha=_CANONICAL_MAIN,
            required_owner_go=OWNER_GO,
            integrity_backend=backend,
        )


def test_owner_go_does_not_bypass_integrity_gate() -> None:
    backend = _FakeIntegrityBackend(origin_main=_CANONICAL_MAIN, head=_CANONICAL_MAIN)
    with pytest.raises(PlTf002ProductiveReadOnlySessionError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        build_pl_tf_002_read_only_get_session_preflight_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            integrity_backend=backend,
        )


def test_protected_paths_include_ne_tf_001_constants() -> None:
    assert (
        "src/ops/pl_tf_002_network_evidence_contract_v1/constants_v1.py"
        in PROTECTED_WIRE_SURFACE_PATHS
    )


def test_post_merge_main_advance_does_not_self_invalidate_when_surfaces_clean() -> None:
    """Squash merge advances origin/main; gate passes when HEAD matches and paths clean."""
    post_merge_main = "9bd633bb175dab27dc383b91a512e379bd31cefa"
    backend = _FakeIntegrityBackend(origin_main=post_merge_main, head=post_merge_main, drift="")
    pre = build_pl_tf_002_read_only_get_session_preflight_v1(
        owner_go=OWNER_GO,
        origin_main_sha=post_merge_main,
        integrity_backend=backend,
    )
    assert pre.origin_main_sha_bound == post_merge_main
