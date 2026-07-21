"""Tests for independent DEVELOPMENT panel quarantine release v1."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.research.independent_dev_panel_quarantine_release_v1 import (
    CONTRACT_REL_PATH,
    DATASET_ID,
    DEV_PANEL_SUBDIR,
    EXPECTED_CONTENT_HASH,
    EXPECTED_MANIFEST_SHA256,
    PanelQuarantineReleaseError,
    RELEASED_STATUS,
    assert_trees_byte_identical,
    preflight_quarantine_release,
    quarantine_source_path,
    release_quarantine_panel,
    release_target_path,
    tree_file_inventory,
    verify_panel_identity,
)

REPO = Path(__file__).resolve().parents[2]


def _write_file(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_release_contract_present() -> None:
    assert (REPO / CONTRACT_REL_PATH).is_file()
    payload = json.loads((REPO / CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    assert payload["dataset_id"] == DATASET_ID
    assert payload["released_status"] == RELEASED_STATUS
    assert payload["evaluation_authorized"] is False


def test_quarantine_source_missing_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(PanelQuarantineReleaseError, match="PANEL_MISSING|ARCHIVE"):
        preflight_quarantine_release(archive_root=tmp_path, repo_root=REPO)


def test_target_exists_divergent_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = quarantine_source_path(tmp_path)
    target = release_target_path(tmp_path)
    source.mkdir(parents=True)
    target.mkdir(parents=True)
    _write_file(source / "a.txt", b"aaa")
    _write_file(target / "a.txt", b"bbb")

    def _boom(panel_root: Path):  # noqa: ANN001
        return {
            "panel_root": str(panel_root),
            "dataset_id": DATASET_ID,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "content_hash": EXPECTED_CONTENT_HASH,
            "universe_digest": "x",
            "instrument_count": 46,
            "raw_file_count": 4876,
            "interval": "PT1H",
            "start": "2022-06-01T03:55:17Z",
            "end": "2023-08-16T05:55:00Z",
            "holdout_boundary_ok": True,
        }

    monkeypatch.setattr(
        "src.research.independent_dev_panel_quarantine_release_v1.verify_panel_identity",
        _boom,
    )
    with pytest.raises(PanelQuarantineReleaseError, match="TREE_NOT_BYTE_IDENTICAL"):
        preflight_quarantine_release(archive_root=tmp_path, repo_root=REPO)


def test_target_exists_identical_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = quarantine_source_path(tmp_path)
    target = release_target_path(tmp_path)
    _write_file(source / "a.txt", b"same")
    _write_file(target / "a.txt", b"same")

    def _ok(panel_root: Path):  # noqa: ANN001
        return {
            "panel_root": str(panel_root),
            "dataset_id": DATASET_ID,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "content_hash": EXPECTED_CONTENT_HASH,
            "universe_digest": "u",
            "instrument_count": 46,
            "raw_file_count": 4876,
            "interval": "PT1H",
            "start": "2022-06-01T03:55:17Z",
            "end": "2023-08-16T05:55:00Z",
            "holdout_boundary_ok": True,
        }

    monkeypatch.setattr(
        "src.research.independent_dev_panel_quarantine_release_v1.verify_panel_identity",
        _ok,
    )
    pre = preflight_quarantine_release(archive_root=tmp_path, repo_root=REPO)
    assert pre["identical_existing_target"] is True
    evidence = release_quarantine_panel(
        archive_root=tmp_path, repo_root=REPO, write_repo_evidence=False
    )
    assert evidence["release_mode"] == "IDEMPOTENT_ALREADY_RELEASED_BYTE_IDENTICAL"
    assert evidence["panel_released"] is True


def test_tree_inventory_and_compare(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_file(a / "f.bin", b"hello")
    _write_file(b / "f.bin", b"hello")
    inv = tree_file_inventory(a)
    assert inv["f.bin"][0] == 5
    cmp = assert_trees_byte_identical(a, b)
    assert cmp["file_count"] == 1


def test_holdout_path_rejected() -> None:
    with pytest.raises(PanelQuarantineReleaseError, match="HOLDOUT"):
        verify_panel_identity(Path("/tmp/offline_economic_reevaluation_sealed_long_panel_v1/foo"))


def test_atomic_release_abort_leaves_no_partial_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = quarantine_source_path(tmp_path)
    target = release_target_path(tmp_path)
    _write_file(source / "x.txt", b"payload")

    calls = {"n": 0}

    def _verify(panel_root: Path):  # noqa: ANN001
        calls["n"] += 1
        if (
            calls["n"] >= 2
            and DEV_PANEL_SUBDIR in str(panel_root)
            and "staging" not in str(panel_root)
        ):
            # should not reach final target if rename fails earlier
            pass
        if "release_staging" in str(panel_root) and calls["n"] >= 2:
            raise PanelQuarantineReleaseError("FORCED_STAGING_ABORT")
        return {
            "panel_root": str(panel_root),
            "dataset_id": DATASET_ID,
            "manifest_sha256": EXPECTED_MANIFEST_SHA256,
            "content_hash": EXPECTED_CONTENT_HASH,
            "universe_digest": "u",
            "instrument_count": 46,
            "raw_file_count": 4876,
            "interval": "PT1H",
            "start": "2022-06-01T03:55:17Z",
            "end": "2023-08-16T05:55:00Z",
            "holdout_boundary_ok": True,
        }

    monkeypatch.setattr(
        "src.research.independent_dev_panel_quarantine_release_v1.verify_panel_identity",
        _verify,
    )
    monkeypatch.setattr(
        "src.research.independent_dev_panel_quarantine_release_v1.assert_trees_byte_identical",
        lambda s, t: {
            "file_count": 1,
            "only_source": 0,
            "only_target": 0,
            "sha_or_size_mismatch": 0,
        },
    )
    with pytest.raises(PanelQuarantineReleaseError, match="FORCED_STAGING_ABORT"):
        release_quarantine_panel(archive_root=tmp_path, repo_root=REPO, write_repo_evidence=False)
    assert not target.exists()


@pytest.mark.skipif(
    not os.environ.get("PEAK_TRADE_DATA_ARCHIVE_ROOT"),
    reason="archive root not set",
)
def test_real_quarantine_preflight_when_env_set() -> None:
    summary = preflight_quarantine_release(repo_root=REPO)
    assert summary["passed"] is True
    assert summary["source_proof"]["manifest_sha256"] == EXPECTED_MANIFEST_SHA256
