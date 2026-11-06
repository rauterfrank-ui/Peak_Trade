"""Atlas binding for native full-cycle host orchestration entry."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.system_atlas_v1.load_v1 import load_atlas_v1
from scripts.ops.system_atlas_v1.validate_v1 import validate_atlas_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
HOST_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_native_full_cycle_host_v1.py"
)


def test_atlas_catalog_contains_native_full_cycle_host_orchestration() -> None:
    text = CATALOG.read_text(encoding="utf-8")
    assert "RUNTIME_COMPONENT:current_productive_native_full_cycle_host_v1" in text
    assert HOST_PATH in text
    assert "AUTHORITY=NONE" in text or "authority=NONE" in text


def test_system_atlas_validate_passes() -> None:
    atlas = load_atlas_v1(repo_root=REPO_ROOT)
    warnings = validate_atlas_v1(atlas)
    assert isinstance(warnings, list)
