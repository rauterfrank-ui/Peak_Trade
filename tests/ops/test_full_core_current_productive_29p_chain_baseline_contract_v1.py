"""CURRENT_PRODUCTIVE 29P chain baseline contract — fail-closed proofs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_chain_baseline_contract_v1 import (
    AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS,
    CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA,
    CurrentProductive29PChainBaselineError,
    resolve_cap24_persisted_repository_sha_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA as COMMON_EPOCH_SHA,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap24_selection_state_canonical_writer_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA as CAP24_WRITER_SHA,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA as CAP24_HANDOFF_SHA,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME


def test_chain_slice_pins_unified() -> None:
    assert CAP24_WRITER_SHA == CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA
    assert CAP24_HANDOFF_SHA == CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA
    assert COMMON_EPOCH_SHA == CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA


def test_resolve_repository_sha_from_manifest(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    prod.mkdir()
    legacy_sha = "e5396206530415b469fa345ec04322613c953c44"
    assert legacy_sha in AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS
    (prod / "cap24_selection_state_publish_manifest_v1.json").write_text(
        json.dumps({"repository_sha": legacy_sha}),
        encoding="utf-8",
    )
    assert resolve_cap24_persisted_repository_sha_v1(productivity_root=prod) == legacy_sha


def test_resolve_repository_sha_unauthorized_fail_closed(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    prod.mkdir()
    (prod / "cap24_selection_state_publish_manifest_v1.json").write_text(
        json.dumps({"repository_sha": "deadbeef" * 5}),
        encoding="utf-8",
    )
    with pytest.raises(
        CurrentProductive29PChainBaselineError,
        match="CAP24_REPOSITORY_SHA_NOT_AUTHORIZED",
    ):
        resolve_cap24_persisted_repository_sha_v1(productivity_root=prod)


def test_resolve_from_selection_when_no_manifest(tmp_path: Path) -> None:
    prod = tmp_path / "prod"
    sel_dir = prod / "runtime_state" / "selection"
    sel_dir.mkdir(parents=True)
    sha = CURRENT_PRODUCTIVE_29P_CHAIN_SLICE_ORIGIN_MAIN_SHA
    (sel_dir / SELECTION_FILENAME).write_text(
        json.dumps({"repository_sha": sha, "state": "SELECTED_ACTIVE"}),
        encoding="utf-8",
    )
    assert resolve_cap24_persisted_repository_sha_v1(productivity_root=prod) == sha
