"""Tests for bounded GAP-001 rewire in run_promotion_proposal_cycle."""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.meta.learning_loop.config_patch_manifest_v1 import (
    build_empty_config_patch_manifest_v1,
    compute_manifest_integrity,
    serialize_config_patch_manifest_v1,
)
from src.meta.learning_loop.models import ConfigPatch, PatchStatus


FIXED_NOW = datetime(2026, 6, 27, 12, 0, 0, tzinfo=timezone.utc)
MANIFEST_ID = "33333333-3333-4333-8333-333333333333"
LINEAGE_ID = "44444444-4444-4444-8444-444444444444"


def _load_promotion_cycle_module():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "run_promotion_proposal_cycle.py"
    module_name = "run_promotion_proposal_cycle_under_test"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def promotion_cycle():
    return _load_promotion_cycle_module()


def _write_manifest(path: Path, *, patches: list[ConfigPatch]) -> None:
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=MANIFEST_ID,
        generated_at=FIXED_NOW,
        lineage_manifest_ref=LINEAGE_ID,
    )
    manifest.patches = patches
    manifest.integrity = compute_manifest_integrity(manifest)
    path.write_text(serialize_config_patch_manifest_v1(manifest), encoding="utf-8")


def test_load_patches_requires_manifest_by_default(promotion_cycle, tmp_path: Path) -> None:
    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=None,
        non_canonical_demo_legacy_patches=False,
    )
    assert patches == []


def test_load_patches_uses_manifest_loader(promotion_cycle, tmp_path: Path) -> None:
    manifest_path = tmp_path / "promotion_input.json"
    _write_manifest(
        manifest_path,
        patches=[
            ConfigPatch(
                id="patch-1",
                target="research.offline.window_days",
                old_value=30,
                new_value=45,
                status=PatchStatus.APPLIED_OFFLINE,
                confidence_score=0.9,
            )
        ],
    )

    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=manifest_path,
        non_canonical_demo_legacy_patches=False,
    )

    assert len(patches) == 1
    assert patches[0].target == "research.offline.window_days"
    assert isinstance(patches[0], ConfigPatch)


def test_load_patches_empty_manifest_returns_empty_list(
    promotion_cycle,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "empty.json"
    _write_manifest(manifest_path, patches=[])

    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=manifest_path,
        non_canonical_demo_legacy_patches=False,
    )

    assert patches == []


def test_demo_json_not_default_without_explicit_legacy_flag(
    promotion_cycle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    demo_path = tmp_path / "demo_patches_for_promotion.json"
    demo_path.write_text(
        json.dumps(
            [
                {
                    "id": "demo-1",
                    "target": "portfolio.leverage",
                    "new_value": 1.5,
                    "status": PatchStatus.APPLIED_OFFLINE.value,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=None,
        non_canonical_demo_legacy_patches=False,
    )

    assert patches == []


def test_non_canonical_demo_legacy_flag_is_explicit_only(
    promotion_cycle,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    demo_dir = tmp_path / "reports" / "learning_snippets"
    demo_dir.mkdir(parents=True)
    demo_path = demo_dir / "demo_patches_for_promotion.json"
    demo_path.write_text(
        json.dumps(
            [
                {
                    "id": "demo-legacy-1",
                    "target": "research.offline.window_days",
                    "new_value": 45,
                    "status": PatchStatus.APPLIED_OFFLINE.value,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=None,
        non_canonical_demo_legacy_patches=True,
    )

    assert len(patches) == 1
    assert patches[0].id == "demo-legacy-1"


def test_invalid_manifest_returns_empty_without_demo_fallback(
    promotion_cycle,
    tmp_path: Path,
) -> None:
    bad_manifest = tmp_path / "bad.json"
    bad_manifest.write_text("{not-json", encoding="utf-8")

    patches = promotion_cycle._load_patches_for_promotion(
        promotion_input_manifest=bad_manifest,
        non_canonical_demo_legacy_patches=False,
    )

    assert patches == []
