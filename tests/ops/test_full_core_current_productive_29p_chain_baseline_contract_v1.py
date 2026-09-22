"""CURRENT_PRODUCTIVE 29P chain baseline — merge-stable execution identity proofs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS,
    CurrentProductive29PChainBaselineError,
    assert_current_productive_29p_execution_identity_v1,
    assert_current_productive_29p_repository_sha_for_execution_v1,
    resolve_cap24_persisted_repository_sha_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME

_LEGACY_E539 = "e5396206530415b469fa345ec04322613c953c44"
_PRE_MERGE_BASE = "8379a278517b23240ca1cdad02fe041b7d618874"
_HYPOTHETICAL_X = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_HYPOTHETICAL_Y = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
_HYPOTHETICAL_Z = "cccccccccccccccccccccccccccccccccccccccc"


@dataclass(frozen=True)
class _MockIntegrityBackend:
    origin_main: str
    head: str
    drift: str = ""

    def resolve_origin_main_sha_v1(self) -> str:
        return self.origin_main

    def resolve_head_sha_v1(self) -> str:
        return self.head

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str:
        return self.drift


def test_trusted_origin_main_and_matching_head_pass() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_X)
    assert (
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_HYPOTHETICAL_X,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )
        == _HYPOTHETICAL_X
    )


def test_feature_branch_head_not_at_origin_main_fail_closed() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_Y)
    with pytest.raises(CurrentProductive29PChainBaselineError, match="HEAD_NOT_AT_ORIGIN_MAIN"):
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_HYPOTHETICAL_X,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )


def test_detached_commit_declared_mismatch_fail_closed() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_Z)
    with pytest.raises(CurrentProductive29PChainBaselineError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_PRE_MERGE_BASE,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )


def test_spoofed_repository_sha_without_trusted_identity_fail_closed() -> None:
    with pytest.raises(
        CurrentProductive29PChainBaselineError, match="REPOSITORY_SHA_BASELINE_MISMATCH"
    ):
        assert_current_productive_29p_repository_sha_for_execution_v1(
            repository_sha=_HYPOTHETICAL_Z,
            trusted_execution_identity=_HYPOTHETICAL_X,
        )


def test_legacy_e539_persisted_provenance_handoff_allowed(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    prod.mkdir()
    assert _LEGACY_E539 in HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS
    (prod / "cap24_selection_state_publish_manifest_v1.json").write_text(
        json.dumps({"repository_sha": _LEGACY_E539}),
        encoding="utf-8",
    )
    assert resolve_cap24_persisted_repository_sha_v1(productivity_root=prod) == _LEGACY_E539


def test_unknown_persisted_sha_fail_closed(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    prod.mkdir()
    (prod / "cap24_selection_state_publish_manifest_v1.json").write_text(
        json.dumps({"repository_sha": _HYPOTHETICAL_Z}),
        encoding="utf-8",
    )
    with pytest.raises(
        CurrentProductive29PChainBaselineError,
        match="CAP24_REPOSITORY_SHA_NOT_AUTHORIZED",
    ):
        resolve_cap24_persisted_repository_sha_v1(productivity_root=prod)


def test_post_merge_hypothetical_x_without_code_constant_passes(tmp_path: Path) -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_X)
    trusted = assert_current_productive_29p_execution_identity_v1(
        declared_origin_main_sha=_HYPOTHETICAL_X,
        integrity_backend=backend,
        verify_protected_surfaces=False,
    )
    prod = tmp_path / "prod"
    prod.mkdir()
    (prod / "cap24_selection_state_publish_manifest_v1.json").write_text(
        json.dumps({"repository_sha": _HYPOTHETICAL_X}),
        encoding="utf-8",
    )
    assert (
        resolve_cap24_persisted_repository_sha_v1(
            productivity_root=prod,
            trusted_execution_identity=trusted,
        )
        == _HYPOTHETICAL_X
    )


def test_next_merge_hypothetical_y_without_source_edit() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_Y, head=_HYPOTHETICAL_Y)
    assert (
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_HYPOTHETICAL_Y,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )
        == _HYPOTHETICAL_Y
    )


def test_origin_x_execution_identity_stale_8379_fail_closed() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_X)
    with pytest.raises(CurrentProductive29PChainBaselineError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_PRE_MERGE_BASE,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )


def test_origin_x_execution_identity_arbitrary_z_fail_closed() -> None:
    backend = _MockIntegrityBackend(origin_main=_HYPOTHETICAL_X, head=_HYPOTHETICAL_X)
    with pytest.raises(CurrentProductive29PChainBaselineError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        assert_current_productive_29p_execution_identity_v1(
            declared_origin_main_sha=_HYPOTHETICAL_Z,
            integrity_backend=backend,
            verify_protected_surfaces=False,
        )


def test_resolve_from_selection_historical_base(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    sel_dir = prod / "runtime_state" / "selection"
    sel_dir.mkdir(parents=True)
    (sel_dir / SELECTION_FILENAME).write_text(
        json.dumps({"repository_sha": _PRE_MERGE_BASE, "state": "SELECTED_ACTIVE"}),
        encoding="utf-8",
    )
    assert resolve_cap24_persisted_repository_sha_v1(productivity_root=prod) == _PRE_MERGE_BASE
