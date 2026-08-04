"""Focused tests: Double Play archive sibling exporter CLI."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.archive_sibling_export_contract_v1 import (
    ArchiveSiblingExportEffectV1,
    ArchiveSiblingExportResultV1,
    canonical_digest_v1,
)
from src.ops.archive_sibling_export_contract_v1.contracts import (
    BLOCK_WRITE_NOT_AUTHORIZED,
)
from src.ops.double_play_archive_sibling_exporter_v1.constants_v1 import (
    TARGET_RELATIVE_PATH,
)

REPO = Path(__file__).resolve().parents[2]
CLI_PATH = REPO / "scripts/ops/run_double_play_archive_sibling_exporter_v1.py"
FORBIDDEN_IMPORT_TOKENS = (
    "src.webui",
    "playwright",
    "presentation_projection_octet",
    "workflow_dashboard",
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "webui",
    "playwright",
)


def _load_cli():
    spec = importlib.util.spec_from_file_location(
        "run_double_play_archive_sibling_exporter_v1",
        CLI_PATH,
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CLI = _load_cli()


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
        "evidence_digest": "e" * 64,
    }
    base.update(overrides)
    return base


def _write_source(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "display_source.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _list_files(root: Path) -> set[str]:
    if not root.exists():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_cli_defaults_dry_run_true() -> None:
    parser = CLI.build_parser()
    args = parser.parse_args(
        [
            "--archive-root",
            "/tmp/archive",
            "--display-source-path",
            "/tmp/display.json",
        ]
    )
    assert args.dry_run is True
    assert args.write_authorized is False
    assert CLI.DEFAULT_DRY_RUN is True

    sig = inspect.signature(CLI.run_double_play_archive_sibling_exporter_cli_v1)
    assert sig.parameters["dry_run"].default is True
    assert sig.parameters["write_authorized"].default is False


def test_default_dry_run_mutates_nothing(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _display())
    archive_root = tmp_path / "archive_root"
    source_before = source.read_bytes()
    before = _list_files(tmp_path)

    out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        display_source_path=source,
    )
    assert out.ok is True
    assert out.dry_run is True
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.CREATE.value
    assert out.target_relative_path == TARGET_RELATIVE_PATH
    assert not archive_root.exists()
    assert source.read_bytes() == source_before
    assert _list_files(tmp_path) == before


def test_missing_write_authorization_blocks(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _display())
    archive_root = tmp_path / "archive_root"
    before = _list_files(tmp_path)

    out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        display_source_path=source,
        dry_run=False,
        write_authorized=False,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.effect == ArchiveSiblingExportEffectV1.BLOCKED.value
    assert out.block_reason == BLOCK_WRITE_NOT_AUTHORIZED
    assert not (archive_root / TARGET_RELATIVE_PATH).exists()
    assert _list_files(tmp_path) == before


def test_cli_requires_explicit_source_and_archive_args() -> None:
    parser = CLI.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(["--archive-root", "/tmp/a"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--display-source-path", "/tmp/d.json"])


def test_no_latest_discovery_in_cli_source() -> None:
    text = CLI_PATH.read_text(encoding="utf-8")
    assert "latest" not in text.lower() or "no latest" in text.lower()
    assert "discover" in text.lower()  # documented as forbidden
    assert "--display-source-path" in text
    assert "--archive-root" in text
    assert "rglob" not in text
    assert "glob(" not in text


def test_authorized_write_uses_pr_a_contract_exactly(tmp_path: Path) -> None:
    payload = _display()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    expected_digest = canonical_digest_v1(payload)
    captured: dict[str, object] = {}

    def _spy(**kwargs: object) -> ArchiveSiblingExportResultV1:
        captured.update(kwargs)
        return ArchiveSiblingExportResultV1(
            effect=ArchiveSiblingExportEffectV1.CREATE,
            write_performed=True,
            dry_run=False,
            contract_name=str(kwargs["contract_name"]),
            target_path=str(Path(str(kwargs["archive_root"])) / TARGET_RELATIVE_PATH),
            source_digest=expected_digest,
            target_digest_before=None,
            target_digest_after=expected_digest,
            expected_target_digest=expected_digest,
            block_reason=None,
            schema_name=str(kwargs["contract_name"]),
        )

    with patch.object(CLI, "export_archive_sibling_json_v1", side_effect=_spy) as mocked:
        out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
            archive_root=archive_root,
            display_source_path=source,
            dry_run=False,
            write_authorized=True,
        )

    assert mocked.call_count == 1
    assert captured["target_relative_path"] == TARGET_RELATIVE_PATH
    assert captured["dry_run"] is False
    assert captured["write_authorized"] is True
    assert captured["contract_name"] == CLI.CONTRACT_NAME
    assert captured["required_fields"] == CLI.REQUIRED_PAYLOAD_FIELDS
    assert captured["payload"] == payload
    assert out.ok is True
    assert out.write_performed is True


def test_authorized_write_payload_semantically_unchanged(tmp_path: Path) -> None:
    payload = _display()
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"
    source_before = source.read_bytes()
    expected_digest = canonical_digest_v1(payload)

    out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        display_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is True
    assert out.write_performed is True
    target = archive_root / TARGET_RELATIVE_PATH
    written = json.loads(target.read_text(encoding="utf-8"))
    assert written == payload
    assert canonical_digest_v1(written) == expected_digest
    assert out.source_digest == expected_digest
    assert source.read_bytes() == source_before


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=tmp_path / "archive_root",
        display_source_path=tmp_path / "missing.json",
        dry_run=False,
        write_authorized=True,
    )
    assert out.ok is False
    assert out.write_performed is False
    assert out.error_code == CLI.ERROR_SOURCE_MISSING_CLI


def test_nonidentical_existing_blocks_dry_run(tmp_path: Path) -> None:
    source = _write_source(tmp_path, _display(overall_status="display_ready"))
    archive_root = tmp_path / "archive_root"
    target = archive_root / TARGET_RELATIVE_PATH
    target.parent.mkdir(parents=True)
    target.write_text(
        json.dumps(_display(overall_status="display_blocked"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        display_source_path=source,
        dry_run=True,
        write_authorized=False,
    )
    assert out.ok is False
    assert out.error_code == CLI.ERROR_TARGET_CONFLICT_CLI


def test_cli_has_no_forbidden_imports() -> None:
    tree = ast.parse(CLI_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for token in FORBIDDEN_IMPORT_TOKENS:
                    assert token not in alias.name
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not alias.name.startswith(prefix)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for token in FORBIDDEN_IMPORT_TOKENS:
                assert token not in node.module
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not node.module.startswith(prefix)


def test_end_to_end_export_materialize_loader(tmp_path: Path) -> None:
    """Explicit source → exporter → materializer → projection → loader."""
    from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
        SOURCE_DISPLAY_RELATIVE_PATH,
        STATUS_WRITTEN,
        materialize_double_play_presentation_projection_v1,
        try_load_double_play_display_source_v1,
    )
    from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
        STORAGE_RELATIVE_PATH,
        try_load_double_play_presentation_projection_v1,
    )

    payload = _display(evidence_digest="f" * 64)
    source = _write_source(tmp_path, payload)
    archive_root = tmp_path / "archive_root"

    export_out = CLI.run_double_play_archive_sibling_exporter_cli_v1(
        archive_root=archive_root,
        display_source_path=source,
        dry_run=False,
        write_authorized=True,
    )
    assert export_out.ok is True
    assert export_out.write_performed is True
    assert (archive_root / SOURCE_DISPLAY_RELATIVE_PATH).is_file()

    loaded, errors, path = try_load_double_play_display_source_v1(archive_root)
    assert errors == ()
    assert loaded is not None
    assert loaded["overall_status"] == "display_ready"
    assert path is not None

    materialize = materialize_double_play_presentation_projection_v1(
        archive_root,
        generated_at="2026-08-05T00:00:00Z",
        effective_at="2026-08-05T00:00:00Z",
    )
    assert materialize.written is True
    assert materialize.status == STATUS_WRITTEN
    assert (archive_root / STORAGE_RELATIVE_PATH).is_file()

    projection = try_load_double_play_presentation_projection_v1(archive_root)
    assert projection.loaded is True
    assert projection.binder_fields is not None
    assert projection.binder_fields["overall_status"] == "display_ready"


def test_src_webui_unchanged_regression() -> None:
    """PR must not mutate dashboard/presentation surfaces under src/webui."""
    diff = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=str(REPO),
        text=True,
    )
    webui_hits = [line for line in diff.splitlines() if line.startswith("src/webui/")]
    assert webui_hits == []
