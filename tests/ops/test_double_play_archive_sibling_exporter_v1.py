"""Bounded Double Play archive sibling exporter V1 — focused contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.ops.archive_sibling_export_contract_v1 import canonical_digest_v1
from src.ops.double_play_archive_sibling_exporter_v1.constants_v1 import (
    CAPABILITY_ID,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_MISSING,
    ERROR_TARGET_CONFLICT,
    TARGET_RELATIVE_PATH,
)
from src.ops.double_play_archive_sibling_exporter_v1.exporter_v1 import (
    export_double_play_display_to_archive_sibling_v1,
)

EXPORTER_PKG = Path("src/ops/double_play_archive_sibling_exporter_v1")
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "src.webui.",
    "trading.master_v2.double_play_composition",
    "trading.master_v2.double_play_state",
)


def _display(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "overall_status": "display_ready",
        "panel_summaries": [
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "Composition: ELIGIBLE_MODEL_ONLY — data-only; not trading-ready.",
                "blockers": [],
            },
            {
                "name": "state_transition",
                "status": "display_ready",
                "summary": "Transition allowed (model label): NOOP",
                "blockers": [],
            },
        ],
        "blockers": [],
        "display_only": True,
        "live_authorization": False,
        "evidence_digest": "d" * 64,
    }
    base.update(overrides)
    return base


def _write_source(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "source" / "double_play_dashboard_display.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_capability_id_is_stable() -> None:
    assert CAPABILITY_ID == "CAPABILITY_DOUBLE_PLAY_ARCHIVE_SIBLING_EXPORTER_V1"


def test_successful_one_to_one_export(tmp_path: Path) -> None:
    payload = _display()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    source_bytes_before = source.read_bytes()
    expected_digest = canonical_digest_v1(payload)

    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is True
    assert out.error_code is None
    assert out.source_payload_digest == expected_digest
    assert out.target_payload_digest == expected_digest
    assert out.overall_status == "display_ready"
    assert out.panel_count == 2
    assert out.replaced_existing is False
    assert out.identical_existing is False
    assert out.bytes_written > 0
    assert out.authority_effect == "NONE"
    assert out.double_play_authority_effect == "NONE"

    target = archive_root / TARGET_RELATIVE_PATH
    assert target.is_file()
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == payload
    assert source.read_bytes() == source_bytes_before


def test_panels_normalized_to_panel_summaries(tmp_path: Path) -> None:
    payload = {
        "overall_status": "display_ready",
        "panels": [
            {
                "name": "composition",
                "status": "display_ready",
                "summary": "ok",
                "blockers": [],
            }
        ],
    }
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is True
    written = json.loads((archive_root / TARGET_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert "panels" not in written
    assert written["panel_summaries"][0]["name"] == "composition"


def test_identical_existing_is_idempotent(tmp_path: Path) -> None:
    payload = _display()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    first = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert first.exported is True
    target = archive_root / TARGET_RELATIVE_PATH
    mtime_before = target.stat().st_mtime_ns
    second = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert second.exported is True
    assert second.identical_existing is True
    assert second.bytes_written == 0
    assert target.stat().st_mtime_ns == mtime_before


def test_corrupt_existing_target_fail_closed(tmp_path: Path) -> None:
    payload = _display()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_text("{not-json", encoding="utf-8")
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_TARGET_CONFLICT


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_root"
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=tmp_path / "absent.json",
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_MISSING
    assert not archive_root.exists()


def test_corrupt_source_fail_closed(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("{not-json", encoding="utf-8")
    archive_root = tmp_path / "archive_root"
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_CORRUPT


def test_invalid_missing_required_field_fail_closed(tmp_path: Path) -> None:
    payload = _display()
    del payload["overall_status"]
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_INVALID


def test_ambiguous_panels_and_summaries_fail_closed(tmp_path: Path) -> None:
    payload = _display()
    payload["panels"] = payload["panel_summaries"]
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=source,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_SOURCE_INVALID


def test_identical_source_target_fail_closed(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    payload = _display()
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    out = export_double_play_display_to_archive_sibling_v1(
        display_source_path=target,
        archive_root=archive_root,
    )
    assert out.exported is False
    assert out.error_code == ERROR_IDENTICAL_PATHS


def test_package_has_no_presentation_or_composer_imports() -> None:
    for path in EXPORTER_PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for prefix in FORBIDDEN_IMPORT_PREFIXES:
                        assert not alias.name.startswith(prefix), (path, alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not node.module.startswith(prefix), (path, node.module)
